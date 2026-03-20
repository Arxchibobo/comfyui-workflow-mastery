# Day 7: LoRA 使用 + 多 LoRA 融合 + LoRA 权重调节

## 1. LoRA 数学原理

### 1.1 核心思想：低秩分解

LoRA (Low-Rank Adaptation) 的核心论文是 [arXiv:2106.09685](https://arxiv.org/abs/2106.09685)（Hu et al., 2021）。

**问题**：微调大模型需要更新全部参数（如 SD 1.5 的 U-Net 约 860M 参数），成本巨大。

**解决方案**：冻结原始权重 W₀，只学习一个低秩增量 ΔW：

```
W = W₀ + ΔW = W₀ + α/r · B·A

其中：
- W₀ ∈ ℝ^(d×k)    — 原始预训练权重（冻结）
- A ∈ ℝ^(r×k)      — 低秩矩阵（可训练）
- B ∈ ℝ^(d×r)      — 低秩矩阵（可训练）
- r << min(d, k)    — 秩（rank），通常 4~128
- α                 — 缩放因子（scaling factor）
```

**参数量对比**：
- 原始矩阵：d × k 个参数
- LoRA 增量：r × (d + k) 个参数
- 例如：d=1000, k=2000, r=10 → 原始 2,000,000 → LoRA 30,000 (66x 压缩)

### 1.2 前向传播

```
h = W₀·x + (α/r)·B·A·x

其中 x 是输入，h 是输出
```

训练时 W₀ 被冻结（requires_grad=False），只有 A 和 B 有梯度。

**初始化策略**：
- A: 随机高斯初始化
- B: 零初始化
- 这样训练开始时 ΔW = B·A = 0，模型从预训练权重出发

### 1.3 alpha 与 rank 的关系

实际缩放系数 = α / r，而不是 α 本身。

```
有效强度 = strength × (alpha / rank)

例如：
- alpha=128, rank=128 → 缩放 = 1.0
- alpha=64, rank=128 → 缩放 = 0.5
- alpha=1, rank=128 → 缩放 ≈ 0.0078（极弱）
```

ComfyUI 源码中，alpha 信息存储在 LoRA safetensors 文件的 `{layer}.alpha` 键中。

### 1.4 在 SD 中的应用位置

LoRA 最初只修改 **交叉注意力层**（Cross-Attention）：
- `to_q` — Query 投影
- `to_k` — Key 投影  
- `to_v` — Value 投影
- `to_out` — Output 投影

这些层是文本条件注入图像生成的关键接口。

**扩展**：LyCORIS 等变体扩展到了更多层（ResNet blocks、MLP 等）。

## 2. LoRA 变体家族（LyCORIS）

LyCORIS（**L**ora be**Y**ond **C**onventional methods, **O**ther **R**ank adaptation **I**mplementations for **S**table diffusion）是一系列 LoRA 变体的合集。

### 2.1 LoCon (LoRA for Convolution)

```
标准 LoRA：只修改线性层（全连接 + 注意力投影）
LoCon：扩展到卷积层（Conv2d）
```

- 额外修改 ResNet blocks 中的卷积核
- 比标准 LoRA 更强表达力（可以改变整体风格而不只是内容）
- 参数量稍大，但仍远小于全量微调

### 2.2 LoHa (LoRA with Hadamard Product)

```
LoRA:  ΔW = B · A（矩阵乘法）
LoHa:  ΔW = (B₁ · A₁) ⊙ (B₂ · A₂)（Hadamard 乘积 = 逐元素乘法）
```

- 使用 4 个低秩矩阵而非 2 个
- 理论上更高表达力（因为 Hadamard 乘积引入非线性交互）
- 相同 rank 下参数量约为 LoRA 的 2 倍
- 来源：FedPara（联邦学习论文）的低秩近似方法

### 2.3 LoKR (LoRA with Kronecker Product)

```
ΔW = W₁ ⊗ W₂ = kron(W₁, W₂)

其中 ⊗ 是 Kronecker 积
```

- 使用 Kronecker 积分解权重矩阵
- 参数量可以非常小
- 缺点：跨模型迁移性较差（在一个 checkpoint 上训练，可能不适用于其他 checkpoint）

### 2.4 DyLoRA (Dynamic Rank LoRA)

- 训练时动态搜索最优 rank
- 不需要预先指定 rank
- 训练后可以截断到更低 rank 而不重新训练

### 2.5 DoRA (Weight-Decomposed Low-Rank Adaptation)

```
W = m · (W₀ + B·A) / ||W₀ + B·A||

其中 m 是可学习的幅度参数（per-column/per-output-channel）
```

- 将权重分解为方向（direction）和幅度（magnitude）
- 在 ComfyUI 源码中对应 `dora_scale` 参数
- 通常比标准 LoRA 表现更好

### 2.6 变体对比速查表

```
┌─────────┬────────────┬────────────┬───────────┬──────────────┐
│ 方法     │ 修改层范围  │ 分解方式    │ 参数量    │ 表达力       │
├─────────┼────────────┼────────────┼───────────┼──────────────┤
│ LoRA    │ 注意力层    │ A·B 乘积   │ 最小      │ 基础         │
│ LoCon   │ +卷积层     │ A·B 乘积   │ 较小      │ 中等         │
│ LoHa    │ +卷积层     │ Hadamard积 │ 中等      │ 较高         │
│ LoKR    │ +卷积层     │ Kronecker积│ 最小      │ 中等(迁移差) │
│ DoRA    │ 同LoRA      │ A·B+幅度   │ 略大于LoRA│ 高           │
└─────────┴────────────┴────────────┴───────────┴──────────────┘
```

**ComfyUI 的统一支持**：在 ComfyUI 中，所有 LoRA 变体（包括 LyCORIS）都通过相同的 `Load LoRA` 节点加载，内部由 `weight_adapter` 模块自动识别格式并应用。

## 3. ComfyUI LoRA 源码深度分析

### 3.1 LoraLoader 节点

LoraLoader 节点定义（nodes.py）：

```python
class LoraLoader:
    INPUT_TYPES = {
        "required": {
            "model": ("MODEL",),           # 基础模型
            "clip": ("CLIP",),             # CLIP 文本编码器
            "lora_name": (folder_paths.get_filename_list("loras"),),  # LoRA 文件名
            "strength_model": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
            "strength_clip": ("FLOAT", {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01}),
        }
    }
    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_lora"
    CATEGORY = "loaders"
    
    def load_lora(self, model, clip, lora_name, strength_model, strength_clip):
        # 1. 加载 safetensors/pt 文件
        lora_path = folder_paths.get_full_path("loras", lora_name)
        lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
        
        # 2. 调用核心函数
        model_lora, clip_lora = comfy.sd.load_lora_for_models(
            model, clip, lora, strength_model, strength_clip
        )
        return (model_lora, clip_lora)
```

**关键设计**：
- `strength_model` 和 `strength_clip` 是独立的，可以分别控制对 U-Net 和 CLIP 的影响
- 范围 -20.0 ~ 20.0，**可以为负数**（反向效果）
- 步长 0.01，精细调节

### 3.2 load_lora_for_models() 核心流程

```python
def load_lora_for_models(model, clip, lora, strength_model, strength_clip):
    # Step 1: 构建 key 映射表
    key_map = {}
    key_map = comfy.lora.model_lora_keys_unet(model.model, key_map)  # U-Net 键映射
    key_map = comfy.lora.model_lora_keys_clip(clip.cond_stage_model, key_map)  # CLIP 键映射
    
    # Step 2: 格式转换（适配不同训练工具的格式）
    lora = comfy.lora_convert.convert_lora(lora)
    
    # Step 3: 加载并匹配 LoRA 权重
    loaded = comfy.lora.load_lora(lora, key_map)
    
    # Step 4: clone + patch（关键！不修改原始模型）
    new_modelpatcher = model.clone()
    k = new_modelpatcher.add_patches(loaded, strength_model)
    
    new_clip = clip.clone()
    k1 = new_clip.add_patches(loaded, strength_clip)
    
    # Step 5: 检查未加载的键
    for x in loaded:
        if (x not in k) and (x not in k1):
            logging.warning("NOT LOADED {}".format(x))
    
    return (new_modelpatcher, new_clip)
```

### 3.3 Clone + Patch 机制（关键架构设计）

**为什么 clone？**

ComfyUI 的执行引擎是基于 DAG（有向无环图）的。同一个 checkpoint 可能分流到多条路径（比如一条带 LoRA，一条不带）。如果直接修改原始模型，会影响所有下游节点。

```
CheckpointLoader
    ├── [直接用] → KSampler1（无 LoRA）
    └── LoraLoader → KSampler2（有 LoRA）
```

`model.clone()` 创建一个新的 `ModelPatcher` 实例，共享底层模型权重（零拷贝），但有独立的 patches 列表。

**add_patches 的延迟应用**：
- `add_patches()` 并不立即修改权重
- 它只是把 patch 信息记录在 patches 列表中
- 真正的权重修改发生在推理时（`model_patcher.patch_model()`）
- 这实现了高效的内存共享：多个带不同 LoRA 的 patch 共享同一份基础权重

### 3.4 Key Mapping 系统

LoRA 文件来自不同训练工具（kohya_ss、OneTrainer、diffusers、SimpleTuner 等），键名格式各异。

`model_lora_keys_unet()` 建立映射：

```python
# 通用 LoRA 格式
"lora_unet_{key}" → "diffusion_model.{key}.weight"

# Diffusers 格式
"unet.{key}" → "diffusion_model.{key}.weight"

# OneTrainer 格式（Flux）
"lora_transformer_{key}" → "diffusion_model.{key}.weight"

# LyCORIS 格式
"lycoris_{key}" → "diffusion_model.{key}.weight"
```

这就是为什么 ComfyUI 能统一加载各种格式的 LoRA 文件。

### 3.5 weight_adapter 系统

ComfyUI 通过 `weight_adapter` 模块统一处理不同类型的 LoRA 适配器：

```python
# load_lora() 中的加载逻辑
for adapter_cls in weight_adapter.adapters:
    adapter = adapter_cls.load(x, lora, alpha, dora_scale, loaded_keys)
    if adapter is not None:
        patch_dict[to_load[x]] = adapter
        break

# 已注册的适配器类型（从源码分析）：
# - LoRAAdapter（标准 LoRA：A·B 低秩分解）
# - LoConAdapter（LoCon：扩展到卷积层）
# - LoHaAdapter（LoHA：Hadamard 积分解）
# - LoKRAdapter（LoKR：Kronecker 积分解）
# - GLoRAAdapter（GLoRA）
# - OFTAdapter（正交微调）
# - BOFTAdapter（块正交微调）
```

每个适配器类都继承 `WeightAdapterBase`，实现：
- `load()` — 从 safetensors 文件加载权重
- `calculate_weight()` — 计算最终的权重修改量
- `calculate_shape()` — 计算输出形状

### 3.6 Bypass LoRA（新特性）

```python
def load_bypass_lora_for_models(model, clip, lora, strength_model, strength_clip):
    """
    不修改基础权重，而是注入到前向传播：
    output = base_forward(x) + lora_path(x)
    
    适用于：
    - 训练场景
    - 模型权重被 offload 到 CPU/磁盘的情况
    """
```

这是标准 patch 模式的替代方案：
- **标准模式**：W' = W + ΔW，然后用 W' 做推理
- **Bypass 模式**：h = f(W, x) + g(ΔW, x)，分别计算再相加

## 4. 多 LoRA 堆叠原理与实践

### 4.1 链式加载机制

ComfyUI 中多 LoRA 通过链式连接 `Load LoRA` 节点实现：

```
Checkpoint → LoRA_1(style) → LoRA_2(character) → LoRA_3(object) → KSampler
```

每次 `Load LoRA` 都会：
1. `clone()` 当前 model/clip
2. `add_patches()` 添加新的 patch

最终效果：

```
W_final = W₀ + s₁·ΔW₁ + s₂·ΔW₂ + s₃·ΔW₃

其中 sᵢ 是 strength_model，ΔWᵢ 是各 LoRA 的权重修改
```

**关键洞察**：这是线性叠加！多个 LoRA 的效果在权重空间中是简单相加的。

### 4.2 加载顺序是否重要？

**数学上**：加法是交换的，`ΔW₁ + ΔW₂ = ΔW₂ + ΔW₁`，所以理论上顺序不影响最终权重。

**实践中**：由于浮点精度和缓存行为，顺序可能有微小影响，但通常可忽略。

建议保持一致的约定（如 style → character → object）方便管理。

### 4.3 权重调节策略

#### strength_model vs strength_clip 分离控制

```
strength_model：影响 U-Net（视觉风格、结构、细节）
strength_clip：影响 CLIP 文本编码器（语义理解、提示词响应）
```

**调优指南**：

| LoRA 类型 | strength_model | strength_clip | 说明 |
|-----------|---------------|--------------|------|
| 风格 LoRA | 0.4 - 0.8 | 0.3 - 0.7 | 降低 clip 防止语义干扰 |
| 角色 LoRA | 0.7 - 1.1 | 0.5 - 0.9 | model 要强以保持身份特征 |
| 物体 LoRA | 0.2 - 0.6 | 0.2 - 0.6 | 两者都低防止过度渗透 |
| 环境 LoRA | 0.4 - 0.7 | 0.3 - 0.5 | 中等即可 |

#### 负值 strength 的用途

`strength_model` 可以为负数（-20 ~ 20），实现反向效果：

```
W = W₀ - s·ΔW   （当 s < 0）
```

用途：
- 风格反转（生成与 LoRA 风格相反的图像）
- 减弱某种训练偏差
- 创意实验

### 4.4 多 LoRA 冲突问题与解决

**常见冲突**：
1. **风格 vs 角色**：强风格 LoRA 抹除角色特征
2. **多风格冲突**：两个风格 LoRA 拉扯色彩/构图
3. **物体溢出**：物体 LoRA 在不需要的地方出现

**解决方案**：

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| 角色特征丢失 | 风格 strength 太高 | 降风格 model 到 0.3-0.5，先降 clip |
| 怪异纹理 | 两风格频率/色彩冲突 | 禁用一个，或都降到 0.3-0.4 |
| 物体到处出现 | 物体 LoRA 过度激活 | 降到 0.2-0.3，减少提示词中的触发词 |
| 输出模糊 | LoRA 太多/权重太高 | 最多 2-3 个，权重 0.3-0.7 范围 |

### 4.5 区域化 LoRA 应用

使用 Latent Couple 或 Regional 节点，可以让不同 LoRA 只作用于画面的不同区域：

```
区域1（面部）：角色 LoRA 0.9/0.7
区域2（服装）：风格 LoRA 0.6/0.5
区域3（背景）：环境 LoRA 0.4/0.3
```

这需要额外的自定义节点（如 ComfyUI-Regional-Prompts）。

## 5. LoRA 与不同模型架构

### 5.1 SD 1.5 LoRA

- 最成熟的 LoRA 生态
- CivitAI 上数万个 LoRA
- 典型大小：10-200 MB
- 修改层：U-Net 交叉注意力 + 可选 ResNet

### 5.2 SDXL LoRA

- 双 CLIP（clip_l + clip_g）→ LoRA 需要适配两个文本编码器
- 键名前缀不同：`lora_te1_`（clip_l）+ `lora_te2_`（clip_g）
- 模型更大，LoRA 通常也更大

### 5.3 Flux LoRA

- Transformer（DiT）架构而非 U-Net
- 使用 T5 文本编码器
- 键名格式：`transformer.{key}` 或 `lora_transformer_{key}`
- LoRA 效果与 SD 系列不同（Rectified Flow 训练）

### 5.4 跨架构注意事项

**⚠️ LoRA 不能跨架构使用！**
- SD 1.5 LoRA 不能用于 SDXL
- SDXL LoRA 不能用于 Flux
- 必须确保 LoRA 与基础模型架构匹配

但在同架构内，不同 checkpoint 通常可以共享 LoRA（如 SD 1.5 的 Dreamshaper 和 RealisticVision 都可以用同一个 SD 1.5 LoRA）。

## 6. 实践经验总结

### 6.1 LoRA 使用检查清单

1. ✅ 确认 LoRA 与基础模型架构匹配（SD1.5/SDXL/Flux）
2. ✅ 检查 LoRA 的推荐 trigger word（触发词）
3. ✅ 从默认 strength 1.0/1.0 开始，逐步调整
4. ✅ 多 LoRA 时从低权重开始（0.5/0.5）
5. ✅ 固定 seed 做 A/B 对比测试
6. ✅ 如果效果太强，先降 strength_clip

### 6.2 最佳实践

- **单独验证**：先逐一测试每个 LoRA，了解其"性格"
- **CLIP 优先调**：遇到语义混乱先降 strength_clip
- **触发词精简**：不要在 prompt 中过度重复触发词
- **维护 LoRA 库**：按类型/架构/推荐权重分类管理
- **批量 A/B 测试**：固定 seed 和 sampler，每次只变一个权重
- **适可而止**：3 个以上 LoRA 通常得不偿失

### 6.3 性能影响

- 每个 LoRA 增加少量 VRAM（patch 数据）
- 首次 patch 有一次性计算开销（将 LoRA 权重合并到模型权重）
- 多 LoRA 的 VRAM 开销是线性叠加的
- ComfyUI 的缓存机制会缓存已 patch 的模型，重复生成时不会重新 patch
