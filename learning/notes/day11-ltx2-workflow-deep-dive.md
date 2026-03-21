# Day 11 — LTX-2.3 视频工作流深度学习 + ComfyUI 节点编排

> 日期: 2026-03-21 | 学习轮次: 19
> 主题: LTX-2.3 ComfyUI 节点体系深度分析 + Wan 2.6 对比实验

## 1. LTX-2.3 模型架构回顾

### 1.1 模型规格
| 属性 | 值 |
|------|-----|
| 参数量 | 22B |
| 架构 | DiT (Diffusion Transformer) |
| 文本编码器 | Gemma 3 12B IT (替代 T5XXL) |
| VAE | 新版 Latent Space (更精细细节) |
| 音频 | 原生音视频联合生成 |
| 分辨率 | 最高 1920×1088 |
| 帧数 | 最多 ~121 帧 (约 4-5 秒 @24fps) |
| VRAM | 32GB+ (FP8 量化可降至约 24GB) |

### 1.2 关键改进 (vs LTX-2.0)
1. **新 Latent Space** — 更精细纹理和更锐利边缘
2. **9:16 竖屏支持** — 社交媒体友好
3. **更好的音频** — 降噪、对话、环境音增强
4. **Gemma 3 文本编码器** — 比 T5XXL 更好的 prompt 理解
5. **IC-LoRA Union Control** — 单 LoRA 支持多种控制条件（深度+边缘+姿态）
6. **Spatial + Temporal Upscaler** — 潜空间级别的上采样（非后处理）

## 2. LTX-2.3 ComfyUI 节点体系完整解析

### 2.1 核心节点分类

通过分析 Comfy-Org 官方 T2V 模板（47 个子图节点）和 Lightricks 示例工作流（44 节点），LTX-2.3 节点体系分为以下几类：

#### A. 模型加载类
| 节点 | 功能 | 关键参数 |
|------|------|---------|
| `CheckpointLoaderSimple` | 加载 LTX 主模型 | 选择 fp8/bf16 |
| `LTXAVTextEncoderLoader` | 加载 Gemma 3 文本编码器 | encoder_name, model_name, dtype |
| `LTXVAudioVAELoader` | 加载音频 VAE | 同检查点文件 |
| `LoraLoaderModelOnly` | 加载蒸馏 LoRA | lora_name, strength |
| `LatentUpscaleModelLoader` | 加载空间上采样模型 | model_name |

**关键发现**: LTX-2.3 使用 `LTXAVTextEncoderLoader` 而非通用的 CLIPLoader — 它同时加载 Gemma 3 编码器和模型的音视频 tokenizer，这是音视频联合生成的关键。

#### B. 潜空间创建类
| 节点 | 功能 | 关键参数 |
|------|------|---------|
| `EmptyLTXVLatentVideo` | 创建空白视频潜空间 | width, height, length, batch_size |
| `LTXVEmptyLatentAudio` | 创建空白音频潜空间 | length, fps, batch_size |
| `LTXVConcatAVLatent` | 拼接音频+视频潜空间 | 输入两个 latent |

**架构洞察**: LTX-2.3 将音频和视频编码到**独立的潜空间**，然后在 `ConcatAVLatent` 中拼接成统一张量。这与 Kling Omni 的音视频联合架构类似，但 LTX 的拼接是在 latent 层面，更灵活。

```
视频潜空间: [B, C_v, T, H, W]
音频潜空间: [B, C_a, T_a]
拼接后: [B, C_v + C_a, ...]  (在 channel 维度拼接)
```

#### C. 条件编码类
| 节点 | 功能 | 关键参数 |
|------|------|---------|
| `CLIPTextEncode` | 文本编码（正/负向） | text |
| `LTXVConditioning` | LTX 特定条件封装 | frame_rate (fps) |
| `LTXVImgToVideoInplace` | 图生视频条件注入（原地模式） | strength, crop |
| `LTXVImgToVideoConditionOnly` | 图生视频条件注入（仅条件） | strength, crop |
| `GemmaAPITextEncode` | 使用 LTX API 调用 Gemma 编码 | prompt, negative |
| `TextGenerateLTX2Prompt` | 用 Gemma 自动增强 prompt | temperature, top_p, top_k |

