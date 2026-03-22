# Day 18: ComfyUI API 自动化 + 批量任务

> 学习时间: 2026-03-22 00:03 UTC | 轮次: 26 | 阶段: Phase 5

## 1. ComfyUI API 架构全景

### 1.1 核心 HTTP 端点（server.py 定义）

ComfyUI 内置的 HTTP API 是一个基于 aiohttp 的异步服务器，默认端口 8188。

```
核心端点:
┌─────────────────────────┬──────────┬────────────────────────────────────┐
│ 路径                     │ 方法     │ 用途                              │
├─────────────────────────┼──────────┼────────────────────────────────────┤
│ /prompt                  │ POST     │ 提交工作流到执行队列               │
│ /prompt                  │ GET      │ 获取当前队列状态                   │
│ /queue                   │ GET      │ 获取队列详情（pending + running）  │
│ /queue                   │ POST     │ 管理队列（清除 pending/running）   │
│ /history                 │ GET      │ 获取执行历史                       │
│ /history/{prompt_id}     │ GET      │ 获取特定 prompt 的执行结果         │
│ /history                 │ POST     │ 清除/删除历史记录                  │
│ /interrupt               │ POST     │ 中断当前执行                       │
│ /free                    │ POST     │ 释放显存（卸载模型）               │
│ /upload/image            │ POST     │ 上传图片到 input 目录              │
│ /upload/mask             │ POST     │ 上传遮罩                          │
│ /view                    │ GET      │ 查看/下载输出图片                  │
│ /object_info             │ GET      │ 获取所有节点类型的详细信息          │
│ /object_info/{class}     │ GET      │ 获取特定节点的参数规格              │
│ /system_stats            │ GET      │ 系统信息（Python/设备/显存）       │
│ /embeddings              │ GET      │ 可用 embeddings 列表              │
│ /extensions              │ GET      │ 已加载的扩展列表                   │
│ /models                  │ GET      │ 模型类型列表                       │
│ /models/{folder}         │ GET      │ 特定类型的模型文件列表              │
│ /ws                      │ WebSocket│ 实时双向通信                       │
└─────────────────────────┴──────────┴────────────────────────────────────┘
```

### 1.2 /prompt POST 请求格式

```json
{
    "prompt": {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 8566257,
                "steps": 20,
                "cfg": 8,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors"
            }
        }
        // ... 其他节点
    },
    "client_id": "unique-uuid-string",
    "prompt_id": "optional-custom-prompt-id",
    "extra_data": {
        "extra_pnginfo": { "workflow": {} }
    },
    "front": false,
    "number": 0
}
```

**关键字段说明**：
- `prompt`: 工作流 JSON（API 格式，node_id → {class_type, inputs}）
- `client_id`: WebSocket 关联的客户端 ID（用于接收特定客户端的更新）
- `prompt_id`: 可选的自定义 ID（不提供则自动生成 UUID）
- `extra_data`: 元数据，包含 workflow 信息用于 PNG 元数据嵌入
- `front`: true 则插到队列最前面
- `number`: 优先级数字（-1 = 使用当前最大 + 1）

### 1.3 WebSocket 消息协议

连接: `ws://{server}/ws?clientId={client_id}`

```
消息类型:
┌──────────────────────┬──────────────────────────────────────────────────┐
│ type                  │ 含义                                            │
├──────────────────────┼──────────────────────────────────────────────────┤
│ status                │ 系统状态（queue_remaining 等）                   │
│ execution_start       │ 开始执行一个 prompt                             │
│ execution_cached      │ 被缓存跳过的节点列表                            │
│ executing             │ 正在执行哪个节点（node=null 表示完成）           │
│ progress              │ 长操作进度（KSampler 步数等）                   │
│ executed              │ 节点执行完成，包含输出信息                       │
│ execution_success     │ 整个 prompt 执行成功                            │
│ execution_error       │ 执行出错，包含错误详情                           │
│ execution_interrupted │ 被用户中断                                      │
└──────────────────────┴──────────────────────────────────────────────────┘
```

