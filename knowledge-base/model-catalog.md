# ComfyUI 模型目录

基于 55 个官方工作流模板提取的完整模型清单，按类型和用途分类整理。

## Checkpoints (基础扩散模型)

| 模型名 | 类型 | 参数量 | 精度 | 用于管线 |
|--------|------|--------|------|---------|
| ltx-2.3-22b-distilled-fp8.safetensors | Video Models | 22B | fp8 | LTX-2 视频生成 |
| wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors | Video Models | 14B | fp8 | Wan2.2 文本生成视频 |
| wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors | Video Models | 14B | fp8 | Wan2.2 文本生成视频 |
| wan2.1_t2v_14B_fp8_scaled.safetensors | Video Models | 14B | fp8 | Wan2.1 文本生成视频 |
| flux-2-klein-9b-fp8.safetensors | Modern Generation | 9B | fp8 | Flux2 Klein 图像生成 |
| flux-2-klein-base-9b-fp8.safetensors | Modern Generation | 9B | fp8 | Flux2 Klein 基础版 |
| qwen_3_8b_fp8mixed.safetensors | Text Encoders | 8B | fp8 | Qwen 多模态编码 |
| qwen_2.5_vl_7b_fp8_scaled.safetensors | Text Encoders | 7B | fp8 | Qwen 视觉语言编码 |
| wan2.2_ti2v_5B_fp16.safetensors | Video Models | 5B | fp16 | Wan2.2 图像生成视频 |
| flux-2-klein-4b-fp8.safetensors | Modern Generation | 4B | fp8 | Flux2 Klein 轻量版 |
| flux-2-klein-base-4b-fp8.safetensors | Modern Generation | 4B | fp8 | Flux2 Klein 基础版 |
| qwen_3_4b.safetensors | Text Encoders | 4B | fp16 | Qwen 文本编码 |
| hunyuan_3d_v2.1.safetensors | 3D Models | 未知 | bf16 | 图像到3D模型转换 |
| ltx-video-2b-v0.9.5.safetensors | Video Models | 2B | fp16 | LTX 视频生成 |

## LoRA 适配器

| 模型名 | 用途 | 兼容模型 | 步数优化 |
|--------|------|----------|----------|
| flux1-depth-dev-lora.safetensors | 深度控制 | Flux 系列 | 标准 |
| Qwen-Image-Lightning-4steps-V1.0.safetensors | 推理加速 | Qwen Image | 4步 |
| Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors | 推理加速 | Qwen Image Edit | 4步 |
| Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16.safetensors | 极速生成 | Qwen Image 2512 | 2步 |
| Qwen_Image_Edit_2511-SYSTMS_INFL8.safetensors | 充气效果 | Qwen Image Edit | 特效 |
| wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors | 推理加速 | Wan2.2 T2V | 4步 |
| wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors | 推理加速 | Wan2.2 T2V | 4步 |
| wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors | 推理加速 | Wan2.2 I2V | 4步 |
| wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors | 推理加速 | Wan2.2 I2V | 4步 |
| wan_alpha_2.1_rgba_lora.safetensors | RGBA通道 | Wan2.1 Alpha | 透明度 |
| lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank64_bf16.safetensors | 推理加速 | Wan2.1 T2V | CFG优化 |
| qwen_image_union_diffsynth_lora.safetensors | 统一控制 | Qwen Image | Union ControlNet |

## VAE 编解码器

| 模型名 | 适用模型 | 分辨率支持 | 特点 |
|--------|----------|------------|------|
| flux2-vae.safetensors | Flux 系列 | 高分辨率 | 新一代VAE |
| qwen_image_vae.safetensors | Qwen Image | 高分辨率 | 多模态VAE |
| hunyuanvideo15_vae_fp16.safetensors | HunyuanVideo | 720p | 视频VAE |
| hunyuan_video_vae_bf16.safetensors | HunyuanVideo | 720p | 视频VAE |
| wan2.2_vae.safetensors | Wan2.2 | 640x640 | 视频VAE |
| wan_2.1_vae.safetensors | Wan2.1 | 640x640 | 视频VAE |
| wan_alpha_2.1_vae_rgb_channel.safetensors | Wan2.1 Alpha | RGB通道 | RGB专用 |
| wan_alpha_2.1_vae_alpha_channel.safetensors | Wan2.1 Alpha | Alpha通道 | 透明度通道 |
| ae.safetensors | 通用 | 标准 | 通用自编码器 |
| vae-ft-mse-840000-ema-pruned.safetensors | SD1.5 | 标准 | 经典VAE |

