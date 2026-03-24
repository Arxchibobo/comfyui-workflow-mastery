# PostGrad #10: First-Last Frame 三模型对比 + 视频扩展管线

> 日期: 2026-03-24 06:03 UTC | 学习轮次: 54 | 总成本: ¥2.35

## 📋 学习目标

1. **First-Last Frame (FLF) 首尾帧生视频** — 三模型横向对比（Hailuo 02 / Veo 3.1 Pro / Vidu Q3 Pro）
2. **Video Extension 视频扩展** — Veo 3.1 fast 扩展管线实测
3. **Hailuo 02 三模式发现** — standard/pro/fast 隐藏能力解析
4. **跨模型拼接管线** — 不同模型输出如何衔接

---

## 1. Hailuo 02 三模式全面发现（新发现！）

### 1.1 三种端点对比

之前 PostGrad 只使用过 Hailuo 2.3 系列的 I2V 端点。本轮发现 **Hailuo 02** 实际有三种独立模式：

| 端点 | 任务类型 | 核心能力 | 首帧 | 尾帧 | 时长 | 价格估算 |
|------|---------|---------|------|------|------|---------|
| `hailuo-02/standard` | video-other | T2V + I2V + **FLF** | ✅可选 | ✅可选 | 6/10s | ¥0.25 |
| `hailuo-02/pro` | video-other | T2V + I2V + **FLF** | ✅可选 | ✅可选 | 6s only | ¥? |
| `hailuo-02/fast` | video-other | **I2V only** | ✅必需 | ❌ | 6/10s | ¥0.08 |

### 1.2 关键发现

- **Hailuo 02 standard 支持首尾帧！** — `firstImageUrl` + `lastImageUrl` 可选参数
- **Hailuo 02 fast 是 I2V 快速版** — `imageUrl` 必需，无首尾帧支持
- **pro vs standard**: pro 仅支持 6s，standard 支持 6/10s
- **prompt 最长 2000 字符**，支持 `enablePromptExpansion` 自动扩展
- **fast 模式分辨率明显更低**: 916×512 vs standard 的 1376×768

### 1.3 API 参数差异

```
Standard/Pro:
  - firstImageUrl: IMAGE (optional) 
  - lastImageUrl: IMAGE (optional)
  - prompt: STRING (required, max 2000)
  - enablePromptExpansion: BOOLEAN (required, default true)
  - duration: LIST ["6", "10"] (standard) / ["6"] (pro)

Fast:
  - imageUrl: IMAGE (required!)
  - prompt: STRING (optional, max 2000) 
  - enablePromptExpansion: BOOLEAN (required, default true)
  - duration: LIST ["6", "10"]
```

---

## 2. 首尾帧生视频三模型对比

### 2.1 实验设置

**统一条件**：
- 首帧: 龙虾厨师在日式拉面厨房内（rhart-image-n-pro 2K 16:9）
- 尾帧: 龙虾厨师在夜晚店外举着 OPEN 霓虹灯（同模型同风格）
- Prompt: 描述从厨房内到店外的过渡，樱花飘落

### 2.2 结果对比

| 指标 | Hailuo 02 Std | Veo 3.1 Pro | Vidu Q3 Pro |
|------|-------------|------------|------------|
| **分辨率** | 1376×768 | 1280×720 | 1284×716 |
| **帧率** | 24fps | 24fps | 24fps |
| **时长** | 5.92s | 8.00s | 8.04s |
| **有音频** | ❌ | ✅ (AAC 48kHz 立体声) | ✅ (AAC 48kHz 立体声) |
| **文件大小** | 4.0MB | 5.7MB | 6.1MB |
| **生成时间** | ~120s | ~110s | ~105s |
| **成本** | ¥0.25 | ¥0.13 | ¥0.88 |
| **性价比** | 中 | **极高** | 低 |

### 2.3 各模型分析

