# PostGrad#17 — ComfyUI 多阶段工作流编排 + 新模型实测

> 学习时间: 2026-03-24 20:04 UTC | 轮次 #61 | 成本: ¥1.35

## 🎯 本轮目标

1. **ComfyUI 多阶段工作流 JSON 编排深度** — 从 T2I 到 Video Edit 的完整链式管线
2. **Vidu Q3 Pro 首尾帧实测** — Q3 vs Q2 系列对比
3. **Wan 2.6 Flash Ref2V 首测** — 低成本参考生视频方案
4. **完整管线实测** — T2I → Upscale → I2V + Audio

---

## 1. ComfyUI 多阶段工作流 JSON 编排模式

### 1.1 工作流 JSON 核心结构回顾

ComfyUI 工作流 JSON 是一个节点字典，每个节点由 `class_type` + `inputs` 定义，节点间通过 `["nodeId", outputIndex]` 引用连接。

```json
{
  "nodeId": {
    "class_type": "ClassName",
    "inputs": {
      "param1": "value",
      "param2": ["otherNodeId", 0]  // 引用其他节点的输出
    }
  }
}
```

### 1.2 多阶段管线的五种编排模式

#### 模式一：线性管线（Sequential Pipeline）
```
[T2I] → [Upscale] → [I2V] → [Edit] → [Save]
```
- **特点**: 每个阶段串行执行，前一阶段的输出是后一阶段的输入
- **适用**: 单一产品的完整生产流程
- **示例**: `multi-stage-t2i-upscale-i2v-audio-pipeline.json`

#### 模式二：扇出对比（Fan-out Comparison）
```
              ┌→ [Model A] → [Save A]
[LoadImage] → ├→ [Model B] → [Save B]  
              └→ [Model C] → [Save C]
```
- **特点**: 共享输入层，多分支并行（ComfyUI 默认串行但无依赖）
- **适用**: A/B/C 模型选型对比测试
- **示例**: `ref2v-multi-model-comparison.json`

#### 模式三：钻石合并（Diamond Merge）
```
[T2I] → [Image] → [I2V Video] ─┐
                                ├→ [FFmpeg Merge] → [Final]
[T2I] → [Image] → [TTS Audio] ─┘
```
- **特点**: 多条分支最终合并为一个输出
- **限制**: ComfyUI 原生不支持 FFmpeg 合并节点，需自定义节点或后处理脚本
- **实现**: 通常用 VHS_VideoCombine 或外部 Python 脚本

#### 模式四：迭代精炼（Iterative Refinement）
```
[T2I] → [I2V] → [Edit pass 1] → [Edit pass 2] → [Upscale] → [Save]
```
- **特点**: 多轮 API 调用逐步精炼
- **注意**: 每轮 API 调用有成本，需要成本意识

#### 模式五：条件路由（Conditional Routing）
```
                     ┌→ [Kling V3 I2V]     (if budget > ¥0.5)
[T2I] → [Condition] → 
                     └→ [Veo 3.1 Fast I2V]  (if budget ≤ ¥0.5)
```
- **限制**: ComfyUI 原生不支持条件路由，需要自定义节点（Switch/If-Else）
- **实现**: Impact Pack 的 Switch 节点 或 `rgthree-comfy` 的 PowerLoom

### 1.3 Partner Node 链式调用的关键模式

#### VIDEO 类型传播

ComfyUI 0.3.x+ 引入了原生 `VIDEO` 数据类型（PR #7844），Partner Node 的视频输出可以直接作为下一个 Partner Node 的输入：

```json
// I2V 输出 VIDEO 类型
"30": {
  "class_type": "KlingImageToVideoNode",
  "inputs": { "image": ["22", 0], ... }
}

// Video Edit 接收 VIDEO 类型
"40": {
  "class_type": "KlingVideoEditNode", 
  "inputs": { "video": ["30", 0], ... }  // 直接连接！
}
```

#### 音频传递模式

```
I2V (sound=true) → Video Edit (keepOriginalSound=true) → 最终视频保留音频
```

- Kling V3.0 的 `sound` 参数：生成视频时自动配音
- Kling O3 Edit 的 `keepOriginalSound`：编辑时保留原音轨
- 无需额外 V2A 步骤

