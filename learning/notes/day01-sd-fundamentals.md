# Day 01: Stable Diffusion 算法原理 & ComfyUI 架构

> 学习日期: 2026-03-18 | 状态: 进行中

---

## 一、扩散模型基础理论 (DDPM)

### 1.1 核心思想
扩散模型灵感来自非平衡热力学统计物理：**可以通过马尔可夫链逐步将一个分布转换为另一个分布**。

两个对立过程：
- **前向扩散 (Forward Diffusion)**：逐步向图像添加高斯噪声，将复杂的数据分布转化为简单的高斯分布
- **反向扩散 (Reverse Diffusion)**：训练神经网络学习逐步去噪，从高斯噪声恢复出有意义的图像

### 1.2 数学基础

#### 前向过程
```
q(x_t | x_{t-1}) = N(x_t; √(1-β_t) · x_{t-1}, β_t · I)
```
- `β_t` = 扩散率，由 variance scheduler 预计算
- 线性调度：β 从 0.0001 到 0.02，T=1000 步
- 每步添加少量高斯噪声 ε，图像逐渐变成纯噪声

#### 重参数化技巧（关键优化！）
不需要逐步迭代 t 步，可以直接从 x_0 跳到任意 x_t：
```
α_t = 1 - β_t
ᾱ_t = α_1 · α_2 · ... · α_t  (累积乘积)
x_t = √(ᾱ_t) · x_0 + √(1-ᾱ_t) · ε    (ε ~ N(0,I))
```

#### 反向过程
```
p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))
```
- 用 U-Net 预测噪声 ε_θ(x_t, t)
- 训练目标：MSE loss = ||ε - ε_θ(x_t, t)||²
- 推理时从纯噪声 x_T ~ N(0,I) 开始，逐步去噪

### 1.3 训练与采样算法

**训练：**
1. 从数据集采样图像 x_0
2. 随机选择时间步 t ~ Uniform(1,T)
3. 随机采样噪声 ε ~ N(0,I)
4. 前向加噪得到 x_t
5. U-Net 预测噪声 ε_θ
6. 计算 loss = ||ε - ε_θ||²

**采样（推理）：**
1. 从 N(0,I) 采样 x_T
2. 从 t=T 到 t=1 逐步去噪
3. 每步用训练好的模型预测噪声并减去

---

## 二、Stable Diffusion = 潜空间扩散模型 (LDM)

### 2.1 三大核心组件

```
Text Prompt → [CLIP Text Encoder] → Text Embedding
                                          ↓ (Cross-Attention)
Random Noise → [VAE Encoder→] Latent → [U-Net 去噪 x N步] → Clean Latent → [VAE Decoder] → Final Image
```

#### 组件 1: VAE (Variational Autoencoder)
- **编码器**: 将 512×512×3 像素图像压缩为 64×64×4 的潜空间表示
- **解码器**: 将潜空间表示还原为像素空间图像
- **核心价值**: 在低维潜空间操作，计算效率提升 ~48x（512²×3 vs 64²×4）
- 保留语义信息，丢弃高频细节

#### 组件 2: U-Net (噪声预测器)
- **参数量**: 860M
- **结构**: ResNet backbone + Cross-Attention layers
- **输入**: 有噪声的 latent + 时间步 t + 文本条件 embedding
- **输出**: 预测的噪声 ε
- Cross-Attention 机制：将文本 embedding 注入到 U-Net 的中间层，实现文本条件控制

#### 组件 3: CLIP Text Encoder
- **模型**: 预训练的 CLIP ViT-L/14
- **参数量**: 123M
- **功能**: 将文本 prompt 转换为 768 维 embedding 向量
- **SDXL 升级**: 使用两个文本编码器（OpenCLIP ViT-bigG + CLIP ViT-L）

### 2.2 SD 版本架构演进

| 版本 | 架构 | 分辨率 | 关键变化 |
|------|------|--------|----------|
| SD 1.5 | LDM (U-Net) | 512×512 | 经典架构，CLIP ViT-L/14 |
| SD 2.0/2.1 | LDM (U-Net) | 768×768 | OpenCLIP ViT-H，v-prediction |
| SDXL | LDM (大 U-Net) | 1024×1024 | 双文本编码器，多纵横比训练，Refiner |
| SD 3.0 | MMDiT (Transformer) | 可变 | 抛弃 U-Net，用 Rectified Flow Transformer |
| SD 3.5 | MMDiT | 可变 | SD3 改进版 |

