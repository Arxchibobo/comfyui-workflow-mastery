# PostGrad#19 — 统一 API 端点体系 + FLF 多模型深度对比

> 日期: 2026-03-25 00:03 UTC | 轮次: 63 | 成本: ¥1.42

## 📋 本轮学习目标

1. **Hailuo 02 统一 API 端点系统**：发现并测试 `video-other` 类别的统一端点
2. **Veo 3.1 Start-End-to-Video**：首次测试 FLF 专用端点（fast + pro 对比）
3. **Seedance V1.5 Pro T2V**：首次测试纯文本生视频能力
4. **多模型 FLF 对比**：同一首尾帧，4 个端点对比

---

## 1. Hailuo 02 统一 API 端点体系（重要发现）

### 1.1 端点分类发现

RunningHub 上的 Hailuo 02 有**两套 API**：

**专用端点（之前已测试）：**
| 端点 | 任务 | 参数名 |
|------|------|--------|
| `minimax/hailuo-02/i2v-standard` | image-to-video | `imageUrl` |
| `minimax/hailuo-02/i2v-pro` | image-to-video | `imageUrl` |
| `minimax/hailuo-02/t2v-standard` | text-to-video | 无图片参数 |
| `minimax/hailuo-02/t2v-pro` | text-to-video | 无图片参数 |

**统一端点（本次发现）：**
| 端点 | 类别 | 能力 | 图片参数 |
|------|------|------|----------|
| `minimax/hailuo-02/standard` | video-other | T2V + I2V + FLF | `firstImageUrl`(可选) + `lastImageUrl`(可选) |
| `minimax/hailuo-02/pro` | video-other | T2V + I2V + FLF | `firstImageUrl`(可选) + `lastImageUrl`(可选) |
| `minimax/hailuo-02/fast` | video-other | I2V only | `imageUrl`(必需) |

### 1.2 统一端点的模式切换逻辑

```
无图片参数         → T2V（纯文本生成）
只传 firstImageUrl → I2V（图生视频）
传 firstImageUrl + lastImageUrl → FLF（首尾帧生视频）
```

**关键发现：**
- 统一端点的 FLF 是**隐藏能力**（PostGrad#10 首次发现 standard 支持 FLF，本次用 pro 确认）
- Fast 模式不支持 FLF（参数名是 `imageUrl` 而非 `firstImageUrl`）
- Standard 支持 6/10 秒，Pro 只支持 6 秒

### 1.3 参数名差异速查（⚠️ 关键陷阱）

```
统一端点:     firstImageUrl / lastImageUrl
专用 I2V:     imageUrl
专用 FLF:     firstImageUrl / lastImageUrl（和统一端点一致）
Fast:         imageUrl（强制必需）
```

### 1.4 价格与专用端点对比

| 模式 | 统一端点价格 | 专用端点价格 | 差异 |
|------|-------------|-------------|------|
| Standard T2V | ¥0.25 | ¥0.25 (t2v-standard) | 相同 |
| Standard I2V | ¥0.25 | ¥0.25 (i2v-standard) | 相同 |
| Standard FLF | ¥0.25 | — (无专用端点) | 统一端点独有 |
| Pro FLF | ¥0.44 | — (无专用端点) | 统一端点独有 |

**结论：FLF 功能只能通过统一端点使用。**

---

## 2. Veo 3.1 Start-End-to-Video 首测

### 2.1 端点规格对比

| 参数 | Fast | Pro |
|------|------|-----|
| 实际引擎 | Google Veo 3.1 Fast | Google Veo 3.1 Pro |
| 时长 | 固定 8s | 固定 8s |
| 分辨率选项 | 720p / 1080p / 4K | 720p / 1080p / 4K |
| 宽高比 | 16:9 / 9:16 | 16:9 / 9:16 |
| 音频 | ✅ AAC 48kHz 立体声 | ✅ AAC 48kHz 立体声 |
| Prompt 限制 | 800 字符 | 800 字符 |
| `lastFrameUrl` | 可选 | 可选 |

### 2.2 仅提供首帧 vs 首尾帧

- 两个端点都支持省略 `lastFrameUrl`（变成类似 I2V 的模式）
- 提供两帧时 → 模型理解语义过渡，补全中间动画
- 仅首帧时 → 基于 prompt 自由发挥结尾

