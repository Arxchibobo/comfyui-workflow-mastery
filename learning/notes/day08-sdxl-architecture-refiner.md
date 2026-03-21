# Day 8: SDXL 架构差异 + Refiner 工作流

> 学习时间: 2026-03-21 00:03 UTC | 轮次: 15

## 1. SDXL 架构总览

SDXL (Stable Diffusion XL) 是 SD 1.5/2.x 的重大架构升级，论文: arXiv:2307.01952

### 1.1 核心参数对比

```
维度              SD 1.5          SD 2.1          SDXL Base       SDXL Refiner
─────────────────────────────────────────────────────────────────────────────
U-Net 参数        ~860M           ~860M           2.6B            ~2.3B (估)
文本编码器        CLIP ViT-L/14   OpenCLIP H/14   CLIP-L + OpenCLIP-bigG   OpenCLIP-bigG only
文本嵌入维度      768             1024            2048 (768+1280拼接)      1280
原生分辨率        512×512         768×768         1024×1024       1024×1024
VAE              SD-VAE          SD-VAE          SDXL-VAE (重训)  共用 SDXL-VAE
下采样层级        [1,1,1,1]       [1,1,1,1]       [0,2,10]+无8x   与base相似
Pooled Embedding  无              无              OpenCLIP pooled  OpenCLIP pooled
总参数(含编码器)   ~1B             ~1B             ~3.4B           ~3.1B
最低 VRAM 建议    4GB             6GB             ~8-12GB         额外 ~6GB
```

### 1.2 U-Net 架构变化（核心）

**SD 1.5 的 Transformer 分布**: 每个下采样层级各 1 个 Transformer Block → [1,1,1,1]
- 4 个下采样层级（1x, 2x, 4x, 8x）
- 每层都有注意力

**SDXL 的异构 Transformer 分布**: [0, 2, 10] + 移除 8x 层
- **最高分辨率层（1x）**: 0 个 Transformer Block → 纯 CNN，效率优先
- **中间层（2x 下采样）**: 2 个 Transformer Block
- **低分辨率层（4x 下采样）**: 10 个 Transformer Block → 计算主力
- **最低层（8x 下采样）**: 完全移除！
- 每个 Transformer Block 的注意力头数也增加

**设计理念**：
```
SD 1.5: 均匀分布注意力 → 简单但不高效
SDXL:   集中注意力到低分辨率特征图 → 计算效率更高

原因：低分辨率特征图尺寸小（如 32×32 vs 128×128），
     注意力计算量 = O(n²)，n=h×w
     在低分辨率层放更多 block = 同样参数量下更深的语义理解
     高分辨率层用纯 CNN = 处理局部纹理足够，不需要全局注意力
```

### 1.3 双文本编码器系统

SD 1.5 只用一个 CLIP ViT-L/14（768维）。SDXL 用两个编码器：

**CLIP ViT-L/14（text_l）**:
- OpenAI 原版 CLIP 的文本编码器
- 输出维度: 768
- 使用倒数第二层输出（penultimate layer）
- 擅长：短描述、简单概念

**OpenCLIP ViT-bigG/14（text_g）**:
- 最大的开源 CLIP 模型，训练于 LAION-2B（20亿图文对）
- 输出维度: 1280
- 更强的语义理解、更丰富的视觉-语言对齐
- 额外输出 Pooled Embedding（1280维，全局语义压缩）

**拼接方式**:
```python
# 逐 token 拼接（cross-attention 用）
text_embedding = concat(clip_l_output, openclip_g_output, dim=-1)  
# shape: [batch, 77, 768+1280] = [batch, 77, 2048]

# Pooled embedding（加到 timestep embedding）
pooled = openclip_g.pooled_output  # [batch, 1280]
```

**ComfyUI 中的体现**:
- `CLIPTextEncode`: 通用节点，两个编码器用相同 prompt
- `CLIPTextEncodeSDXL`: 高级节点，text_g 和 text_l 可以写不同 prompt
  - text_g: 给 OpenCLIP-bigG 的 prompt（主要语义）
  - text_l: 给 CLIP-L 的 prompt（辅助细节）
  - 实践中大多数人两个写一样的 prompt

### 1.4 SDXL-VAE

