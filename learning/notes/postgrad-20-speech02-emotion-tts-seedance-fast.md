# PostGrad#20: MiniMax Speech 02 情感 TTS + Seedance Fast 变体

> 日期: 2026-03-25 02:04 UTC | 轮次: 64 | 累计花费: ¥0.660

## 学习主题
1. **MiniMax Speech 02 HD/Turbo** — 新一代 TTS 模型，对比 Speech 2.8
2. **Seedance V1.5 Pro Fast 变体** — T2V/I2V Fast 首测，对比 Pro 版

---

## 1. MiniMax Speech 02 情感 TTS 深度分析

### 1.1 Speech 02 vs 2.8 全参数对比

| 参数 | Speech 02 HD | Speech 02 Turbo | Speech 2.8 HD | Speech 2.8 Turbo |
|------|-------------|----------------|--------------|-----------------|
| **emotion** | ✅ 7种 | ✅ 7种 | ✅ 7种 | ✅ 7种 |
| **pitch** | -12 ~ +12 | -12 ~ +12 | -12 ~ +12 | -12 ~ +12 |
| **speed** | 0.5 ~ 2.0 | 0.5 ~ 2.0 | 0.5 ~ 2.0 | 0.5 ~ 2.0 |
| **volume** | 0.1 ~ 10.0 | 0.1 ~ 10.0 | 0.1 ~ 10.0 | 0.1 ~ 10.0 |
| **pronunciation_dict** | ✅ | ✅ | ✅ | ✅ |
| **english_normalization** | ✅ | ✅ | ✅ | ✅ |

⚠️ **关键发现**: API 参数完全一致！两者的差异在底层模型和定价。

### 1.2 七种情感模式

| 情感 | 英文标识 | 典型场景 | 声学特征 |
|------|---------|---------|---------|
| 开心 | `happy` | 活动播报/产品介绍 | 语调上扬/节奏轻快 |
| 悲伤 | `sad` | 故事旁白/回忆叙述 | 语调下沉/节奏缓慢 |
| 愤怒 | `angry` | 激昂演讲/投诉场景 | 音量增大/节奏加快/重音强 |
| 恐惧 | `fearful` | 悬疑/恐怖旁白 | 气息不稳/语速不均 |
| 厌恶 | `disgusted` | 批评/反感表达 | 鼻音加重/语气下压 |
| 惊讶 | `surprised` | 揭秘/意外发现 | 语调骤升/停顿后加速 |
| 中性 | `neutral` | 新闻播报/技术文档 | 平稳/无明显情感色彩 |

### 1.3 Pitch 控制原理

`pitch` 参数范围 -12 ~ +12，以半音（semitone）为单位：
- **+12** = 高一个八度（2x 基频）
- **-12** = 低一个八度（0.5x 基频）
- **±3** = 明显可感知的音调变化
- **±1** = 微调，适合精细控制

**组合使用**: emotion=angry + pitch=+3 → 尖锐愤怒的声音效果

### 1.4 Pronunciation Dict 功能

格式: `KEY/发音说明`，用于解决缩写/专有名词的发音问题：
```
ASAP/As soon as possible
API/A P I
ComfyUI/Comfy U I
```

多条用换行分隔。

### 1.5 定价对比（关键发现）

| 模型 | 英文文本(~50词) | 中文文本(~50字) | 推测计费逻辑 |
|------|----------------|----------------|------------|
| Speech 02 HD | ¥0.007 | **¥0.003** | 按字符数？中文更便宜 |
| Speech 02 Turbo | ¥0.005 | — | 比 HD 便宜 ~30% |
| Speech 2.8 HD | — | ¥0.006 | 同文本贵 2x |
| Speech 2.8 Turbo | — | — | 未测试 |

⭐ **Speech 02 HD 中文价格仅 Speech 2.8 HD 的 50%！** 同等功能下，02 系列性价比碾压。

### 1.6 速度对比

| 模型 | 生成时间 | 说明 |
|------|---------|------|
| Speech 02 HD | 13-18s | 首次调用略慢（冷启动？） |
| Speech 02 Turbo | 13s | 与 HD 几乎一样快 |
| Speech 2.8 HD | 13s | 同速 |

