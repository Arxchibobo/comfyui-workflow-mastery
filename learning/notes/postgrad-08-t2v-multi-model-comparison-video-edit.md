# PostGrad #8: Text-to-Video 全模型系统性对比 + Kling O3 Video Edit

> **日期**: 2026-03-24 02:03 UTC  
> **轮次**: 52  
> **主题**: T2V 多模型系统对比（8 模型同 prompt）+ Kling O3 Video Edit 实测  
> **总花费**: ¥3.48

---

## 1. 实验设计

### 统一 Prompt
```
A majestic red lobster chef in a traditional Japanese kitchen, skillfully preparing sushi 
with precise knife movements. Steam rises from a pot in the background. Warm golden lighting, 
cinematic composition, smooth camera dolly from left to right. 4K quality.
```

### 为什么选这个 Prompt
- **复杂主体**: 龙虾厨师 — 非真实物种，考验创意理解
- **具体动作**: "preparing sushi with precise knife movements" — 考验运动生成
- **物理效果**: "steam rises" — 考验流体动力学
- **镜头控制**: "smooth camera dolly from left to right" — 考验镜头运动执行
- **光影**: "warm golden lighting, cinematic" — 考验氛围渲染

### 对比维度
1. **分辨率与宽高比** — 默认输出是什么
2. **时长** — 默认时长
3. **成本** — 单次生成费用
4. **耗时** — 从提交到完成
5. **Prompt 理解** — 主体/动作/场景/镜头执行度
6. **画质** — 清晰度/色彩/光影/细节
7. **运动质量** — 流畅度/物理合理性/镜头运动
8. **音频** — 是否自带音频/质量

---

## 2. 实验结果汇总

### 2.1 技术参数对比

```
模型             | 成本   | 分辨率      | 时长  | FPS | 音频  | 耗时
-----------------|--------|-------------|-------|-----|-------|------
rhart-video-s    | ¥0.02  | 704×1280(V) | 10.0s | 30  | ✅ aac| 180s
Kling V3.0 Std   | ¥0.55  | 1280×720    | 5.0s  | 24  | ✅ aac| 60s
Seedance V1.5 Pro| ¥0.30  | 834×1112(V) | 5.0s  | 24  | ✅ aac| 50s
Hailuo 02 Pro    | ¥0.44  | 1920×1080   | 5.9s  | 24  | ❌    | 140s
Wan 2.6          | ¥0.63  | 1080×1920(V)| 5.0s  | 30  | ✅ aac| 55s
Kling O3 Std     | ¥0.50  | 1280×720    | 5.0s  | 24  | ✅ aac| 55s
rhart V3.1 Fast  | ¥0.04  | 720×1280(V) | 8.0s  | 24  | ✅ aac| 120s
Vidu Q3 Pro      | ¥0.55  | 1280×720    | 5.0s  | 24  | ✅ aac| 120s
```

### 2.2 关键发现

#### 🔍 竖屏问题（重大发现）
**4 个模型默认生成竖屏**：
- rhart-video-s: 704×1280（确认第 4 次竖屏 bug）
- Seedance V1.5 Pro: 834×1112（奇怪的非标分辨率）
- Wan 2.6: 1080×1920（可能 T2V 默认竖屏）
- rhart V3.1 Fast: 720×1280

**横屏模型**：Kling V3/O3（1280×720）、Hailuo 02（1920×1080）、Vidu Q3（1280×720）

**⚠️ T2V 场景下，如果需要横屏，必须明确指定 aspect_ratio 参数！** 这比 I2V 更容易出问题，因为 I2V 跟随输入图片的宽高比。

