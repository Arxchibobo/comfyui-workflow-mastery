# Day 17: Model Merging — 理论、数学、ComfyUI 实现与高级技术

> 学习时间: 2026-03-21 20:03 UTC | 轮次: 25

## 1. 模型合并基础理论

### 1.1 为什么模型合并有效？

模型合并的理论基础来自三个关键发现：

#### Mode Connectivity（模式连通性）[Garipov et al., 2018]
- 独立训练的神经网络在损失景观中，可以通过简单曲线连接，且路径上训练/测试精度近似恒定
- 这意味着两个模型的权重之间存在"平滑过渡路径"

#### Linear Mode Connectivity（线性模式连通性）[Frankle et al., 2020]
- 从**同一预训练权重**微调出的模型，它们之间的线性插值路径上损失几乎不变
- 关键条件：模型必须**共享同一个基础模型**（如 SD1.5 的各种微调版本）
- 这直接解释了为什么 SD 社区的模型合并如此有效——所有模型都从同一个 checkpoint 微调而来

#### 神经网络稀疏性
- 大型神经网络的权重和激活值中，只有少数值是关键的
- 大量参数是冗余的（可以剪枝 90% 而不显著影响性能）
- 因此合并时两个模型的关键参数**冲突概率很低**

### 1.2 核心数学框架

设基础模型权重为 θ_base，微调后模型权重为 θ_ft

**Task Vector（任务向量）**定义：
```
τ = θ_ft - θ_base
```
任务向量编码了微调学到的"新能力"，是现代合并方法的核心抽象。

---

## 2. 经典合并方法

### 2.1 Weighted Sum（加权求和）
最简单也是最常用的方法。

**数学公式：**
```
θ_merged = (1 - α) · θ_A + α · θ_B
```
- α = 0 → 完全是模型 A
- α = 1 → 完全是模型 B  
- α = 0.5 → 50/50 混合

**ComfyUI 实现（ModelMergeSimple）：**
```python
def merge(self, model1, model2, ratio):
    m = model1.clone()
    kp = model2.get_key_patches("diffusion_model.")
    for k in kp:
        m.add_patches({k: kp[k]}, 1.0 - ratio, ratio)
    return (m, )
```

**关键理解：**
- `add_patches(patches, strength_patch, strength_model)` 内部执行：
  `weight = weight * strength_model + patch * strength_patch`
- 所以 `add_patches({k: kp[k]}, 1.0 - ratio, ratio)` 实际上是：
  `weight_merged = model1_weight * ratio + model2_weight * (1 - ratio)`
  （注意：ratio=1 意味着保留 model1，这是 ComfyUI 的约定）

### 2.2 Add Difference（差异叠加）
三模型方法，提取两个模型之间的差异并叠加到第三个模型上。

**数学公式：**
```
θ_merged = θ_C + α · (θ_A - θ_B)
```
- θ_A - θ_B = 两个模型之间的"差异向量"
- α 控制差异的强度
- 常见用例：`inpaint_model - base_model + other_model` → 让 other_model 获得 inpaint 能力

**ComfyUI 实现（ModelSubtract + ModelAdd）：**
```python
# ModelSubtract: model1 - multiplier * model2
def merge(self, model1, model2, multiplier):
    m = model1.clone()
    kp = model2.get_key_patches("diffusion_model.")
    for k in kp:
        m.add_patches({k: kp[k]}, -multiplier, multiplier)
    return (m, )

# ModelAdd: model1 + model2
def merge(self, model1, model2):
    m = model1.clone()
    kp = model2.get_key_patches("diffusion_model.")
    for k in kp:
        m.add_patches({k: kp[k]}, 1.0, 1.0)
    return (m, )
```

### 2.3 SLERP（球面线性插值）
在高维球面上进行插值，保持向量范数，避免线性插值的"塌缩"问题。

**数学公式：**
```
SLERP(θ_A, θ_B, t) = sin((1-t)Ω)/sin(Ω) · θ_A + sin(tΩ)/sin(Ω) · θ_B
```
其中 Ω = arccos(θ_A · θ_B / (|θ_A| · |θ_B|))

