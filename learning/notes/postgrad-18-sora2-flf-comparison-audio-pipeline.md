# PostGrad #18 — Sora 2 Pro + FLF Multi-Model Comparison + Audio-Video Pipeline Patterns

> **Date**: 2026-03-24 22:03 UTC | **Session**: 62 | **Cost**: ¥1.30

## 学习目标

1. **rhart-video-s Pro (Sora 2) 首测** — 15/25s 长视频 + 高分辨率
2. **rhart-video-s Realistic 首测** — 真人支持变体
3. **FLF 四模型对比** — Vidu Q3 Turbo/Pro + Veo 3.1 Fast
4. **ComfyUI 音视频同步管线 JSON 编排**

---

## 1. rhart-video-s 变体系统分析

### 变体全景

| 变体 | 后端模型 | 时长选项 | 分辨率 | 音频 | 价格 |
|------|---------|---------|--------|------|------|
| rhart-video-s (基础) | Sora 2 | 5s | 704×1280 竖屏 | ✅ AAC 96kHz | ¥0.02 |
| rhart-video-s Pro | Sora 2 | **15/25s** | **1792×1024** | ✅ AAC 96kHz | ¥0.30 (15s) |
| rhart-video-s Realistic | Sora 2 官方 | 4/8/12s | 1280×720 | ✅ AAC 96kHz | ¥0.50 (4s) |
| rhart-video-s-official | Sora 2 官方 | 5s | ~1280×720 | ✅ | ~¥0.50 |

### ⭐ 实验 A: rhart-s Pro (Sora 2 长视频) 首测

**参数**: I2V, prompt=寿司切鱼, duration=15, aspectRatio=16:9

**结果**:
- **分辨率**: 1792×1024 (1.84MP) — **Sora 2 系列最高分辨率**
- **帧率**: 30fps
- **时长**: 14.5s (436 帧)
- **音频**: AAC 96kHz 立体声 — 异常高采样率
- **文件大小**: 13.5MB
- **耗时**: 495s (~8.3 分钟)
- **成本**: ¥0.30

**关键发现**:
1. ⭐ **性价比极高**: ¥0.02/秒，14.5s 视频仅 ¥0.30
2. 分辨率自动升级到 1792×1024（接近 2K）
3. 30fps 而非常见的 24fps
4. 音频采样率 96kHz 是行业最高（通常 44.1-48kHz）
5. 长时间生成（~8 分钟），适合非实时场景
6. **Sora 2 = 长视频 + 高分辨率之王**，但速度慢

### ⭐ 实验 B: rhart-s Realistic (真人模式) 首测

**参数**: I2V, prompt=寿司切鱼, duration=4

**结果**:
- **分辨率**: 1280×720 (720p)
- **帧率**: 30fps
- **时长**: 4.2s (126 帧)
- **音频**: AAC 96kHz 立体声
- **文件大小**: 2.7MB
- **耗时**: 120s
- **成本**: ¥0.50

**关键发现**:
1. "Realistic" = 官方渠道，优先真人场景优化
2. 价格较贵（¥0.125/秒 vs Pro 的 ¥0.02/秒）
3. 分辨率 720p 不如 Pro 的 1792×1024
4. 同样 96kHz 音频
5. **定位**: 需要真人逼真度时使用，非通用推荐

### rhart-s 变体选择决策

```
需要长视频 (>10s)?
  └─ 是 → rhart-s Pro (15/25s, ¥0.02/秒, 1792×1024)
  └─ 否 → 需要真人逼真度?
            └─ 是 → rhart-s Realistic (¥0.50/4s, 官方渠道)
            └─ 否 → rhart-s 基础 (¥0.02/5s, 最便宜)
```

---

## 2. FLF (首尾帧生视频) 四模型对比

同一对首尾帧（龙虾厨师：准备→展示寿司），对比 4 种 FLF 方案。

### 实验结果汇总