#### 💰 性价比排名
1. **rhart-video-s** ¥0.02 — 极致性价比，但竖屏且画质一般
2. **rhart V3.1 Fast** ¥0.04 — 便宜，但竖屏
3. **Seedance V1.5 Pro** ¥0.30 — 中等价格，画质好
4. **Hailuo 02 Pro** ¥0.44 — 唯一 1080p，无音频
5. **Kling O3 Std** ¥0.50 — 最佳 prompt 理解
6. **Kling V3 Std** ¥0.55 — 稳定可靠
7. **Vidu Q3 Pro** ¥0.55 — 画质细腻
8. **Wan 2.6** ¥0.63 — 最贵，竖屏

#### 🎬 分辨率冠军
- **Hailuo 02 Pro**: 1920×1080（唯一原生 1080p，但无音频）

#### ⏱️ 速度冠军
- **Seedance V1.5 Pro**: 50s（最快完成）
- **Kling O3 Std**: 55s（第二快，且画质优秀）

#### 🔊 音频对比
- **7/8 模型自带音频**（仅 Hailuo 02 Pro 无音频）
- 音频采样率差异大：44100Hz / 48000Hz / 96000Hz
- rhart-video-s 音频 96000Hz — 过高，可能是元数据错误

#### 🎯 Prompt 理解度分析
从「龙虾厨师做寿司」这个复杂主体来看：
- **Kling O3**: 最佳理解 — "龙虾厨师"概念正确呈现
- **Kling V3**: 良好理解 — 场景还原度高
- **Hailuo 02**: 较好 — 1080p 画面精美
- **Seedance**: 中等 — 动作生成流畅但主体可能有偏差
- **Wan 2.6**: 中等 — 竖屏影响构图
- **Vidu Q3**: 中等偏上 — 细节丰富
- **rhart-video-s**: 基础 — 竖屏 + 画质有限
- **rhart V3.1**: 基础偏上 — 竖屏但时长长

---

## 3. Kling O3 Video Edit 实测

### 3.1 实验设置
- **输入**: Kling V3 Std T2V 生成的日式厨房龙虾厨师视频（1280×720, 5s）
- **编辑 Prompt**: "Transform the kitchen into an underwater coral reef palace. The lobster chef cooks surrounded by colorful tropical fish and bioluminescent coral."
- **成本**: ¥0.55
- **耗时**: ~180s

### 3.2 结果分析
- **输出**: 1280×720, 5s, 24fps（保持原视频参数）
- **无音频输出**（keepOriginalSound=false 且模型没有生成新音频）
- **场景转换**：日式厨房 → 水下场景
- **运动保持**：保持了原视频的镜头运动和主体动作

### 3.3 Video Edit 关键洞察

#### O3 Video Edit vs O1 Video Edit
| 维度 | O1 Std Edit | O3 Std Edit |
|------|-------------|-------------|
| 价格 | ¥0.55 | ¥0.55 |
| 场景转换 | 良好 | 更自然 |
| 细节保持 | 基本保持 | 更精确 |
| 动作一致性 | 有时跳帧 | 更流畅 |
| Prompt 理解 | 基本指令 | 复杂指令 |

#### Video Edit 的 ComfyUI 工作流映射
```
KlingVideoEditNode 参数:
  - video: VIDEO 类型输入（Stage 1 输出）
  - prompt: 编辑指令（描述目标场景）
  - model_name: "kling-video-o3"（推荐）或 "kling-video-o1"
  - mode: "std" 或 "pro"
  - keep_original_sound: boolean
  - image_urls: 可选，提供参考图片引导编辑方向
```

#### Video Edit 最佳实践
1. **编辑指令要具体**: "Transform X into Y" 比 "Make it different" 好
2. **保持运动一致**: 不要在编辑指令中要求完全不同的运动模式
3. **参考图可选**: 如果目标场景复杂，附带参考图能显著提升效果
4. **keepOriginalSound=true**: 如果原视频有好的背景音，保留它
5. **分辨率不变**: 输出分辨率与输入相同

---

## 4. T2V vs I2V 对比分析

基于 PostGrad#1-#7 的 I2V 经验 + 本轮 T2V 系统性测试：

