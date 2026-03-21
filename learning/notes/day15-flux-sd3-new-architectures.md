# Day 15: Flux / SD3 新架构深度解析

> 学习时间: 2026-03-21 16:03 UTC | 轮次: 23

## 1. 从 U-Net 到 DiT：架构范式转移

### 1.1 SD 架构演进时间线
```
SD 1.x (2022.08) → U-Net + CLIP-L        → 860M 参数
SD 2.x (2022.11) → U-Net + OpenCLIP      → 865M 参数  
SDXL   (2023.07) → U-Net + CLIP-L+G      → 2.6B 参数（仍是 U-Net 最后的辉煌）
SD3    (2024.03) → MMDiT + CLIP-L+G+T5   → 2B/8B 参数（DiT 范式转移）
SD3.5  (2024.10) → MMDiT(x) + CLIP-L+G+T5 → 2.5B/8B 参数
Flux.1 (2024.08) → Double/Single Stream DiT → 11.9B 参数（Flux 由 BFL 创始团队开发，即 SD 原班人马）
```

**核心转变**: 
- U-Net 时代: 卷积层 + 少量 Attention（局部感受野 + 跳连接）
- DiT 时代: 纯 Transformer（全局注意力 + 无卷积偏置 + 更好的可扩展性）

### 1.2 为什么要抛弃 U-Net？
1. **可扩展性瓶颈**: U-Net 的参数增长效率低（SDXL 2.6B 已接近上限）
2. **全局上下文**: Transformer 原生支持长程依赖（U-Net 需要堆叠层才能扩大感受野）
3. **多模态融合**: Transformer 天然适合处理不同模态的 token 序列
4. **Scaling Law**: DiT 遵循 LLM 式的 scaling law — 参数越大、数据越多、效果越好

---

## 2. Rectified Flow：从 DDPM 到直线路径

### 2.1 DDPM vs Rectified Flow 核心区别

**DDPM（传统扩散）**:
```
训练目标: ε-prediction（预测噪声）
  L_ε = E[||ε_θ(x_t, t) - ε||²]
  
前向过程: x_t = √(α_t) · x_0 + √(1-α_t) · ε
采样路径: 弯曲的随机轨迹（SDE/ODE）
需要: 复杂的 noise schedule + 多步迭代
```

**Rectified Flow（SD3/Flux 使用）**:
```
训练目标: v-prediction（预测速度向量）
  L_v = E[||v_θ(x_t, t) - (x_1 - x_0)||²]

前向过程: x_t = (1-t) · x_0 + t · x_1  （线性插值！）
  其中 x_0 ~ N(0,I)（噪声）, x_1 ~ p_data（数据）
采样路径: 直线路径（Optimal Transport）
优势: 更少步数、更稳定、更简单
```

### 2.2 直线路径为什么更好？

```
传统扩散路径:          Rectified Flow 路径:
  噪声 ──╮              噪声 ──────→ 数据
         ╰──╮                    （直线！）
              ╰──→ 数据
  （弯曲，需要很多步）    （直线，少步即可）
```

- **误差累积少**: 直线路径每步偏差不会放大
- **步数效率**: Euler 离散化一步就能走很远
- **理论保证**: Optimal Transport 理论保证了这是 Wasserstein 距离最优的传输路径

### 2.3 Logit-Normal 时间步采样（SD3 特有）
- 传统: 均匀采样 t ~ U(0, 1)
- SD3: logit-normal 采样，**偏重中间时间步**
- 原因: 中间步的信噪比变化最大，是 "最难学" 的部分
- 数学: t = σ(μ + σ·z), z ~ N(0,1)，μ=0, σ=1 使采样集中在 t≈0.5

---

## 3. SD3 / SD3.5 架构详解

### 3.1 MMDiT（Multimodal Diffusion Transformer）

**核心创新: Joint Attention with Separate Weights**

```
传统 DiT:          MMDiT:
┌──────────┐       ┌─────────┬─────────┐
│ Image    │       │ Image   │  Text   │
│ tokens   │       │ tokens  │ tokens  │
│          │       │   ↓     │    ↓    │
│ Self-Attn│       │ Q_i K_i │ Q_t K_t │  ← 各自独立的 QKV 权重
│          │       │ V_i     │ V_t     │
│ Cross-Attn       │         │         │
│ (text)   │       │  concat(Q_i, Q_t)  │  ← 拼接后做联合注意力
│          │       │  concat(K_i, K_t)  │
│ FFN      │       │  Softmax(QK^T/√d)V │
└──────────┘       │         │         │
                   │ split → │ split → │  ← 分回各自的 stream
                   │ MLP_i   │ MLP_t   │  ← 各自独立的 FFN
                   └─────────┴─────────┘
```

