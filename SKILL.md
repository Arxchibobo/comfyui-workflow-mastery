# ComfyUI Workflow Mastery

## Description
ComfyUI 工作流大师 — 从零编译任意 ComfyUI 工作流并通过 RunningHub API 执行。覆盖文生图、图生图、LoRA、ControlNet、Inpaint、Outpaint、超分、Flux、视频生成等全场景。

## Trigger Conditions
- 用户要求生成/编辑图片、视频
- 涉及 ComfyUI、工作流、节点
- 涉及 RunningHub 平台
- "帮我画"、"生成一张"、"风格转换"、"超分辨率"、"去水印"、"局部重绘"
- "做个视频"、"图生视频"、"文生视频"

## Core Architecture

### 节点系统基础
ComfyUI 使用**节点图（Node Graph）**模式，每个节点有输入和输出，通过连线传递数据。

#### 5 种核心数据类型
| 类型 | 说明 | 来源节点 | 消费节点 |
|------|------|---------|---------|
| MODEL | 扩散模型权重（UNet） | CheckpointLoaderSimple[0], UNETLoader[0], LoraLoader[0] | KSampler, LoraLoader |
| CLIP | 文本编码器 | CheckpointLoaderSimple[1], CLIPLoader[0], DualCLIPLoader[0] | CLIPTextEncode, LoraLoader |
| VAE | 潜空间↔像素编解码器 | CheckpointLoaderSimple[2], VAELoader[0] | VAEEncode, VAEDecode |
| CONDITIONING | 文本嵌入向量（引导生成方向） | CLIPTextEncode[0], ControlNetApplyAdvanced[0,1] | KSampler, ControlNetApplyAdvanced |
| LATENT | 潜空间张量 | EmptyLatentImage[0], VAEEncode[0], KSampler[0] | KSampler, VAEDecode |
| IMAGE | 像素图像 | LoadImage[0], VAEDecode[0], ImageUpscaleWithModel[0] | SaveImage, VAEEncode, AIO_Preprocessor |
| CONTROL_NET | ControlNet 模型 | ControlNetLoader[0] | ControlNetApplyAdvanced |
| UPSCALE_MODEL | 超分模型 | UpscaleModelLoader[0] | ImageUpscaleWithModel |

### 连接语法（API Format）
```json
{
  "node_id": {
    "class_type": "NodeClassName",
    "inputs": {
      "static_param": "value",
      "connected_input": ["source_node_id", output_index]
    }
  }
}
```
- Node ID 是**字符串**
- 连接用 `["source_node_id", output_index]` 表示
- `output_index` 是整数，对应来源节点的第几个输出

## Workflow Patterns（已验证可执行）

### Pattern 1: Text2Img（文生图）
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
                       ↓ CLIP
              CLIPTextEncode (positive) → CONDITIONING
              CLIPTextEncode (negative) → CONDITIONING
EmptyLatentImage → LATENT
                       ↓
KSampler(MODEL, +COND, -COND, LATENT) → denoised LATENT
VAEDecode(LATENT, VAE) → IMAGE
SaveImage(IMAGE) → file
```
- **节点数**: 7
- **关键参数**: steps=20-30, cfg=7-8, sampler=dpmpp_2m_sde, scheduler=karras, denoise=1.0

### Pattern 2: Img2Img（图生图）
```
与 Text2Img 相同，但替换 EmptyLatentImage 为:
LoadImage → IMAGE
VAEEncode(IMAGE, VAE) → LATENT (编码原图到潜空间)
KSampler.denoise = 0.3~0.8 (保留原图结构)
```
- **节点数**: 8
- **关键参数**: denoise=0.3(轻微) / 0.5(中等) / 0.8(大改)

### Pattern 3: LoRA（风格叠加）
```
CheckpointLoaderSimple → MODEL + CLIP + VAE
LoraLoader(MODEL, CLIP) → modified MODEL + modified CLIP
(后续用 modified MODEL/CLIP, VAE 不变)
```
- **节点数**: 8
- **关键**: LoRA 修改 MODEL 和 CLIP，不修改 VAE
- **链式堆叠**: 多个 LoraLoader 串联即可叠加多个 LoRA

### Pattern 4: ControlNet（空间控制）
```
ControlNetLoader → CONTROL_NET
LoadImage → IMAGE (控制图)
AIO_Preprocessor(IMAGE) → preprocessed IMAGE (可选：提取边缘/深度/姿态)
CLIPTextEncode → base CONDITIONING
ControlNetApplyAdvanced(+COND, -COND, CONTROL_NET, IMAGE)
  → modified +CONDITIONING, modified -CONDITIONING
