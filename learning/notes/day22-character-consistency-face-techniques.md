# Day 22: 角色一致性与人脸技术 (Character Consistency & Face Techniques)

> 学习日期: 2026-03-22 | 轮次: 30
> 主题: IP-Adapter / InstantID / PuLID / ReActor / PhotoMaker — 全技术栈深度解析

---

## 1. 角色一致性技术全景

### 1.1 问题定义

角色一致性 (Character Consistency) 是 AI 图像/视频生成中最具挑战性的问题之一：
- **核心矛盾**: 生成模型天然倾向于每次生成不同的面部特征
- **应用场景**: 虚拟偶像、广告素材、漫画/动画制作、影视前期可视化、游戏角色设计
- **关键指标**: 面部识别准确率 (Face Recognition Accuracy)、自然度、Prompt 遵从度

### 1.2 技术路线分类

```
角色一致性技术
├── 🎯 训练型 (Training-based)
│   ├── LoRA 微调 — 最高保真度，需数据+训练时间
│   ├── Textual Inversion — 学习 token embedding
│   └── DreamBooth — 全模型微调
├── 🔌 零样本型 (Zero-shot / Tuning-free)
│   ├── IP-Adapter 系列 — 解耦交叉注意力
│   │   ├── IP-Adapter (风格/内容迁移)
│   │   ├── IP-Adapter FaceID (面部身份)
│   │   ├── IP-Adapter FaceID Plus V2 (CLIP+Face 双路)
│   │   └── IP-Adapter Portrait (肖像风格迁移)
│   ├── InstantID — InsightFace + ControlNet + IP-Adapter
│   ├── PuLID — 对比对齐 + 闪电 T2I 双分支
│   └── PhotoMaker — 堆叠 ID Embedding (CVPR 2024)
├── 🔄 人脸替换型 (Face Swap)
│   ├── ReActor — InsightFace inswapper_128
│   ├── DeepFuze — 视频换脸
│   └── FaceShaper — 人脸形状控制
└── 🔀 组合型 (Hybrid Pipeline)
    ├── PuLID 生成 + ReActor 精修
    ├── InstantID + ControlNet Canny 多重控制
    └── IP-Adapter + AnimateDiff 视频一致性
```

### 1.3 技术演进时间线

```
2023.08  IP-Adapter 发布 (Tencent AI Lab) — 解耦交叉注意力开创性工作
2023.12  PhotoMaker 发布 (TencentARC) — 堆叠 ID Embedding
2024.01  IP-Adapter FaceID 系列 — InsightFace 面部嵌入
2024.02  InstantID 发布 (InstantX) — 零样本身份保持
2024.04  PuLID 发布 — 对比对齐最小化模型污染
2024.09  PuLID-FLUX 发布 — 适配 Flux 架构
2024.10  PuLID v2 — 增强版
2025.02  cubiq IPAdapter Plus 维护模式 — 社区接手
2025.06  comfyorg/comfyui-ipadapter — 官方分支
```

---

## 2. IP-Adapter 架构深度解析

### 2.1 核心论文 (arXiv:2308.06721)

**核心创新: 解耦交叉注意力 (Decoupled Cross-Attention)**

传统 Text-to-Image 中，U-Net 的交叉注意力层：
```
Attention(Q, K_text, V_text) = softmax(Q·K_text^T / √d) · V_text
```

IP-Adapter 添加并行的图像注意力分支：
```
Output = Attention(Q, K_text, V_text) + λ · Attention(Q, K_image, V_image)
```

其中:
- Q 来自 U-Net latent features
- K_text, V_text 来自 CLIP Text Encoder
- K_image, V_image 来自 CLIP Image Encoder → 新增的可训练投影层
- λ 是权重缩放因子 (weight)

### 2.2 架构组件

```
┌─────────────────────────────────────────┐
│              IP-Adapter 架构              │
├─────────────────────────────────────────┤
│                                         │
│  参考图像 ──→ [CLIP ViT-H/14] ──→ 图像特征 (257 tokens, 1024d)
│                     │                   │
│                     ↓                   │
│            [Trainable Projection]       │
│            (Linear → LayerNorm)         │
│                     │                   │
│                     ↓                   │
│              K_img, V_img               │
│                     │                   │
│  U-Net Q ───────────┼──────────────→ [Cross-Attn Text]  │
│                     │                   │
│                     └──────────────→ [Cross-Attn Image] │
│                                         │
│  最终输出 = Text_Attn + weight × Image_Attn  │
└─────────────────────────────────────────┘
```

