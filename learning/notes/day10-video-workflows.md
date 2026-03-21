# Day 10 续 — ComfyUI 视频生成工作流深度学习

> 日期: 2026-03-21 | 路径纠正: bobooo 指出不应用封装 API，应学 ComfyUI 工作流中的视频生成

## 🔴 纠正记录

**我的错误**: 用 RunningHub 标准 API (rhart-video-s) 调用视频生成就说"图生视频实验完成"
**正确路径**: 在 ComfyUI 工作流中通过以下方式做视频生成：
1. **API 节点** — ComfyUI 内调用 Kling/Seedance/Veo3.1 等商业模型
2. **LTX 本地工作流** — 开源视频模型 LTX-2，在 ComfyUI 内本地运行
3. **AnimateDiff** — 在 SD 工作流基础上加运动模块

## ComfyUI 视频生成方案全景

### 方案 A: API 节点（调用外部商业模型）

ComfyUI 支持 Partner Nodes / API Nodes，在工作流内调用外部模型 API。

#### 1. Kling 3.0 (快手)
- **ComfyUI 节点**: 内置 Partner Node，需登录 comfy.org 账号
- **能力**: 多镜头生成 / 主体一致性 / 多语言音频+口型同步 / 原生文字渲染
- **模型**:
  - Kling Video 3.0 (标准视频)
  - Kling Video 3.0 Omni (音视频联合)
  - Kling Image 3.0 / 3.0 Omni
- **工作流模板**:
  - I2V: `api_kling_v3_i2v.json`
  - Omni Video Edit: `api_kling_v3_omni_video_edit.json`
- **核心节点链路**: LoadImage → KlingVideo3.0 → SaveVideo
- **RunningHub 可用**: `kling-v3.0-pro/image-to-video`，支持 3-15 秒，带声音

#### 2. Seedance 1.5 Pro (字节跳动)
- **ComfyUI 节点**: `ComfyUI-Seedance` 或 `ComfyUI-fal-API` (fal.ai 封装)
- **能力**: 高质量图生视频 / 文生视频 / 参考视频
- **节点类型**:
  - `SeedanceImageToVideo_fal` — 图生视频
  - `SeedanceTextToVideo_fal` — 文生视频
  - `ConfigGenerateVideoSeedanceProI2V` — 高级配置
- **RunningHub 可用**: `seedance-v1.5-pro/image-to-video`

#### 3. Veo 3.1 (Google)
- **ComfyUI 节点**: `ComfyUI-fal-API` 中的 `Veo3_fal` 节点
- **能力**: Google 最新视频生成模型，文本→视频
- **特点**: 需要 fal.ai API key

### 方案 B: LTX-2 本地工作流（开源，需 GPU）

**LTX-2.3 (Lightricks)** — 目前最强的开源视频生成模型之一

- **ComfyUI 集成**: 已内置到 ComfyUI core (`comfy/ldm/lightricks/`)
- **额外节点**: `ComfyUI-LTXVideo` 仓库提供高级功能
- **硬件要求**: 32GB+ VRAM, 100GB+ 磁盘空间

#### 核心模型
| 模型 | 大小 | 速度 | 质量 | 推荐 |
|------|------|------|------|------|
| ltx-2.3-22b-distilled | ~22B | 快 | 好 | ✅ 入门推荐 |
| ltx-2.3-22b-dev | ~22B | 慢 | 最佳 | 最终渲染 |

#### 工作流类型
1. **Text/Image to Video (单阶段)** — 基础生成
2. **Two Stage (with Upsampling)** — 先低分辨率生成，再空间+时间上采样
3. **IC-LoRA Union Control** — 深度图 + 人体姿态 + 边缘控制
4. **IC-LoRA Motion Track** — I2V 运动追踪

