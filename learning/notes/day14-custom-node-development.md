# Day 14: ComfyUI 自定义节点开发（Python API）

> 学习时间: 2026-03-21 14:03 UTC | 轮次: 22
> 实验: #21 (技术架构图生成)

---

## 1. 自定义节点基础架构

### 1.1 节点类的四个必需属性

每个 ComfyUI 自定义节点本质上是一个 Python 类，**必须**包含以下四个核心属性：

```python
class MyCustomNode:
    # 1. 在 Add Node 菜单中的分类路径
    CATEGORY = "my_category/subcategory"
    
    # 2. 输入定义（必须是 @classmethod）
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "mask": ("MASK",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
            }
        }
    
    # 3. 输出类型元组
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("processed_image",)  # 可选，标签名
    
    # 4. 执行函数名
    FUNCTION = "process"
    
    def process(self, image, strength, mask=None):
        result = image * strength
        return (result,)  # 必须返回元组，注意尾逗号！
```

**关键设计决策**：
- `INPUT_TYPES` 是 `@classmethod`，因为 ComfyUI 在运行时调用它来构建 UI（比如动态填充 checkpoint 下拉列表）
- `FUNCTION` 用字符串指向函数名，不是直接引用函数对象 — 允许 ComfyUI 按需调用
- 返回值必须是元组，即使只有一个输出也要 `return (result,)`

### 1.2 INPUT_TYPES 三级字典

```
INPUT_TYPES → dict
├── "required" → dict[str, tuple]    # 必须连接/设值
├── "optional" → dict[str, tuple]    # 可以不连接（函数里需默认值）
└── "hidden"   → dict[str, str]      # 特殊系统值注入
```

**输入定义格式**: `"name": (TYPE_STRING, OPTIONS_DICT)`

| TYPE_STRING | Python 类型 | OPTIONS 支持的 key |
|-------------|-------------|-------------------|
| `"IMAGE"` | `torch.Tensor [B,H,W,C]` | `forceInput`, `lazy` |
| `"LATENT"` | `dict{"samples": Tensor [B,C,H,W]}` | `forceInput` |
| `"MASK"` | `torch.Tensor [H,W]` 或 `[B,C,H,W]` | — |
| `"MODEL"` | `ModelPatcher` | — |
| `"CLIP"` | `CLIP` | — |
| `"VAE"` | `VAE` | — |
| `"CONDITIONING"` | `list[tuple]` | — |
| `"INT"` | `int` | `default`(必需), `min`, `max` |
| `"FLOAT"` | `float` | `default`(必需), `min`, `max`, `step` |
| `"STRING"` | `str` | `default`(必需), `multiline`, `placeholder`, `dynamicPrompts` |
| `"BOOLEAN"` | `bool` | `default`(必需), `label_on`, `label_off` |
| `"NOISE"` | `NoiseObject` | — |
| `"SAMPLER"` | `SamplerObject` | — |
| `"SIGMAS"` | `Tensor [steps+1]` | — |
| `"GUIDER"` | `callable` | — |
| `"AUDIO"` | `dict{"waveform": Tensor [B,C,T], "sample_rate": int}` | — |

**COMBO 类型**（下拉菜单）— 不用字符串声明，直接用列表：
```python
"mode": (["fast", "quality", "balanced"],)
```

**通用 OPTIONS**：
| Key | 作用 |
|-----|------|
| `defaultInput` | 默认显示为输入接口（而非 widget） |
| `forceInput` | 强制为输入接口，不可转回 widget |
| `lazy` | 声明为惰性求值输入 |
| `rawLink` | 接收链接引用而非实际值（用于 Node Expansion） |

### 1.3 Hidden Inputs 特殊值

```python
"hidden": {
    "unique_id": "UNIQUE_ID",      # 节点唯一 ID（用于前后端通信）
    "prompt": "PROMPT",            # 完整 prompt JSON
    "extra_pnginfo": "EXTRA_PNGINFO",  # PNG metadata 字典
    "dynprompt": "DYNPROMPT",      # DynamicPrompt（Node Expansion 用）
}
```

---

## 2. 节点注册与生命周期

### 2.1 目录结构

