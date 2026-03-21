# Day 9: LoRA 训练（kohya_ss / sd-scripts）

## 1. LoRA 训练全景图

### 1.1 训练工具生态

LoRA 训练的核心引擎是 **kohya-ss/sd-scripts**，它是一组 Python 脚本，提供了对 SD 1.5、SDXL、Flux 等架构的 LoRA/LoCon/LoHa 训练支持。围绕它形成的工具生态：

| 工具 | 类型 | 特点 |
|------|------|------|
| **kohya-ss/sd-scripts** | CLI 脚本 | 核心训练引擎，最灵活 |
| **bmaltais/kohya_ss** | Gradio GUI | 可视化界面，方便参数调整 |
| **OneTrainer** | 独立 GUI | 更现代的界面，支持多架构 |
| **SimpleTuner** | CLI | 专注简洁，Flux 支持好 |
| **Civitai Trainer** | 在线 | 无需本地 GPU，但参数有限 |
| **ComfyUI LoRA Trainer** | ComfyUI 节点 | 在 ComfyUI 内训练 |
| **ai-toolkit** | CLI | Ostris 出品，Flux 训练优秀 |

### 1.2 sd-scripts 仓库结构

```
sd-scripts/
├── train_network.py          # SD1.5/SDXL LoRA 训练入口
├── sdxl_train_network.py     # SDXL 专用入口（调用同一后端）
├── flux_train_network.py     # Flux LoRA 训练入口
├── train_db.py               # DreamBooth 训练
├── fine_tune.py              # 全量微调
├── library/
│   ├── train_util.py         # 核心训练工具函数（超大文件）
│   ├── model_util.py         # 模型加载/保存
│   ├── custom_train_functions.py  # 自定义损失函数
│   ├── sdxl_train_util.py    # SDXL 特定工具
│   └── flux_train_utils.py   # Flux 特定工具
├── networks/
│   ├── lora.py               # LoRA 网络实现
│   ├── lora_flux.py          # Flux LoRA 网络实现
│   ├── locon.py              # LoCon 实现
│   └── dylora.py             # DyLoRA 实现
└── docs/
    └── train_network_advanced.md  # 高级参数文档
```

## 2. 训练管线深度解析

### 2.1 完整训练流程

```
数据准备                    训练配置                     训练循环
┌──────────┐          ┌──────────────┐          ┌─────────────────┐
│ 收集图片  │          │ 选择基础模型  │          │  加载预训练模型   │
│    ↓     │          │    ↓         │          │      ↓          │
│ 质量筛选  │          │ 设置网络参数  │          │  冻结基础权重    │
│    ↓     │          │ (dim/alpha)  │          │      ↓          │
│ 裁剪/缩放 │   →     │    ↓         │    →    │  初始化 LoRA    │
│    ↓     │          │ 配置优化器    │          │      ↓          │
│ 打标/描述 │          │ (LR/scheduler)│         │  训练循环开始    │
│    ↓     │          │    ↓         │          │  ┌→ 采样 batch  │
│ 正则化图片│          │ 输出 TOML    │          │  │  加噪        │
│    ↓     │          │              │          │  │  预测噪声    │
│ 目录结构  │          │              │          │  │  计算 loss   │
└──────────┘          └──────────────┘          │  │  反向传播    │
                                                │  │  更新 LoRA   │
                                                │  └← 下一步     │
                                                │      ↓          │
                                                │  保存 checkpoint │
                                                └─────────────────┘
```

### 2.2 数据准备（关键中的关键）

#### 2.2.1 图片收集原则

**质量 > 数量**，不同模型的推荐数量：

| 模型 | 最少 | 推荐 | 上限（边际递减） |
|------|------|------|------------------|
| Flux | 10 | 25-30 | 50 |
| SDXL | 20 | 40-50 | 100 |
| SD 1.5 | 30 | 70-100 | 200 |

**必须包含的多样性维度**：
- 角度：正面、3/4 侧、侧面、背面
- 姿势：不同体态和动作
- 光照：自然光、室内、影棚
- 背景：多种场景（避免学到固定背景）
- 距离：特写、半身、全身
- 表情（人物）：多种表情

**绝对避免**：
- 近乎重复的图片（同一角度/光照多张）
- 统一背景（会被学成主体特征）
- 过度滤镜/后处理
- 极端裁切丢失上下文

#### 2.2.2 图片预处理