### 2.3 实验结果

| 变体 | 分辨率 | 帧率 | 时长 | 音频 | 生成时间 | 价格 |
|------|--------|------|------|------|---------|------|
| Fast 720p | 1280×720 | 24fps | 8.0s | ✅ AAC 48kHz | 145s | ¥0.04 |
| Pro 720p | 1280×720 | 24fps | 8.0s | ✅ AAC 48kHz | 140s | ¥0.13 |

**关键观察：**
- Pro 生成速度与 Fast 几乎一样（140s vs 145s），但贵 3.25x
- 两者都包含高质量音频（环境音效）
- 720p 下差异不明显，Pro 的优势可能在 1080p/4K 更显著
- ¥0.04/8s = ¥0.005/秒 → 视频 FLF 中**最极致的性价比**

---

## 3. Seedance V1.5 Pro T2V 首测

### 3.1 端点参数

| 参数 | 值 |
|------|-----|
| 宽高比 | 16:9/9:16/4:3/3:4/1:1/21:9（6种！） |
| 时长 | 4-12s（灵活） |
| 分辨率 | 480p/720p/1080p |
| 音频生成 | 可选 (generateAudio) |
| 固定镜头 | 可选 (cameraFixed) |
| Prompt 限制 | 5000 字符（最长！） |

### 3.2 实验结果

| 指标 | 结果 |
|------|------|
| 分辨率 | 1280×720 |
| 帧率 | 24fps |
| 时长 | 5.0s |
| 音频 | ✅ AAC 44100Hz 立体声 |
| 文件大小 | 6.8MB |
| 生成时间 | 50s（⭐极快！） |
| 价格 | ¥0.30 |

**Seedance T2V 独特优势：**
1. **21:9 超宽屏**支持 → 电影感最强
2. **5000 字符 prompt** → 最详细的场景描述
3. **50s 生成** → T2V 中最快之一
4. **cameraFixed 参数** → 明确控制镜头运动
5. **4-12s 灵活时长** → 按需调整

---

## 4. 多模型 FLF 对比（同一首尾帧）

### 4.1 完整对比表

```
端点                    分辨率      帧率  时长  音频  生成时间  价格   性价比(¥/秒)
─────────────────────  ──────────  ────  ────  ────  ───────  ─────  ──────────
Veo 3.1 Fast FLF       1280×720   24fps  8.0s  ✅    145s    ¥0.04   ¥0.005 ⭐
Veo 3.1 Pro FLF        1280×720   24fps  8.0s  ✅    140s    ¥0.13   ¥0.016
Hailuo 02 Std FLF      1376×768   24fps  5.9s  ❌    135s    ¥0.25   ¥0.042
Hailuo 02 Pro FLF      1934×1080  24fps  5.9s  ❌    200s    ¥0.44   ¥0.075
```

### 4.2 对比分析

**性价比排名（¥/秒含音频）：**
1. 🥇 **Veo 3.1 Fast** — ¥0.005/秒（含音频！）→ 绝对性价比之王
2. 🥈 **Veo 3.1 Pro** — ¥0.016/秒（含音频）
3. 🥉 **Hailuo 02 Standard** — ¥0.042/秒（无音频）
4. **Hailuo 02 Pro** — ¥0.075/秒（无音频，但分辨率最高）

**画质排名（基于分辨率）：**
1. 🥇 **Hailuo 02 Pro** — 1934×1080（最高像素数）
2. 🥈 **Hailuo 02 Standard** — 1376×768
3. 🥉 **Veo 3.1** — 1280×720（但支持 1080p/4K 选项未测）

**功能性排名：**
1. 🥇 **Veo 3.1** — 含音频 + 支持 4K + 8s 时长
2. 🥈 **Hailuo 02 Pro** — 最高分辨率 + prompt expansion
3. 🥉 **Hailuo 02 Standard** — 支持 10s 时长选项

### 4.3 FLF 模型选择决策树更新

```
需要 FLF →
├─ 预算最低 → Veo 3.1 Fast (¥0.04, 8s, 含音频) ⭐
├─ 需要音频 → Veo 3.1 Fast/Pro (唯二含音频的 FLF)
├─ 需要高分辨率 → Hailuo 02 Pro (1934×1080) 或 Veo 3.1 4K(未测)
├─ 需要 10 秒 → Hailuo 02 Standard (支持 6s/10s)
├─ 需要最快 → Hailuo 02 Standard (135s)
└─ 质量最高 → Veo 3.1 Pro 4K (¥待测) 或 Hailuo 02 Pro
```

