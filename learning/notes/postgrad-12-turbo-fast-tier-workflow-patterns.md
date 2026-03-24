# PostGrad#12: Turbo/Fast 模型层级对比 + ComfyUI 工作流 JSON 编排模式

> 日期: 2026-03-24 10:03 UTC | 轮次: 56 | 累计实验: 65

## 1. Turbo/Fast 模型层级系统性对比

### 1.1 实验设计

**统一控制变量**:
- 同一参考图（龙虾厨师 in 日式庭园）
- 同一/相似 Prompt
- 5s 时长（有些模型固定不可调）
- 16:9 横屏

**测试模型矩阵**（6 模型首测）:

| 模型 | 层级 | 分辨率 | 时长 | FPS | 耗时 | 成本 | 音频 | 文件大小 |
|------|------|--------|------|-----|------|------|------|----------|
| Kling V2.5 Turbo Pro | turbo+pro | 1924×1076 | 5.04s | 24 | 75s | ¥0.30 | 🔇 | 13.4MB |
| Kling V2.5 Turbo Std | turbo+std | 1284×716 | 5.04s | 24 | 235s | ¥0.18 | 🔇 | 9.2MB |
| Hailuo 2.3 Pro I2V | pro | 1934×1080 | 5.87s | 24 | 155s | ¥0.44 | 🔇 | 2.6MB |
| Hailuo 2.3 Fast Pro | fast+pro | 1934×1080 | 5.87s | 24 | 105s | ¥0.29 | 🔇 | 4.5MB |
| Wan 2.6 Flash I2V | flash | 1926×1076 | 5.01s | 30 | 50s | ¥0.30 | 🔊 | 13.2MB |
| Wan 2.6 Flash Ref2V | flash+ref | 1920×1080 | 5.05s | 30 | 220s | ¥0.30 | 🔊 | 5.0MB |

### 1.2 关键发现

#### 🔑 发现一：Kling V2.5 Turbo 层级体系

Kling 的版本×层级矩阵：
```
V2.5 Turbo Std  → ¥0.18  720p  最便宜的 Kling 方案
V2.5 Turbo Pro  → ¥0.30  1080p 速度最快(75s)
V3.0 Std        → ¥0.25  720p  标准画质
V3.0 Pro        → ¥0.55  1080p 最高画质
O1              → ¥0.50  1080p 多能力(Ref2V/FLF/Edit)
O3 Std          → ¥0.50  1080p 全能力
O3 Pro          → ¥0.55  1080p 全能力最高级
```

**Turbo vs Standard 核心区别**：
- Turbo 用蒸馏模型（推理步数更少，速度更快）
- Pro vs Std 区别：分辨率（1080p vs 720p）
- V2.5 Turbo Pro 是**性价比甜点**：¥0.30 拿到 1080p，速度 75s（比 V3.0 Pro 快 50%+）
- ⚠️ Turbo Std 竟然比 Turbo Pro 更慢（235s vs 75s），可能是排队或服务端差异

**Kling Turbo 特有参数**：
- `firstImageUrl`（不是 `imageUrl`！与 V3.0 参数名不同）
- `lastImageUrl` 可选（支持首尾帧！V2.5 Turbo 也有这个能力）
- `guidanceScale` 0-1（默认 0.5，类似 denoise 概念）

#### 🔑 发现二：Wan 2.6 Flash 系列

Flash = 万象的轻量化推理版本，两种模式：
- **Flash I2V**: 标准图生视频，50s 极快，¥0.30，1080p+30fps+音频
- **Flash Ref2V**: 参考生视频（角色保持），220s 较慢，¥0.30，1080p+30fps+音频

**Flash vs Standard 对比**：
| 维度 | Standard I2V | Flash I2V | Flash Ref2V |
|------|-------------|-----------|-------------|
| 成本 | ¥0.63 | ¥0.30 | ¥0.30 |
| 速度 | 210s | **50s** | 220s |
| 分辨率 | 1920×1080 | 1926×1076 | 1920×1080 |
| FPS | 30 | 30 | 30 |
| 音频 | 🔊 | 🔊 | 🔊 |
| 质量 | 最高 | 略低 | 参考保持能力强 |