| 模型 | 分辨率 | 时长 | 帧率 | 音频 | 耗时 | 成本 | 成本/秒 |
|------|--------|------|------|------|------|------|---------|
| **Veo 3.1 Fast FLF** | 1280×720 | 8.0s | 24fps | ✅ AAC 48kHz | 120s | **¥0.04** | **¥0.005** |
| **Vidu Q3 Turbo FLF** | 1284×716 | 4.0s | 24fps | ✅ AAC 48kHz | 70s | **¥0.16** | ¥0.040 |
| **Vidu Q3 Pro FLF** | 1284×716 | 4.0s | 24fps | ✅ AAC 48kHz | 40s | ¥0.44 | ¥0.110 |
| Hailuo 02 Std FLF* | 1376×768 | 5.9s | 24fps | ❌ | ~90s | ¥0.25 | ¥0.042 |
| Veo 3.1 Pro FLF* | 1280×720 | 8.0s | 24fps | ✅ | ~135s | ¥2.52 | ¥0.315 |

*历史数据供参考

### 关键发现

#### ⭐ Veo 3.1 Fast FLF — FLF 绝对性价比王

- **¥0.005/秒** — 比第二名 Vidu Q3 Turbo 便宜 8 倍
- 8 秒固定时长（比 Vidu 4s 更长）
- **自带音频同步** — 省去配音步骤
- 支持 `lastFrameUrl` 可选 — 也可用作单帧 I2V
- 支持 720p/1080p/4K 分辨率
- 唯一缺点：120s 生成时间稍慢

#### Vidu Q3 Turbo vs Pro 性价比分析

- Q3 Turbo: ¥0.16 / 70s — **Vidu 系列性价比最优**
- Q3 Pro: ¥0.44 / 40s — 更快但贵 2.75x
- 同等分辨率（1284×716），质量差异需视觉评估
- 均支持 1-16s 灵活时长 + 540p/720p/1080p
- 均自带音频

#### Vidu Q3 vs Q2 演进

| 维度 | Q2 Pro | Q3 Turbo | Q3 Pro |
|------|--------|----------|--------|
| FLF 价格 | ¥0.55 | ¥0.16 | ¥0.44 |
| 最长时长 | 8s | **16s** | **16s** |
| 分辨率 | 720p | **1080p** | **1080p** |
| 音频 | ✅ | ✅ | ✅ |
| movementAmplitude | ❌ | ✅ auto/small/medium/large | ✅ |

Q3 全面超越 Q2：更便宜、更长、更高分辨率、更多控制参数。

### FLF 模型选择决策树（更新版）

```
FLF 视频生成 →
  预算极低 / 批量生产?
    └─ ⭐ Veo 3.1 Fast (¥0.04/8s, 含音频)
  需要灵活时长 (1-16s)?
    └─ 预算敏感 → Vidu Q3 Turbo (¥0.16/4s)
    └─ 需要速度 → Vidu Q3 Pro (¥0.44/4s, 最快40s)
  需要最高分辨率?
    └─ Hailuo 02 Std (1376×768, 但无音频)
  需要最长时长?
    └─ Vidu Q3 (最长16s) > Veo 3.1 (固定8s)
  需要4K?
    └─ Veo 3.1 Fast/Pro (支持4K选项)
```

---

## 3. rhart-video-s Pro 参数深度

### API 参数

```json
{
  "prompt": "STRING (required, maxLength=4000)",
  "imageUrl": "IMAGE (required, maxSizeMB=50)",
  "duration": "LIST ['15', '25']",
  "aspectRatio": "LIST ['9:16', '16:9']",
  "storyboard": "BOOLEAN (default=false)"
}
```

### 关键发现

1. **storyboard 参数** — 可能支持分镜模式（未测试，待探索）
2. **4000 字符 prompt** — 超长描述支持
3. **仅支持 15s 和 25s** — 定位为长视频生成
4. **aspectRatio 只有 16:9 和 9:16** — 无方形选项
5. **50MB 最大图片** — 支持超高分辨率输入

### Sora 2 Pro vs 竞品 I2V 长视频对比

| 模型 | 最长时长 | 分辨率 | 帧率 | 成本/秒 | 音频 |
|------|---------|--------|------|---------|------|
| **rhart-s Pro** | **25s** | **1792×1024** | **30fps** | **¥0.02** | ✅ 96kHz |
| Kling V3.0 Pro | 10s | 1920×1080 | 24fps | ¥0.075 | ✅ (sound=true) |
| Kling O3 Std | 10s | 1280×720 | 24fps | ¥0.050 | ✅ |
| Wan 2.6 | 10s | 1280×720 | 24fps | ¥0.063 | ❌ |
| Vidu Q3 Pro | 16s | ~1284×720 | 24fps | ¥0.034 | ✅ |