```
目标分辨率：
  SD 1.5  → 512×512 或 768×768
  SDXL    → 1024×1024
  Flux    → 1024×1024（1:1 最佳）

预处理步骤：
1. 筛选 → 删除低质量/重复
2. 裁切 → 主体居中，1:1（或启用 bucketing 支持多宽高比）
3. 缩放 → 统一到目标分辨率
4. 检查 → 100% 放大确认清晰度
```

#### 2.2.3 打标（Captioning）

打标是告诉模型"这张图里什么是重要的"。两种风格：

**Tag 式（booru 风格）**：
```
1girl, blue hair, red eyes, school uniform, standing, outdoor, sunny
```
- 适合动漫风格模型（Pony, Illustrious, NoobAI）
- 工具：WD14 Tagger, DeepDanbooru

**自然语言描述式**：
```
A young woman with blue hair and red eyes wearing a school uniform, 
standing outdoors on a sunny day with trees in the background.
```
- 适合 Flux、SD3、写实模型
- 工具：BLIP-2, GPT-4V, Gemini Pro

**关键概念 — Trigger Word（触发词）**：
- 在所有标注的开头加一个独特的触发词
- 例：`sks person`, `txcl style`, `ohwx character`
- 选择标准：不与已有词汇冲突的生僻组合
- 推理时用这个触发词激活 LoRA

#### 2.2.4 目录结构

kohya 的标准目录结构：

```
training_data/
├── <repeats>_<class_token>/      # 训练图片
│   ├── image001.png
│   ├── image001.txt              # 对应标注
│   ├── image002.png
│   └── image002.txt
└── reg/                          # 正则化图片（可选）
    └── <repeats>_<class>/
        ├── reg001.png
        └── reg001.txt
```

**目录名格式**：`<重复次数>_<类别标记>`
- `10_sks person` → 每张图每 epoch 训练 10 次，类别是 "sks person"
- `3_` → 重复 3 次，不设类别标记

**计算公式**：
```
总训练步数 = (图片数 × 重复次数 × epoch 数) / batch_size

例：30张图 × 10次重复 × 3 epoch / batch_size=2 = 450 步
```

#### 2.2.5 正则化图片（Regularization Images）

防止模型"遗忘"通用能力：
- 用基础模型生成同类别的图片（如训练人物就生成各种人物）
- 数量通常是训练图的 2-5 倍
- 与训练图放不同文件夹
- 对角色 LoRA 尤其重要，风格 LoRA 可跳过

### 2.3 训练核心参数深度解析

#### 2.3.1 Network Dimension (rank) 与 Network Alpha

**dim/rank — LoRA 中间层维度**：
```
LoRA 公式：ΔW = (α/r) × B × A
- A: [d_in × r] 降维矩阵
- B: [r × d_out] 升维矩阵
- r = rank = dim
```

| dim | 参数量 | 文件大小 | 适用场景 |
|-----|--------|---------|---------|
| 2-4 | 极少 | ~1MB | 不推荐，容量太小 |
| 8 | 少 | ~5MB | 简单风格迁移 |
| **16** | 适中 | ~10MB | **通用推荐起点** |
| **32** | 较多 | ~20MB | **角色/复杂概念** |
| 64 | 多 | ~40MB | 极复杂，边际效益低 |
| 128 | 很多 | ~80MB | 几乎全量微调级别 |

**alpha — 缩放因子**：
- `effective_scale = alpha / dim`
- alpha = dim → scale = 1.0（标准行为）
- alpha = dim/2 → scale = 0.5（减半学习效果，更稳定）
- 社区常见配置：`dim=32, alpha=16` 或 `dim=32, alpha=32`

#### 2.3.2 Learning Rate（学习率）

**分层学习率**是关键概念：

```
U-Net LR（unet_lr）：控制图像生成能力
  → SD 1.5: 1e-4 ~ 5e-4
  → SDXL:   1e-4 ~ 3e-4
  → Flux:   1e-4 ~ 5e-4

Text Encoder LR（text_encoder_lr）：控制文本理解
  → 通常设为 U-Net LR 的 1/10 ~ 1/2
  → 概念/角色: 5e-5（影响全局）
  → 简单风格: 关闭 TE 训练（设为 0）
```

**为什么 Text Encoder LR 要低？**
- TE 的变化影响所有 prompt 的理解
- 过高会破坏原有的文本-图像对齐
- 风格 LoRA 往往不需要改变文本理解

#### 2.3.3 Optimizer（优化器）