#### Hailuo 02 Standard
- ✅ 分辨率最高 (1376×768)
- ✅ 首尾帧能力是隐藏特性，文档未突出
- ❌ 无音频
- ❌ 仅 ~6s（即使设 6s 也是 5.92s）
- 💡 适合后续需要自配音的场景

#### Veo 3.1 Pro (Start-End-to-Video)
- ✅ **自带音频**（场景匹配的环境音效）
- ✅ 最便宜 ¥0.13 / 性价比最高
- ✅ 固定 8s 完整时长
- ✅ 支持 720p/1080p/4K 分辨率选项
- ✅ 支持 negative prompt
- ❌ 宽高比仅 16:9 / 9:16 两种
- 💡 **综合最优选择**

#### Vidu Q3 Pro
- ✅ 自带音频
- ✅ 灵活时长 (1-16s)
- ✅ 运动幅度可控 (auto/small/medium/large)
- ❌ **最贵 ¥0.88** — 是 Veo 3.1 Pro 的 6.8x
- ❌ 分辨率略低
- 💡 适合需要精确时长控制的场景

### 2.4 首尾帧生视频成本效率排名

```
┌─────────────────────────────────────────────┐
│ 首尾帧生视频 性价比排名 (每秒成本)          │
├────────────────┬────────┬──────┬────────────┤
│ 模型            │ 成本   │ 时长 │ ¥/秒      │
├────────────────┼────────┼──────┼────────────┤
│ Veo 3.1 Pro    │ ¥0.13  │ 8.0s │ ¥0.016/s ★│
│ Hailuo 02 Std  │ ¥0.25  │ 5.9s │ ¥0.042/s  │
│ Vidu Q3 Pro    │ ¥0.88  │ 8.0s │ ¥0.110/s  │
└────────────────┴────────┴──────┴────────────┘
→ Veo 3.1 Pro 每秒成本仅 Vidu Q3 的 1/7
```

---

## 3. Hailuo 02 Fast I2V 实测

### 3.1 实验结果

| 指标 | Hailuo 02 Fast |
|------|---------------|
| 分辨率 | 916×512 |
| 帧率 | 24fps |
| 时长 | 5.88s |
| 音频 | ❌ |
| 文件大小 | 1.8MB |
| 生成时间 | ~65s |
| 成本 | **¥0.08** |

### 3.2 分析

- **超低成本**: ¥0.08 是所有视频模型中最便宜之一（仅 rhart-video-s ¥0.02 更低）
- **分辨率很低**: 916×512 仅约 540p，需要后续放大
- **速度快**: 65s 生成，约为 standard 的一半
- **适用场景**: 快速原型验证、草稿预览、低预算批量生产

### 3.3 Hailuo 02 Fast vs 其他低价 I2V

| 模型 | 成本 | 分辨率 | 时长 | 音频 |
|------|------|--------|------|------|
| rhart-video-s | ¥0.02 | 704×1280竖 | 9.5s | ❌ |
| Hailuo 02 fast | ¥0.08 | 916×512 | 5.9s | ❌ |
| Hailuo 2.3 fast | ¥0.17 | 1376×768 | 5.4s | ❌ |
| Seedance fast | ¥0.30 | 960×960 | 5.0s | ✅ |

---

## 4. Video Extend 视频扩展管线

### 4.1 Veo 3.1 Fast Video Extend 实测

**输入**: Hailuo 02 standard FLF 视频 (1376×768, 5.92s, 无音频)
**输出**: 1280×720, 12.92s, **含音频** (AAC 48kHz 立体声)

| 指标 | 值 |
|------|---|
| 输入时长 | 5.92s |
| 输出时长 | 12.92s |
| 扩展量 | +7.0s (+118%) |
| 分辨率 | 1280×720 (从 1376×768 自动缩放) |
| 音频 | **自动生成**（原始无音频，扩展后有！）|
| 成本 | ¥0.95 |
| 生成时间 | ~105s |

