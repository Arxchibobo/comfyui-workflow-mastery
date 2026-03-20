# Day 6 (续): Tile ControlNet + IP-Adapter + 多 ControlNet 组合

> 学习时间: 2026-03-20 20:03 UTC (Session 13)
> 参考论文: IP-Adapter (Ye et al., 2023, arXiv:2308.06721)
> 参考: ComfyUI 官方文档 Mixing ControlNets、ControlNet v1.1 Tile 模型

---

## §1 Tile ControlNet — 超分辨率的秘密武器

### 1.1 Tile ControlNet ≠ 普通放大器

**常见误解**: Tile ControlNet 是一个"upscaler"。
**实际定位**: **结构细节重建器 (Structural Detail Reconstructor)**。

与其他 ControlNet 模型（Canny 提取边缘、Depth 提取深度）不同，Tile ControlNet：
- **不需要传统预处理器**（没有边缘检测、没有深度估计）
- **直接分析图像 tile 的局部语义**
- **在保持局部结构的同时"幻觉"出高频细节**

### 1.2 为什么需要 Tile ControlNet

**问题背景**: SD 在生成超大图像时（如 4096×4096）容易出错——两个头、六条腿，因为模型对巨大画布缺乏全局视野。

**Tiled Diffusion 方案**: 把大图切成 512×512 或 1024×1024 的小 tiles，逐个处理。

**但没有 Tile ControlNet 的问题**:
- 模型看到一个只含"皮肤纹理"的 tile → 可能把整个 tile 变成一张"脸"
- 结果：图像上出现一堆恐怖的重复面孔

**Tile ControlNet 的两个核心作用**:

| 作用 | 说明 | 例子 |
|------|------|------|
| **保持局部结构** | 告诉模型"这个 tile 是山的一部分，别变成别的" | 避免语义漂移 |
| **细节注入** | 允许模型"幻觉"出高频纹理 | 雪花、岩石裂缝、皮肤毛孔 |

### 1.3 Tile ControlNet 的 Prompt 冲突处理

**一个精妙的设计**: 当全局 prompt 和局部 tile 内容冲突时：
- 全局 prompt = "金色宫殿"
- 局部 tile 内容 = 绿色的树

普通扩散模型可能混合出"金色的树"。而 Tile ControlNet 会**优先服从图像内容**，保持树的绿色。
→ 这种 **"局部语义感知" (Local Semantic Awareness)** 是它成为旧照片修复金标准的原因。

### 1.4 三阶段超分辨率管线 (Supra-Resolution Pipeline)

```
Stage 1: AI 放大 (ESRGAN / SwinIR / 4x-UltraSharp)
├── 确定性放大：增加像素数，但不增加"新信息"
├── 输出：更大但依然模糊的图像
│
Stage 2: Tile-Conditioned Diffusion
├── 用 SD/SDXL + Tile ControlNet 处理放大后的图像
├── denoise = 0.3~0.45（低 denoise 保结构，高 denoise 多幻觉）
├── Tile ControlNet weight = 1.0
├── 模型看着模糊像素 → 在 Tile 引导下替换为真实纹理
│
Stage 3: 频率混合 (可选)
├── 高通滤波器混合原始颜色 + AI 生成的纹理
└── 保证 100% 色彩准确性 + AI 锐度
```

### 1.5 关键参数速查

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| denoise | 0.3-0.45 | <0.3 几乎不变，>0.5 开始偏离原图 |
| ControlNet strength | 0.5-1.0 | <0.5 太弱会幻觉，建议 ≥0.5 |
| Tile 尺寸 | 512(SD1.5) / 1024(SDXL) | 匹配模型原生分辨率 |
| Overlap | 128px | 避免 tile 接缝 |
| Upscale 模型 | 4x-UltraSharp | 社区公认最佳通用放大模型 |

### 1.6 ComfyUI 中的 Tile 工作流拓扑

```
LoadImage → ImageUpscaleWithModel (4x-UltraSharp)
                  ↓
            VAEEncode
                  ↓
LoadCheckpoint → KSampler (denoise=0.35)
     ↓                ↑
  CLIPTextEncode  ←   │
     ↓                │
  ControlNetLoader → ApplyControlNet → conditioning
  (tile model)        ↑
                  LoadImage (same upscaled image)
                      ↓
                  VAEDecode → SaveImage
```

