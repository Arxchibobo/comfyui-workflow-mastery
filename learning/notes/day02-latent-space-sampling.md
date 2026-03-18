# Day 02: Latent Space & Sampling 深入

> 学习日期: 2026-03-18 | 状态: 进行中

---

## 一、Latent Space 操作原理

### 1.1 Stable Diffusion 中的两个潜空间

SD 有**两个不同的潜空间**，可以分别操作：

```
1. 图像潜空间 (Image Latent Space)
   - 由 VAE Encoder 编码得到
   - 形状: [B, 4, H/8, W/8]（SD 1.5/SDXL, f=8）
   - 例如 512x512 图像 → [1, 4, 64, 64] 潜变量
   - 这是扩散过程真正操作的空间

2. 文本/条件潜空间 (Text Embedding Space)  
   - 由 CLIP / T5 文本编码器生成
   - SD 1.5: [1, 77, 768]（CLIP ViT-L/14）
   - SDXL: [1, 77, 2048]（双 CLIP）
   - SD3: [1, 77, 4096]（CLIP + T5-XXL）
   - 通过 Cross-Attention 引导去噪方向
```

**关键理解**：两个空间可以独立操作。图像插值和文本插值产生不同的效果。

### 1.2 Latent Space 的连续性

高质量的潜空间具备两个重要性质：

**连续性 (Continuity)**：
- 潜空间中距离相近的点 → 解码后的图像也相似
- 微小移动 → 微小视觉变化
- 数学保证：VAE 的 KL 正则化使潜空间接近标准正态分布，确保平滑

**插值性 (Interpolation)**：
- 任意两点 A、B 之间的路径上，每个中间点都是有效图像
- 这不是所有模型都能保证的——VAE/Diffusion 的训练使其特别好

### 1.3 三种核心操作

#### 操作一：潜空间插值 (Interpolation)

在两个潜变量之间创建平滑过渡，用于动画、变形等。

**线性插值 (LERP)**：
```python
# z_interp = (1-t) * z_A + t * z_B,  t ∈ [0, 1]
def lerp(z_A, z_B, t):
    return (1 - t) * z_A + t * z_B
```

**球面线性插值 (SLERP)**：
```python
# 在高维球面上沿大弧插值
def slerp(z_A, z_B, t):
    # 归一化
    z_A_norm = z_A / torch.norm(z_A)
    z_B_norm = z_B / torch.norm(z_B)
    # 计算夹角
    omega = torch.acos(torch.clamp(torch.dot(z_A_norm.flatten(), z_B_norm.flatten()), -1, 1))
    # 球面插值
    return (torch.sin((1-t) * omega) / torch.sin(omega)) * z_A + \
           (torch.sin(t * omega) / torch.sin(omega)) * z_B
```

**SLERP vs LERP — 为什么 SLERP 更好？**

这是一个非常重要的概念：

```
高斯分布的样本集中在"壳"（shell）上：
- N 维标准正态分布的样本，其范数集中在 √N 附近
- 例如 [4, 64, 64] = 16384 维 → 范数 ≈ √16384 ≈ 128

LERP 的问题 — "帐篷效应" (Tent-pole Effect)：
- LERP 的中间点穿过球心
- 中点 (t=0.5) 的范数 ≈ |z_A + z_B|/2，通常远小于 √N
- 这个范数的点"远离数据流形"，产生模糊/不自然的图像

SLERP 的优势：
- 沿着球面的大弧走，所有中间点范数保持 ≈ √N
- 每个中间点都在"数据壳"上 → 更自然、更清晰

直觉类比：
  地球表面两城市之间——
  LERP = 穿过地心的直线（路过岩浆）
  SLERP = 沿地表走的大圆航线（始终在地面）
```

视觉效果差异：
| 插值方法 | 中间帧质量 | 过渡平滑度 | 范数一致性 |
|---------|----------|----------|----------|
| LERP | 中点可能模糊 | 中等 | 中点范数下降 |
| SLERP | 全程清晰 | 优秀 | 保持恒定 |

