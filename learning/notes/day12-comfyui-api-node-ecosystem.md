# Day 12: ComfyUI API 节点体系 — Partner Nodes / Kling / Seedance / Veo3.1 集成

> 学习时间: 2026-03-21 10:03 UTC | 轮次: 20

## 1. ComfyUI Partner Nodes 架构总览

### 1.1 什么是 Partner Nodes？

Partner Nodes 是 ComfyUI 官方（Comfy Org）内置的 API 节点系统，于 2025 年 5 月正式发布。它的核心设计理念是：

- **原生集成**：直接内置在 ComfyUI 代码仓库中，不需要安装第三方自定义节点
- **统一认证**：通过 Comfy 账号 + Credits 系统统一管理，用户无需维护多个 API Key
- **标准接口**：所有 Partner Nodes 共享统一的 `AUTH_TOKEN_COMFY_ORG` 认证机制
- **Opt-in 设计**：完全可选，`--disable-api-nodes` 可完全禁用

### 1.2 Partner Nodes 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   ComfyUI Frontend                   │
│         (Node Graph / Workflow Editor)                │
└─────────────────┬───────────────────────────────────┘
                  │ prompt API (/prompt)
                  ▼
┌─────────────────────────────────────────────────────┐
│               ComfyUI Execution Engine               │
│    (validate → topological sort → execute nodes)     │
└─────────────────┬───────────────────────────────────┘
                  │ Partner Node 执行
                  ▼
┌─────────────────────────────────────────────────────┐
│           Partner Node Base Classes                   │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │ ApiEndpoint   │  │ PollingOp    │                  │
│  │ (path/method) │  │ (poll loop)  │                  │
│  └──────┬───────┘  └──────┬───────┘                  │
│         │                  │                          │
│  ┌──────▼──────────────────▼──────┐                  │
│  │    SynchronousOperation        │                  │
│  │    (submit → poll → download)  │                  │
│  └────────────────┬───────────────┘                  │
└───────────────────┼─────────────────────────────────┘
                    │ HTTPS (via Comfy Org Proxy)
                    ▼
┌─────────────────────────────────────────────────────┐
│             Comfy Org API Gateway                     │
│    (认证/计费/路由/速率限制)                            │
└────────────┬──────────┬──────────┬──────────────────┘
             │          │          │
        ┌────▼───┐ ┌────▼───┐ ┌───▼────┐
        │ Kling  │ │ Veo3.1 │ │Seedance│  ...more
        │  API   │ │  API   │ │  API   │
        └────────┘ └────────┘ └────────┘
```

### 1.3 Partner Node 源码模式（以 Kling T2V 为例）

从源码分析，每个 Partner Node 遵循严格的三步模式：

```python
class KlingTextToVideoNode(KlingNodeBase):
    # Step 1: INPUT_TYPES — 声明参数
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ...,
                "model_name": ...,  # 例如 "kling-v2-master"
                "cfg_scale": ...,
                "duration": ...,
                "aspect_ratio": ...,
            },
            "hidden": {"auth_token": "AUTH_TOKEN_COMFY_ORG"},  # 关键！统一认证
        }
    
    RETURN_TYPES = ("VIDEO", "STRING", "STRING")  # VIDEO 是 ComfyUI 新增的原生类型
    
    # Step 2: api_call — 提交任务
    def api_call(self, prompt, ..., auth_token=None):
        # 2a. 提交初始请求
        initial_operation = SynchronousOperation(
            endpoint=ApiEndpoint(path=PATH_TEXT_TO_VIDEO, method=POST, ...),
            request=KlingText2VideoRequest(...),
            auth_token=auth_token,
        )
        initial_response = initial_operation.execute()
        
        # 2b. 轮询等待完成
        task_id = initial_response.data.task_id
        final_response = self.poll_for_task_status(task_id, auth_token)
        
        # 2c. 下载结果
        video = final_response.data.task_result.videos[0]
        return (download_url_to_video_output(video.url), ...)
    
    # Step 3: poll_for_task_status — 异步轮询
    @staticmethod
    def poll_for_task_status(task_id, auth_token):
        polling_operation = PollingOperation(
            poll_endpoint=ApiEndpoint(path=f"{PATH}/{task_id}", method=GET, ...),
            completed_statuses=["succeed"],
            failed_statuses=["failed"],
            status_extractor=lambda r: r.data.task_status.value,
            auth_token=auth_token,
        )
        return polling_operation.execute()
