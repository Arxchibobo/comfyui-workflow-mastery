# 模型兼容性表

本文档列出了 ComfyUI 中各类模型的兼容性和推荐配置。

## 基础模型分类

### Stable Diffusion 1.5 系列
**分辨率**: 512x512
**VAE**: vae-ft-mse-840000-ema-pruned.safetensors
**CLIP**: 单 CLIP 模型
**采样器推荐**: euler, dpmpp_2m
**CFG 推荐**: 7-8

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| v1-5-pruned-emaonly-fp16.safetensors | Checkpoint | 标准 SD1.5 | 通用文生图 |
| deliberate_v2.safetensors | Checkpoint | 写实风格 | 人像、风景 |
| dreamshaper_8.safetensors | Checkpoint | 梦幻风格 | 艺术创作 |

### SDXL 系列
**分辨率**: 1024x1024
**VAE**: sdxl_vae.safetensors
**CLIP**: 双 CLIP 模型 (clip_l + clip_g)
**采样器推荐**: dpmpp_2m, euler
**CFG 推荐**: 6-8

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| sd_xl_base_1.0.safetensors | Checkpoint | SDXL 基础模型 | 高分辨率生成 |
| juggernautXL_v8Rundiffusion.safetensors | Checkpoint | 写实风格 | 商业级图像 |
| dreamshaperXL_v21TurboDPMSDE.safetensors | Checkpoint | 快速生成 | 概念验证 |

### SD3 系列
**分辨率**: 1024x1024
**VAE**: sd3_vae.safetensors
**CLIP**: 双 CLIP + T5 文本编码器
**采样器推荐**: dpmpp_2m
**CFG 推荐**: 5-7

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| sd3_medium.safetensors | Checkpoint | SD3 中等模型 | 文本理解增强 |
| sd3.5_large.safetensors | Checkpoint | SD3.5 大模型 | 最高质量 |

### Flux 系列
**分辨率**: 1024x1024 或更高
**VAE**: ae.safetensors
**CLIP**: 双 CLIP (clip_l + t5xxl)
**采样器推荐**: euler
**CFG 推荐**: 1.0 (Flux 使用特殊 CFG)

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| flux1-dev-fp8.safetensors | UNET | Flux Dev 版本 | 开发测试 |
| flux1-schnell-fp8.safetensors | UNET | 快速版本 | 实时生成 |
| flux.2-dev.safetensors | UNET | Flux 2.0 Dev | 最新特性 |

### Z-Image 系列
**分辨率**: 1024x1024
**特点**: 极速生成（1-4 步）
**采样器推荐**: euler
**CFG 推荐**: 1.0-2.0

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| z-image-turbo.safetensors | Checkpoint | 超快生成 | 快速原型 |
| z-image.safetensors | Checkpoint | 标准版本 | 质量平衡 |

---

## 图像编辑模型

### Qwen Image Edit 系列
**输入**: 原图 + 文本指令
**分辨率**: 支持多种分辨率
**特点**: 指令式编辑

| 模型名称 | 版本 | 特点 | 推荐用途 |
|---------|------|------|---------|
| qwen-image-edit-2509 | 2024.09 | 基础编辑 | 通用图像编辑 |
| qwen-image-edit-2511 | 2024.11 | 增强版 | 复杂编辑任务 |
| qwen-image-edit-2512 | 2024.12 | 最新版 | 最佳编辑效果 |

### FireRed 系列
**输入**: 原图 + 编辑描述
**特点**: 高保真编辑

| 模型名称 | 版本 | 特点 | 推荐用途 |
|---------|------|------|---------|
| firered-image-edit-1.1 | 1.1 | 精准编辑 | 产品图编辑 |

### Seedream 系列 
**输入**: 原图 + 编辑提示
**特点**: 创意编辑

| 模型名称 | 版本 | 特点 | 推荐用途 |
|---------|------|------|---------|
| seedream-4.0 | 4.0 | 创意编辑 | 艺术创作 |
| seedream-5.0-lite | 5.0 | 轻量版 | 快速编辑 |

---

## 视频生成模型

### Wan2.2 系列
**输入类型**: 图生视频 (I2V) + 文生视频 (T2V)
**分辨率**: 720p, 1080p
**帧率**: 8 fps
**最大长度**: 8 秒

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| wan2.2-14B-i2v | I2V | 图像到视频 | 静图动画化 |
| wan2.2-14B-t2v | T2V | 文本到视频 | 视频生成 |
| wan2.2-animate | 特化 | 角色动画 | 人物动作 |

