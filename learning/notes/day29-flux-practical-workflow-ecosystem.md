# Day 29: Flux 实战工作流生态 — 从 Tools 套件到 FLUX.2 Klein + Kontext

> 学习时间: 2026-03-23 04:03 UTC
> 实验: 2个（RunningHub T2I + I2I 风格转换）¥0.06
> 重点: Flux Tools 全家桶 / ControlNet 生态 / ComfyUI 工作流模式 / FLUX.2 Klein / Kontext

---

## 一、Flux 模型家族全景（截至 2026-03）

### 1.1 FLUX.1 系列

| 模型 | 参数量 | 特点 | 许可证 |
|------|--------|------|--------|
| FLUX.1 [pro] | 12B | 最高质量，API only | 商业 |
| FLUX.1 [dev] | 12B | 开源权重，guidance distilled | 非商业 |
| FLUX.1 [schnell] | 12B | 4步蒸馏，最快 | Apache 2.0 |
| FLUX1.1 [pro] Ultra | 12B | 4MP输出，灵活宽高比 | 商业API |

### 1.2 FLUX.1 Tools 套件（2024-11发布）

BFL 发布的四大工具模型，为 FLUX.1 添加控制和引导能力：

| 工具 | 功能 | 输入 | 模型形式 |
|------|------|------|----------|
| **FLUX.1 Fill** | Inpainting + Outpainting | 图像 + Mask + 文本 | 完整模型 |
| **FLUX.1 Depth** | 深度图结构控制 | 图像(→深度图) + 文本 | 完整/LoRA |
| **FLUX.1 Canny** | 边缘检测结构控制 | 图像(→Canny) + 文本 | 完整/LoRA |
| **FLUX.1 Redux** | 图像变体/风格混合 | 参考图 + 文本 | Adapter |

### 1.3 FLUX.1 Kontext（2025-05发布）

**革命性的 in-context 图像编辑模型**，统一了生成与编辑：

- **核心创新**: 同时接受文本和图像作为输入，支持上下文感知的生成/编辑
- **三个版本**: pro（快速迭代编辑）/ max（最高性能）/ dev（开源 12B）
- **关键能力**:
  - 角色一致性保持 — 跨场景维持角色/物体特征
  - 局部编辑 — 精准修改特定区域
  - 风格参考 — 保持参考图风格生成新场景
  - 迭代编辑 — 基于上次编辑结果继续修改
- **性能**: 比 GPT-Image 快 8 倍，在文字编辑和角色保持上得分最高
- **限制**: 6 轮以上迭代编辑可能产生视觉退化

### 1.4 FLUX.2 [klein]（2026-01发布）

**最新一代，统一生成与编辑的紧凑高速模型**：

| 变体 | 参数 | 推理步数 | 速度(5090) | VRAM | 许可 |
|------|------|----------|-----------|------|------|
| 4B distilled | 4B | 4步 | ~1.2s | 8.4GB | Apache 2.0 |
| 4B base | 4B | 50步 | ~17s | 9.2GB | Apache 2.0 |
| 9B distilled | 9B | 4步 | ~2s | 19.6GB | 非商业 |
| 9B base | 9B | 50步 | ~35s | 21.7GB | 非商业 |

- **统一架构**: 单一模型同时支持 T2I 和图像编辑（包括多参考图）
- **4B Apache 2.0**: 真正可商用的高质量开源模型
- **量化版本**: FP8 / NVFP4 版本官方提供
- **编辑能力**: 风格转换、语义修改、物体替换/删除、多参考图合成

---

## 二、Flux ControlNet 生态深度解析

### 2.1 官方 ControlNet（BFL 出品）

#### Flux.1 Canny Dev（完整模型）
```
模型: flux1-canny-dev.safetensors
位置: ComfyUI/models/diffusion_models/
大小: ~23GB（完整 12B transformer）
原理: 从基础 Flux 模型 fine-tune，接受 Canny 边缘图作为条件输入
```

**ComfyUI 工作流结构**:
```
Load Diffusion Model (flux1-canny-dev)
  → [model] KSampler
DualCLIPLoader (t5xxl + clip_l)
  → CLIPTextEncode → [conditioning] KSampler
Load Image → [canny edge map input]
  → InpaintModelConditioning / Apply ControlNet
Load VAE (ae.safetensors)
  → VAEDecode → Save Image
```

#### Flux.1 Depth Dev LoRA（轻量版）
```
模型: flux1-depth-dev-lora.safetensors
位置: ComfyUI/models/loras/
大小: ~数百MB
原理: 基于 flux1-dev 基础模型的 LoRA 适配器
```

