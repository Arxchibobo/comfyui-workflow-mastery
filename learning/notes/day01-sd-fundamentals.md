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

## 七、参考资料

1. [DDPM 论文](https://arxiv.org/abs/2006.11239) - Ho et al., 2020
2. [LDM 论文](https://arxiv.org/abs/2112.10752) - Rombach et al., 2021
3. [LearnOpenCV DDPM Guide](https://learnopencv.com/denoising-diffusion-probabilistic-models/)
4. [Complete Guide to Samplers](https://www.felixsanz.dev/articles/complete-guide-to-samplers-in-stable-diffusion)
5. [ComfyUI Source Code](https://github.com/comfyanonymous/ComfyUI) - execution.py, graph.py
6. [Wikipedia - Stable Diffusion](https://en.wikipedia.org/wiki/Stable_Diffusion)
