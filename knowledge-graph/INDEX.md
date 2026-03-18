# 知识图谱总索引

> 需求 → 节点组合 → 工作流，一图打尽

## 需求→工作流 快速映射

| 需求 | 核心节点 | 工作流 | 难度 |
|------|---------|--------|------|
| 文字生图 | CheckpointLoader → CLIPTextEncode → KSampler → VAEDecode | `basic/text2img.json` | ⭐ |
| 图片风格转换 | LoadImage → VAEEncode → KSampler(denoise<1) → VAEDecode | `basic/img2img.json` | ⭐ |
| 局部重绘 | LoadImage + MaskEditor → SetLatentNoiseMask → KSampler | `basic/inpaint.json` | ⭐⭐ |
| 姿势控制 | ControlNetLoader + OpenPose → Apply ControlNet → KSampler | `controlnet/pose.json` | ⭐⭐ |
| 边缘控制 | Canny → ControlNetApply → KSampler | `controlnet/canny.json` | ⭐⭐ |
| 深度控制 | DepthMap → ControlNetApply → KSampler | `controlnet/depth.json` | ⭐⭐ |
| 风格迁移 | IP-Adapter → KSampler | `controlnet/ip-adapter.json` | ⭐⭐⭐ |
| LoRA 风格 | LoRALoader → 插入 MODEL/CLIP 链路 | `lora/single-lora.json` | ⭐⭐ |
| 多 LoRA 叠加 | 多个 LoRALoader 串联 | `lora/multi-lora.json` | ⭐⭐⭐ |
| SDXL 高质量 | SDXL Base → Refiner 二阶段 | `advanced/sdxl-refiner.json` | ⭐⭐⭐ |
| 视频生成 | AnimateDiff / SVD 节点链 | `video/animatediff.json` | ⭐⭐⭐⭐ |
| 图片放大 | Upscale Model + VAE Tiled | `advanced/upscale.json` | ⭐⭐ |

## 核心节点分类

### 模型加载
- `CheckpointLoaderSimple` — 加载完整 checkpoint（MODEL+CLIP+VAE）
- `LoraLoader` — 加载 LoRA 微调权重
- `ControlNetLoader` — 加载 ControlNet 模型
- `VAELoader` — 单独加载 VAE（替代 checkpoint 自带的）

### 文本编码
- `CLIPTextEncode` — prompt → CONDITIONING
- `CLIPTextEncodeSDXL` — SDXL 专用双编码
- `ConditioningCombine` — 合并多个条件
- `ConditioningSetArea` — 区域条件（不同区域不同 prompt）

### 采样
- `KSampler` — 核心采样器（sampler + scheduler + steps + cfg）
- `KSamplerAdvanced` — 高级版（支持 start/end step 控制）
- `SamplerCustom` — 完全自定义采样流程

### 图像处理
- `VAEEncode` / `VAEDecode` — 像素↔潜空间
- `LoadImage` — 加载输入图像
- `SaveImage` / `PreviewImage` — 输出
- `ImageScale` / `ImageUpscaleWithModel` — 放大

### 潜空间操作
- `EmptyLatentImage` — 创建空白潜空间（txt2img 起点）
- `LatentUpscale` — 潜空间放大
- `SetLatentNoiseMask` — 设置 inpaint 遮罩

（持续补充中...）