**实践建议**：扩散模型的 latent 插值**始终使用 SLERP**。

#### 操作二：潜空间算术 (Arithmetic)

类似 Word2Vec 的 "king - man + woman = queen"，潜空间也支持语义算术：

```
概念加减法（在 text embedding 空间）：
  "微笑女人" - "女人" + "男人" ≈ "微笑男人"
  
实现方式：
  e_smile_woman = CLIP("a smiling woman")
  e_woman = CLIP("a woman")  
  e_man = CLIP("a man")
  e_smile_man = e_smile_woman - e_woman + e_man

在图像潜空间也可以：
  z_result = z_source - z_attribute_A + z_attribute_B
```

这种算术之所以有效，是因为：
1. VAE 将语义相似的图像编码到相近的区域
2. 特定属性（如"微笑"）在潜空间中对应一个近似线性的方向
3. 沿该方向移动 ≈ 添加/移除该属性

**局限性**：
- 不是所有属性都是线性的
- 复杂变化（如年龄变化）可能需要非线性操作
- 效果取决于 VAE/CLIP 训练质量

#### 操作三：潜空间编辑 (Editing)

通过在去噪过程中修改潜变量来编辑生成的图像：

**DDIM Inversion（反转）**：
```
给定一张生成的图像 x，可以"反推"出生成它的噪声 z_T：
  x → VAE Encode → z_0 → DDIM 反向加噪 → z_T

然后修改条件（换 prompt），从同一个 z_T 重新去噪：
  z_T + 新 prompt → DDIM 去噪 → z_0 → VAE Decode → 编辑后的图像

保留了原图的结构布局，但改变了语义内容
```

**Prompt-to-Prompt Editing**：
```
在去噪过程中，操纵 Cross-Attention map：
  - 替换某个词 → 只改变该词对应区域的 attention
  - 权重调节 → 增强/减弱某个概念的影响
  - 精确控制哪些区域被修改，哪些保持不变
```

### 1.4 ComfyUI 中的 Latent 操作节点

ComfyUI 提供了原生节点来操作潜空间：

| 节点名 | 功能 | 对应操作 |
|--------|------|---------|
| `EmptyLatentImage` | 创建全零/随机潜变量 | 初始化 z_T |
| `LatentComposite` | 将一个 latent 粘贴到另一个上 | 区域合成 |
| `LatentBlend` | 按 blend_factor 混合两个 latent | 插值/混合 |
| `LatentCrop` | 裁剪 latent 区域 | 局部操作 |
| `LatentUpscale` | 放大潜变量（双线性/最近邻） | 分辨率调整 |
| `LatentFlip` | 翻转潜变量 | 镜像 |
| `LatentRotate` | 旋转潜变量 | 旋转变换 |
| `SetLatentNoiseMask` | 设置噪声掩码 | Inpainting 控制 |
| `LatentBatch` | 将多个 latent 合并为 batch | 批量处理 |

**`LatentComposite` 详细说明**：
```
功能：将 samples_from（源）粘贴到 samples_to（目标）的指定位置
参数：
  - x, y: 粘贴位置（像素坐标，自动转换为 latent 坐标 /8）
  - feather: 边缘羽化像素数（平滑过渡）

用途：
  - 区域组合：不同区域用不同 prompt 生成
  - 渐变融合：利用 feather 实现平滑拼接
  - 多主体合成：不同主体在不同 latent 区域生成后合并
```

**`LatentBlend` 详细说明**：
```
功能：z_out = (1 - factor) * z_1 + factor * z_2
参数：
  - blend_factor: 0.0（全部 z_1）到 1.0（全部 z_2）
  - blend_mode: 通常是线性混合

用途：
  - 风格混合：factor=0.5 → 两种风格各半
  - 渐变动画：factor 从 0 到 1 递增 → 变形动画
  - 概念融合：混合不同生成结果
  
注意：这是 LERP 而非 SLERP，实际效果可能在 factor=0.5 时略有退化
```

### 1.5 实际应用场景

