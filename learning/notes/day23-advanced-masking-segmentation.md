# Day 23: 高级蒙版与自动分割 (Advanced Masking & Segmentation)

> 学习日期: 2026-03-22 | 轮次: 31 | 阶段: Phase 6
> 关键技术: SAM/SAM2、GroundingDINO、Impact Pack、Florence-2、RMBG、mask 操作

---

## 1. 分割技术全景概览

### 1.1 图像分割的三个层次

```
┌─────────────────────────────────────────────────────────┐
│                    图像分割技术栈                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Level 1: 检测 (Detection)                              │
│  ├─ YOLO 系列 (YOLOv8/v11) — 封闭类别 bbox              │
│  ├─ GroundingDINO — 开放词汇 bbox (文本驱动)             │
│  └─ Florence-2 — 多任务视觉基础模型                      │
│                                                         │
│  Level 2: 分割 (Segmentation)                           │
│  ├─ SAM / SAM2 — 提示式万物分割 (point/box/mask)         │
│  ├─ CLIPSeg — 文本驱动语义分割                           │
│  └─ BiRefNet / RMBG — 专用前景/背景分割                  │
│                                                         │
│  Level 3: 组合管线 (Combined Pipeline)                   │
│  ├─ Grounded-SAM = GroundingDINO + SAM                  │
│  ├─ Impact Pack FaceDetailer = YOLO + SAM + Detailer    │
│  └─ ComfyUI-Grounding = 19+ 检测模型 + SAM2             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 技术演进时间线

| 时间 | 里程碑 | 意义 |
|------|--------|------|
| 2023.04 | SAM (Meta) | 万物分割基础模型，SA-1B 数据集 |
| 2023.03 | GroundingDINO (IDEA) | 开放词汇检测，ECCV 2024 |
| 2023.06 | Grounded-SAM | 文本→bbox→mask 完整管线 |
| 2023.08 | Impact Pack | ComfyUI 生态核心：FaceDetailer + SEGS |
| 2024.01 | Florence-2 (Microsoft) | 统一视觉基础模型 (caption/detect/segment) |
| 2024.07 | SAM 2 (Meta) | 图像+视频统一分割，流式记忆架构 |
| 2024.12 | RMBG 2.0 (BRIA AI) | 专用背景移除 SOTA |
| 2025.03 | ComfyUI-Grounding | 统一 19+ 检测模型 + SAM2 |
| 2025.06 | SAM3 | 下一代分割模型 |

---

## 2. SAM (Segment Anything Model) 深度解析

### 2.1 SAM 原始架构 (2023)

```
┌────────────────────────────────────────────────────────┐
│                    SAM 架构                             │
│                                                        │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Image Encoder │    │ Prompt Encoder│                 │
│  │  (ViT-H/L/B) │    │ (Point/Box/  │                 │
│  │  MAE 预训练   │    │  Mask/Text)  │                 │
│  └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                          │
│         ▼                   ▼                          │
│  ┌──────────────────────────────────┐                  │
│  │      Mask Decoder                │                  │
│  │  (Lightweight Transformer)       │                  │
│  │  2-layer decoder + MLP head      │                  │
│  │  → 3 个分辨率的 mask 输出        │                  │
│  │  + IoU 置信度预测                │                  │
│  └──────────────────────────────────┘                  │
│         │                                              │
│         ▼                                              │
│  Mask 1 (whole)  |  Mask 2 (part)  |  Mask 3 (subpart)│
│  + IoU Score     |  + IoU Score    |  + IoU Score      │
└────────────────────────────────────────────────────────┘
```

**三个核心组件：**

1. **Image Encoder (ViT-H)**
   - 基于 MAE (Masked Autoencoder) 预训练的 ViT-H/16
   - 输入: 1024×1024 图像 → 输出: 64×64×256 特征图
   - 仅需运行一次，后续不同 prompt 复用
   - 参数量: ViT-H = 632M, ViT-L = 308M, ViT-B = 91M

2. **Prompt Encoder**
   - **Point prompts**: 前景点 (positive) + 背景点 (negative) → 位置编码 + 类型编码
   - **Box prompts**: 左上角 + 右下角 → 两个 point embedding
   - **Mask prompts**: 低分辨率 (256×256) mask → 卷积下采样 → 与图像嵌入相加
   - **Text prompts**: CLIP 文本编码器 (SAM 原版训练时未使用文本)

3. **Mask Decoder**
   - 仅 2 层 Transformer decoder（极轻量）
   - 输入: image embedding + prompt embedding + output token
   - 使用可变形自注意力（效率优化）
   - 输出 3 层级 mask（whole object / part / subpart）+ IoU 预测
   - 设计哲学: **歧义感知** — 一个点可能对应多个有效分割

### 2.2 SAM 模型变体

| 变体 | 编码器 | 参数量 | 模型大小 | 速度 | 质量 |
|------|--------|--------|----------|------|------|
| sam_vit_h | ViT-H | 632M | 2.56GB | 基准 | 最高 |
| sam_vit_l | ViT-L | 308M | 1.25GB | 1.5x | 高 |
| sam_vit_b | ViT-B | 91M | 375MB | 3x | 良好 |
| sam_hq_vit_h | ViT-H (HQ) | ~635M | 2.57GB | 基准 | HQ边缘 |
| sam_hq_vit_l | ViT-L (HQ) | ~310M | 1.25GB | 1.5x | HQ边缘 |
| sam_hq_vit_b | ViT-B (HQ) | ~93M | 379MB | 3x | HQ边缘 |
| mobile_sam | TinyViT | ~10M | 39MB | 10x+ | 中等 |

**SAM-HQ** (NeurIPS 2023): 添加 High-Quality Output Token + Learnable mask feature，边缘精度显著提升

### 2.3 SAM 2 架构革新 (2024.07)

**论文**: arXiv:2408.00714 — "Segment Anything in Images and Videos"

```
┌──────────────────────────────────────────────────────────┐
│                     SAM 2 架构                            │
│                                                          │
│  ┌─────────────┐                                         │
│  │ Hiera Image  │  ← 层次化骨干网络（取代 ViT plain）     │
│  │  Encoder     │  ← 多尺度特征金字塔                     │
│  └──────┬──────┘                                         │
│         │                                                │
│  ┌──────▼──────┐     ┌───────────────┐                   │
│  │ Memory       │ ←→ │ Memory Bank   │  ← 流式记忆       │
│  │ Attention    │     │ (FIFO Queue)  │  ← 最近 N 帧特征  │
│  └──────┬──────┘     └───────────────┘                   │
│         │                                                │
│  ┌──────▼──────┐     ┌───────────────┐                   │
│  │ Mask Decoder │ ←── │ Prompt Encoder│                   │
│  │ (改进版)     │     │ + 遮挡感知    │                   │
│  └──────┬──────┘     └───────────────┘                   │
│         │                                                │
│         ▼                                                │
│  Mask + IoU + Occlusion Score                            │
└──────────────────────────────────────────────────────────┘
```

**SAM 2 vs SAM 关键改进：**

| 维度 | SAM (2023) | SAM 2 (2024) |
|------|-----------|--------------|
| **骨干网络** | ViT (plain) | Hiera (层次化) |
| **多尺度** | 单尺度 64×64 | 多尺度金字塔 |
| **视频支持** | ❌ 仅图像 | ✅ 图像+视频统一 |
| **记忆机制** | 无 | 流式 Memory Bank (FIFO) |
| **遮挡处理** | 无 | Occlusion Score 预测 |
| **速度** | 基准 | 6x faster (图像) |
| **精度** | SA-1B 基准 | 更高（图像）+ SOTA（视频） |
| **数据集** | SA-1B (11M) | SA-V (51K 视频, 600K masklets) |
| **交互** | 单帧提示 | 跨帧传播 + 3x 更少交互 |

**Hiera 骨干网络特点：**
- 层次化设计（类似 Swin，但去除了窗口注意力的复杂性）
- 多尺度特征金字塔（1/4, 1/8, 1/16, 1/32）
- MAE 预训练 → 移除冗余 token → 极快推理
- 比 ViT-H 快 6x，同时保持或超过精度

**Memory Attention 机制：**
```python
# 伪代码 — SAM2 Memory Attention
class MemoryAttention:
    def __init__(self):
        self.memory_bank = FIFOQueue(max_size=6)  # 保存最近 6 帧
        
    def forward(self, current_frame_features, prompts):
        # 1. 编码当前帧
        image_embed = self.image_encoder(current_frame)
        
        # 2. Memory Cross-Attention: 当前帧 attend 到历史帧
        for memory in self.memory_bank:
            image_embed = cross_attention(
                query=image_embed,
                key=memory.spatial_features,
                value=memory.spatial_features
            )
        
        # 3. Prompt-conditioned 解码
        masks, iou, occlusion = self.mask_decoder(image_embed, prompts)
        
        # 4. 将当前帧压缩后存入 Memory Bank
        memory_entry = self.memory_encoder(image_embed, masks)
        self.memory_bank.push(memory_entry)
        
        return masks, iou, occlusion
