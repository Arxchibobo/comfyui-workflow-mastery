# ComfyUI 50+ 工作流管线完整知识库

## 一、图像生成 (Image Generation) — 7 种

### 1.1 text2img_sd15 — SD1.5 文生图
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
CLIPTextEncode(+) + CLIPTextEncode(-) → CONDITIONING
EmptyLatentImage(512x512) → LATENT
KSampler(steps=20, cfg=7, dpmpp_2m_sde, karras, denoise=1.0) → LATENT
VAEDecode → IMAGE → SaveImage
```
- **节点数**: 7 | **模型**: SD1.5 checkpoints | **分辨率**: 512x512

### 1.2 text2img_sdxl — SDXL 文生图
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
CLIPTextEncode(+) + CLIPTextEncode(-) → CONDITIONING
EmptyLatentImage(1024x1024) → LATENT
KSampler(steps=25, cfg=7.5, dpmpp_2m_sde, karras, denoise=1.0) → LATENT
VAEDecode → IMAGE → SaveImage
```
- **节点数**: 7 | **模型**: maximumEffort_maximumEffortXLV10 | **分辨率**: 1024x1024
- ✅ 已验证执行

### 1.3 text2img_flux1 — Flux.1 Dev 文生图
```
DualCLIPLoader(clip_l + t5xxl, type=flux) → CLIP
UNETLoader(flux1-dev) → MODEL
VAELoader(ae.safetensors) → VAE
CLIPTextEncode → CONDITIONING
FluxGuidance(3.5) → modified CONDITIONING
EmptySD3LatentImage(1024x1024) → LATENT
BasicScheduler + RandomNoise + BasicGuider + SamplerCustomAdvanced → LATENT
VAEDecode → IMAGE → SaveImage
```
- **关键差异**: 分离加载器(UNETLoader/CLIPLoader/VAELoader)，FluxGuidance 替代 cfg
- **模型**: flux1-dev-fp8 + clip_l + t5xxl_fp8

### 1.4 text2img_flux2_klein_base — Flux.2 Klein 4B Base
```
UNETLoader(flux-2-klein-base-4b) → MODEL
CLIPLoader(qwen_3_4b, type=flux2) → CLIP
VAELoader(flux2-vae) → VAE
CLIPTextEncode(+) + CLIPTextEncode(-) → CONDITIONING
EmptyFlux2LatentImage(1024x1024) → LATENT
Flux2Scheduler(steps=20) → SIGMAS
KSamplerSelect(euler) → SAMPLER
RandomNoise → NOISE
CFGGuider(cfg=5) → GUIDER
SamplerCustomAdvanced(NOISE, GUIDER, SAMPLER, SIGMAS, LATENT) → LATENT
VAEDecode → IMAGE → SaveImage
```
- **文本编码器**: Qwen3-4B（不再是 CLIP+T5！）
- **延迟图节点**: EmptyFlux2LatentImage（不是 EmptyLatentImage 或 EmptySD3）
- **采样器**: SamplerCustomAdvanced（高级采样链路）

### 1.5 text2img_flux2_klein_distilled — Flux.2 Klein 4B Distilled
```
与 Base 相同结构，但:
- 模型: flux-2-klein-4b (distilled)
- steps=4, cfg=1
- 加 ConditioningZeroOut 处理 negative
```
- **速度**: ~1.2秒/张！

### 1.6 text2img_flux2_9b — Flux.2 Klein 9B
```
与 4B 相同结构，更换模型:
- UNETLoader: flux-2-klein-base-9b-fp8 或 flux-2-klein-9b-fp8
- CLIPLoader: qwen_3_8b_fp8mixed
```

### 1.7 text2img_qwen — Qwen Image 文生图
```
UNETLoader(qwen_image_edit) → MODEL
CLIPLoader(qwen_2.5_vl_7b, type=qwen_image) → CLIP
VAELoader(qwen_image_vae) → VAE
CFGNorm(1) → modified MODEL
ModelSamplingAuraFlow(shift=3) → modified MODEL
LoraLoaderModelOnly(Lightning-4steps) → modified MODEL
TextEncodeQwenImageEditPlus → CONDITIONING
EmptySD3LatentImage → LATENT
KSampler(steps=4, cfg=1, euler, simple) → LATENT
VAEDecode → IMAGE → SaveImage
```
- **特殊**: CFGNorm + ModelSamplingAuraFlow 调整模型行为
- **速度**: 4步 Lightning LoRA

## 二、图像编辑 (Image Editing) — 5 种

