# RunningHub 热门工作流深度分析

## 分析范围
- 分析了 13 个工作流（5 个热门 + 7 个系统模板 + 1 个自定义）
- 发现 121 种唯一节点类型
- 覆盖：文生图、图生图、LoRA、ControlNet、超分、视频、音频、批处理、换脸等

## 工作流拓扑模式总结

###  SeeDance 2.0AI短剧漫剧专用超真实感资产道具库Qwen-image2511
- **来源**: home | **节点数**: 23
- **节点类型**: Any Switch (rgthree), CFGNorm, CR LoRA Stack, CR Prompt List, CheckpointLoaderSimple, FluxKontextMultiReferenceLatentMethod, JWInteger, KSampler, ModelSamplingAuraFlow, PrimitiveStringMultiline, RHHiddenNodes, SaveImage, TextEncodeQwenImageEditPlus, VAEDecode, VAEEncode
- **模式**: 标准扩散管线 + Flux 模型 + Qwen 图像/多角度

### Qwen3 TTS 声音克隆
- **来源**: home | **节点数**: 7
- **节点类型**: Apply Whisper, AudioCrop, LoadAudio, Qwen3TTSModelLoader, Qwen3TTSVoiceClone, SaveAudio, ShowText|pysssss
- **模式**: 音频/TTS + Qwen 图像/多角度

### 视频自动添加字幕（剪映和必剪免费接口）
- **来源**: home | **节点数**: 10
- **节点类型**: AudioSeparation, HAIGC_TimestampTextReplace, HAIGC_VideoSubtitleTimestampPro, SubtitleOptimizer, TranscribeConfig, VHS_LoadVideo, VHS_VideoCombine, VHS_VideoInfoSource, VideoTranscribe, easy showAnything
- **模式**: 视频生成/处理 + 音频/TTS

### 智能多角度生成【plus】
- **来源**: home | **节点数**: 20
- **节点类型**: CLIPLoader, ConditioningZeroOut, EmptyLatentImage, KSampler, LoadImage, LoraLoaderModelOnly, QwenMultiangleCameraNode, RHHiddenNodes, SaveImage, TextEncodeQwenImageEditPlusAdvance_lrzjason, UNETLoader, VAEDecode, VAELoader, easy imageSize
- **模式**: LoRA 风格 + Qwen 图像/多角度

### 一键生成多角色对话动画片，Qwen3-TTS + LTX-2工作流！
- **来源**: home | **节点数**: 57
- **节点类型**: Audio Duration (mtb), CFGGuider, CLIPTextEncode, CR Text, DualCLIPLoaderGGUF, EmptyImage, EmptyLTXVLatentVideo, FB_Qwen3TTSDialogueInference, FB_Qwen3TTSRoleBank, FB_Qwen3TTSVoiceClonePrompt, FB_Qwen3TTSVoiceDesign, GetImageSize, INTConstant, ImageScaleBy, KSamplerSelect
- **模式**: LoRA 风格 + 视频生成/处理 + 音频/TTS + 超分辨率 + Flux 模型 + Qwen 图像/多角度

### 文生图基础款
- **来源**: template | **节点数**: 7
- **节点类型**: CLIPTextEncode, CheckpointLoaderSimple, EmptyLatentImage, KSampler, SaveImage, VAEDecode
- **模式**: 标准扩散管线

### 图生图基础款
- **来源**: template | **节点数**: 10
- **节点类型**: CLIPTextEncode, CheckpointLoaderSimple, KSampler, LoadImage, RH_Captioner, SaveImage, TextCombinerTwo, VAEDecode, VAEEncode
- **模式**: 标准扩散管线

### 文生图+LoRA
- **来源**: template | **节点数**: 8
- **节点类型**: CLIPTextEncode, CheckpointLoaderSimple, EmptyLatentImage, KSampler, LoraLoader, SaveImage, VAEDecode
- **模式**: 标准扩散管线 + LoRA 风格

### ZIP批量上传图片，for循环处理多张图片演示实例
- **来源**: template | **节点数**: 14
- **节点类型**: Bjornulf_ShowInt, PreviewImage, RHBatchImages:, RHExtractImage, RHUploadZip, SaveImage, easy forLoopEnd, easy forLoopStart, easy imageCount, easy imageRemBg, easy showAnything
- **模式**: 自定义

### 图生图+LoRA
- **来源**: template | **节点数**: 10
- **节点类型**: CLIPTextEncode, CheckpointLoaderSimple, KSampler, LoadImage, LoraLoader, RepeatLatentBatch, SaveImage, VAEDecode, VAEEncode
- **模式**: 标准扩散管线 + LoRA 风格