### 2.3 Classifier-Free Guidance (CFG)
```
ε_guided = ε_uncond + w × (ε_cond - ε_uncond)
```
- `w` = CFG Scale（引导比例，通常 7-12）
- 每步同时做两次推理：有文本条件 + 无文本条件
- w 越大，图像越贴合 prompt，但过高会产生伪影
- 训练时随机丢弃 10% 文本条件来支持 CFG

---

## 三、采样算法（Samplers）详解

### 3.1 两大类别

**数值方法类（ODE Solvers）：**
- **Euler**: 最简单，一阶线性近似，极快，10-30步出图
- **Heun**: Euler 的升级版，二阶（预测+修正），质量更高但慢 2x
- **LMS**: 线性多步法，利用前几步信息，精度更高

**概率模型类：**
- **DDPM**: 原始算法，需要很多步（1000+）
- **DDIM**: 隐式模型，大幅减少步数（50步≈DDPM 1000步）
- **PLMS**: DDIM 改进，50步≈DDIM 1000步
- **DPM++**: 混合方法，速度和质量的最佳平衡

### 3.2 DPM 家族详解

| 采样器 | 特点 | 推荐步数 |
|--------|------|----------|
| DPM2 | DPM 二代 | 30-50 |
| DPM++ 2S | 单步二阶，快 | 20-30 |
| DPM++ 2M | 多步二阶，利用历史信息，更准 | 20-30 |
| DPM++ 2M Karras | 2M + Karras 噪声调度，低步数更好 | 20-30 |
| DPM++ SDE | 随机微分方程版本，更富创意 | 20-40 |
| DPM adaptive | 自适应步长，最慢但最高质量 | 自动 |

### 3.3 变体标记含义
- **A (Ancestral)**: 每步回加随机噪声，永不收敛，更有创意但不可复现
- **Karras**: Nvidia Karras 团队的噪声调度改进，低步数表现更好
- **SDE**: 随机微分方程，更精确的噪声建模
- **2S/2M**: Single-step vs Multi-step

### 3.4 实用推荐
- 快速测试：**Euler A** (20步) 或 **DPM++ 2M Karras** (20步)
- 高质量：**DPM++ 2M Karras** (30-50步)
- 创意探索：**Euler A** (不同步数 = 不同结果)
- 最高质量：**DPM adaptive** (自动步数，慢)

---

## 四、ComfyUI 架构深度分析

### 4.1 核心设计理念
ComfyUI 是基于**节点图（Node Graph）**的 Stable Diffusion 前端，核心是一个**有向无环图（DAG）执行引擎**。

### 4.2 执行引擎架构（源码分析）

```
用户工作流 (JSON) 
    → DynamicPrompt (解析节点和连接)
    → TopologicalSort (拓扑排序)
    → ExecutionList (执行列表，支持缓存)
    → 逐节点执行 (map_node_over_list)
    → 缓存结果 (CacheSet)
```

#### 关键类：

**DynamicPrompt** - 工作流解析器
- 管理原始 prompt + 动态生成的临时节点（ephemeral）
- 支持执行过程中动态扩展图（expand 子图）
- `get_node()`, `add_ephemeral_node()`, `get_real_node_id()`

**TopologicalSort** - 拓扑排序器
- 基于入度（blockCount）的拓扑排序
- `pendingNodes`: 待执行节点
- `blockCount[node]`: 该节点被多少上游节点阻塞
- `blocking[node]`: 该节点阻塞了哪些下游节点
- 支持 lazy 输入（按需求值）

**ExecutionList** - 执行调度器（继承 TopologicalSort）
- 智能缓存：`is_cached()` 检查输出缓存
- UX 友好：优先执行输出节点（让用户更快看到结果）
- 支持异步执行（asyncio）
- 循环检测（DependencyCycleError）

**CacheSet** - 缓存系统
- Classic: 执行完即清
- LRU: 最近最少使用缓存
- RAMPressure: 按内存压力自动清理
- NULL: 不缓存

### 4.3 节点系统

每个节点是一个 Python 类，必须定义：
```python
class MyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image": ("IMAGE",)},
            "optional": {"mask": ("MASK",)},
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "execute"        # 执行函数名
    CATEGORY = "my_nodes"
    
    def execute(self, image, mask=None):
        # 处理逻辑
        return (result_image,)
```

关键属性：
- `INPUT_TYPES()`: 声明输入类型（required/optional/hidden）
- `RETURN_TYPES`: 输出类型元组
- `FUNCTION`: 执行入口
- `IS_CHANGED`: 判断是否需要重新执行（缓存失效）
- `INPUT_IS_LIST` / `OUTPUT_IS_LIST`: 批处理控制

