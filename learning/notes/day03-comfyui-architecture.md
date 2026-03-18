# Day 3: ComfyUI 架构深入

> 学习时间: 2026-03-18 22:03 UTC  
> 重点: 节点系统源码 + 自定义节点加载机制

---

## 1. 节点系统总览

ComfyUI 的核心是一个 **图执行引擎**（Graph Execution Engine），所有 AI 操作都被抽象为"节点"（Node），节点通过"连线"（Links）传递数据，形成有向无环图（DAG）。

### 架构分层

```
┌─────────────────────────────────────────────┐
│  Frontend (LiteGraph.js)                     │
│  - 节点可视化拖拽 / WebSocket 实时通信         │
├─────────────────────────────────────────────┤
│  Server Layer (server.py / aiohttp)          │
│  - REST API (/prompt, /history, /view...)    │
│  - WebSocket (/ws) 实时状态推送               │
├─────────────────────────────────────────────┤
│  Execution Layer (execution.py + graph.py)   │
│  - Prompt 验证 → 拓扑排序 → 节点调度执行       │
│  - 缓存管理 / Lazy Eval / 并行策略            │
├─────────────────────────────────────────────┤
│  Node Layer (nodes.py + custom_nodes/)       │
│  - 内置节点 + 自定义节点 → NODE_CLASS_MAPPINGS │
│  - 数据类型系统 (MODEL/CLIP/IMAGE/LATENT...)  │
├─────────────────────────────────────────────┤
│  Backend (comfy/ 核心库)                      │
│  - Model Management / Samplers / SD Pipeline  │
└─────────────────────────────────────────────┘
```

---

## 2. 节点注册机制详解

### 2.1 节点类的必备属性

每个节点是一个 Python 类，**必须**定义以下 4 个属性：

| 属性 | 类型 | 说明 |
|------|------|------|
| `INPUT_TYPES()` | classmethod → dict | 定义节点接受的输入，分为 required / optional / hidden |
| `RETURN_TYPES` | tuple of str | 输出端口的数据类型列表 |
| `FUNCTION` | str | 执行时调用的方法名 |
| `CATEGORY` | str | 在 UI 添加菜单中的分类路径 |

#### 示例：CLIPTextEncode 节点源码解析

```python
class CLIPTextEncode(ComfyNodeABC):
    @classmethod
    def INPUT_TYPES(s) -> InputTypeDict:
        return {
            "required": {
                "text": (IO.STRING, {"multiline": True, "dynamicPrompts": True, 
                         "tooltip": "The text to be encoded."}),
                "clip": (IO.CLIP, {"tooltip": "The CLIP model used for encoding."})
            }
        }
    RETURN_TYPES = (IO.CONDITIONING,)
    OUTPUT_TOOLTIPS = ("A conditioning containing the embedded text...",)
    FUNCTION = "encode"
    CATEGORY = "conditioning"
    DESCRIPTION = "Encodes a text prompt using a CLIP model..."
    SEARCH_ALIASES = ["text", "prompt", "text prompt", ...]

    def encode(self, clip, text):
        tokens = clip.tokenize(text)
        return (clip.encode_from_tokens_scheduled(tokens), )
```

**关键要点**：
1. `INPUT_TYPES` 是 `@classmethod`（不是实例方法），因为 ComfyUI 需要在实例化前就知道输入规格
2. 每个输入是 `(类型, 选项dict)` 的 tuple
3. FUNCTION 指定的方法**接收的参数名必须匹配 INPUT_TYPES 中的 key 名**
4. 返回值必须是 **tuple**（注意尾逗号 `(result,)`）

### 2.2 INPUT_TYPES 三种类别

```python
{
    "required": {  # 必须连线或填值，缺少会报错
        "images": ("IMAGE",),
        "mode": (["brightest", "reddest"],),  # 列表 = 下拉选择 Combo
    },
    "optional": {  # 可选，不连也不会报错
        "mask": ("MASK",),
    },
    "hidden": {    # 不在 UI 显示，由系统自动注入
        "prompt": "PROMPT",
        "extra_pnginfo": "EXTRA_PNGINFO",
        "unique_id": "UNIQUE_ID",
    }
}
```