**二进制消息**: 第 1-4 字节是 event type（int），5-8 字节是图片格式，8+ 字节是 latent preview 图片数据。

### 1.4 完整的 API 调用流程

```
1. 建立 WebSocket 连接
   ws://127.0.0.1:8188/ws?clientId=my-uuid

2. POST /prompt 提交工作流
   → 返回 { prompt_id, number }

3. 监听 WebSocket 消息
   ← status: {queue_remaining: 1}
   ← execution_start: {prompt_id: "xxx"}
   ← executing: {node: "4"} (CheckpointLoader)
   ← executing: {node: "6"} (CLIPTextEncode)
   ← executing: {node: "3"} (KSampler)
   ← progress: {value: 1, max: 20, prompt_id: "xxx", node: "3"}
   ← progress: {value: 2, max: 20, ...}
   ...
   ← executing: {node: "8"} (VAEDecode)
   ← executing: {node: "9"} (SaveImage)
   ← executed: {node: "9", output: {images: [...]}}
   ← executing: {node: null, prompt_id: "xxx"} → 执行完成信号！

4. GET /history/{prompt_id}
   → 获取输出结果（文件名、子目录、类型）

5. GET /view?filename=xxx&subfolder=&type=output
   → 下载输出图片
```

## 2. Python 自动化工具生态

### 2.1 官方示例 (ComfyUI/script_examples/)

官方提供了两个示例脚本：
- `websockets_api_example.py`: WebSocket + 历史查询方式
- `basic_api_example.py`: 纯 HTTP 轮询方式

**官方 WebSocket 示例核心模式**：

```python
import websocket, uuid, json, urllib.request

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

def queue_prompt(prompt, prompt_id):
    p = {"prompt": prompt, "client_id": client_id, "prompt_id": prompt_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    urllib.request.urlopen(req).read()

def get_images(ws, prompt):
    prompt_id = str(uuid.uuid4())
    queue_prompt(prompt, prompt_id)
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break  # 执行完成
        else:
            continue  # 二进制 = latent preview
    
    history = get_history(prompt_id)[prompt_id]
    # 从 history 中提取输出图片
```

### 2.2 第三方 Python 库对比

```
┌──────────────────────────┬─────────────────────────────────────────────────┐
│ 库名                      │ 特点                                           │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ comfyui-python-api        │ 轻量工具库，支持回调、进度、队列位置跟踪        │
│ (andreyryabtsev)          │ 适合聊天机器人集成，pip install comfyui_utils    │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ comfy-api-simplified      │ 简化的 API 封装，声明式工作流定义               │
│ (pypi)                    │ 适合快速原型，不需要直接操作 JSON               │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ ComfyUI-to-Python         │ 自定义节点，将 GUI 工作流导出为可运行 Python    │
│ (pydn)                    │ 适合从 GUI 到脚本的迁移，queue_size 参数控制    │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ comfy-nodekit             │ 类型安全的 Python 工作流构建，自动代码生成       │
│ (production-focused)      │ 适合生产环境，typed edges + 实时验证            │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ ComfyScript               │ 命令式 Python 语法写 ComfyUI 工作流            │
│                           │ 直接在 ComfyUI 运行时中执行，最接近原生         │
└──────────────────────────┴─────────────────────────────────────────────────┘
```

### 2.3 生产级部署方案

#### SaladTechnologies/comfyui-api
- **核心理念**: 将 ComfyUI 包装为无状态 API 服务
- **输出方式**:
  - 同步: 返回 base64 编码的图片
  - 异步: Webhook 回调（prompt.complete / prompt.failed）
  - 存储: S3 / Azure Blob / HuggingFace / HTTP
- **关键特性**: 
  - Warmup Workflow（启动预热）
  - Dynamic Model Loading（URL 自动缓存）
  - Swagger 文档（/docs）
  - 健康检查（/health, /ready）
  - LRU 缓存（控制本地存储）

#### BentoML/comfy-pack
- **核心理念**: 将 ComfyUI 工作流打包为可部署的 BentoService
- **特点**: 环境快照（节点+模型+配置）→ Docker 镜像 → 云部署
- **适合**: 需要完整环境一致性的生产部署