**ComfyUI 工作流结构**:
```
Load Diffusion Model (flux1-dev.safetensors)
  → LoraLoaderModelOnly (flux1-depth-dev-lora)
  → [model] KSampler
... (其余同上)
```

**完整版 vs LoRA 版本对比**:

| 方面 | 完整模型 | LoRA 版 |
|------|----------|---------|
| 文件大小 | ~23GB | ~数百MB |
| 显存占用 | 与完整Flux相同 | 基础Flux + LoRA开销 |
| 质量 | 最优 | 接近完整版 |
| 灵活性 | 独立加载 | 可堆叠多LoRA |
| 适用场景 | 专用机/API | 资源受限环境 |

### 2.2 社区 ControlNet

#### InstantX / Shakker Labs 系列

**Shakker-Labs ControlNet-Union-Pro (v1)**:
- 支持 7 种控制模式: canny, tile, depth, blur, pose, gray, low quality
- 6.15GB 模型大小
- 6 个 double blocks + 4 个 single blocks

**Shakker-Labs ControlNet-Union-Pro-2.0（2025-04）**:
- 模型大小减至 **3.98GB**（去掉 mode embedding）
- 支持 5 种模式: canny, soft edge, depth, pose, gray
- ⚠️ 移除了 tile 模式支持
- 6 个 double blocks, 0 个 single blocks
- 训练: 20M 高质量图像，300K步，512x512，BF16

**推荐参数**:
```
Canny:      scale=0.7, guidance_end=0.8
Soft Edge:  scale=0.7, guidance_end=0.8 (AnylineDetector)
Depth:      scale=0.8, guidance_end=0.8 (Depth-Anything)
Pose:       scale=0.9, guidance_end=0.65 (DWPose)
Gray:       scale=0.9, guidance_end=0.8
```

#### XLabs-AI ControlNet
- Canny V3, Depth, HED — 三种独立模型
- 训练于 1024×1024
- 还提供了 Flux IP-Adapter (beta)
- 放置在 `ComfyUI/models/xlabs/controlnets/`

#### InstantX 独立模型
- `FLUX.1-dev-Controlnet-Canny` — 专用 Canny 模型
- `FLUX.1-dev-ControlNet-Depth` — 专用深度模型
- `FLUX.1-dev-IP-Adapter` — 图像参考适配器

### 2.3 ComfyUI 中 Flux ControlNet 的使用模式

**模式 A: 官方完整模型（Load Diffusion Model）**
```json
{
  "LoadDiffusionModel": {
    "unet_name": "flux1-canny-dev.safetensors"
  },
  "条件输入": "直接连接到 KSampler 的 model 端"
}
```

**模式 B: 官方 LoRA（基础模型 + LoRA）**
```json
{
  "LoadDiffusionModel": { "unet_name": "flux1-dev.safetensors" },
  "LoraLoaderModelOnly": { "lora_name": "flux1-depth-dev-lora.safetensors" },
  "控制图输入": "连接到采样器前"
}
```

**模式 C: 社区 Union ControlNet**
```json
{
  "LoadControlNetModel": { "control_net_name": "FLUX.1-dev-ControlNet-Union-Pro-2.0.safetensors" },
  "SetUnionControlNetType": { "type": "canny|depth|pose|..." },
  "ApplyControlNet": { "strength": 0.7, "end_percent": 0.8 }
}
```

---

## 三、Flux Fill 工作流详解

### 3.1 Inpainting 工作流

**专用模型**: `flux1-fill-dev.safetensors`（放在 diffusion_models/）

**核心节点链路**:
```
Load Diffusion Model (flux1-fill-dev)
  ↓
DualCLIPLoader (t5xxl + clip_l) → CLIPTextEncode
  ↓
Load Image (with mask/alpha channel)
  ↓
InpaintModelConditioning
  ↓
KSampler → VAEDecode → SaveImage
```

**关键点**:
- flux1-fill-dev 是独立的完整模型（不是 LoRA）
- 图像可以带 alpha 通道作为 mask
- 也可以使用 ComfyUI 的 MaskEditor 手绘 mask
- 同一个模型同时支持 inpainting 和 outpainting

### 3.2 Outpainting 工作流

**额外节点**: `Pad Image for Outpainting`
```
Load Image → Pad Image for Outpainting (设置四方向扩展像素)
  ↓
InpaintModelConditioning
  ↓
KSampler (flux1-fill-dev) → VAEDecode → SaveImage
```

### 3.3 Flux Fill vs 传统 Inpainting

