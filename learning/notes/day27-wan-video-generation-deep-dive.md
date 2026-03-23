# Day 27: Wan 视频生成模型深度解析 — 从 2.1 到 2.2 + 开源视频本地工作流

> 学习时间: 2026-03-23 00:03 UTC | 轮次: 35
> 重点: Wan 全系列架构深度、ComfyUI 原生集成 vs kijai WanVideoWrapper、VACE 统一编辑模型、本地部署实操

---

## 1. Wan 模型系列全景（2025.03 — 2026.03）

### 1.1 版本演进时间线

```
2025.03  Wan 2.1 发布 — 首个开源大规模视频生成模型
         ├── T2V-1.3B（消费级 GPU，8.19GB VRAM）
         ├── T2V-14B（旗舰，65-80GB VRAM）
         └── I2V-14B-480P / I2V-14B-720P

2025.05  Wan 2.1 VACE — 统一视频创建与编辑模型
         ├── VACE-1.3B（480P）
         └── VACE-14B（480P + 720P）

2025.07  Wan 2.2 — MoE 架构升级
         ├── T2V-A14B（MoE, 27B total / 14B active）
         ├── I2V-A14B（MoE）
         └── TI2V-5B（混合模型，新 VAE 16×16×4 压缩比）

2025.08  Wan 2.2-S2V-14B — 音频驱动视频生成
2025.09  Wan 2.2-Animate-14B — 角色动画与替换
2025.09  Wan 2.5-Preview — 多模态音视频（API only）
2025.12  Wan 2.6 — 最新版本（API only，未开源权重）
         ├── T2V / I2V / Ref2V / I2V-Flash
         └── Reference-to-Video（参考视频生成）
```

### 1.2 关键里程碑

| 版本 | 核心创新 | 架构 | 开源权重 |
|------|---------|------|---------|
| 2.1 | Wan-VAE 3D 因果 VAE + 多尺度 DiT | Dense Transformer | ✅ 全部开源 |
| 2.1 VACE | 统一视频编辑框架 | Dense + Mask 条件 | ✅ 全部开源 |
| 2.2 | MoE 专家分离 + 新 VAE | Mixture-of-Experts | ✅ 全部开源 |
| 2.2-S2V | 音频驱动视频 + CosyVoice | S2V Pipeline | ✅ 开源 |
| 2.2-Animate | 角色动画替换 | Animate Pipeline | ✅ 开源 |
| 2.6 | 参考视频生成 + 商业级质量 | 未公开 | ❌ API Only |

---

## 2. Wan 2.1 架构深度解析

### 2.1 整体架构: 3D Causal VAE + DiT + UMT5

```
┌─────────────────────────────────────────────────────────────┐
│                    Wan 2.1 架构总览                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Text Prompt ──→ [UMT5-XXL] ──→ Text Embeddings            │
│                                    │                        │
│                                    ▼                        │
│  Input ──→ [Wan-VAE Encoder] ──→ Latent + Noise             │
│  (Image/                          │                         │
│   Video)                          ▼                         │
│                         [DiT Transformer]                   │
│                         (Flow Matching)                     │
│                                │                            │
│                                ▼                            │
│                     [Wan-VAE Decoder] ──→ Output Video      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Wan-VAE: 3D 因果变分自编码器

**核心创新: 3D Causal Convolution**

传统图像 VAE 使用 2D 卷积，只能处理空间维度。Wan-VAE 引入 **3D 因果卷积**:

```
传统 2D VAE:  [B, C, H, W] → 空间压缩 8×8
Wan-VAE:      [B, C, T, H, W] → 时空压缩 4×8×8