```

**关键设计模式**:
1. `AUTH_TOKEN_COMFY_ORG` — 隐藏参数，由 ComfyUI 前端自动注入
2. `SynchronousOperation` + `PollingOperation` — 提交-轮询二阶段
3. `VIDEO` 类型 — ComfyUI 2025.5 新增的原生数据类型（PR #7844）
4. `download_url_to_video_output()` — URL → VideoFromFile 转换

## 2. 视频生成 Partner Nodes 全景

### 2.1 当前支持的视频模型（截至 2026.03）

| 提供商 | 模型 | 节点名 | 功能 | 特色 |
|--------|------|--------|------|------|
| **Kling (快影)** | Kling 3.0 | KlingTextToVideo / KlingImageToVideo | T2V, I2V, 首尾帧, Motion Control | 3-15s / 声音生成 / Element Binding 面部一致性 |
| **Kling** | Kling 3.0 Motion Control | KlingMotionControl | 动作迁移 | 参考视频→角色动画 / 面部稳定 / 遮挡恢复 |
| **Google DeepMind** | Veo 3.1 | GoogleVeo3VideoGeneration | T2V, I2V | 8s / 电影级质量 / 长时间一致性 |
| **ByteDance** | Seedance Pro | SeedanceImageToVideo / SeedanceTextToVideo | T2V, I2V, 首尾帧控制 | 4-12s / 720p-1080p / 音频生成 / 相机固定 |
| **MiniMax** | Hailuo 2.3 | MiniMaxTextToVideo / MiniMaxImageToVideo | T2V, I2V | 海螺视频 |
| **Luma** | Ray 2 | LumaRay2 | T2V, I2V | 电影级 |
| **PixVerse** | V4 | PixVerseVideo | T2V, I2V | 特效 |
| **Pika** | 2.2 | PikaVideo | T2V, I2V | 创意视频 |
| **Wan (万相)** | 2.6 | WanTextToVideo / WanImageToVideo | T2V, I2V, Ref2V | 角色主演 / 多镜头叙事 / 音频同步 |

### 2.2 三大头部模型 ComfyUI 集成深度对比

#### Kling 3.0 Partner Node 体系

```
Kling Partner Nodes (内置):
├── Kling Text to Video          — T2V (kling-v2-master / kling-v3.0)
├── Kling Image to Video         — I2V (首帧/尾帧)
├── Kling Text to Video (Audio)  — T2V + 同步音频
├── Kling Image to Video (Audio) — I2V + 同步音频
├── Kling Motion Control         — 动作迁移 (3.0: Element Binding)
├── Kling Camera Control         — 镜头控制（预设运镜）
└── Kling Start-End to Video     — 首尾帧插值

关键参数:
- model_name: "kling-v2-master" / "kling-v3.0-std" / "kling-v3.0-pro"
- duration: 3-15 秒 (3.0)
- cfg_scale: 0.0-1.0 (注意: 不是传统的7.0, 这是归一化后的)
- sound: true/false (3.0 支持音频生成)
- mode: "std" / "pro"
```

**Kling 3.0 Motion Control 特色**:
- **Element Binding**: 面部一致性系统，多角度/多表情保持人物身份
- 输入: 参考图片 + 参考动作视频 → 输出: 角色按视频动作运动
- `characterOrientation`: "image"(保持图片朝向) / "video"(跟随视频朝向)
- 支持遮挡恢复（帽子/手遮挡面部时仍保持身份）

#### Seedance Pro Partner Node 体系

```
Seedance Partner Nodes (内置):
├── Seedance Text to Video       — T2V
├── Seedance Image to Video      — I2V
└── Seedance First-Last to Video — 首尾帧控制

关键参数:
- duration: 4-12 秒
- resolution: "480p" / "720p" / "1080p"
- aspectRatio: "16:9" / "9:16" / "1:1" / "4:3" / "3:4" / "21:9" / "adaptive"
- generateAudio: true/false
- cameraFixed: true/false (锁定相机 vs 自由运镜)
```

**Seedance vs Kling 差异**:
- Seedance 支持 `adaptive` 宽高比（自动匹配输入图）
- Seedance 支持 1080p 输出（Kling 3.0 默认 720p）
- Seedance 有 `cameraFixed` 选项控制相机运动
- Kling 有 Motion Control（Seedance 无此功能）

#### Veo 3.1 Partner Node

```
Google Veo Partner Nodes (内置):
└── Google Veo 3 Video Generation — T2V / I2V

关键参数:
- prompt: 文本描述
- model: "veo-3.1" (选择版本)
- 固定 8 秒时长