**关键点**:
1. **两组独立权重**: text 和 image 各有自己的 QKV 投影和 FFN
2. **联合注意力**: QKV 拼接后做一次大的 self-attention（取代了 cross-attention！）
3. **等价效果**: 一次 joint attention = self-attention + cross-attention（但更高效）
4. **adaLN（Adaptive Layer Normalization）**: 用 timestep embedding 调制 shift/scale/gate

### 3.2 SD3 三文本编码器系统

```
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│  CLIP-L/14  │  │ CLIP-G/14   │  │  T5-XXL      │
│  (768d)     │  │ (1280d)     │  │  (~5B params) │
└──────┬──────┘  └──────┬──────┘  └──────┬───────┘
       │                │                │
  Token 768d      Token 1280d      Token 4096d
  Pooled 768d     Pooled 1280d     （无 pooled）
       │                │                │
       ├────────────────┤                │
       ↓ 拼接+投影       ↓                ↓
  Pooled: 768+1280      Token:           Token:
  → timestep embed      pad to 4096d     原始 4096d
                        ↓─── concat ─────↓
                      Joint text token sequence
                      → MMDiT joint attention
```

- **CLIP 双编码器**: 提供 pooled embedding（全局语义锚点）+ token embedding
- **T5-XXL**: 提供深层语言理解（对复杂/长 prompt 至关重要）
- **训练时 40% dropout**: 每个编码器独立 dropout → 推理时可去掉 T5 以省 VRAM
- **去掉 T5 的影响**: 质量下降较小，主要影响**文字渲染**能力

### 3.3 SD3 版本对比

| 维度 | SD3 Medium | SD3.5 Medium | SD3.5 Large | SD3.5 Large Turbo |
|------|-----------|-------------|-------------|------------------|
| 参数量 | 2B | 2.5B | 8B | 8B |
| 架构 | MMDiT | MMDiT-X | MMDiT | MMDiT |
| DiT Blocks | 24 | 38 (MMDiT-X 多了额外 self-attn) | 38 | 38 |
| 推荐步数 | 28-50 | 28-50 | 28-50 | 4-8 |
| VAE Channels | 16 | 16 | 16 | 16 |
| 文本编码器 | CLIP-L + CLIP-G + T5-XXL | 同 | 同 | 同 |
| Turbo 蒸馏 | ❌ | ❌ | ❌ | ✅ (ADD) |
| 许可 | 非商用 → 后开放 | 社区许可 | 社区许可 | 社区许可 |
| 最大分辨率 | 1MP | 2MP | 2MP | 2MP |

**MMDiT-X（SD3.5 Medium 独有）**: 在 MMDiT 基础上增加了额外的自注意力层，用更多注意力层弥补参数量不足

### 3.4 SD3 QKV Normalization
- **问题**: 高分辨率 + 混合精度(bf16) 训练会导致 loss 发散
- **解决方案**: 对 Q 和 K 施加 RMSNorm（在 attention 计算前）
- **效果**: 稳定 bf16 训练，不需要回退到 fp32（2× 速度优势）
- 这个技巧后来被 Flux 和几乎所有后续 DiT 模型采用

---

## 4. Flux.1 架构详解

### 4.1 概述

Flux.1 由 Black Forest Labs (BFL) 开发，其核心团队就是 Stable Diffusion / LDM 的原作者（Robin Rombach 等）。Flux 没有发布论文，架构通过逆向工程从开源推理代码中解析。

**核心数字**:
- **11.9B 参数** 的 Transformer
- **16 通道 VAE**（与 SD3 共享 VAE 设计理念，从 4→16 通道）
- **2 个文本编码器**: CLIP-L + T5-XXL（去掉了 CLIP-G）
- **Rectified Flow 训练**
- **Guidance Distillation**（Flux.1-Dev 的核心创新）

### 4.2 双流 + 单流 Transformer 架构

**Flux 的核心架构创新**: 混合使用两种 Transformer Block