#### LTX 工作流核心节点链
```
CheckpointLoader (LTX-2.3)
    → LTXVModelLoader
    → TextEncoder (Gemma 3 12B)
    → LTXVSampler (steps, cfg, denoise)
    → LTXVDecoder
    → SaveVideo

可选: SpatialUpscaler (x1.5/x2) + TemporalUpscaler (x2)
```

#### 关键参数
- **frames**: 41-81 帧（入门建议少帧快速迭代）
- **resolution**: 480×720 (快速) → 720×1280 (正式)
- **steps**: distilled 模型 6-8 步，full 模型 25-50 步
- **cfg**: distilled ~1.0, full ~3.5-7.0
- **文本编码器**: Gemma 3 12B IT (新) 替代 T5XXL

### 方案 C: AnimateDiff（基于 SD 的运动模块）

- 在已有的 SD/SDXL text2img 工作流上加 AnimateDiff 运动模块
- 适合：已有图片生成工作流，想加动画效果
- 核心节点: `AnimateDiffLoader` + `AnimateDiffSampler`
- 运动模型: mm_sd_v14/v15, mm_sdxl_v10
- 我在 Day 11 课程中会深入学习

## 模型选择决策树

```
需要视频生成？
├─ 有 API 预算？
│  ├─ 要最高质量？→ Kling 3.0 Pro / Veo 3.1
│  ├─ 要性价比？→ Seedance 1.5 Pro
│  └─ 要音频+口型同步？→ Kling 3.0 Omni
├─ 有 GPU (32GB+)？
│  └─ LTX-2.3 本地工作流（免费，可控性最强）
└─ 只有 SD 级 GPU？
   └─ AnimateDiff（轻量，但质量较低）
```

## RunningHub 实操：模型升级对比

### 实验 13: 可灵 3.0 Pro 图生视频
- 输入: 赛博朋克狗图 (experiment-04)
- 参数: duration=5s, cfgScale=0.5, sound=true
- 对比: rhart-video-s (实验09) vs kling-v3.0-pro (实验13)

### 实验 14: Seedance 1.5 Pro 图生视频
- 输入: 赛博朋克狗图 (experiment-04)
- 参数: duration=5s, resolution=720p, generateAudio=true, cameraFixed=false
- 耗时: 70s, 费用: ¥0.30

### 三模型视频对比

```
模型               耗时    费用    声音   动态效果
─────────────────────────────────────────────────────
rhart-video-s      185s   ¥0.10   ❌    主体基本不动，雨滴闪烁
Kling 3.0 Pro      135s   ¥0.75   ✅    主体有动作，场景丰富
Seedance 1.5 Pro    70s   ¥0.30   ✅    快速，质量好，动作自然
```

**结论**: Seedance 性价比最优（速度快+便宜+质量好），Kling 质量最高但贵

## 学习路径纠正

### 原路径（已弃用）
Day 10 → 标准 API 调用 ❌
Day 11 → AnimateDiff 理论 ❌

### 新路径（bobooo 纠正后）
```
Day 10 ✅ RunningHub 标准 API 基础实操（已完成）
Day 10 续 ✅ 视频生成方案全景学习 + Kling/Seedance 对比实验
Day 11 → LTX-2 工作流深度学习（通过 RunningHub AI App 或 ComfyUI Cloud）
Day 12 → ComfyUI API 节点体系（Partner Nodes / fal.ai 集成）
Day 13 → AnimateDiff 工作流（基于 SD 的运动模块）
Day 14 → 自定义节点开发（Python API）
Day 15 → Flux / SD3 新架构
Day 16 → 综合实战：从零编排完整视频生成工作流
```

### 核心变化
1. ❌ 不要只调封装 API → ✅ 要在 ComfyUI 工作流中编排视频节点
2. ❌ 不要只学理论 → ✅ 每个工作流必须在 RunningHub 跑通
3. ❌ 不要跳过商业 API 节点 → ✅ Kling/Seedance/Veo3.1 都要实操
4. ✅ 每天更新学习仓库到 GitHub
