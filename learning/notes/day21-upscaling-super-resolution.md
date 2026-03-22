# Day 21: 超分辨率与图像增强深度解析

> 学习时间: 2026-03-22 08:03 UTC | 轮次: 29

## 1. 超分辨率技术全景

### 1.1 两类根本不同的放大方式

在 ComfyUI 中，图像放大分为两大类：

**传统插值放大（Pixel Upscale）**
- 节点：`ImageScale` / `ImageScaleBy`
- 方法：nearest / bilinear / bicubic / lanczos / area
- 原理：基于像素邻域的数学插值
- 特点：快速但无法生成新细节，只是模糊放大
- 用途：中间尺寸调整、Latent 空间预处理

**AI 模型放大（Model Upscale）**
- 节点：`UpscaleModelLoader` + `ImageUpscaleWithModel`
- 模型：ESRGAN / SwinIR / HAT 等
- 原理：深度学习网络从低分辨率重建高频细节
- 特点：能"幻觉"出合理的细节纹理
- 用途：最终输出的质量增强

**SD 重绘放大（SD Upscale / Hires Fix）**
- 节点：Ultimate SD Upscale / Tile ControlNet + KSampler
- 原理：将放大后的图像通过 Stable Diffusion 重新采样添加细节
- 特点：可以添加全新的语义细节，质量最高但最慢
- 用途：高端出图、专业级放大

### 1.2 技术发展时间线

```
2018 — ESRGAN (GAN训练, RRDB块)
2021 — Real-ESRGAN (真实世界退化建模)
2021 — SwinIR (Swin Transformer引入SR)
2022 — Swin2SR (Swin Transformer V2)
2023 — HAT (Hybrid Attention Transformer, 新SOTA)
2023 — StableSR (利用SD先验做超分)
2024 — DAT (Dual Aggregation Transformer)
2024 — PMRF (Flow-based, 极速2x)
2025 — SPAN (轻量级, 效率SOTA)
```

## 2. ComfyUI 超分源码深度分析

### 2.1 Spandrel — ComfyUI 的模型加载统一层

ComfyUI 通过 **spandrel** 库统一加载所有超分模型。这是关键设计：

```python
# comfy_extras/nodes_upscale_model.py 核心代码
from spandrel import ModelLoader, ImageModelDescriptor

class UpscaleModelLoader:
    def execute(cls, model_name):
        model_path = folder_paths.get_full_path_or_raise("upscale_models", model_name)
        sd = comfy.utils.load_torch_file(model_path, safe_load=True)
        
        # 特殊处理：某些模型有 "module." 前缀
        if "module.layers.0.residual_group.blocks.0.norm1.weight" in sd:
            sd = comfy.utils.state_dict_prefix_replace(sd, {"module.":""})
        
        # Spandrel 自动检测架构！
        out = ModelLoader().load_from_state_dict(sd).eval()
        
        if not isinstance(out, ImageModelDescriptor):
            raise Exception("Upscale model must be a single-image model.")
        return io.NodeOutput(out)
```

**Spandrel 的魔法**: 它通过分析 state_dict 的 key 名称和张量形状，自动识别模型架构（ESRGAN/SwinIR/HAT等）。这就是为什么你只需把 .pth 文件放入 upscale_models/ 目录就能用。

**支持的架构列表**（截至 2025）：
| 架构 | 类型 | 关键特点 |
|------|------|---------|
| ESRGAN (RRDBNet) | GAN | 经典, 社区模型最多 |
| Real-ESRGAN Compact (SRVGGNet) | GAN | 轻量版, 适合实时 |
| SwinIR | Transformer | 纹理保真度最高 |
| Swin2SR | Transformer | SwinIR改进版 |
| HAT | Hybrid Attention | 当前学术SOTA |
| DAT | Dual Aggregation | 2024新架构 |
| SPAN | 轻量级 | 效率SOTA |
| OmniSR / SRFormer / GRL / DITN / MM-RealSR | 各类 | 小众但特定场景优 |

### 2.2 ImageUpscaleWithModel — 分块处理核心

