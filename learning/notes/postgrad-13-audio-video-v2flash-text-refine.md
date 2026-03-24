# PostGrad#13: Audio-Enabled Video + V2 Flash + Text Refine Upscale

**日期**: 2026-03-24 12:03 UTC
**轮次**: 57
**主题**: Kling V3.0 Audio I2V/FLF 首测 + rhart-image V2 Flash 对比 + Topaz Text Refine 放大
**总成本**: ¥1.27

---

## 1. rhart-image-n-g31-flash (V2 Flash) — 新 T2I 模型分析

### 模型定位
- **引擎**: Gemini 3.1 Flash（比 Pro 更快更便宜的模型）
- **内部名**: nano-banana2-gemini31flash
- **定价**: ¥0.02/张（比 Pro 的 ¥0.03 便宜 33%）
- **速度**: 25-30s（与 Pro 相近）

### 参数对比（V2 Flash vs Pro）

| 维度 | V2 Flash (g31-flash) | Pro (n-pro) |
|------|---------------------|-------------|
| 引擎 | Gemini 3.1 Flash | Gemini 3 Pro |
| 价格 | ¥0.02 | ¥0.03 |
| 速度 | 25-30s | 20-25s |
| 分辨率 | 1K/2K/4K | 1K/2K/4K |
| 宽高比 | 14种（含1:8/8:1极端比例） | 14种 |
| 图像编辑 | 支持(I2I) | 支持(edit) |
| 文字渲染 | ⚠️ 复杂文字场景偶尔失败 | 更稳定 |

### 实测发现
- **实验 #60**: 简化 prompt 成功，复杂带文字排版的 prompt 失败（1000 Unknown Error）
- 图像质量与 Pro 接近，对于卡通/插画风格没有明显差异
- 适合快速迭代和预览场景，不适合需要精确文字的设计类任务

### ComfyUI 工作流映射
V2 Flash 在 ComfyUI 中的映射方式与 Pro 相同：
- 使用 `RhartImageTextToImageNode` 或类似的 API 代理节点
- 区别仅在模型选择参数
- **最佳实践**: 开发阶段用 Flash 快速迭代，最终输出切换 Pro

---

## 2. Kling V3.0 I2V + Audio — 首次实测 sound 参数

### 关键发现

**这是我们 PG#11 分析了 Kling Partner Nodes 源码后的首次实际验证！**

#### API 参数结构
```json
{
  "firstImageUrl": "IMAGE (required)",
  "lastImageUrl": "IMAGE (optional)",  // ← FLF 支持！
  "prompt": "STRING (max 5000 chars)",
  "negativePrompt": "STRING (optional, max 2500)",
  "duration": "LIST: 3-15s",           // ← 比以前的 5/10s 更灵活！
  "cfgScale": "FLOAT: 0-1 (default 0.8)",
  "sound": "BOOLEAN (default true)"    // ← 音频开关
}
```

#### 音频生成能力分析

**实验 #61**: I2V + Audio（单帧）
- 输入: 960x960 龙虾厨师卡通图
- 输出: 960x960 / 24fps / 5.0s / AAC 44100Hz 立体声
- 音频内容: 根据 prompt 中描述的音效自动生成（厨房环境音）
- 耗时: 170s / ¥0.55

**实验 #63**: FLF + Audio（首尾帧 + 音频）
- 输入: 首帧（烹饪中）+ 尾帧（展示菜品）
- 输出: 960x960 / 24fps / 5.0s / AAC 44100Hz 立体声
- 耗时: 140s / ¥0.55
- **价格发现**: 开启 sound=true 在 V3.0 std 层级下**不额外收费**（仍为 ¥0.55）

### 音频定价分析更新

| Kling 层级 | sound=false | sound=true | 音频额外成本 |
|-----------|------------|-----------|-------------|
| V3.0 std | ¥0.55* | ¥0.55 | **免费** |
| V3.0 pro | ¥0.75* | ？待测 | 待确认 |
| V2.6 pro | ¥0.30* | ？ | PG#11 源码显示翻倍 |
| V2.5 turbo | ¥0.18-0.30 | ？ | 待测 |

*注: V3.0 std 在 PG#8 中无音频测试时也是 ¥0.55，说明 sound 参数可能已默认包含在价格中

### ComfyUI Partner Node 映射

在 PG#11 中我们分析了源码，现在可以验证实际行为：