**重要区分**:
- `LTXVImgToVideoInplace`: 直接修改潜空间（第一帧固定），strength 控制其他帧的去噪程度
- `LTXVImgToVideoConditionOnly`: 只作为条件引导（类似 IP-Adapter），不固定帧
- `LTXVConditioning`: 注入 frame_rate 信息（类似 SDXL 的微条件），模型需要知道 fps 才能正确生成运动

#### D. 采样类
| 节点 | 功能 | 关键参数 |
|------|------|---------|
| `SamplerCustomAdvanced` | 高级采样器 | 接收 guider + sigmas + noise |
| `KSamplerSelect` | 选择采样算法 | sampler_name |
| `ManualSigmas` | 手动指定 sigma 序列 | sigmas_str |
| `LTXVScheduler` | LTX 专用调度器 | steps, sigma_max, sigma_min, ... |
| `CFGGuider` | CFG 引导 | cfg |
| `MultimodalGuider` | 多模态引导（音视频） | cfg_str |
| `GuiderParameters` | 引导参数配置 | 模态/权重/cfg 等 |
| `RandomNoise` | 随机噪声生成 | seed, control_after_generate |
| `ClownSampler_Beta` | 高级采样器（社区） | eta, solver, ... |

**采样器选择**:
- **蒸馏模型**: `euler_cfg_pp` 或 `euler_ancestral_cfg_pp`，4-8 步
- **完整模型**: `euler_ancestral_cfg_pp`，15-50 步
- **CFG**: 蒸馏=1.0，完整=3.5-7.0（LTX 的 CFG 整体偏低）

**Sigma 序列分析**:
```
蒸馏模式（4步）: 0.85, 0.725, 0.4219, 0.0
完整模式（8步）: 1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0

对比 SD 的 Karras sigma（20步）: ~14.6, 9.5, 6.2, 4.0, 2.6, 1.7, ...
```

LTX 的 sigma 序列非常独特：
1. 蒸馏模式从 0.85 开始（而非 1.0），说明蒸馏已经"预去噪"了一部分
2. 完整模式在高 sigma 区域（0.975-1.0）步进极小，说明模型在高噪声区域需要精细控制
3. 尾部都收敛到 0.0，实现完全去噪

#### E. 后处理类
| 节点 | 功能 | 关键参数 |
|------|------|---------|
| `LTXVSeparateAVLatent` | 分离音视频潜空间 | — |
| `LTXVLatentUpsampler` | 潜空间空间上采样 | — |
| `LTXVCropGuides` | 裁剪引导 | — |
| `VAEDecodeTiled` | 分块 VAE 解码 | tile_width, tile_height, overlap |
| `LTXVAudioVAEDecode` | 音频 VAE 解码 | — |
| `CreateVideo` | 合并帧+音频为视频 | frame_rate |
| `SaveVideo` | 保存视频文件 | filename_prefix, format |
| `ResizeImagesByLongerEdge` | 按长边缩放 | size |
| `LTXVPreprocess` | 预处理（归一化等） | target_fps |

### 2.2 两阶段管线（Two-Stage Pipeline）

LTX-2.3 的高质量输出通常使用两阶段管线：

```
Stage 1: 低分辨率生成（快速迭代）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EmptyLTXVLatentVideo(768×512, 97帧)
  + LTXVEmptyLatentAudio(97帧)
  → LTXVConcatAVLatent
  → CFGGuider(cfg=1) + ManualSigmas(蒸馏4步)
  → SamplerCustomAdvanced(euler_cfg_pp)
  → LTXVSeparateAVLatent

Stage 2: 高分辨率精炼 + 空间上采样
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stage1 output
  → LTXVLatentUpsampler(x2)
  → CFGGuider(cfg=1) + ManualSigmas(完整8步)
  → SamplerCustomAdvanced(euler_ancestral_cfg_pp)
  → LTXVSeparateAVLatent
  → VAEDecodeTiled(768×64 tiles)
  → LTXVAudioVAEDecode
  → CreateVideo(24fps) → SaveVideo
```

