# ComfyUI 工作流拓扑模式汇总

本文档汇总了 ComfyUI 中常见的工作流拓扑模式，每种都包含节点连接图、完整 API format JSON 和使用场景。

## 目录
- [1. 基础 Text-to-Image 模式](#1-基础-text-to-image-模式)
- [2. Image-to-Image 模式](#2-image-to-image-模式)
- [3. LoRA 应用模式](#3-lora-应用模式)
- [4. Inpainting 模式](#4-inpainting-模式)
- [5. Outpainting 模式](#5-outpainting-模式)
- [6. ControlNet 控制模式](#6-controlnet-控制模式)
- [7. 多 ControlNet 混合模式](#7-多-controlnet-混合模式)
- [8. Upscale 超分辨率模式](#8-upscale-超分辨率模式)
- [9. 复合流水线模式](#9-复合流水线模式)

---

## 1. 基础 Text-to-Image 模式

### 节点连接图
```
CheckpointLoaderSimple
├── MODEL → KSampler
├── CLIP → CLIPTextEncode (Positive) → KSampler
├── CLIP → CLIPTextEncode (Negative) → KSampler  
└── VAE → VAEDecode

EmptyLatentImage → KSampler → VAEDecode → SaveImage
```

### 何时使用
- 纯文本创作图像
- 概念验证和快速原型
- 批量生成变体

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "3": {
    "inputs": {
      "text": "masterpiece, best quality, beautiful landscape, golden hour",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "4": {
    "inputs": {
      "text": "low quality, blurry, deformed, ugly",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal", 
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["3", 0],
      "negative": ["4", 0],
      "latent_image": ["2", 0]
    },
    "class_type": "KSampler"
  },
  "6": {
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "7": {
    "inputs": {
      "filename_prefix": "ComfyUI_txt2img",
      "images": ["6", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 2. Image-to-Image 模式

### 节点连接图
```
CheckpointLoaderSimple
├── MODEL → KSampler
├── CLIP → CLIPTextEncode (Positive/Negative) → KSampler
└── VAE → VAEEncode & VAEDecode

LoadImage → VAEEncode → KSampler → VAEDecode → SaveImage
```

### 何时使用
- 风格转换
- 基于参考图的再创作
- 细节调整和优化

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "image": "reference.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "3": {
    "inputs": {
      "pixels": ["2", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEEncode"
  },
  "4": {
    "inputs": {
      "text": "oil painting style, dramatic lighting",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "text": "low quality, blurry",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 6.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 0.65,
      "model": ["1", 0],
      "positive": ["4", 0],
      "negative": ["5", 0],
      "latent_image": ["3", 0]
    },
    "class_type": "KSampler"
  },
  "7": {
    "inputs": {
      "samples": ["6", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "8": {
    "inputs": {
      "filename_prefix": "ComfyUI_img2img",
      "images": ["7", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 3. LoRA 应用模式

### 节点连接图
```
CheckpointLoaderSimple → LoadLoRA → 标准Text2Img流程
                            ├── MODEL → KSampler
                            └── CLIP → CLIPTextEncode
```

### 何时使用
- 特定风格生成
- 角色一致性保持
- 概念注入

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "dreamshaper_8.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "lora_name": "style_lora.safetensors",
      "strength_model": 1.0,
      "strength_clip": 1.0,
      "model": ["1", 0],
      "clip": ["1", 1]
    },
    "class_type": "LoraLoader"
  },
  "3": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "4": {
    "inputs": {
      "text": "anime style, 1girl, beautiful",
      "clip": ["2", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "text": "low quality, ugly",
      "clip": ["2", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["2", 0],
      "positive": ["4", 0],
      "negative": ["5", 0],
      "latent_image": ["3", 0]
    },
    "class_type": "KSampler"
  },
  "7": {
    "inputs": {
      "samples": ["6", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "8": {
    "inputs": {
      "filename_prefix": "ComfyUI_lora",
      "images": ["7", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 4. Inpainting 模式

### 节点连接图
```
CheckpointLoaderSimple (inpainting model)
├── MODEL → KSampler
├── CLIP → CLIPTextEncode → KSampler
└── VAE → VAEDecode

LoadImage → VAEEncodeForInpainting → KSampler → VAEDecode → SaveImage
```

### 何时使用
- 局部内容修复
- 移除不需要的对象
- 细节重绘

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "512-inpainting-ema.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "image": "input_with_mask.png",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "3": {
    "inputs": {
      "pixels": ["2", 0],
      "vae": ["1", 2],
      "mask": ["2", 1],
      "grow_mask_by": 6
    },
    "class_type": "VAEEncodeForInpainting"
  },
  "4": {
    "inputs": {
      "text": "beautiful garden, flowers, natural lighting",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "text": "low quality, distorted",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["4", 0],
      "negative": ["5", 0],
      "latent_image": ["3", 0]
    },
    "class_type": "KSampler"
  },
  "7": {
    "inputs": {
      "samples": ["6", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "8": {
    "inputs": {
      "filename_prefix": "ComfyUI_inpaint",
      "images": ["7", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 5. Outpainting 模式

### 节点连接图
```
CheckpointLoaderSimple (inpainting model)
├── MODEL → KSampler
├── CLIP → CLIPTextEncode → KSampler
└── VAE → VAEDecode

LoadImage → PadImageForOutpainting → VAEEncodeForInpainting → KSampler
```

### 何时使用
- 扩展图像边界
- 增加场景内容
- 调整画面比例

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "512-inpainting-ema.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "image": "input.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "3": {
    "inputs": {
      "left": 128,
      "top": 128,
      "right": 128,
      "bottom": 128,
      "feathering": 40,
      "image": ["2", 0]
    },
    "class_type": "PadImageForOutpainting"
  },
  "4": {
    "inputs": {
      "pixels": ["3", 0],
      "vae": ["1", 2],
      "mask": ["3", 1],
      "grow_mask_by": 6
    },
    "class_type": "VAEEncodeForInpainting"
  },
  "5": {
    "inputs": {
      "text": "extended landscape, natural scenery",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "text": "low quality, seams, borders",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["5", 0],
      "negative": ["6", 0],
      "latent_image": ["4", 0]
    },
    "class_type": "KSampler"
  },
  "8": {
    "inputs": {
      "samples": ["7", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI_outpaint",
      "images": ["8", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 6. ControlNet 控制模式

### 节点连接图
```
CheckpointLoaderSimple
├── MODEL → KSampler
├── CLIP → CLIPTextEncode → ApplyControlNet → KSampler
└── VAE → VAEDecode

LoadControlNet → ApplyControlNet
LoadImage → ApplyControlNet
```

### 何时使用
- 精确控制生成内容
- 保持特定构图
- 基于线稿或姿态生成

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "dreamshaper_8.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "control_net_name": "control_v11p_sd15_canny_fp16.safetensors"
    },
    "class_type": "ControlNetLoader"
  },
  "3": {
    "inputs": {
      "image": "control_image.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "4": {
    "inputs": {
      "text": "beautiful portrait, detailed face",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "text": "low quality, blurry",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "6": {
    "inputs": {
      "conditioning": ["4", 0],
      "control_net": ["2", 0],
      "image": ["3", 0],
      "strength": 1.0,
      "start_percent": 0.0,
      "end_percent": 1.0
    },
    "class_type": "ControlNetApply"
  },
  "7": {
    "inputs": {
      "conditioning": ["5", 0],
      "control_net": ["2", 0],
      "image": ["3", 0],
      "strength": 1.0,
      "start_percent": 0.0,
      "end_percent": 1.0
    },
    "class_type": "ControlNetApply"
  },
  "8": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "9": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["8", 0]
    },
    "class_type": "KSampler"
  },
  "10": {
    "inputs": {
      "samples": ["9", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "11": {
    "inputs": {
      "filename_prefix": "ComfyUI_controlnet",
      "images": ["10", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 7. 多 ControlNet 混合模式

### 节点连接图
```
CheckpointLoaderSimple
├── MODEL → KSampler
├── CLIP → CLIPTextEncode → ControlNet1 → ControlNet2 → KSampler
└── VAE → VAEDecode

ControlNet1_Model + Image1 → ApplyControlNet1
ControlNet2_Model + Image2 → ApplyControlNet2 → ApplyControlNet1
```

### 何时使用
- 复杂场景控制
- 多层次约束
- 精细化生成控制

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "dreamshaper_8.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "control_net_name": "control_v11p_sd15_canny_fp16.safetensors"
    },
    "class_type": "ControlNetLoader"
  },
  "3": {
    "inputs": {
      "control_net_name": "control_v11f1p_sd15_depth_fp16.safetensors"
    },
    "class_type": "ControlNetLoader"
  },
  "4": {
    "inputs": {
      "image": "canny_image.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "5": {
    "inputs": {
      "image": "depth_image.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "6": {
    "inputs": {
      "text": "beautiful landscape, detailed",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "7": {
    "inputs": {
      "text": "low quality, blurry",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "8": {
    "inputs": {
      "conditioning": ["6", 0],
      "control_net": ["2", 0],
      "image": ["4", 0],
      "strength": 1.0,
      "start_percent": 0.0,
      "end_percent": 0.8
    },
    "class_type": "ControlNetApply"
  },
  "9": {
    "inputs": {
      "conditioning": ["8", 0],
      "control_net": ["3", 0],
      "image": ["5", 0],
      "strength": 0.7,
      "start_percent": 0.0,
      "end_percent": 1.0
    },
    "class_type": "ControlNetApply"
  },
  "10": {
    "inputs": {
      "conditioning": ["7", 0],
      "control_net": ["2", 0],
      "image": ["4", 0],
      "strength": 1.0,
      "start_percent": 0.0,
      "end_percent": 0.8
    },
    "class_type": "ControlNetApply"
  },
  "11": {
    "inputs": {
      "conditioning": ["10", 0],
      "control_net": ["3", 0],
      "image": ["5", 0],
      "strength": 0.7,
      "start_percent": 0.0,
      "end_percent": 1.0
    },
    "class_type": "ControlNetApply"
  },
  "12": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "13": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["9", 0],
      "negative": ["11", 0],
      "latent_image": ["12", 0]
    },
    "class_type": "KSampler"
  },
  "14": {
    "inputs": {
      "samples": ["13", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "15": {
    "inputs": {
      "filename_prefix": "ComfyUI_multi_controlnet",
      "images": ["14", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 8. Upscale 超分辨率模式

### 节点连接图
```
LoadUpscaleModel → UpscaleImageWithModel → SaveImage
LoadImage → UpscaleImageWithModel
```

### 何时使用
- 提升图像分辨率
- 细节增强
- 打印质量优化

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "model_name": "4x-ESRGAN.pth"
    },
    "class_type": "UpscaleModelLoader"
  },
  "2": {
    "inputs": {
      "image": "low_res_image.jpg",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "3": {
    "inputs": {
      "upscale_model": ["1", 0],
      "image": ["2", 0]
    },
    "class_type": "ImageUpscaleWithModel"
  },
  "4": {
    "inputs": {
      "filename_prefix": "ComfyUI_upscale",
      "images": ["3", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 9. 复合流水线模式

### Text2Img + Upscale 流水线

#### 节点连接图
```
Text2Img Pipeline → UpscaleModel → FinalOutput
```

#### 何时使用
- 高质量图像生成
- 批量处理工作流
- 专业输出需求

### 完整 API Format JSON
```json
{
  "1": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"
    },
    "class_type": "CheckpointLoaderSimple"
  },
  "2": {
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "class_type": "EmptyLatentImage"
  },
  "3": {
    "inputs": {
      "text": "masterpiece, best quality, detailed artwork",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "4": {
    "inputs": {
      "text": "low quality, blurry",
      "clip": ["1", 1]
    },
    "class_type": "CLIPTextEncode"
  },
  "5": {
    "inputs": {
      "seed": 42,
      "steps": 25,
      "cfg": 7.5,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["1", 0],
      "positive": ["3", 0],
      "negative": ["4", 0],
      "latent_image": ["2", 0]
    },
    "class_type": "KSampler"
  },
  "6": {
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    },
    "class_type": "VAEDecode"
  },
  "7": {
    "inputs": {
      "model_name": "4x-ESRGAN.pth"
    },
    "class_type": "UpscaleModelLoader"
  },
  "8": {
    "inputs": {
      "upscale_model": ["7", 0],
      "image": ["6", 0]
    },
    "class_type": "ImageUpscaleWithModel"
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI_pipeline",
      "images": ["8", 0]
    },
    "class_type": "SaveImage"
  }
}
```

---

## 工作流选择指南

### 场景对应工作流

| 需求场景 | 推荐工作流 | 复杂度 |
|---------|-----------|--------|
| 快速创作 | Text-to-Image | ⭐ |
| 风格转换 | Image-to-Image | ⭐⭐ |
| 特定风格 | LoRA 应用 | ⭐⭐ |
| 局部修复 | Inpainting | ⭐⭐⭐ |
| 画面扩展 | Outpainting | ⭐⭐⭐ |
| 精确控制 | ControlNet | ⭐⭐⭐⭐ |
| 复杂场景 | 多 ControlNet | ⭐⭐⭐⭐⭐ |
| 质量提升 | Upscale | ⭐⭐ |
| 专业输出 | 复合流水线 | ⭐⭐⭐⭐⭐ |

### 性能考虑

#### 显存使用排序（从低到高）
1. Upscale 模式
2. Text-to-Image 模式
3. Image-to-Image 模式
4. LoRA 应用模式
5. ControlNet 模式
6. Inpainting/Outpainting 模式
7. 多 ControlNet 模式
8. 复合流水线模式

#### 处理时间排序（从快到慢）
1. Upscale 模式
2. Text-to-Image 模式
3. LoRA 应用模式
4. Image-to-Image 模式
5. ControlNet 模式
6. Inpainting/Outpainting 模式
7. 多 ControlNet 模式
8. 复合流水线模式

---

这些工作流模式覆盖了 ComfyUI 的主要使用场景。根据具体需求选择合适的模式，可以显著提高工作效率和输出质量。