### 2.3 IP-Adapter 变体全家族

| 变体 | CLIP 编码器 | 额外组件 | 特点 | 参数量 |
|------|------------|---------|------|--------|
| IP-Adapter (SD1.5) | ViT-H/14 | 无 | 基础风格迁移 | ~22M |
| IP-Adapter Plus | ViT-H/14 | Perceiver Resampler | 更精细特征 | ~30M |
| IP-Adapter Plus Face | ViT-H/14 (face crop) | Perceiver Resampler | 肖像优化 | ~30M |
| IP-Adapter FaceID | ArcFace (512d) | LoRA | 面部身份嵌入 | ~LoRA额外 |
| IP-Adapter FaceID Plus V2 | ViT-H + ArcFace | LoRA | 双路融合最强 | ~LoRA+适配器 |
| IP-Adapter Portrait | InsightFace | 无 LoRA | 风格迁移肖像 | ~22M |
| IP-Adapter SDXL | ViT-bigG/14 | 无 | SDXL 基础 | ~22M |
| IP-Adapter Flux | 待定 | 待定 | Flux 适配 | 实验中 |

### 2.4 IP-Adapter FaceID 技术细节

**与普通 IP-Adapter 的关键区别:**

普通 IP-Adapter:
```
图像 → CLIP ViT-H → 全局语义特征 (包含背景、构图、风格)
```

FaceID:
```
图像 → InsightFace ArcFace → 面部身份嵌入 (512d, 纯身份信息)
       → 投影到 CLIP 空间 → 解耦交叉注意力注入
```

**FaceID Plus V2 (双路融合):**
```
图像 → InsightFace ArcFace → 身份嵌入 (512d)  ──┐
                                                 ├──→ 融合 → Cross-Attn
图像 → CLIP ViT-H → CLIP 特征 (1024d)         ──┘
```

- InsightFace 提供高保真身份信息
- CLIP ViT-H 提供细节特征 (肤色、纹理、妆容)
- 双路融合 = 身份保持 + 视觉细节

**需要配套 LoRA 的原因:**
FaceID 模型替换了 CLIP 图像特征空间，ArcFace 512d → CLIP 空间的映射需要额外的 LoRA 来帮助 U-Net 适配这种新的条件格式。

### 2.5 ComfyUI_IPAdapter_plus 节点体系

cubiq 的参考实现 (4.93K ⭐, 2025.04 进入维护模式):

**核心节点:**
- `IPAdapterUnifiedLoader` — 自动匹配模型+CLIP 编码器
- `IPAdapterUnifiedLoaderFaceID` — FaceID 专用加载器 (自动加载 InsightFace)
- `IPAdapter` — 基础适配器应用
- `IPAdapterAdvanced` — 高级控制 (weight_type, start/end_at, combine_embeds)
- `IPAdapterFaceID` — FaceID 专用 (weight_v2, 多人脸支持)
- `IPAdapterBatch` — 批量/动画支持
- `IPAdapterTiled` — 分块处理大图
- `IPAdapterStyleComposition` — 风格+构图分离控制

**Weight Types (注意力权重注入方式):**
```python
WEIGHT_TYPES = [
    "linear",           # 所有层等权重
    "ease in",          # 前面层权重低，后面高（细节强化）
    "ease out",         # 前面层权重高，后面低（结构强化）
    "ease in-out",      # 中间层权重最高
    "reverse in-out",   # 两端高中间低
    "weak input",       # 输入块弱化
    "weak output",      # 输出块弱化
    "weak middle",      # 中间块弱化
    "strong middle",    # 中间块强化（推荐用于面部）
    "style transfer",   # 仅 style 层（用于风格迁移）
    "composition",      # 仅构图层
    "strong style transfer",   # 更强风格
    "style and composition",   # 风格+构图
    "strong style and composition",
]
```

**start_at / end_at 参数:**
- 控制 IP-Adapter 在采样过程的哪个阶段生效
- `start_at=0, end_at=1` = 全程生效
- `start_at=0, end_at=0.5` = 只在前半段生效（结构+身份，后半段细节自由发挥）
- 推荐: FaceID 用 `end_at=0.8`，避免过度约束细节