---

## 5. 统一 API vs 专用 API 架构对比

### 5.1 设计哲学差异

| 维度 | 专用端点 | 统一端点 |
|------|---------|---------|
| 设计理念 | 一个端点一个任务 | 一个端点多种模式 |
| 参数复杂度 | 简单（固定输入） | 中等（可选参数决定模式） |
| 工作流集成 | 每种任务一个节点 | 一个节点多种行为 |
| 错误概率 | 低（参数明确） | 中（参数组合可能意外） |
| 灵活性 | 低 | 高（动态切换模式） |

### 5.2 ComfyUI 工作流映射

**专用端点映射（已有节点）：**
```
KlingTextToVideoNode → kling-v3.0/text-to-video
KlingImageToVideoNode → kling-v3.0/image-to-video
SeedanceFLF2VNode → seedance/first-last-frame
```

**统一端点映射（需自定义节点）：**
```
HailuoUnifiedNode:
  mode: "t2v" | "i2v" | "flf"  (由输入连接决定)
  if firstImageUrl connected → I2V 或 FLF
  if lastImageUrl connected → FLF
  else → T2V
```

### 5.3 统一端点在工作流中的优势

1. **条件路由简化**：一个节点替代三个，通过输入连接动态切换
2. **批量任务灵活**：同一管线可以处理纯文本、单图、双图输入
3. **参数一致性**：prompt/duration/enablePromptExpansion 全模式通用
4. **FLF 独占性**：某些 FLF 能力只在统一端点中可用

---

## 6. Hailuo 02 Standard T2V 分析

### 6.1 T2V 与 FLF 分辨率差异

有趣发现：
- T2V 模式: 1366×768
- FLF 模式: 1376×768
- 差异 10px → 可能是内部分辨率对齐策略不同

### 6.2 T2V 生成速度

- 80s（T2V）vs 135s（FLF）→ 无参考图时生成更快
- 这符合直觉：T2V 不需要编码参考图+保持一致性

---

## 7. 全模型 T2V 能力更新对比

```
端点                      宽高比选择    时长范围    音频   价格    生成速度  分辨率
─────────────────────────  ──────────  ─────────  ────  ──────  ───────  ──────────
Seedance V1.5 Pro T2V      6种(含21:9)  4-12s     ✅    ¥0.30   50s     1280×720
Hailuo 02 Std (unified)    自动         6/10s     ❌    ¥0.25   80s     1366×768
Hailuo 02 Pro (unified)    自动         6s        ❌    ¥0.44   ~120s   1934×1080
rhart-video-s T2V          16:9/9:16    默认       🔊    ¥0.02   ~60s    704×1280
rhart-video-s Pro T2V      多种         默认       🔊    ¥0.30   ~120s   1792×1024
Kling V3.0 std T2V         多种         3-15s     ✅    ¥0.55   ~120s   960×960
Wan 2.6 T2V                16:9/9:16    5s        ❌    ¥0.63   ~90s    1280×720
```

**T2V 新发现排名：**
1. **最快 T2V** → Seedance V1.5 Pro（50s）
2. **最便宜 T2V** → rhart-video-s（¥0.02）
3. **最高分辨率 T2V** → Hailuo 02 Pro / rhart-s Pro（~1080p）
4. **最灵活宽高比** → Seedance（6种含 21:9 超宽）
5. **最长时长** → Kling V3.0（3-15s）

---

## 8. ComfyUI 工作流 JSON 设计

### 8.1 Veo 3.1 FLF + Hailuo FLF 对比工作流（概念设计）

