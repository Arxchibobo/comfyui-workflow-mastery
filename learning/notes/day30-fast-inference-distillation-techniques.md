# Day 30: 快速推理与蒸馏技术 (Fast Inference & Distillation Techniques)

> 学习日期: 2026-03-23 | 轮次: 38 | 主题: Phase 10 — 推理加速方法论

## 1. 为什么需要快速推理

### 1.1 扩散模型的推理瓶颈

传统扩散模型（DDPM/LDM/Rectified Flow）需要 **20-50 步** 迭代去噪：
- SDXL 在 A100 上 50 步约 3-5 秒 → 非实时
- Flux.1 Dev 在 A100 上 28 步约 4-8 秒
- 视频模型更甚：Wan 2.2 生成 5s 视频需要数分钟

**核心矛盾**: 每步都需要完整 forward pass（SDXL 2.6B / Flux 12B），步数 = 成本

### 1.2 加速推理的三条路线

| 路线 | 方法 | 代表 | 步数 | 需要重训 |
|------|------|------|------|---------|
| **更好的求解器** | 高阶 ODE solver | DPM++ 2M, UniPC | 10-20 | ❌ |
| **蒸馏** | 知识蒸馏到少步模型 | LCM, Lightning, Turbo | 1-8 | ✅ |
| **架构优化** | 编译/量化/缓存 | TensorRT, torch.compile | 不变 | ❌ |

**蒸馏是唯一能将步数降到 1-4 步的方法**，也是本笔记的核心主题。

---

## 2. 蒸馏方法学术体系

### 2.1 蒸馏方法分类学

扩散模型蒸馏按核心机制分为 **四大家族**：

```
扩散蒸馏方法
├── 一致性蒸馏 (Consistency Distillation)
│   ├── CM — Consistency Models (Song et al., ICML 2023)
│   ├── iCT — improved Consistency Training (Song & Dhariwal, 2024)
│   ├── LCM — Latent Consistency Models (Luo et al., 2023)
│   ├── PCM — Phased Consistency Models (NeurIPS 2024)
│   ├── ECM — Easy Consistency Models (ICLR 2025)
│   └── AnimateLCM — 视频一致性蒸馏 (SIGGRAPH Asia 2024)
├── 渐进式蒸馏 (Progressive Distillation)
│   ├── PD — Progressive Distillation (Salimans & Ho, ICLR 2022)
│   └── Guidance Distillation (Meng et al., 2023) → Flux Dev
├── 对抗式蒸馏 (Adversarial Distillation)
│   ├── ADD — Adversarial Diffusion Distillation (Sauer et al., 2023) → SDXL Turbo
│   ├── LADD — Latent ADD (Sauer et al., SIGGRAPH Asia 2024) → SD3-Turbo, Flux Schnell
│   └── SDXL-Lightning — Progressive + Adversarial (ByteDance, 2024)
├── 分布匹配蒸馏 (Distribution Matching Distillation)
│   ├── DMD — Distribution Matching (Yin et al., CVPR 2024)
│   ├── DMD2 — Improved DMD (NeurIPS 2024 Oral)
│   └── SenseFlow — 大规模 Flow 蒸馏 (2025)
└── 混合方法
    ├── Hyper-SD — 轨迹分段一致性 + Score Distillation (ByteDance, 2024)
    └── SANA-Sprint — sCM + LADD 混合 (NVIDIA, ICCV 2025)
```

### 2.2 时间线