### 4.4 数据流类型
ComfyUI 的连线传递的是类型化数据：
- `MODEL` - SD 模型
- `CLIP` - 文本编码器
- `VAE` - VAE 模型
- `CONDITIONING` - 条件信息（文本 embedding + 区域控制等）
- `LATENT` - 潜空间张量
- `IMAGE` - 图像张量 [B,H,W,C]
- `MASK` - 遮罩张量
- `INT`, `FLOAT`, `STRING` - 基础类型

### 4.5 典型 text2img 工作流节点链

```
CheckpointLoaderSimple
  ├→ MODEL ──→ KSampler
  ├→ CLIP ───→ CLIPTextEncode (positive)
  │            CLIPTextEncode (negative)
  └→ VAE ───→ VAEDecode

EmptyLatentImage ──→ LATENT ──→ KSampler

CLIPTextEncode (positive) ──→ CONDITIONING ──→ KSampler
CLIPTextEncode (negative) ──→ CONDITIONING ──→ KSampler

KSampler ──→ LATENT ──→ VAEDecode ──→ IMAGE ──→ SaveImage
```

KSampler 核心参数：
- `seed`: 随机种子
- `steps`: 采样步数
- `cfg`: CFG Scale
- `sampler_name`: 采样算法
- `scheduler`: 噪声调度器（normal/karras/exponential/sgm_uniform）
- `denoise`: 去噪强度（1.0=完全去噪，<1.0=img2img 部分去噪）

---

## 五、关键概念速查

| 概念 | 解释 |
|------|------|
| Latent Space | 64×64×4 的压缩表示空间，比像素空间计算效率高 ~48x |
| CFG Scale | 文本引导强度，越高越贴合 prompt，过高产生伪影 |
| Denoise | 去噪强度，1.0=txt2img，0.3-0.7=img2img |
| Checkpoint | 包含 U-Net + CLIP + VAE 的完整模型文件 |
| LoRA | 低秩自适应，小文件（几十MB）微调特定风格/概念 |
| ControlNet | 额外条件控制（姿势/边缘/深度等），不改变原模型 |
| VAE | 像素↔潜空间的编解码器 |
| Embedding/Textual Inversion | 扩展文本编码器的词汇表 |

---

## 六、今日实操计划

- [x] 理论学习：DDPM 原理 + 数学推导
- [x] 理论学习：Stable Diffusion LDM 架构
- [x] 理论学习：采样算法对比
- [x] 源码分析：ComfyUI execution.py + graph.py
- [ ] 实操：不同采样器对比实验（同 prompt 同 seed，切换 sampler）
- [ ] 实操：CFG Scale 对比实验（1, 3, 7, 12, 20）
- [ ] 实操：步数对比实验（5, 10, 20, 30, 50, 100 步）
- [ ] 深入阅读：原始论文 DDPM (arXiv:2006.11239) + LDM (arXiv:2112.10752)

---

## 七、论文精读笔记

### 7.1 DDPM 原始论文精读 (arXiv:2006.11239)

> Ho, Jain & Abbeel, 2020. "Denoising Diffusion Probabilistic Models"

#### 论文定位与贡献

DDPM 并非扩散模型的发明者（2015 Sohl-Dickstein 提出），而是第一个让扩散模型在图像生成质量上**媲美 GAN** 的工作。论文的核心贡献：

1. **简化训练目标**：将复杂的变分下界 (VLB/ELBO) 简化为一个简单的 MSE 噪声预测 loss
2. **建立与 Score Matching 的理论连接**：揭示 DDPM 与 Langevin 动力学、去噪分数匹配的深层联系
3. **渐进式有损压缩视角**：将反向过程解释为逐步解压缩，建立率失真 (rate-distortion) 分析框架

#### ELBO 推导详解

扩散模型的训练本质是**最大化数据的对数似然** log p_θ(x_0)。但直接计算需要对所有可能的去噪路径积分，不可行。

**变分下界推导**（参考 Jake Tae 的优秀推导）：

```
log p(x) = log Σ_h p(x,h)                    [全概率公式]
         = log Σ_h q(h|x) · p(x,h)/q(h|x)    [乘除 q]
         ≥ Σ_h q(h|x) · log[p(x,h)/q(h|x)]   [Jensen 不等式，利用 log 的凹性]
         = E_q[log p(x,h) - log q(h|x)]        [ELBO]
```