**1. 变形动画 (Morphing Animation)**：
```
工作流：
  prompt_A + seed → z_A（通过 KSampler 部分去噪停在 z_0）
  prompt_B + seed → z_B
  for t in [0, 0.05, 0.1, ..., 1.0]:
      z_interp = slerp(z_A, z_B, t)
      frame = VAEDecode(z_interp)
  → 拼接成视频
```

**2. 概念空间探索 (Concept Exploration)**：
```
在 text embedding 空间做 2D 网格插值：
  四角 prompt → 4 个 embedding
  双线性插值填充网格
  → 生成 N×N 的概念地图
```

**3. Seed Walking**：
```
固定 prompt，连续改变 seed 的某个维度：
  noise[i, j, k] += delta
  → 观察生成图像的局部变化
  → 理解潜空间的各维度语义
```

**4. Circular Walk（环形漫游）**：
```
在潜空间中画一个圆形路径：
  z(θ) = r · [cos(θ) · z_A + sin(θ) · z_B]
  θ 从 0 到 2π
  → 生成无缝循环动画

为什么用圆形？
  - 保持范数恒定（始终在数据壳上）
  - 起点=终点，适合 GIF 循环
  - 两个正交基向量定义圆所在的2D平面
```

---

## 二、Sampling 算法数学细节：ODE vs SDE 统一框架

### 2.1 核心思想：扩散过程的连续时间形式

Song et al. (2021) 的 Score-based SDE 框架将所有扩散模型统一为连续时间随机微分方程。

**前向 SDE（加噪过程）**：
```
dx = f(x, t) dt + g(t) dw

其中：
  x ∈ ℝ^D — 数据（或潜变量）
  f(x, t) — 漂移系数 (drift)，控制确定性变化
  g(t) — 扩散系数 (diffusion)，控制噪声注入量  
  w — 标准维纳过程 (Wiener process / Brownian motion)
  t ∈ [0, T]，从 t=0（干净数据）到 t=T（纯噪声）
```

**两种经典参数化**：

| 名称 | f(x,t) | g(t) | 转移核 q(x_t\|x_0) |
|------|--------|------|---------------------|
| VP-SDE (Variance Preserving) | -½β(t)x | √β(t) | N(α_t x_0, σ_t² I) |
| VE-SDE (Variance Exploding) | 0 | √(dσ²/dt) | N(x_0, σ_t² I) |

其中 VP-SDE 对应 DDPM/SD，有 α_t² + σ_t² ≈ 1（方差守恒）。

### 2.2 反向 SDE（去噪采样）

**Anderson 定理 (1982)**：前向 SDE 的时间反转也是一个 SDE：

```
dx = [f(x,t) - g(t)² ∇_x log p_t(x)] dt̄ + g(t) dw̄

其中：
  dt̄ — 反向时间微元（从 T 到 0）
  dw̄ — 反向维纳过程
  ∇_x log p_t(x) — Score Function（分数函数），即 t 时刻数据分布的对数梯度
```

**核心洞察**：去噪的关键是 **Score Function** ∇_x log p_t(x)。
- 它指向"数据密度增加最快的方向"
- 可以用去噪网络来近似：∇_x log p_t(x) ≈ -ε_θ(x_t, t) / σ_t

### 2.3 Probability Flow ODE（确定性采样）

Song et al. 证明了一个关键结果：存在一个 **确定性 ODE**，其解的边际分布与反向 SDE 相同：

```
Probability Flow ODE:
  dx/dt = f(x,t) - ½ g(t)² ∇_x log p_t(x)

对比反向 SDE:
  dx = [f(x,t) - g(t)² ∇_x log p_t(x)] dt̄ + g(t) dw̄
                    ↑                              ↑
              系数变为 ½                       去掉噪声项
```

**为什么这很重要？**
```
反向 SDE (随机路径):
  z_T ─── 随机漂移+扩散 ──→ x_0
  • 每次采样路径不同（即使相同初始噪声）
  • 需要更多步骤才能收敛
  • 多样性更好（额外的随机性探索更多模式）
  
PF-ODE (确定性路径):
  z_T ─── 确定性漂移 ──→ x_0
  • 相同初始噪声 → 完全相同的输出
  • 可以用高阶 ODE solver 加速（10-20步）
  • 支持精确的编码/解码（DDIM Inversion）
  • 支持 latent 操作（插值有意义）
```

