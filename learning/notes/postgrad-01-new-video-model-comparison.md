# Post-Graduation Lab 01: 新视频模型对比测试

> 时间: 2026-03-23 12:03 UTC | 轮次: 45 (Post-Grad #1)

## 1. 实验目标

毕业后首次实操巩固：测试 3 个未实验过/较少使用的视频模型，同图同 prompt 横向对比，评估性价比和适用场景。

## 2. 测试模型

| 模型 | RunningHub 端点 | 说明 |
|------|----------------|------|
| 全能视频S | `rhart-video-s/image-to-video` | RunningHub 自研封装，rank #1 |
| 全能视频V3.1-fast | `rhart-video-v3.1-fast/image-to-video` | V3.1 快速版 |
| Seedance v1.5 Pro | `seedance-v1.5-pro/image-to-video` | 基线对照 |

## 3. 实验设置

### 关键帧
- 端点: `rhart-image-n-pro/text-to-image`
- Prompt: "A majestic red lobster chef standing in a futuristic kitchen, wearing a white chef hat and apron, holding a golden spatula, steam rising from a wok, cyberpunk neon lighting, cinematic composition, ultra detailed, 8k"
- 宽高比: 16:9, 分辨率: 1K
- 耗时: 25s, 成本: ¥0.03

### 视频生成 Prompt
"The lobster chef confidently flips a wok with flames erupting, steam swirling around, neon lights flickering in the background, camera slowly pans right, cinematic smooth motion"

## 4. 实验结果

### 对比总览

```
模型              分辨率      时长    FPS   文件大小  耗时    成本    性价比
─────────────────────────────────────────────────────────────────────────
rhart-video-s     704×1280    9.5s   30    6.8MB    175s   ¥0.02   ★★★★★
rhart-v3.1-fast   1280×720    8.0s   24    5.5MB    105s   ¥0.04   ★★★★☆
Seedance 1.5 Pro  1280×720    5.0s   24    8.6MB    75s    ¥0.30   ★★★☆☆
```

### 关键发现

#### rhart-video-s（全能视频S）
- **分辨率**: 竖屏 704×1280（看起来自动适配了输入图的宽高比方向？或有默认竖屏行为）
- **时长**: 最长 9.5s，30fps（总 286 帧）
- **成本**: 仅 ¥0.02，极其便宜
- **耗时**: 175s 较长
- **⚠️ 注意**: 输出为竖屏格式，虽然输入是 16:9 横屏

#### rhart-video-v3.1-fast
- **分辨率**: 1280×720 标准横屏
- **时长**: 8s，24fps（总 192 帧）
- **成本**: ¥0.04，非常便宜
- **耗时**: 105s 中等
- **平衡**: 分辨率、时长、速度、成本四维平衡最好

#### Seedance v1.5 Pro
- **分辨率**: 1280×720 标准
- **时长**: 仅 5s，24fps（总 121 帧）
- **成本**: ¥0.30，是 rhart-s 的 15 倍
- **耗时**: 75s 最快
- **优势**: 通常运动质量和视觉效果更好（需看实际画面评估）

### 性价比分析

```
每秒视频成本:
  rhart-video-s:     ¥0.002/s  ← 极致性价比
  rhart-v3.1-fast:   ¥0.005/s  ← 高性价比
  Seedance 1.5 Pro:  ¥0.060/s  ← 12-30x 贵
```

## 5. 结论与建议

### 模型选择决策

```
需要最高画质 → Seedance / Kling 3.0 Pro
需要性价比   → rhart-video-v3.1-fast（推荐）
批量生产     → rhart-video-s（极低成本）
横屏内容     → 避免 rhart-video-s（可能竖屏化）
```

### 新发现
1. **rhart 系列极低成本**: ¥0.02-0.04 对比 Seedance ¥0.30 / Kling ¥0.75，适合大批量场景
2. **rhart-video-s 竖屏行为**: 需要进一步测试是否能控制输出方向，可能需要明确设置 aspect ratio
3. **V3.1-fast 最佳平衡**: 速度、成本、分辨率、时长四个维度都不错
4. **rhart 系列生成时间较长**: 175s 和 105s vs Seedance 75s，但成本优势弥补了等待

### 后续测试方向
- [ ] rhart-video-s-pro vs std 画质差异
- [ ] rhart-video-v3.1-pro vs fast 画质差异
- [ ] rhart-video-g (全能视频G) 系列
- [ ] 测试 rhart-video-s 竖屏/横屏控制参数
- [ ] 多场景对比（人物/风景/动物/特效）

## 6. 成本总结

| 实验 | 端点 | 耗时 | 成本 |
|------|------|------|------|
| 关键帧生成 | rhart-image-n-pro T2I | 25s | ¥0.03 |
| 实验 A: 全能视频S | rhart-video-s I2V | 175s | ¥0.02 |
| 实验 B: V3.1-fast | rhart-video-v3.1-fast I2V | 105s | ¥0.04 |
| 实验 C: Seedance 基准 | seedance-v1.5-pro I2V | 75s | ¥0.30 |
| **总计** | | | **¥0.39** |

---

*Post-Graduation Lab #1 完成 — 发现 rhart 系列性价比极高，可作为批量生产首选 🦞*