其中:
- T (时间): 压缩比 4（每 4 帧压缩为 1 个时间 token）
- H (高度): 压缩比 8
- W (宽度): 压缩比 8
- 总压缩比: 4 × 8 × 8 = 256
```

**因果性 (Causality)**: 
- 时间卷积只看当前帧和之前的帧，不看未来帧
- 保证第一帧可以独立编码（兼容图像输入）
- `causal_conv3d`: 在时间维度做 padding 只在左侧（past）

**Wan 2.1 VAE vs Wan 2.2 VAE**:

| 特性 | Wan 2.1 VAE | Wan 2.2 VAE (5B 专用) |
|------|------------|---------------------|
| 压缩比 | 4×8×8 = 256 | 4×16×16 = 1024 |
| 潜空间通道 | 16 | 16 |
| 适用模型 | 所有 2.1 + 2.2 14B | 仅 2.2 TI2V-5B |
| 分辨率 | 480P / 720P | 720P @ 24fps |

Wan 2.2 的 5B 模型使用 **16×16×4** 的超高压缩比 VAE（空间压缩 16 倍！），是目前开源视频模型中压缩比最高的，使得 5B 模型能在 RTX 4090 上运行。

### 2.3 UMT5-XXL 文本编码器

Wan 选择 **UMT5-XXL**（Universal mT5）而非 CLIP 或 T5-XXL:

```
为什么选 UMT5-XXL:
1. 多语言原生支持（中文/英文/日文等 101 种语言）
2. 比 T5-XXL 更好的跨语言泛化
3. 参数量 ~4.7B
4. 输出维度: 每 token 4096d
5. 最大 token 长度: 512 tokens

vs 其他视频模型的编码器选择:
- LTX-2.3: Gemma 3 12B（更大但单语言优势弱）
- CogVideoX: T5-XXL（英文为主）
- HunyuanVideo: mT5-XXL（类似选择）
- Flux: CLIP-L + T5-XXL（双编码器）
```

**ComfyUI 中的 UMT5 加载**:
- FP16 版: `umt5_xxl_fp16.safetensors`（~9.5GB）
- FP8 版: `umt5_xxl_fp8_e4m3fn_scaled.safetensors`（~4.8GB，推荐）

### 2.4 DiT 扩散骨干 (Flow Matching)

Wan 2.1 使用 **Diffusion Transformer + Flow Matching** 训练范式:

```
Flow Matching 核心公式:
  x_t = (1 - t) * x_0 + t * ε    （线性插值路径）
  v_θ(x_t, t) = ε - x_0           （速度场预测）

vs DDPM ε-prediction:
  x_t = √α_t * x_0 + √(1-α_t) * ε
  ε_θ(x_t, t) 预测噪声

Flow Matching 优势:
1. OT (Optimal Transport) 直线路径 → 更少采样步数
2. 误差累积少
3. CFG-free 推理可能（guidance 蒸馏）
```

**模型规格**:

| 变体 | 参数量 | 层数 | 隐藏维度 | 注意力头 | VRAM (720P) |
|------|--------|------|---------|---------|-------------|
| 1.3B | 1.3B | 30 | 1536 | 12 | 8-20 GB |
| 14B | 14B | 40 | 5120 | 40 | 65-80 GB |

---

## 3. Wan 2.2: MoE 架构革新

### 3.1 Mixture-of-Experts 核心思想

Wan 2.2 将 MoE 引入视频扩散模型，这是一个关键创新:

```
┌──────────────────────────────────────────────────────┐
│              Wan 2.2 MoE 架构                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  输入 x_t (带噪声)                                    │
│       │                                              │
│       ▼                                              │
│  计算 SNR(x_t) = signal / noise                      │
│       │                                              │
│       ├─ SNR < threshold ──→ [高噪声专家] (14B)       │
│       │                      处理: 整体布局/构图/主体  │
│       │                                              │
│       └─ SNR ≥ threshold ──→ [低噪声专家] (14B)       │
│                              处理: 细节/纹理/精炼     │
│                                                      │
│  注意: 切换点 = 噪声占比降低一半的时间步               │
│  总参数: 27B | 每步活跃: 14B                          │
│  推理成本 ≈ Wan 2.1 14B（相同 VRAM）                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**关键区别 vs 传统 MoE (如 Mixtral)**:
- 传统 MoE: 逐 token 路由到不同专家
- Wan 2.2 MoE: **按时间步切换专家**（不是逐 token）
- 基于 SNR 阈值确定切换点
- 每个扩散步只用一个专家

### 3.2 MoE 带来的改进

与 Wan 2.1 相比 (同时得益于更大训练数据):

```
训练数据增量:
- 图片: +65.6%
- 视频: +83.2%

三大改进:
1. 运动连贯性 ↑ — 物体/角色跨帧外观一致性更好
2. 指令遵循 ↑ — 复杂多主体提示更准确
3. 结构稳定性 ↑ — 相机运动/场景转换更平滑
```