**优势：**
- 保持权重向量的范数（不会"缩小"）
- 在高维空间中更好地保持特征
- SD 社区很多流行模型都是 SLERP 合并的产物

**局限：**
- 只能合并两个模型（不支持多模型）
- ComfyUI 内置节点不直接支持，需要第三方节点

### 2.4 Block Weighted Merge（分块加权合并/MBW）
对模型的不同部分使用不同的合并比例。

**U-Net 结构分块（SD1.5 = 25 块）：**
```
Input Blocks:  input.0 ~ input.11  （12块）
Middle Block:  middle.0             （1块）
Output Blocks: output.0 ~ output.11 （12块）
```

**ComfyUI 实现（ModelMergeBlocks）：**
```python
def merge(self, model1, model2, **kwargs):
    m = model1.clone()
    kp = model2.get_key_patches("diffusion_model.")
    default_ratio = next(iter(kwargs.values()))
    
    for k in kp:
        ratio = default_ratio
        k_unet = k[len("diffusion_model."):]
        
        last_arg_size = 0
        for arg in kwargs:
            if k_unet.startswith(arg) and last_arg_size < len(arg):
                ratio = kwargs[arg]
                last_arg_size = len(arg)
        
        m.add_patches({k: kp[k]}, 1.0 - ratio, ratio)
    return (m, )
```

**关键理解：**
- 使用最长前缀匹配来确定每个参数的合并比例
- input/middle/out 三个粗粒度控制（ModelMergeBlocks 内置）
- 更细粒度：SD1.5 可以精确到 25 个 block 的独立比例
- SDXL 可以精确到各个 transformer block

**直觉指导：**
| 区域 | 控制内容 | 偏向模型A时 | 偏向模型B时 |
|------|---------|-----------|-----------|
| Input Blocks（浅层）| 构图、整体结构 | 保留A的构图 | 采用B的构图 |
| Middle Block | 语义/全局理解 | 保留A的语义 | 采用B的语义 |
| Output Blocks（深层）| 细节、纹理、风格 | 保留A的风格 | 采用B的风格 |

---

## 3. 高级合并方法（2023-2025 前沿）

### 3.1 Task Arithmetic（任务算术）[Ilharco et al., 2023]
利用任务向量进行算术运算。

```
# 添加能力
θ_merged = θ_base + α · τ_task

# 减去能力（"反学习"）
θ_merged = θ_base - α · τ_task

# 组合多个能力
θ_merged = θ_base + Σ αᵢ · τᵢ
```

**核心思想：**任务向量可以像普通向量一样加减，从而"注入"或"移除"特定能力。

### 3.2 TIES-Merging（Trim, Elect Sign & Merge）[Yadav et al., 2023, NeurIPS]

解决多模型合并时的**参数干扰**问题。三步流程：

**Step 1: Trim（修剪）**
- 去掉幅度最小的 delta 参数（保留 top-k%）
- 小幅度变化通常是噪声，去掉可减少干扰

**Step 2: Elect Sign（符号选举）**
- 对每个参数位置，统计所有任务向量中正/负的总幅度
- 选择幅度更大的方向作为"共识方向"
- 消除符号冲突（一个模型想增大，另一个想减小）

**Step 3: Merge（合并）**
- 只保留与共识方向一致的参数，不一致的置零
- 对保留的参数求平均

**数学表达：**
```
τᵢ_trimmed = trim(τᵢ, k)           # 保留top-k%幅度
sign_consensus = elect_sign(τ₁...τₙ) # 选举共识方向
τᵢ_aligned = τᵢ_trimmed ⊙ (sign(τᵢ_trimmed) == sign_consensus)
θ_merged = θ_base + α · mean(τ₁_aligned...τₙ_aligned)
```

### 3.3 DARE（Drop And REscale）[Yu et al., 2024]

**核心发现：**可以随机丢弃 90-99% 的 delta 参数而不显著影响性能！

**两步流程：**

