# Day 20: Advanced Conditioning & Composition Techniques

> 学习时间: 2026-03-22 04:03 UTC | 轮次: 28

## 1. Conditioning 数据结构深度解析

### 1.1 内部表示

ComfyUI 中，`CONDITIONING` 类型本质上是一个 Python `list`，每个元素是 `[tensor, dict]` 的二元组：

```python
# CONDITIONING = list of [embedding_tensor, metadata_dict]
conditioning = [
    [torch.Tensor(shape=[1, 77, 768]),   # CLIP 文本嵌入
     {
         "pooled_output": torch.Tensor(shape=[1, 768]),  # 池化输出（SDXL 必需）
         # 可选元数据：
         "area": (h, w, y, x),          # ConditioningSetArea
         "strength": 1.0,               # ConditioningSetAreaStrength
         "mask": torch.Tensor,           # ConditioningSetMask
         "mask_strength": 1.0,           # mask 强度
         "set_area_to_bounds": False,    # 是否裁剪到 mask 边界
         "start_percent": 0.0,          # ConditioningSetTimestepRange
         "end_percent": 1.0,            # ConditioningSetTimestepRange
         "gligen": (type, model, data),  # GLIGEN 布局数据
         "control": ControlBase,         # ControlNet 对象
         "hooks": HookGroup,             # Hook 系统
         "uuid": UUID,                   # 唯一标识
     }
    ],
    # ... 可以有多个条目（Combine 就是加多个条目）
]
```

### 1.2 采样器如何消费 Conditioning

核心函数 `_calc_cond_batch()`（`comfy/samplers.py`）的处理流程：

```
1. 初始化 out_conds（全零）和 out_counts（极小值防除零）
2. 遍历每个 cond 条目：
   a. get_area_and_mult() → 检查 timestep 范围 → 裁剪 area → 计算 mask × strength → 返回 cond_obj
   b. 按 hooks 分组到 hooked_to_run
3. 处理 default_conds（未被任何区域覆盖的剩余区域）
4. 对每组 hooks：
   a. 尝试 batch 多个兼容的 cond（相同 shape/control/patches）
   b. 一次 model forward pass
   c. 结果按 area narrow 回各自区域：out_c += output * mult
5. 最终：out_conds /= out_counts（加权平均）
```

**关键洞察**：
- **Combine 的多个条目** → 分别跑 model forward → 输出按 mult 加权平均
- **面积越大的条目贡献越大**（因为 mult 覆盖更多像素）
- **区域边缘有 8 像素的 fuzz 渐变**（避免硬边界伪影）

## 2. 四种 Conditioning 操作的数学本质

### 2.1 ConditioningCombine — 噪声预测级混合

```python
def combine(self, conditioning_1, conditioning_2):
    return (conditioning_1 + conditioning_2, )  # Python list 拼接！
```

**数学本质**：
```
ε_combined = (ε₁ × mult₁ + ε₂ × mult₂) / (mult₁ + mult₂)
```

- 不是嵌入空间的混合，而是**扩散模型输出级别的混合**
- 每个条目独立跑一次 model forward pass
- 最终对所有条目的噪声预测做加权平均
- 类似于 "compositional generation"（AND 语义）

**何时用**：
- 同时满足多个独立条件（如 "red car" AND "snowy mountain"）
- 区域提示（配合 SetArea/SetMask）
- 多 ControlNet 条件合并

### 2.2 ConditioningConcat — Token 序列级拼接

```python
def concat(self, conditioning_to, conditioning_from):
    tw = torch.cat((t1, cond_from), dim=1)  # 沿 token 维度拼接
    # t1.shape = [1, 77, 768] + cond_from.shape = [1, 77, 768]
    # → tw.shape = [1, 154, 768]
```

**数学本质**：
```
embedding_concat = cat([e_to, e_from], dim=token_dim)
# 等效于突破 77 token 限制
```

- 相当于 AUTOMATIC1111 中的 `BREAK` token
- 每个 "chunk" 的 77 个 token 独立编码后拼接
- 模型的 cross-attention 同时看到所有 token
- **pooled_output 保持不变**（取 conditioning_to 的）

**何时用**：
- 超长 prompt（超过 77 token）
- 精确描述多个细节（颜色不串）
- 分离不同概念的描述