---

## 3. InstantID 架构深度解析

### 3.1 核心论文 (InstantX Research, 2024)

**设计理念: 零样本身份保持生成 (Zero-shot Identity-Preserving Generation)**

### 3.2 三组件架构

```
┌────────────────────────────────────────────────────────────┐
│                    InstantID 架构                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  参考人脸图像                                               │
│       │                                                    │
│       ├──→ [InsightFace AntelopeV2] ──→ 面部嵌入 (512d)    │
│       │         │                                          │
│       │         ├──→ 面部关键点 (kps)                       │
│       │         │         │                                │
│       │         │         ↓                                │
│       │         │    [IdentityNet ControlNet]               │
│       │         │    (面部空间结构引导)                      │
│       │         │         │                                │
│       │         ↓         │                                │
│       │    [IP-Adapter]   │                                │
│       │    (身份语义注入)  │                                │
│       │         │         │                                │
│       │         ↓         ↓                                │
│       └──→  [SDXL U-Net] ←──── text prompt                │
│                  │                                         │
│                  ↓                                         │
│            生成结果图像                                      │
└────────────────────────────────────────────────────────────┘
```

### 3.3 三大组件详解

**1. InsightFace AntelopeV2 (面部分析)**
- 检测人脸边界框
- 提取 512d 面部身份嵌入 (ArcFace 特征)
- 提取 5 点关键点 (eyes, nose, mouth corners)
- ONNX 格式，CPU/GPU 均可运行

**2. IdentityNet (定制 ControlNet)**
- 基于 ControlNet 架构的身份空间控制
- 输入: 从关键点生成的面部结构图
- 注入方式: 与标准 ControlNet 相同（零卷积 → U-Net 各层）
- 控制面部的**空间布局** (位置、大小、朝向)

**3. IP-Adapter 模块 (语义注入)**
- 接收 InsightFace 512d embedding
- 投影到 CLIP 空间
- 通过解耦交叉注意力注入
- 控制面部的**身份特征** (长相、五官比例)

### 3.4 InstantID vs IP-Adapter FaceID 关键区别

| 维度 | InstantID | IP-Adapter FaceID |
|------|-----------|-------------------|
| 空间控制 | ControlNet 关键点引导 | 无（纯语义） |
| 面部结构 | 精确控制位置/角度 | 依赖 prompt/其他 ControlNet |
| 模型依赖 | SDXL only (原版) | SD1.5 / SDXL 都支持 |
| 额外 LoRA | 不需要 | 大部分需要 |
| Prompt 遵从 | 中等 (ControlNet 会约束) | 高 (更灵活) |
| 身份保真度 | 高 (84%) | 中 (79%) |

### 3.5 ComfyUI_InstantID 节点

cubiq 的 ComfyUI 实现:

**核心节点:**
- `InstantIDFaceAnalysis` — 加载 AntelopeV2 模型
- `InstantIDModelLoader` — 加载 InstantID IP-Adapter 权重
- `ApplyInstantID` — 应用 InstantID (ip_weight + cn_strength 分别控制)
- `ApplyInstantIDAdvanced` — 高级版 (start_at/end_at + noise)

**关键参数:**
```python
# ip_weight: IP-Adapter 身份语义强度 (0-3, 推荐 0.8-1.2)
# cn_strength: ControlNet 空间结构强度 (0-2, 推荐 0.4-0.7)
# start_at: IP-Adapter 开始时间 (推荐 0)
# end_at: IP-Adapter 结束时间 (推荐 0.8-1.0)
# noise: InsightFace embedding 噪声 (0-1, 推荐 0.35, 增加多样性)
```

**典型工作流拓扑:**
```
[LoadCheckpoint(SDXL)] → model
[LoadImage(face)] → [InstantIDFaceAnalysis] → face_embeds, face_kps
[InstantIDModelLoader] → instantid_model
model + face_embeds + face_kps + instantid_model → [ApplyInstantID] → model_conditioned
model_conditioned + prompt → [KSampler] → latent → [VAEDecode] → image
```

---

## 4. PuLID 架构深度解析

### 4.1 核心论文 (NeurIPS 2024, arXiv:2404.16022)

**全称: Pure and Lightning ID Customization via Contrastive Alignment**