**数学直觉**：
- SDE 的去噪 = "一边去噪一边加小噪声"，像退火 (annealing)
- ODE 的去噪 = "沿着概率流的梯度场直接滑向目标"
- 两者的**边际分布**（即采样的统计特性）完全相同
- 但 **单条路径**不同：ODE 是唯一确定的，SDE 有无穷多条

### 2.4 收敛性分析

**一阶方法的局部截断误差 (LTE)**：

以 Euler 方法为例，离散化 PF-ODE：
```
x_{t-Δt} = x_t + Δt · v(x_t, t)     # v 是 ODE 的速度场

LTE = O(Δt²)   # 一阶方法
GTE = O(Δt)    # 全局截断误差
```

**高阶方法的误差**：
```
方法         | 阶数 | LTE        | 每步 NFE | 总 NFE (固定精度)
------------|------|-----------|---------|------------------
Euler       | 1    | O(Δt²)   | 1       | N
Heun (改进Euler) | 2 | O(Δt³) | 2       | ~√N
DPM-Solver-2 | 2  | O(Δt³)   | 1*      | ~√N
DPM-Solver-3 | 3  | O(Δt⁴)   | 1*      | ~N^(1/3)
DPM++ 2M    | 2   | O(Δt³)   | 1       | ~√N

* DPM-Solver 的 "1 NFE/步" 是多步法的优势：复用历史评估值
```

**关键发现**（DPM-Solver++论文）：

高阶方法在 **有 guidance** 时会不稳定：
```
CFG scale s 的影响：
  guided noise prediction: ε̃_θ = (1+s) · ε_θ(x_t, c) - s · ε_θ(x_t, ∅)
  
  大 s → ε̃_θ 的值域远超训练时的 [-1, 1]
  → ODE 的速度场变得"尖锐"（Lipschitz 常数大）
  → 高阶展开的高次项爆炸
  → 收敛半径急剧缩小
```

**DPM-Solver++ 的解决方案**：
1. 使用 **data prediction** 参数化（而非 noise prediction）
   - x_θ(x_t, t) = (x_t - σ_t ε_θ) / α_t
   - 这让预测值有界（在数据范围内），不像 ε 会爆
2. 用 **multistep** 而非 singlestep（减小有效步长）
3. 加 **dynamic thresholding**（截断异常值）

---

## 三、Euler / DPM++ 2M / DDIM 数学推导对比

### 3.1 统一的数学框架

所有采样器都是在求解同一个 ODE（或 SDE），区别仅在**离散化方法**。

**引入 log-SNR 时间变量**：
```
定义 λ_t = log(α_t / σ_t)  — 对数信噪比

ODE 的变量替换 (Change of Variables):
  原始: dx/dt = f(x,t) - ½g(t)² · score
  换元后: 
    x_λ = (α_λ/α_s) · x_s - α_λ ∫_{λ_s}^{λ} e^{-λ} · ε_θ(x̂_λ, λ) dλ     (noise param)
    x_λ = (σ_λ/σ_s) · x_s - σ_λ ∫_{λ_s}^{λ} e^{λ} · x_θ(x̂_λ, λ) dλ      (data param)
```

Lu et al. 引入的这个**精确解公式**是 DPM-Solver 系列的基础。所有采样器的差异归结为如何近似积分项。

### 3.2 DDIM — 一阶 ODE Solver

**推导**：

DDIM (Song et al. 2021a) 原始是从非马尔可夫角度推导的，但 Lu et al. 证明它等价于对 PF-ODE 的一阶 Euler 离散化。