**Step 1: Random Drop**
- 以概率 p 随机将 delta 参数置零
- 利用了大模型的极高稀疏性

**Step 2: Rescale**
- 将存活参数除以 (1-p) 来补偿丢弃的幅度
- 类似 Dropout 的 rescaling 技巧

```
τᵢ_dare = (τᵢ ⊙ mask_bernoulli(1-p)) / (1-p)
```

**DARE + TIES 组合（DARE-TIES）：**
先用 DARE 稀疏化，再用 TIES 的符号选举来合并。这是目前最先进的方法之一。

### 3.4 Git Re-Basin [Ainsworth et al., 2023]
通过排列对齐（permutation alignment）将两个模型映射到"同一个basin"中，然后再做线性插值。

**思路：**
- 神经网络的权重矩阵有排列对称性（交换两个神经元不影响功能）
- 两个独立训练的模型可能在"排列空间"上差异很大
- 先对齐排列，再合并，可以大幅减少失真

### 3.5 方法对比总结

| 方法 | 模型数 | 需要基础模型 | 稀疏性利用 | 符号处理 | 适用场景 |
|------|--------|------------|----------|---------|---------|
| Weighted Sum | 2 | ❌ | ❌ | ❌ | 简单快速合并 |
| SLERP | 2 | ❌ | ❌ | ❌ | 保持范数的合并 |
| Add Difference | 3 | ✅（隐式）| ❌ | ❌ | 能力迁移 |
| Block Weighted | 2 | ❌ | ❌ | ❌ | 精细控制不同层 |
| Task Arithmetic | N | ✅ | ❌ | ❌ | 多能力组合 |
| TIES | N | ✅ | ✅（trim）| ✅ | 减少干扰 |
| DARE | N | ✅ | ✅（drop）| ❌ | 高稀疏合并 |
| DARE-TIES | N | ✅ | ✅（both）| ✅ | 最先进方法 |
| Git Re-Basin | 2+ | ❌ | ❌ | ❌ | 跨训练对齐 |

---

## 4. ComfyUI 模型合并节点体系

### 4.1 内置节点（comfy_extras/nodes_model_merging.py）

| 节点 | 功能 | 输入 | 公式 |
|------|------|------|------|
| ModelMergeSimple | 加权合并 | model1, model2, ratio | (1-r)·M1 + r·M2 |
| ModelMergeBlocks | 分块合并 | model1, model2, input/middle/out | 每块独立比例 |
| ModelSubtract | 模型减法 | model1, model2, multiplier | M1 - mul·M2 |
| ModelAdd | 模型加法 | model1, model2 | M1 + M2 |
| CLIPMergeSimple | CLIP合并 | clip1, clip2, ratio | 同模型合并 |
| CLIPSubtract | CLIP减法 | clip1, clip2, multiplier | 同上 |
| CLIPAdd | CLIP加法 | clip1, clip2 | 同上 |
| CheckpointSave | 保存合并结果 | model, clip, vae | .safetensors |
| ModelSave | 只保存模型 | model | .safetensors |
| CLIPSave | 只保存CLIP | clip | .safetensors |
| VAESave | 只保存VAE | vae | .safetensors |

**CLIP 合并注意点（源码细节）：**
```python
# CLIPMergeSimple 跳过 position_ids 和 logit_scale
for k in kp:
    if k.endswith(".position_ids") or k.endswith(".logit_scale"):
        continue
    m.add_patches({k: kp[k]}, 1.0 - ratio, ratio)
```
- `position_ids` 是固定的位置编码索引（整数），不能插值
- `logit_scale` 是温度参数，合并可能导致数值不稳定

### 4.2 SDXL / Flux 特殊节点

ComfyUI 动态生成了架构特定的 MBW 节点：
- **ModelMergeSD1** — 25 个权重滑块（IN00-IN11, M00, OUT00-OUT11）
- **ModelMergeSD2** — 同 SD1
- **ModelMergeSDXL** — 不同的 block 结构
- **ModelMergeSD3_2B** — DiT 架构 block
- **ModelMergeFlux1** — 19 double + 38 single stream blocks