**核心创新: 双分支训练 + 对比对齐**

### 4.2 训练架构

PuLID 解决的关键问题: 其他身份注入方法（IP-Adapter、InstantID）在注入身份信息时会"污染"原始模型的生成能力——即使不提供参考图，模型的输出也会偏移。

```
┌──────────────────────────────────────────────────────────┐
│                    PuLID 训练架构                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────┐  ┌────────────────────────┐  │
│  │  Standard Diffusion    │  │  Lightning T2I         │  │
│  │  Branch (慢速/高质)    │  │  Branch (快速预览)     │  │
│  │                        │  │                        │  │
│  │  完整扩散过程           │  │  加速采样 (4步)        │  │
│  │  + ID 注入              │  │  + ID 注入            │  │
│  │       ↓                │  │       ↓                │  │
│  │  生成结果 G_std         │  │  生成结果 G_light      │  │
│  └────────┬───────────────┘  └────────┬───────────────┘  │
│           │                           │                  │
│           ↓                           ↓                  │
│    ┌──────────────────────────────────────┐              │
│    │         Contrastive Alignment        │              │
│    │  L_align = -log(sim(G_std, ref))     │              │
│    │         + log(sim(G_std, neg))       │              │
│    └──────────────────────────────────────┘              │
│           +                                              │
│    ┌──────────────────────────────────────┐              │
│    │         Accurate ID Loss             │              │
│    │  L_id = 1 - cos(F(G), F(ref))       │              │
│    │  F = InsightFace 面部特征提取         │              │
│    └──────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

### 4.3 关键技术点

**1. Lightning T2I Branch**
- 使用 SDXL-Lightning/Turbo 作为快速预览分支
- 训练时同时生成标准版和闪电版
- 闪电分支的作用: 提供快速反馈信号，让模型学会在不注入 ID 时保持原始行为

**2. Contrastive Alignment Loss**
- 正样本: 生成图像 vs 参考身份图像（应该相似）
- 负样本: 生成图像 vs 其他身份图像（应该不相似）
- 效果: 让模型精确学习"什么是该保留的身份信息"，而非污染全局特征空间

**3. Accurate ID Loss**
- 直接在 InsightFace 特征空间计算余弦相似度
- 确保面部识别系统认为生成结果和参考是同一人

**4. 纯净性 (Purity)**
- PuLID 的"Pure"指: 不注入 ID 时，模型行为与原始模型完全一致
- 量化指标: FID 偏移最小（<0.5）
- 其他方法 (IP-Adapter/InstantID) 即使 weight=0 也有微弱偏移

### 4.4 PuLID-FLUX 适配

PuLID 最初为 SDXL 设计，后适配 Flux:
- 替换 U-Net 注入点为 DiT 对应的注意力层
- 适配 Flux 的 Double-Stream / Single-Stream 架构
- ID 注入点选择: 主要在 Double-Stream Blocks（保持模态分离的优势）
- 模型文件: `pulid_flux_v0.9.1.safetensors` (~800MB)

### 4.5 PuLID vs InstantID 关键区别

| 维度 | PuLID | InstantID |
|------|-------|-----------|
| 训练方法 | 对比对齐 + 双分支 | IP-Adapter 标准训练 |
| 模型纯净性 | 极高（无 ID 时 ≈ 原始模型） | 中等（有微弱偏移） |
| 身份保真度 | 91% (最高) | 84% |
| 空间控制 | 无 ControlNet | 有 ControlNet 关键点 |
| 自然度 | 92% (最高) | 86% |
| Prompt 遵从 | 83% (最低) | 88% |
| VRAM | 10.2GB (最高) | 8.5GB |
| 速度 | 35s (最慢) | 28s |
| 支持架构 | SDXL + Flux | SDXL only |

### 4.6 ComfyUI PuLID 节点

**ComfyUI-PuLID (balazik 实现):**
- `PulidModelLoader` — 加载 PuLID 模型
- `PulidInsightFaceLoader` — 加载 InsightFace
- `ApplyPulid` — 应用 PuLID
- `ApplyPulidFlux` — Flux 专用版本

**关键参数:**
```python
# weight: 身份强度 (0-5, 推荐 0.8-1.0)
# start_at: 注入开始点 (推荐 0)
# end_at: 注入结束点 (推荐 1.0)
# method: "fidelity" (保真) | "style" (风格)
# fidelity = 更像参考脸，style = 更像 prompt 描述的风格
```

---

## 5. PhotoMaker 架构解析

### 5.1 核心论文 (CVPR 2024, arXiv:2312.04461)

**核心创新: 堆叠 ID Embedding (Stacked ID Embedding)**

### 5.2 架构设计

```
┌────────────────────────────────────────────────┐
│                PhotoMaker 架构                   │
├────────────────────────────────────────────────┤
│                                                │
│  N 张参考图像 (1-4张)                           │
│       │                                        │
│       ↓                                        │
│  [CLIP Image Encoder] × N                      │
│       │                                        │
│       ↓                                        │
│  N 个 CLIP image embedding                     │
│       │                                        │
│       ↓                                        │
│  [MLP Projection] — 将图像特征投射到文本空间     │
│       │                                        │
│       ↓                                        │
│  Stacked ID Embedding (多张图 → 堆叠)          │
│       │                                        │
│       ↓                                        │
│  与 Text Embedding 合并 (替换 trigger token)    │
│       │                                        │
│       ↓                                        │
│  [SDXL U-Net Cross-Attention]                  │
│       │                                        │
│       ↓                                        │
│  生成结果                                       │
└────────────────────────────────────────────────┘
```

### 5.3 关键特性

- **多图输入**: 支持 1-4 张参考图像，多张图像提供不同角度/表情
- **堆叠嵌入**: 多图的 embedding 通过 MLP 融合后堆叠，增强身份信息
- **Trigger Token**: 在 prompt 中使用特殊 token（如 "img"）标记身份位置
- **数据管线**: 自建大规模 ID 配对数据集训练

### 5.4 PhotoMaker V2

- 改进的 ID 嵌入融合方案
- 更好的多角度一致性
- 与 LCM 加速兼容
- 可与 IP-Adapter FaceID / InstantID 组合使用

---

## 6. ReActor 人脸替换深度解析

### 6.1 技术原理

ReActor 与上述方法有本质不同——它是**后处理型人脸替换**，不参与扩散过程：

```
┌──────────────────────────────────────────────┐
│               ReActor 管线                    │
├──────────────────────────────────────────────┤
│                                              │
│  源人脸图像 → [InsightFace] → 源人脸嵌入      │
│                                              │
│  目标图像 → [InsightFace] → 检测目标人脸      │
│                  │                           │
│                  ↓                           │
│  [inswapper_128] — ONNX 人脸替换模型          │
│  (128×128 分辨率内部处理)                     │
│                  │                           │
│                  ↓                           │
│  替换后的 128×128 人脸                        │
│                  │                           │
│                  ↓                           │
│  [后处理修复]                                 │
│  ├── GFPGAN (GAN 人脸修复)                   │
│  ├── CodeFormer (Transformer 人脸修复)        │
│  └── RestoreFormer++                         │
│                  │                           │
│                  ↓                           │
│  [Mask 融合] — 将修复后的人脸贴回原图          │
│                  │                           │
│                  ↓                           │
│  最终结果                                     │
└──────────────────────────────────────────────┘
```

### 6.2 ReActor 的致命限制: 128px

- inswapper_128 模型在 128×128 分辨率下工作
- 直接输出会模糊！必须配合人脸修复
- **社区最佳实践**: ReActor + FaceDetailer (Impact Pack)
  1. ReActor 执行基础人脸替换 (128px)
  2. FaceDetailer 检测人脸区域
  3. 裁剪 → SD 重绘 (高分辨率) → 贴回
  4. 最终质量远超单纯 ReActor

### 6.3 ReActor vs ID 注入方法对比

| 维度 | ReActor (后处理) | PuLID/InstantID (扩散注入) |
|------|-----------------|--------------------------|
| 工作阶段 | 生成后替换 | 生成过程中注入 |
| 身份精度 | 极高 (~98%) | 高 (84-91%) |
| 自然度 | 中等 (边缘伪影) | 高 (无缝融合) |
| 角度适应 | 差 (正脸最好) | 好 (任意角度) |
| 表情控制 | 差 (保持源表情) | 好 (prompt 控制) |
| 速度 | 极快 (<1s) | 中等 (25-35s) |
| 多人支持 | 好 (逐个替换) | 有限 |
| 视频适用 | 好 (逐帧处理) | 差 (需逐帧生成) |

### 6.4 ComfyUI ReActor 节点

**核心节点 (Gourieff/ComfyUI-ReActor):**
- `ReActorFaceSwap` — 主换脸节点
- `ReActorFaceSwapOpt` — 带可选参数的换脸
- `ReActorBuildFaceModel` — 从图像构建面部模型 (.safetensors)
- `ReActorLoadFaceModel` — 加载预保存的面部模型
- `ReActorRestoreFace` — GFPGAN/CodeFormer 人脸修复
- `ReActorMaskHelper` — 遮罩辅助

**关键参数:**
- `face_restore_model`: GFPGAN / CodeFormer 选择
- `face_restore_visibility`: 修复强度 (0-1, 推荐 1.0)
- `codeformer_weight`: CodeFormer fidelity (0-1, 推荐 0.5)

---

## 7. 生产级组合工作流

### 7.1 方案 A: PuLID 生成 + ReActor 精修 (推荐)

**适用场景**: 需要最高身份保真度的专业肖像/商业图像

```
工作流拓扑:
[LoadCheckpoint(SDXL/Flux)] → model
[LoadImage(face_ref)] → reference