```
ComfyUI/custom_nodes/
└── my_node_pack/
    ├── __init__.py          # 入口：导出 NODE_CLASS_MAPPINGS
    ├── nodes.py             # 节点类定义
    ├── utils.py             # 工具函数
    ├── requirements.txt     # Python 依赖
    └── web/
        └── js/
            └── my_extension.js  # 前端 JS 扩展（可选）
```

### 2.2 __init__.py 标准模板

```python
from .nodes import MyNode1, MyNode2

# 必须导出 — ComfyUI 通过此发现节点
NODE_CLASS_MAPPINGS = {
    "MyNode1": MyNode1,      # key = 全局唯一名称
    "MyNode2": MyNode2,
}

# 可选 — 在 UI 中显示的友好名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode1": "My Node v1",
    "MyNode2": "My Node v2",
}

# 前端 JS 目录（可选）
WEB_DIRECTORY = "./web/js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

### 2.3 加载流程

```
ComfyUI 启动
  → 扫描 custom_nodes/ 目录
  → 对每个 Python module (含 __init__.py 的目录)：
    → import module
    → 检查是否导出 NODE_CLASS_MAPPINGS
    → 是 → 注册所有节点类
    → 否 / 导入报错 → 标记为加载失败（控制台报错，继续启动）
```

### 2.4 comfy-cli scaffold 快速创建

```bash
cd ComfyUI/custom_nodes
comfy node scaffold
# 交互式问答后自动生成完整目录结构
```

---

## 3. 执行控制机制

### 3.1 缓存与 IS_CHANGED

ComfyUI 的核心优势之一：**缓存系统**。只有输入/widget 变化的节点才会重新执行。

```python
class MyNode:
    OUTPUT_NODE = False  # 默认。设为 True = 标记为输出节点（总是执行）
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # 返回值与上次比较，不等则重新执行
        # ⚠️ 不要返回 True/False！True == True → 永远被认为"没变"
        
        # 永远重新执行：
        return float("NaN")  # NaN != NaN → 总是触发
        
        # 按文件内容判断：
        m = hashlib.sha256()
        with open(filepath, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()
```

**缓存工作原理**：
1. 识别所有 `OUTPUT_NODE = True` 的节点
2. 反向遍历依赖图
3. 对比每个节点的 `IS_CHANGED` 返回值
4. 只执行"变化链"上的节点

### 3.2 VALIDATE_INPUTS

```python
@classmethod
def VALIDATE_INPUTS(cls, foo, bar):
    # 在工作流执行前调用
    # 返回 True = 合法
    # 返回 str = 错误消息（阻止执行）
    if foo < 0:
        return "foo must be non-negative"
    return True

# 特殊：接收 input_types 参数 → 跳过默认类型验证
@classmethod
def VALIDATE_INPUTS(cls, input_types):
    if input_types["input1"] not in ("INT", "FLOAT"):
        return "input1 must be INT or FLOAT"
    return True
```

### 3.3 SEARCH_ALIASES

```python
SEARCH_ALIASES = ["text concat", "join text", "merge strings"]
# 在 /object_info API 返回中出现，帮助用户搜索节点
```

---

## 4. 高级特性

### 4.1 自定义数据类型

```python
# 定义：随便起个大写名字
class CheeseNode:
    RETURN_TYPES = ("CHEESE",)
    
    def make_cheese(self):
        return ({"type": "gouda", "age": 12},)  # 任何 Python 对象

class EatCheeseNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "my_cheese": ("CHEESE", {"forceInput": True}),
                # forceInput 必需：因为前端不知道 CHEESE 怎么渲染 widget
            }
        }
```

**前端自动限制**：CHEESE 输出只能连到 CHEESE 输入。

### 4.2 通配符输入（接受任何类型）

```python
@classmethod
def INPUT_TYPES(cls):
    return {"required": {"anything": ("*",{})}}

@classmethod
def VALIDATE_INPUTS(cls, input_types):
    return True  # 必须跳过类型验证
```

### 4.3 动态创建输入（ContainsAnyDict 技巧）

```python
class ContainsAnyDict(dict):
    def __contains__(self, key):
        return True  # 任何 key 都"存在"

@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {},
        "optional": ContainsAnyDict()  # 接受任意命名的输入
    }

def main_method(self, **kwargs):
    # 所有动态输入都在 kwargs 里
    for name, value in kwargs.items():
        print(f"Dynamic input: {name} = {value}")