**例子**：
```
Chunk 1: "a red cat sitting on a blue chair"
Chunk 2: "in a sunny garden with yellow flowers"
→ Concat = [77 tokens of chunk1, 77 tokens of chunk2]
→ 模型同时用 154 个 token 做 cross-attention
```

### 2.3 ConditioningAverage — 嵌入空间插值

```python
tw = torch.mul(t1, strength) + torch.mul(t0, (1.0 - strength))
# 同时插值 pooled_output
pooled = pooled_to * strength + pooled_from * (1.0 - strength)
```

**数学本质**：
```
e_avg = α × e_to + (1-α) × e_from
```

- 在 CLIP 嵌入空间做线性插值
- 混合两个 prompt 的 "语义方向"
- 结果是单个条目，只需一次 model forward
- 类似 "风格融合"

**何时用**：
- 两种风格/概念的平滑过渡
- 微调 prompt 效果（加入少量其他概念）
- 比 Combine 更 "均匀" 的混合

⚠️ **注意**：`conditioning_from` 只取第一个条目，多余的被警告忽略

### 2.4 对比总表

```
┌─────────────────┬──────────────┬──────────────┬──────────────────┬──────────────┐
│ 操作            │ 混合层级     │ 数学操作     │ Model Forward    │ 典型用途     │
├─────────────────┼──────────────┼──────────────┼──────────────────┼──────────────┤
│ Combine         │ 噪声预测     │ 加权平均     │ 每条目一次       │ 区域合成     │
│ Concat          │ Token 序列   │ 维度拼接     │ 一次(更长序列)   │ 超长 prompt  │
│ Average         │ 嵌入空间     │ 线性插值     │ 一次             │ 风格混合     │
│ SetArea+Combine │ 区域噪声     │ 区域加权平均 │ 每区域一次       │ 构图控制     │
└─────────────────┴──────────────┴──────────────┴──────────────────┴──────────────┘
```

## 3. 区域条件控制（Regional Prompting）

### 3.1 ConditioningSetArea — 矩形区域

```python
def append(self, conditioning, width, height, x, y, strength):
    c = conditioning_set_values(conditioning, {
        "area": (height // 8, width // 8, y // 8, x // 8),  # 转换到 latent 空间
        "strength": strength,
        "set_area_to_bounds": False
    })
```

**坐标系**：
- 像素坐标，原点在左上角
- 自动除以 8 转换到 latent 空间
- width/height 必须是 8 的倍数

**采样器处理**：
```python
# 裁剪到指定区域
input_x = x_in.narrow(i + 2, area[dims + i], area[i])
# 边缘 fuzz 渐变（8 像素）
for t in range(rr):
    m = mult.narrow(i + 2, t, 1)
    m *= ((1.0 / rr) * (t + 1))
```

**典型工作流**：
```
CLIP Encode "blue sky" → SetArea(上半部分) → Combine ─┐
CLIP Encode "green field" → SetArea(下半部分) → Combine ─┤→ KSampler positive
CLIP Encode "landscape photo" ───────────────────────────┘   
```

### 3.2 ConditioningSetAreaPercentage — 百分比区域

与 SetArea 相同，但用 0.0-1.0 百分比而非像素值：
```python
"area": ("percentage", height, width, y, x)
```

**优势**：分辨率无关，适合可复用工作流

### 3.3 ConditioningSetMask — 自由形状区域

```python
def append(self, conditioning, mask, set_cond_area, strength):
    c = conditioning_set_values(conditioning, {
        "mask": mask,                    # 任意形状 mask
        "set_area_to_bounds": set_area_to_bounds,  # "mask bounds" 优化
        "mask_strength": strength
    })
```

**set_cond_area 参数**：
- `"default"`: mask 应用到整个 latent（mask 外区域 = 0 权重）
- `"mask bounds"`: 裁剪到 mask 的 bounding box（节省计算量）

**vs SetArea 对比**：

| 特性 | SetArea | SetMask |
|------|---------|---------|
| 形状 | 仅矩形 | 任意形状 |
| 精度 | 像素/百分比 | mask 图像 |
| 性能 | 快（直接 narrow） | 需乘法 |
| 边缘 | 自动 8px fuzz | mask 控制 |
| 工具 | 参数即可 | 需要 mask 图 |