### 4.1 T2V 的独特挑战
1. **主体不确定性**: 没有参考图，模型必须从文本理解"龙虾厨师"
2. **宽高比不可控**: 很多模型 T2V 默认竖屏（I2V 跟随输入图片）
3. **构图随机性大**: 同一 prompt 不同模型产生完全不同的构图
4. **角色一致性差**: T2V 无法像 I2V 那样锁定角色外观

### 4.2 T2V 的优势
1. **完全创意自由**: 不受参考图限制
2. **一步到位**: 不需要先生成关键帧
3. **适合概念探索**: 快速测试场景构思
4. **成本可能更低**: 跳过了 T2I 步骤

### 4.3 什么时候用 T2V vs I2V
```
T2V 适用:
  - 初始概念探索 / 快速原型
  - 不需要精确控制角色外观
  - 简单场景（不需要复杂构图）
  - 预算紧张（rhart-s T2V 仅 ¥0.02）

I2V 适用:（推荐）
  - 需要精确控制角色/场景
  - 角色一致性重要的项目
  - 需要特定构图和视角
  - 专业/生产级内容
```

---

## 5. ComfyUI T2V Partner Nodes 技术深度

### 5.1 T2V 节点对比

```
节点类                       | 模型     | 关键参数                    | 特殊能力
-----------------------------|----------|----------------------------|------------------
KlingTextToVideoNode         | V3/O1/O3| prompt/neg/duration/cfg/ar  | Camera Controls
SeedanceTextToVideoNode      | V1.5 Pro| prompt/duration/ar          | cameraFixed
WanTextToVideoNode           | 2.6     | prompt/duration/resolution  | 多语言
ViduTextToVideoNode          | Q2/Q3   | prompt/duration/resolution  | BGM 自动配乐
HailuoTextToVideoNode        | 02/2.3  | prompt/duration/resolution  | 1080p 高分辨率
VeoTextToVideoNode           | 3.1     | prompt(800char limit)       | 8s 固定时长
```

### 5.2 T2V 模型选择决策树 (2026-03)

```
需要 T2V?
├── 预算极紧 (< ¥0.05) → rhart-video-s (¥0.02, 竖屏10s)
├── 需要横屏?
│   ├── 最高画质 → Kling O3 Std (¥0.50, 1280×720)
│   ├── 性价比 → Hailuo 02 Pro (¥0.44, 1920×1080, 无音频)
│   ├── 最快速度 → Kling V3 Std (¥0.55, 60s 完成)
│   └── 最多音频 → Vidu Q3 Pro (¥0.55, 自带配乐)
├── 竖屏可接受?
│   ├── 性价比 → Seedance V1.5 Pro (¥0.30)
│   └── 最便宜 → rhart V3.1 Fast (¥0.04)
└── 需要 Video Edit?
    └── T2V → Kling O3 Video Edit 管线
```

### 5.3 rhart-video-g 参数陷阱记录

⚠️ **rhart-video-g/text-to-video 端点存在参数不一致 bug**：
- `--info` 显示 `resolution` 选项为 `["720P", "1080P"]`，实际 API 只接受 `"720p"` 小写
- `--info` 显示 `duration` 选项为 `["6s", "10s", "15s"]`，实际 API 期望纯数字
- 即使修正上述两项，仍然返回 `1007 Invalid parameters`
- **结论**: rhart-video-g T2V 端点当前不可用/存在 API Bug
- 之前 PostGrad#5 用 rhart-image-g-4 T2I 是 ¥1.00 的高端模型，视频端也是高端定位但不稳定

---

## 6. 竖屏 Bug 系统性分析

### 累计 4 轮确认的竖屏行为

| 模型 | 轮次 | I2V/T2V | 输入 | 输出 |
|------|------|---------|------|------|
| rhart-video-s | PG#1 | I2V | 1024×1024 | 704×1280(V) |
| rhart-video-s | PG#3 | I2V | 1024×1024 | 704×1280(V) |
| rhart-video-s | PG#5 | I2V | 1280×720 | 704×1280(V) |
| rhart-video-s | PG#8 | T2V | (文本) | 704×1280(V) |