限制:
- 只有 16:9 / 9:16 两种宽高比
- prompt 上限 800 字符（远低于 Kling 的 5000）
- 无 Motion Control / 首尾帧控制
```

## 3. 第三方 API 节点生态（自定义节点）

除了官方 Partner Nodes，社区还有多个第三方集成方案：

### 3.1 主要第三方节点包

| 节点包 | API 后端 | 支持模型 | 特色 |
|--------|----------|----------|------|
| **ComfyUI-fal-API** | fal.ai | Kling/Runway/Luma/Flux/Seedance | 一个 API Key 统一多个模型 |
| **ComfyUI-Kie-API** | Kie.ai | Kling 3.0 (含实验性功能) | 社区驱动，更新快 |
| **ComfyUI-KLingAI-API** | Kling 官方 | Kling 全系列 | 官方维护 |
| **wavespeed-comfyui** | WaveSpeed | Seedance/ESRGAN/TTS/3D | 多模态 |
| **Comfly_Googel_Veo3** | Google AI | Veo 3.x | 非官方 Veo 封装 |
| **seedance_2_Comfy_UI_Node** | Sjinn.ai | Seedance 2.0 | 社区封装 |

### 3.2 Partner Nodes vs 第三方节点对比

| 维度 | Partner Nodes (官方) | 第三方自定义节点 |
|------|---------------------|-----------------|
| **安装** | 内置，无需安装 | 需 `custom_nodes/` 安装 |
| **认证** | Comfy 账号统一管理 | 各自 API Key |
| **计费** | Comfy Credits 预付费 | 各平台独立计费 |
| **更新** | 随 ComfyUI 更新 | 独立维护周期 |
| **安全** | 只允许 localhost/HTTPS | 无网络限制 |
| **自定义** | 参数固定 | 可 fork 修改 |
| **BYOK** | 计划支持但未实现 | 直接支持自己的 Key |
| **Headless** | 支持 API Key Integration | 直接支持 |

### 3.3 ComfyUI API Key Integration（Headless 调用）

对于无前端自动化场景，Partner Nodes 支持通过 API 提交：

```python
# 在 prompt 的 extra_data 中注入 API Key
payload = {
    "prompt": workflow_json,
    "extra_data": {
        "api_key_comfy_org": "your-comfy-api-key"
    }
}
requests.post("http://127.0.0.1:8188/prompt", json=payload)
```

这使得 ComfyUI 可以作为纯后端视频生成服务运行。

## 4. ComfyUI 视频工作流编排模式

### 4.1 三种视频生成集成层次

```
Layer 3: 封装 API 调用 (RunningHub / fal.ai / 直接 REST)
         └── 最简单，一行命令出视频，但无法组合工作流

Layer 2: ComfyUI Partner Nodes / 自定义 API 节点
         └── 在 ComfyUI 图中调 API，可与本地节点组合
         └── 例: LoadImage → ControlNet预处理 → Kling I2V → SaveVideo

Layer 1: 本地 ComfyUI 模型节点 (AnimateDiff / LTX / Wan)
         └── 完全本地，可深度定制每个参数
         └── 需要 GPU，但延迟低、可控性最强
```

### 4.2 混合工作流范式（Partner + Local）

ComfyUI 最强大的设计在于可以**混合使用云端 API 和本地模型**：

```
典型混合工作流:

[LoadImage] → [ControlNet Canny 预处理 (本地)] 
                                          ↘
                                    [Kling I2V (API)]
[CLIP Encode (本地)] ───────────────────↗        ↓
                                          [SaveVideo]

高级混合示例:
[GPT-Image-1 生成基础图 (API)] 
    → [Local ControlNet + IP-Adapter 增强 (本地)]
        → [Seedance I2V (API)] 
            → [Local ESRGAN 超分 (本地)]
                → [SaveVideo]
```

### 4.3 VIDEO 数据类型

ComfyUI 2025.5 新增的原生 `VIDEO` 类型（PR #7844）：

```python
# 视频相关核心类型
VIDEO       # 视频文件对象 (VideoFromFile)
IMAGE       # 图像张量 [B, H, W, C]
AUDIO       # 音频数据

# 视频工作流核心节点
LoadVideo          # 加载视频文件
SaveVideo          # 保存视频
VideoToFrames      # 视频→帧序列
FramesToVideo      # 帧序列→视频
LoadImage          # 可作为视频第一帧