**注意**: Tile ControlNet 的条件图像就是要处理的图像本身（放大后的），不需要额外的预处理器。

### 1.7 SD1.5 vs SDXL vs Flux 的 Tile 支持

| 模型 | Tile 支持 | 模型文件 |
|------|----------|----------|
| SD 1.5 | ✅ 完善 | control_v11f1e_sd15_tile.pth |
| SDXL | ✅ 可用 | 社区训练版本 (如 xinsir/controlnet-tile-sdxl) |
| Flux | ❌ 暂无 | 截至 2026 年仍无官方 Tile ControlNet |

---

## §2 IP-Adapter — 图像 Prompt 适配器

### 2.1 核心问题

文字 prompt 的局限：
- 无法精确描述特定艺术风格（试试用文字描述米开朗基罗的画风？）
- 无法传递具体的视觉纹理、色彩方案
- 复杂 prompt engineering 门槛高

**IP-Adapter 的解决方案**: 让扩散模型同时接受**文字 prompt** + **图像 prompt**。

### 2.2 架构设计 — 解耦的双交叉注意力

**核心创新**: Decoupled Cross-Attention（解耦交叉注意力）

```
原始 SD U-Net 的交叉注意力:
  Q = latent features (来自图像 latent)
  K, V = text embeddings (来自 CLIP text encoder)
  
IP-Adapter 新增的图像交叉注意力:
  Q = latent features (同一个)  
  K', V' = image embeddings (来自 CLIP vision encoder)

最终输出:
  output = TextCrossAttn(Q, K_text, V_text) + λ · ImageCrossAttn(Q, K_img, V_img)
```

**为什么要解耦而不是拼接？**

| 方法 | 做法 | 问题 |
|------|------|------|
| 特征拼接 (T2I-Adapter 等) | concat(text_feat, img_feat) → 共享 K,V | 强制图像特征对齐到文字空间，丢失图像特有信息，只能粗粒度控制(如风格) |
| 解耦注意力 (IP-Adapter) | 独立的 K,V 投影 | 两种模态各走各的路径，互不干扰，精细度高 |

### 2.3 双通路设计

```
通路 1: 语义控制 (原始文字交叉注意力)
├── 控制"生成什么"
├── 物体识别、场景构图、布局
└── 高层概念理解

通路 2: 视觉风格控制 (图像交叉注意力)  
├── 控制"看起来像什么"
├── 纹理细节、表面属性
├── 色彩方案、艺术技法
└── 视觉层次和构图风格
```

### 2.4 图像编码器

**CLIP ViT (Vision Transformer)**:
- 将参考图像编码为语义丰富的特征向量
- IP-Adapter 原版使用 CLIP ViT-H/14 (patch=14, hidden=1280)
- IP-Adapter Plus 使用 CLIP ViT 的中间层特征（而非只用最后一层 [CLS] token）
  → 保留更多空间信息和细节

| 变体 | 图像特征 | 效果 |
|------|---------|------|
| IP-Adapter (基础) | CLIP 全局 [CLS] token (1×1024) | 风格迁移为主，细节弱 |
| IP-Adapter Plus | CLIP 中间层 patch tokens (257×1280) | 更强的细节保留 |
| IP-Adapter FaceID | 使用 InsightFace 而非 CLIP | 专注人脸身份保持 |

### 2.5 训练过程

```
冻结部分 (不训练):
├── 预训练 U-Net
├── CLIP text encoder  
└── CLIP image encoder

训练部分 (~22M 参数，仅占总量 3-5%):
├── 图像交叉注意力层 (新增的 K', V' 投影)
├── 线性投影模块 (映射图像嵌入到正确维度)
└── LayerNorm 层

损失函数:
  L = ||ε - ε_θ(z_t, t, c_text, c_image)||²
  (标准扩散 L2 noise prediction loss)
```

**22M 参数就能达到甚至超过全量微调的效果** — 这是 IP-Adapter 的惊人之处。

### 2.6 IP-Adapter 的变体

