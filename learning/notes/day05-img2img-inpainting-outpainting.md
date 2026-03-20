# Day 5: Img2Img, Inpainting & Outpainting

> 学习时间: 2026-03-20 16:03 UTC | 轮次: 11-12

---

## 1. Img2Img 原理深度解析

### 1.1 核心概念：从 Text2Img 到 Img2Img

Text2Img 和 Img2Img 的本质区别只有**一个**：latent 的起点不同。

| | Text2Img | Img2Img |
|---|---|---|
| **起始 latent** | 纯随机噪声 `EmptyLatentImage` | 编码后的图片 + 部分噪声 `VAEEncode` |
| **denoise** | 固定 1.0（全量去噪） | 0.0 ~ 1.0（控制变化程度） |
| **节点** | EmptyLatentImage → KSampler | LoadImage → VAEEncode → KSampler |

### 1.2 数学原理：denoise 如何工作

从 ComfyUI 源码 `comfy/samplers.py` 的 `KSampler.set_steps()` 可以看到核心逻辑：

```python
def set_steps(self, steps, denoise=None):
    self.steps = steps
    if denoise is None or denoise > 0.9999:
        # 完全去噪 = text2img
        self.sigmas = self.calculate_sigmas(steps).to(self.device)
    else:
        if denoise <= 0.0:
            self.sigmas = torch.FloatTensor([])  # 不做任何事
        else:
            new_steps = int(steps / denoise)  # 扩展总步数
            sigmas = self.calculate_sigmas(new_steps).to(self.device)
            self.sigmas = sigmas[-(steps + 1):]  # 只取最后 steps+1 个 sigma
```

**关键理解**：
- `denoise=1.0`：从 σ_max 开始（纯噪声），等价于 text2img
- `denoise=0.5`：从 sigma 序列的中间点开始，原图结构大量保留
- `denoise=0.3`：从 sigma 序列的后段开始，只做轻微调整

**sigma 截断图示**（假设 steps=20）：
```
denoise=1.0: σ_max ─────────────────────────── σ_min (全部 20 步)
denoise=0.7: 原图 ──────── 加噪到此 ──────── σ_min (20 步但从 σ 序列的后 20 步)
denoise=0.3: 原图 ─────────────── 加噪到此 ── σ_min (少量步数)
```

实际计算：`new_steps = int(steps / denoise)`
- steps=20, denoise=0.5 → new_steps=40, 取 sigmas[-21:]（从第 20 步开始）
- steps=20, denoise=0.7 → new_steps=28, 取 sigmas[-21:]（从第 8 步开始）

### 1.3 VAEEncode 流程 vs EmptyLatentImage 区别

#### EmptyLatentImage（Text2Img 用）
```python
class EmptyLatentImage:
    def generate(self, width, height, batch_size=1):
        latent = torch.zeros([batch_size, 4, height // 8, width // 8],
                            device=comfy.model_management.intermediate_device())
        return ({"samples": latent}, )
```
- 生成**全零** latent（不是随机噪声！）
- 噪声在 KSampler 内部通过 `prepare_noise()` 添加
- latent dict 只有 `samples` 键

#### VAEEncode（Img2Img 用）
```python
class VAEEncode:
    def encode(self, vae, pixels):
        t = vae.encode(pixels)
        return ({"samples": t}, )
```
- 将 RGB 图片通过 VAE Encoder 压缩到 latent space
- 压缩比 8x（SD 1.5/SDXL）：512×512 → 64×64×4
- latent dict 同样只有 `samples` 键
- KSampler 在采样时会将噪声 **叠加** 到这个编码后的 latent 上

#### 关键区别
```
EmptyLatentImage: zeros(B, 4, H/8, W/8) → KSampler 加全量噪声 → 去噪
VAEEncode:        vae.encode(image)       → KSampler 加部分噪声 → 去噪
```

### 1.4 denoise 值对生成效果的影响

| denoise 范围 | 效果 | 典型用途 |
|---|---|---|
| **0.0 - 0.2** | 几乎无变化，轻微纹理调整 | 微调色调、去除压缩伪影 |
| **0.2 - 0.4** | 保持原图结构，调整细节 | 风格迁移（轻度）、细节增强 |
| **0.4 - 0.6** | 明显变化但保留构图 | 风格迁移（中度）、局部重绘 |
| **0.6 - 0.8** | 大幅重绘，仅保留大致构图 | 创意变体、概念迭代 |
| **0.8 - 1.0** | 接近完全重生成 | 以原图为灵感的全新创作 |

**实践经验总结**：
- **局部修改**（面部微调、颜色调整）：0.2-0.4
- **风格迁移**（保持内容换风格）：0.4-0.6
- **大幅重绘**（几乎重新创作）：0.7-0.9
- **Hi-Res Fix / 迭代放大**：0.3-0.5（经典甜点值 0.4）