**输入选项详解**（第二个元素 dict）：

| 选项 | 类型 | 说明 |
|------|------|------|
| `default` | any | 默认值 |
| `min` / `max` | number | 数值范围限制 |
| `step` | number | 滑块步长 |
| `multiline` | bool | 文本框是否多行 |
| `dynamicPrompts` | bool | 是否支持动态提示词语法 |
| `tooltip` | str | 鼠标悬停提示 |
| `lazy` | bool | **惰性求值**，节点可以延迟请求该输入 |
| `advanced` | bool | 标记为高级参数（默认折叠） |

### 2.3 可选属性（增强功能）

| 属性 | 类型 | 说明 |
|------|------|------|
| `OUTPUT_NODE` | bool | True = 输出节点（如 SaveImage、PreviewImage），决定执行优先级 |
| `RETURN_NAMES` | tuple | 输出端口的自定义名称 |
| `OUTPUT_TOOLTIPS` | tuple | 输出端口的提示文字 |
| `DESCRIPTION` | str | 节点说明文字 |
| `SEARCH_ALIASES` | list | 搜索别名（UI 搜索用） |
| `DEPRECATED` | bool | 标记为已弃用 |
| `IS_CHANGED()` | classmethod | 判断节点是否需要重新执行（返回不同值=需要重执行） |
| `VALIDATE_INPUTS()` | classmethod | 自定义输入验证逻辑 |
| `ESSENTIALS_CATEGORY` | str | Essentials 分类（ComfyUI 内部用） |

#### IS_CHANGED 的缓存机制

```python
@classmethod
def IS_CHANGED(s, latent):
    image_path = folder_paths.get_annotated_filepath(latent)
    m = hashlib.sha256()
    with open(image_path, 'rb') as f:
        m.update(f.read())
    return m.digest().hex()  # 返回文件哈希，文件变了就重新执行
```

ComfyUI 会缓存每个节点的 `IS_CHANGED` 返回值。如果两次执行返回相同值，该节点直接使用缓存结果，不重新执行。

---

## 3. 数据类型系统

### 3.1 核心数据类型

ComfyUI 通过字符串标识符定义类型系统，连线时只有类型匹配的端口才能相连。

| 类型标识符 | Python 实际类型 | 说明 |
|-----------|----------------|------|
| `MODEL` | comfy 内部对象 | 扩散模型（U-Net + scheduler 配置） |
| `CLIP` | comfy 内部对象 | 文本编码器（可能是 CLIP-L、CLIP-G、T5 等） |
| `VAE` | comfy 内部对象 | 图像编解码器 |
| `CONDITIONING` | list[tuple[Tensor, dict]] | 条件信息（编码后的文本 + 元数据） |
| `LATENT` | dict{"samples": Tensor, ...} | 潜空间张量，形状 [B,C,H,W] |
| `IMAGE` | torch.Tensor [B,H,W,C] | 图像批次，值范围 [0,1]，RGB float32 |
| `MASK` | torch.Tensor [B,H,W] | 掩码，0=遮挡 1=保留 |
| `CLIP_VISION` | comfy 内部对象 | 视觉编码器（IP-Adapter 等用） |
| `INT` | int | 整数，UI 自动生成滑块 |
| `FLOAT` | float | 浮点数，UI 自动生成滑块 |
| `STRING` | str | 字符串，UI 自动生成文本框 |
| `BOOLEAN` | bool | 布尔值，UI 自动生成复选框 |

### 3.2 类型系统的设计哲学

```
核心原则：类型即连线约束

STRING ──────→ STRING  ✅ 可以连
IMAGE  ──────→ IMAGE   ✅ 可以连
IMAGE  ──────→ STRING  ❌ 类型不匹配，无法连线
```

特殊类型规则：
- **Combo 类型**（列表）：`["option1", "option2"]` → 生成下拉菜单，不能被连线
- **隐藏类型**：`"PROMPT"`, `"EXTRA_PNGINFO"`, `"UNIQUE_ID"` → 系统自动注入
- **通配符**：自定义节点可以用 `"*"` 表示接受任意类型