| 优化器 | 特点 | 推荐场景 |
|--------|------|---------|
| **AdamW8bit** | 经典可靠，省显存 | 通用首选 |
| **Adafactor** | 自适应 LR，更省显存 | 低显存/SDXL |
| **Prodigy** | 全自动 LR，小数据集好 | 小数据集 |
| **CAME** | Adam 改进，低步数优化 | 低步数训练 |
| **Lion** | 更新更快，但不够稳 | 实验性 |
| **DAdaptation** | 自适应 LR | 不想调 LR 时 |

**AdamW8bit 是最安全的起点**。自适应优化器（Prodigy/DAdapt）适合不想手动调 LR 的场景。

#### 2.3.4 LR Scheduler（学习率调度器）

```
constant          ████████████████  恒定不变
                  ↑ 简单直接，容易过拟合

cosine            █████████▇▆▅▃▂▁  余弦下降
                  ↑ 最常用，后期自动减速

cosine_with_restarts  ████▃▁████▃▁████▃▁  多次余弦
                  ↑ 多次探索，更鲁棒

constant_with_warmup  ▁▂▃████████████  预热+恒定
                  ↑ 开头稳定，避免初始震荡

linear            ████████▇▆▅▄▃▂▁  线性下降

polynomial        ████████▇▅▃▁     多项式下降（比线性陡）
```

**推荐**：`cosine` 是最稳妥的选择。如果训练步数长，`cosine_with_restarts` 更好。

#### 2.3.5 其他关键参数

**Batch Size**：
- 越大训练越稳定（梯度更平滑）
- 受限于 VRAM
- batch_size=1-2 适合 8GB，4-8 适合 24GB+
- 增大 batch_size 时建议同比增大 LR

**Noise Offset**：
- 允许生成更暗/更亮的图片
- 推荐值：0.03-0.1
- 超过 0.1 可能引入伪影

**Min SNR Gamma**：
- 平衡不同噪声水平的损失权重
- 推荐值：5
- 来自论文 "Efficient Diffusion Training via Min-SNR Weighting Strategy"

**Gradient Checkpointing**：
- 用时间换显存，降低 30-40% 显存占用
- 速度慢 20-30%
- 低显存必开

**Cache Latents（缓存 Latent）**：
- 预计算 VAE 编码结果缓存到内存/磁盘
- 大幅加速训练（不用每次重新编码）
- 开启后不能用 augmentation（除了 flip）

**Mixed Precision**：
- fp16：半精度，省显存，精度足够
- bf16：与 fp16 同位宽但数值范围更大
- 推荐 fp16（兼容性最好）

**Clip Skip**：
- SD 1.5 常用 clip_skip=2（跳过 CLIP 最后一层）
- SDXL 通常 clip_skip=1 或 2
- 需匹配基础模型的训练设定

## 3. 训练循环内部机制

### 3.1 核心训练循环（train_network.py 简化伪代码）

```python
# train_network.py 核心逻辑

def training_loop():
    # 1. 加载预训练模型（冻结）
    text_encoder, vae, unet = load_pretrained_model(args.pretrained_model)
    text_encoder.requires_grad_(False)
    vae.requires_grad_(False)
    unet.requires_grad_(False)
    
    # 2. 初始化 LoRA 网络
    network = LoRANetwork(
        unet, text_encoder,
        rank=args.network_dim,        # 如 32
        alpha=args.network_alpha,     # 如 16
    )
    # 只有 LoRA 参数可训练
    trainable_params = network.prepare_optimizer_params(
        text_encoder_lr=args.text_encoder_lr,  # 如 5e-5
        unet_lr=args.unet_lr,                  # 如 1e-4
    )
    
    # 3. 配置优化器和调度器
    optimizer = create_optimizer(trainable_params, args)
    lr_scheduler = create_scheduler(optimizer, args)
    
    # 4. 训练循环
    for epoch in range(num_epochs):
        for batch in dataloader:
            # 4a. 编码图片到 latent space（或从缓存读取）
            latents = vae.encode(batch.images)  # [B, 4, H/8, W/8]
            
            # 4b. 编码文本条件
            encoder_hidden_states = text_encoder(batch.captions)
            
            # 4c. 随机采样时间步
            timesteps = torch.randint(0, 1000, (B,))
            
            # 4d. 添加噪声
            noise = torch.randn_like(latents)
            noisy_latents = scheduler.add_noise(latents, noise, timesteps)
            
            # 4e. 预测噪声（通过带 LoRA 的 U-Net）
            noise_pred = unet(noisy_latents, timesteps, encoder_hidden_states)
            
            # 4f. 计算损失
            # ε-prediction: loss = MSE(noise_pred, noise)
            # v-prediction: loss = MSE(noise_pred, v_target)
            target = noise  # 或 v_target
            loss = F.mse_loss(noise_pred, target, reduction="none")
            loss = loss.mean([1, 2, 3])  # 按像素平均
            
            # 4g. 可选：Min-SNR 加权
            if args.min_snr_gamma:
                loss = apply_snr_weight(loss, timesteps, gamma=5)
            
            # 4h. 反向传播（只更新 LoRA 参数）
            loss.mean().backward()
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()
        
        # 4i. 每 N epoch 保存 checkpoint
        if epoch % save_every == 0:
            network.save_weights(output_path)
```