**关键**：Flash I2V 是目前**最快的高质量 I2V** — 50s 出 1080p 30fps 带音频，只要 ¥0.30（性价比仅次于 Veo 3.1 Fast ¥0.04）

Flash Ref2V 参数亮点：
- 支持最多 **5 张参考图** + **3 个参考视频**
- 支持 1920×1080 原生高分辨率
- `shotType`: single/multi（多镜头模式！）
- `audio`: 原生音频生成
- `duration`: 2-10s 灵活选择

#### 🔑 发现三：Hailuo 2.3 层级体系

```
Hailuo 2.3 Standard I2V  → ¥0.25  1376×768  5.87s  基础版
Hailuo 2.3 Pro I2V       → ¥0.44  1934×1080 5.87s  高分辨率
Hailuo 2.3 Fast I2V      → ¥0.08  低分辨率       快速版
Hailuo 2.3 Fast Pro I2V  → ¥0.29  1934×1080 5.87s  快速+高分辨率
```

**Hailuo 分辨率异常**：1934×1080（不是标准 1920×1080），所有版本一致

**Pro vs Standard 对比**：
- Pro 分辨率提升 40%（1934×1080 vs 1376×768）
- Pro 成本 +76%（¥0.44 vs ¥0.25）
- Fast Pro 是**最佳 Hailuo 选择**：¥0.29 拿到 Pro 分辨率，速度 105s（比 Pro 155s 快 32%）

**Hailuo 致命缺陷**：所有版本均**无音频**（🔇）！这在 2026 年竞争格局中是重大劣势。

### 1.3 性价比排名（I2V ¥/秒 @ 1080p）

```
性价比排名（1080p I2V）:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ⭐ Veo 3.1 Fast         ¥0.005/秒  (¥0.04/8s)    🔊
 2. Wan 2.6 Flash I2V    ¥0.060/秒  (¥0.30/5s)    🔊
 3. Kling V2.5 Turbo Pro ¥0.060/秒  (¥0.30/5s)    🔇
 4. Hailuo 2.3 Fast Pro  ¥0.049/秒  (¥0.29/5.87s) 🔇
 5. Seedance Fast        ¥0.060/秒  (¥0.30/5s)    🔊
 6. Hailuo 2.3 Pro       ¥0.075/秒  (¥0.44/5.87s) 🔇
 7. Kling V3.0 Pro       ¥0.110/秒  (¥0.55/5s)    🔇
 8. Wan 2.6 Standard     ¥0.126/秒  (¥0.63/5s)    🔊
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**2026-03 I2V 模型选择更新决策树**：
```
                    I2V 需求
                       │
              ┌────────┼────────┐
          极致预算     平衡       最高质量
              │        │          │
        Veo 3.1 Fast  ├──有音频？  Kling V3.0 Pro
         ¥0.04/8s     │   │       ¥0.55/5s
                    是──┘   └──否
                    │           │
              Wan Flash    Kling V2.5 Turbo Pro
              ¥0.30/5s    ¥0.30/5s (最快75s)
              (50s最快)
              
        参考生视频(Ref2V)?
              │
        ┌─────┼─────┐
      快速   平衡   最强
        │     │      │
   Seedance  Wan    Kling O3
    ¥0.15   Flash    ¥0.50
            ¥0.30
```

### 1.4 速度排名（I2V 出图耗时）

```
速度排名:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ⭐ Wan 2.6 Flash I2V     50s
 2. Kling V2.5 Turbo Pro  75s
 3. Hailuo 2.3 Fast Pro  105s
 4. Hailuo 2.3 Pro       155s
 5. Wan 2.6 Flash Ref2V  220s
 6. Kling V2.5 Turbo Std 235s  ← 疑似排队
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 2. ComfyUI 工作流 JSON 高级编排模式

### 2.1 工作流 JSON 格式回顾