```
KlingImageToVideoWithAudioNode:
  输入: image, prompt, negative_prompt, duration, cfg_scale, sound=True
  对应 API: kling-v3.0-std/image-to-video + sound=true
  
  源码中的关键实现:
  - sound 参数通过 task.data.sound 传递
  - 音频随视频一起生成（不是后处理配音）
  - 原生同步音频（与视频内容匹配的环境音/音效）
```

### Duration 灵活性发现

V3.0 std 现在支持 **3-15 秒**的连续 duration 选择（以 1 秒为步长）：
- 之前只有 5s/10s 两个选项
- 这大大增加了视频长度灵活性
- 对应 ComfyUI 的 duration 参数: `LIST [3,4,5,6,7,8,9,10,11,12,13,14,15]`

### FLF + Audio 组合工作流

这是一个此前未被记录的能力组合：

```
首帧(烹饪) + 尾帧(展示) + prompt(描述过渡+音效) + sound=true
→ 5s 完整视频，包含：
  - 视觉过渡: 从烹饪动作平滑过渡到展示完成品
  - 同步音频: 与视觉内容匹配的厨房环境音
```

**这在 ComfyUI 中对应**:
- 使用 `KlingStartEndToVideoNode`（如果支持 sound 参数）
- 或使用 `KlingImageToVideoWithAudioNode` + `lastImageUrl` 参数

---

## 3. Topaz Text Refine — 文字专用放大模型

### 模型特性
- **专长**: 优化图像中的文字清晰度和可读性
- **参数**: 
  - scale: 2x / 4x / 6x
  - subjectDetection: All / Foreground / Background
  - faceEnhancement: bool + creativity + strength
- **价格**: ¥0.10（与其他 Topaz 变体相同）

### 实验 #62 结果
- 输入: 896×1200 餐厅海报（大量文字）
- 输出: 1792×2400（精确 2x）
- 速度: 15s
- 效果: 文字边缘锐利保持，无模糊化或伪影放大

### 五种 Topaz 放大模型选择指南（更新版）

| 模型 | 最佳场景 | 特殊能力 |
|------|---------|---------|
| **Standard V2** | 通用照片 | 平衡质量 |
| **High Fidelity V2** | 艺术/插画 | 细节保持最好 |
| **Low Resolution V2** | 极低分辨率源 | 重建能力强 |
| **CGI** | 3D渲染/CG图 | 保持几何锐利 |
| **Text Refine** ⭐新 | 图文设计/海报/截图 | 文字清晰度优化 |

### ComfyUI 工作流中的位置

Text Refine 最适合以下 ComfyUI 管线环节：
1. **Qwen-Image-Edit 输出后放大** — 编辑后的文字图需要高分辨率
2. **宣传物料管线** — T2I → 编辑 → Text Refine 放大 → 输出
3. **截图/文档增强** — 低质量截图放大时保持文字可读
4. **AI 生成海报放大** — 生成的含文字海报需要打印级分辨率

---

## 4. ComfyUI 工作流 JSON — Audio-Enabled Video Pipeline

### 完整管线架构

```
Stage 1: 关键帧生成 (T2I)
├── rhart-image-n-g31-flash/text-to-image (快速预览)
└── rhart-image-n-pro/text-to-image (最终质量)

Stage 2: 音频视频生成 (I2V + Audio)
├── kling-v3.0-std/image-to-video + sound=true (性价比)
├── kling-v3.0-pro/image-to-video + sound=true (最高质量)
└── FLF 模式: 首帧+尾帧 + sound=true (精确过渡控制)

Stage 3: 后处理
├── Topaz Text Refine (文字图放大)
├── Topaz Standard V2 (通用放大)
└── FFmpeg 合成 (多段拼接)
```

### Kling I2V + Audio ComfyUI 节点拓扑

```
[CheckpointLoaderSimple/Flux]
    ├── [CLIPTextEncode] → positive_cond
    ├── [CLIPTextEncode] → negative_cond  
    └── [EmptyLatentImage]
           ↓
[KSampler] → [VAEDecode] → [SaveImage] → first_frame.png
                                              ↓
                            [KlingImageToVideoWithAudioNode]
                                ├── image: first_frame
                                ├── prompt: "动作+音效描述"
                                ├── duration: 5
                                ├── sound: true
                                └── cfg_scale: 0.8
                                              ↓
                            [KlingV2ADownloadNode] → video_with_audio.mp4
```

### Kling FLF + Audio ComfyUI 节点拓扑