关键洞察：**log p(x) - ELBO = D_KL(q(h|x) || p(h|x))**

因为 KL 散度 ≥ 0，所以 ELBO 确实是 log p(x) 的下界。当 q = p（近似后验=真实后验）时取等号。

**DDPM 中的 ELBO 展开**：

将 h 替换为扩散过程的全部隐变量 x_{1:T}：

```
L = E_q[-log p_θ(x_{0:T}) / q(x_{1:T}|x_0)]

展开后分解为三项之和：
L = L_T + Σ_{t=2}^{T} L_{t-1} + L_0

其中：
L_T = D_KL(q(x_T|x_0) || p(x_T))                       [前向终点 vs 先验]
L_{t-1} = D_KL(q(x_{t-1}|x_t,x_0) || p_θ(x_{t-1}|x_t))  [核心：每步去噪]
L_0 = -log p_θ(x_0|x_1)                                 [最终重建]
```

- **L_T**：前向过程将数据映射到近似 N(0,I)，这项与训练参数无关，可忽略
- **L_{t-1}**：两个高斯分布的 KL 散度，**有闭合解**！这是训练的核心
- **L_0**：离散化的数据似然项

#### Ho 的关键简化：从 VLB 到简单 loss

L_{t-1} 的核心是比较：
- q(x_{t-1}|x_t, x_0)：前向过程的后验（已知 x_0 时可闭合求解）
- p_θ(x_{t-1}|x_t)：模型预测的反向转移

前向后验的均值和方差有闭合形式：

```
μ̃_t(x_t, x_0) = [√(ᾱ_{t-1}) · β_t / (1-ᾱ_t)] · x_0 
                + [√(α_t)(1-ᾱ_{t-1}) / (1-ᾱ_t)] · x_t

σ̃²_t = β_t · (1-ᾱ_{t-1}) / (1-ᾱ_t)
```

**Ho 的重参数化技巧**：不让模型直接预测均值 μ_θ，而是预测噪声 ε_θ。因为 x_0 = (x_t - √(1-ᾱ_t)·ε) / √(ᾱ_t)，代入上式后：

```
μ_θ(x_t, t) = 1/√(α_t) · [x_t - β_t/√(1-ᾱ_t) · ε_θ(x_t, t)]
```

**最终简化 loss**：

```
L_simple = E_{t, x_0, ε} [||ε - ε_θ(√(ᾱ_t)·x_0 + √(1-ᾱ_t)·ε, t)||²]
```

这个简化丢弃了 VLB 中的时间步权重，但实验表明效果更好——因为它让模型在所有噪声级别上平等训练。

#### 与 Langevin 动力学和 Score Matching 的联系

这是论文的深刻理论贡献：

- **Score Function**：∇_x log p(x)，数据分布的梯度场
- **Langevin 动力学采样**：x_{k+1} = x_k + η·∇_x log p(x_k) + √(2η)·z，通过梯度场+随机噪声从分布采样
- **DDPM 的反向过程** ≈ 退火 Langevin 动力学：从高噪声逐渐降噪，对应温度从高到低

核心等价关系：**ε_θ(x_t, t) ∝ -∇_{x_t} log p(x_t)**

即预测噪声 = 预测负分数函数。这解释了为什么 DDPM 生成的样本质量如此之高——它隐式学习了数据分布的梯度场。

#### 渐进式压缩视角

论文还提出将 DDPM 解读为渐进式有损压缩器：

- 前向过程 = 编码（逐步增加压缩率）
- 反向过程 = 解码（逐步还原细节）
- 早期去噪步骤恢复 **全局结构**（低频），后期恢复 **细节纹理**（高频）
- 率失真曲线显示：大部分"建模容量"花在感知上重要的细节上

这个视角解释了为什么少步采样（如 DDIM）仍可产生合理图像——主要结构在前几步就确定了。

#### 实验关键数据
- 模型：U-Net with self-attention（类似 PixelCNN++ 的架构）
- T=1000, β: 0.0001→0.02 线性调度
- 256×256 LSUN 数据集：FID 达到与 GAN 可比的水平
- CIFAR-10: FID 3.17（当时最优）

#### 论文的局限
1. **采样慢**：需要 1000 步串行去噪，远慢于 GAN 的单次前传
2. **直接在像素空间操作**：计算开销大，限制了分辨率
3. **无条件控制机制**：不支持文本/图像条件生成
→ 这些局限催生了 DDIM（加速采样）、LDM（潜空间扩散）、Classifier-Free Guidance（条件控制）

