# PostGrad#6: Voice Clone + 悠船 MJ 系模型 + 多模态管线

> 日期: 2026-03-23 22:03 UTC | 轮次: 50 | 阶段: Post-Graduation Labs

## 📋 本轮学习目标

1. **悠船 (Youchuan) MJ 系模型首测** — v7/niji7 T2I + I2V
2. **Voice Clone 首测** — MiniMax 声音克隆引擎
3. **多模态合成管线** — 图像→视频→音频→合成

---

## 1. 悠船 (Youchuan) MJ 系模型深度测试

### 1.1 悠船模型家族

悠船是 RunningHub 上提供 Midjourney 风格生成的系列模型：

| 端点 | 说明 | 对标 |
|------|------|------|
| youchuan/text-to-image-v7 | MJ v7 文生图 | Midjourney v7 |
| youchuan/text-to-image-niji7 | MJ niji7 动漫 | Midjourney niji7 |
| youchuan/text-to-image-v6 | MJ v6 文生图 | Midjourney v6 |
| youchuan/text-to-image-v61 | MJ v6.1 文生图 | Midjourney v6.1 |
| youchuan/text-to-image-niji6 | MJ niji6 动漫 | Midjourney niji6 |
| youchuan/image-to-video | MJ 图生视频 | Midjourney I2V |

### 1.2 Prompt 理解差异对比（同一 Prompt）

**Prompt**: "A majestic crimson lobster chef standing in a futuristic kitchen..."

| 模型 | 理解方式 | 风格 | 成本 | 耗时 |
|------|---------|------|------|------|
| youchuan v7 | 写实人类厨师+龙虾食材 | 电影级写实 | ¥0.09 | 35s |
| youchuan niji7 | 拟人龙虾厨师（完美！） | 吉卜力动漫 | ¥0.09 | 70s |
| rhart-image-n-pro | 龙虾本体做厨师 | 3D渲染/概念艺术 | ¥0.03 | 25s |

#### 关键发现

1. **v7 偏写实** — 会把 "lobster chef" 理解为 "拿着龙虾的厨师"，而不是 "龙虾做厨师"。MJ v7 倾向生成照片级写实图像
2. **niji7 擅长拟人化** — 完美理解 "lobster chef" 的拟人概念，生成了极可爱的龙虾厨师角色。动漫模型更擅长将非人类角色拟人化
3. **rhart-image-n-pro 理解最准确** — 生成了龙虾本体穿围裙拿刀的形象，且场景感最强（全息屏幕+未来厨房）
4. **悠船比 rhart 贵 3 倍** — ¥0.09 vs ¥0.03，但各有风格优势
5. **悠船支持 MJ 语法** — `--ar 16:9` 等参数直接可用

### 1.3 悠船 I2V 图生视频测试

用 niji7 龙虾厨师做动画化：

| 维度 | 悠船 I2V | Seedance Fast (对照) |
|------|---------|---------------------|
| 输入图 | niji7 龙虾厨师 | rhart-pro 龙虾厨师 |
| 分辨率 | 1264×704 | 1280×720 |
| 时长 | 5.2s | 5.1s |
| FPS | 24 | 24 |
| 音频 | 无 | 有 |
| 耗时 | 205s | 70s |
| 成本 | ¥0.27 | ¥0.30 |

**分析**:
- 悠船 I2V 耗时是 Seedance 的 3 倍（205s vs 70s）
- 价格接近（¥0.27 vs ¥0.30）
- 悠船无音频，Seedance 自带音频
- 悠船支持首尾帧（lastImageUrl）和 loop 循环模式

**参数特色**:
- `motion`: low/high 运动幅度控制
- `raw`: 原始模式（vs 美化处理）
- `loop`: 循环视频模式
- 支持 720p/480p 分辨率

### 1.4 rhart-video-s realistic 首测

**新发现**: rhart-video-s-official 有 `image-to-video-realistic` 端点，专门支持真人视频生成。

| 维度 | 结果 |
|------|------|
| 分辨率 | 1280×720 |
| 时长 | 4.3s |
| FPS | 30fps（比标准 24fps 高！） |
| 音频 | 有 (AAC) |
| 耗时 | 130s |
| 成本 | ¥0.50 |
| duration 选项 | 4/8/12 秒 |