```

### 4.4 Lazy Evaluation（惰性求值）

```python
class LazyMixImages:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE", {"lazy": True}),   # 标记为惰性
                "image2": ("IMAGE", {"lazy": True}),
                "mask": ("MASK",),                       # 非惰性，总是求值
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "mix"
    
    def check_lazy_status(self, mask, image1, image2):
        """执行前调用，返回需要求值的惰性输入名列表"""
        needed = []
        if image1 is None and mask.min() != 1.0:
            needed.append("image1")
        if image2 is None and mask.max() != 0.0:
            needed.append("image2")
        return needed  # 空列表 = 所有需要的输入已就绪
    
    def mix(self, mask, image1, image2):
        if mask.min() == 0.0 and mask.max() == 0.0:
            return (image1,)
        return (image1 * (1 - mask) + image2 * mask,)
```

**惰性求值的价值**：避免不必要的上游计算。比如 Switch 节点只需评估选中的分支。

### 4.5 ExecutionBlocker（执行阻断）

```python
from comfy_execution.graph import ExecutionBlocker

def conditional_output(self, image, enabled):
    if not enabled:
        return (ExecutionBlocker(None),)  # 静默阻断
    return (image,)

# 带错误消息的阻断
vae = ExecutionBlocker(f"No VAE in model {ckpt_name}")  # 下游节点会显示此错误
```

**传播规则**：ExecutionBlocker 会沿连接线向前传播，**无法中断**。需要条件执行应用 Lazy Evaluation。

### 4.6 Node Expansion（节点展开）

高级技巧：一个节点在执行时"展开"为一组子节点。

```python
def load_and_merge(self, ckpt1, ckpt2, ratio):
    from comfy_execution.graph_utils import GraphBuilder
    graph = GraphBuilder()
    
    # 在子图中创建节点
    loader1 = graph.node("CheckpointLoaderSimple", checkpoint_path=ckpt1)
    loader2 = graph.node("CheckpointLoaderSimple", checkpoint_path=ckpt2)
    merge = graph.node("ModelMergeSimple", 
                        model1=loader1.out(0), 
                        model2=loader2.out(0), 
                        ratio=ratio)
    
    return {
        "result": (merge.out(0), loader1.out(1), loader1.out(2)),
        "expand": graph.finalize(),  # 子图 JSON
    }
```

**优势**：子图中的每个节点独立缓存。改变 ckpt2 不需要重新加载 ckpt1。

### 4.7 List 处理（INPUT_IS_LIST / OUTPUT_IS_LIST）

```python
class ImageRebatch:
    INPUT_IS_LIST = True          # 接收完整列表而非逐个
    OUTPUT_IS_LIST = (True,)      # 输出也是列表
    
    def rebatch(self, images, batch_size):
        batch_size = batch_size[0]  # INPUT_IS_LIST 下所有输入都是列表
        output = []
        all_imgs = [img[i:i+1] for img in images for i in range(img.shape[0])]
        for i in range(0, len(all_imgs), batch_size):
            output.append(torch.cat(all_imgs[i:i+batch_size], dim=0))
        return (output,)
```

**默认行为**（无 INPUT_IS_LIST）：ComfyUI 自动对列表中的每个元素调用函数一次。

---

## 5. 前后端通信

### 5.1 Server → Client（send_sync）

```python
from server import PromptServer

class MyNode:
    def process(self, image):
        # ... 处理逻辑 ...
        PromptServer.instance.send_sync(
            "my.custom.event",           # 消息类型（全局唯一）
            {"message": "Done!", "stats": {"time": 1.5}}
        )
        return (result,)
```

### 5.2 Client → Server（自定义 HTTP 路由）

```python
from server import PromptServer
from aiohttp import web

routes = PromptServer.instance.routes

@routes.post('/my_custom_api')
async def handle_request(request):
    data = await request.post()  # FormData → dict
    result = MyNode.process_request(data)
    return web.json_response({"status": "ok", "result": result})

@routes.get('/my_custom_status')
async def get_status(request):
    return web.json_response({"running": True})