### 1.5 Img2Img 工作流拓扑

```
LoadCheckpoint ─┬─ MODEL ──────────────────────── KSampler
                ├─ CLIP ─┬─ CLIPTextEncode(+) ──── positive
                │        └─ CLIPTextEncode(-) ──── negative
                └─ VAE ──── VAEEncode ─────────── latent
                             ↑
LoadImage ───── pixels ──────┘
                                    KSampler ── VAEDecode ── SaveImage
                                    (denoise<1.0)
```

**与 Text2Img 的唯一区别**：用 `LoadImage → VAEEncode` 替代 `EmptyLatentImage`，并将 `denoise` 设为 <1.0。

---

## 2. Inpainting 原理深度解析

### 2.1 核心概念

Inpainting = **局部重绘**。只修改图片中被遮罩（mask）覆盖的区域，保持其余区域不变。

### 2.2 两种 Inpainting 方法

ComfyUI 支持两种截然不同的 inpainting 方式：

#### 方法 A：通用模型 + SetLatentNoiseMask（简单方法）

**原理**：在 latent space 中标记哪些区域需要重新采样。

```python
class SetLatentNoiseMask:
    def set_mask(self, samples, mask):
        s = samples.copy()
        s["noise_mask"] = mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1]))
        return (s,)
```

**采样时的行为**（`KSamplerX0Inpaint.__call__`）：
```python
def __call__(self, x, sigma, denoise_mask, model_options={}, seed=None):
    if denoise_mask is not None:
        latent_mask = 1. - denoise_mask
        # 被 mask 的区域：继续去噪 (denoise_mask=1)
        # 未被 mask 的区域：保持原图 latent (latent_mask=1)
        x = x * denoise_mask + self.latent_image * latent_mask
    out = self.inner_model(x, sigma, ...)
    if denoise_mask is not None:
        # 输出也只在 mask 区域取模型预测，其余保持原样
        out = out * denoise_mask + self.latent_image * latent_mask
    return out
```

**每一步采样都在做**：
1. 把未遮罩区域的 latent 替换回原图编码值
2. 让模型只在遮罩区域做预测
3. 输出时再次确保未遮罩区域不变

**优点**：可以用任何模型
**缺点**：边缘可能不够自然（latent space 拼接）

#### 方法 B：VAEEncodeForInpaint（边缘处理更好）

```python
class VAEEncodeForInpaint:
    def encode(self, vae, pixels, mask, grow_mask_by=6):
        # 1. 对齐到 VAE 压缩比
        downscale_ratio = vae.spacial_compression_encode()
        
        # 2. 扩展 mask（grow_mask_by 像素）确保 latent 边界平滑
        kernel_tensor = torch.ones((1, 1, grow_mask_by, grow_mask_by))
        mask_erosion = torch.clamp(
            torch.nn.functional.conv2d(mask.round(), kernel_tensor, padding=...),
            0, 1
        )
        
        # 3. 将 mask 区域的像素设为灰色（0.5）
        m = (1.0 - mask.round()).squeeze(1)
        for i in range(3):
            pixels[:,:,:,i] -= 0.5
            pixels[:,:,:,i] *= m    # mask 区域乘以 0 → 变成 0
            pixels[:,:,:,i] += 0.5  # 再加 0.5 → 变成 0.5（灰色）
        
        # 4. 编码处理后的图片
        t = vae.encode(pixels)
        
        # 5. 返回带 noise_mask 的 latent
        return ({"samples": t, "noise_mask": mask_erosion.round()}, )
```

**关键设计**：
- `grow_mask_by=6`：通过卷积膨胀 mask 6px，确保 latent space 的边界有过渡
- 将 mask 区域像素设为 0.5（中性灰）：避免 VAE 编码时 mask 区域的颜色信息"泄漏"到 latent
- 自动附加 `noise_mask`：无需额外 SetLatentNoiseMask 节点

#### 方法 C：Inpainting 专用模型 + InpaintModelConditioning（最佳方法）

```python
class InpaintModelConditioning:
    def encode(self, positive, negative, pixels, vae, mask, noise_mask=True):
        # 1. mask 区域设灰
        m = (1.0 - mask.round()).squeeze(1)
        for i in range(3):
            pixels[:,:,:,i] -= 0.5
            pixels[:,:,:,i] *= m
            pixels[:,:,:,i] += 0.5
        
        # 2. 编码两个版本
        concat_latent = vae.encode(pixels)     # 灰色遮罩版（给模型看 mask 信息）
        orig_latent = vae.encode(orig_pixels)  # 原始版（用于采样）
        
        # 3. 将 mask 和遮罩图像注入 conditioning
        for conditioning in [positive, negative]:
            c = conditioning_set_values(conditioning, {
                "concat_latent_image": concat_latent,  # 额外 4 通道
                "concat_mask": mask                     # 额外 1 通道
            })
```