---

### 7.2 LDM 原始论文精读 (arXiv:2112.10752)

> Rombach, Blattmann, Lorenz, Esser & Ommer, 2022. "High-Resolution Image Synthesis with Latent Diffusion Models"

#### 论文定位与贡献

LDM 是 Stable Diffusion 的直接理论基础。核心洞察：**将感知压缩与生成学习解耦**。

三大贡献：
1. **潜空间扩散**：在预训练自编码器的低维潜空间中训练扩散模型，计算效率提升数倍
2. **Cross-Attention 条件机制**：通用的多模态条件注入方法，支持文本/语义图/边界框等
3. **系统性的压缩比分析**：找到最优下采样因子 f=4~8 的平衡点

#### 核心创新：两阶段解耦

**为什么在潜空间做扩散？**

像素空间扩散的问题（DDPM 的局限）：
```
512×512×3 = 786,432 维 → 每步去噪都在这个巨大空间操作
大部分计算花在建模"不可感知的高频细节"上
训练成本：150-1000 V100 GPU-days
```

LDM 的解决方案：
```
阶段1（感知压缩）：图像 x → 编码器 E → 潜表示 z （如 64×64×4）
阶段2（语义压缩）：在 z 空间训练扩散模型

压缩率对比（f=8 为例）：
512×512×3 → 64×64×4 = 16,384 维
降低 48 倍计算空间！
```

**自编码器的训练**

自编码器并非简单的 AE，而是结合了：
- **感知损失 (Perceptual Loss)**：匹配 VGG 深层特征，确保视觉保真度
- **对抗损失 (Patch-based Adversarial)**：Patch Discriminator 提升锐度
- **正则化**：KL 正则（潜空间趋向标准正态）或 VQ 正则（向量量化码本）

关键超参数：KL 权重极低 (~10⁻⁶)，只做"温和约束"，不像 VAE 那样过度正则化。

核心设计原则：**自编码器只需训练一次，可复用于不同扩散模型和任务。**

#### 潜空间扩散的训练目标

```
L_LDM = E_{E(x), ε~N(0,1), t} [||ε - ε_θ(z_t, t)||²]
```

和 DDPM 的 loss 完全相同，只是操作对象从像素 x 变成潜变量 z。
U-Net 主干网络（ε_θ）带有时间嵌入，在潜空间进行去噪。

#### Cross-Attention 条件机制（关键创新）

这是让 SD 支持文本引导的核心机制：

```
给定条件输入 y（如文本 prompt）：
1. 领域编码器 τ_θ(y) → M×d_τ 的条件嵌入序列
   （文本用 BERT/CLIP tokenizer → transformer）

2. 在 U-Net 的每个分辨率层插入 Cross-Attention：
   Q = W_Q · φ_i(z_t)     [Query 来自 U-Net 特征（即潜图像）]
   K = W_K · τ_θ(y)       [Key 来自条件嵌入（即文本）]
   V = W_V · τ_θ(y)       [Value 也来自条件嵌入]
   
   Attention(Q,K,V) = softmax(QK^T / √d) · V

3. 条件化 loss：
   L = E_{E(x), y, ε, t} [||ε - ε_θ(z_t, t, τ_θ(y))||²]
   
   τ_θ 和 ε_θ 联合优化！
```

**直觉理解**：
- Q（图像特征）在"询问"：这个空间位置应该画什么？
- K/V（文本特征）在"回答"：根据 prompt，你应该关注这些语义信息
- 每个像素位置的 attention 权重 = 该位置与每个文本 token 的相关性
- 这就是为什么 attention map 可视化能展示"文本对图像各区域的影响"

**两种条件注入方式**：
1. **Concatenation**：将条件信息拼接到输入 z_t（如 inpainting 中的 mask）
2. **Cross-Attention**：通过注意力机制交互（如文本、语义图），更灵活

#### 压缩比的系统性分析

这是论文最实用的实验结论之一：

```
f=1  (LDM-1) ：无压缩，就是像素级扩散 → 训练极慢
f=2  (LDM-2) ：轻微压缩 → 仍然慢
f=4  (LDM-4) ：最佳平衡点之一 → FID优秀，训练快
f=8  (LDM-8) ：最佳平衡点之一 → FID 优于像素扩散 38 点！
f=16 (LDM-16)：压缩过度 → 开始丢失细节
f=32 (LDM-32)：压缩严重 → 显著质量下降
```