## ControlNet 控制网络

| 模型名 | 控制类型 | 兼容模型 | 功能描述 |
|--------|----------|----------|----------|
| Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors | 多合一 | Qwen Image 2512 | 统一多种控制类型 |
| Qwen-Image-InstantX-ControlNet-Union.safetensors | 多合一 | Qwen Image | InstantX即时控制 |
| Qwen-Image-InstantX-ControlNet-Inpainting.safetensors | 修复控制 | Qwen Image | 修复专用控制 |
| Z-Image-Turbo-Fun-Controlnet-Union.safetensors | 多合一 | Z-Image Turbo | 超快推理控制 |
| qwen_image_canny_diffsynth_controlnet.safetensors | 边缘检测 | Qwen Image | Canny边缘控制 |
| qwen_image_depth_diffsynth_controlnet.safetensors | 深度控制 | Qwen Image | 深度图控制 |
| qwen_image_inpaint_diffsynth_controlnet.safetensors | 修复控制 | Qwen Image | DiffSynth修复 |

## Text Encoders (文本编码器)

现代模型普遍采用大语言模型作为文本编码器：

### 多模态编码器
- **qwen_2.5_vl_7b_fp8_scaled.safetensors** - Qwen 2.5 视觉语言模型，7B参数
- **qwen_3_4b.safetensors** - Qwen 3.0 文本编码器，4B参数
- **qwen_3_8b_fp8mixed.safetensors** - Qwen 3.0 大型编码器，8B参数

### 传统编码器
- **t5xxl_fp16.safetensors** - T5-XXL 长文本处理
- **clip_l.safetensors** - CLIP-L 图像文本对齐
- **byt5_small_glyphxl_fp16.safetensors** - ByT5 字节级编码
- **umt5_xxl_fp8_e4m3fn_scaled.safetensors** - UMT5 多语言支持
- **gemma_3_12B_it_fp4_mixed.safetensors** - Gemma 3.0 指令调优

### 视觉编码器
- **sigclip_vision_patch14_384.safetensors** - SigCLIP 视觉编码
- **llava_llama3_fp8_scaled.safetensors** - LLaVA 多模态编码

## Video Models (视频模型)

### Wan2.x 系列
- **wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors** - 文本生成视频，高噪声版
- **wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors** - 文本生成视频，低噪声版
- **wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors** - 图像生成视频，高噪声版
- **wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors** - 图像生成视频，低噪声版
- **wan2.2_ti2v_5B_fp16.safetensors** - 文本+图像生成视频，5B版本
- **wan2.1_t2v_14B_fp8_scaled.safetensors** - Wan2.1 文本生成视频

### LTX 系列
- **ltx-2.3-22b-distilled-fp8.safetensors** - LTX-2.3 旗舰版，22B参数
- **ltx-video-2b-v0.9.5.safetensors** - LTX 基础版，2B参数
- **ltx-video-2b-v0.9.safetensors** - LTX 早期版本

### HunyuanVideo 系列
- **hunyuanvideo1.5_720p_t2v_fp16.safetensors** - 720p 文本生成视频
- **hunyuanvideo1.5_720p_i2v_fp16.safetensors** - 720p 图像生成视频
- **hunyuanvideo1.5_1080p_sr_distilled_fp16.safetensors** - 1080p 超分辨率
- **hunyuanvideo15_latent_upsampler_1080p.safetensors** - 潜在空间上采样

## Audio Models (音频模型)  

### 音乐生成
- **ace_step_v1_3.5b.safetensors** - ACE-Step 音乐生成，支持标签和歌词

### TTS 语音合成
- 通过 API 节点调用：
  - Chatterbox TTS - 多语言文本转语音
  - ElevenLabs - 高质量语音合成
  - Stability AI - 音效和环境音生成

