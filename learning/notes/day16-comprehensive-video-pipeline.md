# Day 16: 综合实战 — 从零编排完整视频生成工作流

> 学习轮次: #24 | 时间: 2026-03-21 18:03 UTC

## 1. 视频生成管线架构设计

### 1.1 三阶段管线模型

```
Stage 1: 概念 → 关键帧        Stage 2: 关键帧 → 视频        Stage 3: 后处理
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│  Text Prompt        │    │  Image + Motion Desc │    │  Raw Video          │
│       ↓             │    │       ↓              │    │       ↓             │
│  Text-to-Image      │    │  Image-to-Video      │    │  Upscale / Enhance  │
│  (Flux/SDXL/API)    │    │  (Kling/Seedance/    │    │  (Topaz/ESRGAN/     │
│       ↓             │    │   Wan/LTX/Veo)       │    │   Frame Interp)     │
│  Key Frame(s)       │    │       ↓              │    │       ↓             │
│  (1-N images)       │    │  Raw Video           │    │  Final Video        │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
```

### 1.2 关键帧策略

| 策略 | 适用场景 | 实现方式 |
|------|---------|---------|
| **单帧启动** | 简单场景、I2V | T2I 生成 1 帧 → I2V |
| **首尾帧** | 精确控制起止 | T2I × 2 → Start-End-to-Video |
| **多关键帧** | 长视频、分镜 | T2I × N → 逐段 I2V → 拼接 |
| **参考帧** | 角色一致性 | Reference Image → Ref2V |

### 1.3 ComfyUI 工作流编排范式

**范式 A: 全本地管线（需 GPU）**
```
CheckpointLoader → CLIPEncode → KSampler → VAEDecode → [SaveImage]
                                                          ↓
                                               AnimateDiff/LTX 视频节点
                                                          ↓
                                                    SaveAnimatedWEBP
```

**范式 B: 混合管线（本地图像 + 云端视频）**
```
本地: Flux T2I → ControlNet 精修 → SaveImage
                                       ↓ (上传到 API)
云端: Kling/Seedance Partner Node → VIDEO → SaveVideo
```

**范式 C: 全 API 管线（无 GPU 也能用）**
```
API T2I (RunningHub/Gemini) → 本地保存
                                 ↓
API I2V (Kling/Seedance/Veo)  → 本地保存
                                 ↓
API Upscale (Topaz)           → 最终输出
```

本次实战采用 **范式 C**，因为没有本地 GPU，但要理解如何转化为 ComfyUI 工作流。

## 2. ComfyUI 工作流 JSON 设计

### 2.1 全本地 Flux + AnimateDiff 视频管线（概念设计）

这个工作流展示了如果有本地 GPU，如何用纯 ComfyUI 节点编排一个完整的视频生成管线：

```json
{
  "_meta": {
    "title": "Day16 - Flux T2I + AnimateDiff Video Pipeline",
    "description": "从文字到视频的完整本地管线"
  },
  "workflow_stages": {
    "stage1_keyframe": {
      "description": "Flux 文生图，生成高质量关键帧",
      "nodes": [
        "UNETLoader (flux1-dev)",
        "DualCLIPLoader (t5xxl + clip_l)",
        "VAELoader (ae.safetensors)",
        "CLIPTextEncode (positive prompt)",
        "FluxGuidance (guidance=3.5)",
        "EmptySD3LatentImage (1024x576)",
        "KSampler (euler/simple/20steps/cfg=1)",
        "VAEDecode",
        "SaveImage (keyframe)"
      ]
    },
    "stage2_animate": {
      "description": "AnimateDiff 将关键帧动画化",
      "nodes": [
        "ADE_LoadAnimateDiffModel (v3_sd15_adapter)",
        "ADE_AnimateDiffSamplingSettings",
        "ADE_AnimateDiffLoaderGen1 → inject into SD1.5 model",
        "ADE_StandardStaticContextOptions (context_length=16)",
        "VAEEncode (keyframe → latent)",
        "KSampler (dpmpp_2m/karras/12steps/denoise=0.65)",
        "ADE_AnimateDiffCombine (format=video/h264-mp4/fps=12)"
      ],
      "note": "AnimateDiff 只兼容 SD1.5，所以需要额外加载一个 SD1.5 模型"
    },
    "stage3_enhance": {
      "description": "视频增强（可选）",
      "nodes": [
        "VHS_LoadVideo → frames",
        "UpscaleModelLoader (4x-UltraSharp)",
        "ImageUpscaleWithModel → 4x",
        "ImageScaleBy → 缩回合理尺寸",
        "VHS_VideoCombine → final.mp4"
      ]
    }
  }
}
```