ComfyUI 工作流 JSON 有两种格式：
- **API 格式**（精简版）：`{ "节点ID": { "class_type": "...", "inputs": {...} } }`
  - 用于 `/prompt` API 提交
  - 节点之间通过 `["源节点ID", 输出索引]` 引用
- **GUI 格式**（完整版）：包含 `nodes[]` + `links[]` + 位置/大小/UI 状态
  - 用于 ComfyUI 前端加载
  - 节点引用方式不同（link ID → links 数组查找）

### 2.2 API 格式核心语法

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "flux1-dev-fp8.safetensors"
    }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "a beautiful landscape",
      "clip": ["1", 1]  // ← 引用节点1的第2个输出(CLIP, 0-indexed)
    }
  }
}
```

**关键规则**：
- 节点 ID 是字符串（"1", "2" 等）
- 输入引用格式：`["源节点ID", 输出slot索引]`
- 输出索引从 0 开始
- 非引用的输入直接赋值

### 2.3 Partner Nodes 视频工作流编排模式

Partner Nodes（Kling/Seedance/Veo 等）在 ComfyUI 中的节点模式：

**模式 A：同步操作（图像类）**
```
LoadImage → [API Node: SynchronousOperation] → SaveImage
```
等待 API 返回，直接获取结果。

**模式 B：轮询操作（视频类）**
```
LoadImage → [Submit Node: creates task_id] → [Poll Node: waits for completion] → SaveVideo
```
大多数视频 API 都是异步的。

**模式 C：Kling 完整 I2V 工作流节点链**
```json
{
  "1": { "class_type": "LoadImage", "inputs": { "image": "input.png" } },
  "2": {
    "class_type": "KlingImageToVideoNode",
    "inputs": {
      "prompt": "...",
      "negative_prompt": "",
      "cfg_scale": 0.5,
      "mode": "pro",
      "duration": "5",
      "aspect_ratio": "16:9",
      "image": ["1", 0],
      "AUTH_TOKEN_COMFY_ORG": "..."
    }
  },
  "3": { "class_type": "VHS_VideoCombine", "inputs": { "images": ["2", 0], ... } }
}
```

### 2.4 多模型对比工作流设计模式

**核心思路**：同一输入图 → 多条并行管线 → 各自输出

```
                  ┌─→ [Kling V3 I2V] ──→ [Save "kling-v3"]
LoadImage ────────┼─→ [Seedance I2V] ──→ [Save "seedance"]
                  ├─→ [Wan 2.6 I2V]  ──→ [Save "wan26"]
                  └─→ [Veo 3.1 I2V]  ──→ [Save "veo31"]
```

这是 ComfyUI 的天然优势 — **一次提交，多模型并行执行**（前提：每个 API 节点独立轮询）。

### 2.5 ComfyUI 工作流 JSON 编写最佳实践

1. **节点 ID 命名约定**：使用有意义的数字段
   - 1-9: 输入/加载节点
   - 10-19: 预处理
   - 20-29: 核心生成
   - 30-39: 后处理
   - 40-49: 输出/保存

2. **参数外部化**：标记需要动态替换的参数
   ```json
   "prompt": "{{PROMPT}}"  // 用占位符，API 调用时替换
   ```

3. **错误隔离**：每条管线独立，一个失败不影响其他

4. **输出命名**：使用 `filename_prefix` 区分不同管线的输出
   ```json
   { "class_type": "SaveImage", "inputs": { "filename_prefix": "exp/kling-v3" } }
   ```

5. **条件路由**：使用 Switch 节点根据参数选择不同管线
   ```
   Input → [Switch: if model=="kling"] → Kling Pipeline
                                        → Seedance Pipeline
   ```

### 2.6 生产级工作流编排 Pattern

#### Pattern 1: 串行管线（最常用）
```
T2I → Upscale → I2V → V2A → FFmpeg Combine
```
每个节点依赖前一个的输出。

#### Pattern 2: 并行+汇聚
```
          ┌─→ [Kling I2V] ─┐
Image ────┤                 ├─→ [Select Best] → Output
          └─→ [Wan I2V]   ─┘