| 方面 | 传统 SD Inpainting | Flux Fill |
|------|-------------------|-----------|
| 模型基础 | SD 1.5/SDXL | Flux 12B |
| 质量 | 好 | 极优（超越 Ideogram 2.0） |
| 提示跟随 | 一般 | 极好 |
| VRAM | ~8GB | ~20GB（可用 GGUF/NF4 降到 ~8GB） |
| 量化方案 | 不常见 | Q5/NF4/GGUF 广泛支持 |

---

## 四、Flux Redux 工作流详解

### 4.1 核心概念

Redux 是一个 **adapter**（适配器），不是独立模型：
- 输入: 参考图像 → 通过 SigLIP 视觉编码器提取特征
- 输出: 条件信号注入 Flux 生成过程
- 效果: 生成与参考图相似但有变化的图像

### 4.2 ComfyUI 工作流

**需要的模型**:
- flux1-redux-dev.safetensors → `ComfyUI/models/style_models/`
- sigclip_vision_patch14_384.safetensors → `ComfyUI/models/clip_vision/`

**节点链路**:
```
Load Style Model (flux1-redux-dev)
  ↓
Load CLIP Vision (SigLIP)
  ↓
CLIP Vision Encode (参考图像)
  ↓
StyleModelApply → [conditioning] → KSampler
```

### 4.3 高级 Redux 控制

**ComfyUI_AdvancedRefluxControl** 自定义节点:
- 提供 image_strength 参数（low/medium/high）
- 替代默认的 StyleModelApply 节点
- 解决 Redux "太强" 的问题 — 原生 Redux 容易过度影响输出

**Redux + Img2Img 组合**:
```
参考图 → CLIP Vision Encode → StyleModelApply → conditioning
参考图 → VAE Encode → latent（作为 img2img 起点）
两路合流到 KSampler
```

### 4.4 Redux vs IP-Adapter 对比

| 方面 | Flux Redux | IP-Adapter (XLabs/InstantX) |
|------|-----------|---------------------------|
| 来源 | BFL 官方 | 社区/研究机构 |
| 架构 | SigLIP → Style Adapter | CLIP → Cross-attention |
| 控制精度 | 整体风格/内容 | 更细粒度的特征控制 |
| 多图支持 | 支持多参考图 | 支持 |
| 与 ControlNet | 可组合 | 可组合 |
| 使用场景 | 图像变体/风格迁移 | 角色一致性/风格参考 |

---

## 五、FLUX.2 Klein ComfyUI 工作流

### 5.1 T2I 工作流
```
Load Diffusion Model (FLUX.2-klein-4B 或 9B)
DualCLIPLoader (t5xxl + clip_l)
CLIPTextEncode → KSampler(steps=4 for distilled, 50 for base)
VAEDecode → SaveImage
```

### 5.2 图像编辑工作流
```
Load Diffusion Model (FLUX.2-klein-4B)
Load Image (参考图) → VAE Encode → latent
CLIPTextEncode ("edit: change the background to sunset")
KSampler → VAEDecode → SaveImage
```

### 5.3 多参考图编辑
```
Load Image 1 (角色) → CLIP Vision Encode → conditioning_1
Load Image 2 (场景) → CLIP Vision Encode → conditioning_2
Combine → KSampler → output
```

---

## 六、Flux 量化方案与低 VRAM 实践

### 6.1 量化方案对比

| 方案 | 大小 | VRAM | 质量损失 | 工具 |
|------|------|------|----------|------|
| BF16（原始） | ~23GB | ~24GB | 无 | 原生 |
| NF4 | ~5.5GB | ~8GB | 极小 | ComfyUI-GGUF / BnB |
| GGUF Q5 | ~8GB | ~10GB | 很小 | ComfyUI-GGUF |
| GGUF Q4 | ~6GB | ~8GB | 小 | ComfyUI-GGUF |
| FP8 | ~12GB | ~14GB | 可忽略 | 原生/官方 |
| NVFP4 | ~6GB | ~8GB | 小 | NVIDIA TensorRT |

### 6.2 NF4 工作流

使用 `ComfyUI-GGUF` 自定义节点:
```
UnetLoaderGGUF → Load GGUF model (flux1-dev-Q4_K_M.gguf)
  ↓ model
DualCLIPLoader → CLIPTextEncode
  ↓ conditioning
EmptyLatentImage
  ↓ latent
KSampler → VAEDecode → SaveImage
```

**关键参数差异**: NF4 模型建议 guidance 从 4.0 降到 3.5

---

## 七、Flux ComfyUI 工作流最佳实践

### 7.1 Flux 特有的工作流差异（vs SD/SDXL）