### 3.2 损失函数详解

**ε-prediction（噪声预测）**：
```
target = ε（添加的噪声）
loss = ||ε̂(x_t, t) - ε||²
```
- SD 1.5 默认模式
- 简单直接，大多数模型使用

**v-prediction（速度预测）**：
```
v = α_t · ε - σ_t · x_0
target = v
loss = ||v̂(x_t, t) - v||²
```
- SD 2.x、某些 SDXL 微调模型使用
- 数值更稳定，尤其在高噪声水平

**scale_v_pred_loss_like_noise_pred**：
- v-prediction 的 loss 在低噪声时间步会变大
- 此选项按噪声水平缩放 loss，使其行为类似 ε-prediction
- 推荐在 v-pred 模型训练时开启

### 3.3 Min-SNR Weighting

来自论文 "Efficient Diffusion Training via Min-SNR Weighting Strategy"：

```python
def apply_snr_weight(loss, timesteps, gamma=5):
    # SNR(t) = α²_t / σ²_t
    snr = compute_snr(timesteps)
    # 权重 = min(SNR, γ) / SNR
    # 高噪声（低 SNR）: weight ≈ 1
    # 低噪声（高 SNR）: weight = γ/SNR < 1（降权）
    weight = torch.clamp(snr, max=gamma) / snr
    return loss * weight
```

效果：防止模型过度关注低噪声（容易的）步骤，更均匀地学习所有噪声水平。

## 4. 不同架构的训练差异

### 4.1 SD 1.5 vs SDXL vs Flux 训练对比

| 维度 | SD 1.5 | SDXL | Flux |
|------|--------|------|------|
| **脚本** | train_network.py | sdxl_train_network.py | flux_train_network.py |
| **LoRA 模块** | networks/lora.py | networks/lora.py | networks/lora_flux.py |
| **基础分辨率** | 512 | 1024 | 1024 |
| **VRAM 最低** | 8GB | 12GB | 12GB（fp8） |
| **推荐 dim** | 16-32 | 32-64 | 16-32 |
| **推荐 LR** | 1e-4 ~ 5e-4 | 1e-4 ~ 3e-4 | 1e-4 ~ 5e-4 |
| **TE 训练** | 可选 | 双 TE 可选 | 一般不训练 TE |
| **数据集规模** | 30-100 | 20-50 | 10-30 |
| **标注风格** | tag 或自然语言 | 两者皆可 | **自然语言优先** |
| **正则化** | 推荐 | 推荐 | 不太需要 |
| **预测模式** | ε-prediction | ε 或 v-prediction | flow matching |
| **容错性** | 低 | 中 | **高（难过拟合）** |

### 4.2 Flux LoRA 训练特殊性

Flux 使用 **flow matching** 而非传统 diffusion：
- 没有离散时间步（0-999），而是连续 t ∈ [0, 1]
- 目标是预测 velocity field（速度场），不是噪声
- LoRA 应用在 DiT（Diffusion Transformer）块上，不是 U-Net
- `networks/lora_flux.py` 替代 `networks/lora.py`

**Flux 训练命令示例**：
```bash
accelerate launch \
  --mixed_precision bf16 \
  flux_train_network.py \
  --pretrained_model_name_or_path /path/to/flux-dev \
  --clip_l /path/to/clip_l.safetensors \
  --t5xxl /path/to/t5xxl_fp16.safetensors \
  --ae /path/to/ae.safetensors \
  --cache_latents_to_disk \
  --save_model_as safetensors \
  --network_module networks.lora_flux \
  --network_dim 16 \
  --network_alpha 8 \
  --optimizer_type adamw8bit \
  --learning_rate 2e-4 \
  --lr_scheduler constant \
  --max_train_steps 1000 \
  --save_every_n_steps 200 \
  --mixed_precision bf16 \
  --save_precision bf16 \
  --gradient_checkpointing \
  --dataset_config dataset.toml
```

