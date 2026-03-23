# PostGrad Lab #3: 音视频多模态全链路管线实操

> **日期**: 2026-03-23 16:03 UTC | **轮次**: 47 | **耗时**: ~25min | **总成本**: ¥1.907

## 🎯 学习目标

1. **端到端多模态管线实操** — 图像→视频→音乐→语音→合成
2. **新模型对比** — Hailuo 2.3 fast-pro / Vidu Q3 Pro
3. **首尾帧生视频实战** — Vidu Q3 双关键帧过渡
4. **FFmpeg 多镜头后期** — xfade 交叉淡化 + 多轨音频混合

## 📊 实验结果汇总

### 实验 #60: 角色关键帧生成
- **端点**: `rhart-image-n-pro/text-to-image`
- **用时**: 25s | **成本**: ¥0.03
- **结果**: 16:9 龙虾厨师在赛博朋克厨房，全息菜单 "Galactic Crustacean Specials"
- **评价**: 场景细节丰富，全息 UI 元素惊艳

### 实验 #61: Hailuo 2.3 fast-pro I2V 🆕
- **端点**: `minimax/hailuo-2.3-fast-pro/image-to-video`
- **用时**: 115s | **成本**: ¥0.29
- **规格**: 1934×1080 / 24fps / 5.875s / H.264
- **发现**:
  - 分辨率超预期 — 1934×1080 接近 2K（非标准 1920）
  - Hailuo 2.3 生成宽度可能基于图像原始比例自适应
  - fast-pro 模式在 ~2min 完成，速度合理
  - 画面稳定，运动幅度适中

### 实验 #62: Seedance 1.5 Pro Fast I2V（基线）
- **端点**: `seedance-v1.5-pro/image-to-video-fast`
- **用时**: 55s | **成本**: ¥0.30
- **规格**: 1280×720 / 24fps / 5.074s / H.264
- **对比**: Seedance 速度快 2x，但分辨率低

### 实验 #63: MiniMax Music 2.5 背景音乐
- **端点**: `rhart-audio/text-to-audio/music-2.5`
- **用时**: 135s | **成本**: ¥0.14
- **规格**: 36.18s / 256kbps / 1.2MB MP3
- **Prompt**: "Upbeat electronic jazz fusion with cyberpunk vibes, funky bass line..."
- **发现**: 生成时长远超视频需要（36s vs 5-10s），可裁剪使用

### 实验 #64: MiniMax Speech 2.8 HD 旁白
- **端点**: `rhart-audio/text-to-audio/speech-2.8-hd`
- **用时**: 10s | **成本**: ¥0.017
- **规格**: 10.76s / 128kbps / 171KB MP3
- **内容**: "Welcome to the Galactic Crustacean Kitchen!..."
- **发现**: 极快生成速度，HD 音质清晰

### 实验 #65: FFmpeg 多模态合成 v1
- **管线**: Hailuo 视频 + BGM (vol=0.15) + 旁白 (delay 300ms, vol=0.9)
- **FFmpeg filter**: `atrim` + `adelay` + `amix`
- **结果**: 3.9MB / 5.89s / 1934×1080 / AAC 192kbps
- **评价**: 首次成功的端到端 AI 多模态合成！

### 实验 #66: Vidu Q3 Pro I2V 🆕
- **端点**: `vidu/image-to-video-q3-pro`
- **用时**: 100s | **成本**: ¥0.55
- **规格**: 1284×716 / 24fps / 5.042s / H.264
- **评价**: 价格最高但分辨率反而最低，性价比不佳
- **vs Hailuo 2.3**: Hailuo 以近一半价格给出更高分辨率

### 实验 #67: rhart-video-g I2V ❌
- **端点**: `rhart-video-g/image-to-video`
- **状态**: FAILED — 参数校验失败
- **错误**: resolution 需小写 `720p`（不是 `720P`），duration 需要纯数字（不是 `6s`）
- **教训**: 
  - rhart-video-g 参数格式与其他 rhart 系列不一致
  - 修正参数后仍失败，可能有其他未知必需参数
  - **需要进一步研究 G 系列的完整参数规格**

### 实验 #68: Vidu Q3 首尾帧生视频
- **端点**: `vidu/start-end-to-video-q3-pro`
- **双图上传**: 使用 `--image img1 --image img2` 传递首尾帧
- **用时**: ~60s | **成本**: ¥0.55
- **规格**: 1284×716 / 24fps / 5.042s / H.264 + AAC 48kHz 2ch
- **重要发现**:
  - Vidu Q3 首尾帧视频**自带音频轨**（自动生成环境音）
  - 过渡效果自然，从烹饪到出菜的变形连贯
  - 支持 audio=true 参数控制