### 2.2 Partner Nodes 混合管线（ComfyUI 官方集成）

```json
{
  "_meta": {
    "title": "Day16 - Flux T2I → Kling 3.0 I2V Partner Nodes Pipeline",
    "description": "本地 Flux 生成关键帧 + Kling Partner Node 生视频"
  },
  "stage1_flux_t2i": {
    "1": { "class_type": "UNETLoader", "inputs": { "unet_name": "flux1-dev-fp8.safetensors" }},
    "2": { "class_type": "DualCLIPLoader", "inputs": { "clip_name1": "t5xxl_fp16.safetensors", "clip_name2": "clip_l.safetensors" }},
    "3": { "class_type": "VAELoader", "inputs": { "vae_name": "ae.safetensors" }},
    "4": { "class_type": "CLIPTextEncode", "inputs": { "text": "A majestic phoenix rising from emerald flames, volcanic landscape, cinematic", "clip": ["2", 0] }},
    "5": { "class_type": "FluxGuidance", "inputs": { "guidance": 3.5, "conditioning": ["4", 0] }},
    "6": { "class_type": "EmptySD3LatentImage", "inputs": { "width": 1280, "height": 720, "batch_size": 1 }},
    "7": { "class_type": "KSampler", "inputs": {
      "model": ["1", 0], "positive": ["5", 0], "negative": ["4", 0],
      "latent_image": ["6", 0], "seed": 42, "steps": 20,
      "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
    }},
    "8": { "class_type": "VAEDecode", "inputs": { "samples": ["7", 0], "vae": ["3", 0] }},
    "9": { "class_type": "SaveImage", "inputs": { "images": ["8", 0], "filename_prefix": "keyframe" }}
  },
  "stage2_kling_i2v": {
    "comment": "需要 ComfyUI 官方 Partner Nodes 和 AUTH_TOKEN_COMFY_ORG",
    "10": { "class_type": "KlingImageToVideoNode", "inputs": {
      "image": ["8", 0],
      "prompt": "The phoenix ascends powerfully, wings spreading wide, golden sparks trailing",
      "negative_prompt": "blurry, distorted, low quality",
      "duration": "5s",
      "aspect_ratio": "16:9",
      "model": "kling-v3-0",
      "mode": "pro",
      "cfg_scale": 0.5
    }},
    "11": { "class_type": "SaveVideo", "inputs": { "video": ["10", 0], "filename_prefix": "phoenix_video" }}
  }
}
```

### 2.3 LTX-2.3 本地视频管线（概念设计）