### 4.3 SDXL 特殊考量

- **双文本编码器**：可分别设置 `text_encoder_lr`（影响 CLIP-L + OpenCLIP-bigG）
- **微条件**：训练时自动从图片元数据提取 size/crop conditioning
- **更大模型**：2.6B U-Net，显存需求显著增加
- **Bucket 分辨率**：围绕 1024 的多种宽高比

## 5. 训练诊断与质量评估

### 5.1 Loss 曲线解读

```
理想 loss 曲线：
  ┃█
  ┃█▇
  ┃ ▆▅▄▃
  ┃    ▃▂▂▂▂▂▂  ← 收敛平稳
  ┗━━━━━━━━━━━━
  
过拟合 loss 曲线：
  ┃█
  ┃█▇▆▅▄▃▂▁▁▁  ← loss 过低
  ┃            （测试时生成僵硬、不灵活的图）
  ┗━━━━━━━━━━━━
  
欠拟合 loss 曲线：
  ┃█
  ┃█▇▇▇▆▆▆▆▆▆  ← loss 没怎么下降
  ┃            （LoRA 几乎没效果）
  ┗━━━━━━━━━━━━
```

**注意**：loss 绝对值本身不太有意义（参见 sd-scripts Discussion #294 "Everything you know about loss is a LIE!"）。相对趋势更重要。

### 5.2 常见问题诊断

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| LoRA 无效果 | dim 太小 / 步数不够 | 增大 dim，增加步数 |
| 输出变形扭曲 | LR 太高 / 过拟合 | 降 LR，减少步数 |
| 只在高权重生效 | dim 太小 / 欠训练 | 增大 dim，加长训练 |
| 风格渗透一切 | 过拟合 + 标注不好 | 加正则化图，改善标注 |
| 训练崩溃 | VRAM 不够 / LR 太高 | 减 batch，开 gradient_checkpointing |
| 背景总一样 | 数据集背景单一 | 增加背景多样性 |

### 5.3 推理测试清单

训练完成后的系统性测试：

1. **权重测试**：分别用 strength 0.5 / 0.75 / 1.0 / 1.2 生成
2. **灵活性测试**：不同 prompt 是否都能激活
3. **兼容性测试**：与其他 LoRA 组合是否冲突
4. **负面测试**：不用触发词时是否正常
5. **风格迁移测试**：配合不同 checkpoint 效果如何

## 6. ComfyUI 中使用训练好的 LoRA

训练完成后回到 ComfyUI 使用，工作流节点：

```
CheckpointLoaderSimple → LoraLoader → KSampler → ...
                          ↑
                  加载训练好的 .safetensors
                  设置 strength_model / strength_clip
```

- `strength_model`：控制 U-Net 部分的 LoRA 影响
- `strength_clip`：控制 Text Encoder 部分的 LoRA 影响
- 通常先设 1.0，再根据效果微调

## 7. 经验总结与最佳实践

### 7.1 新手快速启动配置

**SD 1.5 角色 LoRA**：
- 图片：20-30 张，512×512
- dim=32, alpha=16
- unet_lr=1e-4, te_lr=5e-5
- optimizer=AdamW8bit, scheduler=cosine
- epochs=3, batch=2
- 约 1500-3000 步

**SDXL 风格 LoRA**：
- 图片：30-50 张，1024×1024
- dim=32, alpha=32
- unet_lr=5e-5, te_lr=关闭或 1e-5
- optimizer=Adafactor, scheduler=cosine
- epochs=10, batch=2
- 约 2000-4000 步

**Flux 角色 LoRA**：
- 图片：15-25 张，1024×1024
- dim=16, alpha=8
- lr=2e-4, TE 不训练
- optimizer=adamw8bit, scheduler=constant
- 约 800-1200 步

### 7.2 核心原则

1. **数据质量是一切的基础** — 垃圾进垃圾出
2. **保守开始，逐步调整** — 先用推荐参数跑一轮
3. **多保存 checkpoint** — 每 200-500 步保存一次，挑最好的
4. **标注要精确** — 标注质量直接决定可控性
5. **用触发词** — 方便在推理时精确控制
6. **注意正则化** — 角色 LoRA 务必用正则化图