#### Cloud Platforms
- **RunComfy**: 工作流 = JSON + 环境 + 节点 + 模型，自动缩放 API
- **ViewComfy**: 工作流 → 可嵌入的 API 端点
- **Comfy.org Cloud**: 官方云 API（wss://cloud.comfy.org/ws）

## 3. 批量任务自动化模式

### 3.1 批量生成架构

```
                         ┌────────────────┐
                         │  任务数据源      │
                         │ CSV/JSON/DB/API │
                         └────────┬───────┘
                                  │
                         ┌────────▼───────┐
                         │  任务调度器      │
                         │ (Python Script) │
                         └────────┬───────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ 参数替换 + 提交  │ │ 参数替换 + 提交  │ │ 参数替换 + 提交  │
    │ (prompt 1)       │ │ (prompt 2)       │ │ (prompt N)       │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
             ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────────────┐
    │              ComfyUI Server (Queue)                      │
    │  WebSocket ← 进度/完成通知 → 客户端                       │
    └─────────────────────────────────────────────────────────┘
             │                   │                   │
             ▼                   ▼                   ▼
    ┌─────────────────────────────────────────────────────────┐
    │              输出处理（保存/上传/后处理）                  │
    └─────────────────────────────────────────────────────────┘
```

### 3.2 四种批量模式对比

```
┌────────────────────┬────────────────────────┬──────────┬───────────────┐
│ 模式                │ 实现方式                │ 并发     │ 适用场景       │
├────────────────────┼────────────────────────┼──────────┼───────────────┤
│ 1. 串行队列         │ for循环 + queue_prompt  │ 1        │ 简单批量       │
│ 2. 预提交队列       │ 一次性提交所有prompt    │ 队列深度  │ 大批量+单GPU   │
│ 3. 多WebSocket并行  │ 多client_id + 多连接    │ N个连接  │ 多GPU         │
│ 4. 分布式集群       │ 负载均衡多ComfyUI实例   │ M×N      │ 生产环境      │
└────────────────────┴────────────────────────┴──────────┴───────────────┘
```

### 3.3 参数扫描（Parameter Sweep）

常见扫描维度：
- **Seed sweep**: 同参数不同 seed，选最佳结果
- **CFG sweep**: CFG 从 1.0 到 15.0，步长 0.5
- **Sampler sweep**: euler/dpmpp_2m/dpmpp_sde 等对比
- **Prompt sweep**: 不同 prompt 变体
- **LoRA sweep**: LoRA strength 从 0.0 到 1.5
- **Resolution sweep**: 不同宽高比/分辨率

**XY Plot 节点**（GUI 方式）:
- ComfyUI 社区有 Efficiency Nodes 的 XY Plot 节点
- 自动生成参数网格对比图

### 3.4 错误处理与重试策略

```python
# 生产级重试模式
class BatchRunner:
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.results = []
        self.failures = []
    
    async def run_with_retry(self, prompt, job_id):
        for attempt in range(self.max_retries):
            try:
                result = await self.execute(prompt)
                self.results.append({"id": job_id, "result": result})
                return result
            except TimeoutError:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
            except Exception as e:
                if "CUDA out of memory" in str(e):
                    await self.free_memory()  # POST /free
                    continue
                raise
        self.failures.append({"id": job_id, "error": "max retries exceeded"})
```

**关键错误类型与处理**：
| 错误 | 处理策略 |
|------|---------|
| CUDA OOM | POST /free → 等待 → 重试 |
| WebSocket 断连 | 重新连接 + 从 /history 恢复状态 |
| 节点验证失败 | 记录错误，跳过该 prompt |
| 模型不存在 | 预检查 /models/{folder} |
| 队列满 | 等待 queue_remaining < 阈值再提交 |

## 4. 高级自动化技术

### 4.1 工作流动态修改