```
输入预处理:
  Image latents → Patchify(2×2) → Linear → image tokens
  Text → T5 → token embeddings (encoder_hidden_states)
  Text → CLIP → pooled embedding (pooled_projection)
  Timestep → MLP → timestep embedding
  Guidance → MLP → guidance embedding (仅 dev 版)
  
  ↓

╔═══════════════════════════════════════╗
║  19 × Double-Stream Block (MMDiT 风格) ║
║                                       ║
║  ┌──────────┐    ┌──────────┐        ║
║  │ Image    │    │  Text    │        ║
║  │ stream   │    │  stream  │        ║
║  │          │    │          │        ║
║  │ Q_i K_i  │    │ Q_t K_t  │        ║
║  │ V_i      │    │ V_t      │        ║
║  │    ↓     │    │    ↓     │        ║
║  │ concat QKV → Joint Attention     ║
║  │    ↓     │    │    ↓     │        ║
║  │ MLP_img  │    │ MLP_txt  │        ║
║  └──────────┘    └──────────┘        ║
║  （文本和图像独立处理 + 联合注意力）      ║
╚════════════════════╤══════════════════╝
                     ↓ concat(img, txt)
╔═══════════════════════════════════════╗
║  38 × Single-Stream Block             ║
║                                       ║
║  ┌────────────────────────────┐      ║
║  │ [img_tokens; txt_tokens]   │      ║
║  │         ↓                  │      ║
║  │  Shared QKV + Self-Attn   │      ║  ← 共享权重！
║  │         ↓                  │      ║
║  │  Shared MLP               │      ║  ← 更高效
║  └────────────────────────────┘      ║
║  （文本和图像合并为统一序列处理）        ║
╚════════════════════╤══════════════════╝
                     ↓ extract img tokens
                 Final Layer
                     ↓
                Output latent
```

### 4.3 Double-Stream vs Single-Stream 设计哲学

| 特性 | Double-Stream Block | Single-Stream Block |
|-----|-------------------|-------------------|
| 数量 | 19 层 | 38 层 |
| 权重 | text/image 独立权重 | text/image 共享权重 |
| 注意力 | Joint Attention（concat QKV） | Self-Attention（统一序列） |
| MLP | 独立的 MLP_img + MLP_txt | 共享 MLP |
| 优势 | 模态特异性（专业化） | 效率 + 深度融合（简洁性） |
| 类比 | 早期学习：各科分开教 | 后期融合：综合应用 |

**设计直觉**:
- 前 19 层（Double-Stream）: 让文本和图像各自学习各自的特征空间，但通过 joint attention 交换信息
- 后 38 层（Single-Stream）: 两种模态已经足够对齐，可以用共享权重统一处理
- 这是一种 **渐进融合** 策略，兼顾了效率和表达能力

### 4.4 Flux 的 Positional Encoding

Flux 使用 **Rotary Position Embedding (RoPE)** 而非传统的正弦位置编码：
- Image tokens: 2D 网格位置 (h, w)
- Text tokens: 统一设为 (0, 0, 0)
- img_ids 格式: (t, h, w) — t 维度为 0（预留给视频扩展？）
- RoPE 优势: 外推性好、相对位置编码、对变分辨率友好

### 4.5 Flux 模型变体

| 变体 | Flux.1 Pro | Flux.1 Dev | Flux.1 Schnell |
|------|-----------|-----------|---------------|
| 开放性 | API only | 开源权重 | 开源权重 |
| 许可 | 商用 API | 非商用 | Apache 2.0 |
| 参数 | 11.9B | 11.9B | 11.9B |
| 训练方法 | 完整训练 | Guidance Distillation | LADD (Latent Adversarial Diffusion Distillation) |
| 推荐步数 | 25-50 | 20-50 | 1-4 |
| CFG | 需要 | **不需要**（CFG=1） | 不需要 |
| Guidance 输入 | ❌ | ✅ (distilled_cfg_scale) | ❌ |
| 用途 | 商用最佳质量 | 开发/微调/LoRA | 实时/快速迭代 |

**Guidance Distillation（Dev 独有机制）**:
- 教师模型（Pro）用传统 CFG 生成
- 学生模型（Dev）学习将 guidance_scale 作为输入条件（而非 CFG 的双推理）
- 结果: **一次推理** 即可获得 CFG 效果（速度翻倍）
- guidance_in MLP 接收 guidance_scale 并编码为 embedding 注入每个 block

---

## 5. SD3 vs Flux 全维度对比

### 5.1 架构对比