| 变体 | 用途 | ComfyUI 节点 |
|------|------|-------------|
| IP-Adapter | 基础风格迁移 | IPAdapterApply |
| IP-Adapter Plus | 更强细节+风格 | IPAdapterApply |
| IP-Adapter Plus Face | 面部风格 | IPAdapterApply |
| IP-Adapter FaceID | 人脸身份保持 | IPAdapterFaceID |
| IP-Adapter FaceID Plus | 面部身份+质量 | IPAdapterFaceID |
| IP-Adapter Style & Composition | SDXL 专用，分离风格和构图 | IPAdapterStyleComposition |

### 2.7 IP-Adapter 与 ControlNet 的对比

| 维度 | ControlNet | IP-Adapter |
|------|-----------|------------|
| 控制目标 | 空间结构（边缘/深度/姿势） | 语义风格（纹理/色彩/内容） |
| 注入方式 | 零卷积 → U-Net encoder/middle | 解耦交叉注意力 → U-Net attention |
| 条件图像 | 需要预处理（Canny/Depth/Pose） | 直接使用原始图像 |
| 参数量 | ~360M (复制了半个 U-Net) | ~22M (仅交叉注意力层) |
| 兼容性 | 可与 IP-Adapter 叠加 | 可与 ControlNet 叠加 |

**最佳组合**: IP-Adapter (控制风格) + ControlNet (控制结构) → 风格+结构双重控制

### 2.8 ComfyUI 中的 IP-Adapter 工作流

```
LoadCheckpoint
     ↓
CLIPVisionLoader → IPAdapterModelLoader
     ↓                    ↓
LoadImage(参考图) → IPAdapterApply ← model
     ↓                              ↓
  (可选: ControlNet)        KSampler
                               ↓
                          VAEDecode → SaveImage
```

**关键参数**:
- `weight` (0.0-2.0): 图像 prompt 影响力，推荐 0.6-1.0
- `noise` (0.0-1.0): 给图像嵌入加噪声，增加多样性
- `weight_type`: standard / style / composition / strong style transfer

### 2.9 IP-Adapter 在 ComfyUI 中的核心节点 (ComfyUI_IPAdapter_plus)

| 节点 | 用途 |
|------|------|
| IPAdapterUnifiedLoader | 自动加载正确的 CLIP vision + IP-Adapter 模型 |
| IPAdapterApply | 基础应用 |
| IPAdapterAdvanced | 高级控制 (weight_type, start/end) |
| IPAdapterFaceID | 人脸身份保持 |
| IPAdapterStyleComposition | SDXL 风格+构图分离 |
| IPAdapterTiled | 分块处理大图 |
| IPAdapterBatch | 批量处理多张参考图 |

---

## §3 多 ControlNet 组合使用

### 3.1 链式连接原理

ComfyUI 中多 ControlNet 的核心是 **Apply ControlNet 节点的链式连接**:

```
CLIPTextEncode (positive prompt)
     ↓ conditioning
ApplyControlNet #1 (Depth)
     ↓ conditioning (已叠加 depth)
ApplyControlNet #2 (Pose)
     ↓ conditioning (已叠加 depth + pose)
ApplyControlNet #3 (Canny)  
     ↓ conditioning (已叠加 depth + pose + canny)
KSampler
```

**源码层面**: 每个 `Apply ControlNet` 把新的 ControlNet 对象追加到 conditioning 的 `control` 链上。在采样时，所有 ControlNet 的输出**信号相加**注入 U-Net。

### 3.2 两种组合模式

#### 模式 A: 区域分工 (Regional Division)

不同 ControlNet 控制图像的**不同区域**:
- Pose ControlNet → 控制左侧人物姿势
- Scribble ControlNet → 控制右侧物体形状

**要点**: 条件图像在各自区域外应该是空白（黑色/零），避免跨区域干扰。

#### 模式 B: 多维控制 (Multi-dimensional Control)

多个 ControlNet 控制**同一个主体的不同维度**:
- Pose + Depth → 控制姿势 + 空间感
- Pose + Canny → 控制姿势 + 边缘细节
- Depth + Canny → 控制空间 + 轮廓
- Pose + Reference(IP-Adapter) → 控制姿势 + 参考风格

**要点**: 参考图像应该对齐到同一个主体。

### 3.3 权重调节策略