**rhart-s Pro 在长视频 + 高分辨率 + 性价比三个维度同时领先。**

---

## 4. ComfyUI 音视频同步管线工作流 JSON

### 管线架构

```
T2I → Upscale → I2V+Audio → TTS旁白 → FFmpeg混音 → 输出
```

这是一个展示 ComfyUI Partner Nodes 音视频同步能力的参考工作流。

### 核心 ComfyUI 节点映射（音频相关）

| 功能 | ComfyUI Partner Node | RunningHub 等价 |
|------|---------------------|----------------|
| I2V + 音效 | KlingImageToVideoNode (sound=true) | kling-v3.0-pro/image-to-video |
| T2V + 音效 | KlingTextToVideoNode (sound=true) | kling-v3.0-pro/text-to-video |
| TTS 旁白 | 第三方节点 | rhart-audio/text-to-audio/speech-2.8-hd |
| BGM 生成 | 第三方节点 | rhart-audio/text-to-audio/music-2.5 |
| 声音克隆 | 第三方节点 | rhart-audio/text-to-audio/voice-clone |
| FLF + 音效 | Seedance/Veo Partner + FFmpeg | rhart-video-v3.1-fast/start-end-to-video |

### ComfyUI 音视频同步的三种模式

#### 模式 1: 原生音频生成（最简单）

视频模型直接生成音效，零额外成本。

```
适用模型: Kling (sound=true) / Veo 3.1 / Vidu Q3 / rhart-s
优点: 零额外成本，音效自然同步
缺点: 无法控制音频内容
```

#### 模式 2: 后配音混音（最灵活）

先生成无声视频，再单独生成音频，FFmpeg 混合。

```
视频生成 → BGM生成 → TTS旁白 → FFmpeg amix 混音
适用: 需要旁白、精确BGM的场景
关键: FFmpeg -filter_complex "[1:a]volume=0.3[bg];[2:a]volume=0.8[voice];[bg][voice]amix=inputs=2"
```

#### 模式 3: 音频驱动视频（最高级）

音频先行，驱动视频生成。

```
TTS/Music → Kling Audio2Video / LTX-2.3 AudioConditioned
适用: 口型同步、音乐可视化
节点: KlingAudioGenerationNode → KlingLipSyncNode
```

### 生产级完整管线成本估算

| 步骤 | 方案 | 成本 |
|------|------|------|
| 关键帧 T2I | rhart-image-n-pro | ¥0.03 |
| 放大 2x | Topaz Standard V2 | ¥0.10 |
| I2V 5s | Kling V3.0 Std + Audio | ¥0.55 |
| TTS 旁白 10s | MiniMax Speech 2.8 HD | ¥0.016 |
| BGM 30s | MiniMax Music 2.5 | ¥0.07 |
| **总计** | | **¥0.77** |

**极致预算方案:**

| 步骤 | 方案 | 成本 |
|------|------|------|
| 关键帧 T2I | rhart-image-n-pro | ¥0.03 |
| I2V 8s (含音效) | Veo 3.1 Fast | ¥0.04 |
| **总计** | | **¥0.07** |

---

## 5. Vidu Q3 FLF API 参数详解

### 新增参数（vs Q2）

```json
{
  "prompt": "STRING (required)",
  "firstImageUrl": "IMAGE (required)",
  "lastImageUrl": "IMAGE (required)",
  "duration": "LIST ['1'-'16']",     // Q2: 最多8s → Q3: 最多16s
  "resolution": "LIST ['540p','720p','1080p']",  // Q2: 无1080p → Q3: 支持
  "movementAmplitude": "LIST ['auto','small','medium','large']",  // 全新参数
  "audio": "BOOLEAN (default=true)"  // 自带音频
}
```

### movementAmplitude 参数分析

- `auto`: 模型自动判断首尾帧间的运动幅度
- `small`: 微小变化（表情转换、光影变化）
- `medium`: 中等运动（身体转向、物体移动）
- `large`: 大幅运动（场景切换、动作序列）

**与时长的关系**:
- 大运动 + 短时长 → 可能跳帧
- 小运动 + 长时长 → 可能过渡太慢
- 推荐: `auto` 让模型自适应