**结论**：f=4 和 f=8 是最优选择。
- f=4：更高保真度，适合需要精细细节的任务（如 inpainting）
- f=8：更高效率，适合大分辨率生成（如 text2img）
- SD 1.x 和 SDXL 都使用 f=8

#### 实验关键数据

| 任务 | 模型 | FID | 对比 |
|------|------|-----|------|
| CelebA-HQ 无条件 | LDM-4 | 5.11 | SOTA（当时）|
| ImageNet 类条件 | LDM-4-G | 3.60 | 优于 ADM-G (4.59) |
| MS-COCO 文本生成 | LDM-KL-8 | 12.63 | 比肩 GLIDE (12.24)，但参数量 1.45B vs 6B |
| Places 修复 | LDM-4 big | 1.50 | SOTA |
| ImageNet 超分 | LDM-4 big | 2.4 | 优于 SR3 |

硬件：单 A100 即可完成压缩比实验；训练速度比像素扩散快 2.7x+

#### 论文的架构遗产

LDM 的架构设计直接定义了 Stable Diffusion 的基因：

```
SD 1.x/2.x 架构 = LDM 论文的直接实例化

VAE：VQGAN 变体，f=8，4通道潜空间
U-Net：时间条件化 + 多层 Cross-Attention
文本编码器：
  - SD 1.x: CLIP ViT-L/14 (768d)
  - SD 2.x: OpenCLIP ViT-H/14 (1024d)

训练数据演进：
  - 论文实验: LAION-400M
  - SD 1.x: LAION-2B (更大版本)
  - SD 2.x: LAION-5B (过滤后子集)
```

#### 与 ComfyUI 的直接关联

ComfyUI 中的每个基础节点都对应 LDM 论文的组件：

| ComfyUI 节点 | LDM 论文组件 |
|---|---|
| CheckpointLoaderSimple | 加载 U-Net (ε_θ) + CLIP (τ_θ) + VAE (E, D) |
| CLIPTextEncode | 文本编码器 τ_θ(y)，产生 Cross-Attention 的 K/V |
| KSampler | 反向扩散过程 p_θ(z_{t-1}\|z_t, τ_θ(y)) |
| VAEDecode | 解码器 D：z → x，从潜空间恢复像素图像 |
| EmptyLatentImage | 初始化 z_T ~ N(0,I)，扩散的起点 |
| KSampler.cfg | Classifier-Free Guidance scale s |
| KSampler.sampler_name | 选择具体采样算法（Euler/DPM++/DDIM 等）|

理解了 LDM 论文 = 理解了 ComfyUI 每个基础节点的"为什么"。

---

## 八、采样器 / CFG / 步数系统性对比分析

> 本节为理论性对比实验——基于社区大量 benchmark 数据和数学分析，系统总结不同采样参数的影响规律。

### 8.1 采样器分类体系

采样器可沿三个维度分类：

**维度1: 确定性 vs 随机性**
```
确定性 (Deterministic)          随机性 (Stochastic / Ancestral)
─────────────────────          ─────────────────────────────
Euler                          Euler A (Euler Ancestral)
Heun                           DPM++ 2S A (Ancestral)
DPM++ 2M                       DPM++ SDE
DDIM                           DPM++ 2M SDE
LMS                            
UniPC                          

关键区别：
- 确定性：同 seed + 同参数 = 完全相同的输出。可复现。
- 随机性：每步引入额外噪声，同 seed 也可能不同。不可复现。
```

**维度2: 收敛性 vs 非收敛性**
```
收敛型 (Convergent)            非收敛型 (Non-convergent)
─────────────────              ────────────────────────
增加步数 → 逼近最终结果        增加步数 → 持续变化，永不稳定
30步和50步几乎一样             30步和50步完全不同
Euler, DPM++ 2M, DDIM          Euler A, DPM++ 2S A

实际意义：
- 收敛型：可以用较少步数获得接近最终质量的结果，效率更高
- 非收敛型：步数本身成为创意变量，适合探索
```

**维度3: 单步 vs 多步方法**
```
单步 (Single-step)：每步只调用一次模型
  Euler, Euler A, LMS, DDIM
  → 速度更快，每步消耗少

多步 (Multi-step)：每步调用两次或更多次模型
  Heun (2次), DPM++ 2M (2次), DPM++ SDE (1-2次)
  → 精度更高，但每步时间翻倍
  
注意：Heun 虽然每步调用2次，但需要的总步数更少
```