```

**SAM2 模型变体：**

| 模型 | 参数量 | 大小 | 推荐场景 |
|------|--------|------|---------|
| sam2.1_hiera_tiny | ~39M | ~160MB | 实时/低端设备 |
| sam2.1_hiera_small | ~46M | ~185MB | 平衡选择 |
| sam2.1_hiera_base_plus | ~80M | ~320MB | 高质量 |
| sam2.1_hiera_large | ~224M | ~900MB | 最高质量 |

### 2.4 ComfyUI 中的 SAM/SAM2 节点

**主要节点包：**

1. **kijai/ComfyUI-segment-anything-2** (主流)
   - `DownloadAndLoadSAM2Model` — 加载 SAM2 模型（自动下载 safetensors）
   - `Sam2Segmentation` — 基于点/框提示的分割
   - `Sam2AutoSegmentation` — 自动分割（无提示，类似 ADE20K 全图分割）
   - `Sam2VideoSegmentation` — 视频追踪分割
   - 模型存储: `ComfyUI/models/sam2/`
   - 支持 segmentor 类型: `single_image` / `video` / `automask`

2. **Impact Pack SAMLoader + SAMDetector**
   - `SAMLoader (Impact)` — 加载 SAM/SAM2 模型（V8.18 起支持 SAM2）
   - `SAMDetector (combined)` — 基于 SEGS 提示的 SAM 分割 → 统一 mask
   - `SAMDetector (Segmented)` — SAM 分割 → 多个独立 mask (batch)
   - `SAM2 Video Detector (SEGS)` — SAM2 视频追踪 → SEGS batch

3. **storyicon/comfyui_segment_anything** (Grounded-SAM)
   - `GroundingDinoModelLoader (segment anything)` — 加载 GroundingDINO
   - `GroundingDinoSAMSegment (segment anything)` — 文本→bbox→mask 一步到位
   - `InvertMask` / `IsMaskEmpty` — mask 工具节点

---

## 3. GroundingDINO 深度解析

### 3.1 架构设计 (ECCV 2024)

**论文**: arXiv:2303.05499 — "Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection"

**核心创新**: 在检测器 DINO 的三个阶段都融入语言信息

```
┌──────────────────────────────────────────────────────────────┐
│                GroundingDINO 架构                              │
│                                                              │
│  Image ─→ [Swin-T/B Backbone] ─→ Multi-scale Features       │
│                                        │                     │
│  Text ──→ [BERT Tokenizer] ─→ Text Features                 │
│                                        │                     │
│  ┌─────────────────────────────────────▼────────────────┐    │
│  │          Phase A: Feature Enhancer (Neck)            │    │
│  │  ┌──────────────────────────────────────────────┐    │    │
│  │  │ × 6 layers:                                  │    │    │
│  │  │  1. Image Self-Attention (deformable)        │    │    │
│  │  │  2. Text Self-Attention                      │    │    │
│  │  │  3. Image-to-Text Cross-Attention            │    │    │
│  │  │  4. Text-to-Image Cross-Attention            │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────┬────────────────┘    │
│                                        │                     │
│  ┌─────────────────────────────────────▼────────────────┐    │
│  │       Phase B: Language-Guided Query Selection       │    │
│  │  Top-k image features × text similarity → queries    │    │
│  └─────────────────────────────────────┬────────────────┘    │
│                                        │                     │
│  ┌─────────────────────────────────────▼────────────────┐    │
│  │          Phase C: Cross-Modality Decoder (Head)      │    │
│  │  ┌──────────────────────────────────────────────┐    │    │
│  │  │ × 6 layers:                                  │    │    │
│  │  │  1. Self-Attention on queries                │    │    │
│  │  │  2. Image Cross-Attention (deformable)       │    │    │
│  │  │  3. Text Cross-Attention                     │    │    │
│  │  │  4. FFN                                      │    │    │
│  │  └──────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────┬────────────────┘    │
│                                        │                     │
│  ┌─────────────────────────────────────▼────────────────┐    │
│  │            Detection Head                            │    │
│  │  bbox regression + contrastive text-region matching  │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 关键技术细节