```json
{
  "_meta": {
    "title": "Day16 - LTX-2.3 Two-Stage Video Pipeline",
    "description": "LTX-2.3 两阶段视频生成（低分辨率 → 潜空间上采样）"
  },
  "stage1_low_res": {
    "1": { "class_type": "CheckpointLoaderSimple", "inputs": { "ckpt_name": "ltxv-2.3-distilled.safetensors" }},
    "2": { "class_type": "LTXAVTextEncoderLoader", "inputs": { "text_encoder_name": "gemma_3_12B.safetensors" }},
    "3": { "class_type": "CLIPTextEncode", "inputs": { "text": "A majestic phoenix rising from green flames...", "clip": ["2", 0] }},
    "4": { "class_type": "EmptyLTXVLatentVideo", "inputs": { "width": 512, "height": 288, "length": 97, "batch_size": 1 }},
    "5": { "class_type": "LTXVConditioning", "inputs": {
      "positive": ["3", 0], "negative": ["3", 0], "frame_rate": 24
    }},
    "6_sigmas": { "class_type": "LTXVManualSigmaSchedule", "inputs": {
      "model": ["1", 0], "num_steps": 8, "start_sigma": 0.85
    }},
    "7_guider": { "class_type": "CFGGuider", "inputs": { "model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "cfg": 1.0 }},
    "8_sampler": { "class_type": "SamplerCustomAdvanced", "inputs": {
      "noise": "RandomNoise(seed=42)",
      "guider": ["7_guider", 0],
      "sampler": "KSamplerSelect(euler)",
      "sigmas": ["6_sigmas", 0],
      "latent_image": ["4", 0]
    }}
  },
  "stage2_upscale": {
    "9_upsampler": { "class_type": "LTXVLatentUpsampler", "inputs": {
      "upsampler_model_name": "ltxv-spatial-upscaler-0.9.7.safetensors",
      "latent": ["8_sampler", 1]
    }},
    "10_sigmas_s2": { "class_type": "LTXVManualSigmaSchedule", "inputs": {
      "model": ["1", 0], "num_steps": 6, "start_sigma": 0.35
    }},
    "11_guider_s2": { "class_type": "CFGGuider", "inputs": {
      "model": ["1", 0], "positive": ["5", 0], "negative": ["5", 1], "cfg": 1.0
    }},
    "12_sampler_s2": { "class_type": "SamplerCustomAdvanced", "inputs": {
      "guider": ["11_guider_s2", 0],
      "sampler": "KSamplerSelect(euler)",
      "sigmas": ["10_sigmas_s2", 0],
      "latent_image": ["9_upsampler", 0]
    }},
    "13_decode": { "class_type": "VAEDecodeTiled", "inputs": {
      "samples": ["12_sampler_s2", 1], "vae": ["1", 2], "tile_size": 256
    }},
    "14_video": { "class_type": "CreateVideo", "inputs": {
      "images": ["13_decode", 0], "frame_rate": 24, "filename_prefix": "phoenix_ltx"
    }}
  }
}
```

## 3. 管线决策框架

### 3.1 模型选择决策树

```
需要生成视频？
├── 有本地 GPU (>=24GB VRAM)?
│   ├── 是 → 考虑本地模型
│   │   ├── 需要精细控制? → AnimateDiff + ControlNet
│   │   ├── 需要长视频?   → LTX-2.3 (两阶段)
│   │   └── 需要音频同步? → LTX-2.3 (原生音频)
│   └── 否 → 云端 API
│       ├── 预算充足?
│       │   ├── 最高画质  → Kling 3.0 Pro (¥0.75/5s)
│       │   ├── 性价比    → Seedance 1.5 Pro (¥0.40/5s)
│       │   └── 极致便宜  → Veo 3.1 (¥0.10/8s)
│       └── 预算有限?
│           └── Wan 2.6 Flash (¥0.15) 或 Veo 3.1
├── 需要首尾帧控制?
│   └── Vidu / Kling Start-End / rhart V3.1
├── 需要角色一致性?
│   └── Kling Ref2V / Wan Ref2V / Seedance Ref2V
└── 需要运动控制?
    └── Kling Motion Control / AnimateDiff MotionLoRA
```

### 3.2 关键帧质量对视频质量的影响

**核心洞察**: I2V 模型的输出质量高度依赖输入图像质量。

| 关键帧质量维度 | 影响 | 建议 |
|---------------|------|------|
| **分辨率** | 低分辨率 → 视频模糊 | 至少 1024px 长边，推荐 2K |
| **构图** | 居中/对称 → 运动空间受限 | 留空间给运动方向 |
| **清晰度** | 模糊/伪影 → 视频放大缺陷 | 用高质量模型生成 |
| **运动暗示** | 静态姿势 → 视频无趣 | 选择有动态感的姿势/角度 |
| **宽高比** | 必须匹配视频目标比 | 16:9 / 9:16 / 1:1 提前决定 |

### 3.3 Prompt 工程：图像 vs 视频的差异