```
多模型竞赛，选最优。

#### Pattern 3: 分层合成
```
Image ──→ [RMBG: 分离前景/背景]
            │                 │
      [前景 I2V]         [背景静态]
            │                 │
            └───→ [合成] ←────┘
```

#### Pattern 4: 迭代精炼
```
Image → [Edit: Round 1] → [Edit: Round 2] → [Edit: Round 3] → Output
```
链式编辑，逐步精炼。

## 3. ComfyUI 多模型对比工作流 JSON

编写一个完整的 4 模型 I2V 对比工作流（API 格式）：

```json
// 见 sample-workflows/postgrad/multi-model-i2v-comparison-v2.json
```

关键设计点：
- 共享输入节点（LoadImage 只加载一次）
- 4 条并行 I2V 管线
- 各自独立的 SaveVideo 输出
- 统一 prompt 变量

## 4. 模型 API 参数差异速查

### 4.1 图片输入参数名称差异（⚠️ 易踩坑）

```
Kling V3.0:      imageUrl / image      (单一图片)
Kling V2.5:      firstImageUrl         (⚠️ 名称不同！)
Kling O1/O3:     imageUrl + prompt中 @image引用
Seedance:        imageUrl / image
Hailuo:          imageUrl
Wan 2.6:         imageUrls (数组！)
Veo 3.1:         image
Vidu:            imageUrl
```

### 4.2 ComfyUI Partner Node 输入对照

```
KlingImageToVideoNode:     image (IMAGE type)
KlingStartEndToVideoNode:  start_image + end_image
SeedanceImageToVideoNode:  image
VeoImageToVideoNode:       image
HailuoImageToVideoNode:    image (if exists)
```

### 4.3 特殊参数对照

| 模型 | CFG参数 | 时长选项 | 宽高比 |
|------|---------|----------|--------|
| Kling V3 | cfg_scale 0-1 | 5/10 | 16:9/9:16/1:1 |
| Kling V2.5 Turbo | guidanceScale 0-1 | 5/10 | 无(跟随图片) |
| Seedance | N/A | 5 固定 | 跟随图片 |
| Wan 2.6 | N/A | 2-10 灵活 | size 参数 |
| Hailuo 2.3 | N/A | 6 固定(fast)/变 | 跟随图片 |
| Veo 3.1 | N/A | 8 固定 | 跟随图片 |

## 5. 总结与心智模型更新

### 5.1 Turbo/Fast 模型定位

```
                    质量
                     ↑
                     │  ✦ Kling V3 Pro (¥0.55)
                     │  ✦ Wan 2.6 Std (¥0.63)
                     │  ✦ Kling O3 (¥0.50)
              ───────┼──✦ Kling V2.5 Turbo Pro (¥0.30) ← 性价比王
                     │  ✦ Wan Flash (¥0.30) ← 速度王+音频
                     │  ✦ Seedance Fast (¥0.30)
                     │  ✦ Hailuo Fast Pro (¥0.29)
              ───────┼─────────────────────────── → 性价比线
                     │  ✦ Veo 3.1 Fast (¥0.04) ← 极致性价比
                     │  ✦ Kling V2.5 Turbo Std (¥0.18)
                     │
                     └──────────────────────────→ 成本

图例：线上=推荐  线下=预算方案
```

### 5.2 本轮实验成本汇总

| 实验 | 模型 | 耗时 | 成本 |
|------|------|------|------|
| 参考图 | rhart-image-n-pro | 25s | ¥0.03 |
| #60 | Kling V2.5 Turbo Pro | 75s | ¥0.30 |
| #61 | Wan 2.6 Flash Ref2V | 220s | ¥0.30 |
| #62 | Hailuo 2.3 Pro | 155s | ¥0.44 |
| #63 | Kling V2.5 Turbo Std | 235s | ¥0.18 |
| #64 | Wan 2.6 Flash I2V | 50s | ¥0.30 |
| #65 | Hailuo 2.3 Fast Pro | 105s | ¥0.29 |
| **总计** | | | **¥1.84** |