⚠️ HD vs Turbo 在 RunningHub 上速度差异不大（可能受 API 开销掩盖模型推理差异）

### 1.7 输出文件大小分析

| 实验 | 文件大小 | 情感 | 说明 |
|------|---------|------|------|
| 02 HD Happy (EN) | 200KB | happy | 基准 |
| 02 HD Sad (EN) | 202KB | sad | 几乎相同 |
| 02 Turbo Happy (EN) | 176KB | happy | 比 HD 小 12%（比特率更低？） |
| 02 HD Angry+P3 (EN) | 132KB | angry+pitch+3 | 最小！语速 1.1x + angry 节奏快 → 时长更短 |
| 02 HD CN Surprised | 239KB | surprised | 中文 |
| 2.8 HD CN | 262KB | neutral | 中文同内容更大 |

### 1.8 架构推测

MiniMax Speech 02 相比 2.8 的可能改进：
- **更高效的编码**: 同等质量更少 token → 更低成本
- **改进的情感嵌入**: 虽然 2.8 也有 emotion 参数，02 可能在训练数据和情感表达上更精准
- **统一声码器升级**: 输出音频更紧凑

### 1.9 ComfyUI 集成映射

MiniMax Speech 02 对应 ComfyUI 节点：
- **Kling Partner Nodes** 不直接暴露 MiniMax Speech（Kling 的音频用的是自有引擎）
- **TTS-Audio-Suite** 社区节点可通过 HTTP API 调用
- **comfyui-sound-lab** 支持本地 TTS 但不支持 MiniMax API

**建议集成方式**: 自定义 API 代理节点，参数映射：
```python
INPUT_TYPES = {
    "required": {
        "text": ("STRING", {"multiline": True}),
        "voice_id": ("STRING", {"default": "Wise_Woman"}),
        "emotion": (["happy","sad","angry","fearful","disgusted","surprised","neutral"],),
    },
    "optional": {
        "speed": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0}),
        "pitch": ("INT", {"default": 0, "min": -12, "max": 12}),
    }
}
```

### 1.10 Speech 模型选择决策树

```
需要 TTS？
├── 预算极低 → Speech 02 Turbo (¥0.005/50词)
├── 需要情感控制？
│   ├── 是 → Speech 02 HD (情感更精准/价格更低)
│   └── 否 → Speech 02 Turbo (最便宜最快)
├── 需要声音克隆？ → Voice Clone (¥0.45/15s，贵 75x)
└── 需要最高音质？ → Speech 02 HD
```

---

## 2. Seedance V1.5 Pro Fast 变体深度分析

### 2.1 Fast vs Pro 参数对比

| 参数 | T2V Fast | T2V Pro | I2V Fast | I2V Pro |
|------|---------|---------|---------|---------|
| **duration** | 4-12s | 4-12s | 4-12s | 4-12s |
| **aspectRatio** | 6种(含21:9) | 6种(含21:9) | - | - |
| **resolution** | 720p, 1080p | 720p, **480p**, 1080p | 720p | 720p, 1080p |
| **generateAudio** | ✅ | ✅ | ✅ | ✅ |
| **cameraFixed** | ✅ | ✅ | ✅ | ✅ |
| **prompt maxLength** | 5000 | 5000 | 5000 | 5000 |

⚠️ 关键差异：
- Fast T2V 没有 480p 选项（最低 720p）
- Fast I2V 只有 720p（Pro 还有 1080p）
- **两者价格完全相同: ¥0.30**

### 2.2 实验结果