**1. 三阶段紧密融合 (Tight Fusion)**

| 阶段 | 位置 | 融合方式 | 作用 |
|------|------|---------|------|
| A | Neck (Feature Enhancer) | 双向 Cross-Attention (I→T + T→I) | 早期多模态对齐 |
| B | Query Init | 语言引导 query 选择 | 将高文本相关性区域作为初始 query |
| C | Head (Decoder) | 文本 Cross-Attention | 持续文本条件精炼 |

与竞品对比：
- GLIP: 只在 A 阶段融合
- OV-DETR: 只在 B 阶段融合
- MDETR: 在 A + C 阶段融合
- **GroundingDINO: A + B + C 三阶段全融合 → 最强**

**2. Sub-Sentence 文本表示** (vs 直接拼接类别名)

传统做法 (GLIP): `"cat . dog . person ."` → BERT 编码 → 类别间互相 attend
GroundingDINO: 用 `.` 作为分隔符 + **移除不相关类别间的注意力** → 避免语义污染

```python
# Sub-sentence level representation
text = "cat . dog . person"
# BERT tokenization 后，cat/dog/person 各自的 token 不互相 attend
# 只有 `.` 分隔符的 attention 被保留
# 效果：每个类别的 text feature 更纯净
```

**3. Language-Guided Query Selection (Phase B)**

```python
# 从图像特征中选择与文本最相关的 top-k 特征作为 decoder query
def language_guided_query_selection(image_features, text_features, k=900):
    # image_features: [N, C] — 多尺度特征点
    # text_features: [L, C] — 文本 token 特征
    
    # 计算每个图像特征与所有文本 token 的最大相似度
    similarity = image_features @ text_features.T  # [N, L]
    max_sim = similarity.max(dim=-1).values  # [N]
    
    # 选择 top-k 最相关的图像特征作为初始 query
    topk_indices = max_sim.topk(k).indices
    queries = image_features[topk_indices]
    
    return queries  # → 送入 Phase C decoder
```

### 3.3 GroundingDINO 模型

| 模型 | 骨干网络 | 大小 | COCO AP (zero-shot) |
|------|---------|------|---------------------|
| GroundingDINO-T | Swin-T | 694MB | 48.4 |
| GroundingDINO-B | Swin-B | 938MB | 56.7 |
| GroundingDINO 1.5 Pro | — | — | 更高 (2024) |
| GroundingDINO 1.5 Edge | — | — | 移动端 |

### 3.4 GroundingDINO vs YOLO 对比

| 维度 | GroundingDINO | YOLOv8/v11 |
|------|--------------|------------|
| 类别范围 | **开放词汇** (任意文本描述) | 封闭类别 (COCO 80类等) |
| 输入 | 图像 + 文本 prompt | 仅图像 |
| 速度 | ~300ms/帧 (GPU) | ~5ms/帧 (GPU) |
| 精度 | 高（复杂场景优势） | 高（已知类别） |
| 训练数据 | 多源 (检测+grounding+caption) | 检测数据集 |
| 适用场景 | 灵活/少见物体/描述式检测 | 实时/高吞吐/已知类别 |
| ComfyUI 集成 | comfyui_segment_anything | Impact Subpack |

---

## 4. Grounded-SAM 组合管线

### 4.1 核心流程

