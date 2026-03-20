# Day 4 — SD1.5 vs SDXL vs Flux 采样器行为差异 & 高级参数调校

> 日期: 2026-03-20 | 学习轮次: 9

---

## 1. 三种架构的根本差异

### 1.1 架构对比总览

| 特性 | SD 1.5 | SDXL | Flux |
|------|--------|------|------|
| **骨干网络** | U-Net (~860M params) | U-Net (~2.6B params) | DiT (Diffusion Transformer, ~12B) |
| **计算主体** | 卷积为主 | 卷积为主 | Attention 为主 |
| **Latent 维度** | 4×64×64 (512px) | 4×128×128 (1024px) | 16×128×128 (1024px) |
| **VAE 压缩比** | 8:1 | 8:1 | 8:1 (但16通道 → 信息量4倍) |
| **训练范式** | DDPM (扩散) | DDPM (扩散) | Rectified Flow (流匹配) |
| **噪声参数化** | ε-prediction (预测噪声) | ε-prediction | v-prediction / flow matching |
| **CFG 使用** | 必需 (7-12) | 必需 (5-9) | **不使用** (guidance_scale=1.0) |
| **推荐步数** | 20-30 | 20-25 | 20-30 |
| **Text Encoder** | CLIP ViT-L/14 | CLIP ViT-L + OpenCLIP ViT-G | CLIP ViT-L + T5-XXL |

### 1.2 Flux 的核心创新：Rectified Flow

**传统扩散模型** (SD1.5/SDXL):
- 训练：学习预测每一步的噪声 ε
- 采样：从纯噪声出发，沿着弯曲的概率路径逐步去噪
- 数学：`x_{t-1} = (x_t - ε_θ(x_t, t) * β_t) / sqrt(α_t)`
- 需要 CFG 做条件引导，因为无条件/有条件路径不同

**Rectified Flow** (Flux):
- 训练：学习从噪声到数据的**直线向量场** v
- 采样：沿着接近直线的路径从噪声走到数据
- 数学：`x_t = (1-t) * x_0 + t * ε`, 预测 `v = x_0 - ε`
- **不需要 CFG**：模型直接学习条件生成，guidance 已经内化
- 更少步数即可收敛（路径更直 → 每步更有效）

**在 ComfyUI 源码中的体现**：
```python
# comfy/model_sampling.py
class CONST:  # Flux 使用的模型采样类
    # sigma 直接等于 t (时间步), 范围 [0, 1]
    # 而非传统扩散的 sigma (噪声标准差)
    
# k_diffusion/sampling.py
def sample_euler_ancestral(model, x, sigmas, ...):
    if isinstance(model.inner_model.inner_model.model_sampling, comfy.model_sampling.CONST):
        return sample_euler_ancestral_RF(...)  # 走 Rectified Flow 分支!
```

关键代码：`sample_euler_ancestral_RF` 中 Euler 步变成了：
```python
sigma_down_i_ratio = sigma_down / sigmas[i]
x = sigma_down_i_ratio * x + (1 - sigma_down_i_ratio) * denoised
# 这是线性插值! 不是传统的 x + d * dt
```

---

## 2. 各架构的最优采样器选择

### 2.1 SD 1.5 最优采样器

| 排名 | 采样器 + Scheduler | 适用场景 | 推荐步数 | 备注 |
|------|-------------------|---------|---------|------|
| 🥇 | dpmpp_2m + karras | **通用首选** | 20-30 | 社区金标准，平衡速度与质量 |
| 🥈 | euler_a + normal | 创意/艺术风格 | 20-30 | 非收敛，每次不同，适合探索 |
| 🥉 | dpmpp_sde + karras | 写实/细节 | 15-25 | SDE 随机性带来自然纹理 |
| 4 | ddim + normal | 稳定/可复现 | 25-50 | 学术基线，适合对比实验 |
| 5 | uni_pc + kl_optimal | 快速生成 | 5-10 | 少步数之王 |

**SD 1.5 特点**：
- 对 CFG 比较敏感，通常用 7-12
- euler_a 在 SD1.5 生态特别流行（anime 风格）
- karras scheduler 几乎是万金油
- 20 步已经能出不错效果，30 步基本收敛

### 2.2 SDXL 最优采样器

| 排名 | 采样器 + Scheduler | 适用场景 | 推荐步数 | 备注 |
|------|-------------------|---------|---------|------|
| 🥇 | dpmpp_2m + karras | **通用首选** | 20-25 | 延续 SD1.5 的地位 |
| 🥈 | dpmpp_2m_sde + karras | 写实摄影 | 20-25 | 随机性+多步精度，细节拉满 |
| 🥉 | dpmpp_sde + karras | 柔和艺术 | 15-20 | SDXL-Turbo 默认采样器 |
| 4 | dpmpp_3m_sde + linear_quadratic | 复杂场景 | 25-35 | 三阶精度，适合大场景 |
| 5 | heunpp2 + karras | 高质量 | 15-20 | 二阶精度，有效步数30-40 |

