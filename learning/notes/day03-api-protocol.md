# Day 3 补充: ComfyUI API 调用流程 — WebSocket / REST / 队列管理

> 学习时间: 2026-03-19 06:03 UTC  
> 来源: server.py 源码 + ComfyUI 官方文档 + 生产部署最佳实践  
> 轮次: Session 5

---

## 1. API 架构总览

ComfyUI 基于 **aiohttp** 实现了一个轻量级 Web 服务器，支持 REST API + WebSocket 双通道通信。

```
┌────────────────────────────────────────────────────┐
│  客户端（前端/脚本/API调用方）                        │
│                                                      │
│  ┌──────────────┐  ┌────────────────────────────┐   │
│  │ REST API     │  │ WebSocket (/ws)             │   │
│  │ POST /prompt │  │ 实时双向通信                 │   │
│  │ GET /history │  │ ← status/executing/progress │   │
│  │ GET /view    │  │ ← executed/error            │   │
│  │ POST /upload │  │ → feature_flags             │   │
│  └──────┬───────┘  └──────────┬─────────────────┘   │
│         │                     │                       │
│  ┌──────┴─────────────────────┴──────────────────┐   │
│  │            PromptServer (server.py)            │   │
│  │  - aiohttp 异步 HTTP 框架                      │   │
│  │  - 路由注册 / 中间件链 / 连接管理               │   │
│  └──────────────────┬────────────────────────────┘   │
│                     │                                  │
│  ┌──────────────────┴────────────────────────────┐   │
│  │  PromptQueue (execution.py)                   │   │
│  │  - 优先级队列 (heapq)                          │   │
│  │  - 并发控制 / 取消任务                          │   │
│  └──────────────────┬────────────────────────────┘   │
│                     │                                  │
│  ┌──────────────────┴────────────────────────────┐   │
│  │  PromptExecutor (execution.py)                │   │
│  │  - 执行引擎（拓扑排序 + 缓存 + 节点调度）       │   │
│  └───────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

---

## 2. REST API 端点详解

### 2.1 核心端点

#### POST /prompt — 提交工作流执行

```python
# 请求体
{
    "prompt": {        # workflow_api.json 格式的工作流
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "model": ["4", 0],      # [node_id, output_index] = 连线
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}
        },
        // ... 其他节点
    },
    "client_id": "abc123",    # 可选，WebSocket session 标识
    "extra_data": {            # 可选，额外元数据
        "extra_pnginfo": {}    # 会写入生成图片的元数据
    }
}

# 成功响应
{
    "prompt_id": "550e8400-e29b-41d4-a716-446655440000",
    "number": 1  # 在队列中的位置
}

# 验证失败响应
{
    "error": "Prompt validation error",
    "node_errors": {
        "3": [{"type": "value_not_in_range", "message": "..."}]
    }
}
```

**内部流程**：
```
1. 接收 JSON → 解析 prompt + client_id + extra_data
2. validate_prompt() → 类型检查 + 环检测 + 自定义验证
3. 触发 on_prompt_handlers（自定义节点可注册钩子）
4. PromptQueue.put() → 入队（带优先级编号）
5. 返回 prompt_id 给客户端
```

#### GET /prompt — 查询队列状态

```python
# 响应
{
    "exec_info": {
        "queue_remaining": 2  # 队列中剩余任务数
    }
}
```

#### GET /history/{prompt_id} — 获取执行结果

```python
# 响应
{
    "550e8400-...": {
        "prompt": [/* 原始 prompt 信息 */],
        "outputs": {
            "9": {  # node_id
                "images": [
                    {
                        "filename": "ComfyUI_00001_.png",
                        "subfolder": "",
                        "type": "output"  # "output" | "temp"
                    }
                ]
            }
        },
        "status": {
            "status_str": "success",
            "completed": true,
            "messages": [
                ["execution_start", {"prompt_id": "..."}],
                ["execution_cached", {"nodes": ["4", "5"]}],
                ["executing", {"node": "3", ...}],
                // ...
            ]
        }
    }
}
```

#### GET /view — 获取生成的图片

```
GET /view?filename=ComfyUI_00001_.png&subfolder=&type=output