### 2.1 img2img_sdxl — SDXL 图生图
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
LoadImage → IMAGE
VAEEncode(IMAGE, VAE) → LATENT
CLIPTextEncode(+/-) → CONDITIONING
KSampler(denoise=0.3~0.8) → LATENT
VAEDecode → IMAGE → SaveImage
```
- ✅ 已验证 | **关键**: denoise 控制保留程度

### 2.2 img_edit_flux_kontext — Flux Kontext 单图编辑
```
UNETLoader(flux1-dev-kontext) → MODEL
DualCLIPLoader(clip_l + t5xxl, type=flux) → CLIP
VAELoader(ae.safetensors) → VAE
LoadImage → IMAGE
VAEEncode(IMAGE) → LATENT
ReferenceLatent(LATENT) → LATENT reference
FluxKontextImageScale(IMAGE) → scaled IMAGE
CLIPTextEncode("change X to Y") → CONDITIONING
FluxGuidance(2.5) → modified CONDITIONING
ConditioningZeroOut → zero CONDITIONING
KSampler(steps=20, cfg=1, euler, simple) → LATENT
VAEDecode → IMAGE → SaveImage
```
- **核心概念**: ReferenceLatent 保持参考图的结构
- **提示词**: 描述性编辑指令，如 "Change the car color to red"

### 2.3 img_edit_flux_kontext_multi — Flux Kontext 多参考编辑
```
LoadImage(A) + LoadImage(B) → IMAGE_A, IMAGE_B
ImageStitch(IMAGE_A, IMAGE_B, direction=right) → stitched IMAGE
（后续同单图编辑）
```
- **多参考**: 用 ImageStitch 拼接多张参考图

### 2.4 img_edit_qwen — Qwen Image Edit
```
UNETLoader(qwen_image_edit_2509) → MODEL
CLIPLoader(qwen_2.5_vl_7b, type=qwen_image) → CLIP
VAELoader(qwen_image_vae) → VAE
CFGNorm(1) + ModelSamplingAuraFlow(3) + LoRA(Lightning-4steps) → MODEL
LoadImage → IMAGE
ImageScaleToTotalPixels(1M) → scaled IMAGE
VAEEncode(IMAGE) → LATENT
TextEncodeQwenImageEditPlus(IMAGE, text) → CONDITIONING
KSampler(steps=4, cfg=1, euler, simple) → LATENT
VAEDecode → IMAGE
```
- **特殊编码器**: TextEncodeQwenImageEditPlus 同时接收图片和文本

### 2.5 img_edit_qwen_2512 — Qwen Image 2512 最新版
- 同 2.4 但使用 qwen_image_edit_2512 模型
- 可能有新的 ControlNet patch 支持

## 三、ControlNet 控制生成 — 5 种

### 3.1 controlnet_sdxl — 标准 ControlNet
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
ControlNetLoader → CONTROL_NET
LoadImage → IMAGE
AIO_Preprocessor(Canny/Depth/Pose) → processed IMAGE
CLIPTextEncode(+/-) → CONDITIONING
ControlNetApplyAdvanced(+COND, -COND, CN, IMAGE, strength=0.85) → modified CONDITIONING
EmptyLatentImage → LATENT
KSampler(modified MODEL, modified +COND, modified -COND) → LATENT
```
- ✅ 已验证 | **预处理器**: CannyEdge, DepthAnything, OpenPose, Scribble, Tile 等

### 3.2 controlnet_union — ControlNet-Union
- 单个模型支持多种控制模式（Canny+Depth+Pose 等）
- 模型: xinsir-controlnet-union-sdxl-1.0-promax

### 3.3 controlnet_multi — 多 ControlNet 混合
```
ControlNetApplyAdvanced(CN1) → CONDITIONING_1
ControlNetApplyAdvanced(CN2, input=CONDITIONING_1) → CONDITIONING_2
（链式连接，每个 CN 接收前一个的输出）
```
- ✅ 已验证 | 可叠加 Canny + Depth + Pose 等

### 3.4 controlnet_qwen — Qwen ControlNet
- Qwen Image + InstantX ControlNet / Union Control LoRA
- 支持 inpainting ControlNet

### 3.5 controlnet_flux_depth — Flux Depth ControlNet
- Flux.1 Dev + Depth LoRA
- flux_depth_lora_example 模板

## 四、LoRA 风格 — 4 种