```

### 5.3 前端 JS 扩展

```javascript
// web/js/myExtension.js
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "my.custom.extension",
    
    async setup() {
        // 监听后端消息
        app.api.addEventListener("my.custom.event", (event) => {
            console.log(event.detail.message);
        });
    },
    
    async nodeCreated(node) {
        // 节点被创建时的钩子
        if (node.comfyClass === "MyCustomNode") {
            // 添加自定义 widget
        }
    }
});
```

⚠️ `WEB_DIRECTORY` 只会serve `.js` 文件，不能用 `.css` 等。

---

## 6. ComfyUI 内置 API 路由一览

| 路由 | 方法 | 用途 |
|------|------|------|
| `/prompt` | POST | 提交工作流到执行队列 |
| `/prompt` | GET | 获取队列状态 |
| `/ws` | WebSocket | 实时通信（进度/状态/错误） |
| `/history` | GET | 获取执行历史 |
| `/history/{id}` | GET | 获取特定 prompt 历史 |
| `/object_info` | GET | 获取所有节点类型详情 |
| `/object_info/{class}` | GET | 获取单个节点类型详情 |
| `/view` | GET | 查看生成的图片 |
| `/upload/image` | POST | 上传图片 |
| `/upload/mask` | POST | 上传遮罩 |
| `/queue` | GET | 获取队列状态 |
| `/queue` | POST | 管理队列（清除等） |
| `/interrupt` | POST | 中断当前执行 |
| `/free` | POST | 释放显存 |
| `/system_stats` | GET | 系统信息 |
| `/models` | GET | 可用模型类型列表 |
| `/models/{folder}` | GET | 特定目录下的模型列表 |
| `/embeddings` | GET | 可用 embedding 列表 |
| `/extensions` | GET | 已注册扩展列表 |

**WebSocket 消息类型**：
- `status` — 系统状态更新
- `execution_start` — prompt 开始执行
- `execution_cached` — 使用缓存结果
- `executing` — 节点执行中（含 node_id）
- `progress` — 进度百分比
- `executed` — 节点完成（含输出数据）

---

## 7. Nodes V3 — 下一代节点规范（进行中）

### 7.1 V3 解决的核心问题

| 问题 | V1 现状 | V3 方案 |
|------|---------|---------|
| 稳定性 | 内部/公共 API 无分离，小更新可能破坏节点 | 版本化公共 API，向后兼容保证 |
| 依赖冲突 | 不同节点包的 Python 依赖可能冲突 | 进程隔离 |
| 动态 I/O | 可以实现但脆弱 | 一等公民支持 |
| 模型管理 | 手动管理本地模型 | 自动检测+存储组织 |
| 未来扩展 | 单进程串行执行 | async/await + 分布式/并行 |

### 7.2 V3 Schema 对比

```python
# V1（当前）
class TestNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"

# V3（提议中，可能变化）
class TestNode:
    @classmethod
    def DEFINE_SCHEMA(cls):
        return Schema(
            inputs=[ImageInput("image")],
            outputs=[ImageOutput("processed_image")]
        )
```

### 7.3 API 版本化

```python
from comfy_api.v0_0_3 import ComfyAPI  # 固定版本
api = ComfyAPI()
await api.set_progress(0.5)  # async-ready
```

### 7.4 Nodes 2.0 Vue 迁移（2026 年进行中）

ComfyUI 正在将前端从 **LiteGraph.js（Canvas 渲染）** 迁移到 **Vue.js（组件渲染）**：

**变化**：
- 节点 widget 从 canvas 像素绘制 → 真实 DOM 组件
- 下拉菜单、文本输入、滑块等成为原生 HTML 元素
- 支持复杂 UI：嵌入预览、交互曲线、实时直方图
- 已迁移的节点类型：Audio Encoder、GITS、Differential Diffusion、PAG、Morphology、Torch Compile 等

**影响**：
- 现有工作流向后兼容（可正常加载）
- 自定义节点的 **Python 后端**基本不变
- 自定义节点的 **JS 前端**需要重写（从 LiteGraph canvas code → Vue 组件）
- 纯后端节点（标准 widget）自动受益，几乎免费迁移

---

## 8. 真实世界模式：流行节点包分析

### 8.1 常见架构模式

**模式 1: API 代理节点**（如 Partner Nodes / fal-API）
```python
class APINode:
    def execute(self, prompt, api_key):
        response = requests.post(API_URL, json={"prompt": prompt}, headers={"Authorization": api_key})
        # 轮询等待结果
        result = self.poll_for_result(response["task_id"])
        # 下载并转换为 tensor
        image = self.download_and_convert(result["url"])
        return (image,)