```
从精确解出发（noise prediction 参数化）：
  x_t = (α_t/α_s) · x_s - α_t · (e^{-(λ_t - λ_s)} - 1) · ε_θ(x_s, s)
  
令 h = λ_t - λ_s (时间步长)，一阶近似 ∫ ε_θ ≈ ε_θ(x_s, s) · h：

  x_t = (α_t/α_s) · x_s - σ_t · (e^h - 1) · ε_θ(x_s, s)

展开 α_t/α_s 和 σ_t 的关系，写成更熟悉的形式：

DDIM 更新公式：
  x_{t-1} = α_{t-1} · [(x_t - σ_t · ε_θ(x_t, t)) / α_t]  +  σ_{t-1} · ε_θ(x_t, t)
           = α_{t-1} · x̂_0(x_t, t)  +  σ_{t-1} · ε_θ(x_t, t)
                ↑ "predicted x_0"           ↑ "predicted noise direction"
```

**直觉理解**：
- DDIM 每步先"预测干净图像 x̂_0"，再"从 x̂_0 出发加上 t-1 时刻应有的噪声"
- 这就是为什么 DDIM 可以跳步（不用每步都走，可以 [1000, 800, 600, ...]）

**η 参数**（DDIM 的随机版本）：
```
x_{t-1} = α_{t-1} · x̂_0 + √(σ²_{t-1} - η²σ̃²) · ε_θ + η · σ̃ · ε_random

  η = 0 → 纯确定性（ODE），DDIM
  η = 1 → DDPM（完整马尔可夫链）
  0 < η < 1 → 介于两者之间
```

### 3.3 Euler — 最朴素的一阶求解器

**推导**：

直接对 ODE 的 dx/dt = v(x,t) 做前向 Euler：
```
x_{t+Δt} = x_t + Δt · v(x_t, t)

对于扩散 ODE，v(x,t) 需要计算。
在 k-diffusion 框架（Karras et al. 2022 EDM）中，参数化为：
  
  dx/dσ = (x - D(x; σ)) / σ

  其中 D(x; σ) 是 denoiser（去噪器），σ 是噪声级别
  
Euler 更新：
  x_{σ_{i+1}} = x_{σ_i} + (σ_{i+1} - σ_i) · (x_{σ_i} - D(x_{σ_i}; σ_i)) / σ_i
```

**Euler vs DDIM 本质相同**：
```
在同一参数化下，DDIM 和 Euler 是等价的（只是记号不同）。
区别在于"时间刻度"：
  - DDIM 用 timestep (t) 或 α_t / σ_t 的函数
  - Euler (k-diffusion) 直接用 σ 做变量
  
实质上 DDIM 就是 PF-ODE 的 Euler 方法
```

### 3.4 Heun（改进 Euler / 二阶 Runge-Kutta）

```
Step 1 (预测): x̃ = x_t + Δt · v(x_t, t)           # Euler 预测
Step 2 (校正): x_{t+Δt} = x_t + Δt/2 · [v(x_t, t) + v(x̃, t+Δt)]  # 取平均

  → 用两次模型评估（NFE=2/步），获得二阶精度
  → 相当于梯形法 (Trapezoidal Rule)
```

**Heun 的问题**：每步需要**两次**网络前向传播，总 NFE 翻倍。

### 3.5 DPM-Solver 与 DPM++ 2M — 高阶多步求解器

**核心创新**：利用**指数积分器 (Exponential Integrator)** + **多步法 (Multistep)**

**Step 1: 精确解的半线性分离**

扩散 ODE 不是一般 ODE，它有特殊结构——**半线性 (Semi-linear)**：
```
dx/dλ = linear(x) + nonlinear(x, λ)

其中 linear 部分可以精确求解（指数衰减/增长），
只需要近似 nonlinear 部分的积分。
```

这就是为什么 DPM-Solver 比通用 ODE solver (RK4等) 更高效的原因。

**Step 2: DPM-Solver（noise prediction, singlestep）**

一阶（= DDIM）：
```
x_t = (α_t/α_s) · x_s - σ_t · (e^h - 1) · ε_θ(x_s, s)
```