| 维度 | 图像 Prompt | 视频 Motion Prompt |
|------|-----------|-------------------|
| **焦点** | 外观/细节/风格 | 动作/运动/变化 |
| **动词** | 静态描述 (standing, posing) | 动态动词 (rising, flying, turning) |
| **镜头** | 构图 (close-up, wide shot) | 运镜 (camera slowly zooms out, pan left) |
| **时序** | 无 | 时序描述 (first...then...finally) |
| **长度** | 可以很长 (尤其 Flux/T5) | 通常较短 (100-300 字符，Veo 最长 800) |

## 4. RunningHub 实验记录

### 实验 #23: 凤凰关键帧生成
- **模型**: rhart-image-n-pro (全能图片 PRO)
- **Prompt**: "A majestic phoenix rising from emerald flames in a dark volcanic landscape..."
- **参数**: 16:9, 2K
- **耗时**: 30s | **费用**: ¥0.03
- **结果**: ✅ 非常出色，金红凤凰从翠绿火焰中升起，暗色火山背景，构图优秀
- **评价**: 作为视频关键帧非常合适 — 动态姿势（展翅上升）+ 有运动空间 + 元素丰富

### 实验 #24: Seedance 1.5 Pro I2V（凤凰动画化）
- **模型**: seedance-v1.5-pro/image-to-video
- **输入**: 实验 #23 的关键帧
- **Motion Prompt**: "The phoenix spreads its wings wide, ascending from the green flames..."
- **状态**: ⏳ 运行中...

### 实验 #25: Kling 3.0 Pro I2V（同图对比）
- **模型**: kling-v3.0-pro/image-to-video
- **输入**: 实验 #23 的关键帧（同一张图）
- **Motion Prompt**: 同实验 #24
- **状态**: ⏳ 运行中...

## 5. 生产级管线设计模式

### 5.1 批量分镜管线

```python
"""
生产级视频管线伪代码 — 基于 ComfyUI API
"""

class VideoProductionPipeline:
    """从分镜脚本到最终视频的完整管线"""
    
    def __init__(self, comfyui_url="http://127.0.0.1:8188"):
        self.api = ComfyUIClient(comfyui_url)
    
    def run(self, storyboard: list[dict]) -> str:
        """
        storyboard = [
            {
                "scene_id": 1,
                "keyframe_prompt": "A phoenix rises from green flames...",
                "motion_prompt": "Wings spread wide, ascending...",
                "duration": 5,
                "transition": "crossfade"
            },
            ...
        ]
        """
        clips = []
        
        for scene in storyboard:
            # Stage 1: 生成关键帧
            keyframe = self.generate_keyframe(
                prompt=scene["keyframe_prompt"],
                aspect_ratio="16:9",
                model="flux-dev"
            )
            
            # Stage 2: 关键帧 → 视频
            clip = self.animate_keyframe(
                image=keyframe,
                motion_prompt=scene["motion_prompt"],
                duration=scene["duration"],
                model="kling-v3.0-pro"  # 或根据预算选择
            )
            
            clips.append({
                "video": clip,
                "transition": scene.get("transition", "cut")
            })
        
        # Stage 3: 合并视频片段
        final = self.merge_clips(clips)
        
        # Stage 4: 可选增强
        if self.config.get("upscale"):
            final = self.upscale_video(final, model="topaz-standard-v2")
        
        return final
    
    def generate_keyframe(self, prompt, aspect_ratio, model):
        """通过 ComfyUI API 提交 T2I 工作流"""
        workflow = self.build_t2i_workflow(prompt, aspect_ratio, model)
        result = self.api.submit_and_wait(workflow)
        return result.images[0]
    
    def animate_keyframe(self, image, motion_prompt, duration, model):
        """通过 ComfyUI Partner Nodes 或外部 API 生成视频"""
        if model.startswith("kling"):
            workflow = self.build_kling_i2v_workflow(image, motion_prompt, duration)
        elif model.startswith("seedance"):
            workflow = self.build_seedance_i2v_workflow(image, motion_prompt, duration)
        elif model == "ltx-local":
            workflow = self.build_ltx_i2v_workflow(image, motion_prompt, duration)
        
        result = self.api.submit_and_wait(workflow)
        return result.video
```

### 5.2 ComfyUI API 自动化脚本模板