SDXL 使用重新训练的 VAE（同架构，不同权重）：
- **训练改进**: batch size 从 9 提升到 256
- **权重追踪**: 使用 Exponential Moving Average (EMA)
- **效果**: 所有评估指标都优于 SD 1.5 的 VAE
- **压缩比**: 同样 8x 下采样，但重建质量更高
- **编码**: [1, 3, H, W] → [1, 4, H/8, W/8]
- **关键**: SDXL Base 和 Refiner **共用同一个 VAE**，这是 latent 可以直接传递的基础


## 2. SDXL 微条件系统（Micro-Conditioning）

SDXL 的三大条件创新，都通过 Fourier 特征编码后加到 timestep embedding：

### 2.1 Size Conditioning (c_size)

**问题**: SD 1.5 训练时丢弃所有小于 512px 的图片 → 丢失 39% 数据
**方案**: 把原始图片尺寸 (h_original, w_original) 作为条件输入

```
c_size = (h_original, w_original)
→ Fourier Feature Encoding 
→ 拼接后加到 timestep embedding
```

**推理时效果**:
- `c_size = (1024, 1024)`: 生成清晰、高分辨率风格的图片
- `c_size = (256, 256)`: 生成模糊、低分辨率风格的图片
- 模型学会了把尺寸条件和图像质量关联

**ComfyUI CLIPTextEncodeSDXL 中的 width/height 参数就是 c_size**

### 2.2 Crop Conditioning (c_crop)

**问题**: SD 1.5 训练时随机裁剪图片 → 生成图常出现被裁剪的物体（如猫头被切掉）
**方案**: 把裁剪坐标 (crop_top, crop_left) 作为条件输入

```
c_crop = (crop_top, crop_left)
→ Fourier Feature Encoding
→ 加到 timestep embedding
```

**推理时**:
- `c_crop = (0, 0)`: 生成居中、完整的物体（推荐默认值）
- `c_crop = (y, x)`: 模拟从 (y, x) 开始裁剪的效果
- 实践中几乎总是设为 (0, 0)

**ComfyUI 中的 crop_w/crop_h 参数**

### 2.3 Multi-Aspect Conditioning (c_ar / target size)

**问题**: 不同宽高比的图片需要分桶训练
**方案**: 把目标尺寸 (h_target, w_target) 即 bucket size 作为条件

```
c_ar = (h_target, w_target)
```

**推理时**:
- 设为你实际想要生成的分辨率
- 帮助模型理解"我在生成一个横向/纵向/正方形的图"

**ComfyUI 中的 target_width/target_height 参数**

### 2.4 CLIPTextEncodeSDXL 源码分析

```python
class CLIPTextEncodeSDXL:
    INPUT_TYPES = {
        'width': INT(1024),       # c_size: 原始训练图像宽
        'height': INT(1024),      # c_size: 原始训练图像高
        'crop_w': INT(0),         # c_crop: 裁剪左偏移
        'crop_h': INT(0),         # c_crop: 裁剪上偏移
        'target_width': INT(1024), # c_ar: 目标宽（bucket）
        'target_height': INT(1024),# c_ar: 目标高（bucket）
        'text_g': STRING,          # OpenCLIP-bigG 的 prompt
        'text_l': STRING,          # CLIP-L 的 prompt
        'clip': CLIP,
    }
    
    def encode(self, clip, width, height, crop_w, crop_h, 
               target_width, target_height, text_g, text_l):
        # 分别 tokenize 两个 prompt
        tokens = clip.tokenize(text_g)
        tokens['l'] = clip.tokenize(text_l)['l']
        
        # 补齐长度：确保 l 和 g 的 token 数量一致
        if len(tokens['l']) != len(tokens['g']):
            empty = clip.tokenize('')
            while len(tokens['l']) < len(tokens['g']):
                tokens['l'] += empty['l']
            while len(tokens['l']) > len(tokens['g']):
                tokens['g'] += empty['g']
        
        # 编码 → 得到拼接后的 2048 维嵌入 + pooled
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        
        # conditioning 附带所有微条件参数
        return ([[cond, {
            'pooled_output': pooled,
            'width': width, 'height': height,     # c_size
            'crop_w': crop_w, 'crop_h': crop_h,   # c_crop
            'target_width': target_width,           # c_ar
            'target_height': target_height
        }]],)
```