```python
class ImageUpscaleWithModel:
    def execute(cls, upscale_model, image):
        device = model_management.get_torch_device()
        
        # 内存估算（关键！）
        memory_required = model_management.module_size(upscale_model.model)
        memory_required += (512 * 512 * 3) * image.element_size() * max(upscale_model.scale, 1.0) * 384.0
        # ↑ 384.0 是经验系数，估算中间激活的内存
        memory_required += image.nelement() * image.element_size()
        model_management.free_memory(memory_required, device)
        
        upscale_model.to(device)
        in_img = image.movedim(-1,-3).to(device)  # NHWC → NCHW
        
        tile = 512      # 初始分块大小
        overlap = 32    # 重叠区域防接缝
        
        # OOM 自动降级机制！
        oom = True
        while oom:
            try:
                steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(
                    in_img.shape[3], in_img.shape[2], 
                    tile_x=tile, tile_y=tile, overlap=overlap)
                pbar = comfy.utils.ProgressBar(steps)
                s = comfy.utils.tiled_scale(
                    in_img, 
                    lambda a: upscale_model(a),  # 模型推理
                    tile_x=tile, tile_y=tile, 
                    overlap=overlap, 
                    upscale_amount=upscale_model.scale,
                    pbar=pbar)
                oom = False
            except Exception as e:
                model_management.raise_non_oom(e)
                tile //= 2         # OOM → 减半分块
                if tile < 128:     # 最小128, 否则放弃
                    raise e
        
        upscale_model.to("cpu")  # 推理后释放GPU
        s = torch.clamp(s.movedim(-3,-1), min=0, max=1.0)  # NCHW → NHWC, 裁剪[0,1]
        return io.NodeOutput(s)
```

**关键设计要点**:
1. **分块处理 (Tiling)**: 默认 512x512 分块，32px 重叠，防止接缝
2. **OOM 自动降级**: 内存不足时自动减半分块大小（512→256→128）
3. **内存管理**: 推理前估算+释放，推理后模型回 CPU
4. **进度条**: 通过 ProgressBar 显示分块进度

### 2.3 tiled_scale 函数 — 分块放大的数学

`comfy.utils.tiled_scale` 的核心逻辑：
1. 将输入图像按 tile_x × tile_y 网格分块
2. 每块扩展 overlap 像素（防边缘伪影）
3. 对每块独立调用模型推理
4. 输出块按重叠区域加权混合（渐变融合）
5. 拼接成最终大图

**重叠融合权重**: 重叠区域使用线性渐变权重，从边缘到中心 0→1，确保分块边界无缝。

### 2.4 ImageScale / ImageScaleBy — 传统插值

ComfyUI 内置的传统放大节点直接调用 PyTorch 的 `torch.nn.functional.interpolate`:

```
方法对比：
nearest    — 最快, 最锯齿, 适合像素艺术
bilinear   — 快, 略模糊, 通用
bicubic    — 稍慢, 更平滑, 推荐默认
lanczos    — 最慢, 最锐利, 最高质量插值
area       — 适合缩小, 抗锯齿好
```

## 3. 超分模型架构深度对比

### 3.1 ESRGAN 系列（GAN-based）

**ESRGAN (2018)**
- 架构：RRDB (Residual in Residual Dense Block)
- 训练：L1 Loss + Perceptual Loss + GAN Loss
- 参数：~16M (4x)
- 特点：锐利、细节丰富，但可能引入伪影

**Real-ESRGAN (2021)**
- 改进：高阶退化建模（模糊→噪声→压缩→再退化）
- 架构：同 RRDB，但训练数据更真实
- 变体：x4plus（通用）/ x4plus_anime（动漫）/ x2plus（2x）

**社区 ESRGAN 模型生态**（通过 OpenModelDB）：
```
4x-UltraSharp     — 社区最受欢迎, 极度锐利, 适合人像/产品
4x-Remacri        — 自然纹理好, 不过度锐化
4x-NMKD-Siax      — 平衡选手, 适合多数场景
4x-AnimeSharp      — 动漫线条优化
4x-Nomos8kSCHAT-L  — 8K训练, 极端锐利
RealESRGAN_x4plus  — 官方通用模型
```

### 3.2 SwinIR（Transformer-based, 2021）