| 场景 | 权重建议 | 说明 |
|------|---------|------|
| 区域分工 | 各 1.0 | 不同区域互不干扰，保持均衡 |
| 多维叠加 | 各 0.5-0.8 | 总信号叠加可能过强，需降低 |
| 主导+辅助 | 主 0.8-1.0 / 辅 0.3-0.5 | 明确主次关系 |
| 含 IP-Adapter | IP 0.6-0.8 / CN 0.8-1.0 | IP 过高会压制文字 prompt |

### 3.4 冲突检测与处理

**信号冲突的三种类型**:

| 冲突类型 | 例子 | 解决方案 |
|---------|------|---------|
| 空间冲突 | Pose 说手在左，Depth 暗示右 | 确保条件图像一致 |
| 语义冲突 | Canny 画了猫，Pose 画了人 | 避免混用不同主体 |
| 强度冲突 | 一个 CN 压倒另一个 | 调低强势方权重 |

**调试方法**:
1. 先单独测试每个 ControlNet 的效果
2. 逐个添加，观察叠加效果
3. 如果某个 CN 被压制，提高其 strength 或降低竞争者

### 3.5 start_percent / end_percent 高级策略

```
ControlNet 在采样过程的不同阶段发挥作用:

采样步骤:  [0%] =============================== [100%]
             ↑ 早期: 决定构图和大结构
                           ↑ 中期: 细化形状和比例
                                         ↑ 晚期: 添加细节和纹理

推荐策略:
- Depth:   start=0.0, end=0.5  (只控制早期构图)
- Pose:    start=0.0, end=0.8  (控制全程姿势)
- Canny:   start=0.2, end=1.0  (跳过最早期，控制细节)
- Tile:    start=0.0, end=1.0  (全程保持结构)
- IP-Adapter: start=0.0, end=0.7 (早中期控制风格，晚期释放细节)
```

通过错开不同 ControlNet 的生效区间，可以**在时间维度上减少冲突**。

### 3.6 Comfyroll Multi-ControlNet Stack

社区节点 `CR Multi-ControlNet Stack` + `CR Apply Multi-ControlNet` 提供了更便捷的批量管理方式:

```
CR Multi-ControlNet Stack
├── controlnet_1: depth model, weight=0.8, start=0.0, end=0.5
├── controlnet_2: pose model, weight=1.0, start=0.0, end=0.8
└── controlnet_3: canny model, weight=0.6, start=0.2, end=1.0
      ↓
CR Apply Multi-ControlNet → conditioning → KSampler
```

好处: 一个节点管理所有 ControlNet，参数清晰，易于调试。

### 3.7 IP-Adapter + ControlNet 组合

**最强组合公式**: IP-Adapter (what it looks like) + ControlNet (spatial structure)

```
参考图(风格) → IP-Adapter (weight=0.7)  ─┐
                                          ├─→ conditioning → KSampler
Pose图 → ControlNet Pose (strength=0.9)  ─┘
```

**实际使用 tips**:
- IP-Adapter weight 不要超过 0.8，否则文字 prompt 基本失效
- 先确保 ControlNet 结构正确，再叠加 IP-Adapter 风格
- 如果风格和结构打架，优先降低 IP-Adapter weight

---

## §4 经验总结与决策树

### 4.1 什么时候用什么

```
需要放大图像？
├── 保守放大（不改细节）→ ESRGAN/SwinIR 直接放大
└── 智能放大（添加细节）→ Tile ControlNet + Img2Img

需要风格迁移？
├── 有参考图 → IP-Adapter
├── 只有文字 → Prompt + LoRA
└── 参考图 + 精确结构 → IP-Adapter + ControlNet

需要多种控制？
├── 同区域多维度 → 多 ControlNet 链式 (降低各自 weight)
├── 不同区域 → 区域分工 (保持各自 weight=1.0)
└── 结构 + 风格 → ControlNet + IP-Adapter
```

### 4.2 常见坑

1. **Tile denoise 过高** (>0.5) → 图像偏离原图，失去放大的意义
2. **IP-Adapter weight 过高** (>1.0) → 文字 prompt 完全失效
3. **多 ControlNet 权重总和过大** → 图像过度约束，出现伪影
4. **条件图像分辨率不匹配** → ControlNet 效果不稳定
5. **Flux 没有 Tile ControlNet** → 不要试图用 SD1.5 的 Tile 模型套 Flux

---

*下一步: 编写实践工作流 JSON*