| 维度 | SD3 (8B) | Flux.1 Dev |
|------|---------|-----------|
| 参数量 | 8B | 11.9B |
| 骨干 | MMDiT（统一 joint attention） | Double-Stream + Single-Stream |
| Block 数 | 38 | 19 + 38 = 57 |
| 文本编码器 | CLIP-L + CLIP-G + T5-XXL | CLIP-L + T5-XXL |
| VAE | 16 通道 | 16 通道 |
| 位置编码 | 2D Sinusoidal | RoPE |
| 训练方式 | Rectified Flow | Rectified Flow + Guidance Distillation |
| CFG | 需要（双推理） | 不需要（单推理，guidance 已蒸馏） |
| Patchify | 2×2 | 2×2 |
| adaLN | ✅ | ✅ |
| QKV Norm | RMSNorm | RMSNorm |
| 训练数据 | 未公开 | 未公开 |

### 5.2 性能与社区评价

| 方面 | SD3/SD3.5 | Flux.1 |
|------|----------|--------|
| 图像质量 | 好（Large Turbo 尤其实用） | **更好**（ELO 评分领先） |
| Prompt 遵循 | 好（T5 帮助大） | **更好**（文字渲染尤其出色） |
| 文字渲染 | 较好 | **优秀**（industry-leading） |
| LoRA 生态 | 较少（社区支持弱） | **丰富**（CivitAI 大量 Flux LoRA） |
| ControlNet | 有社区移植 | **成熟**（XLabs/InstantX ControlNet） |
| 训练工具 | sd-scripts 支持 | sd-scripts + ComfyUI-FluxTrainer + ai-toolkit |
| VRAM 需求 | Large: ~24GB | ~24GB (fp16) / ~12GB (fp8) |
| 推理速度 | Turbo: 4步极快 | Schnell: 1-4步极快 |
| 社区活跃度 | 低迷（SD3 初始发布争议大） | **极高**（当前主流选择） |

### 5.3 SD3 争议与教训
1. **初始发布质量问题**: SD3 Medium 首发时质量不及预期（手指/人体畸形）
2. **许可争议**: 最初的非商用限制引发社区不满
3. **SD3.5 挽救**: SD3.5 Large/Turbo 大幅改善质量，挽回部分口碑
4. **但已被 Flux 超越**: 社区重心已转向 Flux（更好的质量 + 更宽松的许可）

---

## 6. ComfyUI 工作流差异

### 6.1 SD3/SD3.5 ComfyUI 工作流

```
CheckpointLoaderSimple ─→ model, clip, vae
                           │
CLIPTextEncodeSD3 ─────→ positive_cond  ← 注意: SD3 专用编码器
CLIPTextEncodeSD3 ─────→ negative_cond  
                           │
EmptySD3LatentImage ───→ latent  ← 16 通道 latent
                           │
KSampler ─────────────→ samples
  sampler: euler / dpmpp_2m
  scheduler: normal / sgm_uniform
  cfg: 4.0-7.0
  steps: 28-50 (Large) / 4-8 (Turbo)
                           │
VAEDecode ────────────→ image
```

**SD3 特殊节点**:
- `CLIPTextEncodeSD3`: 支持 clip_l / clip_g / t5xxl 三路文本输入
- `EmptySD3LatentImage`: 生成 16 通道空 latent（而非 SD1.5 的 4 通道）

### 6.2 Flux ComfyUI 工作流

```
方法 A: 简单模式
  UNETLoader ──→ model (Flux UNET)
  DualCLIPLoader ──→ clip (CLIP-L + T5)
  VAELoader ──→ vae
  
方法 B: 一体化
  CheckpointLoaderSimple ──→ model, clip, vae

CLIPTextEncode ──→ positive  ← Flux 用标准编码器即可
(Flux 不用 negative prompt!)
                    │
EmptyLatentImage ──→ latent (1024x1024 推荐)
                    │
KSampler:
  sampler: euler
  scheduler: simple / beta
  cfg: 1.0  ← ⚠️ CFG 必须为 1！（已蒸馏）
  steps: 20-30 (Dev) / 1-4 (Schnell)
  
  或使用 KSamplerAdvanced + BasicGuider:
    FluxGuidance node → guidance_scale 3.5
                    │
VAEDecode ──→ image
```

**Flux 关键差异**:
1. **无 negative prompt**: Flux 不使用负面提示（CFG=1）
2. **FluxGuidance 节点**: 替代 CFG，将 guidance_scale 作为模型输入
3. **推荐 euler sampler**: Flux 的 rectified flow 与 euler 最契合
4. **simple/beta scheduler**: 不用 karras/exponential

### 6.3 Flux LoRA 训练与 SD3 的区别