**SDXL 与 SD1.5 的采样器差异**：
1. **更低的 CFG 需求**：SDXL 用 5-9 (vs SD1.5 的 7-12)，高 CFG 更容易过饱和
2. **euler_a 地位下降**：SDXL 架构更大，DPM++ 系列优势更明显
3. **SDE 采样器更受欢迎**：SDXL 的大模型 + SDE 随机性 = 极好的写实细节
4. **步数需求降低**：20 步通常就够，相比 SD1.5 的 25-30
5. **Refiner 二阶段**：SDXL Refiner 通常用独立采样器配置

### 2.3 Flux 最优采样器

| 排名 | 采样器 + Scheduler | 适用场景 | 推荐步数 | 备注 |
|------|-------------------|---------|---------|------|
| 🥇 | euler + normal | **通用首选** | 20-30 | 最快，Flux 官方推荐 |
| 🥈 | dpmpp_2m + beta | 高质量 | 20-30 | 多步精度更好 |
| 🥉 | euler + beta | prompt 复杂 | 25-35 | beta schedule 对复杂 prompt 更稳 |
| 4 | euler + simple | **快速出图** | 4 (Schnell) | Flux-Schnell 专用 |
| 5 | dpmpp_2m + simple | 快速替代 | 20-25 | 速度和 euler 并列最快 |

**Flux 的采样器选择逻辑完全不同**：

1. **不使用 CFG → cfg_scale 固定 1.0**
   - 传统模型 CFG 公式：`output = uncond + cfg * (cond - uncond)`
   - Flux：不做这个计算，模型直接输出条件结果
   - **后果**：`_cfg_pp` 系列采样器无效！

2. **Scheduler 选择变化大**
   - karras 在 Flux 上**不是最优**（为传统扩散设计）
   - `simple` / `normal` / `beta` 更合适
   - beta scheduler 来自论文 arXiv:2407.12173，专为 flow matching 设计

3. **简单采样器反而更好**
   - Rectified Flow 的路径本身就近似直线
   - 复杂高阶采样器（heun, dpmpp_3m_sde）优势不大，反而浪费算力
   - Euler 一阶方法配直线路径 = 高效准确

4. **社区实测数据**（Reddit 全组合测试）：
   - 速度：DPM++ 2M ≈ Euler >> 其余
   - 质量：Euler + normal ≈ DPM++ 2M + beta > Euler + simple
   - HeunPP2 最慢（2x NFE），质量提升不成比例

---

## 3. Scheduler（噪声调度）深度分析

### 3.1 ComfyUI 中所有 Scheduler 的数学公式

从源码 `comfy/samplers.py` 和 `comfy/k_diffusion/sampling.py` 提取：

#### normal
```python
def normal_scheduler(model_sampling, steps, sgm=False, floor=False):
    # 在时间步空间均匀采样，然后转换为 sigma
    timesteps = torch.linspace(start, end, steps)  # 均匀时间步
    sigs = [model_sampling.sigma(ts) for ts in timesteps]
```
- **原理**：在模型的内部时间步空间（timestep）均匀分布
- 转换到 sigma 后不是均匀的（因为 sigma(t) 通常是非线性映射）
- **最通用**，几乎所有采样器都能用

#### karras
```python
def get_sigmas_karras(n, sigma_min, sigma_max, rho=7.):
    ramp = torch.linspace(0, 1, n)
    min_inv_rho = sigma_min ** (1 / rho)
    max_inv_rho = sigma_max ** (1 / rho)
    sigmas = (max_inv_rho + ramp * (min_inv_rho - max_inv_rho)) ** rho
```
- **原理**：在 σ^(1/ρ) 空间均匀分布，默认 ρ=7
- 效果：**高噪声区域步长更大，低噪声（细节）区域步长更小**
- 来源：Karras et al. (2022) "Elucidating the Design Space"
- **直觉**：像画家先画大笔触（高噪声），再慢慢刻画细节（低噪声）
- **最适合**：DPM++ 系列，尤其是 dpmpp_2m, dpmpp_sde

#### exponential
```python
def get_sigmas_exponential(n, sigma_min, sigma_max):
    sigmas = torch.linspace(math.log(sigma_max), math.log(sigma_min), n).exp()
```
- **原理**：在 log(σ) 空间均匀分布
- 效果：比 karras 更激进地在高噪声区用大步长
- **适合**：euler_ancestral, er_sde 等随机采样器
- **不适合**：精度要求高的确定性采样器