**架构**:
```
Input → Shallow Feature Extraction (Conv3x3)
     → Deep Feature Extraction (N × RSTB)
         RSTB = Residual Swin Transformer Block
              = 多个 STL (Swin Transformer Layer)
              + Conv + Residual Connection
     → Image Reconstruction (Conv + PixelShuffle)
```

**核心创新**: 将 Swin Transformer 的窗口自注意力引入超分
- Window size: 通常 8×8
- Shifted window: 跨窗口信息交互
- 相对位置偏置: 位置感知

**优势**: 纹理自然、不过度锐化、细节保真
**劣势**: 比 ESRGAN 慢 2-3x

### 3.3 HAT（Hybrid Attention Transformer, 2023）

**当前学术 SOTA**:
- Channel Attention + Window Self-Attention + 跨窗口注意力
- Overlapping Cross-Attention Block (OCAB)
- 在多个基准测试上超越 SwinIR

**变体**: HAT / HAT-L / HAT-S (大/中/小)

### 3.4 模型选择决策树

```
需要什么？
├─ 极速 → Real-ESRGAN Compact (SRVGGNet) / SPAN
├─ 平衡速质 → 4x-UltraSharp / Remacri (ESRGAN)
├─ 自然纹理 → SwinIR / 4x-NMKD-Siax
├─ 最高质量 → HAT-L / StableSR (极慢)
├─ 动漫 → 4x-AnimeSharp / Real-ESRGAN anime
├─ 人脸 → GFPGAN + ESRGAN / FaceDetailer
└─ 视频帧 → Real-ESRGAN Compact (速度优先)
```

## 4. ComfyUI 超分工作流模式

### 4.1 模式一：纯模型放大（Simple Upscale）

```
LoadImage → UpscaleModelLoader → ImageUpscaleWithModel → SaveImage
```

最简单的工作流，适合后期处理。2-3 节点完成。

### 4.2 模式二：生成+放大流水线（Generate + Upscale）

```
CheckpointLoader → KSampler → VAEDecode → ImageUpscaleWithModel → SaveImage
```

文生图后直接接超分，一步到位。

### 4.3 模式三：Hires Fix（高分辨率修复）

这是最重要的高级模式：

```
Stage 1: 低分辨率生成
  CheckpointLoader → EmptyLatentImage(512x512) → KSampler → VAEDecode
  
Stage 2: 放大 + 重编码 + 重采样
  → ImageScale(bicubic, 2x) [或 ESRGAN 放大]
  → VAEEncode 
  → KSampler(denoise=0.4-0.6)  ← 关键: 低 denoise 保持构图
  → VAEDecode → SaveImage
```

**核心原理**: 
1. 先在小尺寸快速出图（构图/色彩正确）
2. 放大到目标尺寸
3. 用低 denoise 重采样添加高频细节
4. 得到大尺寸+丰富细节的图像

**denoise 值对放大的影响**:
```
0.2-0.3 — 极保守, 几乎只增强纹理
0.4-0.5 — 推荐, 添加细节同时保持构图  
0.5-0.6 — 较激进, 可能改变小细节
0.7+    — 危险, 会大幅改变图像内容
```

### 4.4 模式四：Tile ControlNet 超分（最高质量）

```
LoadImage 
  → ESRGAN 4x 预放大 (像素级)
  → ControlNetLoader(tile_v11) 
  → ControlNetApply(image=原图 or 放大图, strength=0.5-1.0)
  → KSampler(steps=20, denoise=0.4)
  → SaveImage
```

**Tile ControlNet 的作用**: 
- 使 SD 在重采样时参考原图的局部结构
- 防止 Hires Fix 中高 denoise 导致的内容偏移
- 在添加细节的同时保持忠实于原图

### 4.5 模式五：Ultimate SD Upscale（分块SD放大）

来自社区节点 `ComfyUI_UltimateSDUpscale`：

```
原理：
1. ESRGAN 先放大到目标尺寸（纯像素级）
2. 将大图分成 tile（如 512x512 块）
3. 每个 tile 独立经过 KSampler 重绘
4. 所有 tile 拼接回大图

优势：
- 可以处理任意大尺寸（不受 VRAM 限制）
- 每个分块都能获得完整的 SD 细节增强
- 支持 ControlNet Tile 进一步控制

参数：
- tile_width / tile_height: 分块大小（通常 512 或 1024）
- padding: 分块重叠（防接缝, 通常 32-64）
- seam_fix_mode: 接缝修复方式（half_tile / band / none）
- denoise: 同 Hires Fix
- upscale_by: 放大倍率
```