### 3.3 IO 枚举（现代写法）

ComfyUI 最新版引入了 `comfy.comfy_types.IO` 枚举，让类型标识更规范：

```python
from comfy.comfy_types import IO

# 旧写法
RETURN_TYPES = ("IMAGE",)
# 新写法（推荐）
RETURN_TYPES = (IO.IMAGE,)
```

---

## 4. 节点发现与加载流程

### 4.1 启动流程总览

```
ComfyUI main.py 启动
    │
    ├── 1. 加载内置节点
    │   └── import nodes  →  nodes.py 中所有类注册到 NODE_CLASS_MAPPINGS
    │
    ├── 2. 扫描 custom_nodes/ 目录
    │   └── 对每个子目录：
    │       ├── 检查 __init__.py 是否存在
    │       ├── import 该 Python 包
    │       ├── 读取 NODE_CLASS_MAPPINGS
    │       ├── 读取 NODE_DISPLAY_NAME_MAPPINGS（可选）
    │       ├── 读取 WEB_DIRECTORY（可选，JS 扩展路径）
    │       └── 合并到全局 nodes.NODE_CLASS_MAPPINGS
    │
    ├── 3. 初始化 PromptServer
    │   └── 注册所有 REST/WebSocket 路由
    │
    └── 4. 启动事件循环
        └── 等待前端提交 /prompt
```

### 4.2 内置节点注册

在 `nodes.py` 文件末尾，所有内置节点类被显式注册：

```python
NODE_CLASS_MAPPINGS = {
    "KSampler": KSampler,
    "CheckpointLoaderSimple": CheckpointLoaderSimple,
    "CLIPTextEncode": CLIPTextEncode,
    "VAEDecode": VAEDecode,
    "VAEEncode": VAEEncode,
    "EmptyLatentImage": EmptyLatentImage,
    "SaveImage": SaveImage,
    "LoadImage": LoadImage,
    "LoraLoader": LoraLoader,
    # ... 几十个内置节点
}
```

key 是字符串标识符（用于 API JSON 中的 `class_type`），value 是实际的 Python 类。

### 4.3 自定义节点加载机制详解

#### 目录结构规范

```
ComfyUI/
└── custom_nodes/
    └── my_custom_node/
        ├── __init__.py          # 必须：导出 NODE_CLASS_MAPPINGS
        ├── nodes.py             # 节点类定义（约定俗成的文件名）
        ├── requirements.txt     # 依赖（可选）
        └── web/                 # 前端 JS 扩展（可选）
            └── js/
                └── my_extension.js
```

#### __init__.py 标准模板

```python
from .nodes import MyNode1, MyNode2

# 必须导出：节点类映射
NODE_CLASS_MAPPINGS = {
    "MyNode1": MyNode1,
    "MyNode2": MyNode2,
}

# 可选：显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode1": "My Custom Node 1",
    "MyNode2": "My Custom Node 2",
}

# 可选：前端 JS 扩展目录
WEB_DIRECTORY = "./web/js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
```

#### 加载过程代码级分析

ComfyUI 在启动时调用 `init_extra_nodes()`（位于 nodes.py 或 main 流程），核心逻辑：

```python
# 伪代码，简化自 ComfyUI 源码
def load_custom_node(module_path):
    """加载单个自定义节点包"""
    try:
        module = importlib.import_module(module_path)
        
        # 检查是否导出了 NODE_CLASS_MAPPINGS
        if hasattr(module, 'NODE_CLASS_MAPPINGS'):
            # 合并到全局映射
            nodes.NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        
        if hasattr(module, 'NODE_DISPLAY_NAME_MAPPINGS'):
            nodes.NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
        
        if hasattr(module, 'WEB_DIRECTORY'):
            # 记录 JS 扩展目录，后续由 server.py 静态服务
            nodes.EXTENSION_WEB_DIRS[module_name] = web_dir
            
    except Exception as e:
        logging.warning(f"Failed to load custom node {module_path}: {e}")
        # 不会 crash 整个 ComfyUI，只是跳过这个节点
```