**为什么最强**：
- Inpainting 模型有 **9 个输入通道**（4 原始 latent + 4 遮罩 latent + 1 mask）
- 模型在训练时就学会了如何利用 mask 和周围区域信息
- 边缘融合由模型内部完成，不是后处理拼接

### 2.3 三种方法对比

```
方法                      需要专用模型   边缘质量   灵活性   复杂度
───────────────────────────────────────────────────────────────
SetLatentNoiseMask        ❌            ⭐⭐       ⭐⭐⭐⭐   简单
VAEEncodeForInpaint       ❌            ⭐⭐⭐     ⭐⭐⭐    中等
InpaintModelConditioning  ✅            ⭐⭐⭐⭐⭐  ⭐⭐     最佳
```

### 2.4 Mask 的数据格式

ComfyUI 中 mask 的约定：
- **类型**：MASK（torch.Tensor）
- **形状**：`(H, W)` 或 `(B, H, W)`
- **值域**：0.0（保留）到 1.0（重绘）
- **白色=重绘，黑色=保留**（与 Photoshop 相反！）

mask 来源：
1. `LoadImage` 节点 → 如果图片有 alpha 通道，自动提取为 mask
2. `LoadImageMask` → 从图片的 R/G/B/A 通道提取
3. MaskEditor（右键 LoadImage → Open in MaskEditor）
4. `SolidMask` + `MaskComposite` → 编程方式组合

### 2.5 Mask 相关节点

| 节点 | 功能 |
|---|---|
| `FeatherMask` | 羽化边缘，避免硬切 |
| `InvertMask` | 反转（重绘↔保留） |
| `CropMask` | 裁剪 mask |
| `MaskComposite` | 组合多个 mask（add/subtract/intersect） |
| `ConvertImageToMask` | 从图片通道提取 mask |
| `ConvertMaskToImage` | mask 转图片（预览用） |

### 2.6 遮罩羽化与边缘融合技巧

**grow_mask_by 参数**（VAEEncodeForInpaint 特有）：
- 默认值 6：向外扩展 6 像素
- 作用：在 latent space 中创建过渡区，防止硬边
- 越大 = 融合越柔和 = 影响范围越大

**FeatherMask 节点**：
- 在像素空间羽化 mask 边缘
- 典型值：10-30px（取决于图片分辨率）

**最佳实践**：
1. 先用 MaskEditor 画 mask（略大于要修改的区域）
2. FeatherMask 羽化 20px
3. VAEEncodeForInpaint 的 grow_mask_by 设为 6
4. denoise 设为 0.7-0.9（inpainting 通常需要较高 denoise）

---

## 3. Outpainting 扩展画布

### 3.1 核心原理

Outpainting = 扩展画布后 Inpainting 新区域。本质上是：
1. 将原图放在更大的画布中央（或指定位置）
2. 新扩展的区域标记为 mask
3. 对 mask 区域进行 inpainting

### 3.2 ImagePadForOutpaint 节点源码分析

```python
class ImagePadForOutpaint:
    def expand_image(self, image, left, top, right, bottom, feathering):
        d1, d2, d3, d4 = image.size()  # batch, height, width, channels
        
        # 1. 创建新画布，填充 0.5（中性灰）
        new_image = torch.ones(
            (d1, d2 + top + bottom, d3 + left + right, d4),
            dtype=torch.float32,
        ) * 0.5
        
        # 2. 将原图放入画布
        new_image[:, top:top + d2, left:left + d3, :] = image
        
        # 3. 创建 mask（1=需要重绘的新区域）
        mask = torch.ones((d2 + top + bottom, d3 + left + right))
        t = torch.zeros((d2, d3))  # 原图区域为 0
        
        # 4. 在原图边缘创建羽化过渡
        if feathering > 0:
            # 对原图边缘的像素计算到四边的距离
            # 距离 < feathering 的像素做线性渐变
            v = (feathering - d) / feathering
            t[i][j] = max(v, t[i][j])
        
        # 5. 将处理后的 mask 放入全局 mask
        mask[top:top + d2, left:left + d3] = t
        
        return (new_image, mask)  # 返回扩展图 + mask
```

**关键设计**：
- 新区域填充 0.5（灰色）而不是 0（黑色），因为 VAE 对灰色的编码更"中性"
- 原图边缘的 feathering 确保新旧区域在 inpainting 时平滑过渡
- 返回 IMAGE 和 MASK 两个输出，直接接入 inpainting 工作流

### 3.3 Outpainting 工作流拓扑