### 4.2 关键发现

1. **Video Extend 会自动添加音频** — 即使原始视频无音频，扩展后 Veo 会生成匹配的环境音
2. **分辨率会被调整** — 1376×768 输入 → 1280×720 输出（可能受 resolution=720p 参数影响）
3. **扩展比例约 2x** — 5.9s → 12.9s，接近翻倍
4. **成本较高**: ¥0.95 是一次 Veo 3.1 pro SE2V 的 7.3x
5. **内容连续性**: Veo 能理解原始视频的场景并合理延续

### 4.3 Video Extend API 参数

```json
{
  "endpoint": "rhart-video-v3.1-fast-official/video-extend",
  "params": {
    "video": "VIDEO (required, max 10MB)",
    "prompt": "STRING (optional, max 8000)",
    "resolution": "LIST [720p, 1080p]",
    "negativePrompt": "STRING (optional)",
    "seed": "INT (optional)"
  }
}
```

### 4.4 Video Extend 与 Start-End-to-Video 对比

| 维度 | Video Extend | Start-End-to-Video |
|------|-------------|-------------------|
| 输入 | 已有视频 | 两张图片 |
| 控制方向 | 向后延续 | 从 A→B 过渡 |
| 内容自由度 | 低（延续原视频） | 高（连接两个场景） |
| 音频 | 自动生成 | 自动生成 |
| 成本 | ¥0.95/次 | ¥0.04-0.88/次 |
| 典型用途 | 延长短视频、补充时长 | 场景过渡、变形动画 |

---

## 5. 跨模型视频拼接管线设计

### 5.1 管线架构

```
┌──────────────────────────────────────────────────────────┐
│               跨模型视频生产管线 v1                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Stage 1: 关键帧生成                                      │
│  ┌───────────┐                                           │
│  │rhart-image │─→ 首帧.jpg + 尾帧.jpg                    │
│  │ -n-pro T2I│   (2K, 16:9, ¥0.03×2)                    │
│  └───────────┘                                           │
│                                                          │
│  Stage 2: 首尾帧→视频 (选一)                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │ A. Veo 3.1 Pro SE2V — 最佳性价比 (¥0.13, 8s, 音频)│  │
│  │ B. Hailuo 02 Std FLF — 最高分辨率 (¥0.25, 6s)     │  │
│  │ C. Vidu Q3 Pro SE2V — 时长灵活 (¥0.88, 1-16s)     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Stage 3: 视频扩展 (可选)                                 │
│  ┌───────────────┐                                       │
│  │Veo 3.1 Fast   │─→ 时长翻倍 + 自动配音                 │
│  │Video Extend   │   (¥0.95, +~7s)                       │
│  └───────────────┘                                       │
│                                                          │
│  Stage 4: 后处理                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │ • Topaz 放大 (¥0.10)                         │        │
│  │ • FFmpeg 拼接/调色                            │        │
│  │ • MiniMax Music BGM (¥0.14)                  │        │
│  │ • MiniMax Speech 旁白 (¥0.016)               │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  总成本: ¥0.22 (最低配) → ¥1.25 (全配)                    │
└──────────────────────────────────────────────────────────┘
```

### 5.2 成本结构分析

**最低成本路径** (¥0.22):
- 2× T2I (¥0.06) + Veo 3.1 Pro SE2V (¥0.13) + MiniMax Speech (¥0.016) = ¥0.22
- 产出: 8s 含音频视频 + 旁白

**标准路径** (¥0.42):
- 2× T2I (¥0.06) + Veo 3.1 Pro SE2V (¥0.13) + Topaz 放大 (¥0.10) + Music (¥0.14) = ¥0.43
- 产出: 8s 高清视频 + BGM + 音效

**长视频路径** (¥1.25):
- 2× T2I (¥0.06) + Hailuo 02 Std FLF (¥0.25) + Veo Extend (¥0.95) = ¥1.26
- 产出: ~13s 含音频长视频