### 8.2 主流采样器深度对比

#### Top 5 采样器推荐表

| 排名 | 采样器 | 质量 | 速度 | 最佳步数 | 适用场景 | 调度器搭配 |
|------|--------|------|------|---------|---------|----------|
| 1 | DPM++ 2M Karras | ★★★★★ | ★★★☆ | 20-30 | 通用首选 | Karras |
| 2 | Euler | ★★★★☆ | ★★★★★ | 15-20 | 快速迭代 | Normal |
| 3 | DPM++ SDE Karras | ★★★★★+ | ★★☆☆ | 30-40 | 最终出图 | Karras |
| 4 | Euler A | ★★★★☆ | ★★★★★ | 20-25 | 创意探索 | Normal |
| 5 | UniPC | ★★★★☆ | ★★★★★ | 10-15 | 低步数生成 | Normal |

#### 各采样器数学本质速览

**Euler (欧拉法)**：
```
最简单的 ODE 求解器：x_{t-1} = x_t + h · f(x_t, t)
h = 步长（由 scheduler 决定）
f = 模型预测的去噪方向

优点：实现简单，速度快，VRAM 最低（4GB 可跑 512px）
缺点：大步长时精度不高
```

**Heun (改进欧拉法 / 梯形法)**：
```
每步做两次预测取平均：
  预测: x̃ = x_t + h · f(x_t, t)
  校正: x_{t-1} = x_t + h/2 · [f(x_t, t) + f(x̃, t-1)]

本质是二阶 Runge-Kutta (RK2)
精度更高但每步 2x 时间。img2img 保真度最好。
```

**DPM++ 2M (多步法)**：
```
DPM-Solver++ 的 2 阶多步变体：
利用前一步的梯度信息来提高精度，无需额外模型评估。
"2M" = 2nd order Multistep

核心公式（简化）：
x_{t-1} = (1+r) · D(x_t, t) - r · D(x_{t+1}, t+1)
r = h_t / h_{t+1}（步长比）

社区公认的质量/速度最佳平衡点。
```

**DDIM (去噪扩散隐式模型)**：
```
将 DDPM 的随机采样过程变为确定性：
x_{t-1} = √(ᾱ_{t-1}) · x̂_0 + √(1-ᾱ_{t-1}) · (x_t - √(ᾱ_t)·x̂_0) / √(1-ᾱ_t)

特点：
- 可以跳步（skip steps），50步 DDIM ≈ 效果而不需 1000步 DDPM
- 支持 DDIM Inversion（精确反推初始噪声），这是很多编辑技术的基础
- 步数灵活性最强
```

**DPM++ SDE**：
```
DPM-Solver++ 的随机微分方程版本：
在确定性 ODE 轨迹上叠加布朗运动噪声

质量最高（社区评测），但速度最慢
适合最终渲染，不适合迭代
```

### 8.3 CFG Scale 系统性分析

#### CFG 的数学本质（回顾）

```
ε̃ = ε_uncond + s · (ε_cond - ε_uncond)

s=1  → 纯无条件生成（忽略 prompt）
s=7  → 标准值，平衡创意与遵循
s=15 → 高遵循，可能过饱和
s=30 → 极高，通常产生伪影
```

#### CFG 值域效果对照表

| CFG 范围 | 效果描述 | 图像特征 | 适用场景 |
|---------|---------|---------|---------|
| 1-3 | 几乎忽略 prompt | 混沌、模糊、随机 | 几乎不用 |
| 4-6 | 弱引导 | 创意自由度高，色彩柔和 | 抽象艺术 |
| **7-8** | **标准范围** | **质量与遵循的最佳平衡** | **通用推荐** |
| 9-12 | 强引导 | 锐利细节，高饱和 | 精确构图 |
| 13-16 | 过强引导 | 开始出现伪影、色彩失真 | 特殊效果 |
| 17+ | 过度引导 | 严重伪影、对比度极端 | 不推荐 |

#### 不同模型的最优 CFG

```
SD 1.5:   7-9  （经典值 7.5）
SDXL:     5-8  （更好的训练使得低CFG即可遵循）
SD3:      3-5  （DiT架构+改进训练，CFG需求更低）
Flux:     1-4  （已内置 guidance distillation，几乎不需要高CFG）

趋势：模型越新 → 最优 CFG 越低
原因：训练质量提升 + 架构改进使条件信号更高效
```

### 8.4 步数 (Steps) 对比分析

#### 步数-质量关系（以 DPM++ 2M Karras 为例）