Stage 1: PuLID 基础生成
reference → [PuLID] → conditioned_model
conditioned_model + prompt → [KSampler] → base_image

Stage 2: ReActor 精修
reference + base_image → [ReActor] → swapped_image

Stage 3: FaceDetailer 增强
swapped_image → [FaceDetailer] → final_image
```

**为什么组合优于单独使用:**
- PuLID 保证整体构图自然 + 风格正确
- ReActor 将面部精确度提升到 ~98%
- FaceDetailer 修复 ReActor 的 128px 限制

### 7.2 方案 B: InstantID + ControlNet Canny (多重控制)

**适用场景**: 需要精确控制姿态/构图的场景

```
[LoadImage(face)] → [InstantIDFaceAnalysis] → embeds + kps
[LoadImage(pose_ref)] → [CannyEdgePreprocessor] → canny_map

model + embeds + kps → [ApplyInstantID] → model_id
model_id + canny_map → [ControlNetApply] → model_id_canny
model_id_canny + prompt → [KSampler] → image
```

### 7.3 方案 C: IP-Adapter + AnimateDiff (视频一致性)

**适用场景**: 动画/视频中保持角色一致

```
model → [ApplyAnimateDiff(motion_module)] → model_anim
model_anim + face_ref → [IPAdapterFaceID] → model_face
model_face + prompt → [KSampler(batch=16)] → video_latents
video_latents → [VAEDecode] → video_frames
```

**关键技巧:**
- IP-Adapter weight 设 0.7-0.85（太高会限制运动自由度）
- AnimateDiff ContextOptions: Standard Uniform, context_length=16
- FreeNoise: 开启（减少帧间闪烁）
- ControlNet OpenPose: 可选（进一步约束身体姿态一致性）

### 7.4 方案 D: LoRA + 零样本方法混合

**适用场景**: 长期角色项目 (品牌形象大使、虚拟偶像)

```
1. 用 InstantID + Canny 生成 10-20 张多角度一致图像
2. 用这些图像训练角色 LoRA (sd-scripts, dim=32, 20 epoch)
3. 生产时: LoRA + IP-Adapter (低权重 0.3-0.5 辅助) → 最高一致性
```

---

## 8. 全方法对比总结

### 8.1 性能基准对比

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    角色一致性方法全维度对比                                 │
├──────────────┬─────────┬──────────┬─────────┬──────────┬────────────────┤
│ 方法          │ 身份精度 │ 自然度   │ Prompt  │ VRAM     │ 速度          │
│              │ (%)     │ (%)     │ 遵从(%) │ (GB)     │ (sec, SDXL)   │
├──────────────┼─────────┼──────────┼─────────┼──────────┼────────────────┤
│ PuLID        │ 91      │ 92      │ 83      │ 10.2     │ 35            │
│ InstantID    │ 84      │ 86      │ 88      │ 8.5      │ 28            │
│ FaceID Plus  │ 79      │ 81      │ 91      │ 7.8      │ 25            │
│ PhotoMaker V2│ 82      │ 85      │ 87      │ 8.0      │ 30            │
│ ReActor      │ 98      │ 75*     │ N/A     │ 2.0      │ <1            │
│ LoRA (专训)  │ 95+     │ 95      │ 90      │ base     │ base          │
│ PuLID+ReActor│ 97      │ 90      │ 83      │ 10.2+2   │ 36            │
└──────────────┴─────────┴──────────┴─────────┴──────────┴────────────────┘
* ReActor 自然度低是因为 128px 限制，配合 FaceDetailer 可提升到 88+
```