# API 节点返回 VIDEO 类型，可直接连接：
[KlingI2V] ──VIDEO──→ [SaveVideo]
[KlingI2V] ──VIDEO──→ [VideoToFrames] ──IMAGE──→ [本地后处理]
```

## 5. 实验记录

### 实验 17: Kling 3.0 Pro I2V (samurai 动画化)

| 项目 | 值 |
|------|-----|
| 端点 | kling-v3.0-pro/image-to-video |
| 输入 | samurai-cliff.jpg (text2img 生成) |
| Prompt | "The samurai slowly sheathes his katana with a fluid motion, wind gusts blow his robes dramatically, camera slowly dollies in" |
| Duration | 5s |
| cfgScale | 0.5 |
| Sound | true |
| 耗时 | 150s |
| 成本 | ¥0.75 |
| 输出 | /tmp/rh-output/samurai-kling3-i2v.mp4 |

### 实验 18: Veo 3.1 Pro I2V (同一 samurai 图 → 对比)

| 项目 | 值 |
|------|-----|
| 端点 | rhart-video-v3.1-pro/image-to-video (=google/veo3.1-pro) |
| 输入 | 同上 samurai-cliff.jpg |
| Prompt | "The samurai slowly sheathes his katana, wind blows through robes, dramatic sunset, cinematic camera dolly in" |
| Duration | 8s (固定) |
| 耗时 | 125s |
| 成本 | ¥0.10 |
| 输出 | /tmp/rh-output/samurai-veo31-i2v.mp4 |

### Kling 3.0 vs Veo 3.1 对比分析

| 维度 | Kling 3.0 Pro | Veo 3.1 Pro |
|------|--------------|-------------|
| 时长灵活性 | 3-15s 可选 | 固定 8s |
| 宽高比 | 1:1, 16:9, 9:16 | 16:9, 9:16 |
| Prompt 上限 | 5000 字符 | 800 字符 |
| 音频生成 | ✅ 内置 | ❌ |
| Motion Control | ✅ 动作迁移+Element Binding | ❌ |
| 首尾帧控制 | ✅ | ❌ |
| CFG 控制 | ✅ 0-1 | ❌ |
| 生成速度 | 150s (5s视频) | 125s (8s视频) |
| API 成本 | ¥0.75/5s | ¥0.10/8s |
| ComfyUI 集成 | Partner Node (内置) | Partner Node (内置) |

**发现**: Veo 3.1 性价比极高（¥0.10/8s vs Kling ¥0.75/5s），但 Kling 在可控性上远超（Motion Control、音频、首尾帧、时长灵活性）。

## 6. 关键洞见与架构理解

### 6.1 Partner Nodes 的本质

Partner Nodes 本质上是 **ComfyUI 执行引擎内的异步 HTTP 客户端**。它将外部 API 的 "提交→轮询→下载" 模式封装为同步节点接口，使得 API 调用可以像本地计算一样参与图执行。

**核心抽象**:
- `ApiEndpoint` — 定义 REST 端点 (path + method + request/response model)
- `SynchronousOperation` — 提交任务并返回 task_id
- `PollingOperation` — 按状态轮询直到 succeed/failed
- `download_url_to_video_output()` — URL → 本地视频文件

### 6.2 为什么不只调 API？

bobooo 纠正过的核心观点: "不要只调封装 API，要理解底层 ComfyUI 工作流编排"

原因:
1. **组合能力**: API 只能单步调用，ComfyUI 图可以串联多步（预处理→生成→后处理）
2. **参数暴露**: ComfyUI 节点暴露了 API 不一定暴露的底层参数
3. **本地+云端混合**: 可以用本地 ControlNet 预处理 + 云端生成 + 本地超分
4. **批量自动化**: ComfyUI API (/prompt) 支持批量提交，Partner Nodes 自动处理轮询
5. **可复现性**: 工作流 JSON 完整记录参数，可分享/复现

### 6.3 集成层次选择建议

```
快速原型 → RunningHub API / fal.ai (一行命令)
生产管线 → ComfyUI Partner Nodes (图编排 + 自动化)
深度定制 → 本地模型节点 (AnimateDiff / LTX / Wan)
企业级   → ComfyUI API + Headless + 自定义节点
```

## 7. 下一步学习方向

- [ ] Day 13: AnimateDiff 运动模块 — 基于 SD 的本地视频生成
- [ ] ComfyUI 自定义 API 节点开发（写一个连接自己 API 的节点）
- [ ] Partner Node 批量自动化脚本（/prompt API + API Key Integration）
- [ ] Kling Motion Control 实操（需要参考动作视频素材）