```
Text Prompt                     Image
    │                             │
    ▼                             ▼
┌─────────────┐           ┌──────────────┐
│ GroundingDINO│           │ SAM Image    │
│ (检测 bbox)  │           │ Encoder      │
└──────┬──────┘           └──────┬───────┘
       │                         │
       │  bounding boxes         │  image embedding
       │                         │
       └────────┐  ┌─────────────┘
                ▼  ▼
         ┌──────────────┐
         │ SAM Mask     │
         │ Decoder      │
         │ (bbox→mask)  │
         └──────┬───────┘
                │
                ▼
        Precise Segmentation Masks
```

### 4.2 ComfyUI 实现

**方式一: comfyui_segment_anything (一体化)**

```
GroundingDinoModelLoader → model
SAMModelLoader → sam_model
                            → GroundingDinoSAMSegment → (image, mask)
LoadImage → image ──────────┘   ↑
                                text_prompt: "cat . dog"
```

节点参数:
- `threshold`: GroundingDINO 检测置信度阈值 (默认 0.3)
- `text_prompt`: 检测目标描述（用 `.` 分隔多个目标）

**方式二: ComfyUI-Grounding (2025 新方案，19+ 模型)**

```
GroundingDetect → (image, bboxes, labels, scores)
                    ↓
GroundingSAM2Segment → masks
```

支持的检测模型:
- GroundingDINO / MM-GroundingDINO
- Florence-2 (多任务)
- OWLv2
- YOLO-World
- SA2VA (MLLM + SAM2, 最强语义理解)

---

## 5. Impact Pack — ComfyUI 分割生态核心

### 5.1 SEGS 数据结构

**SEGS (SEGmentS)** 是 Impact Pack 的核心数据类型，不同于普通 MASK:

```python
# SEGS 内部结构
SEGS = (
    source_shape,       # (H, W) 原图尺寸
    [
        SEG(             # 每个检测到的区域
            cropped_image,    # 裁剪后的图像（可选）
            cropped_mask,     # 裁剪区域的 mask
            confidence,       # 检测置信度
            crop_region,      # (x1, y1, x2, y2) 裁剪坐标
            bbox,             # (x1, y1, x2, y2) 检测框
            label,            # 标签字符串
            control_net_wrapper  # 绑定的 ControlNet（可选）
        ),
        SEG(...),
        ...
    ]
)
```

**SEGS vs MASK 对比:**

| 维度 | SEGS | MASK |
|------|------|------|
| 信息量 | bbox + mask + label + confidence + image | 仅像素值 |
| 多目标 | 原生支持多个独立区域 | 需要 batch 或合并 |
| 裁剪 | 自带裁剪信息 | 需要额外节点裁剪 |
| ControlNet | 可绑定 ControlNet | 不支持 |
| 用途 | Detailer 管线核心 | 通用 mask 操作 |

### 5.2 FaceDetailer 管线深度解析

FaceDetailer 是 Impact Pack 最常用的节点之一，集成了完整的 检测→裁剪→增强→贴回 管线:

```
┌──────────────────────────────────────────────────────────┐
│                 FaceDetailer 内部流程                      │
│                                                          │
│  Step 1: Detection (BBOX)                                │
│  ├─ bbox_detector (YOLOv8 face_yolov8m.pt)              │
│  ├─ 输出: bounding boxes + confidence                    │
│  └─ 参数: bbox_threshold, bbox_dilation                  │
│                                                          │
│  Step 2: Segmentation (SAM)                              │
│  ├─ sam_model (sam_vit_b/l/h 或 sam2)                   │
│  ├─ bbox center → SAM point prompt                       │
│  ├─ 输出: 精确面部轮廓 mask                              │
│  └─ 参数: sam_detection_hint, sam_dilation,              │
│           sam_bbox_expansion, sam_mask_hint_threshold     │
│                                                          │
│  Step 3: Crop & Enhance (Detailer)                       │
│  ├─ 按 guide_size 裁剪并放大面部区域                      │
│  ├─ 使用主模型 (checkpoint) 重新生成面部                   │
│  ├─ 可选: wildcard_spec 作为面部专用 prompt               │
│  ├─ 可选: ControlNet (通过 SEGS 绑定)                    │
│  └─ 参数: guide_size, max_size, denoise, seed            │
│                                                          │
│  Step 4: Paste Back                                      │
│  ├─ 将增强后的面部贴回原图                                │
│  ├─ mask 边缘 feathering                                 │
│  └─ 参数: feather, inpaint_model                         │
│                                                          │
│  输出:                                                   │
│  ├─ image: 增强后的完整图像                               │
│  ├─ cropped_refined: 裁剪增强后的面部列表                  │
│  ├─ cropped_enhanced_alpha: 带 alpha 的面部列表           │
│  ├─ mask: 所有面部区域的合并 mask                         │
│  └─ detailer_pipe: 管线参数（用于多 pass）                │
└──────────────────────────────────────────────────────────┘
```

### 5.3 FaceDetailer 关键参数详解