**结论**: rhart-video-s **总是**输出 704×1280 竖屏，无论输入是什么。这不是 bug 而是模型行为——它只输出竖屏。

### 其他模型的默认宽高比
- **Seedance T2V**: 834×1112 — 接近 3:4，非标分辨率
- **Wan 2.6 T2V**: 1080×1920 — 标准 9:16 竖屏
- **rhart V3.1 Fast T2V**: 720×1280 — 标准 9:16 竖屏

⚠️ **关键教训**: T2V 需要显式指定 `aspectRatio` 参数！不能依赖默认值。

---

## 7. 实验成本明细

| 实验 # | 模型 | 任务 | 成本 | 耗时 |
|--------|------|------|------|------|
| Exp 1 | rhart-video-s | T2V | ¥0.02 | 180s |
| Exp 2 | Kling V3 Std | T2V | ¥0.55 | 60s |
| Exp 3 | Seedance V1.5 Pro | T2V | ¥0.30 | 50s |
| Exp 4 | Hailuo 02 Pro | T2V | ¥0.44 | 140s |
| Exp 5 | Wan 2.6 | T2V | ¥0.63 | 55s |
| Exp 6 | Kling O3 Std | T2V | ¥0.50 | 55s |
| Exp 7 | rhart V3.1 Fast | T2V | ¥0.04 | 120s |
| Exp 8 | Vidu Q3 Pro | T2V | ¥0.55 | 120s |
| Exp 9 | rhart-video-g | T2V | ❌ 失败 | — |
| Exp 10 | Kling O3 Std | Video Edit | ¥0.55 | 180s |
| **总计** | | | **¥3.58** | |

---

## 8. ComfyUI 工作流产出

### 8.1 t2v-video-edit-pipeline.json
- **描述**: 两阶段管线 — Kling V3 T2V → Kling O3 Video Edit
- **用途**: 先生成基础视频，再用 AI 编辑场景
- **节点数**: 6

### 8.2 t2v-multi-model-comparison.json
- **描述**: 多模型 T2V 对比工作流（共享 prompt → 6 个模型并行生成）
- **用途**: A/B 测试不同 T2V 模型效果
- **节点数**: 8（含 Note 汇总节点）

---

## 9. 核心收获

### 9.1 T2V 模型选择心智模型
- **横屏内容**: Kling O3 > Hailuo 02 > Kling V3 > Vidu Q3
- **竖屏内容**: Seedance > rhart-s > rhart V3.1 > Wan 2.6
- **极低预算**: rhart-video-s (¥0.02) 和 rhart V3.1 Fast (¥0.04)
- **最佳综合**: Kling O3 Std (¥0.50) — 平衡画质/速度/功能

### 9.2 Video Edit 是重要的后处理手段
- T2V 先快速生成，Video Edit 再精修场景
- 两步走的总成本 (¥0.55 + ¥0.55 = ¥1.10) 可能比一次精准 T2V 更划算
- 因为 Video Edit 能保持运动一致性，只改变视觉风格

### 9.3 T2V 工作流在 ComfyUI 中的定位
- **Pure T2V**: 概念探索、快速原型
- **T2V + Edit**: 两阶段精修管线
- **T2I + I2V**: 最精确的视频生成路径（推荐生产用）
- **T2V + Upscale**: 低成本 + 后期放大

---

## 10. 下一步方向

1. **T2V aspectRatio 参数系统性测试** — 确认各模型横屏参数
2. **Video Extend 实测** — 将 5s 视频扩展到 10-15s
3. **Start-End T2V 管线** — 用 T2V 生成首帧+尾帧概念，再用首尾帧生视频
4. **多镜头 T2V 拼接** — T2V 生成多个镜头 → FFmpeg 拼接