#### simple
```python
def simple_scheduler(model_sampling, steps):
    ss = len(model_sampling.sigmas) / steps
    sigs = [model_sampling.sigmas[-(1 + int(x * ss))] for x in range(steps)]
```
- **原理**：直接在模型预定义的 sigma 序列上等间隔取样
- 最简单，无额外数学变换
- **Flux-Schnell 首选**（4 步快速生成）

#### ddim_uniform
```python
def ddim_scheduler(model_sampling, steps):
    ss = max(len(model_sampling.sigmas) // steps, 1)
    # 从 sigma 序列等间隔跳步取
```
- **原理**：原始 DDIM 论文的调度方式
- 与 simple 类似但从另一端开始
- **适合**：ddim, ipndm 采样器

#### beta
```python
def beta_scheduler(model_sampling, steps, alpha=0.6, beta=0.6):
    ts = 1 - numpy.linspace(0, 1, steps, endpoint=False)
    ts = numpy.rint(scipy.stats.beta.ppf(ts, alpha, beta) * total_timesteps)
```
- **原理**：用 Beta 分布的逆 CDF 来分配时间步
- 来源：arXiv:2407.12173
- alpha=beta=0.6 → 两端密集、中间稀疏的 U 型分布
- **特别适合 Flow Matching 模型**（Flux, SD3）
- **直觉**：开始和结束阶段需要更精细（建立结构 + 精修细节）

#### sgm_uniform
- **原理**：Score Generative Models 均匀调度
- 类似 normal 但尾部处理不同（不附加 0）
- **适合**：LCM（Latent Consistency Model）快速采样

#### linear_quadratic
```python
def linear_quadratic_schedule(model_sampling, steps, threshold_noise=0.025):
    # 前半段：线性从 0 到 threshold
    # 后半段：二次曲线从 threshold 到 1.0
```
- **原理**：两段式调度，低噪声线性 + 高噪声二次
- 来源：Mochi 视频生成模型
- **适合**：dpmpp_3m_sde（复杂场景/视频）

#### kl_optimal
- **原理**：最小化 KL 散度的最优调度
- 理论上最优的步骤分配
- **适合**：uni_pc（自适应预测-校正器）

### 3.2 Scheduler × Sampler 交叉效应

**关键发现：不是所有组合都有意义**

#### 最佳搭配（from ComfyUI.dev 兼容性矩阵）

| 采样器 | 最佳 Scheduler | 为什么 |
|--------|---------------|--------|
| euler | normal | 快速清晰，高对比 |
| euler_cfg_pp | karras | CFG 增强需要平滑过渡 |
| euler_ancestral | exponential | 随机性 + 激进调度 = 梦幻效果 |
| dpmpp_2m | **karras** | 工业金标准组合 |
| dpmpp_2m_cfg_pp | beta | CFG++ 需要两端密集 |
| dpmpp_2m_sde | karras | 写实王者组合 |
| dpmpp_3m_sde | linear_quadratic | 三阶精度 + 两段调度 |
| heunpp2 | karras | 二阶校正 + 细节强化 |
| lcm | sgm_uniform | 速度匹配 |
| uni_pc | kl_optimal | 自适应 + 最优调度 |
| deis | simple | 指数积分器 + 简洁调度 |
| ipndm | ddim_uniform | 四阶方法 + DDIM 步骤 |

#### 💣 危险组合（避免使用）

| 组合 | 问题 |
|------|------|
| lcm + exponential | LCM 为速度设计，复杂调度反而劣化 |
| uni_pc + simple | 丢失自适应优势，输出平淡 |
| *_cfg_pp + 无双 CLIP | CFG++ 需要双编码器配合 |
| dpmpp_sde_gpu + exponential | 高噪声调度 + SDE 随机 = 混乱 |
| Flux + karras | karras 为传统扩散设计，Flux 不适用 |

### 3.3 步数-质量关系

**通用曲线（确定性采样器）**：
```
质量
 ↑
 │         ┌────────── 收敛（30-50步后质量饱和）
 │       ╱
 │     ╱  ← 甜蜜区（15-25步）
 │   ╱
 │ ╱ ← 快速上升区（1-10步）
 └─────────────────→ 步数
```

**各步数档位实用性**（以 dpmpp_2m + karras 为例）：

| 步数 | SD 1.5 | SDXL | Flux |
|------|--------|------|------|
| 5 | ❌ 模糊变形 | ❌ 不可用 | ⚠️ 勉强（Schnell） |
| 10 | ⚠️ 可辨认但粗糙 | ⚠️ 结构出来 | ✅ 还行 |
| 15 | ✅ 可用质量 | ✅ 不错 | ✅ 好 |
| 20 | ✅ 好 | ✅✅ 推荐 | ✅✅ 推荐 |
| 25 | ✅✅ 推荐 | ✅✅ 最佳 | ✅✅ 最佳 |
| 30 | ✅✅ 最佳 | ✅ 收益递减 | ✅ 收益递减 |
| 50 | ✅ 几乎无改善 | ✅ 过度 | ✅ 过度 |