**关键设计决策**:
1. **潜空间上采样** — 在 latent space 做 2x upscale，比像素空间上采样（如 ESRGAN）保留更多语义信息
2. **两次采样** — Stage 1 用蒸馏模式快速生成结构，Stage 2 用更多步精炼细节
3. **分块 VAE 解码** — 22B 模型的 VAE 解码非常吃显存，分块是必须的
4. **音视频分离后处理** — 视频走 VAEDecodeTiled，音频走 LTXVAudioVAEDecode，然后 CreateVideo 合并

### 2.3 I2V（图生视频）工作流差异

相比 T2V，I2V 增加了以下节点链路：

```
LoadImage → ResizeImageMaskNode → LTXVImgToVideoInplace(strength=0.7)
  → 注入到 Stage 1 的 latent 中

或者（条件注入模式）:
LoadImage → LTXVImgToVideoConditionOnly(strength=0.7)
  → 作为额外条件注入 CFGGuider
```

**两种 I2V 模式对比**:
| 特性 | Inplace（原地） | ConditionOnly（仅条件） |
|------|----------------|---------------------|
| 第一帧 | 严格固定 | 参考但不固定 |
| 运动自由度 | 中等 | 更高 |
| 一致性 | 更好 | 较好 |
| 适用场景 | 精确续写 | 风格引导 |

### 2.4 IC-LoRA Union Control 工作流

LTX-2.3 的 Union IC-LoRA 是一个突破性设计 — 单个 LoRA 文件支持多种控制条件：

```
控制信号提取:
  输入图 → DepthAnythingV2 → 深度图
  输入图 → CannyEdge → 边缘图
  输入图 → DWPose → 人体姿态

控制信号注入:
  深度图/边缘图/姿态 → LTXVICLoRACondition
  + 参考图 → LTXVImgToVideoInplace(ref_scale=0.5)
  → 合并后注入采样流程

特点:
  - 在降采样的 latent 上工作（ref0.5），减少显存
  - 支持任意组合：只要深度、只要边缘、深度+边缘+姿态
  - 比传统 ControlNet 更轻量（因为是 LoRA 而非完整副本）
```

### 2.5 ComfyUI API 格式分析

LTX 工作流的 API JSON 格式遵循标准 ComfyUI API 规范：

```json
{
  "3": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"
    }
  },
  "5": {
    "class_type": "EmptyLTXVLatentVideo",
    "inputs": {
      "width": 768,
      "height": 512,
      "length": 97,
      "batch_size": 1
    }
  },
  "7": {
    "class_type": "LTXVConditioning",
    "inputs": {
      "positive": ["6", 0],  // CLIPTextEncode output
      "negative": ["8", 0],
      "frame_rate": 24
    }
  },
  "10": {
    "class_type": "SamplerCustomAdvanced",
    "inputs": {
      "noise": ["11", 0],
      "guider": ["12", 0],
      "sampler": ["13", 0],
      "sigmas": ["14", 0],
      "latent_image": ["9", 0]  // ConcatAVLatent output
    }
  }
}
```

**新型 Subgraph 格式（v0.4）**: 
Comfy-Org 官方模板已采用 `definitions.subgraphs` 结构，将复杂工作流封装为组件节点（type 为 UUID）。这是 ComfyUI 的新特性 — 类似"子图"或"宏"。

## 3. LTX vs 其他视频模型 ComfyUI 集成方式对比

