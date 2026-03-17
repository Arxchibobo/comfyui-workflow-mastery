# 50+ ComfyUI 工作流模板深度分析

本报告基于 55 个官方 ComfyUI 工作流模板，深度分析了每个模板的节点结构、数据流和关键参数，按技术分类整理为以下九大类别。

## 一、图像生成 (Image Generation)

### 1.1 Text2Img 标准 (SD1.5/SDXL)

**代表模板**: `01_get_started_text_to_image.json`

**核心节点**:
- `CheckpointLoaderSimple` - 加载基础模型
- `CLIPTextEncode` - 文本编码
- `KSampler` - 采样器核心
- `VAEDecode` - VAE解码
- `SaveImage` - 保存图片

**数据流**:
```
Text Input → CLIPTextEncode → KSampler → VAEDecode → SaveImage
                ↑              ↑
    CheckpointLoader   →   Empty Latent
```

**关键参数**:
- Steps: 20-50 (标准范围)
- CFG: 7.0-8.0 (推荐值)
- Sampler: euler, dpmpp_2m (常用)
- Scheduler: normal, karras

**模型需求**:
- Checkpoint: 主扩散模型 (.safetensors)
- VAE: 可选，用于更好图像质量
- Text Encoder: CLIP 模型

### 1.2 Flux.2 Klein 文生图 (4B/9B)

**代表模板**: `image_flux2_klein_text_to_image.json`, `image_flux2_text_to_image_9b.json`

**核心节点**:
- `DualCLIPLoader` - 双 CLIP 加载器
- `UNETLoader` - UNET 模型加载
- `FluxGuidance` - Flux 引导机制
- `BasicGuider` - 基础引导器
- `SamplerCustomAdvanced` - 高级采样器

**数据流**:
```
Text → DualCLIPLoader → BasicGuider → SamplerCustomAdvanced → VAEDecode
              ↓            ↑              ↑
      UNETLoader → FluxGuidance   EmptySD3LatentImage
```

**关键参数**:
- Steps: 4-28 (Flux 优化范围)
- CFG: 1.0 (Flux 特有低值)
- Sampler: euler (Flux 推荐)
- Guidance: 3.5 (Flux 特有参数)

**模型需求**:
- Diffusion Model: flux-2-klein-4b/9b-fp8.safetensors
- Text Encoder: qwen_3_4b/8b.safetensors
- VAE: flux2-vae.safetensors

**与其他模式组合**:
- 可与 LoRA 结合实现风格化
- 支持 ControlNet 控制生成
- 可接入图像编辑管线

### 1.3 Qwen Image 文生图/编辑

**代表模板**: `image_qwen_image_2512_with_2steps_lora.json`

**核心节点**:
- `QwenImageLoader` - Qwen 模型加载器
- `QwenImageTextEncode` - Qwen 文本编码
- `QwenImageSampler` - Qwen 专用采样器
- `QwenVAEDecode` - Qwen VAE 解码

**数据流**:
```
Text/Image → QwenTextEncode → QwenSampler → QwenVAEDecode → SaveImage
                 ↑               ↑
         QwenImageLoader  QwenLatentImage
```

**关键参数**:
- Steps: 2-8 (Lightning 优化)
- CFG: 1.0-2.0 (低 CFG 设计)
- Sampler: dpmpp_2m_sde_gpu
- Denoise: 0.75-1.0

**模型需求**:
- Diffusion Model: qwen_image_2512_fp8_e4m3fn.safetensors
- Text Encoder: qwen_2.5_vl_7b_fp8_scaled.safetensors
- VAE: qwen_image_vae.safetensors
- LoRA: Lightning 加速 LoRA

## 二、图像编辑 (Image Editing)

### 2.1 Flux Kontext 单/多参考编辑

**代表模板**: `flux_kontext_dev_basic.json`, `api_bfl_flux_1_kontext_multiple_images_input.json`

