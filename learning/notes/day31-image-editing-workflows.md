# Day 31: 图像编辑工作流 — Image Editing Workflows

> 学习时间: 2026-03-23 08:03 UTC | 轮次: #39

## 目录
1. [图像编辑技术全景](#1-图像编辑技术全景)
2. [InstructPix2Pix — 指令驱动编辑的奠基者](#2-instructpix2pix--指令驱动编辑的奠基者)
3. [ICEdit — In-Context 编辑新范式](#3-icedit--in-context-编辑新范式)
4. [Flux Fill — 高级 Inpainting/Outpainting](#4-flux-fill--高级-inpaintingoutpainting)
5. [Flux Kontext — 上下文感知编辑](#5-flux-kontext--上下文感知编辑)
6. [VACE — 统一视频/图像编辑框架](#6-vace--统一视频图像编辑框架)
7. [Qwen-Image-Edit — 双语文本编辑专家](#7-qwen-image-edit--双语文本编辑专家)
8. [OmniGen2 — 统一多模态生成与编辑](#8-omnigen2--统一多模态生成与编辑)
9. [ComfyUI 编辑节点体系总览](#9-comfyui-编辑节点体系总览)
10. [编辑方法全维度对比](#10-编辑方法全维度对比)
11. [生产级编辑工作流模式](#11-生产级编辑工作流模式)
12. [RunningHub 实验](#12-runninghub-实验)

---

## 1. 图像编辑技术全景

### 1.1 三大编辑范式

图像编辑在扩散模型时代经历了三个范式阶段：

| 范式 | 代表方法 | 核心机制 | 优势 | 劣势 |
|------|---------|---------|------|------|
| **Training-Free** | RF-Solver, StableFlow, MasaCtrl | 注意力注入/反转/特征操控 | 零训练成本 | 指令理解弱，需精确 prompt |
| **Fine-tuning** | InstructPix2Pix, UltraEdit, MagicBrush | 架构修改 + 大数据微调 | 精确跟随指令 | 数据量大(450K-10M), 训练昂贵 |
| **Hybrid/In-Context** | ICEdit, Flux Kontext, Qwen-Image-Edit | DiT 上下文能力 + 轻量微调 | 高效 + 高质量 | 依赖大模型基座 |

### 1.2 编辑任务分类

```
图像编辑任务
├── 局部编辑 (Local Editing)
│   ├── Inpainting（区域重绘）
│   ├── Object Removal（物体移除）
│   ├── Object Replacement（物体替换）
│   └── Attribute Modification（属性修改：颜色/材质/大小）
├── 全局编辑 (Global Editing)
│   ├── Style Transfer（风格迁移）
│   ├── Season/Weather Change（季节/天气变换）
│   ├── Lighting Adjustment（光照调整）
│   └── Color Grading（色彩调整）
├── 结构编辑 (Structural Editing)
│   ├── Outpainting（画面扩展）
│   ├── Object Repositioning（物体移位）
│   ├── Pose Change（姿态改变）
│   └── Composition Adjustment（构图调整）
├── 文本编辑 (Text Editing)
│   ├── Add Text（添加文字）
│   ├── Remove Text（移除文字）
│   └── Modify Text（修改文字内容/样式）
└── 语义编辑 (Semantic Editing)
    ├── IP Creation（IP 创作/角色风格化）
    ├── Object Rotation（物体旋转）
    └── Abstract Transformation（抽象变换）
```

### 1.3 技术演进时间线

```
2022.11 InstructPix2Pix (SD 1.5, 450K pairs) ─ 开创指令编辑
2023.09 MagicBrush (SD 1.5, 人工标注) ─ 高质量小数据
2024.04 CosXL Edit (SDXL, Stability AI) ─ SDXL 指令编辑
2024.06 UltraEdit (SD 1.5/SDXL, 4M pairs) ─ 大规模高质量
2024.11 Flux Fill Dev (12B, BFL) ─ Flux 原生 inpainting
2025.04 ICEdit (Flux LoRA, 0.5% data) ─ 上下文编辑新范式
2025.05 Flux Kontext (12B, BFL) ─ 上下文感知编辑模型
2025.06 OmniGen2 (7B, VLM+DiT) ─ 统一多模态编辑
2025.08 Qwen-Image-Edit (20B, Alibaba) ─ 双语文本编辑SOTA
2025.12 Qwen-Image-Layered ─ 分层可编辑图像
```

---

## 2. InstructPix2Pix — 指令驱动编辑的奠基者

### 2.1 论文概要

- **论文**: Brooks et al., "InstructPix2Pix: Learning to Follow Image Editing Instructions" (CVPR 2023)
- **arXiv**: 2211.09800
- **核心创新**: 首个用自然语言指令驱动的端到端图像编辑模型

### 2.2 训练数据生成管线

InstructPix2Pix 的核心突破在于数据生成管线（无需人工标注编辑对）：

```
Step 1: GPT-3 生成编辑指令
  Input:  "a photograph of a girl riding a horse"
  Output: ("make it a painting", "a painting of a girl riding a horse")

Step 2: Prompt-to-Prompt 生成编辑对
  Source: SD("a photograph of a girl riding a horse") → 图A
  Target: SD("a painting of a girl riding a horse") + P2P注意力共享 → 图B

Step 3: 过滤
  CLIP Direction Similarity > threshold → 保留
  结果: 454,445 个 (指令, 源图, 目标图) 三元组
```

### 2.3 架构修改

基于 SD 1.5，核心修改是 **U-Net 输入通道扩展**：

```
原始 SD:    4 通道 (latent z)
IP2P 修改:  8 通道 (latent z + 源图 latent c_I)
           新增 4 通道权重初始化为零 → 训练初始等同于原始模型

条件注入:
  c_T = 文本编辑指令 → cross-attention (标准 CLIP 编码)
  c_I = 源图像 latent → channel concatenation (额外 4 通道)
```

### 2.4 双 Classifier-Free Guidance

InstructPix2Pix 引入了 **双 CFG** 机制：

```python
# 三次前向传播
e_uncond     = model(z_t, ∅, ∅)         # 无条件
e_img        = model(z_t, c_I, ∅)        # 仅图像条件
e_full       = model(z_t, c_I, c_T)      # 完整条件

# 双 CFG 公式
e = e_uncond
  + s_I * (e_img - e_uncond)             # 图像引导强度
  + s_T * (e_full - e_img)               # 文本引导强度

# s_I: 图像引导比例 (image guidance scale) — 控制与源图的相似度
#   高 s_I → 更保留原图，低 s_I → 更自由编辑
# s_T: 文本引导比例 (text guidance scale) — 控制编辑强度
#   高 s_T → 更强编辑效果，低 s_T → 更微妙变化
```

**推荐参数**:
- `s_T` (text guidance): 5.0-7.5
- `s_I` (image guidance): 1.0-2.0

### 2.5 CosXL Edit — SDXL 版本

Stability AI 的 CosXL Edit 将 InstructPix2Pix 范式迁移到 SDXL：

- **基座**: CosXL (Cosine Schedule SDXL 变体)
- **训练**: 使用 EDM2 cosine noise schedule
- **改进**: SDXL 的 2.6B U-Net 提供更好的指令理解
- **特点**: `is_cosxl_edit` 标志，图像 latent 需要特殊缩放

### 2.6 ComfyUI 节点

```
InstructPixToPixConditioning
├── INPUT:
│   ├── positive (CONDITIONING) — 编辑指令
│   ├── negative (CONDITIONING) — 负面提示
│   └── vae (VAE) — VAE编码器
│   └── pixels (IMAGE) — 源图像
├── OUTPUT:
│   ├── positive (CONDITIONING) — 带图像条件的正向
│   ├── negative (CONDITIONING) — 带图像条件的负向
│   └── latent (LATENT) — 用于采样的噪声 latent
```

**ComfyUI CosXL Edit 工作流**:
```
CheckpointLoaderSimple (cosxl_edit.safetensors)
  ↓ MODEL/CLIP/VAE
LoadImage → InstructPixToPixConditioning ← CLIPTextEncode (编辑指令)
  ↓ positive/negative/latent
KSampler (cfg=8, denoise=1.0)
  ↓
VAEDecode → SaveImage
```

### 2.7 局限性

1. **数据偏差**: 合成数据（SD 生成）导致对真实图片的泛化性有限
2. **指令理解**: SD 1.5 的 CLIP 编码器限制了复杂指令理解
3. **ID 保持差**: 人脸/角色编辑后身份常丢失
4. **分辨率限制**: 基于 512×512 训练
5. **不可逆编辑**: 无法精确控制编辑区域（全图编辑）

---

## 3. ICEdit — In-Context 编辑新范式

### 3.1 论文概要

- **论文**: Zhang et al., "In-Context Edit: Enabling Instructional Image Editing with In-Context Generation in Large Scale Diffusion Transformer" (NeurIPS 2025)
- **arXiv**: 2504.20690
- **核心创新**: 利用 DiT 的原生上下文能力实现高效编辑，仅需 0.5% 训练数据 + 1% 可训练参数

### 3.2 核心原理 — Diptych 范式

ICEdit 的核心洞察：**大规模 DiT（如 Flux）天生具备上下文编辑能力**。

```
Diptych (双联画) 格式:
┌─────────────┬─────────────┐
│  源图像      │  编辑后图像  │
│  (左面板)    │  (右面板)    │
└─────────────┴─────────────┘

IC Prompt 构造:
"A diptych with two side-by-side images of the same scene,
 [源图描述]. On the left, the original image. On the right,
 the same image but [编辑指令]."

简化版（官方 ComfyUI 节点内嵌）:
"A diptych with two side-by-side images of the same scene ... but [编辑指令]"
用户只需输入: "make the girl wear pink sunglasses"
```

**工作流程**:
1. 将源图像放在 diptych 左半边
2. 右半边为需要编辑生成的区域（mask）
3. DiT 通过自注意力机制理解左右面板的关系
4. 根据文本指令生成右面板的编辑结果
5. 裁剪右半边作为最终输出

### 3.3 三大技术贡献

#### 贡献一: Training-Free In-Context 编辑基线

DiT 模型（如 Flux）的两个关键属性使其适合编辑：
1. **可扩展的生成保真度**: 大参数 DiT 无需辅助模块即可实现 SOTA 文图对齐
2. **内在上下文感知**: Transformer 注意力机制自然建立源-目标双向交互

零样本（不训练）即可工作，但成功率有限 → 为高效微调建立 baseline。

#### 贡献二: LoRA-MoE 混合微调策略

```
问题: 图像编辑包含多种异质任务（添加/删除/修改/风格/...）
      单一 LoRA 难以覆盖所有场景

解决: LoRA-MoE (Mixture of Experts)
      ↓
┌─────────────────────────────────┐
│  DiT Block (frozen)             │
│  ┌─────────┐                    │
│  │ Attn/FFN │ ──── LoRA Expert 1 (object editing)
│  │ (frozen) │ ──── LoRA Expert 2 (style transfer)
│  │          │ ──── LoRA Expert 3 (attribute change)
│  │          │ ──── LoRA Expert N (...)
│  └─────────┘                    │
│        ↑                        │
│   Router (gating network)       │
│   根据编辑任务动态路由           │
└─────────────────────────────────┘

训练数据: 仅 ~2,250 对 (vs InstructPix2Pix 的 454K)
可训练参数: ~1% (LoRA rank + MoE router)
```

**LoRA-MoE 细节**:
- 每个 LoRA Expert 是标准 LoRA 适配器
- Router 是轻量 gating network（学习根据输入激活不同 expert）
- 训练时所有 expert 参与，推理时 top-k routing
- 发布了两个检查点：`ICEdit-normal-lora`（标准）和 `ICEdit-MoE`（MoE 版）

#### 贡献三: Early Filter 推理时间缩放

```
洞察: 初始噪声的选择显著影响编辑质量

方法: VLM-based Early Filter
1. 采样 N 个不同的初始噪声 z₀¹, z₀², ..., z₀ⁿ
2. 对每个噪声仅运行 K 步（K << total steps，例如 K=3）
3. 用 VLM（如 GPT-4V）评估早期去噪结果质量
4. 选择最佳噪声 z₀* 继续完整去噪

优势: 通过少量额外计算显著提升编辑成功率
      对 Rectified Flow 模型特别有效（早期步已建立结构）
```

### 3.4 性能对比

| 方法 | 训练数据 | 可训练参数 | Emu Edit CLIP Score | MagicBrush CLIP Score |
|------|---------|-----------|--------------------|-----------------------|
| InstructPix2Pix | 454K | 100% (860M) | 基准 | 基准 |
| UltraEdit | 4M | 100% | +3.2% | +2.8% |
| ICEdit (LoRA) | ~2.25K | ~1% | **+5.1%** | **+4.3%** |
| ICEdit (MoE) | ~2.25K | ~1.5% | **+6.8%** | **+5.7%** |

**VIE-Score**: 78.2 vs SeedEdit 75.7（超越商业系统）
**ID 保持**: 超越 GPT-4o

### 3.5 ComfyUI 集成

官方 ComfyUI 工作流（River-Zhang/ICEdit 仓库）:

```
核心节点:
ICEditNode (自定义节点)
├── INPUT:
│   ├── image (IMAGE) — 源图像
│   ├── edit_instruction (STRING) — 编辑指令（如 "make her wear sunglasses"）
│   └── model (MODEL) — Flux + ICEdit LoRA
├── INTERNAL:
│   ├── 自动构造 diptych prompt
│   ├── 创建 mask（右半边）
│   ├── 拼接源图到左半边
│   └── 裁剪右半边作为输出
└── OUTPUT:
    └── edited_image (IMAGE)

VRAM 需求:
- 标准 LoRA: ~14GB（含高分辨率精炼模块）
- MoE + Nunchaku NF4: ~4GB（!）

工作流结构:
LoadDiffusionModel (Flux Dev) → LoRALoader (ICEdit) → ICEditNode
  ↓                                                    ↑
DualCLIPLoader → CLIPTextEncode ────────────────────────┘
  ↓
High-Res Refinement Module (可选) → SaveImage
```

### 3.6 与传统方法的本质区别

```
InstructPix2Pix:
  源图 → [U-Net 通道拼接] → 编辑图
  ↓ 需要修改 U-Net 架构（+4 通道）
  ↓ 需要大规模训练数据（454K）

ICEdit:
  [源图 | ???] → [DiT 自注意力] → [源图 | 编辑图]
  ↓ 无需修改架构（利用 Flux 原生能力）
  ↓ 仅需极少量 LoRA 微调（2.25K 样本）
  ↓ DiT 的 joint attention 自然处理左右面板关系
```

---

## 4. Flux Fill — 高级 Inpainting/Outpainting

### 4.1 模型概要

- **模型**: flux1-fill-dev.safetensors（12B 参数）
- **发布**: 2024-11, Black Forest Labs
- **训练**: 基于 Flux Dev，专门针对 inpainting/outpainting 任务微调
- **架构修改**: 扩展输入通道以接受 mask + 参考图像

### 4.2 与传统 Inpainting 的区别

```
传统 SD Inpainting (如 RunwayML inpainting 模型):
- U-Net 架构，额外输入 mask + masked_image
- 512×512 限制
- 对 mask 边缘融合依赖后处理
- 需要精确的 mask 绘制

Flux Fill:
- DiT 架构，12B 参数
- 原生高分辨率支持
- 上下文理解更强（理解 mask 区域应该填什么）
- 支持文本引导的创造性填充
- 原生 outpainting（画面扩展）
```

### 4.3 核心节点: InpaintModelConditioning

```python
# InpaintModelConditioning 源码逻辑
class InpaintModelConditioning:
    """专门为 Inpainting 模型准备条件输入"""
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "vae": ("VAE",),
                "pixels": ("IMAGE",),       # 源图像
                "mask": ("MASK",),           # 编辑区域蒙版
            }
        }
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT")
    
    def encode(self, positive, negative, pixels, vae, mask):
        # 1. VAE 编码源图像 → latent
        x = pixels * (1 - mask_resized)  # mask 区域置零
        t = vae.encode(x)
        
        # 2. 将 mask 下采样到 latent 空间
        # 3. 拼接 [latent, mask_latent] 作为模型额外输入
        # 4. 注入到 positive/negative conditioning 的 metadata 中
```

### 4.4 Inpainting 工作流

```
完整 Flux Fill Inpainting 工作流:

LoadDiffusionModel (flux1-fill-dev.safetensors)
  ↓ model
DualCLIPLoader (clip_l + t5xxl)
  ↓ clip
LoadVAE (ae.safetensors)
  ↓ vae
LoadImage → [绘制 mask 或自动生成]
  ↓ image + mask
CLIPTextEncode → InpaintModelConditioning ← (image, mask, vae)
  ↓ positive/negative/latent
FluxGuidance (guidance=30.0) ← positive
  ↓
KSampler (euler/simple/28步)
  ↓
VAEDecode → SaveImage
```

**关键参数**:
- `guidance`: 30.0（Flux Fill 推荐，比普通 Flux 的 3.5 高很多）
- `steps`: 20-30
- `sampler`: euler
- `scheduler`: simple
- `denoise`: 1.0（Flux Fill 始终完整去噪）

### 4.5 Outpainting 工作流

```
核心节点: Pad Image for Outpainting

LoadImage
  ↓
PadImageForOutpainting
  ├── left: 256    ← 左侧扩展像素
  ├── top: 0
  ├── right: 256   ← 右侧扩展像素
  ├── bottom: 128  ← 底部扩展像素
  └── feathering: 40 ← 羽化过渡宽度
  ↓ image + mask (自动生成)
InpaintModelConditioning
  ↓
KSampler → VAEDecode → SaveImage
```

**Outpainting 最佳实践**:
- `feathering`: 20-60px，过低会有明显接缝
- 每次扩展不超过原图尺寸的 50%
- 多方向扩展时分步执行（先左右，再上下）
- 提高 guidance scale（30-50）以保证一致性
- prompt 描述整体场景而非仅描述扩展区域

### 4.6 高级技巧

**自动 Mask 生成**（与 SAM/GroundingDINO 组合）:
```
GroundingDINO → SAM2 → Mask
  ↓ "the cat"         ↓
自动检测目标    精确分割蒙版
  ↓                    ↓
InpaintModelConditioning ← (mask, "a golden retriever dog")
  ↓
自动替换猫为金毛犬
```

**多区域迭代编辑**:
```
Round 1: 替换背景
Round 2: 修改人物服装
Round 3: 添加物体
每轮使用上一轮输出作为输入
```

---

## 5. Flux Kontext — 上下文感知编辑

### 5.1 模型概要

- **模型**: FLUX.1 Kontext（2025-05, Black Forest Labs）
- **版本**: Pro（API商用）/ Max（实验增强）/ Dev（开源12B）
- **核心**: 首个实现上下文感知编辑的 Flow Matching 模型
- **论文**: arXiv:2506.15742 "Flow Matching for In-Context Image Generation and Editing in Latent Space"

### 5.2 核心能力

```
1. 角色一致性 (Character Consistency)
   输入: [角色参考图] + "Put this character in a beach setting"
   → 生成保持角色特征的新场景

2. 精确编辑 (Targeted Editing)
   输入: [原图] + "Change the t-shirt color to red"
   → 仅修改指定元素，保持其余不变

3. 风格参考 (Style Reference)
   输入: [风格参考图] + "Generate a city scene in this style"
   → 保持参考风格生成新内容

4. 多图输入 (Multi-Image Context)
   输入: [图1] + [图2] + "Combine the person from image 1 with background of image 2"
   → 理解多图关系并组合

5. 多轮迭代编辑
   Round 1: "Make her hair blonde" → Result 1
   Round 2 (input: Result 1): "Add sunglasses" → Result 2
   Round 3 (input: Result 2): "Change background to a garden" → Result 3
```

### 5.3 架构原理

Flux Kontext 基于 Flux Dev 架构扩展：

```
标准 Flux Dev:
  Text tokens → DiT Blocks → Image latent
  (CLIP-L + T5-XXL)

Flux Kontext:
  Text tokens + Image tokens → DiT Blocks → Image latent
  
  关键: 输入图像通过 VAE 编码为 latent tokens
        与文本 tokens 一起输入到 DiT 的 attention 中
        模型学习在 joint attention 中理解图文关系

  image_tokens = VAE.encode(input_image) → patchify → flatten
  text_tokens  = CLIP_L(text) + T5(text)
  combined     = concat(text_tokens, image_tokens)
  output       = DiT(combined, timestep)
```

### 5.4 ComfyUI 工作流

```
Dev 版（本地运行）:

LoadDiffusionModel (flux1-dev-kontext_fp8_scaled.safetensors)
  ↓ model
DualCLIPLoader (clip_l + t5xxl_fp16 或 fp8)
  ↓ clip
LoadVAE (ae.safetensors)
  ↓ vae
LoadImage(from output) ← 支持多轮编辑
  ↓ image
FluxKontextImageEncode ← (vae, image)
  ↓ conditioning (图像条件)
CLIPTextEncode ← "Change the rabbit's scarf to blue"
  ↓ positive (文本条件)
FluxGuidance (guidance=2.5-10.0)
  ↓
KSampler (euler/simple/28步)
  ↓
VAEDecode → SaveImage

Pro/Max 版（API Partner Node）:
FluxKontextProNode (API Key required)
  ├── image → 输入图像
  ├── prompt → 编辑指令
  └── output_image → 结果
```

### 5.5 Prompt 技巧

```
✅ 好的编辑 Prompt:
- "Change the car color to red"（直接、具体）
- "Make the person wear a blue jacket"（明确目标）
- "Transform the background into a snowy mountain"（清晰意图）

❌ 差的编辑 Prompt:
- "Make it better"（太模糊）
- "A beautiful scene"（描述性而非指令性）

高级技巧:
- 参考图中特定元素: "Keep the person but change everything else to..."
- 负面约束: "Change only the sky, do not modify the buildings"
- 精确修改: "Replace the text 'HELLO' with 'WORLD'"（文字编辑有限）
```

### 5.6 Kontext vs Fill vs ICEdit

| 维度 | Flux Kontext | Flux Fill | ICEdit |
|------|-------------|-----------|--------|
| 编辑方式 | 文本+图像上下文 | Mask + 文本 | Diptych + 指令 |
| 是否需要 Mask | ❌ 不需要 | ✅ 必须 | ❌ 自动裁剪 |
| 多图输入 | ✅ 原生支持 | ❌ | ❌ |
| 局部精确控制 | 中等（文本驱动） | 高（mask精确） | 中高 |
| ID 保持 | 优秀 | 依赖 mask | 超越 GPT-4o |
| 开源 | Dev 版 12B | Dev 版 12B | LoRA（轻量） |
| VRAM | ~20GB FP8 | ~20GB FP8 | ~4-14GB |
| 最佳场景 | 角色一致/风格迁移 | 精确区域重绘 | 指令编辑/属性修改 |

---

## 6. VACE — 统一视频/图像编辑框架

### 6.1 概要

- **模型**: Wan 2.1 VACE (Video All-in-one Creation and Editing)
- **核心**: 单一模型覆盖 8 种视频/图像编辑任务
- **架构**: 基于 Wan 2.1 14B DiT + 额外条件编码器

### 6.2 VACE 支持的 8 种任务

```
1. Text-to-Video (T2V) — 文本生成视频
2. Image-to-Video (I2V) — 图像生成视频
3. Video-to-Video (V2V) — 视频风格迁移/编辑
4. Motion Transfer — 运动迁移（A的动作 → B的角色）
5. Local Replacement — 局部替换（mask区域重绘）
6. Video Extension — 视频扩展（outpainting）
7. Background Replacement — 背景替换
8. Reference Generation — 参考图生成视频

通过 ComfyUI Bypass 节点在任务间切换
```

### 6.3 VACE 视频 Inpainting

VACE 的视频 inpainting 是图像 inpainting 的时间扩展：

```
ComfyUI 工作流:

LoadDiffusionModel (wan2.1_vace_14B.safetensors)
  ↓ model
CLIPLoader (umt5-xxl)
  ↓ clip
LoadVAE (wan_vae.safetensors)
  ↓ vae
LoadVideo (VHS) → 提取帧
  ↓ images
CreateMaskSequence → 为每帧创建 mask
  ↓ masks
WanVaceToVideo ← (images, masks, prompt, model, vae, clip)
  ↓
KSampler → VAEDecode → VHS_VideoCombine
```

**核心节点**: `WanVaceToVideo`
- 接受视频帧 + mask 序列 + 文本 prompt
- mask 白色区域 = 需要编辑的区域
- mask 黑色区域 = 保持不变
- 支持不同帧使用不同 mask（动态编辑区域）

### 6.4 VACE Outpainting

```
WanVacePadAndMask
  ├── video_frames (IMAGE) — 原始视频帧
  ├── left/right/top/bottom — 各方向扩展像素
  └── feathering — 羽化宽度
  ↓ padded_frames + auto_mask
WanVaceToVideo ← (padded_frames, auto_mask, prompt)
  ↓
扩展后的视频
```

### 6.5 图像编辑视角下的 VACE

虽然 VACE 主要面向视频，但其图像编辑能力不可忽视：

- **单帧 V2V**: 等效于强力图像编辑
- **Mask 编辑**: 比传统 inpainting 更理解语义
- **背景替换**: 自动分离前景/背景
- **限制**: VRAM 需求大（14B 模型），单图编辑用 VACE 有些 overkill

### 6.6 VACE vs 图像编辑模型

| 维度 | VACE | Flux Fill | ICEdit |
|------|------|-----------|--------|
| 主要用途 | 视频编辑 | 图像 inpainting | 图像指令编辑 |
| 时间一致性 | ✅ 原生支持 | ❌ 单帧 | ❌ 单帧 |
| 模型大小 | 14B | 12B | LoRA (~100M) |
| VRAM | 40GB+ / 量化 12GB+ | ~20GB FP8 | 4-14GB |
| 适用场景 | 视频编辑为主 | 精确区域重绘 | 快速图像编辑 |

---

## 7. Qwen-Image-Edit — 双语文本编辑专家

### 7.1 模型概要

- **模型**: Qwen-Image-Edit（2025-08, Alibaba/Qwen team）
- **基座**: 基于 Qwen-Image 20B 进一步训练
- **独特能力**: 中英双语精确文本编辑（添加/删除/修改图中文字）
- **架构**: DiT + Qwen2.5-VL (语义控制) + VAE Encoder (外观控制)

### 7.2 核心架构 — 双通路编辑

```
Qwen-Image-Edit 双通路设计:

输入图像 ─┬─→ Qwen2.5-VL 7B ──→ 语义理解
          │     (理解"把文字从Hello改成World")
          │     (理解"在右上角添加红色标题")
          │     ↓ semantic conditioning
          ├─→ VAE Encoder ──→ 外观保持
          │     (保持原图布局/颜色/风格)
          │     ↓ appearance conditioning
          │
          ↓  双条件注入
       DiT 20B ──→ 编辑后图像

关键创新:
1. VLM (Qwen2.5-VL) 提供高层语义理解
2. VAE 提供低层视觉外观信息
3. 两路信息融合实现精确编辑
```

### 7.3 文本编辑能力（独特优势）

```
精确文本编辑示例:

1. 添加文字:
   Prompt: "在图片右下角添加红色文字 'SALE 50% OFF'"
   → 精确渲染文字，保持图像其余部分不变

2. 修改文字:
   Prompt: "把图中的 'OPEN' 改成 'CLOSED'"
   → 保持原文字大小、字体、颜色，仅改内容

3. 删除文字:
   Prompt: "删除图片中所有文字"
   → 自然修复文字所在区域

4. 双语支持:
   Prompt: "将英文标题翻译成中文，保持相同样式"
   → 中英文渲染质量均优

这是其他模型（Flux/ICEdit）难以做到的
```

### 7.4 ComfyUI 原生集成

```
模型文件:
📂 ComfyUI/models/
├── diffusion_models/
│   └── qwen_image_edit_fp8_e4m3fn.safetensors
├── loras/
│   └── Qwen-Image-Lightning-4steps-V1.0.safetensors (加速)
├── vae/
│   └── qwen_image_vae.safetensors
└── text_encoders/
    └── qwen_2.5_vl_7b_fp8_scaled.safetensors

工作流结构:
LoadDiffusionModel (qwen_image_edit_fp8)
  ↓ model
LoadCLIP (qwen_2.5_vl_7b_fp8_scaled)
  ↓ clip
[可选] LoRALoader (Qwen-Image-Lightning-4steps) → 4步加速
  ↓ model + clip
LoadVAE (qwen_image_vae)
  ↓ vae
LoadImage → ScaleImageToTotalPixels (1M像素上限)
  ↓ image
CLIPTextEncode ← "编辑指令"
  ↓ positive
ModelSamplingFlux (shift) + BasicGuider + BasicScheduler
  ↓
SamplerCustomAdvanced → VAEDecode → SaveImage

注意:
- ScaleImageToTotalPixels 避免超大输入导致质量下降
- 输入图像建议不超过 1024×1024
- Lightning LoRA 可将步数从 20-30 降至 4 步
```

### 7.5 Qwen-Image-Layered（2025-12 扩展）

```
Qwen-Image-Layered 分层编辑:
- 将图像分解为多个 RGBA 图层
- 每层独立可编辑（重新着色/替换/删除/缩放/移位）
- 不影响其他图层内容
- 类似 Photoshop 的分层概念，但 AI 驱动

这是迈向"AI 原生图像编辑器"的重要一步
```

---

## 8. OmniGen2 — 统一多模态生成与编辑

### 8.1 模型概要

- **模型**: OmniGen2（2025-06, VectorSpaceLab）
- **架构**: 3B VLM + 4B DiT = ~7B 总参数
- **论文**: arXiv:2506.18871
- **核心**: 统一理解+生成，自然语言驱动一切

### 8.2 架构设计

```
OmniGen2 双组件架构:

输入: 文本指令 + [可选] 参考图像
  ↓
┌──────────────────┐
│ 3B Vision-Language│ ← 理解图像+文本
│ Model (VLM)       │    生成中间表示
└────────┬─────────┘
         ↓ intermediate representation
┌──────────────────┐
│ 4B Diffusion      │ ← 基于理解生成/编辑
│ Transformer (DiT) │    图像
└────────┬─────────┘
         ↓
      输出图像

关键: VLM 负责"理解"，DiT 负责"生成"
      自然语言指令统一驱动所有任务
```

### 8.3 编辑能力

```
OmniGen2 支持的编辑操作:

1. Object Removal: "Remove the person on the left"
2. Object Replacement: "Replace the cat with a dog"
3. Style Transfer: "Apply Van Gogh style to <image_1>"
4. Background Processing: "Change background to a sunset beach"
5. Multi-Image Composition: "Put the person from <image_1> into the scene of <image_2>"
6. Attribute Editing: "Make the car blue" / "Add sunglasses to the person"

多图引用语法: <image_1>, <image_2>, ...
```

### 8.4 ComfyUI 原生支持

2025-07-01 起 ComfyUI 官方原生支持 OmniGen2：

```
工作流结构:
LoadDiffusionModel (omnigen2_dit_4b.safetensors)
  ↓ model
LoadCLIP (omnigen2_vlm_3b.safetensors)
  ↓ clip
LoadVAE (omnigen2_vae.safetensors)
  ↓ vae
LoadImage → OmniGen2ImageEncode
  ↓ image_conditioning
CLIPTextEncode ← "Remove the background and replace with a forest"
  ↓ text_conditioning
Combine Conditions → KSampler → VAEDecode → SaveImage
```

### 8.5 OmniGen2 vs 专用编辑模型

| 维度 | OmniGen2 | Flux Kontext | ICEdit | Qwen-Image-Edit |
|------|---------|-------------|--------|-----------------|
| 参数量 | 7B | 12B | LoRA | 20B |
| 编辑质量 | 良好 | 优秀 | 优秀 | 优秀(文字SOTA) |
| 多图组合 | ✅ 原生 | ✅ | ❌ | ❌ |
| 文本渲染 | 一般 | 一般 | 一般 | **SOTA** |
| T2I 能力 | ✅ 统一 | ❌ 需Flux Dev | ❌ 需Flux Dev | ✅ 统一 |
| 本地部署 | ~14GB | ~20GB | 4-14GB | ~24GB |

---

## 9. ComfyUI 编辑节点体系总览

### 9.1 内置编辑节点

```
ComfyUI 原生编辑相关节点:

条件准备:
├── InstructPixToPixConditioning — IP2P/CosXL Edit 条件
├── InpaintModelConditioning — Flux Fill / SD Inpaint 条件
├── ConditioningSetMask — 通用 mask 条件注入
└── SetLatentNoiseMask — latent 空间 mask

图像操作:
├── PadImageForOutpainting — outpainting 画布扩展
├── ImageComposite — 图像合成
├── ImageCrop / ImageScale — 裁剪/缩放
└── MaskComposite — mask 运算

Flux 专用:
├── FluxGuidance — Flux guidance scale
└── FluxKontextImageEncode — Kontext 图像编码
```

### 9.2 第三方编辑节点

```
ICEdit:
├── River-Zhang/ICEdit — 官方 ComfyUI 工作流
│   ├── ICEditNode — 核心编辑节点
│   └── ICEditRefineNode — 高分辨率精炼

Qwen-Image:
├── lrzjason/Comfyui-QwenEditUtils — Qwen 编辑工具
│   └── 自定义 Llama 模板

OmniGen2:
├── Yuan-ManX/ComfyUI-OmniGen2 — 社区节点包
└── 原生支持（2025-07+）

通用编辑:
├── Impact Pack — SEGS/FaceDetailer/CropAndStitch
├── ComfyUI-RMBG — 背景移除
├── comfyui-segment-anything — 分割蒙版
└── ComfyUI-Florence2 — 多任务视觉理解
```

### 9.3 编辑工作流节点对比

| 任务 | 推荐方案 | 核心节点 | 难度 |
|------|---------|---------|------|
| 物体替换 | Flux Fill | InpaintModelConditioning | ⭐⭐ |
| 风格迁移 | Flux Kontext / ICEdit | FluxKontextImageEncode | ⭐⭐ |
| 文字编辑 | Qwen-Image-Edit | LoadDiffusionModel + CLIPTextEncode | ⭐⭐ |
| 背景替换 | RMBG + Flux Fill | ComfyUI-RMBG + InpaintModelConditioning | ⭐⭐⭐ |
| 人脸修复 | FaceDetailer | FaceDetailer (Impact Pack) | ⭐⭐ |
| 物体移除 | Flux Fill / ICEdit | InpaintModelConditioning / ICEditNode | ⭐⭐ |
| 画面扩展 | Flux Fill | PadImageForOutpainting | ⭐⭐ |
| 视频编辑 | VACE | WanVaceToVideo | ⭐⭐⭐⭐ |
| 多图组合 | OmniGen2 / Kontext | OmniGen2ImageEncode | ⭐⭐⭐ |

---

## 10. 编辑方法全维度对比

### 10.1 综合对比表

```
┌───────────────┬────────┬──────────┬──────┬───────┬──────────┬──────────┐
│ 方法           │ 基座    │ 编辑方式  │ VRAM │ 速度   │ ID保持    │ 适用场景  │
├───────────────┼────────┼──────────┼──────┼───────┼──────────┼──────────┤
│ InstructPix2Pix│ SD 1.5 │ 全图指令  │ 4GB  │ 快     │ ⭐⭐      │ 简单编辑  │
│ CosXL Edit    │ SDXL   │ 全图指令  │ 8GB  │ 中     │ ⭐⭐⭐    │ 中等编辑  │
│ Flux Fill     │ Flux   │ Mask重绘  │ 20GB │ 中     │ ⭐⭐⭐⭐  │ 精确区域  │
│ Flux Kontext  │ Flux   │ 上下文    │ 20GB │ 中     │ ⭐⭐⭐⭐⭐│ 多场景    │
│ ICEdit        │ Flux   │ Diptych  │ 4-14 │ 快     │ ⭐⭐⭐⭐⭐│ 通用编辑  │
│ ICEdit MoE    │ Flux   │ Diptych  │ 4GB  │ 最快   │ ⭐⭐⭐⭐⭐│ 通用编辑  │
│ Qwen-Image-Ed │ 20B    │ VLM指令  │ 24GB │ 中慢   │ ⭐⭐⭐⭐  │ 文字编辑  │
│ OmniGen2      │ 7B     │ VLM指令  │ 14GB │ 中     │ ⭐⭐⭐⭐  │ 统一多任务│
│ VACE          │ Wan14B │ Mask序列  │ 40GB │ 慢     │ ⭐⭐⭐⭐  │ 视频编辑  │
└───────────────┴────────┴──────────┴──────┴───────┴──────────┴──────────┘
```

### 10.2 方法选择决策树

```
需要编辑什么？
├── 视频编辑 → VACE
├── 精确区域重绘（有 mask）→ Flux Fill
├── 文字编辑（添加/修改/删除图中文字）→ Qwen-Image-Edit
├── 多图组合/角色一致性 → Flux Kontext 或 OmniGen2
├── 通用指令编辑（无 mask）
│   ├── 低 VRAM (≤8GB) → ICEdit MoE (4GB!)
│   ├── 中 VRAM (8-16GB) → ICEdit normal LoRA
│   └── 高 VRAM (≥20GB) → Flux Kontext
├── 风格迁移 → Flux Kontext (style reference)
├── 背景替换 → RMBG + Flux Fill 管线
└── 简单快速编辑（不需要高质量）→ InstructPix2Pix / CosXL Edit
```

---

## 11. 生产级编辑工作流模式

### 11.1 模式一: 精确局部编辑管线

```
用户需求 → 文本描述目标
  ↓
GroundingDINO → "the red car" → bounding box
  ↓
SAM2 → 精确分割蒙版
  ↓
Flux Fill + InpaintModelConditioning
  ↓ "a blue sports car"
编辑结果 → 人脸检测 → FaceDetailer (如有人脸)
  ↓
Topaz Upscale (可选) → 最终输出
```

### 11.2 模式二: 多轮迭代编辑

```
原图 → Round 1: Flux Kontext ("change hair to blonde")
  ↓ result_1
result_1 → Round 2: Flux Kontext ("add sunglasses")
  ↓ result_2
result_2 → Round 3: Flux Fill + mask ("replace background")
  ↓ result_3
result_3 → Round 4: Qwen-Image-Edit ("add text 'SUMMER' at top")
  ↓ final

关键: 使用 Load Image (from output) 节点实现自动链式编辑
```

### 11.3 模式三: 批量产品图编辑

```
产品图列表 (CSV)
  ↓
batch_edit.py (基于 ComfyUI API)
  ├── 读取每张产品图
  ├── 自动移除背景 (RMBG)
  ├── Flux Fill outpainting (统一画布)
  ├── 添加品牌文字 (Qwen-Image-Edit)
  └── 保存到 output/

适用: 电商场景的批量产品图处理
```

### 11.4 模式四: 图像→视频编辑管线

```
原图 → ICEdit ("make the character smile")
  ↓ edited_image
edited_image → Seedance/Kling I2V ("the character turns and smiles")
  ↓ video
video → VACE ("replace background in all frames")
  ↓ edited_video
edited_video → Frame Interpolation + Upscale → final_video
```

---

## 12. RunningHub 实验

### 实验 #54: 图像编辑技术全景概念图

- **端点**: rhart-image-n-pro/text-to-image
- **Prompt**: 编辑技术全景信息图
- **参数**: aspectRatio=3:4, resolution=1K
- **耗时**: 35s
- **成本**: ¥0.03
- **结果**: 生成了包含各编辑方法的概念信息图

### 实验 #55: 图生图风格编辑（全能图片PRO）

- **端点**: rhart-image-n-pro/edit
- **输入**: 实验#54 生成的信息图
- **编辑指令**: "Transform into dark cyberpunk theme with neon glowing edges, holographic overlays"
- **耗时**: 30s
- **成本**: ¥0.03
- **结果**: 成功将信息图转化为赛博朋克风格，保持了整体布局
- **分析**: 全图风格迁移效果好，但具体文字可读性下降

### 实验 #56: Qwen 2.0 Pro 图像编辑

- **端点**: alibaba/qwen-image-2.0-pro/image-edit
- **输入**: 同实验#54 信息图
- **编辑指令**: "Replace the background with a serene Japanese zen garden"
- **耗时**: 20s
- **成本**: ¥0.05
- **结果**: 背景替换较成功，保持了前景元素
- **分析**: Qwen 的语义理解能力强，编辑精确度高
- **对比**: Qwen 编辑比 rhart 风格迁移更精确，但成本略高

### 实验成本汇总

| 实验 | 端点 | 类型 | 耗时 | 成本 |
|------|------|------|------|------|
| #54 | rhart-image-n-pro/T2I | 概念图 | 35s | ¥0.03 |
| #55 | rhart-image-n-pro/edit | 风格编辑 | 30s | ¥0.03 |
| #56 | qwen-image-2.0-pro/edit | 背景替换 | 20s | ¥0.05 |
| **总计** | | | **85s** | **¥0.11** |

---

## 附录: 关键源码函数速查

### InstructPixToPixConditioning

```python
# comfy/nodes.py
class InstructPixToPixConditioning:
    # 将源图像编码并拼接到 latent 空间
    # positive/negative conditioning 增加 concat_latent_image 元数据
    # KSampler 采样时自动拼接额外通道
```

### InpaintModelConditioning

```python
# comfy/nodes.py  
class InpaintModelConditioning:
    # 1. 源图像 × (1-mask) → VAE encode → latent
    # 2. mask 下采样到 latent 空间
    # 3. 注入 noise_mask 到 LATENT dict
    # 4. 注入 concat_latent_image 到 conditioning metadata
```

### PadImageForOutpainting

```python
# comfy/nodes.py
class ImagePadForOutpainting:
    # 1. 创建更大画布，原图居中放置
    # 2. 自动生成 mask（扩展区域=白色）
    # 3. 边缘 feathering（线性渐变融合）
    # 4. 返回 padded_image + auto_mask
```

---

## 总结

Day 31 覆盖了图像编辑的完整技术栈：

1. **历史线索**: InstructPix2Pix 开创指令编辑 → CosXL 迁移到 SDXL → ICEdit 用 DiT 上下文能力革新范式
2. **当前 SOTA**: Flux Kontext (上下文编辑) + ICEdit (效率之王) + Qwen-Image-Edit (文字编辑独步天下)
3. **统一趋势**: OmniGen2/Qwen-Image 走向理解+生成统一，编辑成为生成模型的子能力
4. **ComfyUI 生态**: 从内置节点 (InpaintModelConditioning) 到第三方 (ICEdit/OmniGen2) 形成完整工具链
5. **生产实践**: Flux Fill 精确区域 + Kontext 上下文 + ICEdit 高效指令 = 覆盖 95% 编辑场景
6. **视频扩展**: VACE 将图像编辑范式自然扩展到视频时间维度

**下一步 (Day 32)**: 3D 生成与多视角（TripoSR / InstantMesh / Zero123++ / ComfyUI 3D 节点）