```
2022.04  Progressive Distillation (Salimans & Ho)
2023.03  Consistency Models (Song et al., OpenAI)
2023.10  LCM (Luo et al.) — 潜空间一致性模型
2023.11  ADD / SDXL Turbo (Stability AI) — 对抗式蒸馏
2023.11  LCM-LoRA — 即插即用加速
2024.01  Improved Consistency Training (iCT)
2024.02  SDXL-Lightning (ByteDance) — 渐进+对抗
2024.02  AnimateLCM — 视频一致性蒸馏
2024.03  LADD / SD3-Turbo (Stability AI) — 潜空间对抗蒸馏
2024.04  Hyper-SD (ByteDance) — 轨迹分段+Score蒸馏
2024.05  DMD2 (MIT) — 改进分布匹配
2024.05  PCM (NeurIPS 2024) — 相位一致性模型
2024.06  ECM / ECT (ICLR 2025) — 易训一致性模型
2024.08  Flux.1 Schnell (BFL) — LADD 蒸馏
2024.08  Flux.1 Dev (BFL) — Guidance Distillation
2025.03  SANA-Sprint (NVIDIA) — sCM + LADD 混合
2025.05  CausVid (CVPR 2025) — 视频因果蒸馏
```

---

## 3. 一致性蒸馏 (Consistency Distillation) 深度解析

### 3.1 Consistency Models 原理 (Song et al., ICML 2023)

**核心思想**: PF-ODE 轨迹上任意一点 x_t 都映射到同一个起点 x_0

```
PF-ODE 轨迹: x_T → x_{t_n} → x_{t_{n-1}} → ... → x_{t_1} → x_0

一致性函数 f(x_t, t) = x_0  对所有 t 成立
即: f(x_{t_1}, t_1) = f(x_{t_2}, t_2) = ... = f(x_T, T) = x_0
```