## 3D Models (3D 生成)

- **hunyuan_3d_v2.1.safetensors** - Hunyuan3D 2.1 图像到3D模型转换

## Upscale Models (超分辨率)

### API 驱动的超分辨率
- **Magnific AI Creative** - 创意性超分辨率，智能细节增强
- **Stability AI Fast** - 快速超分辨率，实时处理优化
- **Wavespeed FlashVSR** - 视频超分辨率

### 本地超分辨率模型
- **lotus-depth-d-v1-1.safetensors** - Lotus 深度感知超分辨率

## 部署建议

### VRAM 需求参考

| 模型类型 | 最小 VRAM | 推荐 VRAM | 备注 |
|----------|-----------|-----------|------|
| Flux Klein 4B | 8GB | 12GB | 轻量高效，适合实时应用 |
| Flux Klein 9B | 12GB | 16GB | 平衡选择，质量与速度兼顾 |  
| Qwen Image 2512 | 16GB | 24GB | 高质量生成，专业用途 |
| Wan2.x 14B | 20GB | 32GB | 视频生成，需大显存 |
| LTX-2.3 22B | 32GB | 48GB | 顶级视频质量 |
| HunyuanVideo 720p | 16GB | 24GB | 高清视频生成 |
| HunyuanVideo 1080p | 24GB | 40GB | 超高清视频 |

### 存储结构建议

```
ComfyUI/
├── models/
│   ├── checkpoints/          # 传统SD模型
│   ├── diffusion_models/     # 现代扩散模型 (Flux, Qwen, Wan等)
│   ├── loras/               # LoRA 适配器
│   ├── vae/                 # VAE 编解码器  
│   ├── controlnet/          # ControlNet 模型
│   ├── text_encoders/       # 文本编码器
│   ├── model_patches/       # 模型补丁和控制器
│   ├── clip_vision/         # 视觉编码器
│   └── upscale_models/      # 超分辨率模型
```

### 性能优化策略

#### 1. 精度选择策略
- **fp8**: 最佳VRAM效率，略微质量损失
- **fp16**: 平衡选择，广泛兼容
- **bf16**: 数值稳定性更好，现代GPU推荐

#### 2. LoRA 组合策略
```
基础模型 + Lightning LoRA (速度) + 风格 LoRA (质量)
= 快速高质量生成
```

#### 3. 分辨率生成策略
```
低分辨率生成 (512x512) → 超分辨率后处理 (2K/4K)
= 更快的高质量输出
```

#### 4. 批处理优化
- **图像生成**: batch_size = 2-4
- **视频生成**: batch_size = 1 (显存限制)
- **音频生成**: batch_size = 1-2

### 模型选择指南

#### 图像生成推荐
1. **入门**: Flux Klein 4B + Lightning LoRA
2. **专业**: Qwen Image 2512 + 多种 LoRA
3. **极致**: 组合多个模型管线

#### 视频生成推荐
1. **快速原型**: LTX-Video 2B
2. **高质量**: Wan2.2 14B + 4步 LoRA
3. **顶级质量**: LTX-2.3 22B

#### 音频生成推荐
1. **TTS**: Chatterbox TTS (本地) / ElevenLabs (API)
2. **音乐**: ACE-Step v1 (本地生成)
3. **音效**: Stability AI Audio (API)

### 硬件配置建议

#### 入门配置 (RTX 4060/4070)
- **VRAM**: 12-16GB
- **推荐模型**: Flux Klein 4B, Qwen Lightning
- **主要功能**: 图像生成、轻量视频

#### 专业配置 (RTX 4080/4090)
- **VRAM**: 16-24GB  
- **推荐模型**: 全系列图像模型、中型视频模型
- **主要功能**: 全功能图像、720p视频

#### 工作站配置 (RTX 6000 Ada/H100)
- **VRAM**: 48GB+
- **推荐模型**: 所有模型无限制
- **主要功能**: 4K视频、实时生成、批量处理

---

*模型统计基于 55 个官方工作流模板，统计时间：2025年3月17日*
*总计模型数量：140+ 个不同模型文件*