### 3.4 社区区域提示方案

#### Impact Pack — RegionalConditioningByColorMask
- 用颜色 mask 划分区域（红色 = 区域A，蓝色 = 区域B）
- 比手动 SetArea 更直观
- 支持任意形状

#### ComfyUI-ComfyCouple — Attention Couple
- 在注意力层级操作（不是噪声预测级）
- 更精确的区域控制
- 防止颜色/属性泄漏

#### Inspire Pack — RegionalPromptColorMask
- 颜色 mask → 区域 prompt 映射
- GUI 友好

## 4. 时间维度控制

### 4.1 ConditioningSetTimestepRange — Prompt Scheduling

```python
def set_range(self, conditioning, start, end):
    c = conditioning_set_values(conditioning, {
        "start_percent": start,  # 0.0 = 采样开始
        "end_percent": end       # 1.0 = 采样结束
    })
```

**采样器检查**（`get_area_and_mult`）：
```python
if 'timestep_start' in conds:
    if timestep_in[0] > timestep_start:
        return None  # 跳过：还没到时间
if 'timestep_end' in conds:
    if timestep_in[0] < timestep_end:
        return None  # 跳过：已过时间
```

**典型用法 — 两阶段 Prompt**：
```
"beautiful landscape" → SetTimestepRange(0.0, 0.5) → Combine ─┐
"detailed texture, 8K" → SetTimestepRange(0.5, 1.0) → Combine ─┤→ KSampler
```

**设计模式**：
- **前半段（0.0-0.5）**：控制整体构图和语义（大结构在早期步骤确定）
- **后半段（0.5-1.0）**：控制细节和质量增强
- **分段 CFG**：不同阶段用不同 prompt 引导（类似 Refiner 概念）

### 4.2 FizzNodes PromptSchedule — 动画 Prompt

- 按帧/步数切换 prompt
- 支持表达式计算（`(step * 0.1)` 等）
- 主要用于 AnimateDiff / 视频工作流

### 4.3 comfyui-prompt-control — 高级调度

- A1111 风格语法：`[prompt1:prompt2:0.5]`
- 支持 LoRA 调度
- 支持自定义编码器节点

## 5. GLIGEN — 接地式布局控制

### 5.1 原理

GLIGEN (Grounded Language-to-Image Generation) 使用 bounding box 指定对象位置：
- 训练时在 frozen SD 上增加 gated self-attention 层
- 推理时通过 bounding box + text 控制对象放置
- 模型作为额外的 "middle_patch" 注入

### 5.2 ComfyUI 实现

```python
# GLIGENTextboxApply 节点
def append(self, conditioning_to, clip, gligen_textbox_model, text, width, height, x, y):
    tokens = clip.tokenize(text)
    cond, pooled = clip.encode_from_tokens(tokens)
    c = conditioning_set_values(conditioning_to, {
        "gligen": ("position", gligen_textbox_model, {
            "text_encoder_tokens": cond,
            "width": width, "height": height, "x": x, "y": y
        })
    })
```

**采样器处理**（在 `get_area_and_mult` 中）：
```python
if 'gligen' in conds:
    gligen = conds['gligen']
    gligen_patch = gligen_model.model.set_position(input_x.shape, gligen[2], input_x.device)
    patches['middle_patch'] = [gligen_patch]
```

### 5.3 使用方式

```
全局 prompt: "a sunny park scene with people and trees"
GLIGEN box 1: text="dog", x=100, y=200, w=300, h=300  → 指定狗的位置
GLIGEN box 2: text="cat", x=500, y=200, w=200, h=200  → 指定猫的位置
```

### 5.4 局限性

- 需要专门的 GLIGEN 模型权重
- 仅支持 SD 1.5 / SD 2.1
- 社区支持有限（2025 年后较少更新）
- 被 ControlNet + Regional Prompting 方案替代

## 6. CLIP Vision & unCLIP 条件

### 6.1 CLIP Vision

```python
# CLIPVisionEncode 节点
def encode(self, clip_vision, image):
    output = clip_vision.encode_image(image)
    return (output, )
```

- CLIP Vision 模型（如 ViT-H/14）将图像编码为向量
- 输出包含 `image_embeds`（全局向量）和 `last_hidden_state`（token 级特征）