**数学定义**: 一致性函数 f: (x_t, t) → x_0 满足：
- **自一致性**: f(x_t, t) = f(x_{t'}, t')  ∀ t, t' 在同一 PF-ODE 轨迹上
- **边界条件**: f(x_ε, ε) = x_ε  (当 t→0 时为恒等映射)

**参数化** (skip connection):
```
f_θ(x_t, t) = c_skip(t) · x_t + c_out(t) · F_θ(x_t, t)
```
其中 c_skip(ε) = 1, c_out(ε) = 0 保证边界条件

**两种训练模式**:
1. **Consistency Distillation (CD)**: 需要预训练的教师扩散模型
   - 用教师的 ODE solver 估计 x_{t_{n-1}} 从 x_{t_n}
   - Loss: ||f_θ(x_{t_{n+1}}, t_{n+1}) - f_{θ⁻}(x̂_{t_n}, t_n)||²
   - θ⁻ 是 EMA 目标网络 (类似 DDPM 的 stop-gradient)
2. **Consistency Training (CT)**: 不需要教师，直接从数据训练

**推理**: 单步生成 x_0 = f_θ(x_T, T)，或多步迭代改善质量

### 3.2 Latent Consistency Models (LCM, 2023.10)

**LCM 的关键创新**: 将 Consistency Model 应用到**潜空间**

**增广 PF-ODE**: LCM 不是直接求解原始 PF-ODE，而是求解带 CFG 的增广版本：
```
dx_t/dt = (1+w) · ε_θ(x_t, t, c) - w · ε_θ(x_t, t, ∅)
```
其中 w 是 CFG guidance scale

**一致性蒸馏在潜空间**:
1. 用预训练 SD 模型作为教师
2. 在 latent space 中执行一致性蒸馏
3. 学生直接预测 "干净" latent

**LCM-LoRA** (极为重要的实用创新):
- 将 LCM 蒸馏的知识编码为 LoRA 权重
- **即插即用**: 可以应用到任何 SD1.5/SDXL fine-tune 模型
- 不需要为每个模型单独蒸馏
- 文件大小: SD1.5 ~67MB, SDXL ~395MB

**ComfyUI 使用**:
```
Model Loader → LoRA Loader (LCM-LoRA) → KSampler
                                         ├── sampler: "lcm"
                                         ├── scheduler: "sgm_uniform" 或 "simple"  
                                         ├── steps: 4-8
                                         ├── cfg: 1.0-2.0 (极低!)
                                         └── denoise: 1.0
```

**关键参数**:
| 参数 | LCM 推荐值 | 原因 |
|------|-----------|------|
| sampler | `lcm` | 专用采样器 (内置在 ComfyUI) |
| scheduler | `sgm_uniform` / `simple` | 均匀间距 |
| steps | 4-8 | 超过 8 步收益递减 |
| cfg | 1.0-2.0 | **必须极低**，蒸馏已内化 CFG |
| denoise | 1.0 | 全程去噪 |

⚠️ **陷阱**: 用 LCM-LoRA 时 CFG > 2 会产生过饱和/失真

### 3.3 Phased Consistency Models (PCM, NeurIPS 2024)

**LCM 的三个关键缺陷** (PCM 论文指出):
1. **ODE 轨迹累积误差**: 教师 ODE solver 在大步长时误差大
2. **CFG 内化限制**: LCM 训练时固定 CFG，推理时无法调整
3. **步数上限**: 增加步数反而质量下降 (因为一致性约束过强)

**PCM 核心创新 — 分段一致性**:
```
传统 CM: 整条 ODE 轨迹 [T, 0] → 单个一致性函数
PCM:     将轨迹分为 K 个子段 → 每段独立一致性函数

[T, t_K] → [t_K, t_{K-1}] → ... → [t_1, 0]
  段 K      段 K-1              段 1
```

**优势**:
- 每段内 ODE 步长更短 → 教师误差更小
- 不同段可以有不同 CFG → 灵活控制
- 增加步数 = 增加段数 → 质量单调提升
- 支持 negative prompt (LCM 不支持!)

**PCM 也支持视频**: 用 AnimateLCM 的解耦策略，先图像后视频蒸馏

### 3.4 Easy Consistency Models (ECM / ECT, ICLR 2025)

**目标**: 大幅降低 CM 的训练成本

**关键发现**:
- CM 训练不稳定的根因: loss 权重函数 w(t) 和噪声调度不匹配
- 正确设置 w(t) 后，训练变得简单且高效

**ECT (Easy Consistency Tuning)** 成果:
- CIFAR-10 上 2-step FID 2.73，**1 小时单卡 A100**
- 匹配之前需要 1 周 8 卡的 CD 质量
- 支持 scaling: 更大模型 → 更好质量

---

## 4. 对抗式蒸馏 (Adversarial Distillation) 深度解析

### 4.1 ADD — Adversarial Diffusion Distillation (Stability AI, 2023.11)

**用于**: SDXL Turbo

**三个组件**:
1. **学生模型** (初始化自预训练 SDXL)
2. **教师模型** (冻结的 SDXL)
3. **判别器** (预训练 DINOv2 作为特征提取器)

**训练流程**:
```
噪声 z_T → 学生(1步去噪) → 生成图 x_gen
                                ├── 蒸馏 loss: ||x_gen - 教师多步去噪结果||²
                                └── 对抗 loss: 判别器(x_gen) vs 判别器(真实图)
总 loss = λ_distill · L_distill + λ_adv · L_adv
```

**ADD 的局限**:
- DINOv2 判别器固定在 518×518 → **限制高分辨率训练**
- 判别器在 pixel space → 高分辨率时需要 decode，计算昂贵
- SDXL Turbo 只能生成 **512×512** (重大限制)
- 训练不稳定，超参数敏感

### 4.2 LADD — Latent Adversarial Diffusion Distillation (Stability AI, SIGGRAPH Asia 2024)

**用于**: SD3-Turbo, **Flux.1 Schnell**

**LADD 相对 ADD 的核心改进**:

| 维度 | ADD | LADD |
|------|-----|------|
| 判别器 | 固定 DINOv2 (pixel space) | 预训练扩散模型 (latent space) |
| 训练空间 | Pixel space | **Latent space** |
| 最大分辨率 | 518×518 | **任意分辨率** |
| 判别器特征控制 | 不可控 | **噪声级别控制** (全局 vs 局部) |
| 训练复杂度 | 高 | 低 |
| 需要 VAE decode | 是 | **否** |

**LADD 判别器的精妙设计**:
```
用预训练扩散模型 D_φ 作为判别器:

给生成图加噪: x_gen_t = (1-t)·x_gen + t·ε
让 D_φ 尝试去噪: D_φ(x_gen_t, t) → x_gen_predicted

对抗 loss = || D_φ(x_gen_t, t) - x_gen ||²  (生成图)
         vs || D_φ(x_real_t, t) - x_real ||²  (真实图)
```

**噪声级别控制判别器感知**:
- 高噪声 t → 判别器关注全局结构/构图
- 低噪声 t → 判别器关注局部细节/纹理
- 可以通过采样 t 的分布来**精确控制反馈级别**

**Flux.1 Schnell 使用 LADD**:
- 基于 Flux.1 Dev 进行 LADD 蒸馏
- 1-4 步生成高质量 1024×1024 图像
- Apache 2.0 开源许可

### 4.3 SDXL-Lightning (ByteDance, 2024.02)

**创新**: 首次结合**渐进式蒸馏 + 对抗蒸馏**

**渐进式蒸馏回顾** (Salimans & Ho, 2022):
```
教师: 1024 步 → 蒸馏 → 学生: 512 步
                → 蒸馏 → 学生: 256 步
                → ... → 学生: N 步
每轮蒸馏: 学生一步 = 教师两步
```

**SDXL-Lightning 的组合**:
1. 先用渐进式蒸馏粗略对齐 (高步数 → 中步数 → 低步数)
2. 再用对抗蒸馏精细调优 (在低步数时避免模糊)

**提供两种格式**:
- **Full UNet**: 完整蒸馏权重 (最佳质量)
- **LoRA**: 蒸馏知识编码为 LoRA (可应用到 fine-tune 模型)

**ComfyUI 使用 (Full UNet)**:
```
Checkpoint Loader: sdxl_lightning_4step.safetensors
KSampler:
├── sampler: euler
├── scheduler: sgm_uniform
├── steps: 4 (必须匹配!)
├── cfg: 1.0
└── denoise: 1.0
```

**ComfyUI 使用 (LoRA)**:
```
SDXL Base → LoRA Loader (sdxl_lightning_4step_lora.safetensors, strength=1.0)
KSampler:
├── sampler: euler
├── scheduler: sgm_uniform
├── steps: 4
├── cfg: 1.0
└── denoise: 1.0
```

⚠️ **关键**: 必须使用与步数匹配的 checkpoint! 4-step checkpoint 就用 4 步。

---

## 5. 分布匹配蒸馏 (Distribution Matching Distillation)

### 5.1 DMD2 (MIT, NeurIPS 2024 Oral)

**核心思想**: 不是让学生模仿教师的单个去噪步，而是匹配**整体分布**

**DMD (v1) 方法**:
```
学生生成分布 p_θ  ≈  教师推理分布 p_teacher

通过最小化两个分布的 KL 散度:
D_KL(p_θ || p_teacher) ≈ E[score_teacher(x_gen) - score_fake(x_gen)]

需要训练一个额外的 "fake score" 网络来估计学生分布的 score
```

**DMD2 的三个关键改进**:
1. **Two-timescale 更新**: 分离生成器和 fake score 的更新频率
2. **Regression Loss**: 加入回归损失稳定训练 (仿 ADD 的蒸馏项)
3. **GAN Loss 替代**: 用判别器替代部分 score 匹配

**结果**:
- ImageNet-64×64: **FID 1.28** (首次**超越教师**!)
- Zero-shot COCO 2014: FID 8.35
- 只需**1 步**推理，500x 推理加速

---

## 6. 混合方法

### 6.1 Hyper-SD (ByteDance, 2024.04)

**方法**: 轨迹分段一致性蒸馏 + Score Distillation + 人类反馈

**三阶段训练**:
1. **轨迹分段一致性蒸馏** (TSCD): 类似 PCM 的分段思想
2. **Score Distillation**: 引入人类偏好奖励模型 (类似 RLHF)
3. **统一框架**: 从 1-step 到 8-step 都提供最优模型

**覆盖范围最广**:
- SD 1.5 / SDXL / SD3 / **Flux.1 Dev** 都有蒸馏版本
- 每个基础模型都提供 1-step / 2-step / 4-step / 8-step LoRA
- 1-step 需要特殊 scheduler (从 timestep 800 开始)

**ComfyUI 使用**:

对于 ≥2-step:
```
SDXL Base → LoRA Loader (Hyper-SDXL-Nstep-lora.safetensors)
KSampler:
├── sampler: euler
├── scheduler: sgm_uniform  
├── steps: N (匹配 LoRA 步数)
├── cfg: 1.0
└── denoise: 1.0
```

对于 1-step:
```
⚠️ 需要安装 ComfyUI-HyperSDXL1StepUnetScheduler 自定义节点
该节点将起始 timestep 从 999 改为 800
```

**与 SDXL-Lightning 对比**:
| 维度 | SDXL-Lightning | Hyper-SD |
|------|---------------|----------|
| 1-step CLIP Score | 基准 | **+0.68** |
| 1-step Aes Score | 基准 | **+0.51** |
| 模型覆盖 | SDXL | SD1.5/SDXL/SD3/**Flux** |
| 训练方法 | Progressive+Adversarial | TSCD+Score Distillation |
| 社区评价 | 4-step 很强 | 8-step 和 1-step 更强 |

### 6.2 SANA-Sprint (NVIDIA, ICCV 2025)

**最新前沿**: 将一致性蒸馏和对抗蒸馏结合到极致

**方法**:
- 基于 SANA 模型 (NVIDIA 的高效 DiT)
- **sCM** (continuous-time Consistency Model) + **LADD** 混合蒸馏
- Dense time embeddings 提高知识迁移效率

**结果**:
- 1024×1024 图像: **1 步 0.03 秒** (A100)
- 比 Flux Schnell 快 **64x**
- 质量匹配 SDXL 20-step

---

## 7. 视频蒸馏

### 7.1 AnimateLCM (SIGGRAPH Asia 2024)

**解耦一致性学习策略**:
```
传统方式: 直接对视频数据做一致性蒸馏 → 计算量巨大且不稳定

AnimateLCM:
Step 1: 图像一致性蒸馏 (冻结时间层，只蒸馏空间层)
Step 2: 视频一致性蒸馏 (冻结空间层，只蒸馏时间层)
```

**优势**:
- 降低训练成本 (图像数据丰富且便宜)
- 兼容 SD1.5 的 ControlNet 和 LoRA
- 4 步生成动画视频
- CFG_max 设为 1-1.5 即可

**ComfyUI 集成**:
- ComfyUI-AnimateDiff-Evolved 原生支持 AnimateLCM
- 加载 animatelcm motion module → 设置 lcm 参数 → 4 步生成

### 7.2 CausVid (CVPR 2025)

**前沿**: 将双向视频扩散模型蒸馏为**因果自回归**模型

- 基于 Wan 视频模型
- 蒸馏后可以实时流式生成视频
- 不需要看到未来帧 → 因果生成

---

## 8. ComfyUI 快速推理实战汇总

### 8.1 所有方法的 ComfyUI 配置速查

| 方法 | 格式 | sampler | scheduler | steps | cfg | 特殊要求 |
|------|------|---------|-----------|-------|-----|---------|
| LCM-LoRA | LoRA | **lcm** | sgm_uniform/simple | 4-8 | 1.0-2.0 | 极低 CFG |
| SDXL Turbo | Full UNet | euler_a | sgm_uniform | 1-4 | 1.0 | 只支持 512×512 |
| SDXL-Lightning (Full) | Checkpoint | euler | sgm_uniform | 2/4/8 | 1.0 | 步数需匹配 |
| SDXL-Lightning (LoRA) | LoRA | euler | sgm_uniform | 2/4/8 | 1.0 | 步数需匹配 |
| Hyper-SD (≥2 step) | LoRA | euler | sgm_uniform | 1/2/4/8 | 1.0 | 步数需匹配 |
| Hyper-SD (1-step) | LoRA+UNet | euler | custom | 1 | 1.0 | 需自定义 scheduler 节点 |
| Flux Schnell | Checkpoint | euler | simple | 1-4 | 1.0 | FluxGuidance 不需要 |
| Flux Dev | Checkpoint | euler | simple | 20-28 | 1.0 | FluxGuidance 3.5 |
| PCM | LoRA | — | — | 2-16 | 1.0-7.5 | 支持灵活 CFG |
| AnimateLCM | Motion Module | lcm | sgm_uniform | 4-8 | 1.0-1.5 | 需 AnimateDiff-Evolved |

### 8.2 关键差异: CFG 行为

| 类别 | CFG 行为 | 原因 |
|------|---------|------|
| LCM / SDXL Turbo / Lightning | **CFG ≈ 1** | CFG 已在蒸馏中内化 |
| PCM | **CFG 自由** (1-7.5) | 分段设计解耦了 CFG |
| Flux Dev | **CFG = 1** | Guidance Distillation 内化 |
| Flux Schnell | **CFG = 1** | LADD 内化 |
| 普通 SD/SDXL | CFG 7-12 | 无蒸馏，需要显式 CFG |

### 8.3 方法选择决策树

```
需要快速推理?
├── 基础模型是什么?
│   ├── SD 1.5
│   │   ├── 需要 LoRA/ControlNet 兼容 → LCM-LoRA (4 步)
│   │   └── 最高质量 → Hyper-SD 1.5 (4/8 步)
│   ├── SDXL
│   │   ├── 1 步实时 → Hyper-SD 1-step (需自定义节点)
│   │   ├── 2-4 步高质量 → SDXL-Lightning 4-step
│   │   ├── 需要灵活 CFG/neg prompt → PCM
│   │   └── 需要与 fine-tune 模型兼容 → LCM-LoRA / Lightning LoRA
│   ├── Flux
│   │   ├── 最快 (1-4步) → Flux.1 Schnell
│   │   ├── 高质量 (20步+) → Flux.1 Dev
│   │   └── 折中 (8步) → Hyper-SD Flux LoRA
│   └── 视频
│       ├── SD 基础动画 → AnimateLCM (4步)
│       └── 高质量视频 → 用 API (Kling/Seedance)
└── 不需要 → 正常采样 (DPM++ 2M Karras, 20-30步)
```

---

## 9. 蒸馏方法深度对比

### 9.1 学术指标对比 (SDXL 蒸馏)

| 方法 | 步数 | FID↓ | CLIP Score↑ | Aes Score↑ | 训练成本 |
|------|------|------|------------|-----------|---------|
| SDXL (教师) | 50 | — | 基准 | 基准 | — |
| LCM-LoRA SDXL | 4 | ~22 | 中等 | 中等 | 低 |
| SDXL Turbo | 1 | ~23 | 低 | 中低 | 高 |
| SDXL-Lightning | 4 | ~15 | 高 | 高 | 中 |
| Hyper-SDXL | 1 | — | **最高** | **最高** | 高 |
| DMD2 SDXL | 1 | **8.35** | 高 | 高 | 高 |

### 9.2 实用维度对比

| 维度 | LCM-LoRA | Lightning | Hyper-SD | Turbo | PCM |
|------|----------|-----------|----------|-------|-----|
| 部署难度 | ⭐ 极简 | ⭐⭐ 简单 | ⭐⭐ 简单 | ⭐⭐⭐ 中等 | ⭐⭐ 简单 |
| 与 LoRA 兼容 | ✅ | ✅ (LoRA版) | ✅ (LoRA版) | ❌ | ✅ |
| 与 ControlNet 兼容 | ✅ | ✅ | ✅ | ⚠️ 有限 | ✅ |
| Negative Prompt | ⚠️ 弱 | ⚠️ 弱 | ⚠️ 弱 | ❌ | ✅ |
| 灵活步数 | 4-8 | 固定 N | 固定 N | 1-4 | 2-16 |
| 分辨率 | 模型限制 | 1024² | 1024² | **512²** | 模型限制 |

---

## 10. Flux 快速推理特殊说明

### 10.1 Flux.1 Dev: Guidance Distillation

**机制**: 将 CFG 的 guidance scale 作为**模型输入**而非推理时计算

```
传统 CFG: 
  ε_guided = ε_uncond + w × (ε_cond - ε_uncond)
  每步需要两次 forward (条件 + 无条件) → 2x 成本

Guidance Distillation (Flux Dev):
  ε_guided = F_θ(x_t, t, c, w)  
  w 作为模型的一个输入参数
  单次 forward 即可 → 1x 成本
```

**ComfyUI 中的 FluxGuidance 节点**: 就是设置这个 w 值 (推荐 3.5)

### 10.2 Flux.1 Schnell: LADD

- 从 Flux.1 Dev 出发，用 LADD 进一步蒸馏到 1-4 步
- Apache 2.0 许可，可商用
- **不需要 FluxGuidance 节点** (w 已内化)
- 使用 `euler` sampler + `simple` scheduler + 4 steps

### 10.3 FLUX.2 Klein: 架构蒸馏

- 不仅蒸馏知识，还**缩小架构** (12B → 4B/9B)
- 保留 Flux 能力但推理更快
- 2026 年最新趋势: 架构蒸馏 + 步数蒸馏组合

---

## 11. 实验记录

### 实验 #53: 快速推理概念信息图

**目标**: 生成一张快速推理蒸馏技术的概念信息图

使用 RunningHub API rhart-image-n-pro/text-to-image 生成概念图，展示四大蒸馏家族及其关系。

---

## 12. 总结与关键洞察

### 12.1 蒸馏技术的演进趋势

1. **Pixel → Latent**: ADD → LADD，蒸馏空间从像素迁移到潜空间
2. **固定步数 → 灵活步数**: LCM 固定 → PCM 分段 → 任意步数
3. **单一范式 → 混合范式**: Hyper-SD 和 SANA-Sprint 组合多种蒸馏
4. **图像 → 视频**: AnimateLCM → CausVid，蒸馏扩展到视频领域
5. **知识蒸馏 → 架构蒸馏**: Flux.2 Klein 同时缩小模型和步数

### 12.2 实用选择建议

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 最简即用，4步好图 | SDXL-Lightning 4-step | 社区成熟，质量稳定 |
| 最高质量单步 | Hyper-SDXL 1-step | SOTA 单步质量 |
| 最佳 Flux 体验 | Flux Schnell (4 步) | 原生蒸馏，Apache 2.0 |
| 需要 ControlNet 兼容 | LCM-LoRA + any model | 即插即用 |
| 需要 negative prompt | PCM | 唯一支持灵活 CFG 的蒸馏方法 |
| 视频快速生成 | AnimateLCM | SD1.5 基础，4 步视频 |
| 极致速度 (学术) | SANA-Sprint | 0.03s / 1024² |

### 12.3 与之前学习的连接

- **Day 2 (采样器)**: 蒸馏模型需要特殊采样器 (lcm/euler) 而非 DPM++
- **Day 7 (LoRA)**: LCM-LoRA 和 Lightning LoRA 是 LoRA 的新用法
- **Day 13 (AnimateDiff)**: AnimateLCM 是 AnimateDiff 的加速版本
- **Day 15 (Flux)**: Flux Dev/Schnell 分别用 Guidance/LADD 蒸馏
- **Day 19 (性能优化)**: 蒸馏 + TensorRT + 量化可以叠加使用
- **Day 29 (Flux 实战)**: Flux Schnell 工作流直接使用 LADD 蒸馏成果