### 3.3 Wan 2.2 模型文件体系

```
ComfyUI/models/
├── diffusion_models/
│   ├── wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors  # T2V 高噪声专家
│   ├── wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors   # T2V 低噪声专家
│   ├── wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors  # I2V 高噪声专家
│   ├── wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors   # I2V 低噪声专家
│   ├── wan2.2_ti2v_5B_fp16.safetensors                   # TI2V 5B (单模型)
│   ├── wan2.2_s2v_14B_bf16.safetensors                   # S2V 音频驱动
│   └── wan2.2_animate_14B.safetensors                    # Animate 角色动画
├── text_encoders/
│   └── umt5_xxl_fp8_e4m3fn_scaled.safetensors            # 共享编码器
└── vae/
    ├── wan_2.1_vae.safetensors                            # 14B 模型用
    └── wan2.2_vae.safetensors                             # 5B 模型用(新)
```

**注意**: 14B MoE 模型需要**同时加载两个专家权重文件**（high_noise + low_noise），ComfyUI 原生节点和 WanVideoWrapper 都支持自动管理。

---

## 4. Wan 2.1 VACE: 统一视频编辑框架

### 4.1 VACE 概述

VACE (Video-Aware Composable Editing) 是一个**全能视频编辑模型**:

```
VACE 支持的任务（单一模型）:
1. Text-to-Video — 文生视频
2. Image-to-Video — 图生视频
3. Video-to-Video — 视频转视频
4. Motion Transfer — 运动迁移
5. Local Replacement — 局部替换（mask + inpaint）
6. Video Extension — 视频扩展（outpainting）
7. Background Replacement — 背景替换
8. Reference-to-Video — 参考图生视频

多模态输入:
- 文本 (text prompt)
- 图像 (reference image)
- 视频 (source video)
- 蒙版 (mask)
- 控制信号 (control signals)
```

### 4.2 ComfyUI VACE 工作流

VACE 使用单一工作流模板，通过 **Bypass 不同节点** 实现不同任务:

```
核心节点拓扑:
Load Diffusion Model (wan2.1_vace_14B)
  │
  ├── Load CLIP (umt5_xxl)
  ├── Load VAE (wan_2.1_vae)
  │
  ├── [可 Bypass] Load Image → 图生视频
  ├── [可 Bypass] Load Video → 视频转视频  
  ├── [可 Bypass] Mask Input → 局部编辑
  ├── [可 Bypass] Control Signal → 控制条件
  │
  ├── CLIP Text Encode (Positive)
  ├── CLIP Text Encode (Negative)
  │
  └── WanVaceToVideo → SamplerCustomAdvanced → VAE Decode → Save Video
```

**性能参考 (RTX 4090)**:
- 720×1280, 81 帧: ~40 分钟
- 640×640, 49 帧: ~7 分钟

---

## 5. ComfyUI 集成: 原生 vs WanVideoWrapper

### 5.1 ComfyUI 原生节点

ComfyUI 自 2025 年 2 月起内置 Wan 支持:

```
原生 Wan 节点:
- Load Diffusion Model — 加载 Wan 权重
- Load CLIP (type: wan) — 加载 UMT5
- Load VAE — 加载 Wan-VAE
- EmptyHunyuanLatentVideo — 创建空视频潜空间
  (注: Wan 复用 HunyuanVideo 的 latent 格式)
- WanVaceToVideo — VACE 专用节点
- WanImageToVideo — I2V 专用条件节点
- WanFunInpaintToVideo — 视频修复
- SamplerCustomAdvanced — 统一采样器

Wan 2.2 新增:
- 支持加载两个 diffusion model (high/low noise expert)
- MoE 切换由采样器内部自动处理
```

### 5.2 kijai/ComfyUI-WanVideoWrapper

Kijai 的 WanVideoWrapper 是最活跃的第三方 Wan 节点包:

```
项目结构:
ComfyUI-WanVideoWrapper/
├── nodes.py                    # 主节点定义
├── nodes_model_loading.py      # 模型加载基础设施
├── wanvideo/
│   ├── modules/
│   │   ├── model.py           # WanModel transformer
│   │   ├── t5.py              # T5/UMT5 文本编码器
│   │   ├── clip.py            # CLIP 视觉编码器
│   │   └── attention.py       # 注意力机制
│   ├── schedulers.py          # 扩散调度器
│   └── wan_video_vae.py       # VAE 编码/解码
├── custom_linear.py           # FP8 量化层
├── gguf/                      # GGUF 量化支持
├── cache_methods/             # TeaCache, MagCache
├── multitalk/                 # MultiTalk 音频条件
├── lynx/                      # Lynx 面部控制
├── unianimate/                # UniAnimate 姿态控制
└── enhance_a_video/           # FETA/Enhance-A-Video
```

**WanVideoWrapper 独有优势**:
1. **前沿优化**: TeaCache / MagCache 加速（25-50% 速度提升）
2. **GGUF 量化**: 支持量化模型加载（更低 VRAM）
3. **FP8 缩放**: Kijai 自制的 fp8_scaled 权重
4. **高级功能**: 
   - Wan 2.2 Animate 支持
   - S2V 音频驱动视频
   - MultiTalk 多人对话
   - UniAnimate 姿态控制
   - Lynx 面部控制
   - Enhance-A-Video 质量增强
   - CausVid LoRA 步数蒸馏
5. **社区工作流**: 大量预制工作流 JSON

### 5.3 原生 vs WanVideoWrapper 对比

| 维度 | ComfyUI 原生 | WanVideoWrapper (kijai) |
|------|------------|----------------------|
| 维护者 | Comfy-Org 官方 | Kijai (社区) |
| 更新速度 | 稳定版发布 | 前沿快速迭代 |
| 模型支持 | Wan 2.1 / 2.2 基础 | 全系列 + Animate + S2V |
| 量化 | FP8 标准 | FP8 + GGUF + 自定义量化 |
| 缓存加速 | 无 | TeaCache / MagCache |
| 高级功能 | 基础 T2V/I2V/VACE | 姿态/面部/音频/增强 |
| 稳定性 | 高 | 中（前沿功能可能不稳定） |
| VRAM 优化 | 标准 | 更多选项（分块/量化/缓存） |
| 推荐场景 | 生产部署 | 实验/研究/最新功能 |

---

## 6. Wan 2.2 扩展模型

### 6.1 Wan 2.2-S2V-14B (Speech-to-Video)

音频驱动视频生成，2025 年 8 月发布:

```
S2V 管线:
  音频 (语音/音乐) + 参考图像
       │
       ▼
  [音频编码器] → 音频特征
       │
       ▼
  [S2V DiT] → 带唇同步的视频
       │
       ▼
  输出: 说话头/表演视频

特点:
- 自然的唇形同步
- 自然的身体运动
- 支持 CosyVoice TTS 集成
- 可处理语音和音乐输入
```

**ComfyUI 支持**:
- WanVideoWrapper: `wan2.2_s2v_14B_bf16.safetensors` → `diffusion_models/`
- 原生 ComfyUI: S2V 工作流模板（2025.08+）

### 6.2 Wan 2.2-Animate-14B

统一角色动画与替换模型，2025 年 9 月发布:

```
Animate 能力:
1. 角色动画 — 静态图像 → 自然运动视频
2. 角色替换 — 替换视频中的角色保持原有运动
3. 全身运动复制 — 表情 + 身体动作全复制
4. 灵活输入 — 支持多种参考图 + 目标视频组合

vs 其他角色方案:
- Kling Motion Control: 商业 API，仅动作迁移
- AnimateDiff: 本地但画质受限于 SD1.5
- Wan Animate: 开源 + 14B 画质 + 统一框架
```

### 6.3 Wan 2.6 (API Only)

2025 年 12 月发布，未开源权重:

```
Wan 2.6 端点 (RunningHub):
- alibaba/wan-2.6/text-to-video       — 文生视频
- alibaba/wan-2.6/image-to-video       — 图生视频
- alibaba/wan-2.6/image-to-video-flash — 图生视频(快速)
- alibaba/wan-2.6/reference-to-video   — 参考视频生成
- alibaba/wan-2.6/reference-to-video-flash — 参考视频(快速)

2.6 新特性:
- 参考视频生成（Reference-to-Video）
- 更好的运动质量
- 更精确的文本遵循
- Flash 版本 → 更快推理

2026.01 ComfyUI Blog: Wan 2.6 Ref2V 已支持 ComfyUI
```