KSampler(MODEL, modified +COND, modified -COND, LATENT)
```
- **节点数**: 11
- **关键**: ControlNet 修改 CONDITIONING（不是 MODEL）
- **strength**: 0.0-1.0, 控制空间约束强度
- **start/end_percent**: 控制在采样过程的哪些步骤应用 CN
- **多 CN 混合**: 链式连接多个 ControlNetApplyAdvanced

### Pattern 5: Inpaint（局部重绘）
```
LoadImage → IMAGE + MASK (alpha 通道)
VAEEncodeForInpaint(IMAGE, MASK, VAE, grow_mask_by=6) → LATENT (含 mask 信息)
KSampler(denoise=1.0) → 只重绘 mask 区域
```
- **关键节点**: `VAEEncodeForInpaint`（不是 VAEEncode！）
- grow_mask_by: 扩展 mask 边界像素数（平滑过渡）

### Pattern 6: Upscale（超分辨率）
```
UpscaleModelLoader → UPSCALE_MODEL
LoadImage → IMAGE
ImageUpscaleWithModel(UPSCALE_MODEL, IMAGE) → 4x IMAGE
SaveImage
```
- **节点数**: 4（最简单的管线！）
- 不需要 KSampler，纯像素空间处理
- 模型: RealESRGAN_x4plus.pth（4倍放大）

### Pattern 7: Fusion（技术融合）
```
Checkpoint → LoRA → modified MODEL/CLIP
modified CLIP → CLIPTextEncode → CONDITIONING
ControlNet + CONDITIONING → modified CONDITIONING
modified MODEL + modified CONDITIONING → KSampler → LATENT
LATENT → VAEDecode → IMAGE → Upscale → 4K IMAGE
```
- **14 节点**: ControlNet + LoRA + Upscale 全融合
- **原理**: LoRA 修改 MODEL/CLIP, ControlNet 修改 CONDITIONING, Upscale 处理 IMAGE
- 三种技术作用于不同数据类型，天然可组合

### Pattern 8: Flux-style（低 CFG 快速生成）
```
与 Text2Img 相同结构，但参数不同:
- cfg=1 (Flux/distilled 模型特征)
- sampler=euler
- scheduler=simple
- steps=4-8 (大幅减少)
```

### Pattern 9: Video（视频生成，Wan2.x/LTX-2）
- T2V: UNETLoader + CLIPLoader + VAELoader → EmptyHunyuanLatentVideo → KSampler
- I2V: 加 WanImageToVideo + CLIPVision
- 使用 uni_pc_bh2 sampler, simple scheduler

## Agent Calling Flow

### Step 1: 理解需求
解析用户请求，映射到 pattern:
- "画一个..." → text2img
- "把这张图变成..." → img2img
- "用XX风格" → lora 或 img2img
- "按照这个姿势/结构" → controlnet
- "修改这个区域" → inpaint
- "放大/高清化" → upscale
- "做个视频" → video

### Step 2: 编译工作流
```bash
python3 scripts/workflow_compiler.py \
  --pipeline <pattern> \
  --prompt "描述" \
  --negative "负面提示词" \
  [--image <url>] \
  [--control-image <url>] \
  [--lora-name <name>] \
  [--width 1024 --height 1024] \
  [--steps 25 --cfg 7.5] \
  [--denoise 0.5]  # img2img only