**关键差异 vs 标准 rhart-video-s**:
- **30fps** 更流畅（标准版通常 24fps）
- **支持真人**内容（标准版有限制）
- 更贵：¥0.50 vs 标准版 ¥0.02-0.04
- 选项简洁：只有 prompt + duration + image

---

## 2. Voice Clone 声音克隆深度解析

### 2.1 MiniMax Voice Clone 引擎

**端点**: `rhart-audio/text-to-audio/voice-clone`

**工作原理**:
1. 上传参考音频（数秒即可）→ 提取声纹特征
2. 输入新文本 → 用克隆的声音合成新语音
3. 支持多种 TTS 后端模型

### 2.2 参数详解

| 参数 | 类型 | 说明 |
|------|------|------|
| audio | AUDIO | 参考音频（≤10MB），几秒就够 |
| custom_voice_id | STRING | 自定义声音 ID（缓存标识） |
| text | STRING | 要合成的文本 |
| accuracy | FLOAT [0-1] | 克隆精度（默认 0.7，越高越像参考） |
| need_noise_reduction | BOOL | 参考音频降噪 |
| need_volume_normalization | BOOL | 音量标准化 |
| model | LIST | 后端模型选择 |
| language_boost | LIST | 语言增强（25 种语言） |

### 2.3 后端模型选项

| 模型 | 特点 |
|------|------|
| speech-02-hd | 高清，最早版本 |
| speech-02-turbo | 快速版 |
| speech-2.5-hd-preview | 2.5 预览 |
| speech-2.5-turbo-preview | 2.5 快速预览 |
| speech-2.6-hd | 最新高清 |
| speech-2.6-turbo | 最新快速 |

### 2.4 实验结果

**参考音频**: MiniMax Speech 2.8 HD 生成的中文（14.1s, 32kHz, 222KB）
**克隆结果**: 14.9s, 32kHz, 176KB

| 维度 | 数值 |
|------|------|
| 耗时 | 15s |
| 成本 | ¥0.45 |
| 参考音频 | 14.1s TTS 生成 |
| 输出音频 | 14.9s |
| 精度设置 | 0.8 |
| 使用模型 | speech-02-hd |

### 2.5 Voice Clone vs 普通 TTS 成本对比

| 方式 | 成本 | 适用场景 |
|------|------|---------|
| Speech 2.8 HD | ¥0.006/条 | 标准旁白 |
| Speech 2.8 Turbo | ~¥0.003/条 | 快速预览 |
| Voice Clone | ¥0.45/条 | 特定声音复刻 |

**Voice Clone 贵 75 倍**！只在需要特定人声时使用。

### 2.6 Voice Clone 在 ComfyUI 工作流中的位置

```
关键帧生成 (Flux/SDXL)
    ↓
视频生成 (Kling/Seedance/Wan)
    ↓
旁白脚本 → Voice Clone → 克隆音频
    ↓
FFmpeg 合成 (视频 + 克隆音频)
    ↓
最终输出 (带特定人声的视频)
```

**典型管线**:
1. 采集目标人物 5-10 秒清晰语音
2. 通过 Voice Clone 生成多段旁白
3. FFmpeg 混合视频轨+旁白轨+BGM轨

---

## 3. 多模态合成管线实操

### 3.1 实验：视频+声音克隆合成

**流程**:
```
rhart-image-n-pro T2I → 龙虾厨师关键帧
                          ↓
               Seedance Fast I2V → 5.1s 动画视频（含自带音频）
                          ↓
Speech 2.8 HD TTS → 参考音频 → Voice Clone → 克隆旁白
                          ↓
               FFmpeg → 替换音轨 → 最终合成视频
```

**FFmpeg 合成命令**:
```bash
ffmpeg -y \
  -i seedance-fast-lobster.mp4 \
  -i voice-clone-result.mp3 \
  -c:v copy -c:a aac -b:a 128k -shortest \
  -map 0:v:0 -map 1:a:0 \
  lobster-chef-with-voiceclone.mp4
```

**结果**: 8.6MB, 5.12s, 视频不变+音频替换为克隆旁白

### 3.2 合成管线成本分析