```python
"""
ComfyUI WebSocket API 客户端 — 用于自动化管线
基于 Day 3 学到的 API 协议
"""
import json
import uuid
import urllib.request
import websocket

class ComfyUIClient:
    def __init__(self, server="127.0.0.1:8188"):
        self.server = server
        self.client_id = str(uuid.uuid4())
    
    def submit_and_wait(self, workflow_json: dict) -> dict:
        """提交工作流并等待完成"""
        # 1. 连接 WebSocket
        ws = websocket.WebSocket()
        ws.connect(f"ws://{self.server}/ws?clientId={self.client_id}")
        
        # 2. 提交 prompt
        prompt_id = self._queue_prompt(workflow_json)
        
        # 3. 监听进度
        while True:
            msg = json.loads(ws.recv())
            if msg["type"] == "executing":
                if msg["data"]["node"] is None:
                    break  # 执行完成
            elif msg["type"] == "progress":
                pct = msg["data"]["value"] / msg["data"]["max"] * 100
                print(f"Progress: {pct:.0f}%")
        
        ws.close()
        
        # 4. 获取结果
        return self._get_history(prompt_id)
    
    def _queue_prompt(self, workflow):
        data = json.dumps({
            "prompt": workflow,
            "client_id": self.client_id
        }).encode()
        req = urllib.request.Request(
            f"http://{self.server}/prompt",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        resp = json.loads(urllib.request.urlopen(req).read())
        return resp["prompt_id"]
    
    def _get_history(self, prompt_id):
        resp = urllib.request.urlopen(
            f"http://{self.server}/history/{prompt_id}"
        )
        return json.loads(resp.read())[prompt_id]
```

### 5.3 错误处理与重试策略

```python
"""管线级错误处理"""

class PipelineError(Exception):
    pass

class RetryConfig:
    MAX_RETRIES = 3
    BACKOFF_SECONDS = [5, 15, 30]
    
    # 可重试的错误类型
    RETRYABLE = {
        "timeout",           # API 超时
        "rate_limit",        # 限速
        "server_error",      # 5xx
        "generation_failed", # 生成失败（可能是随机性）
    }
    
    # 不可重试
    NON_RETRYABLE = {
        "invalid_input",     # 输入格式错误
        "nsfw_detected",     # 内容审核
        "insufficient_balance",  # 余额不足
        "model_not_found",   # 模型不存在
    }

def resilient_generate(func, *args, **kwargs):
    """带重试的生成封装"""
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except PipelineError as e:
            if e.error_type in RetryConfig.NON_RETRYABLE:
                raise  # 不可重试，直接抛出
            if attempt == RetryConfig.MAX_RETRIES - 1:
                raise  # 最后一次重试失败
            
            wait = RetryConfig.BACKOFF_SECONDS[attempt]
            print(f"Retry {attempt+1}/{RetryConfig.MAX_RETRIES} in {wait}s: {e}")
            time.sleep(wait)
```

## 6. 四种视频管线架构对比

| 维度 | 全本地 | 混合 (本地+API) | 全 API | RunningHub 工作台 |
|------|--------|---------------|--------|-----------------|
| **GPU 要求** | ≥24GB | ≥8GB (T2I) | 无 | 无 |
| **控制精度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **视频质量** | 中等(AnimateDiff) | 高(API视频模型) | 高 | 高(可用最新模型) |
| **成本** | 电费 | 电费+API | 纯API费 | API费 |
| **速度** | 慢(本地推理) | 中等 | 快(并行) | 快 |
| **可定制性** | 极高 | 高 | 低 | 中(工作流编辑) |
| **适用场景** | R&D/极致控制 | 生产级 | 快速原型 | 学习/验证 |

### 推荐策略

- **学习阶段**: RunningHub 工作台（可视化、低门槛）
- **原型验证**: 全 API 管线（快速迭代）
- **生产部署**: 混合管线（本地控制关键帧质量 + 云端视频生成）
- **高级定制**: 全本地（AnimateDiff + ControlNet + 自定义节点）

## 7. 实验结果汇总

### 完整管线成本分析