### 4.1 lora_sdxl — SDXL + LoRA
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
LoraLoader(MODEL, CLIP, strength_model=0.8, strength_clip=0.8) → modified MODEL + modified CLIP
（后续用 modified MODEL/CLIP）
```
- ✅ 已验证 | **关键**: LoRA 修改 MODEL+CLIP, VAE 不变

### 4.2 lora_multi — 多 LoRA 堆叠
```
LoraLoader(LoRA1) → MODEL_1 + CLIP_1
LoraLoader(MODEL_1, CLIP_1, LoRA2) → MODEL_2 + CLIP_2
```

### 4.3 lora_flux — Flux + LoRA
```
UNETLoader → MODEL
LoraLoaderModelOnly(MODEL, lora) → modified MODEL
（Flux LoRA 通常只修改 MODEL，不修改 CLIP）
```

### 4.4 lora_qwen — Qwen + LoRA
- Qwen-Image-Edit-Lightning LoRA（4步加速）
- Qwen multi-angle LoRA

## 五、Inpaint / Outpaint — 4 种

### 5.1 inpaint_sdxl
```
LoadImage → IMAGE + MASK
VAEEncodeForInpaint(IMAGE, MASK, grow_mask_by=6) → LATENT
KSampler(denoise=1.0) → LATENT
```
- ✅ 已验证 | grow_mask_by 控制边缘过渡

### 5.2 inpaint_qwen — Qwen Inpaint
- 通过 Qwen ControlNet inpainting 模式

### 5.3 outpaint_sdxl
```
LoadImage → IMAGE
ImagePadForOutpaint(left/right/top/bottom, feathering) → padded IMAGE + MASK
VAEEncodeForInpaint(padded IMAGE, MASK) → LATENT
KSampler → LATENT
```

### 5.4 outpaint_flux — Flux Outpaint
- BFL API 风格，expand image

## 六、超分辨率 — 4 种

### 6.1 upscale_esrgan
```
UpscaleModelLoader(RealESRGAN_x4plus) → UPSCALE_MODEL
LoadImage → IMAGE
ImageUpscaleWithModel(MODEL, IMAGE) → 4x IMAGE
```
- ✅ 已验证 | 4 节点，最简单的管线

### 6.2 upscale_tile — Tile 超分
- HD_UltimateSDUpscale：分块处理大图，避免显存不足

### 6.3 upscale_creative — 创意超分
- 超分同时添加细节

### 6.4 upscale_video — 视频超分
- ltx-2-spatial-upscaler 或逐帧 ESRGAN

## 七、视频生成 — 11 种

### 7.1 video_wan21_t2v — Wan2.1 文生视频
```
UNETLoader(wan2.1_t2v) → MODEL
CLIPLoader(umt5_xxl) → CLIP
VAELoader(wan_2.1_vae) → VAE
CLIPTextEncode → CONDITIONING
EmptyHunyuanLatentVideo(width, height, frames, batch) → VIDEO_LATENT
KSampler(uni_pc_bh2, simple) → VIDEO_LATENT
VAEDecode → VIDEO_FRAMES → VHS_VideoCombine
```

### 7.2 video_wan21_i2v — Wan2.1 图生视频
```
+ LoadImage → IMAGE
+ CLIPVisionLoader → CLIP_VISION
+ CLIPVisionEncode(IMAGE) → CLIP_VISION_OUTPUT
+ WanImageToVideo(CLIP_VISION_OUTPUT, IMAGE) → VIDEO_CONDITIONING
```

### 7.3 video_wan22_t2v — Wan2.2 文生视频 (最新!)
```
⚡ 双 UNet 架构（革命性变化）:
UNETLoader(wan2.2_t2v_high_noise) + ModelSamplingSD3 → MODEL_HIGH
UNETLoader(wan2.2_t2v_low_noise) + ModelSamplingSD3 → MODEL_LOW
LoRA(lightx2v_4steps_high_noise) → MODEL_HIGH_FAST
LoRA(lightx2v_4steps_low_noise) → MODEL_LOW_FAST

KSamplerAdvanced(MODEL_HIGH, start=0, end=0.5) → LATENT_MID
KSamplerAdvanced(MODEL_LOW, LATENT_MID, start=0.5, end=1.0) → LATENT_FINAL