**关键洞察**:
1. `text_g` 和 `text_l` 的 token 长度必须一致（自动用空 token 补齐）
2. 所有微条件参数都存储在 conditioning 的 metadata dict 里
3. 这些参数在采样时由 U-Net 消费（加到 timestep embedding）


## 3. SDXL Refiner 深度解析

### 3.1 Refiner 是什么

Refiner 是一个**独立的扩散模型**，专门训练用于：
- 处理**低噪声**的 latent（只训练了前 200 个离散噪声尺度）
- 提升**高频细节**：皮肤纹理、头发细节、背景元素
- 本质上是一个 **Image-to-Image 模型**，使用 SDEdit 技术

**关键特征**:
- 参数量: ~3.1B（含编码器，U-Net 约 2.3B）
- 只用 OpenCLIP-bigG（没有 CLIP-L）→ 条件用 aesthetic score 替代
- 与 Base 共用同一个 VAE → latent 可以直接传递，无需解码再编码
- **完全可选** — 现代 SDXL fine-tune 模型（如 Juggernaut XL）单模型质量已经足够好

### 3.2 Refiner 条件系统

```python
class CLIPTextEncodeSDXLRefiner:
    INPUT_TYPES = {
        'ascore': FLOAT(6.0),      # 美学分数
        'width': INT(1024),         # 图像宽
        'height': INT(1024),        # 图像高
        'text': STRING,             # 只有一个 prompt（只用 OpenCLIP-bigG）
        'clip': CLIP,
    }
```

**Aesthetic Score (ascore)** 详解:
- 训练时每张图片都有一个美学评分（由 LAION 美学预测器生成）
- 这个分数作为条件输入训练 Refiner
- 推理时：
  - **正面 prompt**: ascore = 6.0（推荐默认值，高一点如 7.5 也可以）
  - **负面 prompt**: ascore = 2.5（引导模型远离低美学质量）
- 分数越高 → 更"精致"、更"干净"，但训练样本也越少
- 实际效果：ascore 6-8 区间变化不大，极端值（<3 或 >9）可能不稳定

### 3.3 Base → Refiner 交接机制

**两种交接方式**:

#### 方式一：KSampler Advanced 的 step 分割（推荐）

```
Base KSampler (Advanced):
  - add_noise: enable
  - start_at_step: 0
  - end_at_step: X (交接点)
  - return_with_leftover_noise: enable
  
Refiner KSampler (Advanced):
  - add_noise: disable (不重复加噪！)
  - start_at_step: X (从交接点继续)
  - end_at_step: total_steps
  - return_with_leftover_noise: disable
```

**交接比例选择**:
```
常见比例        Base步数    Refiner步数    效果
80/20 (推荐)    40          10            标准平衡
70/30           35          15            更多细化
90/10           45          5             最少干预
60/40           30          20            强烈细化（可能改变构图）

总步数 = 50 为例：
- 80/20: Base 走 0-39 步，Refiner 走 40-49 步
- 关键: 设 end_at_step=40, refiner start_at_step=40
```

#### 方式二：denoise 值方式

```
Base: 正常生成完整图片（denoise=1.0, 所有步数）
→ VAEDecode → VAEEncode (或直接传 latent)
→ Refiner KSampler: denoise=0.2~0.3 (从低噪声开始)
```

这种方式更简单但不如 step 分割精确。

### 3.4 Refiner 是否还值得用？（2024-2025 社区共识）

**支持用 Refiner 的场景**:
- 使用原版 SDXL Base 1.0（未 fine-tune）
- 需要极致的人脸/皮肤细节
- 人像摄影类生成

**不用 Refiner 的原因（当前主流观点）**:
1. **Fine-tune 模型已经很强**: Juggernaut XL, RealVisXL, DreamShaper XL 等已经在质量上超越 base+refiner
2. **LoRA 不兼容**: Base 上加的 LoRA 效果会被 Refiner "洗掉"
3. **没有 Refiner fine-tune**: 社区几乎没有为 Refiner 训练 LoRA/fine-tune
4. **替代方案更好**: Hires Fix (upscale + img2img denoise 0.3-0.5) 效果更可控
5. **显存翻倍**: 需要同时加载两个大模型