```

**模式 2: 图像处理管线节点**（如 WAS Node Suite）
```python
class ImageProcessor:
    def process(self, images):
        # tensor → PIL → 处理 → tensor
        pil_images = [tensor_to_pil(img) for img in images]
        processed = [apply_filter(img) for img in pil_images]
        return (torch.stack([pil_to_tensor(img) for img in processed]),)
```

**模式 3: 条件路由节点**（如 Impact Pack）
```python
class SwitchNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"condition": ("BOOLEAN",{"default": True})},
            "optional": {
                "if_true": ("*", {"lazy": True}),
                "if_false": ("*", {"lazy": True}),
            }
        }
    
    def check_lazy_status(self, condition, if_true, if_false):
        if condition and if_true is None:
            return ["if_true"]
        if not condition and if_false is None:
            return ["if_false"]
        return []
```

**模式 4: 模型加载/修补节点**（如 ControlNet / LoRA loader）
```python
class ModelPatchNode:
    def apply(self, model, clip, strength):
        model_clone = model.clone()  # 必须 clone，不修改原始
        # 通过 model_options / patch 系统注入修改
        model_clone.set_model_patch(my_patch, "attn1")
        clip_clone = clip.clone()
        return (model_clone, clip_clone)
```

### 8.2 最佳实践总结

| 实践 | 说明 |
|------|------|
| 始终 clone model/clip | 不要修改输入的 model 对象 |
| 用 `forceInput` 处理自定义类型 | 前端不知道怎么渲染自定义类型的 widget |
| optional 输入在函数中给默认值 | `def func(self, required_in, optional_in=None)` |
| Tensor 形状保持一致 | IMAGE=[B,H,W,C], LATENT=dict, MASK=[H,W]或[B,C,H,W] |
| 惰性求值用于条件分支 | 避免不必要的上游计算 |
| seed 输入替代随机数 | 保证可复现性 + 正确缓存 |
| 错误返回 str 不返回 raise | `VALIDATE_INPUTS` 返回错误字符串 |
| JS 文件放 web/js/ | 不要手动复制到 Comfy web 目录 |

---

## 9. 实验 #21: 技术架构图生成

**目的**: 用 RunningHub API 生成 ComfyUI 节点架构概念图
- **端点**: `rhart-image-n-pro/text-to-image`
- **Prompt**: "A detailed technical diagram showing ComfyUI node architecture: multiple connected nodes with input/output sockets, data flowing through connections, a custom Python node highlighted in blue with INPUT_TYPES, RETURN_TYPES, FUNCTION labels, clean minimal style, dark background, neon blue and green accent lines, isometric 3D view"
- **参数**: 16:9 / 1K
- **结果**: 25s / ¥0.03
- **输出**: `/tmp/rh-output/day14-custom-node-architecture.jpg`
- **观察**: 文生图模型对"技术架构图"的理解偏向视觉风格化而非精确技术表达，实际的技术图应该用代码/SVG 生成

---

## 10. 关键洞察与模式总结

### 10.1 ComfyUI 节点系统的优雅设计

1. **类型系统即连接约束**: 前端通过类型字符串阻止无效连接，简单有效
2. **延迟应用模式**: model.clone() + set_patch 不是立即修改权重，而是记录操作，执行时才应用
3. **缓存驱动执行**: 不是"执行所有节点"，而是"只执行变化的部分"
4. **惰性求值 + 阻断传播**: 两种互补的执行控制机制
5. **Node Expansion**: 一个节点运行时动态生成子图 — 实现宏/循环/条件

### 10.2 开发自定义节点的心智模型

```
你的节点 = 数据变换函数
├── 输入: 类型化的数据（tensor/model/config...）
├── 输出: 变换后的数据（元组）
├── UI: 由 INPUT_TYPES 声明自动生成
├── 缓存: 由 IS_CHANGED 控制
├── 验证: 由 VALIDATE_INPUTS 控制
└── 执行: 在拓扑排序后由引擎调度
```

你不需要关心：
- 连接线的渲染（前端处理）
- 执行顺序（引擎拓扑排序）
- 缓存管理（引擎自动）
- 数据传递（引擎自动 wrap/unwrap）

你需要关心：
- 输入/输出类型正确匹配
- Tensor 形状符合约定 [B,H,W,C]
- 不修改输入对象（clone first）
- 返回值是元组（别忘尾逗号）