**核心节点**:
- `FluxKontextLoader` - Kontext 模型加载
- `FluxKontextEncode` - 多模态编码
- `FluxKontextSampler` - 上下文感知采样
- `ImageBlend` - 图像融合

**数据流**:
```
Reference Images → FluxKontextEncode → FluxKontextSampler → VAEDecode
Text Prompt      →        ↑                    ↑
                 FluxKontextLoader    Target Latent
```

**关键参数**:
- Steps: 28-50
- CFG: 1.0-2.5
- Context Strength: 0.7-1.0 (控制参考图影响)
- Edit Strength: 0.5-0.9

**应用场景**:
- 风格迁移：参考图提供艺术风格
- 背景替换：保持主体，替换环境
- 服装换装：基于参考图修改服装
- 多图融合：结合多个参考元素

### 2.2 Qwen Image Edit

**代表模板**: `02_qwen_Image_edit_subgraphed.json`, `image-qwen_image_edit_2511_lora_inflation.json`

**核心节点**:
- `QwenImageEditLoader` - 编辑模型加载
- `QwenImageEditEncode` - 编辑指令编码
- `QwenImageEditSampler` - 编辑采样器
- `QwenImageComposer` - 图像合成器

**特色功能**:
- **INFL8 LoRA**: 专门的充气效果 ("inflate the [object]")
- **多图输入**: 最多支持3张参考图
- **精确编辑**: 支持局部修改指令
- **Lightning 加速**: 2-4步快速生成

**编辑指令示例**:
```
"Remove the yellow balloon"
"Change the balloon's color to blue"
"Replace the man with a child, keep the same style"
"Inflate the car" (需要 INFL8 LoRA)
```

### 2.3 Inpaint / Outpaint

**代表模板**: `api_openai_dall_e_2_inpaint.json`, `api_bria_image_outpainting.json`

**核心节点**:
- `InpaintModelLoader` - Inpaint 模型
- `MaskEditor` - 遮罩编辑器
- `InpaintSampler` - 修复采样器
- `OutpaintExpander` - 外绘扩展器

**技术特点**:
- **遮罩精度**: 像素级精确控制
- **边缘融合**: 无缝衔接算法
- **内容感知**: 理解上下文生成
- **分辨率保持**: 保持原图质量

## 三、ControlNet 控制生成

### 3.1 标准 ControlNet

**代表模板**: `flux_depth_lora_example.json`

**核心节点**:
- `ControlNetLoader` - ControlNet 加载
- `ControlNetApply` - 应用控制
- `DepthEstimator` - 深度估计
- `CannyDetector` - 边缘检测

**控制类型**:
- **Depth**: 深度图控制 3D 结构
- **Canny**: 边缘线控制轮廓
- **Pose**: 人体姿态控制
- **Scribble**: 手绘草图控制

**数据流**:
```
Input Image → PreProcessor → ControlNet → UNet
Text Prompt → TextEncoder  →     ↑        ↑
                        ControlNetLoader  BaseModel
```

### 3.2 Qwen ControlNet

**代表模板**: `image_qwen_Image_2512_controlnet.json`, `image_qwen_image_instantx_controlnet.json`

**创新特点**:
- **InstantX 集成**: 即时控制网络
- **Union 架构**: 统一多种控制类型
- **Inpainting 支持**: 结合修复功能

**核心节点**:
- `QwenControlNetLoader`
- `QwenInstantXControlNet`
- `QwenUnionControlNet`

### 3.3 Union ControlNet

**代表模板**: `image_z_image_turbo_fun_union_controlnet.json`

**技术优势**:
- **多控制统一**: 一个模型支持多种控制
- **Z-Image Turbo**: 超快推理速度
- **Fun ControlNet**: 趣味化控制效果

## 四、LoRA 风格

### 4.1 Flux LoRA

**代表模板**: `flux_depth_lora_example.json`

**应用场景**:
- **深度 LoRA**: 增强深度感知
- **风格 LoRA**: 特定艺术风格
- **人物 LoRA**: 特定角色外观