```
[T2I Pipeline] → first_frame.png
[T2I Pipeline] → last_frame.png
                     ↓            ↓
              [KlingStartEndToVideoNode]  (如支持 sound 参数)
                  ├── first_image: first_frame
                  ├── last_image: last_frame
                  ├── prompt: "过渡描述 + 音效"
                  ├── duration: 5
                  └── sound: true
                          ↓
              [DownloadNode] → flf_video_with_audio.mp4
```

**注意**: 当前 ComfyUI Partner Nodes 中 `KlingStartEndToVideoNode` 是否支持 `sound` 参数需要验证源码。从 RunningHub API 看，`kling-v3.0-std/image-to-video` 的 `lastImageUrl` 参数表明 FLF 和音频是同一个端点的组合功能。

---

## 5. 实验总结

| # | 实验 | 模型 | 结果 | 耗时 | 成本 |
|---|------|------|------|------|------|
| 60 | V2 Flash T2I | rhart-image-n-g31-flash | 1024×1024 卡通龙虾厨师 ✅ | 25s | ¥0.02 |
| 60' | V2 Flash 复杂文字 | rhart-image-n-g31-flash | ❌ TASK_FAILED | - | ¥0.00 |
| 61 | Kling V3 I2V+Audio | kling-v3.0-std | 960×960/5s/24fps/AAC立体声 ✅ | 170s | ¥0.55 |
| 62a | Text Poster T2I | rhart-image-n-pro | 896×1200 菜单海报 ✅ | 25s | ¥0.03 |
| 62b | Topaz Text Refine | topazlabs/text-refine | 1792×2400 文字清晰放大 ✅ | 15s | ¥0.10 |
| 63a | Last Frame T2I | rhart-image-n-g31-flash | 1024×1024 展示菜品 ✅ | 30s | ¥0.02 |
| 63b | Kling V3 FLF+Audio | kling-v3.0-std | 960×960/5s/AAC/首尾帧过渡 ✅ | 140s | ¥0.55 |

**总成本: ¥1.27** | **总实验: 7 次（5 成功 + 1 失败 + 1 重试成功）**

---

## 6. 关键发现与知识更新

### 🆕 新发现
1. **Kling V3.0 std sound 参数免费** — 开启音频不增加额外费用（¥0.55 含音频）
2. **Kling V3.0 FLF+Audio 组合可用** — 同一端点支持 firstImageUrl + lastImageUrl + sound=true
3. **V3.0 duration 范围扩展到 3-15s** — 比之前的 5/10s 更灵活
4. **V2 Flash 复杂 prompt 稳定性不如 Pro** — 简单 prompt 质量相当，复杂文字场景偶尔失败
5. **Topaz Text Refine** — 文字专用放大，15s 极速，适合图文设计类管线

### 📊 模型选择策略更新

**T2I 快速预览 vs 最终输出**:
- 快速迭代 → V2 Flash (¥0.02, 简单 prompt)
- 最终输出 → Pro (¥0.03, 复杂/文字场景更稳定)
- 文字编辑 → Qwen 2.0 系列 (精确文字控制)

**音频视频一体化**:
- 最佳性价比 → Kling V3.0 std + sound=true (¥0.55/5s 含音频)
- 极致低成本 → Veo 3.1 fast (¥0.04/8s 含音频) [PG#11]
- 首尾帧+音频 → Kling V3.0 std FLF + sound (¥0.55/5s)

**文字图放大**:
- 有大量文字 → Topaz Text Refine (¥0.10/2x)
- 通用图片 → Topaz Standard V2 (¥0.10/2x)
- 3D/CG → Topaz CGI (¥0.10/2x)

### 🔗 与 ComfyUI 的连接

Kling I2V + Audio 在 ComfyUI Partner Nodes 中的实现:
- `KlingImageToVideoWithAudioNode`: sync_op 模式，sound=True 开启原生音频
- `KlingVideoToAudioNode`: 视频到音频（Video-to-Audio, V2A）
- `KlingLipSyncAudioToVideoNode`: 唇同步（Audio + Image → LipSync Video）
- 这些节点都在 `comfy_api_nodes/apis/kling_api.py` 中定义

**重要**: Kling V3.0 的 duration 现在支持 3-15s 连续选择，但 ComfyUI Partner Node 可能还是旧的 `["5", "10"]` 硬编码列表。如果需要用 3-15s 范围，建议通过 API 直接调用或等待 Partner Nodes 更新。