```
┌────────────────────────────────────────────────────────────┐
│ FaceDetailer 参数矩阵                                       │
├────────────────────┬───────────┬───────────────────────────┤
│ 参数               │ 推荐值     │ 说明                       │
├────────────────────┼───────────┼───────────────────────────┤
│ guide_size         │ 384-512   │ 裁剪后放大到的目标尺寸      │
│ guide_size_for     │ True      │ True=bbox, False=crop区域  │
│ max_size           │ 1024      │ 最大裁剪尺寸               │
│ seed               │ random    │ 面部重绘 seed              │
│ steps              │ 20-30     │ 采样步数                   │
│ cfg                │ 7.0-8.0   │ CFG scale                  │
│ sampler_name       │ euler     │ 采样器                     │
│ scheduler          │ normal    │ 调度器                     │
│ denoise            │ 0.3-0.5   │ ⚠️ 关键！太高会改变面部     │
│ feather            │ 5-20      │ mask 边缘羽化              │
│ noise_mask         │ True      │ ✅ 推荐开启（只在mask区域加噪）│
│ force_inpaint      │ True      │ 强制使用 inpaint 模式      │
│ bbox_threshold     │ 0.5       │ 检测置信度阈值             │
│ bbox_dilation      │ 10        │ bbox 膨胀像素              │
│ sam_detection_hint │ center-1  │ SAM 提示策略               │
│ sam_dilation       │ 0         │ SAM mask 膨胀              │
│ sam_bbox_expansion │ 0         │ SAM 输入 bbox 扩展         │
│ drop_size          │ 10        │ 丢弃小于此尺寸的检测       │
│ wildcard           │ ""        │ 面部专用 prompt            │
│ cycle              │ 1         │ 迭代增强次数               │
└────────────────────┴───────────┴───────────────────────────┘
```

**denoise 调优要点（FaceDetailer 核心）：**
- `0.2-0.3`: 轻微修复，保持原始面部 ← 推荐起点
- `0.3-0.5`: 中等增强，添加细节但保持一致性
- `0.5-0.7`: 大幅重绘，可能改变面部特征 ← 谨慎使用
- `> 0.7`: 几乎完全重新生成 ← 仅用于创意目的

**noise_mask 开启 vs 关闭:**
- ✅ `True`: 只在 mask 区域加噪/去噪 → 面部与背景过渡自然
- ❌ `False`: 整个裁剪区域都加噪 → 可能导致面部周围出现不一致

### 5.4 Impact Pack 检测器体系

```
┌──────────────────────────────────────────────────────────┐
│               Impact Pack 检测器类型                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  BBOX_DETECTOR (输出: bounding boxes)                    │
│  ├─ UltralyticsDetectorProvider (需 Impact Subpack)      │
│  │   └─ YOLOv8 系列: face_yolov8m.pt / hand / person    │
│  ├─ ONNXDetectorProvider                                 │
│  │   └─ ONNX 格式模型                                   │
│  └─ CLIPSegDetectorProvider                              │
│      └─ 文本驱动检测 (需 ComfyUI-CLIPSeg)               │
│                                                          │
│  SEGM_DETECTOR (输出: 分割 masks)                        │
│  ├─ UltralyticsDetectorProvider (segm 模型)              │
│  │   └─ YOLOv8-seg 系列                                 │
│  └─ SAMDetector                                          │
│      └─ SAM/SAM2 配合 bbox 检测器                       │
│                                                          │
│  常用模型文件:                                            │
│  ├─ face_yolov8m.pt — 人脸检测 (推荐)                    │
│  ├─ face_yolov8n.pt — 人脸检测 (快速)                    │
│  ├─ hand_yolov8s.pt — 手部检测                           │
│  ├─ person_yolov8m-seg.pt — 人体分割                     │
│  └─ sam_vit_b_01ec64.pth — SAM ViT-B (轻量)             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 5.5 SEGS 操作节点全集

Impact Pack 提供了丰富的 SEGS 操作节点:

**检测 → SEGS:**
- `BBOX Detector (SEGS)` — bbox 检测 → SEGS
- `SEGM Detector (SEGS)` — 分割检测 → SEGS
- `Simple Detector (SEGS)` — 一体化检测 (BBOX + SAM 增强)
- `MASK to SEGS` — mask 转 SEGS
- `MediaPipe FaceMesh to SEGS` — 面部 landmark → SEGS

**SEGS 过滤:**
- `SEGS Filter (label)` — 按标签过滤
- `SEGS Filter (ordered)` — 按大小/位置排序取范围
- `SEGS Filter (range)` — 按尺寸范围过滤
- `SEGS Filter (non max suppression)` — IoU NMS
- `SEGS Filter (intersection)` — 按重叠度过滤

**SEGS 像素操作:**
- `Pixelwise(SEGS & SEGS)` — 两个 SEGS 交集
- `Pixelwise(SEGS - SEGS)` — SEGS 差集
- `Pixelwise(SEGS & MASK)` — SEGS 与 MASK 交集
- `SEGSConcat` — 合并两个 SEGS
- `SEGS Merge` — 将多个 SEG 合并为一个

**SEGS 增强:**
- `ControlNetApply (SEGS)` — 为 SEGS 绑定 ControlNet
- `IPAdapterApply (SEGS)` — 为 SEGS 绑定 IP-Adapter
- `SEGSDetailer` — 对 SEGS 执行 detailing (不贴回)
- `SEGSPaste` — 将 SEGS 结果贴回原图

**SEGS 转换:**
- `SEGSToImageList` — SEGS → 图像列表
- `SEGSToMaskList` — SEGS → mask 列表
- `SEGSPreview` — 预览 SEGS

---

## 6. Florence-2 — 统一视觉基础模型

### 6.1 架构与能力

**论文**: Microsoft, 2024 — 统一的 sequence-to-sequence 视觉模型

```
Florence-2 = DaViT 视觉编码器 + 多任务文本解码器