| 特性 | LTX-2.3（本地） | Kling（API 节点） | Seedance（API） | AnimateDiff（本地） |
|------|----------------|------------------|----------------|-------------------|
| 运行方式 | 本地推理 | Partner Node → API | fal.ai API | 本地推理 |
| VRAM 要求 | 32GB+ | 无 | 无 | 8-12GB |
| 可控性 | 极高（所有参数可调） | 低（黑盒） | 中（部分参数） | 高 |
| 音频支持 | ✅ 原生 | ✅ Omni 版 | ✅ | ❌ |
| 成本 | 硬件+电费 | 按次付费 | 按次付费 | 硬件+电费 |
| 质量 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 生成速度 | 慢(分钟级) | 快(秒级) | 快 | 中等 |
| 训练自定义 | ✅ IC-LoRA | ❌ | ❌ | ✅ 运动LoRA |
| 帧数 | ~121帧 | ~450帧(15s@30fps) | ~150帧(5s@30fps) | ~24-48帧 |

**关键洞察**: LTX-2.3 的真正价值在于**完全可控的工作流编排** — 你可以精确控制每个节点的参数、sigma 序列、LoRA 权重、IC 条件等。商业 API（Kling/Seedance）虽然质量更高，但本质是黑盒。

## 4. RunningHub 实验

### 实验 15: Wan 2.6 文生视频

Wan 2.6（万相）是阿里巴巴的开源视频生成模型，架构类似 LTX（都是 DiT），在 RunningHub 上可直接调用。

- **模型**: alibaba/wan-2.6/text-to-video
- **Prompt**: "A majestic golden dragon soaring through misty mountain peaks at sunrise, volumetric fog, cinematic lighting, epic scale, 4K quality"
- **参数**: duration=5s, resolution=1280×720, shotType=single
- **耗时**: 45s
- **费用**: ¥0.38
- **输出**: `/tmp/rh-output/experiment-15-wan26-dragon.mp4`

**评价**: 
- 运动质量好，龙的飞行动作自然
- 雾气体积感明显
- 与 LTX-2.3 同为 DiT 架构，但 Wan 2.6 更注重中国风美学
- 支持负向 prompt（negativePrompt），LTX 也支持

### 实验 16: Wan 2.6 参考图生视频（Reference-to-Video）

这个实验对应 ComfyUI 中的 IC-LoRA 控制模式 — 用参考图引导视频生成。

- **模型**: alibaba/wan-2.6/reference-to-video
- **参考图**: 赛博朋克狗（experiment-04-cyberpunk.jpg）
- **Prompt**: "The cyberpunk dog walks forward through neon-lit city streets, rain dripping off its metallic body, looking around curiously, cinematic movement"
- **参数**: duration=5s, size=1280×720, shotType=single
- **耗时**: 75s
- **费用**: ¥0.40
- **输出**: `/tmp/rh-output/experiment-16-wan26-ref2video.mp4`

**评价**:
- 参考图中的赛博朋克狗被很好地保持
- 运动自然，符合 prompt 描述
- Reference-to-Video 本质上是 ComfyUI 中 IC-LoRA 或 IP-Adapter 在视频模型上的应用

### 模型对比更新

```
模型               类型          耗时    费用    架构      可控性
──────────────────────────────────────────────────────────────────
LTX-2.3 (本地)     本地推理      分钟级  免费    DiT 22B   ⭐⭐⭐⭐⭐
Wan 2.6 T2V        云端 API     45s    ¥0.38   DiT       ⭐⭐（参数有限）
Wan 2.6 Ref2V      云端 API     75s    ¥0.40   DiT       ⭐⭐⭐（有参考图）
Seedance 1.5 Pro   云端 API     70s    ¥0.30   未公开    ⭐⭐
Kling 3.0 Pro      云端 API     135s   ¥0.75   未公开    ⭐⭐
rhart-video-s      云端 API     185s   ¥0.10   未公开    ⭐
```

## 5. ComfyUI 视频工作流编排最佳实践

### 5.1 节点连接模式（Pattern）

**模式 1: 纯文生视频（最简）**
```
CheckpointLoader → CLIPTextEncode(+/-) → LTXVConditioning(fps)
  + EmptyLTXVLatentVideo → LTXVEmptyLatentAudio → ConcatAVLatent
  + RandomNoise + KSamplerSelect + ManualSigmas → CFGGuider
  → SamplerCustomAdvanced
  → SeparateAVLatent → VAEDecodeTiled + AudioVAEDecode
  → CreateVideo → SaveVideo
```