**关键设计决策**：
1. **容错加载**：单个自定义节点失败不影响其他节点和系统启动
2. **命名冲突**：后加载的会覆盖先加载的（所以 key 要有独特性）
3. **热加载不支持**：修改代码后必须重启 ComfyUI（这是一个常见痛点）

### 4.4 节点验证流程

当用户提交一个 workflow 到 `/prompt` 时，execution.py 会进行验证：

```python
# 验证步骤：
# 1. 检查所有 class_type 是否在 NODE_CLASS_MAPPINGS 中存在
# 2. 对每个节点调用 INPUT_TYPES()，检查必填输入是否都提供了
# 3. 检查连线类型是否匹配
# 4. 检查是否有循环依赖（DAG 验证）
# 5. 如果节点定义了 VALIDATE_INPUTS()，调用它做自定义验证
```

---

## 5. 自定义节点常见模式分析

### 5.1 输出节点（OUTPUT_NODE）

```python
class SaveImage:
    OUTPUT_NODE = True  # 标记为输出节点
    
    def save(self, images, filename_prefix="ComfyUI"):
        # ... 保存逻辑
        return {"ui": {"images": results}}  # 特殊返回格式：ui dict
```

输出节点的特殊性：
- 被标记为执行图的"终点"
- 在拓扑排序中优先调度（`ux_friendly_pick_node` 逻辑）
- 返回 `{"ui": {...}}` 格式，前端会展示结果

### 5.2 Lazy Evaluation（惰性求值）

```python
class ConditionalNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "condition": ("BOOLEAN",),
                "if_true": ("IMAGE", {"lazy": True}),   # 惰性
                "if_false": ("IMAGE", {"lazy": True}),   # 惰性
            }
        }
    
    def execute(self, condition, if_true=None, if_false=None):
        if condition:
            if if_true is None:
                # 请求执行该输入的上游节点
                return ExecutionBlocker("if_true")
            return (if_true,)
        else:
            if if_false is None:
                return ExecutionBlocker("if_false")
            return (if_false,)
```

Lazy 输入不会自动触发上游计算，只有节点显式请求时才执行。这是 ComfyUI 实现条件分支的关键机制。

### 5.3 前端通信（PromptServer.send_sync）

```python
from server import PromptServer

class MyNode:
    def execute(self, ...):
        # 向前端发送实时消息
        PromptServer.instance.send_sync(
            "my_custom_event",     # 事件类型（自定义字符串）
            {"message": "done!"}   # 数据
        )
        return (result,)
```

前端 JS 通过 WebSocket 监听：
```javascript
app.api.addEventListener("my_custom_event", (event) => {
    console.log(event.detail.message);
});
```

### 5.4 自定义路由

```python
from server import PromptServer
from aiohttp import web

routes = PromptServer.instance.routes

@routes.post('/my_custom_endpoint')
async def handler(request):
    data = await request.post()
    return web.json_response({"status": "ok"})
```

---

## 6. graph.py 执行图核心数据结构

### 6.1 DynamicPrompt

```python
class DynamicPrompt:
    """
    管理执行图的数据结构。
    
    - original_prompt: 用户提交的原始工作流 JSON
    - ephemeral_prompt: 执行过程中动态生成的临时节点
    - ephemeral_parents: 临时节点到父节点的映射
    """
```

支持"临时节点"（ephemeral nodes）是 ComfyUI 实现某些高级功能（如循环、动态子图）的基础。

### 6.2 TopologicalSort（拓扑排序）

```python
class TopologicalSort:
    """
    基于依赖关系的节点调度器。
    
    核心数据结构：
    - pendingNodes: 待执行的节点集合
    - blockCount[node_id]: 该节点被多少个上游节点阻塞
    - blocking[node_id]: 该节点阻塞了哪些下游节点
    """
```

工作流程：
```
1. add_node(output_node) → 从输出节点开始，递归添加所有依赖节点
2. 对每条依赖边 (from → to)：
   - blocking[from][to] = True
   - blockCount[to] += 1
3. get_ready_nodes() → 返回 blockCount == 0 的节点（无依赖，可执行）
4. pop_node(executed) → 执行完毕后减少下游节点的 blockCount
5. 重复 3-4 直到所有节点执行完毕
```