支持任务 (通过 text prompt 切换):
┌─────────────────────────────────────────────┐
│ Caption 系列:                               │
│  ├─ <CAPTION>        → 简短描述             │
│  ├─ <DETAILED_CAPTION> → 详细描述           │
│  └─ <MORE_DETAILED_CAPTION> → 超详细描述    │
│                                             │
│ Detection 系列:                             │
│  ├─ <OD>            → 物体检测 (bbox)        │
│  ├─ <DENSE_REGION_CAPTION> → 区域描述       │
│  └─ <CAPTION_TO_PHRASE_GROUNDING> → 短语定位│
│                                             │
│ Segmentation 系列:                          │
│  ├─ <REFERRING_EXPRESSION_SEGMENTATION>     │
│  │   → 文本描述 → 分割 mask                 │
│  └─ <REGION_TO_SEGMENTATION>               │
│      → 区域坐标 → 分割 mask                 │
│                                             │
│ OCR 系列:                                   │
│  ├─ <OCR>           → 文字识别              │
│  └─ <OCR_WITH_REGION> → 文字+位置           │
└─────────────────────────────────────────────┘
```

### 6.2 Florence-2 vs GroundingDINO

| 维度 | Florence-2 | GroundingDINO |
|------|-----------|---------------|
| 架构 | Seq2Seq (编码-解码) | DETR 变体 (检测器) |
| 模型大小 | base: 232M / large: 770M | SwinT: 694MB / SwinB: 938MB |
| 任务范围 | Caption + Detection + Segmentation + OCR | 仅 Detection |
| 检测质量 | 好 (多任务泛化) | **更好** (专注检测) |
| 分割能力 | ✅ 原生支持 | ❌ 需要 SAM |
| 描述能力 | ✅ Caption + QA | ❌ |
| 速度 | 较快 | 中等 |
| ComfyUI 集成 | kijai/ComfyUI-Florence2 | comfyui_segment_anything |

**选择策略:**
- 需要精确检测 → GroundingDINO
- 需要 caption/OCR/多任务 → Florence-2
- 需要最强语义理解 → SA2VA (MLLM + SAM2)
- 需要速度 → YOLO 系列

---

## 7. 背景移除专用技术

### 7.1 RMBG 2.0 (BRIA AI)

专用背景移除模型，比通用分割更精准:

```
RMBG-2.0 特点:
├─ 基于 BiRefNet 架构改进
├─ 专门训练于前景/背景分离
├─ 处理细节极好 (头发丝、半透明物体)
├─ 非商用开源 (BRIA License)
└─ ComfyUI-RMBG 集成 (1038lab)
```

### 7.2 BiRefNet (Bilateral Reference Network)

```
BiRefNet 架构:
├─ 双参考分支 (Bilateral Reference)
│   ├─ 高分辨率分支 → 细节保留
│   └─ 低分辨率分支 → 语义理解
├─ 多变体:
│   ├─ BiRefNet-general — 通用二值分割
│   ├─ BiRefNet-portrait — 人像抠图
│   ├─ BiRefNet-matting — 精细抠图 (带 alpha)
│   ├─ BiRefNet-lite — 轻量版
│   └─ BiRefNet-dynamic — 动态分辨率
└─ 质量: 当前学术 SOTA 之一
```

### 7.3 ComfyUI-RMBG 节点 (1038lab)

支持多种模型的统一背景移除:

```
支持的模型:
├─ RMBG-2.0 (BRIA) — 最佳通用背景移除
├─ INSPYRENET — 高质量显著性检测
├─ BEN / BEN2 — 背景擦除网络
├─ BiRefNet 系列 — 多种变体
├─ SDMatte — SD 风格抠图
├─ SAM / SAM2 / SAM3 — 通用分割
└─ GroundingDINO — 文本驱动目标分割

节点:
├─ RMBG — 基础背景移除
├─ BiRefNetRMBG — BiRefNet 模型
├─ GroundingDinoRMBG — 文本驱动分割
├─ SAM2RMBG — SAM2 分割
├─ MaskOverlay — mask 叠加预览
├─ ObjectRemover — 物体移除
└─ ImageMaskResize — 图像+mask 调整大小
```

---

## 8. ComfyUI 内置 Mask 操作深度

### 8.1 MASK 数据格式

```python
# ComfyUI 中 MASK 的 tensor 格式
# MASK: torch.Tensor, shape = [B, H, W], dtype = float32, range [0.0, 1.0]
# B = batch size (支持多 mask)
# H, W = 与图像相同分辨率
# 0.0 = 未遮罩 (背景), 1.0 = 遮罩 (前景)

# IMAGE: [B, H, W, C] — 注意通道在最后
# MASK:  [B, H, W]    — 无通道维度