### 图生图+高清修复
- **来源**: template | **节点数**: 15
- **节点类型**: CLIPTextEncode, CheckpointLoaderSimple, ImageUpscaleWithModel, KSampler, LoadImage, PreviewImage, RepeatLatentBatch, SaveImage, UpscaleModelLoader, VAEDecode, VAEEncode
- **模式**: 标准扩散管线 + 超分辨率

### ControlNet-Union
- **来源**: template | **节点数**: 93
- **节点类型**: AIO_Preprocessor, Anything Everywhere, Anything Everywhere3, CLIPTextEncode, CLIPVisionLoader, CheckpointLoaderSimple, ControlNetApplyAdvanced, ControlNetLoader, DifferentialDiffusion, EmptyLatentImage, HD UltimateSDUpscale, IPAdapterAdvanced, IPAdapterModelLoader, ImageResize+, KSampler
- **模式**: 标准扩散管线 + ControlNet 控制 + 超分辨率

### 图片对比
- **来源**: shell | **节点数**: 17
- **节点类型**: ImageComposite+, ImageCrop, ImageResizeKJ, ImageSizeInfo, LoadImage, MathExpression|pysssss, PreviewImage, VHS_VideoCombine, easy batchAnything, easy cleanGpuUsed, easy forLoopEnd, easy forLoopStart
- **模式**: 视频生成/处理


## 核心节点使用频率（Top 30）

| 节点类型 | 出现次数 | 分类 |
|---------|---------|------|
| PreviewImage | 31 | 图像I/O |
| SaveImage | 17 | 图像I/O |
| VAEDecode | 16 | VAE |
| KSampler | 16 | 采样 |
| CLIPTextEncode | 14 | 文本编码 |
| LoadImage | 8 | 图像I/O |
| HD UltimateSDUpscale | 8 | 超分 |
| ControlNetApplyAdvanced | 8 | ControlNet |
| AIO_Preprocessor | 8 | 工具 |
| CheckpointLoaderSimple | 7 | 工具 |
| QwenMultiangleCameraNode | 6 | Qwen |
| VAEEncode | 5 | VAE |
| VHS_VideoCombine | 4 | 视频 |
| EmptyLatentImage | 4 | 图像I/O |
| easy showAnything | 3 | 工具 |
| LoraLoaderModelOnly | 3 | LoRA |
| PreviewAudio | 3 | 音频 |
| TextEncodeQwenImageEditPlus | 2 | 图像I/O |
| FluxKontextMultiReferenceLatentMethod | 2 | 工具 |
| JWInteger | 2 | 工具 |
| RHHiddenNodes | 2 | 工具 |
| WujiCleaner | 2 | 工具 |
| VAELoader | 2 | VAE |
| SimpleCalculatorKJ | 2 | 工具 |
| FB_Qwen3TTSVoiceDesign | 2 | 音频 |
| SamplerCustomAdvanced | 2 | 采样 |
| RandomNoise | 2 | 工具 |
| LayerUtility: PurgeVRAM V2 | 2 | 工具 |
| LTXVSeparateAVLatent | 2 | 工具 |
| LTXVConcatAVLatent | 2 | 工具 |

## RunningHub 特色节点

### Qwen 系列（图像编辑/多角度）
- `QwenMultiangleCameraNode` - 多角度相机控制
- `TextEncodeQwenImageEditPlus` - Qwen 图像编辑文本编码
- `WujiCleaner` - 图像清理

### 音频/TTS
- `Qwen3TTSModelLoader` + `Qwen3TTSVoiceClone` - 声音克隆
- `FB_Qwen3TTSVoiceDesign` - TTS 语音设计
- `AudioSeparation` - 音频分离

### 视频
- `VHS_VideoCombine` - 视频合成
- `EmptyLTXVLatentVideo` - LTX 视频潜空间
- `SubtitleOptimizer` + `HAIGC_VideoSubtitleTimestampPro` - 字幕

### 批处理
- `RHBatchImages:` + `RHExtractImage` + `RHUploadZip` - ZIP 批处理
- `easy forLoopStart` / `easy forLoopEnd` - 循环处理

### Flux 扩展
- `FluxKontextMultiReferenceLatentMethod` - Flux Kontext 多参考
- `DualCLIPLoaderGGUF` - GGUF 格式加载
- `CFGNorm` / `CFGGuider` - CFG 控制