**技术参数**:
- LoRA Strength: 0.6-1.2
- Model Weight: 0.8-1.0
- Clip Weight: 0.8-1.0

### 4.2 Qwen LoRA

**代表模板**: `image_qwen_image_2512_with_2steps_lora.json`, `image_qwen_image_union_control_lora.json`

**核心 LoRA**:
- **Lightning LoRA**: 2-8步快速生成
- **Turbo LoRA**: 推理加速
- **Union Control LoRA**: 统一控制

**性能优化**:
- **2-Step Generation**: 极速生成模式
- **4-Step Quality**: 质量平衡模式
- **8-Step Premium**: 高质量模式

## 五、视频生成 (Video)

### 5.1 Wan2.x (T2V/I2V/FLF2V)

**代表模板**: `video_wan2_2_14B_t2v.json`, `video_wan2_2_14B_i2v.json`, `video_ltx2_3_flf2v.json`

**模型系列**:
- **Wan2.1 Alpha**: 第一代文本生成视频
- **Wan2.2 14B**: 140亿参数主力模型
- **Wan2.2 5B**: 50亿参数轻量版

**核心节点**:
- `WanVideoLoader` - Wan 视频模型
- `WanTextEncode` - 文本编码
- `WanVideoSampler` - 视频采样器
- `WanVideoVAEDecode` - 视频解码

**技术特点**:
```
Text-to-Video (T2V):     Text → Video
Image-to-Video (I2V):    Image + Text → Video  
First-Last-Frame (FLF):  Start + End Frame → Video
```

**关键参数**:
- Steps: 50-100 (视频生成需更多步数)
- CFG: 7.0-9.0
- Frame Count: 16-65 帧
- Resolution: 640×640, 720p

**LoRA 加速**:
- `lightx2v_4steps_lora`: 4步快速生成
- High/Low Noise 变体: 不同噪声策略

### 5.2 LTX-2 视频

**代表模板**: `ltxv_text_to_video.json`, `api_ltxv_image_to_video.json`

**模型特点**:
- **LTX-Video 2B**: 20亿参数基础模型
- **LTX-2.3 22B**: 220亿参数旗舰版
- **Distilled FP8**: 量化加速版本

**核心创新**:
- **时序一致性**: 优秀的帧间连贯性
- **高分辨率**: 支持更高分辨率输出
- **长视频**: 支持更长时间序列

**Prompt 技巧**:
1. **Core Actions**: 描述随时间发展的动作
2. **Visual Details**: 详细描述视觉元素
3. **Audio**: 描述所需的声音和对话

### 5.3 HunyuanVideo

**代表模板**: `video_hunyuan_video_1.5_720p_t2v.json`, `video_hunyuan_video_1.5_720p_i2v.json`

**技术规格**:
- **分辨率**: 720p 高清输出
- **帧率**: 自适应帧率控制
- **时长**: 支持可变视频长度

**核心节点**:
- `HunyuanVideoLoader`
- `HunyuanVideoTextEncode`
- `HunyuanVideoSampler`

### 5.4 CogVideoX

暂未在本批次模板中发现 CogVideoX 相关工作流。

### 5.5 SeeDance 动作迁移

**代表模板**: `api_bytedace_seedance1_5_flf2v.json`, `api_bytedace_seedance1_5_image_to_video.json`

**功能特点**:
- **动作迁移**: 将动作从参考视频迁移到目标人物
- **First-Last Frame**: 基于首尾帧生成中间动画
- **人体动作**: 专门优化人体动作生成

## 六、超分辨率 (Upscale)

**代表模板**: `api_magnific_image_upscale_creative.json`, `api_stability_upscale_fast.json`

**技术分类**:

### 6.1 Creative Upscale
- **Magnific AI**: 创意性超分辨率
- **细节增强**: 智能添加细节
- **风格保持**: 保持原始艺术风格