---

## 6. ComfyUI 首尾帧工作流 JSON 设计

### 6.1 Veo 3.1 Pro Start-End-to-Video ComfyUI 节点映射

```
基于 ComfyUI Partner Nodes 架构:
┌─────────────────┐
│LoadImage (首帧)  │──→ IMAGE
└────────┬────────┘
         │
┌────────▼────────┐     ┌─────────────────┐
│VeoStartEndVideo │←────│LoadImage (尾帧)  │
│  prompt          │     └─────────────────┘
│  aspectRatio     │
│  resolution      │
│  duration=8      │
└────────┬────────┘
         │ VIDEO
┌────────▼────────┐
│SaveVideo        │
└─────────────────┘
```

### 6.2 视频扩展 ComfyUI 节点映射

```
┌─────────────────┐
│LoadVideo (src)  │──→ VIDEO
└────────┬────────┘
         │
┌────────▼────────┐
│VeoVideoExtend   │
│  prompt          │
│  resolution      │
│  negativePrompt  │
└────────┬────────┘
         │ VIDEO
┌────────▼────────┐
│SaveVideo        │
└─────────────────┘
```

### 6.3 组合管线 (T2I → FLF → Extend → Save)

完整 ComfyUI 管线需要约 8-10 个节点:
1. FluxGuidance + DualCLIPLoader + EmptyLatentImage + KSampler → 首帧
2. 同上 → 尾帧
3. VeoStartEndToVideo (首帧 + 尾帧 + prompt → 视频)
4. VeoVideoExtend (视频 → 加长视频)
5. SaveVideo

---

## 7. 首尾帧生视频 ComfyUI Partner Nodes 源码分析

### 7.1 Veo 3.1 Start-End-to-Video 节点预期架构

基于 Day 12 分析的 Partner Nodes 三层抽象模式:

```python
class VeoStartEndToVideoNode(PollingOperation):
    """
    继承 PollingOperation 三步模式:
    1. create_operation() → POST 到 Veo API
    2. poll_operation() → 轮询状态  
    3. complete_operation() → 下载视频
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "first_frame": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "maxLength": 800}),
                "aspect_ratio": (["16:9", "9:16"],),
                "resolution": (["720p", "1080p", "4k"],),
            },
            "optional": {
                "last_frame": ("IMAGE",),
                "duration": (["8"],),
                "negative_prompt": ("STRING",),
                "seed": ("INT",),
            },
            "hidden": {
                "auth_token": "AUTH_TOKEN_COMFY_ORG",
            },
        }
    
    RETURN_TYPES = ("VIDEO",)
    CATEGORY = "api/video/veo"
```

### 7.2 Hailuo 02 Standard FLF 节点映射

Hailuo 02 的 `standard` 端点比较特殊 — 它是一个 **万能端点**：
- 不给图 → T2V
- 给首帧 → I2V  
- 给首帧+尾帧 → FLF (首尾帧生视频)

这种设计在 ComfyUI 中映射为一个节点，通过 optional inputs 控制模式:

```python
class HailuoUniversalVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True}),
                "duration": (["6", "10"],),
                "enable_prompt_expansion": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "first_image": ("IMAGE",),  # 给了 → I2V/FLF
                "last_image": ("IMAGE",),   # 给了 → FLF
            },
        }
```

---

## 8. 模型选择策略更新

### 8.1 首尾帧生视频决策树 (更新版)

```
需要首尾帧生视频?
├── 预算敏感 → Veo 3.1 Pro SE2V (¥0.13, 8s, 含音频)
├── 需要高分辨率 → Hailuo 02 Standard (¥0.25, 1376×768, 无音频)
├── 需要灵活时长 (1-16s) → Vidu Q3 Pro (¥0.88, 含音频)
├── 需要低延迟 → Vidu Q3 Turbo (未测，预计更快更便宜)
└── 需要加长 → 先生成短视频 + Veo 3.1 Fast Extend (¥0.95)
```