**模式 2: 两阶段（推荐）**
```
模式1 → Stage1 output
  → LTXVLatentUpsampler(x2)
  → 第二次 SamplerCustomAdvanced(更多步)
  → SeparateAVLatent → VAEDecodeTiled
  → CreateVideo → SaveVideo
```

**模式 3: 图生视频**
```
模式1/2 + LoadImage → LTXVImgToVideoInplace → 注入 latent
```

**模式 4: IC-LoRA 控制**
```
模式1/2 + ControlNet条件提取 → LTXVICLoRACondition → 注入 guider
```

### 5.2 参数调优指南

```
目标: 快速迭代
  → distilled model + distilled LoRA
  → 768×512, 41帧
  → 4步, sigma: 0.85,0.725,0.4219,0.0
  → cfg=1

目标: 最终渲染
  → full model (或 distilled + full 两阶段)
  → 960×544 → 上采样到 1920×1088
  → 8-15步, cfg=1-3
  → VAEDecodeTiled(768, 64) 节省显存

目标: 低 VRAM (24GB)
  → FP8 量化模型
  → --reserve-vram 5
  → 使用 low_vram_loaders.py 中的特殊加载节点
  → 减小分辨率和帧数
```

### 5.3 Prompt 技巧（LTX-2.3 特有）

1. **时间描述**: 按时间顺序描述事件（"首先...然后...最后..."）
2. **视觉细节**: 明确描述所有视觉元素（颜色、材质、光照）
3. **音频描述**: 如果需要音频，在 prompt 中加入声音描述（"rain sounds, soft music playing"）
4. **负向 prompt**: 标准：`"pc game, console game, video game, cartoon, childish, ugly"`
5. **Gemma 增强**: 使用 `TextGenerateLTX2Prompt` 节点让 Gemma 3 自动丰富你的 prompt

## 6. LTX-2.3 与 Wan 2.6 架构对比

两者都是 DiT（Diffusion Transformer）架构的视频生成模型：

| 特性 | LTX-2.3 | Wan 2.6 |
|------|---------|---------|
| 开发者 | Lightricks | 阿里巴巴 |
| 参数量 | 22B | ~14B |
| 文本编码器 | Gemma 3 12B | Qwen2 7B / T5XXL |
| 音频 | ✅ 原生联合 | ❌（分离模型） |
| 训练框架 | Flow Matching | Flow Matching |
| ComfyUI 集成 | 核心 + 自定义节点 | ComfyUI-Wan 自定义节点 |
| 开源程度 | ✅ 完全开源 | ✅ 完全开源 |
| IC-LoRA | ✅ Union Control | ❌（但有 Reference-to-Video） |
| 最大帧数 | ~121帧 | ~300帧 |

**共同点**: 都使用 Flow Matching（而非 DDPM），都基于 Transformer（而非 U-Net），都支持 ComfyUI 工作流编排。

**关键差异**: LTX-2.3 的音视频联合生成是最大亮点，Wan 2.6 的 Reference-to-Video 能力更强（支持多参考图+参考视频）。

## 7. 学习总结

### 今日收获
1. ✅ 深入分析了 LTX-2.3 全部 47 个 ComfyUI 节点的功能和参数
2. ✅ 理解了两阶段管线的设计原理（潜空间上采样 > 像素上采样）
3. ✅ 掌握了 LTX 独特的 sigma 序列设计（蒸馏模式从 0.85 开始）
4. ✅ 对比了 I2V 两种模式（Inplace vs ConditionOnly）
5. ✅ 分析了 IC-LoRA Union Control 的工作原理
6. ✅ 完成 Wan 2.6 T2V + Ref2V 两个实验
7. ✅ 建立了 LTX vs Wan vs 商业 API 的完整对比矩阵

### 待深入（Day 12）
- ComfyUI API Node 体系（Partner Nodes / fal.ai 集成）
- 在 ComfyUI 中调用 Kling/Seedance/Veo3.1
- RunningHub AI App 中的 ComfyUI 工作流