### 6.2 unCLIP Conditioning

```python
# unCLIPConditioning 节点
def apply_adm(self, conditioning, clip_vision_output, strength, noise_augmentation):
    # 将 CLIP Vision 的图像嵌入注入到 conditioning 中
    c["unclip_conditioning"].append({
        "clip_vision_output": clip_vision_output,
        "strength": strength,
        "noise_augmentation": noise_augmentation
    })
```

- 通过 CLIP Vision 嵌入注入图像语义
- 需要 unCLIP 模型（如 SD unCLIP）
- `noise_augmentation`: 给 CLIP 嵌入加噪声增强鲁棒性
- 被 IP-Adapter 方案在功能上替代

### 6.3 Style Model (T2I-Adapter 风格)

```python
# ApplyStyleModel 节点
def apply_stylemodel(self, clip_vision_output, style_model, conditioning):
    cond = style_model.get_cond(clip_vision_output).flatten(start_dim=0, end_dim=1).unsqueeze(dim=0)
    c = torch.cat((t, cond), dim=1)  # 拼接到 token 序列
```

- Style Model 将 CLIP Vision 输出转换为 conditioning tokens
- 拼接到文本 conditioning 后面（类似 Concat）
- 提供图像的风格引导

## 7. 注意力操控技术

### 7.1 Self-Attention Guidance (SAG)

**内置节点**：`SelfAttentionGuidance`

原理（Hong et al., 2023）：
```
ε_sag = ε_uncond + cfg_scale × (ε_cond - ε_uncond) + sag_scale × (ε_cond - ε_blur_cond)
```

- 通过模糊 self-attention map 创建 "degraded" 版本
- 用差异引导模型增强结构一致性
- 减少手指/面部等常见伪影

### 7.2 Perturbed-Attention Guidance (PAG)

**第三方节点**: `sd-perturbed-attention` (pamparamm)

原理（Ahn et al., CVPR 2024）：
```
ε_pag = ε_uncond + cfg_scale × (ε_cond - ε_uncond) + pag_scale × (ε_cond - ε_perturbed)
```

- 将 self-attention 替换为恒等映射，创建 "perturbed" 版本
- 比 SAG 更激进的结构引导
- 支持 SD 1.5 / SDXL / Flux

**生态扩展**（sd-perturbed-attention 包还包含）：
- SEG (Smoothed Energy Guidance)
- SWG (Sliding Window Guidance)
- NAG (Normalized Attention Guidance)
- TPG (Token Perturbation Guidance)
- FDG (Frequency-Decoupled Guidance)
- MG (Momentum Guidance)
- SMC-CFG

### 7.3 Attention Couple

**原理**：在注意力层级强制不同区域使用不同 prompt

vs **ConditioningSetArea + Combine**（噪声预测级混合）：
- Attention Couple 在每个注意力层独立处理
- 更好地防止属性泄漏（颜色/材质不串）
- 但需要修改模型推理管线

## 8. ConditioningZeroOut — 特殊用途

```python
def zero_out(self, conditioning):
    n = [torch.zeros_like(t[0]), d]  # 嵌入全零
    d["pooled_output"] = torch.zeros_like(pooled_output)  # 池化全零
```

**用途**：
- 创建 "空" 条件（等效于无文本引导）
- Flux 工作流中用作 negative（因为 Flux 不支持 negative prompt）
- 测试 CFG 的无条件分支
- 与 SetTimestepRange 配合：某些步骤不使用文本引导

## 9. 高级构图模式

### 9.1 多主体防串色方案

**方案 A: SetArea + Combine（简单）**
```
"red car" → SetArea(左半) → Combine ─┐
"blue truck" → SetArea(右半) → Combine ─┤→ KSampler
```
⚠️ 可能有颜色泄漏

**方案 B: SetMask + Combine（精确）**
```
"red car" → SetMask(car_mask) → Combine ─┐
"blue truck" → SetMask(truck_mask) → Combine ─┤→ KSampler
"highway scene" ──────────────────────────────┘ (全局)
```

**方案 C: Attention Couple（最精确）**
- 模型层面隔离注意力
- 不同区域的交叉注意力完全独立
- 代价：更多 model forward passes