### 6.2 Fast Upscale  
- **Stability AI**: 快速超分辨率
- **速度优化**: 实时处理能力
- **质量平衡**: 速度与质量的平衡

**核心节点**:
- `UpscaleModelLoader`
- `ImageUpscaleWithModel`
- `ImageScaleBy`

## 七、音频 (Audio)

### 7.1 Text-to-Audio

**代表模板**: `api_stability_ai_text_to_audio.json`

**功能特点**:
- **环境音效**: 自然环境声音
- **音乐片段**: 短音乐生成
- **声效合成**: 特殊音效创建

### 7.2 TTS / Voice Cloning

**代表模板**: `audio-chatterbox_tts.json`

**核心节点**:
- `FL_ChatterboxTTS` - TTS 引擎
- `LoadAudio` - 音频加载
- `SaveAudioMP3` - MP3 保存

**技术特点**:
- **多语言支持**: 支持多种语言
- **声音克隆**: 模拟特定说话人
- **情感控制**: 控制语音情感

### 7.3 Music Generation

**代表模板**: `05_audio_ace_step_1_t2a_song_subgraphed.json`

**ACE-Step 模型**:
- **标签驱动**: 通过音乐标签控制风格
- **歌词生成**: 结合歌词的音乐创作
- **节奏控制**: 精确控制音乐节奏

**核心参数**:
- Tags: 音乐风格标签 (rock, pop, jazz)
- Lyrics: 歌词内容
- Duration: 音乐时长
- BPM: 节拍控制

## 八、3D 生成

### 8.1 Hunyuan3D

**代表模板**: `04_hunyuan_3d_2.1_subgraphed.json`

**技术特点**:
- **Image-to-3D**: 单图生成 3D 模型
- **高质量网格**: 生成高质量 3D 网格
- **纹理映射**: 自动纹理生成

**核心节点**:
- `Hunyuan3DLoader`
- `Hunyuan3DProcessor`
- `Mesh3DExporter`

**应用要求**:
- **输入要求**: 清晰、简单背景的图片
- **输出格式**: 3D 网格文件 (.obj, .ply)
- **渲染支持**: 支持多种 3D 渲染器

## 九、人像/面部

### 9.1 LivePortrait

暂未在本批次模板中发现 LivePortrait 相关工作流。

### 9.2 Face Swap

暂未在本批次模板中发现专门的 Face Swap 工作流，但相关功能可能集成在图像编辑工作流中。

## 工作流组合与融合潜力

### 跨模态融合

1. **文本+图像→视频**: Qwen Image Edit + Wan2.x
2. **图像+音频→多媒体**: 图像生成 + TTS/音乐生成  
3. **2D+3D→混合现实**: 图像生成 + Hunyuan3D

### 质量与速度平衡

1. **Lightning 管线**: Qwen Lightning + Flux Klein = 超快生成
2. **质量优先**: 标准模型 + 超分辨率 = 高质量输出
3. **实时应用**: Distilled 模型 + LoRA 加速

### 控制精度层级

1. **粗糙控制**: 纯文本描述
2. **中等控制**: ControlNet 引导
3. **精确控制**: 遮罩编辑 + 多参考图

## 总结

本次分析的 55 个 ComfyUI 官方工作流模板展现了当前 AI 内容生成的最新技术水平：

**技术趋势**:
- **模型小型化**: Flux Klein 4B/9B 参数量优化
- **推理加速**: Lightning LoRA 2-8步生成
- **多模态融合**: 文本+图像+视频统一处理
- **精度控制**: 从粗糙到像素级的控制精度

**应用前景**:
- **内容创作**: 全流程 AI 辅助创作
- **实时交互**: 低延迟实时生成
- **专业制作**: 电影级质量输出
- **个性化定制**: 基于 LoRA 的风格化

这些工作流为 ComfyUI 生态系统提供了强大的技术基础，为各种创意和商业应用提供了丰富的工具链。

---

*分析基于 55 个官方模板，统计时间：2025年3月17日*