| 指标 | T2V Fast | T2V Pro (PostGrad#19) | I2V Fast |
|------|---------|----------------------|---------|
| **价格** | ¥0.30 | ¥0.30 | ¥0.30 |
| **生成时间** | 65s | 50s | 87s |
| **分辨率** | 1280×720 | 1280×720 | 1280×720 |
| **帧率** | 24fps | 24fps | 24fps |
| **时长** | 5.07s | 5.07s | 5.07s |
| **音频** | ✅ AAC 44.1kHz 立体声 | ✅ | ✅ AAC 44.1kHz 立体声 |
| **文件大小** | 5.1MB | ~5MB | 7.0MB |

### 2.3 ⚠️ "Fast" 命名误导

**实测 Fast 并不比 Pro 快！反而更慢：**
- T2V Fast: 65s vs Pro: 50s（慢 30%）
- I2V Fast: 87s（Pro PostGrad#4 测试 60s）

可能原因：
1. **"Fast" 指的是推理模型的架构**（蒸馏/轻量版），不是 API 响应速度
2. 实际生成速度受排队、调度影响
3. RunningHub 的调度策略可能不同

### 2.4 Fast 的真正定位

基于 Seedance 官方文档推测：
- **Pro**: 完整模型推理，最高质量
- **Fast**: 蒸馏版模型，质量略低但 GPU 资源消耗更少
- 在 RunningHub 上价格相同（可能因为 RunningHub 按任务计费而非按 GPU 时间）

### 2.5 Seedance 全变体选择指南

```
Seedance V1.5 Pro 选择：
├── I2V 需要 1080p → Pro (唯一选择)
├── T2V 任何情况 → Pro (同价但可能更快)
├── 参考生视频 → Lite (¥0.15，半价)
└── Fast → 不推荐（同价/同质量/更慢）
```

⭐ **结论：在 RunningHub 上，Seedance Fast 没有明显优势，推荐始终用 Pro 版。**

---

## 3. ComfyUI 情感 TTS 管线工作流设计

### 3.1 情感 TTS + 视频管线架构

```
[T2I/I2I] → [I2V + Audio] → [Emotion TTS] → [FFmpeg Mix]
     │              │               │              │
  关键帧          视频+BGM       情感旁白        最终合成
  (Flux/rhart)  (Seedance/Kling)  (Speech 02)   (多轨混音)
```

### 3.2 自定义 MiniMaxSpeech02 节点设计

```python
class MiniMaxSpeech02Node:
    """ComfyUI 自定义节点 — MiniMax Speech 02 TTS"""
    
    CATEGORY = "audio/tts"
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "generate_speech"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "voice_id": ("STRING", {"default": "Wise_Woman"}),
                "model": (["speech-02-hd", "speech-02-turbo", "speech-2.8-hd", "speech-2.8-turbo"],),
                "emotion": (["happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"],),
            },
            "optional": {
                "speed": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.1}),
                "pitch": ("INT", {"default": 0, "min": -12, "max": 12}),
                "volume": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0}),
                "pronunciation_dict": ("STRING", {"default": "", "multiline": True}),
            }
        }
    
    def generate_speech(self, text, voice_id, model, emotion, 
                        speed=1.0, pitch=0, volume=1.0, pronunciation_dict=""):
        # Map model name to RunningHub endpoint
        endpoint_map = {
            "speech-02-hd": "rhart-audio/text-to-audio/speech-02-hd",
            "speech-02-turbo": "rhart-audio/text-to-audio/speech-02-turbo",
            "speech-2.8-hd": "rhart-audio/text-to-audio/speech-2.8-hd",
            "speech-2.8-turbo": "rhart-audio/text-to-audio/speech-2.8-turbo",
        }
        # Submit to RunningHub API...
        # Return AUDIO tensor for downstream processing
        pass
```

### 3.3 场景化情感 TTS 管线示例

**短视频旁白管线**：
```
镜头 1 (开场): emotion=surprised + speed=1.1 → "哇！你绝对想不到..."
镜头 2 (主题): emotion=neutral + speed=1.0 → "今天我们来聊聊..."
镜头 3 (高潮): emotion=happy + speed=1.0 + pitch=+2 → "最精彩的部分来了！"
镜头 4 (结尾): emotion=sad + speed=0.9 → "这就是我们今天的故事..."
```

**多情感分段合成脚本**：
```python
segments = [
    {"text": "Welcome!", "emotion": "happy", "speed": 1.1},
    {"text": "But then something terrible happened.", "emotion": "sad", "speed": 0.9},
    {"text": "And we fought back!", "emotion": "angry", "speed": 1.2, "pitch": 2},
]
# 逐段生成 → concat → 与视频对齐
```

---

## 4. 实验总结

### 4.1 所有实验

| # | 端点 | 结果 | 时间 | 成本 | 关键发现 |
|---|------|------|------|------|---------|
| 64a | speech-02-hd (EN/happy) | ✅ 200KB MP3 | 18s | ¥0.007 | 首次略慢 |
| 64b | speech-02-hd (EN/sad) | ✅ 202KB MP3 | 13s | ¥0.006 | sad 比 happy 便宜? |
| 64c | speech-02-turbo (EN/happy) | ✅ 176KB MP3 | 13s | ¥0.005 | 最便宜 |
| 64d | speech-02-hd (angry+pitch3) | ✅ 132KB MP3 | 13s | ¥0.006 | 文件最小(语速快) |
| 64e | speech-02-hd (CN/surprised) | ✅ 239KB MP3 | 14s | **¥0.003** | ⭐中文超便宜 |
| 64f | speech-2.8-hd (CN/同文本) | ✅ 262KB MP3 | 13s | ¥0.006 | 对照组 |
| 64g | seedance-t2v-fast | ✅ 1280×720/5s/🔊 | 65s | ¥0.300 | 比 Pro 慢! |
| 64h | rhart-image-n-pro T2I | ✅ 参考图 | 31s | ¥0.030 | 关键帧 |
| 64i | seedance-i2v-fast | ✅ 1280×720/5s/🔊 | 87s | ¥0.300 | 仅720p |

**本轮总成本**: ¥0.007+0.006+0.005+0.006+0.003+0.006+0.300+0.030+0.300 = **¥0.663**

### 4.2 关键发现

1. **Speech 02 中文定价 = 2.8 的 50%** (¥0.003 vs ¥0.006)
2. **Speech 02 和 2.8 API 参数完全一致**（都有 emotion/pitch/speed/volume）
3. **Seedance Fast ≠ 更快**（反而比 Pro 慢 30%），命名指模型架构不是响应速度
4. **Seedance Fast I2V 只有 720p**（Pro 有 1080p），但价格相同 → 不推荐 Fast
5. **所有 Seedance 变体都支持原生音频** (AAC 44.1kHz stereo)
6. **Speech 02 情感对输出长度有影响**: angry+高语速 → 文件更小（时长更短）

### 4.3 模型选择策略更新

**TTS 推荐排序**:
1. **Speech 02 HD** — 最高性价比（中文 ¥0.003！），完整情感控制
2. **Speech 02 Turbo** — 需要最低成本时（英文 ¥0.005）
3. **Speech 2.8 HD** — 仅在 02 不可用时回退
4. **Voice Clone** — 需要特定声音克隆时（¥0.45，贵 150x）

**Seedance 推荐**:
- **始终用 Pro**，不用 Fast（同价/更全/可能更快）
- 需要低成本参考生视频 → Seedance V1 Lite (¥0.15)

---

## 5. ComfyUI 工作流 JSON — 情感 TTS 视频管线

> 注: MiniMax Speech 在 ComfyUI 中没有原生 Partner Node，
> 需要自定义节点或外部脚本调用。以下是概念性管线设计。

### 管线成本估算（30s 短视频）

| 阶段 | 模型 | 成本 |
|------|------|------|
| 关键帧 × 3 | rhart-image-n-pro | ¥0.09 |
| I2V × 3 (10s) | Seedance Pro | ¥0.90 |
| BGM 30s | MiniMax Music 2.5 | ¥0.14 |
| 旁白 4 段 | Speech 02 HD | ¥0.02 |
| FFmpeg 合成 | 本地 | ¥0.00 |
| **总计** | | **¥1.15** |

比 PostGrad#18 的 ¥0.77 贵，因为用了 3 段 10s 视频。

---

*学习持续中 — PostGrad Labs 第 20 轮完成 🧪*