**随机采样器（SDE/ancestral）的特殊行为**：
- **不收敛！** 50 步不一定比 25 步好
- 存在"甜蜜区"，超过后质量可能下降
- euler_a: 甜蜜区 20-30 步
- dpmpp_sde: 甜蜜区 15-25 步

---

## 4. CFG Scale × 采样器交互

### 4.1 不同采样器的 CFG 耐受度

| 采样器 | 低 CFG (1-4) | 中 CFG (5-9) | 高 CFG (10-15) | 超高 CFG (15+) |
|--------|-------------|-------------|---------------|---------------|
| euler | 柔和 | ✅最佳 | 偏锐 | 过饱和 |
| dpmpp_2m | 平淡 | ✅最佳 | ✅稳定 | 偏锐但可用 |
| dpmpp_sde | 模糊 | ✅最佳 | ⚠️容易闪 | ❌不稳定 |
| heun | 柔和 | ✅最佳 | ✅稳定 | 过饱和 |
| euler_a | 多样 | ✅最佳 | ⚠️对比过强 | ❌失控 |
| ddim | 模糊 | ✅可用 | ✅稳定 | 偏硬 |
| uni_pc | 平淡 | ✅最佳 | ✅稳定 | 可用 |

**核心规律**：
1. **DPM++ 2M 对高 CFG 最稳定** — 多步法的误差积累更慢
2. **SDE/ancestral 采样器在高 CFG 下不稳定** — 随机噪声被 CFG 放大
3. **UniPC 的 predictor-corrector 机制天生抗 CFG 发散**
4. **Flux 不用管 CFG** — 这是 Flux 简化工作流的一大优势

### 4.2 CFG++ (cfg_pp 变体)

ComfyUI 的 `*_cfg_pp` 采样器实现了改进版 CFG：
- 传统 CFG: `output = uncond + cfg * (cond - uncond)`
- CFG++: 在 ODE 求解过程中直接融入引导，减少 CFG 导致的 ODE 偏离
- **需要双 CLIP 编码器设置**（positive + negative prompt 走不同编码器）
- **不适用于 Flux**（Flux 不用 CFG）

---

## 5. 实践经验总结

### 5.1 快速决策树

```
选择采样器：
├── 用 Flux？
│   ├── 快速出图 → euler + simple (4 步 Schnell)
│   ├── 高质量 → euler + normal (20-30 步)
│   └── 复杂 prompt → dpmpp_2m + beta (25 步)
├── 用 SDXL？
│   ├── 写实摄影 → dpmpp_2m_sde + karras (20 步)
│   ├── 通用 → dpmpp_2m + karras (20 步)
│   └── 快速 → uni_pc + kl_optimal (8-10 步)
└── 用 SD 1.5？
    ├── 动漫/艺术 → euler_a + normal (25 步)
    ├── 写实 → dpmpp_2m + karras (25 步)
    └── 快速 → deis + simple (10 步)
```

### 5.2 各模型最低可用步数

| 模型 | 最低可用 | 推荐最少 | 质量饱和 |
|------|---------|---------|---------|
| SD 1.5 | 10 步 | 20 步 | 30 步 |
| SDXL | 8 步 | 15 步 | 25 步 |
| SDXL-Turbo | 1 步 | 4 步 | 8 步 |
| Flux-Dev | 10 步 | 20 步 | 30 步 |
| Flux-Schnell | 1 步 | 4 步 | 8 步 |
| LCM | 2 步 | 4 步 | 8 步 |

### 5.3 关键认知升级

1. **Scheduler 的重要性被严重低估** — 同一个采样器配不同 scheduler 差异巨大
2. **Flux 是范式转换** — 传统扩散的调参经验（CFG、karras）在 Flux 上不适用
3. **ComfyUI 源码中 Flux 走独立代码路径** — `model_sampling.CONST` 触发 RF 分支
4. **Beta scheduler 是 flow matching 的最优调度** — 数学上有理论保证
5. **高阶采样器的收益在 Flux 上递减** — 直线路径不需要高阶数值积分

---

## 6. 参考资料

- Karras et al. (2022) "Elucidating the Design Space of Diffusion-Based Generative Models"
- Lu et al. (2022) "DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling"
- Zhao et al. (2023) "UniPC: A Unified Predictor-Corrector Framework"
- Lipman et al. (2023) "Flow Matching for Generative Modeling" (Rectified Flow)
- arXiv:2407.12173 — Beta scheduler for flow matching
- ComfyUI 源码: `comfy/k_diffusion/sampling.py`, `comfy/samplers.py`
- Civitai: "Sampler and Scheduler Reference for Hi-Dream, Flux, SDXL, Illustrious, and Pony"
- ComfyUI.dev: "Sampler and Scheduler Compatibility Matrix"