#### 中间检查点（Checkpoint Pattern）

在每个阶段之间插入 `SaveImage` 节点，方便调试和断点续传：

```json
"9": {
  "class_type": "SaveImage",
  "inputs": {
    "filename_prefix": "pipeline_s1_keyframe",
    "images": ["8", 0]
  }
}
```

### 1.4 分辨率管理策略

生产管线中分辨率规划至关重要：

| 阶段 | 分辨率 | 原因 |
|------|--------|------|
| T2I 生成 | 1280×720 | Flux 最佳生成分辨率 |
| ESRGAN 放大 | 2560×1440 | 2x 放大增加细节 |
| Resize 归一化 | 1920×1080 | I2V API 输入标准化 |
| I2V 输出 | ~1280×720 | Kling V3.0 Std 输出 |
| Video Edit | ~720p/1080p | O3 Pro 自动超分到 1080p |

**关键洞察**: 生成小 → 放大大 → 缩回标准 的流程比直接生成高分辨率质量更好（ESRGAN 添加的细节比 Flux 直接生成 1080p 更丰富）。

### 1.5 成本优化策略

| 策略 | 说明 | 节省 |
|------|------|------|
| 本地 T2I | Flux Dev fp8 本地推理 vs API ¥0.03 | 100% |
| 本地放大 | ESRGAN 本地 vs Topaz ¥0.10 | 100% |
| Std vs Pro | I2V 用 Std (¥0.55) vs Pro (¥0.75) | 27% |
| Flash 模型 | Wan Flash (¥0.20) vs Full (¥0.65) | 69% |
| 跳过 Edit | 不需要风格转换时跳过 Stage 4 | ¥0.88 |

---

## 2. 实验结果

### 实验 #62: 参考图生成 (rhart-image-n-pro T2I)
- **Prompt**: Lobster samurai in moonlit bamboo forest
- **输出**: 1376×768 (默认 16:9)
- **时间**: 25s
- **成本**: ¥0.03

### 实验 #63: ⭐ Vidu Q3 Pro 首尾帧生视频（首测）
- **模型**: vidu/start-end-to-video-q3-pro
- **输入**: 首帧(站立) + 尾帧(跳跃) + prompt
- **输出**: 1284×716 / H.264 / 4s / 24fps
- **音频**: ✅ AAC 48kHz 立体声
- **时间**: 65s
- **成本**: ¥0.44