```python
def modify_workflow(workflow_json, modifications):
    """动态修改工作流参数
    
    modifications = {
        "6": {"inputs": {"text": "new prompt"}},      # 修改 prompt
        "3": {"inputs": {"seed": 12345, "steps": 30}}, # 修改采样参数
        "5": {"inputs": {"width": 1024, "height": 1024}},
    }
    """
    import copy
    wf = copy.deepcopy(workflow_json)
    for node_id, changes in modifications.items():
        if node_id in wf:
            for key, value in changes.get("inputs", {}).items():
                wf[node_id]["inputs"][key] = value
    return wf
```

### 4.2 图片上传 + Img2Img 批量

```python
def upload_image(image_path, server_address):
    """上传图片到 ComfyUI input 目录"""
    import requests
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/png')}
        data = {'overwrite': 'true'}
        response = requests.post(f"http://{server_address}/upload/image", 
                                files=files, data=data)
        return response.json()  # {"name": "uploaded_name.png", "subfolder": "", "type": "input"}

# 然后在工作流中引用
workflow["load_image_node"]["inputs"]["image"] = uploaded_name
```

### 4.3 ComfyUI Cloud API（官方云）

```python
# 官方 Cloud API 使用方式
import websocket, json

API_KEY = "your_comfy_org_api_key"

# WebSocket 连接（wss 协议）
ws = websocket.WebSocket()
ws.connect(f"wss://cloud.comfy.org/ws?clientId={client_id}&token={API_KEY}")

# 提交 prompt（带 token 认证）
headers = {"Authorization": f"Bearer {API_KEY}"}
# POST https://cloud.comfy.org/api/prompt
```

### 4.4 进度追踪 + 回调系统

```python
class ProgressTracker:
    """实时追踪批量任务进度"""
    
    def __init__(self, total_jobs):
        self.total = total_jobs
        self.completed = 0
        self.failed = 0
        self.current_node = None
        self.current_step = 0
        self.max_steps = 0
    
    def on_ws_message(self, message):
        msg = json.loads(message)
        msg_type = msg.get('type')
        data = msg.get('data', {})
        
        if msg_type == 'progress':
            self.current_step = data['value']
            self.max_steps = data['max']
            pct = self.current_step / self.max_steps * 100
            print(f"\r  [{self.completed+1}/{self.total}] "
                  f"Node {data['node']}: {pct:.0f}% "
                  f"({self.current_step}/{self.max_steps})", end='')
        
        elif msg_type == 'executing':
            if data['node'] is None:
                self.completed += 1
                print(f"\n✅ Job {self.completed}/{self.total} done")
            else:
                self.current_node = data['node']
        
        elif msg_type == 'execution_error':
            self.failed += 1
            print(f"\n❌ Job failed: {data.get('exception_message', 'unknown')}")
```

### 4.5 模型预检查 + 环境验证

```python
def verify_environment(server_address, workflow):
    """执行前验证环境"""
    
    # 1. 检查系统状态
    stats = requests.get(f"http://{server_address}/system_stats").json()
    gpu_free = stats['devices'][0]['vram_free'] / 1e9
    print(f"GPU Free VRAM: {gpu_free:.1f}GB")
    
    # 2. 检查所需模型是否存在
    required_models = extract_model_names(workflow)
    for model_type, name in required_models:
        available = requests.get(f"http://{server_address}/models/{model_type}").json()
        if name not in available:
            raise RuntimeError(f"Model not found: {model_type}/{name}")
    
    # 3. 检查所需节点类型是否存在
    required_nodes = set(n['class_type'] for n in workflow.values())
    object_info = requests.get(f"http://{server_address}/object_info").json()
    for node_type in required_nodes:
        if node_type not in object_info:
            raise RuntimeError(f"Node type not found: {node_type}")
    
    # 4. 验证工作流连接
    # POST /prompt 会返回 node_errors（不需要真正执行）
```

## 5. 实操实验

### 实验 #28: RunningHub API 批量自动化

**目标**: 用 Python 脚本批量调用 RunningHub API，同一主题三种风格