1. **双编码器**: 必须使用 DualCLIPLoader（T5XXL + CLIP-L）
2. **FluxGuidance 节点**: 控制 classifier-free guidance 行为（不同于传统 CFG）
3. **无 negative prompt**: Flux 架构不使用 negative conditioning
4. **VAE**: 使用专用 `ae.safetensors`，不是传统 SD VAE
5. **分辨率**: 原生 1024×1024，支持多种宽高比

### 7.2 组合工作流模式

**ControlNet + Redux 组合**:
```
参考图 → Redux（风格）
参考图 → Canny/Depth（结构）
两路 conditioning 合并 → KSampler
= 保持结构 + 迁移风格
```

**ControlNet + LoRA 组合**:
```
Load Diffusion Model (flux1-dev)
  → LoraLoaderModelOnly (style_lora.safetensors)
  → Apply ControlNet (Union-Pro-2.0, type=depth)
  → KSampler
= 自定义风格 + 结构控制
```

**Fill + ControlNet 组合**:
```
flux1-fill-dev → Inpainting mask 区域
ControlNet → 控制被填充区域的结构
= 精准的结构化修复
```

### 7.3 生产级管线推荐

```
阶段 1: T2I 初稿
  Flux Dev/Schnell → 快速生成候选图

阶段 2: 结构调整
  Flux Depth/Canny → 保持结构重新风格化

阶段 3: 局部修改
  Flux Fill → Inpainting 精修细节

阶段 4: 变体生成
  Flux Redux → 生成多个风格变体

阶段 5: 超分
  ControlNet Tile（Union-Pro） → 保持细节放大
  或 ESRGAN / SwinIR
```

---

## 八、实验记录

### 实验 1: 文生图基准（RunningHub API）
- **端点**: rhart-image-n-pro/text-to-image
- **提示**: "A serene Japanese garden with cherry blossoms, koi pond, stone bridge, soft morning light, photorealistic, 8k quality"
- **参数**: 16:9, 1K
- **结果**: 高质量日式庭园图，色彩和细节出色
- **耗时**: ~20s
- **花费**: ¥0.03

### 实验 2: 图生图风格迁移（RunningHub API）
- **端点**: rhart-image-n-pro/edit
- **基础图**: 实验1的日式庭园
- **提示**: "Transform this Japanese garden into a magical fantasy scene with glowing fireflies, ethereal mist, moonlight, fantasy art style, dreamy atmosphere"
- **结果**: 成功将写实庭园转为魔幻风格，保持了基础构图同时添加了梦幻元素
- **耗时**: ~20s
- **花费**: ¥0.03

**实验分析**:
- RunningHub 的 rhart-image-n-pro 底层可能使用 Flux 或类似架构
- I2I 编辑很好地保持了原图结构（深度/构图），同时成功迁移风格
- 这与 Flux Redux + Depth ControlNet 组合工作流的效果类似
- 对应 ComfyUI 中可以用 Flux Fill 或 Redux + Depth 实现同样效果

---

## 九、关键洞察总结

### 9.1 Flux 生态演进路线
```
2024-08: FLUX.1 (dev/schnell/pro) — T2I 基础
2024-11: FLUX.1 Tools (Fill/Depth/Canny/Redux) — 控制与编辑
2025-05: FLUX.1 Kontext — 统一的上下文编辑
2026-01: FLUX.2 Klein — 紧凑高速，4B Apache 2.0
```

### 9.2 ComfyUI 中 Flux 使用的三个层次

**Level 1: 基础使用**
- T2I with Dev/Schnell
- NF4/GGUF 量化节省显存

**Level 2: 工具链组合**
- Fill for Inpainting/Outpainting
- Canny/Depth for 结构控制
- Redux for 图像变体
- Union ControlNet for 多模式控制

**Level 3: 高级编排**
- 多 ControlNet 联合使用
- ControlNet + Redux + LoRA 堆叠
- Kontext for 迭代编辑
- Klein 4B for 实时交互

### 9.3 选型决策树
```
需要什么？
├── 快速 T2I → Schnell（4步）或 Klein 4B Distilled（4步）
├── 高质量 T2I → Dev（30步）或 Klein 9B Base
├── 结构控制 → Canny/Depth Dev + ControlNet
├── Inpainting/Outpainting → Fill Dev
├── 图像变体/风格迁移 → Redux Dev
├── 上下文编辑（角色一致） → Kontext Pro/Dev
├── 实时交互 → Klein 4B Distilled（~1.2s）
└── 商用 → Klein 4B（Apache 2.0）或 API（Pro/Ultra）
```

---

## 十、对应 ComfyUI 工作流 JSON

详见: `../workflows/flux-controlnet-canny-basic.json`
详见: `../workflows/flux-fill-inpainting-basic.json`