**对比 Q2 Pro (PostGrad#5)**:
| 维度 | Q2 Pro | Q3 Pro |
|------|--------|--------|
| 分辨率 | 1280×720 | 1284×716 |
| 帧率 | 24fps | 24fps |
| 音频 | ✅ | ✅ |
| 价格 | ¥0.55 | ¥0.44 |
| 速度 | ~125s | ~65s |
| 最大时长 | 8s | 16s |

**Q3 Pro 关键优势**:
- 价格降低 20% (¥0.55 → ¥0.44)
- 速度快 1.9x (125s → 65s)
- 最大时长从 8s 扩展到 16s！
- 运动幅度控制 (movementAmplitude) 新参数
- 分辨率支持 540p/720p/1080p

### 实验 #64: ⭐ Wan 2.6 Flash Ref2V（首测）
- **模型**: alibaba/wan-2.6/reference-to-video-flash
- **输入**: 参考图 + prompt
- **输出**: 1280×720 / H.264 / 5s / 30fps
- **音频**: ✅ AAC 44.1kHz 立体声
- **时间**: 75s
- **成本**: ¥0.20

**对比 Wan 2.6 Full Ref2V (PostGrad#2)**:
| 维度 | Wan 2.6 Full | Wan 2.6 Flash |
|------|-------------|---------------|
| 分辨率 | 1280×720 | 1280×720 |
| 帧率 | 24fps | 30fps |
| 音频 | ✅ | ✅ |
| 价格 | ¥0.65 | ¥0.20 |
| 速度 | ~100s | ~75s |
| 最大时长 | 10s | 10s |

**Flash 关键优势**:
- 价格降低 69%！(¥0.65 → ¥0.20)
- 帧率更高 (24fps → 30fps) 更流畅
- 速度更快 (100s → 75s)
- 支持 shotType (single/multi) 参数
- 支持最大 1920×1080 分辨率
- **性价比碾压级**: ¥0.04/秒 (Flash) vs ¥0.13/秒 (Full)

### 实验 #65: Topaz Standard V2 Upscale
- **输入**: 1376×768 参考图
- **输出**: 2752×1536 (2x)
- **时间**: 15s
- **成本**: ¥0.10

### 实验 #66: 完整管线 — Kling V3.0 Std I2V + Audio
- **输入**: 2752×1536 放大后的参考图
- **输出**: 1284×716 / H.264 / 5s / 24fps + AAC 44.1kHz 立体声
- **时间**: 60s
- **成本**: ¥0.55
- **管线总成本**: ¥0.03 (T2I) + ¥0.03 (尾帧) + ¥0.10 (Upscale) + ¥0.55 (I2V) = ¥0.71

---

## 3. Ref2V 模型选择策略更新

基于 PostGrad#2 + PostGrad#17 的全部测试，更新后的 Ref2V 模型排名：

### 按性价比排名（¥/秒）
| 排名 | 模型 | ¥/秒 | 帧率 | 音频 | 分辨率 |
|------|------|-------|------|------|--------|
| ⭐1 | Seedance V1 Lite | ¥0.030 | 24fps | ❌ | ~1248×704 |
| 2 | Wan 2.6 Flash | ¥0.040 | 30fps | ✅ | 1280×720 |
| 3 | Kling O3 Std | ¥0.100 | 24fps | ❌ | ~1280×720 |
| 4 | Wan 2.6 Full | ¥0.130 | 24fps | ✅ | 1280×720 |

### 决策树
```
需要 Ref2V?
├── 需要音频？
│   ├── 是 → Wan 2.6 Flash (¥0.20, 30fps, 音频内置)
│   └── 否 → 预算限制？
│       ├── <¥0.20 → Seedance V1 Lite (¥0.15)
│       ├── <¥0.50 → Wan 2.6 Flash (¥0.20)
│       └── 质量优先 → Kling O3 Std (¥0.50)
└── 需要多图引用(5-7张)？
    └── Kling O3 Std/Pro 或 Wan 2.6 (多 imageUrls)
```

---

## 4. ComfyUI Partner Node 工作流编排实践总结

### 4.1 节点类型映射（API 端点 → ComfyUI Partner Node）

| RunningHub API | ComfyUI Partner Node | 数据类型 |
|----------------|---------------------|----------|
| */text-to-image | Flux/SD 本地节点 | IMAGE |
| */image-to-video | KlingImageToVideoNode | VIDEO |
| */reference-to-video | KlingOmniEditModelNode | VIDEO |
| */start-end-to-video | KlingStartEndToVideoNode | VIDEO |
| */video-edit | KlingVideoEditNode | VIDEO |
| */video-extend | Veo3VideoExtendNode | VIDEO |
| */text-to-video | KlingTextToVideoNode | VIDEO |
| */motion-control | KlingMotionControlNode | VIDEO |
| */image-upscale | ImageUpscaleWithModel (本地) | IMAGE |

### 4.2 VIDEO 类型的链式传播规则

Partner Nodes 的 VIDEO 类型在 ComfyUI 中可以直接链式传递：
- I2V 输出 (VIDEO) → Video Edit 输入 ✅
- I2V 输出 (VIDEO) → Video Extend 输入 ✅
- Video Edit 输出 (VIDEO) → 第二次 Edit 输入 ✅
- VIDEO → VHS_VideoCombine (需类型转换节点或兼容版本)

**⚠️ 注意**: VIDEO 类型是 ComfyUI 较新的添加（0.3.x+），不是所有第三方节点都支持。VHS 等老节点可能需要 IMAGE 序列而非 VIDEO。

### 4.3 编写工作流 JSON 的最佳实践

1. **节点 ID 分段**: Stage 1 用 1-9, Stage 2 用 20-29, Stage 3 用 30-39... 便于维护
2. **`_meta` 注释**: 每个节点添加 title 和 notes，方便团队理解
3. **`_comment_*` 段落**: JSON 中添加注释字段（以 `_` 开头的键不影响执行）
4. **Checkpoint 节点**: 每阶段间插入 SaveImage，支持断点调试
5. **参数外化**: 将关键参数（prompt/seed/model_name）放在工作流顶部或通过 API 注入

---

## 5. 新发现与关键洞察

### 5.1 Vidu Q3 系列的重大升级
- **时长翻倍**: Q2 最大 8s → Q3 最大 16s
- **价格下降**: Q2 Pro ¥0.55 → Q3 Pro ¥0.44 (-20%)
- **速度翻倍**: Q2 ~125s → Q3 ~65s
- **新控制**: movementAmplitude (auto/small/medium/large)
- **新分辨率**: 支持 1080p
- **结论**: Q3 全面替代 Q2，不再推荐使用 Q2 系列

### 5.2 Wan 2.6 Flash Ref2V 的颠覆性价比
- **¥0.20 = 5秒1280×720视频 + 30fps + 音频**
- 比 Full 版便宜 69%，且帧率更高(30fps vs 24fps)
- 支持 shotType 参数（single/multi 单镜头/多镜头）
- 支持 negativePrompt
- **最适合**: 快速原型验证、批量视频生成、成本敏感场景

### 5.3 放大后再送 I2V 的效果
- 原图 1376×768 → Topaz 放大到 2752×1536 → 送 Kling V3.0
- Kling 输出仍然是 1284×716（受 Std 模式限制）
- **结论**: 对于 Std 模式的 I2V，放大输入图并不能提升输出分辨率
- **建议**: 只有在用 Pro 模式（支持更高输出分辨率）时才值得放大输入

### 5.4 ComfyUI 工作流与 RunningHub API 的关系

```
ComfyUI 工作流 JSON (本地/RunningHub 工作台)
         ↓ 导出为 API 格式
RunningHub 执行引擎
         ↓ 等价于
直接调用 RunningHub API 端点
```

三种执行方式的对比：
| 方式 | 灵活度 | 复杂度 | 适用 |
|------|--------|--------|------|
| ComfyUI GUI | ⭐⭐⭐⭐⭐ | ⭐⭐ | 工作流设计/调试 |
| ComfyUI API JSON | ⭐⭐⭐⭐ | ⭐⭐⭐ | 自动化/批量 |
| RunningHub 直接 API | ⭐⭐ | ⭐ | 快速测试/脚本集成 |

---

## 6. 工作流 JSON 文件清单

| 文件 | 描述 | 节点数 | 阶段 |
|------|------|--------|------|
| multi-stage-t2i-upscale-i2v-audio-pipeline.json | 四阶段完整管线 (T2I→Upscale→I2V+Audio→Edit) | 16 | 4 |
| ref2v-multi-model-comparison.json | 三模型 Ref2V 并行对比 | 7 | 3 分支 |

---

## 7. 实验成本汇总

| # | 实验 | 端点 | 成本 | 时间 |
|---|------|------|------|------|
| 62 | 参考图 T2I | rhart-image-n-pro/text-to-image | ¥0.03 | 25s |
| 63a | 尾帧 T2I | rhart-image-n-pro/text-to-image | ¥0.03 | 35s |
| 63 | Vidu Q3 Pro FLF | vidu/start-end-to-video-q3-pro | ¥0.44 | 65s |
| 64 | Wan 2.6 Flash Ref2V | alibaba/wan-2.6/reference-to-video-flash | ¥0.20 | 75s |
| 65 | Topaz Upscale | topazlabs/image-upscale-standard-v2 | ¥0.10 | 15s |
| 66 | Kling V3.0 Std I2V+Audio | kling-v3.0-std/image-to-video | ¥0.55 | 60s |
| **Total** | | | **¥1.35** | **275s** |

---

*PostGrad#17 完成。关键成果: 编写了2个生产级ComfyUI多阶段工作流JSON + 首测Vidu Q3 Pro和Wan 2.6 Flash Ref2V + 总结了5种工作流编排模式。*