---

## 7. 本地部署: GPU 需求与优化

### 7.1 VRAM 需求矩阵

| 模型 | 分辨率 | 时长 | VRAM | 推荐 GPU | 生成时间 |
|------|--------|------|------|---------|---------|
| 2.1/2.2 1.3B | 480P | 5s | 8-12 GB | RTX 4090 | ~2-3 min |
| 2.1/2.2 1.3B | 720P | 5s | 16-20 GB | RTX 4090 | ~4-5 min |
| 2.1/2.2 14B | 480P | 5s | 40-48 GB (FP8) | H100 PCIe | ~4-5 min |
| 2.1/2.2 14B | 720P | 5s | 65-80 GB | H100 SXM5 | ~10-12 min |
| 2.1/2.2 14B | 720P | 10s | 80+ GB | H200 | ~20+ min |
| 2.2 TI2V-5B | 720P@24fps | 5s | 8-16 GB | RTX 4090 | ~5-8 min |

### 7.2 部署优化策略

```
消费级 GPU (RTX 4090, 24GB):
1. 使用 1.3B 或 TI2V-5B 模型
2. FP8 量化编码器 → 省 ~5GB
3. VAE tiled decode → 省 ~2GB
4. 480P 优先（720P 可能 OOM）

数据中心 GPU (H100 80GB):
1. 14B 模型 FP8 → 适配 480P-720P
2. 不需要量化 VAE
3. SXM5 比 PCIe 快 ~25%（内存带宽 3.35 vs 2 TB/s）

前沿优化:
1. TeaCache (WanVideoWrapper) → 25-40% 加速
2. MagCache → 类似加速
3. CausVid LoRA → 步数蒸馏（4-8 步）
4. GGUF 量化 → 进一步降低 VRAM
5. LightX2V → 多种加速技术集成
6. FastVideo → 稀疏注意力加速
7. Cache-dit → DBCache + TaylorSeer + Cache CFG
```

### 7.3 本地部署成本对比

| 配置 | 每秒视频成本 | 每 5s 片段成本 |
|------|------------|--------------|
| RTX 4090 1.3B 480P | ~$0.008 | ~$0.04 |
| H100 SXM5 14B 720P (OD) | ~$0.084 | ~$0.42 |
| H100 SXM5 14B 720P (Spot) | ~$0.034 | ~$0.17 |
| RunningHub Wan 2.6 I2V | ~¥0.08/s | ~¥0.38/5s |

---

## 8. Wan 全系列 ComfyUI 工作流

### 8.1 Wan 2.1 基础 T2V (原生节点)

```json
{
  "3": {
    "class_type": "LoadDiffusionModel",
    "inputs": {
      "model_name": "wan2.1_t2v_14B_fp16.safetensors"
    }
  },
  "4": {
    "class_type": "CLIPLoader",
    "inputs": {
      "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
      "type": "wan"
    }
  },
  "5": {
    "class_type": "VAELoader",
    "inputs": {
      "vae_name": "wan_2.1_vae.safetensors"
    }
  },
  "6": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "A golden dragon soaring through misty mountains at sunset",
      "clip": ["4", 0]
    }
  },
  "7": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, distorted",
      "clip": ["4", 0]
    }
  },
  "8": {
    "class_type": "EmptyHunyuanLatentVideo",
    "inputs": {
      "width": 832,
      "height": 480,
      "length": 81,
      "batch_size": 1
    }
  },
  "10": {
    "class_type": "BasicGuider",
    "inputs": {
      "model": ["3", 0],
      "conditioning": ["6", 0]
    }
  },
  "11": {
    "class_type": "KSamplerSelect",
    "inputs": {
      "sampler_name": "euler"
    }
  },
  "12": {
    "class_type": "BasicScheduler",
    "inputs": {
      "model": ["3", 0],
      "scheduler": "simple",
      "steps": 30,
      "denoise": 1.0
    }
  },
  "13": {
    "class_type": "SamplerCustomAdvanced",
    "inputs": {
      "noise": ["14", 0],
      "guider": ["10", 0],
      "sampler": ["11", 0],
      "sigmas": ["12", 0],
      "latent_image": ["8", 0]
    }
  },
  "14": {
    "class_type": "RandomNoise",
    "inputs": { "noise_seed": 42 }
  },
  "15": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["13", 0],
      "vae": ["5", 0]
    }
  },
  "16": {
    "class_type": "SaveAnimatedWEBP",
    "inputs": {
      "filename_prefix": "wan_t2v",
      "fps": 16,
      "quality": 90,
      "images": ["15", 0]
    }
  }
}
```