| 维度 | SD3 LoRA | Flux LoRA |
|------|---------|----------|
| 训练脚本 | sd-scripts (sd3_train_network.py) | sd-scripts (flux_train_network.py) / ComfyUI-FluxTrainer |
| LoRA 模块 | lora_sd3.py | lora_flux.py |
| 训练目标 | v-prediction | v-prediction (flow matching) |
| 图片数量 | 20-50 | 10-30 |
| dim 推荐 | 16-32 | 16-64 |
| 步数 | 2000-5000 | 1500-3000 |
| VRAM | ~24GB | ~24GB (fp16) / ~16GB (fp8+gradient checkpoint) |
| TE 训练 | 可选 | 通常冻结（11.9B 太大） |
| 社区支持 | 弱 | **强** |

---

## 7. RunningHub 实验

### 实验 #22: Flux/SD3 架构对比概念图
- **端点**: rhart-image-n-pro/text-to-image
- **Prompt**: 技术架构对比图（SD3 MMDiT vs Flux Double/Single Stream）
- **耗时**: ~25s
- **成本**: ¥0.030
- **输出**: /tmp/rh-output/flux-sd3-architecture-comparison.jpg
- **用途**: 辅助理解两种架构的结构差异

---

## 8. 关键洞察总结

### 8.1 架构演进的核心逻辑
```
SD1.5: U-Net + 1 CLIP → 快速但质量有限
SDXL:  U-Net + 2 CLIP → 质量飞跃但仍受 U-Net 限制
SD3:   MMDiT + 3 编码器 → DiT 范式转移，但初期口碑问题
Flux:  DS+SS DiT + 2 编码器 → 当前 SOTA，guidance distillation 创新
```

### 8.2 设计选择的权衡

1. **Joint Attention (SD3) vs Double/Single Stream (Flux)**
   - SD3: 始终混合，简单统一，但每层都需要处理两种模态
   - Flux: 先分后合，渐进融合，更好的模态专业化

2. **3 编码器 (SD3) vs 2 编码器 (Flux)**
   - SD3: CLIP-L + CLIP-G + T5 → 更丰富的文本表征
   - Flux: CLIP-L + T5 → 去掉 CLIP-G，T5 已足够强（简化 pipeline）

3. **CFG (SD3) vs Guidance Distillation (Flux)**
   - SD3: 传统 CFG（每步 2 次推理）
   - Flux Dev: 蒸馏后单次推理（速度 2×，且避免 CFG 伪影）

### 8.3 对 ComfyUI 工作流编排的启示
1. **Flux 更简单**: 无 negative prompt、CFG=1、euler sampler
2. **SD3 更灵活**: 三编码器可以分别控制
3. **LoRA 生态**: Flux 生态远超 SD3（CivitAI 资源丰富度差距巨大）
4. **ControlNet**: Flux 的 ControlNet 生态日趋成熟（XLabs/InstantX）
5. **视频扩展**: Flux 的 (t, h, w) img_ids 设计预留了时间维度 → 视频原生支持

### 8.4 2025-2026 趋势判断
- **SD3/SD3.5**: 已逐渐边缘化，仅 Large Turbo 仍有使用价值
- **Flux**: 当前社区主流，LoRA/ControlNet/IP-Adapter 生态完善
- **下一代**: Flux.1 Kontext（in-context editing）、Flux 2.0（预期中）
- **竞争者**: Midjourney V7、DALL-E 4、Imagen 3 — 但均为闭源
- **本地部署**: fp8 量化使 Flux 可在 12GB VRAM 上运行（RTX 4070 级别）

---

## 9. 与之前学习的关联

| 之前的知识 | 在 Flux/SD3 中的体现 |
|-----------|-------------------|
| Day1 DDPM/LDM | SD3/Flux 从 ε-prediction 进化到 v-prediction + flow matching |
| Day2 采样器 | Flux 推荐 euler（flow matching 的最佳搭配） |
| Day3 ComfyUI 架构 | 新的节点类型（CLIPTextEncodeSD3/FluxGuidance/DualCLIPLoader）|
| Day7 LoRA | Flux LoRA 使用专用的 lora_flux.py（DiT 架构的 LoRA 适配） |
| Day8 SDXL | SDXL 的双编码器 → SD3 的三编码器 → Flux 回到双编码器 |
| Day9 LoRA 训练 | Flux 训练更高效（10-30 图 + flow matching 收敛更快） |
| Day12 API 节点 | Flux 也有 API 服务节点（BFL API / fal.ai / Replicate） |
| Day14 自定义节点 | Flux 节点遵循相同的 INPUT_TYPES/RETURN_TYPES 规范 |