```json
{
  "description": "FLF Quality Router - 同一首尾帧，多模型对比",
  "nodes": {
    "1": {"class": "LoadImage", "inputs": {"image": "first_frame.jpg"}, "_meta": {"title": "First Frame"}},
    "2": {"class": "LoadImage", "inputs": {"image": "last_frame.jpg"}, "_meta": {"title": "Last Frame"}},
    "3": {
      "class": "Veo31FLFNode",
      "inputs": {
        "first_frame": ["1", 0],
        "last_frame": ["2", 0],
        "prompt": "smooth transition...",
        "resolution": "720p",
        "aspect_ratio": "16:9"
      },
      "_meta": {"title": "Veo 3.1 Fast FLF (¥0.04)"}
    },
    "4": {
      "class": "HailuoUnifiedNode",
      "inputs": {
        "firstImageUrl": ["1", 0],
        "lastImageUrl": ["2", 0],
        "prompt": "smooth transition...",
        "duration": "6",
        "enablePromptExpansion": true,
        "quality": "standard"
      },
      "_meta": {"title": "Hailuo 02 Standard FLF (¥0.25)"}
    }
  }
}
```

### 8.2 Partner Node 映射分析

**Veo 3.1 FLF 对应的 Partner Node：**
- ComfyUI Partner Nodes 目前可能没有 FLF 专用节点
- 需要通过 `PollingOperation` 基类创建自定义节点
- 或者使用 API 代理模式调用

**Hailuo 02 统一端点：**
- MiniMax Partner Nodes 可能已支持 `firstImageUrl` + `lastImageUrl`
- 但需要确认统一模式是否在 ComfyUI 节点中暴露

---

## 9. 实验汇总

| # | 实验 | 端点 | 结果 | 时间 | 成本 |
|---|------|------|------|------|------|
| 63a | 首帧生成（日景庭园） | rhart-image-n-pro T2I | 成功 | 25s | ¥0.03 |
| 63b | 尾帧生成（夜景庭园） | rhart-image-n-pro T2I | 成功 | 20s | ¥0.03 |
| 63c | Veo 3.1 Fast FLF | rhart-video-v3.1-fast/start-end-to-video | 1280×720/8s/🔊 | 145s | ¥0.04 |
| 63d | Hailuo 02 Std FLF | minimax/hailuo-02/standard | 1376×768/5.9s | 135s | ¥0.25 |
| 63e | Hailuo 02 Std T2V | minimax/hailuo-02/standard | 1366×768/5.9s | 80s | ¥0.25 |
| 63f | Hailuo 02 Pro FLF | minimax/hailuo-02/pro | 1934×1080/5.9s | 200s | ¥0.44 |
| 63g | Veo 3.1 Pro FLF | rhart-video-v3.1-pro/start-end-to-video | 1280×720/8s/🔊 | 140s | ¥0.13 |
| 63h | Seedance V1.5 Pro T2V | seedance-v1.5-pro/text-to-video | 1280×720/5s/🔊 | 50s | ¥0.30 |
| **总计** | | | | | **¥1.47** |

---

## 10. 关键发现总结

### 🔑 三大核心发现

1. **Hailuo 02 统一端点是 FLF 的唯一入口**
   - 专用端点没有 FLF 能力
   - 统一端点通过参数组合动态切换 T2V/I2V/FLF 模式
   - `video-other` 分类容易被忽视

2. **Veo 3.1 FLF 是全场景最优 FLF 方案**
   - ¥0.04/8s 含音频 → 性价比碾压所有竞品
   - 支持 720p/1080p/4K 三档分辨率
   - 唯一支持音频的 FLF 端点

3. **Seedance V1.5 Pro T2V 是最快的文生视频**
   - 50s 生成速度领先
   - 6 种宽高比（含 21:9 超宽）
   - 5000 字符 prompt 最长
   - cameraFixed 镜头控制

### 📝 ComfyUI 工作流启示

- 统一端点模式适合做「动态路由节点」— 一个节点根据输入自动切换行为
- Veo 3.1 FLF 应该被纳入所有视频管线的首选 FLF 方案
- Partner Nodes 体系可能需要新增 FLF 专用节点类型

### 💰 FLF 模型选择最终策略

| 场景 | 推荐 | 价格 |
|------|------|------|
| 默认首选 | Veo 3.1 Fast | ¥0.04 |
| 需要音频+过渡 | Veo 3.1 Fast | ¥0.04 |
| 需要高分辨率 | Hailuo 02 Pro | ¥0.44 |
| 需要 10 秒 FLF | Hailuo 02 Standard (duration=10) | ¥0.25 |
| 质量优先 | Veo 3.1 Pro 4K | ¥估计 ¥0.5+ |
| 多模型保险 | Veo 3.1 Fast + Hailuo 02 Pro 双跑 | ¥0.48 |