参数：
  filename: 文件名
  subfolder: 子目录（可选）
  type: "input" | "output" | "temp"
  preview: "webp;90" 格式请求预览（可选）
  channel: "rgba" | "rgb" | "a"（可选）

返回：图片二进制数据
```

#### POST /upload/image — 上传图片

```python
# multipart/form-data
# 字段：
#   image: 文件
#   type: "input" | "temp" | "output"
#   subfolder: 子目录（可选）
#   overwrite: "true" | "false"

# 响应
{
    "name": "uploaded_image.png",
    "subfolder": "",
    "type": "input"
}
```

### 2.2 辅助端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/queue` | GET | 获取当前队列状态（running + pending） |
| `/queue` | POST | 管理队列：`{"clear": true}` 或 `{"delete": [id1, id2]}` |
| `/interrupt` | POST | 中断当前执行的 workflow |
| `/free` | POST | 释放内存：`{"unload_models": true, "free_memory": true}` |
| `/object_info` | GET | 获取所有节点类型的详细定义（输入/输出/分类等） |
| `/object_info/{class}` | GET | 获取特定节点类型的定义 |
| `/system_stats` | GET | 系统信息（GPU/RAM/版本等） |
| `/models` | GET | 可用模型类型列表 |
| `/models/{folder}` | GET | 特定类型的模型文件列表 |
| `/embeddings` | GET | 可用 embedding 列表 |

---

## 3. WebSocket 通信协议

### 3.1 连接建立

```javascript
// 客户端连接
const clientId = crypto.randomUUID().replace(/-/g, '');
const ws = new WebSocket(`ws://127.0.0.1:8188/ws?clientId=${clientId}`);

// 连接后立即收到 status 消息
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    // message.type + message.data
};
```

**服务端连接处理** (server.py)：
```python
@routes.get('/ws')
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # 获取或生成 session id
    sid = request.rel_url.query.get('clientId', '') or uuid.uuid4().hex
    self.sockets[sid] = ws
    
    # 发送初始状态
    await self.send("status", {"status": self.get_queue_info(), "sid": sid}, sid)
    
    # 如果是重连且正在执行，发送当前节点
    if self.client_id == sid and self.last_node_id is not None:
        await self.send("executing", {"node": self.last_node_id}, sid)
    
    # Feature flags 协商（首条消息）
    # 客户端发送 {"type": "feature_flags", "data": {...}}
    # 服务端回复 {"type": "feature_flags", "data": server_features}
```

### 3.2 消息类型详解

#### 服务端 → 客户端

| 消息类型 | 触发时机 | data 结构 | 说明 |
|---------|---------|-----------|------|
| `status` | 队列状态变化 | `{status: {exec_info: {queue_remaining: N}}}` | 队列剩余任务数 |
| `execution_start` | prompt 开始执行 | `{prompt_id}` | 执行开始 |
| `execution_cached` | 缓存命中的节点 | `{nodes: ["id1", "id2"], prompt_id}` | 列出所有走缓存的节点 |
| `executing` | 节点开始执行 | `{node, display_node, prompt_id}` | node=null 表示执行完毕 |
| `progress` | 长任务进度 | `{value, max, prompt_id, node}` | KSampler 步数进度等 |
| `executed` | 节点执行完成 | `{node, display_node, output, prompt_id}` | output 含 UI 数据 |
| `execution_error` | 执行出错 | `{prompt_id, node_id, node_type, exception_message, traceback, ...}` | 详细错误信息 |
| `execution_interrupted` | 被用户中断 | `{prompt_id, node_id, node_type, executed}` | 中断信息 |

#### 客户端 → 服务端

| 消息类型 | 说明 |
|---------|------|
| `feature_flags` | 首次连接时发送，协商客户端能力 |

### 3.3 二进制消息 (BinaryEventTypes)

ComfyUI 还支持通过 WebSocket 发送二进制数据（图片预览等）：

```python
class BinaryEventTypes:
    PREVIEW_IMAGE = 1  # 实时预览图
    UNENCODED_PREVIEW_IMAGE = 2  # 未编码预览图