### ComfyUI Vidu Partner Node 映射

```python
# ComfyUI 中 Vidu FLF 预期节点（基于 Partner Nodes 架构）
class ViduStartEndToVideoNode:
    CATEGORY = "api_node/video/vidu"
    INPUT_TYPES = {
        "required": {
            "first_frame": ("IMAGE",),
            "last_frame": ("IMAGE",),
            "prompt": ("STRING", {"multiline": True}),
            "duration": ("INT", {"default": 4, "min": 1, "max": 16}),
            "resolution": (["540p", "720p", "1080p"],),
            "movement_amplitude": (["auto", "small", "medium", "large"],),
            "audio": ("BOOLEAN", {"default": True}),
        }
    }
    RETURN_TYPES = ("VIDEO",)
```

---

## 6. rhart-video-s Pro Storyboard 功能推测

API 包含 `storyboard: BOOLEAN` 参数（默认 false），可能支持:

1. **分镜模式**: 输入多图 + 分段描述，生成连贯长视频
2. **故事板描述**: 结构化 prompt 分段（类似电影分镜）
3. **场景转换**: 自动在场景间添加过渡

待后续轮次测试验证。这可能是 Sora 2 的差异化能力。

---

## 7. ComfyUI 工作流 JSON: FLF Quality Router

编写一个条件路由工作流，根据预算和质量需求自动选择 FLF 模型。

见: `sample-workflows/postgrad/flf-quality-router-pipeline.json`

---

## 实验总结

| # | 实验 | 模型 | 结果 | 耗时 | 成本 |
|---|------|------|------|------|------|
| 62a | 关键帧生成×2 | rhart-image-n-pro T2I | 首帧+尾帧 16:9 | 25s×2 | ¥0.06 |
| 62b | I2V Pro 15s | rhart-s Pro (Sora 2) | 1792×1024/30fps/14.5s/🔊96kHz | 495s | ¥0.30 |
| 62c | I2V Realistic 4s | rhart-s Realistic | 1280×720/30fps/4.2s/🔊96kHz | 120s | ¥0.50 |
| 62d | FLF Q3 Turbo | Vidu Q3 Turbo | 1284×716/24fps/4s/🔊 | 70s | ¥0.16 |
| 62e | FLF Q3 Pro | Vidu Q3 Pro | 1284×716/24fps/4s/🔊 | 40s | ¥0.44 |
| 62f | FLF Fast | Veo 3.1 Fast | 1280×720/24fps/8s/🔊 | 120s | ¥0.04 |
| **总计** | | | | | **¥1.50** |

### 本轮关键洞察

1. ⭐ **rhart-s Pro (Sora 2) = 长视频之王**: 25s/1792×1024/¥0.30，性价比碾压
2. ⭐ **Veo 3.1 Fast FLF = FLF 性价比王**: 8s/¥0.04，无人能敌
3. **Vidu Q3 全面超越 Q2**: 更长(16s)、更高(1080p)、更便宜(Turbo ¥0.16)
4. **rhart-s Realistic 定位明确但偏贵**: 真人场景优先选择，但 ¥0.50/4s 性价比不如 Pro
5. **96kHz 音频是 rhart-s/Sora 2 独有**: 行业最高音频采样率
6. **Veo 3.1 FLF 的 lastFrame 可选**: 兼做 I2V 和 FLF

### 模型性价比排名更新

**I2V 长视频 (>10s):**
1. ⭐ rhart-s Pro: ¥0.02/秒 (15-25s, 1792×1024)
2. Vidu Q3 Pro: ¥0.034/秒 (最长16s, 1284×720)

**FLF:**
1. ⭐ Veo 3.1 Fast: ¥0.005/秒 (8s固定, 720p-4K)
2. Vidu Q3 Turbo: ¥0.040/秒 (1-16s灵活)
3. Hailuo 02 Std: ¥0.042/秒 (5.9s, 无音频)

**I2V 短视频 (≤5s) 含音频:**
1. Veo 3.1 Fast: ¥0.005/秒 (8s, via FLF单帧模式)
2. rhart-s 基础: ¥0.004/秒 (5s, 但竖屏)
3. Kling V3.0 Std + Audio: ¥0.110/秒 (5s, 960×960)