### 8.2 方法选择决策树

```
需要角色一致性？
├── 单张图像 / 快速迭代？
│   ├── 身份精度最重要 → PuLID (Flux/SDXL)
│   ├── 需要精确姿态控制 → InstantID + ControlNet
│   ├── 需要最高 prompt 灵活度 → IP-Adapter FaceID Plus V2
│   └── 需要精确换脸 → ReActor + FaceDetailer
├── 视频/动画？
│   ├── SD1.5 视频 → IP-Adapter FaceID + AnimateDiff
│   ├── 现代视频模型 → Kling/Seedance + 一致关键帧(PuLID生成)
│   └── 逐帧替换 → ReActor 批处理
├── 长期角色项目？
│   └── 训练 LoRA + 零样本方法辅助
└── 多人场景？
    ├── 分区域控制 → IP-Adapter (per-face mask)
    └── 后处理替换 → ReActor (逐人替换)
```

### 8.3 2025-2026 趋势展望

1. **Flux 生态主导**: PuLID-FLUX 已是 Flux 上最佳零样本方案
2. **官方内置化**: comfyorg/comfyui-ipadapter 接棒 cubiq 维护
3. **视频一致性**: 视频模型内置 ID 条件（Kling Element Binding 是早期信号）
4. **LoRA 仍是王者**: 对于真正需要高一致性的商业项目，训练 LoRA 仍是最可靠方案
5. **组合管线成为标准**: PuLID 生成 + ReActor 精修 + FaceDetailer 增强 的三步管线