### 4.3 第三方合并节点

#### ComfyUI-DareMerge（推荐）
- **功能**：DARE-TIES 合并、MBW 渐变、注意力目标合并、模型掩码
- **核心节点**：
  - Model Merger (Advanced/DARE) — 完整 DARE-TIES 合并
  - Model Merger (MBW/DARE) — MBW 风格的 DARE 合并
  - CLIP Merger (DARE) — CLIP 的 DARE 合并
  - Gradient 系列 — 精细控制合并梯度
  - Mask 系列 — 基于幅度/随机的参数掩码
  - Normalize Model — 归一化一个模型的参数范数到另一个

#### 其他工具
- **SuperMerger**（A1111 扩展）— 最全面的 MBW 合并工具
- **Chattiori-Model-Merger**（独立工具）— Cosine/频域/Flux 支持
- **sdkit merge**（CLI 工具）— 脚本化合并

---

## 5. 合并实战指南

### 5.1 合并策略决策树

```
你想要什么？
│
├─ 混合两个模型的风格 → Weighted Sum (α=0.3~0.7)
│   └─ 想精细控制？→ Block Weighted (深层控制风格，浅层控制构图)
│
├─ 保持范数稳定 → SLERP
│
├─ 从一个模型提取能力加到另一个 → Add Difference
│   例：inpaint_model - base + my_model
│
├─ 合并3+个模型的不同能力 → TIES 或 DARE-TIES
│   └─ 干扰严重？→ 增加 trim/drop 比例
│
└─ 合并效果不好，有失真 → Git Re-Basin 对齐后再合并
```

### 5.2 合并最佳实践

1. **精度**：合并默认使用推理精度（fp16），如需更高精度用 `--force-fp32`
2. **VAE**：通常不合并 VAE，选一个好的 VAE 独立使用
3. **CLIP**：CLIP 合并需谨慎，位置编码不能插值
4. **测试**：先测试再保存（ComfyUI 的优势——直接在工作流中测试合并效果）
5. **Seed**：用固定 seed 对比合并前后效果
6. **比例**：从 0.3-0.7 开始探索，极端比例（<0.1 或 >0.9）通常没意义
7. **组件分离**：ComfyUI 可以独立合并 MODEL 和 CLIP，比 checkpoint 级合并更灵活

### 5.3 ComfyUI 合并工作流模板

#### 基础两模型合并 + 测试
```
CheckpointLoader_A → ModelMergeSimple ← CheckpointLoader_B
                          │ (ratio=0.5)
                          ↓
CLIPTextEncode(+) → KSampler → VAEDecode → PreviewImage
CLIPTextEncode(-) ↗
```

#### 三模型 Add Difference
```
CheckpointLoader_InpaintModel ──→ ModelSubtract ──→ ModelAdd ──→ KSampler
CheckpointLoader_BaseModel    ──↗      (mul=1.0)       ↑
                                                        │
CheckpointLoader_MyModel ──────────────────────────────────↗
```

#### 分块合并（精细风格控制）
```
CheckpointLoader_A → ModelMergeBlocks ← CheckpointLoader_B
                     input=0.3  (保留A的构图)
                     middle=0.5 (平衡语义)
                     out=0.8    (偏向B的风格)
```

---

## 6. SD 各架构合并差异

### 6.1 SD1.5 合并
- **最成熟**：25 blocks，社区有大量合并配方（recipes）
- MBW 配方例：`0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5`
- 社区流行模型大多是多次合并的产物（OrangeMixs, AbyssOrangeMix, etc.）

### 6.2 SDXL 合并
- Block 结构不同于 SD1.5
- 双 CLIP 编码器需要独立合并（CLIP-L + OpenCLIP-bigG）
- Refiner 模型结构不同，**不能与 Base 模型合并**
- SDXL 的 LoRA 可以通过 LoRA Merge 节点先合入模型