### LTX-2.3 系列
**输入类型**: I2V + T2V + 唇同步
**分辨率**: 多种分辨率支持
**帧率**: 可调节

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| ltx-2.3-i2v | I2V | 图生视频 | 高质量转换 |
| ltx-2.3-t2v | T2V | 文生视频 | 原创视频 |
| ltx-2.3-ia2v | 音频同步 | 唇同步 | 说话视频 |

### Kling 3.0 系列
**特点**: 动作控制 + 高质量
**分辨率**: 1080p
**特殊功能**: 精确动作控制

| 模型名称 | 类型 | 特点 | 推荐用途 |
|---------|------|------|---------|
| kling-v3-video | 综合 | 全功能视频生成 | 专业视频制作 |
| kling-motion-control3 | 动作控制 | 精确动作 | 特定动作生成 |

### Seedance 系列
**特点**: 舞蹈视频专门
**输入**: 图像 + 动作参考

| 模型名称 | 版本 | 特点 | 推荐用途 |
|---------|------|------|---------|
| seedance-1.5 | 1.5 | 舞蹈生成 | 舞蹈视频制作 |

---

## ControlNet 模型

### 通用 ControlNet
适用于 SD1.5、SDXL 等基础模型

| 控制类型 | 模型文件 | 预处理器 | 用途 |
|---------|---------|---------|------|
| Canny | control_v11p_sd15_canny.pth | Canny | 边缘控制 |
| OpenPose | control_v11p_sd15_openpose.pth | DWPreprocessor | 姿态控制 |
| Depth | control_v11f1p_sd15_depth.pth | DepthAnything V2 | 深度控制 |
| LineArt | control_v11p_sd15_lineart.pth | LineArt | 线稿控制 |
| Scribble | control_v11p_sd15_scribble.pth | Scribble | 涂鸦控制 |
| Segmentation | control_v11p_sd15_seg.pth | Segmentation | 分割控制 |

### SDXL ControlNet
| 控制类型 | 模型文件 | 预处理器 | 用途 |
|---------|---------|---------|------|
| Canny | controlnet-canny-sdxl-1.0.safetensors | Canny | SDXL 边缘控制 |
| OpenPose | controlnet-openpose-sdxl-1.0.safetensors | DWPreprocessor | SDXL 姿态控制 |
| Depth | controlnet-depth-sdxl-1.0.safetensors | DepthAnything V2 | SDXL 深度控制 |

---

## IP-Adapter 模型

### 基础 IP-Adapter
| 模型名称 | 兼容模型 | 用途 | 权重范围 |
|---------|---------|------|---------|
| ip-adapter_sd15.safetensors | SD1.5 | 风格迁移 | 0.5-1.5 |
| ip-adapter-plus_sd15.safetensors | SD1.5 | 增强风格 | 0.5-1.5 |
| ip-adapter_sdxl_vit-h.safetensors | SDXL | SDXL 风格 | 0.5-1.5 |

### Face ID 专用
| 模型名称 | 兼容模型 | 用途 | 特点 |
|---------|---------|------|------|
| ip-adapter-faceid_sd15.bin | SD1.5 | 面部保持 | 人脸一致性 |
| ip-adapter-faceid-plus_sd15.bin | SD1.5 | 增强面部 | 更好细节 |
| ip-adapter-faceid_sdxl.bin | SDXL | SDXL 面部 | 高分辨率面部 |

---

## 超分辨率模型

### Real-ESRGAN 系列
| 模型名称 | 倍率 | 特点 | 适用场景 |
|---------|------|------|---------|
| RealESRGAN_x4plus.pth | 4x | 通用超分 | 自然图像 |
| RealESRGAN_x4plus_anime_6B.pth | 4x | 动漫超分 | 动漫风格 |
| RealESRGAN_x2plus.pth | 2x | 快速超分 | 轻度放大 |

### ESRGAN 系列
| 模型名称 | 倍率 | 特点 | 适用场景 |
|---------|------|------|---------|
| ESRGAN_4x.pth | 4x | 经典超分 | 通用放大 |
| ESRGAN_PSNR_4x.pth | 4x | 高 PSNR | 保真度优先 |