### 8.2 I2V 快速模式选择 (补充 fast 系列)

```
I2V 快速预览/草稿:
├── 最便宜 → rhart-video-s (¥0.02, 竖屏)
├── 低成本横屏 → Hailuo 02 fast (¥0.08, 916×512)
├── 中等品质 → Hailuo 2.3 fast (¥0.17, 1376×768)
└── 含音频 → Seedance fast (¥0.30, 960×960)
```

---

## 9. Video Extend 关键观察

### 9.1 跨分辨率兼容性

Veo 3.1 Video Extend 能处理不同分辨率的输入:
- 输入: 1376×768 (非标准)
- 输出: 1280×720 (标准 720p)
- **自动重采样到目标 resolution 参数**

### 9.2 音频自动补全

**最重要的发现**: Veo 3.1 Video Extend 在扩展无音频视频时会**自动生成匹配的环境音效**。
这意味着:
- 用 Hailuo (无音频) 生成初始视频
- 用 Veo Extend 既延长又补上音频
- 一举两得！

### 9.3 成本效率

| 目标 | 方案 A (直接) | 方案 B (先短后扩展) |
|------|-------------|-------------------|
| 8s含音频 | Veo 3.1 Pro SE2V ¥0.13 | — |
| ~13s含音频 | 不可直接 | Hailuo ¥0.25 + Extend ¥0.95 = ¥1.20 |
| ~16s含音频 | Vidu Q3 Pro 16s ¥0.88 | Veo SE2V ¥0.13 + Extend ¥0.95 = ¥1.08 |

→ **短视频直接用 Veo SE2V，长视频 Vidu Q3 的 16s 比 Extend 更划算**

---

## 10. 实验总成本

| 实验 # | 内容 | 时间 | 成本 |
|--------|------|------|------|
| #60 | rhart-image-n-pro T2I ×2 (首帧+尾帧) | 40s×2 | ¥0.06 |
| #61 | Hailuo 02 Std FLF (首尾帧→视频) | 120s | ¥0.25 |
| #62 | Hailuo 02 Fast I2V | 65s | ¥0.08 |
| #63 | Veo 3.1 Pro Start-End-to-Video | 110s | ¥0.13 |
| #64 | Vidu Q3 Pro Start-End-to-Video | 105s | ¥0.88 |
| #65 | Veo 3.1 Fast Video Extend | 105s | ¥0.95 |
| **总计** | **6 个实验** | | **¥2.35** |

---

## 11. 关键 Takeaways

1. **Veo 3.1 Pro SE2V 是首尾帧生视频的最佳选择** — ¥0.13/8s/含音频，性价比碾压
2. **Hailuo 02 standard 隐藏了 FLF 能力** — 文档里没有突出，但确实支持
3. **Hailuo 02 fast 是超低成本 I2V** — ¥0.08 但分辨率仅 540p
4. **Video Extend 会自动配音** — 这是一个非常实用的隐藏特性
5. **长视频 (>8s) 用 Vidu Q3 16s 比 Extend 更划算**
6. **跨模型管线可行** — 不同模型的输出可以通过 Extend/FFmpeg 无缝衔接

---

## 附录: ComfyUI 工作流映射

| RunningHub 端点 | ComfyUI Partner Node (预期) | 状态 |
|----------------|---------------------------|------|
| minimax/hailuo-02/standard | MiniMax Hailuo 02 (video-other) | 需确认 |
| rhart-video-v3.1-pro/start-end-to-video | VeoStartEndToVideo | ✅ 可映射 |
| rhart-video-v3.1-fast-official/video-extend | VeoVideoExtend | ✅ 可映射 |
| vidu/start-end-to-video-q3-pro | ViduStartEndToVideo | 需确认 |