```
步数   质量描述              耗时（相对）
 5     结构模糊，细节丢失      0.25x
10     基本结构清晰             0.50x
15     良好质量，大部分场景够用  0.75x
20     优秀质量                 1.00x (基准)
25     接近最终质量             1.25x
30     收敛点，几乎无提升       1.50x
50     浪费算力                 2.50x
```

#### 不同采样器的最优步数

```
采样器              最少可用    推荐     收敛点
Euler               10         15-20    25
Euler A             15         20-25    不收敛
Heun                10         15-20    20 (实际20步=40次推理)
DPM++ 2M Karras     15         20-25    30
DPM++ SDE Karras    20         30-40    45
DDIM                20         30-50    50
UniPC               8          10-15    20
```

#### 步数与采样器的交互效应

**关键发现**：
1. **收敛型采样器**：步数增加 → 边际收益递减 → 超过收敛点纯浪费
2. **非收敛型（Ancestral）**：步数增加 → 图像持续变化 → 步数本身成为创意参数
3. **ControlNet 场景**：条件约束强时，采样器差异缩小，可大幅降低步数（15步够用）
4. **视频帧生成**：必须用确定性采样器，Euler 20步是社区标准

### 8.5 Scheduler（调度器）与采样器配合

```
Normal:     线性噪声调度，最基础
Karras:     σ 非线性衰减，前期去噪快后期精修 → 质量提升明显
Exponential: 指数衰减
SGM Uniform: Score-Based 均匀调度
Beta:       Beta 分布调度（Flux 推荐）

最佳搭配：
- DPM++ 2M + Karras → 社区公认最强组合
- Euler + Normal → 快速迭代
- DPM++ SDE + Karras → 极致质量
- Flux 模型 + DPM++ 2M + Beta → 模型适配
```

### 8.6 实用决策树

```
需要生成图像？
├── 快速测试 prompt → Euler + Normal, 15步, CFG 7
├── 正式出图 → DPM++ 2M + Karras, 25步, CFG 7.5
├── 创意探索 → Euler A + Normal, 20步, CFG 7-8
├── 最终渲染 → DPM++ SDE + Karras, 35步, CFG 7
├── Img2Img → Heun + Karras, 20步, CFG 7
├── 低VRAM → Euler + Normal, 15步（VRAM最省）
├── ControlNet → Euler + Normal, 15步（条件强时采样器不重要）
└── 视频帧 → Euler + Normal, 20步（确定性 + 帧间一致性）
```

### 8.7 实验结论总结

1. **DPM++ 2M Karras 是万金油**：95% 场景用它不会错
2. **CFG 7-8 是安全区**：几乎所有 SD 1.5/SDXL 模型的甜蜜点
3. **步数 20-25 是效率最优**：在这区间质量/时间比最高
4. **新模型趋势**：Flux/SD3 时代，低 CFG + 简单采样器就够了
5. **Ancestral 采样器**：不是"更差"，是"不同"——用于创意探索而非精确复现
6. **Scheduler 很关键**：Karras 几乎总是比 Normal 好

---

## 九、参考资料

1. [DDPM 论文](https://arxiv.org/abs/2006.11239) - Ho et al., 2020
2. [LDM 论文](https://arxiv.org/abs/2112.10752) - Rombach et al., 2022 (CVPR)
3. [LearnOpenCV DDPM Guide](https://learnopencv.com/denoising-diffusion-probabilistic-models/) - 数学细节配图极佳
4. [From ELBO to DDPM - Jake Tae](https://jaketae.github.io/study/elbo/) - ELBO 推导最清晰的文章
5. [Medium: DDPM Paper Review](https://medium.com/@EleventhHourEnthusiast/denoising-diffusion-probabilistic-models-63b4fd3a3b67) - Langevin 动力学连接
6. [Wikipedia: Latent Diffusion Model](https://en.wikipedia.org/wiki/Latent_diffusion_model) - LDM 架构伪代码
7. [Hunter Heidenreich: LDM Notes](https://hunterheidenreich.com/notes/machine-learning/generative-models/latent-diffusion-models/) - 实验数据整理
8. [Complete Guide to Samplers](https://www.felixsanz.dev/articles/complete-guide-to-samplers-in-stable-diffusion)
9. [ComfyUI Source Code](https://github.com/comfyanonymous/ComfyUI) - execution.py, graph.py
10. [CompVis/latent-diffusion](https://github.com/CompVis/latent-diffusion) - LDM 官方代码 (MIT)