# 转换:
# IMAGE → MASK: image[:, :, :, 0]  (取 R 通道或灰度化)
# MASK → IMAGE: mask.unsqueeze(-1).expand(-1, -1, -1, 3)
```

### 8.2 内置 Mask 节点全集

**创建类:**
- `SolidMask` — 创建纯色 mask (全 0 或全 1)
- `ImageToMask` — 从图像通道提取 mask (R/G/B/A)
- `ImageColorToMask` — 按颜色提取 mask (RGB 匹配)
- `MaskFromList` — 从 mask 列表创建

**操作类:**
- `InvertMask` — 反转 mask: `1.0 - mask`
- `CropMask` — 按坐标裁剪 mask
- `MaskComposite` — 两个 mask 合成

**MaskComposite 操作详解:**

```python
# MaskComposite 支持的操作 (operation 参数):
operations = {
    "multiply":  dst * src,           # 交集 (AND)
    "add":       dst + src,           # 并集 (OR), clamp to [0,1]
    "subtract":  dst - src,           # 差集, clamp to [0,1]
    "and":       torch.min(dst, src), # 逐像素取最小 (严格 AND)
    "or":        torch.max(dst, src), # 逐像素取最大 (严格 OR)
    "xor":       (dst + src) - 2 * dst * src,  # 异或
}
# 注意: add/subtract 有 clamp, 适合软 mask
# and/or/xor 适合二值 mask
```

**变换类:**
- `FeatherMask` — mask 边缘羽化 (高斯模糊)
- `GrowMask` — 膨胀/收缩 mask (morphological dilation/erosion)
- `ThresholdMask` — 二值化 mask

### 8.3 Impact Pack 额外 Mask 操作

```
Pixelwise 系列 (像素级操作):
├─ Pixelwise(MASK & MASK) — mask 交集 (AND)
├─ Pixelwise(MASK - MASK) — mask 差集 (SUBTRACT)
├─ Pixelwise(MASK + MASK) — mask 并集 (ADD)
├─ Dilate Mask — 膨胀/腐蚀 (支持负值=腐蚀)
├─ Gaussian Blur Mask — 高斯模糊 (羽化)
├─ ToBinaryMask — 二值化 (非零→255)
└─ Mask Rect Area — 创建矩形 mask (百分比定义)
```

### 8.4 Masquerade Nodes (BadCafeCode)

第三方强大 mask 工具包:

```
Masquerade Nodes 核心功能:
├─ Mask by Text — CLIP 文本→mask (最方便!)
│   └─ 支持正/负 prompt + 阈值
├─ Combine Masks — Union/Intersect/Difference 操作
├─ Create Rect Mask — 矩形 mask 创建
├─ Create QR Code — 二维码 mask
├─ Prune by Mask — 按 mask 过滤 batch
├─ Change Channel Count — 通道转换
├─ Constant Mask — 常量 mask
├─ Blur — mask 模糊
├─ Mix Color by Mask — 按 mask 混合颜色
└─ Image to Mask — 图像→mask 转换
```

---

## 9. 生产级组合工作流模式

### 9.1 模式一: 文本驱动精确分割 (Grounded-SAM)

**场景**: "帮我把图中的猫分割出来"

```
LoadImage ──→ GroundingDinoSAMSegment ──→ mask
                    ↑
            text_prompt: "cat"
            threshold: 0.3
```

### 9.2 模式二: 人脸增强管线 (FaceDetailer)

**场景**: 群像照片中所有人脸细节增强

```
Text2Img ──→ FaceDetailer ──→ enhanced_image
                ↑         ↑
      bbox: face_yolov8m  sam: sam_vit_b
      guide_size: 512     denoise: 0.35
      noise_mask: True    wildcard: "detailed face"
```

### 9.3 模式三: 分层 Inpainting

**场景**: 分割主体→单独重绘背景→合成

```
LoadImage ─┬→ RMBG ──→ foreground_mask
           │                ↓
           │         InvertMask ──→ background_mask
           │                          ↓
           └→ SetLatentNoiseMask ──→ KSampler ──→ 新背景
                                          ↓
                               ImageComposite ──→ 合成结果
                                    ↑
                              原始前景 + 新背景
```

### 9.4 模式四: 多区域独立控制

**场景**: 画面中不同物体使用不同 prompt/LoRA

```
LoadImage ─→ GroundingDINO ─→ SEGS
                                 │
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            SEGS Filter    SEGS Filter   SEGS Filter
            (label="person") ("car")      ("sky")
                    ↓            ↓            ↓
             SEGSDetailer  SEGSDetailer  SEGSDetailer
             (人物LoRA)    (车辆prompt)  (天空prompt)
                    ↓            ↓            ↓
                    └────────────┼────────────┘
                                 ↓
                            SEGSPaste ──→ 最终结果
```

### 9.5 模式五: 视频帧一致性分割 (SAM2)

**场景**: 视频中追踪某个物体

```
VideoFrames ─→ SAM2 Video Detector (SEGS) ──→ per-frame SEGS
                     ↑
              初始帧 point/box prompt
              (SAM2 自动追踪到后续帧)
```

---

## 10. 方法选择决策树

```
需要分割/蒙版？
├─ 简单背景移除？
│   └─ → RMBG 2.0 / BiRefNet（最简单，效果最好）
│
├─ 知道要分割什么（能用文字描述）？
│   ├─ 简单类别名 ("cat", "person")？
│   │   └─ → GroundingDINO + SAM（Grounded-SAM）
│   ├─ 复杂描述 ("the red car on the left")？
│   │   └─ → SA2VA / Florence-2 → SAM2
│   └─ 多种东西需要分别处理？
│       └─ → GroundingDINO → SEGS → 按 label 过滤
│
├─ 人脸相关？
│   ├─ 增强/修复人脸？
│   │   └─ → FaceDetailer（Impact Pack）
│   ├─ 人脸分割/提取？
│   │   └─ → face_yolov8m → SAM
│   └─ 面部关键点？
│       └─ → MediaPipe FaceMesh to SEGS
│
├─ 视频分割/追踪？
│   └─ → SAM2 Video Detector
│
├─ 手动指定区域？
│   ├─ 矩形？ → ConditioningSetArea / Mask Rect Area
│   ├─ 自由画？ → MaskPainter
│   └─ 图像中某个点？ → SAM (point prompt)
│
└─ 需要自动分割所有物体？
    └─ → SAM2 Auto Segmentation
```

---

## 11. RunningHub 实验

### 实验 #37: 分割技术全景概念图

- **端点**: rhart-image-n-pro/text-to-image
- **Prompt**: 技术信息图 — SAM + GroundingDINO + Impact Pack 管线
- **参数**: aspectRatio=16:9
- **目的**: 可视化分割技术栈

### 实验 #38: 图生图 — 背景替换实验

- **端点**: rhart-image-n-pro/edit
- **目的**: 使用 RunningHub API 模拟分割+重绘管线

（实验结果将在执行后更新）

---

## 12. 关键代码片段

### 12.1 Grounded-SAM API 调用 (Python)

```python
"""
ComfyUI Grounded-SAM 工作流 API 调用示例
使用 comfyui_segment_anything 节点
"""