| 步骤 | 工具 | 成本 |
|------|------|------|
| 关键帧 T2I | rhart-image-n-pro | ¥0.03 |
| I2V 动画 | Seedance Fast | ¥0.30 |
| 参考音频 | Speech 2.8 HD | ¥0.006 |
| 声音克隆 | Voice Clone | ¥0.45 |
| 合成 | FFmpeg (本地) | ¥0 |
| **总计** | | **¥0.786** |

**如果不用 Voice Clone**（普通 TTS）: ¥0.336
**Voice Clone 占成本**: 57%！

### 3.3 ComfyUI 工作流映射

在 ComfyUI 中构建等效管线：

```
[CheckpointLoader] → [CLIPTextEncode] → [KSampler] → [VAEDecode]
                                                          ↓
                                              [KlingI2VNode / SeedanceI2V]
                                                          ↓
                                              [SaveVideo / CreateVideo]
                                                          ↓
                                              外部: Voice Clone API → FFmpeg 合成
```

**注意**: ComfyUI 目前没有原生 Voice Clone 节点，需要：
- 自定义 API 代理节点（调用 MiniMax Voice Clone API）
- 或 ComfyUI comfyui-sound-lab 等音频节点 + 外部 API

---

## 4. 模型选择策略更新

### 4.1 T2I 模型选择（含悠船系列）

| 场景 | 推荐模型 | 成本 | 理由 |
|------|---------|------|------|
| 通用创意 | rhart-image-n-pro | ¥0.03 | 最佳性价比 |
| 电影写实 | youchuan v7 | ¥0.09 | MJ v7 写实质感 |
| 动漫角色 | youchuan niji7 | ¥0.09 | 拟人化能力最强 |
| 高端写实 | rhart-image-g-4 | ¥1.00 | 电影级真实感 |
| 精确编辑 | qwen-image-2.0-pro | ¥0.05 | 文字编辑 SOTA |
| 风格迁移 | seedream-v5-lite | ¥0.04 | I2I 变换 |

### 4.2 I2V 模型选择（含悠船）

| 模型 | 成本 | 耗时 | 分辨率 | 音频 | 适用 |
|------|------|------|--------|------|------|
| Seedance Fast | ¥0.30 | 70s | 1280×720 | ✅ | 通用动画 |
| 悠船 I2V | ¥0.27 | 205s | 1264×704 | ❌ | MJ 风格动画 |
| rhart-s realistic | ¥0.50 | 130s | 1280×720 | ✅ | 真人视频 |
| Hailuo 02 | ¥0.25 | ~60s | 1376×768 | ❌ | 快速预览 |

### 4.3 音频管线选择

| 需求 | 推荐 | 成本 |
|------|------|------|
| 标准旁白 | Speech 2.8 HD | ¥0.006 |
| 快速预览 | Speech 2.8 Turbo | ~¥0.003 |
| 特定人声 | Voice Clone | ¥0.45 |
| 背景音乐 | Music 2.5 | ¥0.14/min |

---

## 5. 实验记录汇总

### 实验 #60: 悠船 v7 T2I — 写实龙虾厨师
- **端点**: youchuan/text-to-image-v7
- **输出**: 写实人类厨师+龙虾食材
- **耗时**: 35s | **成本**: ¥0.09
- **发现**: v7 偏写实，非拟人化理解

### 实验 #61: 悠船 niji7 T2I — 动漫龙虾厨师
- **端点**: youchuan/text-to-image-niji7
- **输出**: 可爱拟人龙虾厨师（吉卜力风）
- **耗时**: 70s | **成本**: ¥0.09
- **发现**: niji7 拟人化能力极强，动漫风格完美

### 实验 #62: rhart-image-n-pro T2I — 对照组
- **端点**: rhart-image-n-pro/text-to-image
- **输出**: 3D 渲染龙虾厨师+未来厨房
- **耗时**: 25s | **成本**: ¥0.03
- **发现**: 最佳性价比，理解准确，场景最丰富

### 实验 #63: 悠船 I2V — 龙虾厨师动画
- **端点**: youchuan/image-to-video
- **输入**: niji7 龙虾厨师
- **输出**: 1264×704, 5.2s, 24fps, 无音频
- **耗时**: 205s | **成本**: ¥0.27
- **发现**: 慢但支持首尾帧和循环模式