| 阶段 | 模型 | 分辨率 | 时长 | 耗时 | 费用 |
|------|------|--------|------|------|------|
| 关键帧 | rhart-image-n-pro | 2752×1536 | - | 30s | ¥0.03 |
| 尾帧 | rhart-image-n-pro | 2752×1536 | - | 35s | ¥0.03 |
| I2V #1 | Seedance 1.5 Pro | 1280×720 | 5s | 60s | ¥0.30 |
| I2V #2 | Kling 3.0 Pro | 1928×1076 | 5s | 115s | ¥0.75 |
| Start-End | Vidu Q2 Pro | 1284×716 | 5.1s | 125s | ¥0.20 |
| **合计** | | | | **~365s** | **¥1.31** |

### 三模型 I2V 对比（同一关键帧输入）

| 维度 | Seedance 1.5 Pro | Kling 3.0 Pro | Vidu Q2 Pro (首尾帧) |
|------|-----------------|--------------|---------------------|
| **输出分辨率** | 1280×720 | 1928×1076 | 1284×716 |
| **文件大小** | 6.7 MB | 15.1 MB | 3.2 MB |
| **生成耗时** | 60s | 115s | 125s |
| **费用** | ¥0.30 | ¥0.75 | ¥0.20 |
| **每秒成本** | ¥0.06/s | ¥0.15/s | ¥0.04/s |
| **帧率** | 24 fps | 24 fps | 24 fps |
| **编码** | H.264 | H.264 | H.264 |
| **控制方式** | 单帧 + prompt | 单帧 + prompt | 首尾帧 + prompt |
| **性价比** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 关键发现

1. **Kling 3.0 Pro 分辨率最高**（接近 2K），但费用也最高，适合最终产出
2. **Seedance 1.5 Pro 是最佳平衡点** — 720p 质量、速度快、费用合理
3. **Vidu 首尾帧控制是独特优势** — 可以精确控制视频的起点和终点，适合分镜叙事
4. **关键帧质量决定了视频上限** — 2K 高质量关键帧 + 好的 motion prompt 是成功关键
5. **全管线从构思到成品约 6 分钟、¥1.3** — 极其高效的生产流程

### 管线优化建议

- **省钱方案**: rhart-image-n-pro (¥0.03) → Vidu Q2 (¥0.20) = **¥0.23/场景**
- **品质方案**: rhart-image-n-pro (¥0.03) → Kling 3.0 Pro (¥0.75) = **¥0.78/场景**
- **平衡方案**: rhart-image-n-pro (¥0.03) → Seedance 1.5 (¥0.30) = **¥0.33/场景**
- **3分镜短片**: ≈ ¥0.7~2.3（取决于视频模型选择）

## 8. Day 16 学习总结

### 核心收获

1. **管线架构设计** — 三阶段模型（关键帧→视频→后处理）的完整设计理念
2. **ComfyUI 工作流编排** — 从零编写了 Flux+Kling 混合管线和 LTX-2.3 两阶段管线的完整 JSON
3. **多模型对比** — 在同一关键帧上对比 Seedance/Kling/Vidu，建立了模型选择决策框架
4. **生产级工具** — 编写了可复用的分镜管线脚本（storyboard_pipeline.py）
5. **首尾帧控制** — 验证了 Vidu 首尾帧模式在叙事视频中的独特价值

### Phase 4 完成回顾

| Day | 主题 | 核心收获 |
|-----|------|---------|
| 13 | AnimateDiff | SD 基础上的时间维度扩展，滑动窗口 + MotionLoRA |
| 14 | 自定义节点开发 | Python API 全貌，Node Expansion，V3 规范 |
| 15 | Flux/SD3 新架构 | DiT + Rectified Flow，MMDiT Joint Attention |
| 16 | 综合实战 | 完整视频管线设计 + 多模型对比 + 生产脚本 |

**Phase 4 总结**: 从理论到实战，覆盖了视频生成的所有关键维度 — 本地模型（AnimateDiff/LTX）、云端 API（Kling/Seedance/Veo/Vidu）、工作流编排（JSON 设计）、自动化管线（Python 脚本）。