**现代替代方案**:
```
方案1: 高质量 fine-tune checkpoint 直出
方案2: Base 生成 → Upscale (RealESRGAN/4x-UltraSharp) → Img2Img denoise 0.3
方案3: Base 生成 → Tile ControlNet 超分
方案4: 使用 Flux/SD3 等新架构
```


## 4. SDXL 推荐分辨率

SDXL 在 1024×1024 原生训练，支持多宽高比：

```
宽高比    分辨率            总像素(约)    场景
1:1      1024 × 1024       1.05M        默认正方形
3:4      768  × 1024       0.79M        人像竖版
4:3      1024 × 768        0.79M        风景横版
9:16     576  × 1024       0.59M        手机壁纸
16:9     1024 × 576        0.59M        桌面壁纸
2:3      832  × 1216       1.01M        全身人像（推荐）
3:2      1216 × 832        1.01M        风景（推荐）
1:2      512  × 1024       0.52M        超长竖图
21:9     1344 × 576        0.77M        超宽屏

⚠️ 总像素尽量在 ~1M 左右（接近 1024²）
⚠️ 不要低于 768 的短边（质量下降明显）
⚠️ 不要超过 1536（可能 OOM 或质量异常）
```


## 5. SDXL vs SD 1.5 工作流差异总结

### 5.1 节点差异

```
功能              SD 1.5                    SDXL
────────────────────────────────────────────────────────
加载模型          CheckpointLoaderSimple     同（但文件 6-7GB vs 2-4GB）
文本编码(简单)     CLIPTextEncode             CLIPTextEncode（自动处理双编码器）
文本编码(高级)     CLIPTextEncode             CLIPTextEncodeSDXL（分离 text_g/text_l）
Refiner编码       不适用                     CLIPTextEncodeSDXLRefiner
采样器            KSampler                   KSampler（或 Advanced 做 refiner 交接）
空 Latent         EmptyLatentImage(512)       EmptyLatentImage(1024)
CFG 推荐          7-8                        5-7（SDXL 对高 CFG 更敏感）
步数推荐          20-30                      25-40
采样器推荐        euler_a / dpmpp_2m_karras  dpmpp_2m_sde_karras / euler
```

### 5.2 Prompt 策略差异

```
SD 1.5:
- 大量负面 prompt 很重要（ugly, deformed, bad anatomy...）
- 质量标签有用（masterpiece, best quality, 8k）
- 在正面 prompt 里堆修饰词

SDXL:
- 负面 prompt 依赖度降低（模型本身质量更好）
- 自然语言描述效果更好（得益于 OpenCLIP-bigG 的理解力）
- 可以分离 text_g（全局语义）和 text_l（局部细节）
- CFG 不要太高（>10 容易过饱和）
```


## 6. 实践经验与技巧

### 6.1 微条件参数最佳实践

```python
# 标准设置（适用于 99% 场景）
{
    'width': 1024,          # = 你要生成的图像宽度
    'height': 1024,         # = 你要生成的图像高度
    'crop_w': 0,            # 保持 0
    'crop_h': 0,            # 保持 0
    'target_width': 1024,   # = width
    'target_height': 1024,  # = height
}

# 技巧：width/height 设大于实际分辨率 → 更清晰的细节
# 例：实际生成 768×1024，但 width=1024, height=1024 → 画质提升
```

### 6.2 常见问题

1. **SDXL 出黑图**: 使用了 SD 1.5 的 VAE 或 fp16 精度问题 → 确保用 SDXL VAE
2. **颜色过饱和**: CFG 太高 → 降到 5-7
3. **人脸模糊**: 分辨率太低或没用 ADetailer → 确保至少 1024 短边
4. **LoRA 效果弱**: SDXL LoRA 的 strength 通常需要比 SD 1.5 更高（0.8-1.2）
5. **OOM**: SDXL 需要至少 8GB VRAM → 使用 --lowvram 或 fp16


## 7. 参考文献

- [SDXL Paper] Podell et al., "SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis", arXiv:2307.01952, 2023
- [FollowFox SDXL Series] https://followfoxai.substack.com/p/part-3-sdxl-in-comfyui-from-scratch
- [ComfyUI SDXL Nodes Source] github.com/comfyanonymous/ComfyUI/comfy_extras/nodes_clip_sdxl.py
- [SDXL Pipeline Deep Dive] https://www.xta0.me/2025/01/20/GenAI-Stable-Diffusion-SDXL.html