二阶（利用中间点 s₁）：
```
需要一次额外的半步评估 ε_θ(u_s₁, s₁)
  u_s₁ = 一阶预测的中间值
  
x_t = 一阶结果 + 二阶修正项（利用 ε_θ 的一阶 Taylor 展开）
```

**Step 3: DPM-Solver++（data prediction, multistep）**

**关键改进 1：参数化**
```
DPM-Solver: 对 ε_θ(x, λ) 做 Taylor 展开
DPM-Solver++: 对 x_θ(x, λ) 做 Taylor 展开

为什么 data prediction 更好？
  • ε_θ 在 guided sampling 时值域不受限（可能 >> 1）
  • x_θ 是对原始数据的预测，值域在 [-1, 1]
  • Taylor 展开对有界函数更稳定
```

**关键改进 2：多步法**
```
Singlestep (如 DPM-Solver-2): 
  每步内部需要额外的中间评估
  → 虽然阶数高，但每步 NFE > 1
  → 且对 guided sampling 不稳定

Multistep (如 DPM++ 2M):
  复用之前步骤的模型输出
  → 每步只需 1 次 NFE
  → 用历史信息做高阶插值
  → 对 guided sampling 更稳定（有效步长更小）
```

**DPM++ 2M 的具体公式**：
```
给定步骤 s → t (λ_s → λ_t)，以及前一步的 x_θ(x_{s'}, s'):

令 h = λ_t - λ_s (当前步长)
    h_prev = λ_s - λ_{s'} (上一步长)  
    r = h_prev / h

二阶多步更新：
  D_θ^(1) = (1 + 1/(2r)) · x_θ(x_s, s) - 1/(2r) · x_θ(x_{s'}, s')
                ↑ 用线性外推估计 x_θ 在当前步的值
  
  x_t = (σ_t/σ_s) · x_s - α_t · (e^{-h} - 1) · D_θ^(1)

第一步没有历史值时，退化为一阶（= DDIM）。
```

**直觉理解**：
- 一阶方法假设 "速度场在步内恒定"
- DPM++ 2M 假设 "速度场在步内线性变化"，用前一步的数据外推斜率
- 这使得误差从 O(h²) 降到 O(h³)

### 3.6 三种方法的系统对比

```
                    DDIM/Euler      Heun         DPM++ 2M
─────────────────────────────────────────────────────────────
阶数                 1              2            2
NFE/步               1              2            1*
局部截断误差          O(h²)         O(h³)        O(h³)
全局误差              O(h)          O(h²)        O(h²)
10 步 NFE 总量       10             20           10
内存开销              ε_θ 缓存×1    ε_θ 缓存×2   ε_θ 缓存×2 (历史)
Guided Sampling 稳定  ✅             ⚠️           ✅
确定性                ✅             ✅            ✅
首步行为              正常           正常         退化为一阶

* 第一步需 2 NFE（无历史），之后每步 1 NFE
```

**实践指南**（来自论文和社区经验）：
```
场景                          推荐方法          步数
──────────────────────────────────────────────────
快速预览                      Euler             8-12
日常出图（有 CFG）            DPM++ 2M Karras   20-25
高质量出图                    DPM++ 2M Karras   25-35
写实人像                      DPM++ SDE Karras  25-30
需要多样性                    Euler a / SDE 变体  20-30
调试/对比实验                 Euler              20
高 CFG (>12)                  DPM++ 2M Karras    30+
```

---

## 四、Noise Schedule 设计

### 4.1 为什么 Noise Schedule 重要？

Noise schedule 定义了**在时间维度上如何分配噪声级别**。它直接影响：
- 训练效率（模型在哪些噪声级别学习最多）
- 采样质量（离散化误差的分布）
- 收敛速度

### 4.2 三种主要的 Noise Schedule

#### Linear Schedule (DDPM, Ho et al. 2020)

```
β_t = β_min + t/(T-1) · (β_max - β_min)

原始 DDPM 设定：
  β_min = 0.0001, β_max = 0.02, T = 1000

α̅_t = ∏_{i=1}^{t} (1 - β_i)    # 累积信号保留率

特点：
  - β 线性增长 → 前期噪声增加慢，后期增加快
  - α̅_t 的衰减不均匀：前 ~600 步还有大量信号，后 ~400 步急剧下降
  - SNR 在时间轴上分布不均匀
```