### 实验 #69: 多镜头拼接 + 最终合成
- **处理流程**:
  1. FFmpeg 分辨率归一化 (scale=1280:720, pad)
  2. xfade 交叉淡化过渡 (fade, 0.5s)
  3. BGM + 旁白多轨混音
- **最终产品**: 4.7MB / 7.38s / 1280×720 / 24fps
- **FFmpeg 命令链**: normalize → xfade → amix

## 🔍 关键发现与分析

### 1. I2V 模型性价比排名（同图对比）

```
模型                    分辨率      时长    成本    用时     性价比
──────────────────────────────────────────────────────────────────
Hailuo 2.3 fast-pro    1934×1080   5.9s   ¥0.29   115s   ⭐⭐⭐⭐⭐
Seedance 1.5 fast      1280×720    5.1s   ¥0.30    55s   ⭐⭐⭐⭐
Vidu Q3 Pro            1284×716    5.0s   ¥0.55   100s   ⭐⭐⭐
```

**结论**: Hailuo 2.3 fast-pro 是新的性价比冠军 — 接近半价提供 2K 级分辨率！

### 2. 多模态管线成本结构

```
环节              成本      占比     备注
─────────────────────────────────────────
关键帧生成 ×2     ¥0.06     5.7%    最便宜
视频生成 ×2       ¥0.84    79.8%    主要成本
背景音乐          ¥0.14    13.3%    可复用
旁白              ¥0.02     1.9%    极便宜
本地后处理        ¥0.00     0.0%    FFmpeg 免费
─────────────────────────────────────────
多镜头短视频合计  ¥1.05    100%
```

**关键洞察**: 
- 视频生成占 80% 成本，是优化重点
- 音频几乎免费（旁白 ¥0.02 / 10s）
- 本地 FFmpeg 后处理零成本，大幅增值

### 3. FFmpeg 多模态管线技术要点

```bash
# 核心命令模式
ffmpeg -i video.mp4 -i bgm.mp3 -i narration.mp3 \
  -filter_complex "
    [1:a]atrim=0:DUR,volume=VOL_BGM[bgm];
    [2:a]adelay=DELAY,volume=VOL_NARR[narr];
    [bgm][narr]amix=inputs=2:duration=longest[aout]
  " \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -shortest output.mp4

# 多镜头交叉淡化
ffmpeg -i shot1.mp4 -i shot2.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=SHOT1_DUR-0.5" \
  -c:v libx264 output.mp4
```

### 4. runninghub.py 首尾帧双图上传

脚本支持 `--image img1 --image img2` 自动映射到 `firstImageUrl` / `lastImageUrl`：
- 代码逻辑：当 IMAGE 类型参数 >1 且 --image 数量匹配时，按序映射
- 但大文件会 base64 内联，可能导致请求过大

### 5. rhart-video-g 系列参数差异

与 rhart-video-s / V3.1 系列不同：
- `resolution` 必须小写 (`720p` not `720P`)
- `duration` 必须纯数字 (`6` not `6s`)
- 可能还有其他未知必需参数，需进一步调试

## 🏗️ 完整生产管线架构

```
[Story Script]
    ↓
[关键帧生成] rhart-image-n-pro T2I (¥0.03 each)
    ↓ (首帧 + 尾帧)
[视频生成] 选择:
    ├─ Hailuo 2.3 fast-pro (最佳性价比)
    ├─ Seedance 1.5 fast (最快)
    ├─ Vidu Q3 首尾帧 (带过渡 + 自带音频)
    └─ Kling V3/O3 (最高质量)
    ↓
[音频生成] 并行:
    ├─ MiniMax Music 2.5 BGM (¥0.14)
    └─ MiniMax Speech 2.8 HD 旁白 (¥0.02)
    ↓
[后期处理] FFmpeg (免费):
    ├─ 分辨率归一化
    ├─ xfade 多镜头拼接
    ├─ 多轨音频混合 (BGM + 旁白)
    └─ 最终编码输出
    ↓
[最终产品] 多镜头短视频 (7-30s)
```

### 预估成本：
- **5s 单镜头 + 音频**: ¥0.32-0.60
- **10s 双镜头 + 音频**: ¥0.90-1.50
- **30s 六镜头 + 音频**: ¥2.50-4.50

## 📝 下一步计划

1. **Motion Control 实操** — Kling V3.0 动作迁移（需准备参考视频）
2. **rhart-video-g 参数调试** — 深入研究 G 系列完整参数规格
3. **Voice Clone 实验** — MiniMax voice-clone 端点测试
4. **ComfyUI 工作流编排** — 将管线转化为 ComfyUI JSON 工作流
5. **Vidu Q3 vs Q2 质量对比** — 测试新老版本差异