CreateVideo + SaveVideo
```
- **核心创新**: 高噪声模型处理前半段，低噪声模型精修后半段
- **4步 LoRA**: 大幅加速（从30+步到4步）

### 7.4 video_wan22_i2v — Wan2.2 图生视频
- 同 7.3 但加 WanImageToVideo 节点

### 7.5 video_wan22_flf2v — 首尾帧生视频
- 给定第一帧和最后一帧，生成中间过渡视频

### 7.6 video_ltx2_t2v — LTX-2 文生视频
```
DualCLIPLoaderGGUF(gemma_3_12B + ltx-2-embeddings) → CLIP
UnetLoaderGGUF(LTX-2-dev) → MODEL
VAELoader(LTX2_video_vae) → VAE
LoraLoaderModelOnly(ltx-2-distilled) → MODEL
CFGGuider + SamplerCustomAdvanced → LATENT
VAEDecodeTiled → VIDEO
```

### 7.7-7.8 video_ltx2_i2v / flf2v
- LTX-2 的图生视频和首尾帧变体

### 7.9 video_hunyuan_t2v — HunyuanVideo 文生视频
### 7.10 video_hunyuan_i2v
### 7.11 video_cogvideo_t2v — CogVideoX

## 八、动画/动作迁移 — 4 种

### 8.1-8.3 SeeDance 系列
- SeeDance 2.0: Bytedance 的动作控制模型
- 支持 T2V / I2V / FLF2V

### 8.4 motion_liveportrait — LivePortrait 面部动画
- 驱动图: 视频或另一张图的表情/姿态
- 输出: 源人物做出驱动动作的视频

## 九、面部 — 2 种

### 9.1 face_swap — 换脸
- ReActor 或 InsightFace 节点
- LoadImage(source) + LoadImage(target) → FaceSwap → SaveImage

### 9.2 face_portrait_light — 人像打光
- 控制光线方向和强度

## 十、音频 — 5 种

### 10.1 audio_t2a_song — ACE-Step 文生歌曲
```
CheckpointLoaderSimple(ace_step_v1_3.5b) → MODEL + CLIP + VAE
TextEncodeAceStepAudio(lyrics + tags) → CONDITIONING
ConditioningZeroOut → zero CONDITIONING
EmptyAceStepLatentAudio(duration) → AUDIO_LATENT
LatentApplyOperationCFG + LatentOperationTonemapReinhard → modified MODEL
ModelSamplingSD3 → modified MODEL
KSampler(steps=50, cfg=5, euler, simple) → AUDIO_LATENT
VAEDecodeAudio → AUDIO → SaveAudio
```
- **特殊**: 音频用 Latent 空间生成，KSampler 采样过程与图像相同！

### 10.2 audio_tts_chatterbox — TTS
### 10.3 audio_tts_qwen3 — Qwen3 TTS 声音克隆
```
Qwen3TTSModelLoader → MODEL
LoadAudio(reference) → AUDIO
AudioCrop(AUDIO) → cropped AUDIO
Apply_Whisper → text transcript
Qwen3TTSVoiceClone(MODEL, AUDIO, text) → cloned AUDIO
SaveAudio
```

### 10.4 audio_sound_effects
### 10.5 audio_inpaint

## 十一、3D 生成 — 1 种

### 11.1 3d_hunyuan — Hunyuan3D 2.1
```
ImageOnlyCheckpointLoader(hunyuan_3d_v2.1) → MODEL + CLIP_VISION + VAE
LoadImage → IMAGE
CLIPVisionEncode(IMAGE) → CLIP_VISION_OUTPUT
Hunyuan3Dv2Conditioning(CLIP_VISION_OUTPUT) → CONDITIONING
ModelSamplingAuraFlow → modified MODEL
EmptyLatentHunyuan3Dv2 → 3D_LATENT
KSampler(steps=30, cfg=5, euler, normal) → 3D_LATENT
VAEDecodeHunyuan3D → 3D_VOXEL
VoxelToMesh → MESH (.obj/.glb)
```
- **输入**: 单张图片 → **输出**: 3D 网格模型
- **特殊**: ImageOnlyCheckpointLoader（不需要文本，用图片作为条件）

## 十二、融合工作流 — 3 种

### 12.1 fusion_cn_lora_upscale
```
Checkpoint → LoRA(MODEL+CLIP) → ControlNet(CONDITIONING) → KSampler → Upscale(IMAGE)
```
- ✅ 已验证 14节点 | 三种技术自由组合

### 12.2 fusion_qwen_edit_upscale
### 12.3 fusion_video_upscale

---

## 模型架构对比

| 特征 | SD1.5/SDXL | Flux.1 | Flux.2 Klein | Qwen Image | Wan2.2 |
|------|-----------|--------|-------------|------------|--------|
| 加载器 | CheckpointLoaderSimple | DualCLIP+UNET+VAE | CLIPLoader(flux2)+UNET+VAE | CLIPLoader(qwen)+UNET+VAE | CLIPLoader+UNET+VAE |
| 文本编码器 | CLIP | CLIP_L+T5XXL | Qwen3-4B/8B | Qwen2.5-VL-7B | UMT5-XXL |
| 采样器 | KSampler | SamplerCustomAdvanced | SamplerCustomAdvanced | KSampler | KSamplerAdvanced(双) |
| CFG | 7-8 | FluxGuidance(3.5) | CFGGuider(5/1) | CFGNorm(1) | 标准 |
| Steps | 20-30 | 20-50 | 4-20 | 4 | 4(LoRA)/30+ |
| 调度器 | karras | simple | simple | simple | simple |
| 潜空间 | EmptyLatentImage | EmptySD3Latent | EmptyFlux2Latent | EmptySD3Latent | EmptyHunyuanLatentVideo |