workflow = {
    "1": {
        "class_type": "LoadImage",
        "inputs": {"image": "input.png"}
    },
    "2": {
        "class_type": "GroundingDinoModelLoader (segment anything)",
        "inputs": {"model_name": "GroundingDINO_SwinT_OGC"}
    },
    "3": {
        "class_type": "SAMModelLoader (segment anything)",
        "inputs": {"model_name": "sam_vit_b_01ec64.pth"}
    },
    "4": {
        "class_type": "GroundingDinoSAMSegment (segment anything)",
        "inputs": {
            "grounding_dino_model": ["2", 0],
            "sam_model": ["3", 0],
            "image": ["1", 0],
            "prompt": "cat . dog",
            "threshold": 0.3
        }
    },
    "5": {
        "class_type": "PreviewImage",
        "inputs": {"images": ["4", 0]}
    },
    "6": {
        "class_type": "MaskPreview",
        "inputs": {"mask": ["4", 1]}
    }
}
```

### 12.2 FaceDetailer 最小工作流

```python
"""
FaceDetailer 最小工作流
"""
workflow = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "realisticVision_v51.safetensors"}
    },
    "2": {
        "class_type": "UltralyticsDetectorProvider",  # Impact Subpack
        "inputs": {"model_name": "face_yolov8m.pt"}
    },
    "3": {
        "class_type": "SAMLoader",
        "inputs": {
            "model_name": "sam_vit_b_01ec64.pth",
            "device_mode": "AUTO"
        }
    },
    "4": {
        "class_type": "FaceDetailer",
        "inputs": {
            "image": ["source_image", 0],
            "model": ["1", 0],
            "clip": ["1", 1],
            "vae": ["1", 2],
            "positive": ["pos_cond", 0],
            "negative": ["neg_cond", 0],
            "bbox_detector": ["2", 0],
            "sam_model_opt": ["3", 0],
            "guide_size": 384,
            "guide_size_for": True,
            "max_size": 1024,
            "seed": 12345,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 0.35,
            "feather": 5,
            "noise_mask": True,
            "force_inpaint": True,
            "bbox_threshold": 0.5,
            "bbox_dilation": 10,
            "bbox_crop_factor": 3.0,
            "sam_detection_hint": "center-1",
            "sam_dilation": 0,
            "sam_threshold": 0.93,
            "sam_bbox_expansion": 0,
            "sam_mask_hint_threshold": 0.7,
            "sam_mask_hint_use_negative": "False",
            "drop_size": 10,
            "wildcard": "",
            "cycle": 1
        }
    }
}
```

---

## 13. 常见问题诊断

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| SAM 分割边缘粗糙 | ViT-B 精度有限 | 升级到 ViT-H 或 SAM-HQ |
| GroundingDINO 检测不到目标 | threshold 太高 / 描述不准确 | 降低 threshold 到 0.2 / 用更具体的描述 |
| FaceDetailer 输出模糊 | guide_size 太小 | 提高 guide_size 到 512+ |
| FaceDetailer 面部变形 | denoise 太高 | 降到 0.25-0.35 |
| Mask 边缘有黑边 | 缺少 feathering | 增加 feather 值 / 使用 Gaussian Blur Mask |
| 多人脸只处理了部分 | bbox_threshold 太高 | 降低 bbox_threshold / 检查 drop_size |
| SAM2 视频追踪丢失 | 目标遮挡/快速运动 | 在关键帧添加新 prompt / 用更大模型 |
| RMBG 细节丢失 | 前景与背景颜色接近 | 尝试 BiRefNet-matting / 手动后处理 |

---

## 14. 总结与关键认知

### 14.1 分割技术选择矩阵

| 需求 | 推荐方案 | 节点包 | 质量 | 速度 |
|------|---------|--------|------|------|
| 背景移除 | RMBG 2.0 | ComfyUI-RMBG | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 文本→分割 | Grounded-SAM | comfyui_segment_anything | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 人脸增强 | FaceDetailer | Impact Pack | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 视频追踪 | SAM2 Video | ComfyUI-segment-anything-2 | ⭐⭐⭐⭐ | ⭐⭐ |
| 多任务 | Florence-2 | ComfyUI-Florence2 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 全图自动分割 | SAM2 Auto | ComfyUI-segment-anything-2 | ⭐⭐⭐⭐ | ⭐⭐ |
| 通用检测 | YOLO v8 | Impact Subpack | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 14.2 核心认知

1. **分割是组合管线** — 很少单独使用某一个模型，通常是 检测→分割→操作→应用 四步
2. **SEGS 是 Impact Pack 的灵魂** — 理解 SEGS 数据结构是用好 Impact Pack 的前提
3. **SAM2 是视频分割的突破** — 流式记忆架构解决了逐帧分割不一致的问题
4. **GroundingDINO 的三阶段融合是关键** — 这是它超越其他开放词汇检测器的核心原因
5. **denoise 是 FaceDetailer 的灵魂参数** — 0.3-0.4 是安全区间，过高必变脸
6. **noise_mask 必须开** — 这是 FaceDetailer 输出自然的关键
7. **背景移除用专用模型** — RMBG/BiRefNet 比通用 SAM 更适合抠图任务