```

### Step 3: 执行
编译器自动执行以下流程：
1. 上传输入图片（如有）→ RunningHub
2. 构建 API format JSON
3. 保存到 workspace
4. 提交任务
5. 轮询等待完成
6. 下载输出文件

### Step 4: 交付
用 `message` tool 发送图片给用户（不暴露 RunningHub URL）。

## Available Pipelines

| Pipeline | 说明 | 节点数 | 需要图片 |
|----------|------|--------|---------|
| text2img | 文生图 | 7 | ❌ |
| img2img | 图生图 | 8 | ✅ |
| text2img+lora | 文生图+LoRA | 8 | ❌ |
| controlnet | ControlNet 控制 | 11 | ✅ |
| multi_controlnet | 多 ControlNet | 15 | ✅ |
| inpaint | 局部重绘 | 8 | ✅ (+mask) |
| outpaint | 扩展画布 | 9 | ✅ |
| upscale | 超分辨率 | 4 | ✅ |
| text2img+upscale | 文生图+超分 | 11 | ❌ |
| flux | Flux-style 快速 | 7 | ❌ |
| wan_t2v | 文生视频 | 9 | ❌ |
| wan_i2v | 图生视频 | 11 | ✅ |
| fusion | 自由组合 | 10-20 | 视情况 |

## KSampler Parameter Guide

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| steps | 去噪迭代次数 | 20-30 (SD), 4-8 (Flux) |
| cfg | 文本引导强度 | 7-8 (SD), 1 (Flux) |
| sampler_name | 采样算法 | dpmpp_2m_sde (质量), euler (速度) |
| scheduler | 噪声调度 | karras (推荐), simple (Flux) |
| denoise | 去噪强度 | 1.0 (文生图), 0.3-0.8 (图生图) |
| seed | 随机种子 | -1=随机, 固定值=可复现 |

## Model Compatibility

### SD1.5 系列
- 512x512 默认，可到 768x768
- 标准 KSampler 参数

### SDXL 系列
- 1024x1024 默认
- 用 dpmpp_2m_sde + karras
- 模型: maximumEffort_maximumEffortXLV10.safetensors

### Flux 系列
- cfg=1, euler, simple, 4-8 steps
- 部分需要 DualCLIPLoader + UNETLoader (分离加载)
- 模型: WuJi_Qwen2511-AIONSFW聚合版_2603.safetensors

### Video 模型
- Wan2.x: UNETLoader + CLIPLoader + VAELoader
- LTX-2: DualCLIPLoaderGGUF + UnetLoaderGGUF + VAELoader
- uni_pc_bh2 sampler, simple scheduler

## RunningHub Integration

### API Endpoints (internal, never expose to users)
- Upload: `/task/openapi/upload` (form-data, apiKey as field)
- Create: `/task/openapi/create` (workflowId + nodeInfoList)
- Status: `/task/openapi/status` (taskId polling)
- Outputs: `/task/openapi/outputs` (get result URLs)

### Execution Method
1. 编译 API format JSON
2. 通过 `setContent(contentType=1)` 保存到 workspace
3. 通过 `create(workflowId=workspace_id)` 执行
4. 轮询 status 直到 SUCCESS
5. 从 outputs 获取结果 URL

### Environment
```
RUNNINGHUB_API_KEY — RunningHub API密钥
RUNNINGHUB_WORKSPACE_ID — 工作流空间ID
```

## Files

| 文件 | 用途 |
|------|------|
| `scripts/workflow_compiler.py` | 核心编译器：从高级描述编译完整工作流 |
| `scripts/comfyui_workflow.py` | 执行器：模板选择→参数构建→提交→轮询 |
| `scripts/workflow_composer.py` | 组合器：template API format + 参数修改 |
| `data/templates.json` | 官方模板参数映射 |
| `data/node_database.json` | 节点类型数据库（206种节点） |
| `knowledge-base/deep-learning-guide.md` | 深度学习指南 |
| `knowledge-base/workflow-patterns.md` | 工作流拓扑模式 |
| `knowledge-base/node-reference.md` | 节点参考手册 |
| `knowledge-base/runninghub-workflows.md` | RunningHub 热门分析 |
| `knowledge-base/model-compatibility.md` | 模型兼容性指南 |

## Verified Test Results

All 8 workflow types verified with from-scratch compilation:

| Phase | Pipeline | Nodes | Time | Status |
|-------|----------|-------|------|--------|
| 1 | text2img | 7 | 30s | ✅ |
| 2 | img2img | 8 | 12s | ✅ |
| 3 | text2img+lora | 8 | 12s | ✅ |
| 4 | controlnet | 11 | 12s | ✅ |
| 5 | inpaint | 8 | 14s | ✅ |
| 6 | upscale | 4 | 12s | ✅ |
| 7 | fusion (CN+LoRA+Upscale) | 14 | 11s | ✅ |
| 8 | flux-style | 7 | 12s | ✅ |

## Extended Verification Results (Round 2)

### New Pipelines
| Test | Pipeline | Nodes | Time | Status |
|------|----------|-------|------|--------|
| 9 | Qwen-style Img Edit (WuJi + cfg=1) | 8 | 45s | ✅ |
| 10 | WuJi + 可爱娃娃手办 LoRA | 8 | 11s | ✅ |

### Fusion Combinations (Novel Topologies)
| Test | Fusion | Nodes | Time | Status |
|------|--------|-------|------|--------|
| 11 | Img2Img + LoRA | 9 | 10s | ✅ |
| 12 | Img2Img + ControlNet | 11 | 11s | ✅ |
| 13 | Inpaint + Upscale | 10 | 10s | ✅ |
| 14 | **Text2Img + LoRA + ControlNet + Upscale (4-way)** | 14 | 10s | ✅ |
| 15 | Outpaint + Upscale | 11 | 10s | ✅ |
| 16 | Multi-LoRA(x2) + ControlNet | 13 | 10s | ✅ |
| 17 | WuJi(Flux) + LoRA + Upscale | 10 | 10s | ✅ |

### Total: 17/17 tests passed (8 original + 9 extended)