### 4.6 模式六：Latent 放大（Latent Upscale）

```
EmptyLatentImage(512x512) → KSampler 
  → LatentUpscale(1024x1024) [或 LatentUpscaleBy(2x)]
  → KSampler(denoise=0.5)
  → VAEDecode → SaveImage
```

**在 Latent 空间直接放大**: 
- `LatentUpscale`: bicubic 插值 latent tensor
- 优势：不需要 VAE 编解码循环
- 劣势：latent 空间插值质量不如 pixel 空间

## 5. 人脸修复与细节增强

### 5.1 人脸修复模型

**CodeFormer (2022)**
- 架构：Transformer + CodeBook (离散化人脸先验)
- 特点：通过 fidelity 参数控制修复-保真平衡
- fidelity=0.0 → 完全修复（可能改变面貌）
- fidelity=1.0 → 完全保真（修复效果弱）
- 推荐：fidelity=0.5-0.7

**GFPGAN (2021)**
- 架构：GAN + 通道注意力 + 预训练人脸先验
- 特点：更激进的修复，人脸更清晰但可能失真

**ComfyUI 人脸修复节点**: `FaceRestoreCFWithModel`
- 来自 `facerestore_cf` 自定义节点
- 支持 CodeFormer + GFPGAN
- 自动检测人脸 → 裁剪 → 修复 → 贴回

### 5.2 FaceDetailer（Impact Pack）

**FaceDetailer** 是 ComfyUI Impact Pack 中最实用的节点之一：

```
工作原理（4步）:
1. BBOX Detect — 用 Ultralytics YOLO 检测人脸边界框
2. Crop — 按 crop_factor 倍率裁剪人脸区域
3. Inpaint/Redraw — 用 SD 重绘裁剪区域（独立 KSampler）
4. Paste Back — 将增强的人脸贴回原图（feather 混合）
```

**关键参数**:
```
bbox_detector     — 人脸检测模型 (ultralytics/face_yolov8n 等)
guide_size        — 目标裁剪尺寸 (384/512/768)
guide_size_for    — 基于 bbox 还是 crop region
max_size          — 最大处理尺寸
denoise           — 重绘强度 (0.3-0.5 推荐)
feather           — 贴回时的羽化像素
crop_factor       — 裁剪倍率 (默认3.0, 包含更多上下文)
dilation          — 扩展检测区域
```

**工作流示例**:
```
CheckpointLoader → KSampler → VAEDecode 
  → FaceDetailer(
      bbox_detector=face_yolov8n,
      denoise=0.4,
      guide_size=512,
      crop_factor=3.0)
  → SaveImage
```

### 5.3 CropAndStitch 替代方案（2025 社区趋势）

社区发现手动 Crop + Inpaint + Stitch 比 FaceDetailer 更灵活：
```
优势:
- 可以手动选择要修复的人脸
- 不依赖检测器的准确性
- 可以用 REACTOR 换脸后再贴回
- CropAndStitch 速度极快

流程:
LoadImage → CropRegion(手动指定区域)
  → KSampler(denoise=0.3-0.5) 
  → StitchBack(原图, feather=16)
```

## 6. 完整超分管线最佳实践

### 6.1 推荐的三阶段超分管线

```
Stage 1: AI 模型预放大 (4x)
  输入 512x512 → ESRGAN/UltraSharp → 输出 2048x2048
  [纯像素级, 快速, 为 Stage 2 提供基础]

Stage 2: SD 重采样增强 (denoise=0.3-0.5)
  2048x2048 → VAEEncode → KSampler + Tile ControlNet → VAEDecode
  [添加语义级细节, 纹理更丰富]

Stage 3: 人脸/局部修复 (可选)
  → FaceDetailer (人脸)
  → CodeFormer (面部质量)
  → 色彩校正 / 锐化
```

### 6.2 分辨率规划表