**问题**：
```
Linear schedule 的两大缺陷：
1. 尾端浪费：最后几百步几乎是纯噪声，信息量极低
2. 分辨率依赖：对高分辨率图像，同样的 β 意味着更快的信号衰减
   （因为信号功率 ∝ D，但噪声功率同样 ∝ D，但高分辨率的有效 SNR 不同）
```

#### Cosine Schedule (Improved DDPM, Nichol & Dhariwal 2021)

```
α̅_t = cos²(π/2 · (t/T + s) / (1 + s))

其中 s = 0.008 是一个小偏移，防止 α̅_0 ≠ 1

对应的 β_t = 1 - α̅_t / α̅_{t-1}（被 clip 到 0.999 以下）

设计思路：
  直接设计 α̅_t 的衰减曲线，而不是 β_t
  cos² 曲线提供了：
  - 中间平缓的过渡（大部分时间步在 "中等噪声" 区域）
  - 两端较快的变化
  
log(SNR) 沿时间近似线性下降 → 采样时间步的利用效率更高
```

**优势**：
```
vs Linear:
  - 更均匀的信噪比分布
  - 减少了"浪费的步数"
  - 高分辨率时也能保持有效
  - 实际效果：同样步数下生成质量明显提升
```

#### Karras Schedule (EDM, Karras et al. 2022)

```
Karras 不用 α_t/β_t 框架，而是直接在 σ 空间设计：

σ_i = (σ_max^(1/ρ) + i/(N-1) · (σ_min^(1/ρ) - σ_max^(1/ρ)))^ρ

  σ_min = 0.002（最小噪声）
  σ_max = 80（最大噪声）
  ρ = 7（控制间距分布的超参数）
  N = 采样步数
  i = 0, 1, ..., N-1

设计原理：
  在 σ^(1/ρ) 空间均匀采样，然后映射回 σ 空间
  
  ρ > 1 → 在低噪声端（σ 小）分配更多时间步
         → 在高噪声端（σ 大）分配较少时间步
  
  ρ = 7 是经过大量实验得到的最优值
```

**为什么 Karras schedule 更好？**
```
核心洞察（EDM 论文的发现）：

1. ODE 的局部截断误差与 dx/dσ 的大小成正比
2. dx/dσ 在低噪声时（σ 小）变化更剧烈
3. 因此低噪声区域需要更密的时间步

Karras schedule 正是这样做的：
  σ_max=80 → σ=5 可能只占 3-4 步
  σ=5 → σ=0.002 占剩余 16-17 步（以 N=20 为例）

对比：
  Uniform in σ: 高噪声浪费步数，低噪声精度不足
  Uniform in log(σ): 较好但非最优
  Karras (ρ=7): 最优分配，最小化总截断误差
```

### 4.3 Noise Schedule 在 ComfyUI 中的体现

ComfyUI 的 KSampler 中：
```
scheduler 参数选项：
  "normal"  — 均匀在 timestep 空间（类似 linear）
  "karras"  — Karras σ schedule
  "exponential" — σ 在对数空间均匀
  "sgm_uniform" — SGM 风格均匀
  "simple"  — 简单线性
  "ddim_uniform" — DDIM 原始均匀

实践经验：
  - 大多数场景 "karras" 最优
  - "normal" 是默认值但非最佳
  - "exponential" 对某些模型效果好
  - SDXL + DPM++ 2M + karras 是社区公认的黄金组合
```

### 4.4 三种 Schedule 的数学对比

```
                Linear         Cosine          Karras
─────────────────────────────────────────────────────────
设计变量        β_t            α̅_t            σ_i
核心函数        线性 β         cos² 衰减       σ^(1/ρ) 均匀
logSNR 分布     不均匀         近似均匀        低噪声密集
步数利用率      低             中              高
高CFG稳定性     差             中              好
适用模型        SD 1.x         iDDPM          SD/SDXL/EDM
时间步分布      均匀           中间密          低噪声密
```