---

## 9. InsightFace 面部分析库详解

### 9.1 为什么所有方法都依赖 InsightFace

InsightFace 是所有角色一致性技术的基础设施:

```
InsightFace 在各方案中的角色:
├── IP-Adapter FaceID → ArcFace 512d embedding
├── InstantID → AntelopeV2 (embedding + keypoints)
├── PuLID → InsightFace 面部特征提取
├── ReActor → inswapper_128 换脸模型 + detection
└── PhotoMaker → 面部检测 + 对齐
```

### 9.2 AntelopeV2 模型组件

```
antelopev2/
├── 1k3d68.onnx          — 68 点 3D 关键点检测
├── 2d106det.onnx         — 106 点 2D 关键点检测
├── genderage.onnx        — 性别年龄估计
├── glintr100.onnx        — 人脸识别 (ArcFace embedding)
└── scrfd_10g_bnkps.onnx  — 人脸检测 (SCRFD)
```

### 9.3 ArcFace Embedding

- 输出: 512 维归一化向量
- 训练: 在大规模人脸数据集上使用 additive angular margin loss
- 特性: 同一人在不同角度/表情/光照下的 embedding 余弦相似度 > 0.5
- 阈值: cos_sim > 0.68 通常被认为是同一人

---

## 10. RunningHub 实验

### 实验 #34: 角色一致性技术全景概念图

**参数:**
- 端点: rhart-image-n-pro/text-to-image
- Prompt: 技术信息图展示角色一致性技术树
- 宽高比: 16:9

**目的:** 生成概念信息图，可视化各技术方案的关系

---

## 关键收获总结

1. **IP-Adapter 是基础**: 解耦交叉注意力是所有零样本方法的共同基础架构
2. **PuLID 最纯净**: 对比对齐训练使其成为身份注入时对原始模型影响最小的方案
3. **InstantID 最可控**: ControlNet 关键点提供空间控制是独特优势
4. **ReActor 最精确但有限**: 128px 限制使其必须配合 FaceDetailer
5. **组合使用是王道**: 生产环境中很少只用单一方法
6. **LoRA 仍不可替代**: 对于长期角色项目，训练专用 LoRA 仍是最佳方案
7. **InsightFace 是基石**: 所有方案都依赖同一个面部分析基础设施