```
目标    | Stage 1 (生成)  | Stage 2 (放大)    | 方法
1080p   | 540x960        | 1080x1920         | ESRGAN 2x
2K      | 512x512        | 2048x2048         | ESRGAN 4x
4K      | 1024x1024      | 4096x4096         | ESRGAN 2x + SD Upscale
8K      | 1024x1024      | 8192x8192         | ESRGAN 4x + 分块SD Upscale
```

### 6.3 常见问题诊断

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 分块接缝可见 | overlap 太小 | 增加 overlap 到 64+ |
| 过度锐化/伪影 | ESRGAN 模型太激进 | 换 SwinIR 或 Remacri |
| 人脸模糊 | 未做人脸修复 | 添加 FaceDetailer 或 CodeFormer |
| 色彩偏移 | VAE 编解码漂移 | 添加色彩校正节点 |
| OOM 错误 | 图片太大 | 用 Ultimate SD Upscale 分块 |
| 细节重复/纹理异常 | Hires Fix denoise 太高 | 降低到 0.3-0.4 |
| 棋盘格伪影 | 某些模型的 PixelShuffle 问题 | 换模型或后处理平滑 |

## 7. RunningHub 实验

### 实验 #32: Topaz Standard V2 放大

- **输入**: 1024x1024 老匠人肖像
- **模型**: topazlabs/image-upscale-standard-v2
- **输出**: 2048x2048 (2x放大)
- **耗时**: 20s
- **成本**: ¥0.10
- **分析**: Standard V2 适合通用场景，锐化程度适中

### 实验 #33: Topaz High Fidelity V2 放大

- **输入**: 同一张 1024x1024 肖像
- **模型**: topazlabs/image-upscale-high-fidelity-v2
- **输出**: 2048x2048 (2x放大)
- **耗时**: 20s
- **成本**: ¥0.10
- **分析**: High Fidelity 版本更注重保持原始细节，锐化更保守

### Topaz Standard vs High Fidelity 对比

| 维度 | Standard V2 | High Fidelity V2 |
|------|------------|-------------------|
| 锐度 | 较高 | 适中 |
| 保真 | 中等 | 高 |
| 伪影 | 可能轻微 | 极少 |
| 适用 | 网页/社交媒体 | 印刷/专业 |
| 成本 | ¥0.10 | ¥0.10 |

## 8. 工作流 JSON 示例

### 8.1 三阶段超分工作流概念

```json
{
  "workflow_concept": "three-stage-upscale",
  "stages": [
    {
      "name": "ESRGAN Pre-upscale",
      "nodes": ["UpscaleModelLoader(4x-UltraSharp)", "ImageUpscaleWithModel"],
      "input": "512x512",
      "output": "2048x2048"
    },
    {
      "name": "SD Hires Fix",
      "nodes": ["VAEEncode", "KSampler(denoise=0.4)", "ControlNet(tile)", "VAEDecode"],
      "input": "2048x2048 latent",
      "output": "2048x2048 enhanced"
    },
    {
      "name": "Face Restoration",
      "nodes": ["FaceDetailer(denoise=0.3)", "FaceRestoreCF(CodeFormer, fidelity=0.6)"],
      "input": "enhanced image",
      "output": "final image"
    }
  ]
}
```

## 9. 总结与决策框架

### 快速决策

```
问: 我应该用什么超分方案？

只需放大, 不需新细节？ → ESRGAN (4x-UltraSharp)
需要添加细节？ → Hires Fix (ESRGAN + KSampler denoise=0.4)
最高质量, 不在乎速度？ → Ultimate SD Upscale + Tile ControlNet
人脸模糊？ → + FaceDetailer
动漫图？ → 4x-AnimeSharp
视频帧批量？ → Real-ESRGAN Compact (速度)
打印/专业用途？ → 三阶段管线
```

### 速度 vs 质量坐标

```
速度 ←————————————————————→ 质量
  |                              |
  ESRGAN Compact (1s)            StableSR (5min)
     Real-ESRGAN (6s)         HAT-L (20s)
        4x-UltraSharp (6s)  SwinIR (12s)
           Hires Fix (30s)
              Ultimate SD Upscale (2min)
                 Tile CN + SD (3min)
```