### 6.3 SD3 / Flux 合并
- DiT 架构，block 结构完全不同
- Flux 有 19 double-stream + 38 single-stream blocks（57 个独立可调比例）
- ComfyUI 已有 ModelMergeFlux1 节点支持
- T5-XXL 编码器较大，合并 CLIP 时注意内存
- CosXL 是一个特殊案例：通过 `(CosXL_base - SDXL_base) + my_SDXL_model` 将任意 SDXL 模型转换为 CosXL

---

## 7. LoRA 合并（与模型合并的关系）

### 7.1 LoRA Merge 到模型
ComfyUI 中 LoRA 本质上是对权重的 patch：
```python
# LoRA 加载后的效果等价于：
weight = weight + strength * ΔW_lora
```

因此 **LoRA 可以永久合入模型**：
```
CheckpointLoader → LoRALoader → CheckpointSave
```

### 7.2 多 LoRA 合并
在 ComfyUI 中，多个 LoRA 是线性叠加的：
```
W_final = W_base + s₁·ΔW₁ + s₂·ΔW₂ + ...
```

可以先将多个 LoRA 合入模型，再保存为新 checkpoint，避免每次推理都重新加载。

### 7.3 LoRA 之间的合并
理论上可以将两个 LoRA 合并：
- Weighted Sum: LoRA_merged = α·LoRA_A + (1-α)·LoRA_B
- 但效果通常不如先分别合入模型再合并模型

---

## 8. 合并质量评估

### 8.1 定性评估（推荐）
- **同 seed 对比**：固定 seed/prompt，对比合并前后
- **多 prompt 覆盖**：测试人物/风景/抽象/文字等多种 prompt
- **边界测试**：测试各模型擅长的 prompt，确保能力保留

### 8.2 定量评估
- **CLIP Score**：文图匹配度
- **FID**：分布差异（需要参考数据集）
- **人类偏好**：A/B 测试

### 8.3 常见问题诊断

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| 图像变灰/失去色彩 | 合并比例不当 | 调整比例，尝试 SLERP |
| 细节丢失 | 深层权重被过度混合 | 用 MBW，降低 output blocks 比例 |
| 构图异常 | 浅层权重冲突 | 用 MBW，偏向一个模型的 input blocks |
| 完全崩坏 | 模型架构不兼容 | 确认模型基于同一架构 |
| 风格不明显 | α 太保守 | 增大目标模型的比例 |
| 过度饱和 | 权重范数膨胀 | 使用 SLERP 或 Normalize Model |

---

## 9. 实验记录

### 实验 #27: 模型合并概念图生成
- **目的**: 生成一张展示模型合并技术的概念图
- **端点**: rhart-image-n-pro/text-to-image
- **Prompt**: "A technical infographic showing model merging concepts for AI image generation: two neural networks flowing into one merged network, with labels showing Weighted Sum, Block Merge, DARE-TIES. Clean vector style, blue and orange color scheme, white background, minimal, professional data visualization, 4K"
- **参数**: aspectRatio=16:9, resolution=1K
- **耗时**: 25s
- **成本**: ¥0.03
- **结果**: ✅ 成功，生成了清晰的技术信息图，展示了 Model A + Model B → Merged Network 的流程，以及三种合并方法的图示
- **保存**: notes/model-merging-concept.jpg

---

## 10. 关键收获

1. **理论基础**：Linear Mode Connectivity 解释了为什么从同一基础模型微调出的模型可以安全合并
2. **ComfyUI 优势**：独立处理 MODEL/CLIP/VAE，比传统 checkpoint 级合并更灵活
3. **内置 vs 高级**：内置节点覆盖 Weighted Sum / Block Merge / Add Difference；DARE-TIES 需要第三方节点
4. **实操建议**：先用 ModelMergeSimple 快速测试，满意后再用 MBW 精调，最后 CheckpointSave 保存
5. **SLERP > LERP**：在保持范数稳定性方面，球面插值优于线性插值
6. **DARE-TIES 是当前最先进的多模型合并方法**：随机丢弃 + 符号共识 + rescale
7. **合并是 SD 社区的核心创新方式**：很多流行模型本身就是多次合并的产物