### 9.2 多阶段 Prompt 策略

```
阶段 1（0.0-0.3）: "composition: character on left, landscape on right"
阶段 2（0.3-0.7）: "detailed character with blue eyes, mountain landscape"  
阶段 3（0.7-1.0）: "sharp details, 8k, professional photography"
```

### 9.3 Negative Prompt 高级用法

```
Positive: "beautiful landscape" → SetTimestepRange(0.0, 1.0) → KSampler positive
Negative 1: "blurry, lowres" → SetTimestepRange(0.0, 0.5) → Combine ─┐
Negative 2: "artifacts, noise" → SetTimestepRange(0.5, 1.0) → Combine ─┤→ KSampler negative
```

## 10. 实操实验 — RunningHub 区域构图

### 实验 #30: 区域构图效果对比

**目标**: 用 RunningHub API 生成同一场景的不同构图控制版本

**Prompt 设计**:
- 全局: "two characters in a fantasy garden"
- 左侧: "a warrior in red armor"
- 右侧: "a mage in blue robes"

**实验结果**:
- 生成时间: 35s
- 成本: ¥0.03
- 分辨率: 2752×1536 (16:9)
- 结果: 红色龙甲战士(左) vs 蓝衣冰法师(右)，完美的颜色分离和构图分割
- 分析: 现代大模型（rhart-image-n-pro 基于 Gemini）已能从纯文本理解"左右"空间关系
- 但对于 SD1.5/SDXL 等开源模型，区域条件控制仍然必要

### 实验 #31: 超长 Prompt 细节测试（模拟 Concat 场景）

**目标**: 超过 77 token 的详细场景描述

**Prompt**: 赛博朋克城市日落场景（约 200 tokens），包含：
- 建筑层（霓虹灯摩天楼+日文/中文招牌+全息广告）
- 天空层（飞行汽车+光尾+琥珀色天空+满月）
- 街道层（湿润路面+紫色/青色霓虹反射+食物摊位+人群）
- 前景（赛博武士+发光电路铠甲+太刀）
- 氛围（体积雾+丁达尔效应+镜头光晕）
- 风格（银翼杀手×攻壳机动队+8K+三分法构图）

**结果**:
- 生成时间: 40s
- 成本: ¥0.03
- 分辨率: 2752×1536 (16:9)
- 几乎所有描述元素都被准确呈现
- 在 ComfyUI 中，SD1.5/SDXL 如此长的 prompt 必须用 ConditioningConcat 分段
- rhart-image-n-pro 内部可能已自动处理长文本

## 11. 条件系统决策树

```
需要什么效果？
│
├─ 超长文本描述 → ConditioningConcat（突破 77 token）
│
├─ 两种风格混合 → ConditioningAverage（嵌入插值）
│
├─ 多个独立条件 → ConditioningCombine
│   │
│   ├─ 需要区域控制？
│   │   ├─ 矩形区域 → SetArea + Combine
│   │   ├─ 自由形状 → SetMask + Combine  
│   │   └─ 精确防串 → Attention Couple（第三方）
│   │
│   └─ 不需要区域 → 直接 Combine（全局混合）
│
├─ 不同步骤不同 prompt → SetTimestepRange + Combine
│
├─ 图像风格迁移 → CLIP Vision + IP-Adapter（首选）
│   └─ 或 unCLIP / Style Model（较旧）
│
├─ 精确对象位置 → GLIGEN（SD1.5 only）或 ControlNet pose
│
└─ 增强结构质量 → SAG / PAG（注意力引导）
```

## 12. 关键源码函数速查

| 函数 | 文件 | 作用 |
|------|------|------|
| `combine()` | nodes.py | list 拼接 |
| `concat()` | nodes.py | torch.cat(dim=1) |
| `addWeighted()` | nodes.py | α×t1 + (1-α)×t0 |
| `get_area_and_mult()` | samplers.py | 解析区域/mask/时间范围 |
| `_calc_cond_batch()` | samplers.py | 核心：多条件加权平均 |
| `cfg_function()` | samplers.py | CFG 公式 |
| `sampling_function()` | samplers.py | 主采样入口 |
| `conditioning_set_values()` | node_helpers.py | 深拷贝 + 设值 |