```

二进制消息格式：
```
[4 bytes: event_type (uint32)] [payload bytes]
```

用于 KSampler 执行过程中的实时去噪预览（latent preview），效率远高于 JSON 编码图片。

### 3.4 完整的执行生命周期消息流

```
Client                          Server
  │                                │
  │─── POST /prompt ──────────────→│
  │←── {prompt_id, number} ────────│
  │                                │
  │←── status {queue_remaining:1} ─│  (入队)
  │                                │
  │←── execution_start ────────────│  (开始执行)
  │                                │
  │←── execution_cached ───────────│  (列出缓存命中节点)
  │    {nodes: ["4","5","6"]}      │
  │                                │
  │←── executing {node:"3"} ───────│  (KSampler 开始)
  │                                │
  │←── progress {value:1,max:20} ──│  (步骤 1/20)
  │←── [binary: preview_image] ────│  (实时预览)
  │←── progress {value:2,max:20} ──│  (步骤 2/20)
  │←── [binary: preview_image] ────│  
  │    ... (重复 20 步) ...         │
  │                                │
  │←── executing {node:"8"} ───────│  (VAEDecode 开始)
  │                                │
  │←── executed {node:"8",...} ────│  (VAEDecode 完成)
  │                                │
  │←── executing {node:"9"} ───────│  (SaveImage 开始)
  │←── executed {node:"9",         │
  │      output:{images:[...]}} ───│  (SaveImage 完成，含图片信息)
  │                                │
  │←── executing {node:null} ──────│  (整个 prompt 执行完毕)
  │                                │
  │←── status {queue_remaining:0} ─│  (队列空了)
  │                                │
  │─── GET /view?filename=... ────→│  (下载生成的图片)
  │←── [image binary] ─────────────│
```

---

## 4. 队列管理 (PromptQueue)

### 4.1 队列结构

```python
class PromptQueue:
    def __init__(self, server):
        self.server = server
        self.mutex = threading.RLock()
        self.not_empty = threading.Condition(self.mutex)
        self.task_counter = 0
        self.queue = []  # heapq，按 (number, task_id, ...) 排序
        self.currently_running = {}  # prompt_id → task_item
        self.history = {}  # prompt_id → execution_result
        self.flags = {}
```

### 4.2 入队流程

```python
def put(self, item):
    """
    item = (number, prompt_id, prompt, extra_data, output_node_ids)
    
    使用 heapq 维护优先级队列，number 越小优先级越高。
    入队后通知等待中的执行线程。
    """
    with self.mutex:
        heapq.heappush(self.queue, item)
        self.server.queue_updated()  # WebSocket 推送 status
        self.not_empty.notify()
```

### 4.3 执行循环

```python
# PromptExecutor 的主循环（简化）
while True:
    item = queue.get()  # 阻塞等待
    prompt_id = item[1]
    prompt = item[2]
    
    try:
        # 执行 workflow
        await executor.execute(prompt, prompt_id, extra_data)
    except Exception as e:
        # 错误处理 + WebSocket 推送
        server.send_sync("execution_error", error_info)
    finally:
        queue.task_done(prompt_id, output_data)
```

### 4.4 队列操作

```python
# 清空等待中的任务
POST /queue {"clear": true}

# 删除特定任务
POST /queue {"delete": ["prompt_id_1", "prompt_id_2"]}

# 中断当前执行
POST /interrupt
# → nodes.interrupt_processing = True
# → 下次 before_node_execution() 检查时抛出 InterruptProcessingException
```

---

## 5. 中间件链

server.py 定义了多层中间件：

```python
middlewares = [
    cache_control,              # 静态资源缓存控制
    deprecation_warning,        # 旧 API 路径警告
    compress_body,              # gzip 压缩（可选）
    create_origin_only_middleware(),  # CSRF 防护
    # 或 create_cors_middleware()     # CORS（如果启用）
    create_block_external_middleware(),  # CSP 策略（如果启用）
    comfyui_manager.create_middleware(),  # Manager 插件（如果启用）
]
```

### CSRF 防护机制

```python
def create_origin_only_middleware():
    """
    当 Host 是 localhost 时：
    比较 Host 和 Origin header 的域名是否一致。
    
    防止恶意网站通过浏览器向 localhost:8188 发送请求
    （浏览器不阻止 POST 到 127.0.0.1 的跨域请求！）
    
    如果 Host ≠ Origin → 返回 403
    """