### 6.3 ExecutionList（执行列表）

继承自 TopologicalSort，增加了：

1. **缓存感知**：`is_cached(node_id)` 检查输出缓存，已缓存的节点直接跳过
2. **执行缓存**：为即将执行的节点预缓存上游输出
3. **UX 友好调度**：`ux_friendly_pick_node` 优先执行以下节点：
   - **异步节点**（`inspect.iscoroutinefunction`）→ 早执行可减少总时间
   - **输出节点**（`OUTPUT_NODE == True`）→ 用户尽早看到结果
   - **输出节点的前一跳**（如 VAEDecode → PreviewImage）
4. **循环检测**：`get_nodes_in_cycle` 在发现死锁时分析循环路径

```python
def ux_friendly_pick_node(self, node_list):
    """
    优先级：
    1. 输出节点或异步节点
    2. 直接阻塞输出节点的节点（如 VAEDecode）
    3. 间接阻塞输出节点的节点（如 VAELoader）
    4. 默认取第一个
    """
```

### 6.4 get_input_info 函数

```python
def get_input_info(class_def, input_name, valid_inputs=None):
    """
    查询某个节点某个输入的类型信息。
    
    返回: (input_type, category, extra_info)
    - input_type: "IMAGE", "FLOAT", "MODEL" 等
    - category: "required" | "optional" | "hidden"
    - extra_info: {"default": ..., "min": ..., "lazy": True, ...}
    """
```

这个函数被 TopologicalSort 在构建依赖图时大量使用，特别是判断 `lazy` 属性来决定是否建立强依赖边。

---

## 7. 关键源码文件索引

| 文件 | 职责 | 核心类/函数 |
|------|------|------------|
| `nodes.py` | 内置节点定义 + NODE_CLASS_MAPPINGS | CLIPTextEncode, KSampler, SaveImage, etc. |
| `execution.py` | 执行引擎 + 队列管理 | PromptExecutor, PromptQueue, validate_prompt |
| `comfy_execution/graph.py` | 执行图数据结构 | DynamicPrompt, TopologicalSort, ExecutionList |
| `comfy_execution/graph_utils.py` | 工具函数 | is_link, ExecutionBlocker |
| `server.py` | HTTP/WS 服务器 | PromptServer |
| `folder_paths.py` | 路径管理 | 模型/输入/输出目录解析 |
| `app/custom_node_manager.py` | 自定义节点管理 | CustomNodeManager (翻译/模板/路由) |
| `comfy/comfy_types/` | 类型系统 | IO 枚举, ComfyNodeABC, InputTypeDict |

---

## 8. 本节学习要点总结

### 节点注册核心公式

```
一个合法的 ComfyUI 节点 = 
    INPUT_TYPES(@classmethod) 
    + RETURN_TYPES(tuple) 
    + FUNCTION(str → method name) 
    + CATEGORY(str)
    + 注册到 NODE_CLASS_MAPPINGS
```

### 执行流程核心链路

```
POST /prompt (JSON workflow)
    → validate_prompt (类型检查 + DAG 验证)
    → PromptQueue.put (入队)
    → PromptExecutor.execute (出队执行)
        → TopologicalSort.add_node (从输出节点反向构建依赖图)
        → ExecutionList.stage_node_execution (UX 优先级调度)
        → 检查缓存 → 调用 node.FUNCTION(**inputs)
        → 结果存入 output_cache
        → WebSocket 推送进度 (executing/progress/executed)
    → 返回结果到 /history/{prompt_id}
```

### 自定义节点开发最小模板

```python
# my_node.py
class MyNode:
    CATEGORY = "my_category"
    
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"value": ("INT", {"default": 0})}}
    
    RETURN_TYPES = ("INT",)
    FUNCTION = "run"
    
    def run(self, value):
        return (value * 2,)

# __init__.py
from .my_node import MyNode
NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Custom Node"}
```
