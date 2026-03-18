# 样本工作流索引

> 每个工作流经过验证，附带运行方式和设计原理

## 快速查找

### 基础工作流
| 文件 | 需求 | 运行方式 | 设计原理 |
|------|------|----------|----------|
| `basic/text2img.json` | 文字生图 | ComfyUI 加载 / API POST | 最小节点链：Checkpoint→CLIP→KSampler→VAEDecode→Save |
| `basic/img2img.json` | 图片风格转换 | 需提供输入图 | 与 txt2img 区别：VAEEncode 替代 EmptyLatent，denoise<1.0 |
| `basic/inpaint.json` | 局部重绘 | 需提供图+遮罩 | SetLatentNoiseMask 标记重绘区域 |

### ControlNet 工作流
| 文件 | 需求 | 核心区别 |
|------|------|----------|
| `controlnet/canny.json` | 边缘控制 | Canny 预处理器提取边缘 |
| `controlnet/depth.json` | 深度控制 | 深度估计模型 |
| `controlnet/pose.json` | 姿势控制 | OpenPose 检测人体关键点 |
| `controlnet/ip-adapter.json` | 风格迁移 | 图像 embedding 而非结构控制 |

### LoRA 工作流
| 文件 | 需求 | 说明 |
|------|------|------|
| `lora/single-lora.json` | 单 LoRA | LoraLoader 插入 MODEL+CLIP 之间 |
| `lora/multi-lora.json` | 多 LoRA 叠加 | 多个 LoraLoader 串联，注意权重平衡 |

### 高级工作流
| 文件 | 需求 | 说明 |
|------|------|------|
| `advanced/sdxl-refiner.json` | SDXL 高质量 | Base→Refiner 两阶段 |
| `advanced/upscale.json` | 图片放大 | Upscale Model + Tiled VAE |
| `advanced/hires-fix.json` | 高分辨率修复 | 先低分辨率再放大重采样 |

### 视频工作流
| 文件 | 需求 | 说明 |
|------|------|------|
| `video/animatediff.json` | 文字/图→视频 | AnimateDiff 运动模块 |

（学习过程中持续补充验证过的工作流）
