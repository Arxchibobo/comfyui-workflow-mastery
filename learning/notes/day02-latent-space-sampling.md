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

## 二、（待续）Sampling 算法数学细节

> 将在后续学习轮次中深入 ODE vs SDE 框架、收敛性证明等

---

## 参考资料

1. [Hugging Face Cookbook: SD Interpolation](https://huggingface.co/learn/cookbook/en/stable_diffusion_interpolation) — 完整代码+动画
2. [Keras: Walk through Latent Space with SD](https://keras.io/examples/generative/random_walks_with_stable_diffusion/) — 文本+图像双空间插值
3. [Smooth Diffusion (CVPR 2024)](https://openaccess.thecvf.com/content/CVPR2024/papers/Guo_Smooth_Diffusion_Crafting_Smooth_Latent_Spaces_in_Diffusion_Models_CVPR_2024_paper.pdf) — 提升潜空间平滑性
4. [Tom White 2016: Sampling Generative Networks](https://arxiv.org/abs/1609.04468) — SLERP 在生成模型中的经典论文
5. [Which Way from B to A (arXiv 2511.12757)](https://arxiv.org/html/2511.12757) — 嵌入几何对插值的影响
6. [ComfyUI Wiki: LatentComposite](https://comfyui-wiki.com/en/comfyui-nodes/latent/latent-composite) — 节点详解
7. [Dev.to: Exploiting Latent Vectors in SD](https://dev.to/ramgendeploy/exploiting-latent-vectors-in-stable-diffusion-interpolation-and-parameters-tuning-j3d) — SLERP 实操