```

---

## 6. 生产部署的 API 使用模式

### 6.1 Python 客户端完整示例

```python
import websocket
import uuid
import json
import requests

SERVER = "127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())

def connect_ws():
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER}/ws?clientId={CLIENT_ID}")
    return ws

def queue_prompt(prompt):
    resp = requests.post(f"http://{SERVER}/prompt", json={
        "prompt": prompt,
        "client_id": CLIENT_ID
    })
    return resp.json()

def wait_for_completion(ws, prompt_id):
    """阻塞等待执行完成"""
    while True:
        msg = json.loads(ws.recv())
        
        if msg["type"] == "executing":
            if msg["data"]["node"] is None:
                # node=null → 执行完毕
                return True
        
        if msg["type"] == "execution_error":
            if msg["data"]["prompt_id"] == prompt_id:
                raise Exception(msg["data"]["exception_message"])

def get_results(prompt_id):
    resp = requests.get(f"http://{SERVER}/history/{prompt_id}")
    history = resp.json()
    outputs = history[prompt_id]["outputs"]
    
    images = []
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for img in node_output["images"]:
                data = requests.get(f"http://{SERVER}/view", params={
                    "filename": img["filename"],
                    "subfolder": img["subfolder"],
                    "type": img["type"]
                }).content
                images.append(data)
    return images

# 使用
ws = connect_ws()
result = queue_prompt(workflow_json)
prompt_id = result["prompt_id"]
wait_for_completion(ws, prompt_id)
images = get_results(prompt_id)
ws.close()
```

### 6.2 并发控制

ComfyUI 默认单线程执行（GPU 限制），队列自动串行化。多客户端并发提交时：

```
Client A: POST /prompt → queue position 1 → executing
Client B: POST /prompt → queue position 2 → waiting
Client C: POST /prompt → queue position 3 → waiting

Client A 完成 → Client B 开始 → Client C 等待
```

每个客户端通过各自的 WebSocket clientId 只接收自己相关的进度消息。

### 6.3 Jobs API（新版）

ComfyUI 新版引入了 Jobs API (`comfy_execution/jobs.py`)：

```python
# 获取所有 jobs
GET /api/jobs  → [{id, status, prompt_id, ...}]

# Job 状态
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"  
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

---

## 7. 安全考虑

### 7.1 默认暴露的风险

ComfyUI 默认绑定 `127.0.0.1:8188`，但如果用 `--listen 0.0.0.0`：

- 任何人可提交 workflow → 消耗 GPU 资源
- 任何人可上传文件 → 潜在安全风险
- 任何人可读取生成结果

### 7.2 内置保护

1. **Origin 检查**：localhost 环境下的 CSRF 防护
2. **路径穿越防护**：上传/下载时检查 `os.path.commonpath`
3. **CSP 策略**（可选）：`--disable-api-nodes` 启用严格 Content-Security-Policy
4. **上传大小限制**：`--max-upload-size` (默认 100MB)

### 7.3 生产建议

```
1. 使用反向代理（nginx/caddy）做认证
2. 不要暴露到公网
3. 如需公网访问，加 API key 认证层
4. 限制上传目录权限
5. 监控队列深度，防止 DoS
```

---

## 8. 关键要点总结

### API 调用最小流程

```
1. WebSocket 连接 /ws?clientId=xxx
2. POST /prompt → 获取 prompt_id
3. 监听 WebSocket → executing {node: null} = 完成
4. GET /history/{prompt_id} → 获取输出文件信息
5. GET /view?filename=xxx → 下载结果
```

### WebSocket 消息判断执行状态

```python
match msg["type"]:
    case "execution_start":    # 开始了
    case "execution_cached":   # 这些节点走缓存
    case "executing":
        if msg["data"]["node"] is None:
            # 执行完毕！
        else:
            # 正在执行某个节点
    case "progress":           # 步数进度
    case "executed":           # 某个节点完成
    case "execution_error":    # 出错了
```