### 8.2 Wan 2.2 MoE T2V 工作流 (双专家)

```
关键区别: 需要加载两个 diffusion model
1. Load Diffusion Model #1: wan2.2_t2v_high_noise_14B_fp8
2. Load Diffusion Model #2: wan2.2_t2v_low_noise_14B_fp8
3. 采样器内部自动切换专家
```

### 8.3 VACE 视频编辑工作流

```
VACE 工作流通过 Bypass 切换模式:

T2V 模式:
  ✅ Text Encode (Positive/Negative)
  ✅ WanVaceToVideo (设置尺寸和帧数)
  ❌ Bypass: Load Image, Load Video, Mask

I2V 模式:
  ✅ Text Encode
  ✅ Load Image → WanVaceToVideo
  ❌ Bypass: Load Video, Mask

V2V 模式:
  ✅ Text Encode
  ✅ Load Video → WanVaceToVideo
  ❌ Bypass: Load Image

局部编辑模式:
  ✅ Text Encode
  ✅ Load Video + Mask → WanVaceToVideo
```

---

## 9. 开源视频模型生态对比 (2025-2026)

### 9.1 主要开源视频模型

| 模型 | 组织 | 参数量 | 架构 | VAE 压缩 | 文本编码器 | 特点 |
|------|------|--------|------|---------|-----------|------|
| **Wan 2.2** | 阿里 | 27B (14B active) | MoE DiT | 4×8×8 / 4×16×16 | UMT5-XXL | MoE + 最大开源 |
| **HunyuanVideo** | 腾讯 | 13B | DiT | 4×8×8 | mT5-XXL + CLIP | 运动真实感最强 |
| **CogVideoX** | 智谱 | 5B | 3D-DiT | 4×8×8 | T5-XXL | 3D Full Attention |
| **LTX-2.3** | Lightricks | 22B | DiT | 8×32×32 | Gemma 3 12B | 超快推理 + 音频 |
| **Mochi 1** | Genmo | 10B | DiT | 6×8×8 | T5-XXL | 运动质量好 |
| **Open-Sora** | HPC-AI | 1.1B | DiT | 4×8×8 | T5-XXL | 轻量级 |

### 9.2 Wan 2.2 vs 竞品详细对比

| 维度 | Wan 2.2 14B | HunyuanVideo 13B | LTX-2.3 | CogVideoX 5B |
|------|------------|-----------------|---------|--------------|
| **质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **速度** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **VRAM** | 65-80 GB | 60-80 GB | 32+ GB | 16-24 GB |
| **最大分辨率** | 720P | 720P | 720P | 720P |
| **最大时长** | 5s | 5s | 5s | 6s |
| **多语言** | ✅ (UMT5) | ✅ (mT5) | ❌ | 有限 |
| **ComfyUI** | ✅ 原生+社区 | ✅ 原生 | ✅ 原生 | ✅ 社区 |
| **扩展生态** | VACE+S2V+Animate | 基础 | Audio+LoRA | 基础 |
| **消费级** | TI2V-5B ✅ | ❌ | ✅ | ✅ |
| **许可证** | Apache 2.0 | Tencent | LTXV License | CogVideoX |
| **社区活跃度** | 最高 | 高 | 高 | 中 |

---

## 10. RunningHub 实验

### 实验 #48: Wan 2.6 T2V — 龙虾厨师 ✅

```
端点: alibaba/wan-2.6/text-to-video
Prompt: "A red lobster wearing a tiny chef hat, cooking in a miniature kitchen, 
         steam rising from a pot, warm kitchen lighting, playful and whimsical, 
         high quality animation style"
耗时: 50s | 费用: ¥0.63
输出: /tmp/rh-output/wan27-lobster-t2v.mp4
观察: Wan 2.6 T2V 价格较高（¥0.63 vs Seedance ¥0.30），
      但质量和文本遵循能力确实出色
```