```
LoadImage → ImagePadForOutpaint ─┬─ IMAGE ─── VAEEncodeForInpaint ─── KSampler
                                 └─ MASK ────┘                        ↑
LoadCheckpoint ─┬─ MODEL ─────────────────────────────────────────────┘
                ├─ CLIP ─┬─ CLIPTextEncode(+) ── positive
                │        └─ CLIPTextEncode(-) ── negative
                └─ VAE ──── (feed to VAEEncodeForInpaint)
```

### 3.4 Outpainting 的挑战与技巧

**挑战 1：分辨率匹配**
- 扩展后的画布分辨率可能不是模型最优的
- SD 1.5 最优 512×512，SDXL 最优 1024×1024
- 解决方案：先按小尺寸生成，再用 img2img 放大

**挑战 2：构图一致性**
- 模型不一定能理解扩展方向的语义
- 解决方案：prompt 中明确描述完整场景，denoise 用 0.8-1.0

**挑战 3：重复模式**
- 大面积扩展容易出现重复纹理
- 解决方案：分多次小步扩展，每次只扩展 128-256px

**最佳实践**：
1. 每次只向一个方向扩展
2. feathering 设为 40-60（像素级，对 512 图来说）
3. 使用 inpainting 专用模型
4. denoise 0.8-1.0（新区域需要完全生成）
5. prompt 描述完整场景而不只是新区域

---

## 4. 实践经验总结

### 4.1 Img2Img 参数速查

```
任务                    denoise    steps    CFG    推荐采样器
────────────────────────────────────────────────────────
微调色调/去伪影          0.15-0.25  15-20   5-7    euler
风格迁移（轻）           0.35-0.45  20-25   7-9    dpmpp_2m
风格迁移（重）           0.55-0.65  20-30   7-9    dpmpp_2m_sde
Hi-Res Fix 放大          0.35-0.45  15-20   7      dpmpp_2m
创意变体                 0.70-0.85  25-30   7-9    dpmpp_sde
```

### 4.2 Inpainting 参数速查

```
任务                    denoise    grow_mask   推荐方法
──────────────────────────────────────────────────────
修补小瑕疵              0.5-0.7    4-6         VAEEncodeForInpaint
面部修复                0.6-0.8    6-8         InpaintModelConditioning
物体替换                0.8-1.0    6-10        InpaintModelConditioning
背景替换                0.9-1.0    8-12        InpaintModelConditioning
```

### 4.3 工作流选择决策树

```
需要修改图片？
├── 全图修改 → Img2Img
│   ├── 轻度调整 → denoise 0.2-0.4
│   └── 大幅重绘 → denoise 0.6-0.9
├── 局部修改 → Inpainting
│   ├── 有 inpainting 专用模型 → InpaintModelConditioning
│   └── 只有通用模型 → VAEEncodeForInpaint
└── 扩展画布 → Outpainting
    └── ImagePadForOutpaint → VAEEncodeForInpaint → KSampler
```

---

## 5. 源码关键发现

### 5.1 noise_mask 在整个管线中的传递

```
SetLatentNoiseMask / VAEEncodeForInpaint
    ↓ latent["noise_mask"]
common_ksampler()
    ↓ noise_mask = latent["noise_mask"]
comfy.sample.sample()
    ↓ noise_mask → denoise_mask
KSampler.sample()
    ↓ denoise_mask
sampler_object.sample()  (具体采样器)
    ↓ 每步调用 KSamplerX0Inpaint.__call__()
        → x = x * denoise_mask + latent_image * (1 - denoise_mask)
        → out = model(x)
        → out = out * denoise_mask + latent_image * (1 - denoise_mask)
```

### 5.2 denoise_mask 的处理

- `denoise_mask` 中 **1 = 重绘区域**，**0 = 保留区域**
- 每一步采样都会"混合"——这不是简单的裁剪再拼贴
- 模型能"看到"未遮罩区域的信息（作为上下文），但只在遮罩区域做预测
- 这就是为什么 inpainting 能保持语义一致性

### 5.3 VAEEncodeForInpaint 的灰色技巧

将 mask 区域设为 0.5 的原因：
1. VAE 编码时，0.5 对应 latent space 的"零点"附近
2. 如果用黑色（0），VAE 会编码出偏暗的 latent，影响 inpainting 质量
3. 灰色是最"中性"的值，让 mask 区域的 latent 信息含量最小

---

## 文件索引

- 笔记：`notes/day05-img2img-inpainting-outpainting.md`（本文件）
- 工作流：
  - `sample-workflows/basic/img2img.json` — 基础 Img2Img 工作流
  - `sample-workflows/basic/inpainting-simple.json` — SetLatentNoiseMask 方法
  - `sample-workflows/basic/inpainting-vae.json` — VAEEncodeForInpaint 方法
  - `sample-workflows/basic/outpainting.json` — 基础 Outpainting 工作流
  - `sample-workflows/experiments/denoise-comparison.json` — denoise 值对比实验