---

## 五、本节小结：采样算法的统一视角

```
                      Score-based SDE 框架
                            │
                 ┌──────────┼──────────┐
                 │                     │
            反向 SDE                PF-ODE
         (随机采样)              (确定性采样)
           │                        │
      SDE 离散化             ODE 离散化
           │                  ┌─────┼─────┐
           │                  │     │     │
         DDPM              一阶   二阶   多步
      ancestral        (DDIM/  (Heun/ (DPM++
      sampling          Euler)  DPM-2) 2M/3M)
                                          │
                                    Noise Schedule
                                  ┌───┼───┐
                                  │   │   │
                               linear cosine karras
```

**最终决策树（ComfyUI 用户实用版）**：
```
开始
 ├─ 需要可复现? → ODE 方法
 │    ├─ 快速预览? → Euler + karras, 8-12 步
 │    ├─ 日常出图? → DPM++ 2M + karras, 20-25 步
 │    └─ 极致质量? → DPM++ 2M + karras, 30+ 步
 └─ 需要多样性? → SDE 方法
      ├─ Euler ancestral, 20-30 步
      └─ DPM++ SDE + karras, 25-30 步
```

---

## 参考资料

1. [Hugging Face Cookbook: SD Interpolation](https://huggingface.co/learn/cookbook/en/stable_diffusion_interpolation) — 完整代码+动画
2. [Keras: Walk through Latent Space with SD](https://keras.io/examples/generative/random_walks_with_stable_diffusion/) — 文本+图像双空间插值
3. [Smooth Diffusion (CVPR 2024)](https://openaccess.thecvf.com/content/CVPR2024/papers/Guo_Smooth_Diffusion_Crafting_Smooth_Latent_Spaces_in_Diffusion_Models_CVPR_2024_paper.pdf) — 提升潜空间平滑性
4. [Tom White 2016: Sampling Generative Networks](https://arxiv.org/abs/1609.04468) — SLERP 在生成模型中的经典论文
5. [Which Way from B to A (arXiv 2511.12757)](https://arxiv.org/html/2511.12757) — 嵌入几何对插值的影响
6. [ComfyUI Wiki: LatentComposite](https://comfyui-wiki.com/en/comfyui-nodes/latent/latent-composite) — 节点详解
7. [Dev.to: Exploiting Latent Vectors in SD](https://dev.to/ramgendeploy/exploiting-latent-vectors-in-stable-diffusion-interpolation-and-parameters-tuning-j3d) — SLERP 实操
8. [Song et al. 2021: Score-Based Generative Modeling through SDEs](https://arxiv.org/abs/2011.13456) — SDE/ODE 统一框架的奠基论文
9. [Song et al. 2021a: Denoising Diffusion Implicit Models (DDIM)](https://arxiv.org/abs/2010.02502) — DDIM 原始论文
10. [Lu et al. 2022: DPM-Solver](https://arxiv.org/abs/2206.00927) — 快速 ODE 求解器，10 步高质量采样
11. [Lu et al. 2022: DPM-Solver++](https://arxiv.org/abs/2211.01095) — Guided sampling 的高阶快速求解器（含 multistep 变体）
12. [Karras et al. 2022: Elucidating the Design Space (EDM)](https://arxiv.org/abs/2206.00364) — Noise schedule + sampler 统一设计空间
13. [Nichol & Dhariwal 2021: Improved DDPM](https://arxiv.org/abs/2102.09672) — Cosine schedule + 学习方差
14. [Hang et al. 2024: Improved Noise Schedule for Diffusion Training](https://arxiv.org/abs/2407.03297) — logSNR=0 附近密集采样加速训练
15. [Anderson 1982: Reverse-time Diffusion Equations](https://doi.org/10.1016/0304-4149(82)90051-5) — 反向 SDE 的数学基础
16. [Keras DDIM Tutorial](https://keras.io/examples/generative/ddim/) — 清晰的代码实现，连续时间 DDIM