### 实验 #49: Wan 2.6 I2V — 金龙穿雾 ✅

```
端点: alibaba/wan-2.6/image-to-video
输入图: 金龙关键帧 (rhart-image-n-pro 生成, ¥0.03)
Prompt: "The golden dragon soars majestically through the mist, its body undulating 
         gracefully, clouds swirling around it, camera slowly tracking the dragon 
         as it flies between mountain peaks, cinematic movement"
耗时: 210s | 费用: ¥0.63
输出: /tmp/rh-output/wan27-dragon-i2v.mp4
观察: I2V 耗时明显更长（210s vs T2V 50s），价格相同。
      图像保真度不错，运动自然
```

### 实验成本汇总

| 实验 | 端点 | 耗时 | 费用 |
|------|------|------|------|
| 关键帧生成 | rhart-image-n-pro/text-to-image | 25s | ¥0.03 |
| #48 T2V | wan-2.6/text-to-video | 50s | ¥0.63 |
| #49 I2V | wan-2.6/image-to-video | 210s | ¥0.63 |
| **总计** | | **285s** | **¥1.29** |

---

## 11. 关键洞察与最佳实践

### 11.1 Wan 模型选择决策树

```
需要视频生成？
├── 有 GPU (24GB+)?
│   ├── 24GB (4090) → Wan 2.2 TI2V-5B 或 1.3B
│   ├── 48GB (A6000/双卡) → Wan 2.2 14B FP8 480P
│   └── 80GB+ (H100/H200) → Wan 2.2 14B 720P
├── 无 GPU / 追求画质?
│   ├── 预算充足 → Wan 2.6 API (RunningHub)
│   └── 预算有限 → Wan 2.6 Flash
└── 需要编辑功能?
    └── VACE 14B (本地) 或 Wan 2.6 API
```

### 11.2 ComfyUI 实操建议

```
1. 新手入门: ComfyUI 原生 Wan 节点 + 官方工作流模板
2. 进阶优化: WanVideoWrapper + TeaCache + FP8
3. 生产部署: 原生节点 + API 批量脚本
4. 最新功能: WanVideoWrapper（Animate/S2V/面部控制等）
5. 视频编辑: VACE 模型（统一框架最方便）

关键参数:
- 步数: 30 步（标准）, 8-12 步（CausVid LoRA）
- 分辨率: 832×480（480P）/ 1280×720（720P）
- 帧数: 49-81 帧（约 3-5 秒 @ 16fps）
- 采样器: euler（推荐）
- 调度器: simple（推荐）
```

### 11.3 Wan 生态中的 ComfyUI 工作流编排

```
高级工作流模式:

模式一: 纯本地 Wan
  [UMT5 Text Encode] → [Wan DiT Sample] → [Wan-VAE Decode] → Video

模式二: Wan VACE 多任务
  [Load Video + Mask] → [VACE Conditioning] → [Sample] → Edited Video

模式三: 混合管线 (本地关键帧 + 云端视频化)
  [Flux/SDXL T2I 本地] → [Wan 2.6 I2V API] → [本地后处理]

模式四: 多模态管线 (Wan 2.2 S2V)
  [CosyVoice TTS] → [Wan S2V + 参考图] → [说话视频]

模式五: 角色动画管线
  [参考图 + 参考动作视频] → [Wan Animate] → [角色动画视频]
```

---

## 12. 总结

### 核心要点

1. **Wan 是当前最完整的开源视频生成框架** — 从 1.3B 消费级到 14B 旗舰，从 T2V/I2V 到编辑/动画/音频驱动，覆盖面最广

2. **Wan 2.2 MoE 是关键创新** — 按时间步分专家（高噪声=布局，低噪声=细节），27B 参数但 14B 推理成本

3. **Wan-VAE 的 3D 因果卷积** 是视频 VAE 的标杆设计 — 4×8×8 压缩比平衡了质量和效率

4. **VACE 统一编辑框架** 证明了单模型多任务在视频领域是可行的 — 一个模型搞定 T2V/I2V/V2V/编辑

5. **ComfyUI 双轨集成** — 原生节点稳定可靠，WanVideoWrapper 前沿功能丰富，根据需求选择

6. **Wan 2.6 未开源** — 最新版只能通过 API 使用，2.2 仍是最新可本地部署的版本