**批量任务定义**:
```python
batch_jobs = [
    {"name": "cyberpunk_dragon",  "prompt": "dragon on neon skyscraper, cyberpunk", "ratio": "16:9"},
    {"name": "watercolor_dragon", "prompt": "dragon in misty forest, watercolor",   "ratio": "1:1"},
    {"name": "scifi_dragon",      "prompt": "mechanical chrome dragon, steampunk",  "ratio": "9:16"},
]
```

**结果**:
| 任务 | 状态 | 耗时 | 宽高比 |
|------|------|------|--------|
| cyberpunk_dragon | ✅ 成功 | 24.7s | 16:9 |
| watercolor_dragon | ✅ 成功 | 24.2s | 1:1 |
| scifi_dragon | ✅ 成功 | 23.6s | 9:16 |

**总耗时**: 72.5s（3 张图，串行执行）
**成本**: ~¥0.03 × 3 = ¥0.09

**关键发现**:
- RunningHub API 响应稳定，每张 ~24s
- 串行 3 张总共 72.5s，平均 24.2s/张
- API 方式无法并行（共享账户限流），但足够用于小批量
- 对比 ComfyUI 原生 API: RunningHub 封装了底层 ComfyUI 细节，无需管理 WebSocket

## 6. ComfyUI API 格式 vs GUI 格式

### 6.1 两种 JSON 格式的区别

**GUI 格式**（Save 按钮导出）：
- 包含节点位置信息（x, y）
- 包含显示名称、颜色等 UI 元素
- 节点之间用 links 数组连接
- 文件通常更大

**API 格式**（Save API Format 导出）：
- 只有 class_type + inputs
- 连接用 ["node_id", output_index] 表示
- 无 UI 信息，纯逻辑
- **这是 /prompt POST 接受的格式**

### 6.2 格式转换

```python
def gui_to_api_format(gui_json):
    """将 GUI 格式转换为 API 格式（简化版）
    注意: ComfyUI UI 导出 API 格式时内部就是这个逻辑
    """
    api_prompt = {}
    nodes = gui_json.get("nodes", [])
    links = gui_json.get("links", [])
    
    # 构建 link 查找表: link_id → (from_node, from_slot)
    link_map = {}
    for link in links:
        link_id, from_node, from_slot, to_node, to_slot, link_type = link[:6]
        link_map[link_id] = (str(from_node), from_slot)
    
    for node in nodes:
        node_id = str(node["id"])
        inputs = {}
        
        # 处理 widget 值
        if "widgets_values" in node:
            # 需要对照 object_info 来映射 widget 值到参数名
            pass
        
        # 处理连接
        if "inputs" in node:
            for inp in node["inputs"]:
                if inp.get("link") is not None:
                    from_node, from_slot = link_map[inp["link"]]
                    inputs[inp["name"]] = [from_node, from_slot]
        
        api_prompt[node_id] = {
            "class_type": node["type"],
            "inputs": inputs
        }
    
    return api_prompt
```

## 7. 生产级批量生成脚本模板

参见 `sample-workflows/scripts/batch_api_runner.py`（同目录附带）。

核心特性：
1. CSV/JSON 批量任务定义
2. WebSocket 实时进度
3. 指数退避重试
4. CUDA OOM 自动恢复
5. 结果报告生成
6. 可选 webhook 回调

## 8. 总结与决策树

```
需要 ComfyUI 自动化？
├─ 单次/少量 → 直接用 GUI
├─ 10-100 张 → Python 脚本 + /prompt API
├─ 100-1000 张 → 批量脚本 + WebSocket 进度 + 重试
├─ 1000+ 张 → 分布式（多 ComfyUI 实例 + 负载均衡）
├─ 无 GPU → 云 API（RunningHub / Comfy Cloud / RunComfy）
└─ 生产 API → SaladTech/comfyui-api 或 BentoML/comfy-pack

选择 Python 库:
├─ 最轻量 → 直接 urllib + websocket-client（官方示例）
├─ 聊天机器人集成 → comfyui_utils（进度回调）
├─ 类型安全 → comfy-nodekit（typed workflow）
├─ GUI 迁移 → ComfyUI-to-Python（一键导出脚本）
└─ 命令式编程 → ComfyScript（Python 直接写工作流）
```