### 实验 #64: Seedance Fast I2V — 对照组
- **端点**: seedance-v1.5-pro/image-to-video-fast
- **输入**: rhart-pro 龙虾厨师
- **输出**: 1280×720, 5.1s, 24fps, 有音频
- **耗时**: 70s | **成本**: ¥0.30
- **发现**: 3x 更快，自带音频

### 实验 #65: Speech 2.8 HD 参考音频
- **端点**: rhart-audio/text-to-audio/speech-2.8-hd
- **输出**: 14.1s 中文旁白, 32kHz
- **耗时**: 10s | **成本**: ¥0.006
- **发现**: 超便宜标准 TTS

### 实验 #66: Voice Clone 声音克隆
- **端点**: rhart-audio/text-to-audio/voice-clone
- **输入**: 实验 #65 的参考音频
- **输出**: 14.9s 克隆语音, 32kHz
- **耗时**: 15s | **成本**: ¥0.45
- **参数**: accuracy=0.8, model=speech-02-hd
- **发现**: 贵但能复刻特定声音

### 实验 #67: rhart-video-s realistic I2V — 真人支持
- **端点**: rhart-video-s-official/image-to-video-realistic
- **输入**: v7 写实厨师图
- **输出**: 1280×720, 4.3s, 30fps, 有音频
- **耗时**: 130s | **成本**: ¥0.50
- **发现**: 30fps 更流畅，支持真人，但较贵

### 实验 #68: FFmpeg 多模态合成
- **流程**: Seedance 视频 + Voice Clone 音频 → FFmpeg 合成
- **输出**: 8.6MB, 5.12s
- **成本**: ¥0 (本地处理)
- **发现**: 简单有效的音视频合成方式

---

## 6. 关键收获与 ComfyUI 工作流启示

### 6.1 悠船模型在 ComfyUI 中的定位

悠船模型目前只通过 RunningHub API 可用，在 ComfyUI 中的集成方式：

1. **ComfyUI API 代理节点** — 类似 Partner Nodes 的 PollingOperation 模式
2. **RunningHub WebApp** — 直接在工作台使用
3. **自定义封装** — Python 脚本 + ComfyUI HTTP API

### 6.2 Voice Clone 工作流集成思路

ComfyUI 当前音频节点生态中缺少原生 Voice Clone 支持。集成路径：

```python
# 自定义节点模板
class VoiceCloneNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "reference_audio": ("AUDIO",),
                "text": ("STRING", {"multiline": True}),
                "voice_id": ("STRING", {"default": "custom_voice"}),
                "accuracy": ("FLOAT", {"default": 0.7, "min": 0, "max": 1}),
            }
        }
    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "clone_voice"
    CATEGORY = "audio/tts"
    
    def clone_voice(self, reference_audio, text, voice_id, accuracy):
        # 调用 MiniMax Voice Clone API
        # 上传参考音频 → 获取克隆结果
        pass
```

### 6.3 完整多模态 ComfyUI 管线设计

```
[Text2Img: Flux/SDXL] ──────────────────────┐
                                              ↓
[Image2Video: Kling/Seedance Partner Node] ──┤
                                              ↓
[TTS: comfyui-sound-lab] ──→ [Voice Clone API] ──→ [Narration Audio]
                                              ↓
[Music: MiniMax Music 2.5] ──→ [BGM Audio]
                                              ↓
[FFmpeg/CreateVideo] ──→ Mix All Tracks ──→ [Final Video with VO + BGM]
```

---

## 7. 本轮成本总结

| 实验 | 成本 |
|------|------|
| 悠船 v7 T2I | ¥0.09 |
| 悠船 niji7 T2I | ¥0.09 |
| rhart-pro T2I | ¥0.03 |
| 悠船 I2V | ¥0.27 |
| Seedance Fast I2V | ¥0.30 |
| Speech 2.8 HD TTS | ¥0.006 |
| Voice Clone | ¥0.45 |
| rhart-s realistic I2V | ¥0.50 |
| **总计** | **¥1.736** |

---

*PostGrad#6 完成 — 2026-03-23 22:40 UTC*