---

## API 服务模型

### Grok 系列
**提供商**: xAI
**功能**: 图像生成 + 图像编辑 + 视频生成

| API 类型 | 输入 | 输出 | 特点 |
|---------|------|------|------|
| grok-text-to-image | 文本提示 | 图像 | 高质量文生图 |
| grok-image-edit | 图像 + 编辑指令 | 图像 | 智能图像编辑 |
| grok-video | 文本/图像 | 视频 | 视频生成 |

### Gemini 系列
**提供商**: Google
**功能**: 图像生成 + 图像编辑

| API 类型 | 输入 | 输出 | 特点 |
|---------|------|------|------|
| gemini-image | 文本提示 | 图像 | Google 图像生成 |
| nano-banana-pro | 文本/图像 | 图像 | Gemini 3 Pro 版本 |

### ByteDance 系列
**提供商**: 字节跳动
**功能**: 图像编辑 + 视频生成

| API 类型 | 输入 | 输出 | 特点 |
|---------|------|------|------|
| seedream-5.0-lite | 图像 + 编辑提示 | 图像 | 轻量编辑 |
| seedance-1.5 | 图像 + 动作 | 视频 | 舞蹈视频 |

---

## 硬件要求

### 内存需求
| 模型类型 | 最小 VRAM | 推荐 VRAM | 备注 |
|---------|-----------|-----------|------|
| SD1.5 | 4GB | 6GB | 基础文生图 |
| SDXL | 8GB | 12GB | 高分辨率 |
| SD3 | 12GB | 16GB | 最新架构 |
| Flux | 16GB | 24GB | 大型模型 |
| 视频模型 | 16GB | 24GB+ | 时序处理 |

### 优化建议
1. **FP16/FP8**: 使用半精度模型减少内存占用
2. **模型卸载**: 不同步骤间卸载不用的模型
3. **批次处理**: 合理设置 batch_size
4. **分片处理**: 大尺寸图像分块处理
5. **模型量化**: 使用量化版本模型

---

## 兼容性矩阵

### VAE 兼容性
| VAE 模型 | SD1.5 | SDXL | SD3 | Flux |
|---------|-------|------|-----|------|
| vae-ft-mse-840000 | ✅ | ❌ | ❌ | ❌ |
| sdxl_vae | ❌ | ✅ | ❌ | ❌ |
| sd3_vae | ❌ | ❌ | ✅ | ❌ |
| ae.safetensors | ❌ | ❌ | ❌ | ✅ |

### ControlNet 兼容性
| ControlNet | SD1.5 | SDXL | SD3 | Flux |
|-----------|-------|------|-----|------|
| SD1.5 ControlNet | ✅ | ❌ | ❌ | ❌ |
| SDXL ControlNet | ❌ | ✅ | ❌ | ❌ |
| Union ControlNet | ✅ | ✅ | ❓ | ❓ |

### LoRA 兼容性
| LoRA 类型 | SD1.5 | SDXL | SD3 | Flux |
|----------|-------|------|-----|------|
| SD1.5 LoRA | ✅ | ❌ | ❌ | ❌ |
| SDXL LoRA | ❌ | ✅ | ❌ | ❌ |
| SD3 LoRA | ❌ | ❌ | ✅ | ❌ |
| Flux LoRA | ❌ | ❌ | ❌ | ✅ |

---

## 推荐配置组合

### 入门配置 (4-6GB VRAM)
```
模型: SD1.5 + VAE-ft-mse + 基础 LoRA
分辨率: 512x512
采样: 20 步, euler, CFG 7
用途: 基础文生图学习
```

### 进阶配置 (8-12GB VRAM)
```
模型: SDXL + SDXL VAE + ControlNet + IP-Adapter
分辨率: 1024x1024
采样: 25 步, dpmpp_2m, CFG 6
用途: 高质量图像生成
```

### 专业配置 (16GB+ VRAM)
```
模型: SD3/Flux + 对应 VAE + 多 ControlNet + 视频模型
分辨率: 1024x1024+ 及视频
采样: 30+ 步, 多种采样器
用途: 商业级生成
```

### API 配置 (无本地限制)
```
服务: Grok + Gemini + ByteDance API
功能: 全类型生成 + 编辑 + 视频
优势: 无硬件限制, 最新模型
用途: 生产环境部署
```