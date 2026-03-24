# PostGrad#15: Video Extend + Video Edit 深度对比

> 日期: 2026-03-24 16:03 UTC | 轮次: 59 | 总成本: ¥5.62

## 1. 本轮主题

深度测试两大视频后处理能力：
1. **Video Extend** — Veo 3.1 fast vs pro 视频扩展对比
2. **Video Edit** — Kling O3 Pro vs O3 Std 视频编辑对比

## 2. 实验设计

### 2.1 基础素材
- **基础图像**: 龙虾武士月夜竹林（rhart-image-n-pro, 2K 16:9, 30s/¥0.03）
- **基础视频**: Veo 3.1 fast I2V（8s/1280×720/24fps/AAC立体声/2.9MB, 130s/¥0.04）

### 2.2 实验矩阵
| # | 任务 | 端点 | 输入 | 输出 | 耗时 | 成本 |
|---|------|------|------|------|------|------|
| 1 | T2I 基准 | rhart-image-n-pro/text-to-image | prompt | 2K JPG | 45s | ¥0.03 |
| 2 | I2V 基准 | rhart-video-v3.1-fast/image-to-video | 图+prompt | 8s/720p/🔊 | 130s | ¥0.04 |
| 3 | Video Extend Fast | rhart-video-v3.1-fast-official/video-extend | 8s视频+prompt | 15s/720p/🔊 | 115s | ¥0.95 |
| 4 | Video Extend Pro | rhart-video-v3.1-pro-official/video-extend | 8s视频+prompt | 15s/720p/🔊 | 135s | ¥2.52 |
| 5 | O3 Pro Edit | kling-video-o3-pro/video-edit | 8s视频+prompt | 8s/1080p/🔊 | 175s | ¥1.20 |
| 6 | O3 Std Edit | kling-video-o3-std/video-edit | 8s视频+prompt | 8s/720p/🔊 | 300s | ¥0.88 |

## 3. Video Extend 深度分析

### 3.1 Veo 3.1 Video Extend 两个层级

两个端点实际底层都是 Google Veo 3.1 模型：
- `rhart-video-v3.1-fast-official/video-extend` → Google Veo 3.1 Fast
- `rhart-video-v3.1-pro-official/video-extend` → Google Veo 3.1 Pro

#### API 参数对比
```
两者参数完全相同：
- video: VIDEO (required, max 10MB)
- prompt: STRING (optional, max 8000 chars)
- resolution: LIST ['720p', '1080p'] (default: 720p)
- negativePrompt: STRING (optional)
- seed: INT (optional)
```

#### 关键发现

| 维度 | Fast Extend | Pro Extend |
|------|-------------|------------|
| 扩展量 | 8s → 15s (+7s) | 8s → 15s (+7s) |
| 分辨率 | 维持输入(720p) | 维持输入(720p) |
| 帧率 | 24fps | 24fps |
| 音频 | ✅ 自动生成/延续 | ✅ 自动生成/延续 |
| 文件大小 | 6.3MB | 5.9MB |
| 处理时间 | 115s | 135s |
| 成本 | **¥0.95** | **¥2.52** |
| 性价比 | **¥0.136/秒新内容** | ¥0.360/秒新内容 |

### 3.2 Video Extend 核心发现

1. **固定扩展量**: 8s→15s，添加 7s 新内容（与之前 PostGrad#5 测的 5.9s→12.9s 一致，约+7s）
2. **音频自动延续**: 扩展部分自动匹配生成音频，无需额外配置
3. **Pro 性价比极低**: 2.65x 价格但扩展量相同，除非质量差异明显否则不推荐
4. **最大输入限制 10MB**: 高分辨率/长视频需要先压缩
5. **支持 1080p**: 虽然本次测试用 720p，参数支持 1080p 输出
6. **Prompt 引导**: 可以用 prompt 描述扩展内容方向（最长 8000 字符！远超生成的 800 字符）

### 3.3 Video Extend 成本模型

```
完整视频生产链（以 15s 为例）：
方案A: 直接 I2V 8s + Extend Fast = ¥0.04 + ¥0.95 = ¥0.99 / 15s
方案B: 直接 I2V 8s + Extend Pro  = ¥0.04 + ¥2.52 = ¥2.56 / 15s
方案C: 直接生成 15s (如 Kling V3 Pro 10s=¥0.75, 需要扩展)

性价比: Extend Fast >> Extend Pro
长视频: 多次 Extend 可行但需注意累积误差
```

### 3.4 Veo 3.1 Video Extend vs PostGrad#5/10 对比

| 对比维度 | PostGrad#5 Extend | PostGrad#15 Fast | PostGrad#15 Pro |
|----------|-------------------|------------------|-----------------|
| 输入视频 | 5.9s | 8s | 8s |
| 输出视频 | 12.9s | 15s | 15s |
| 新增时长 | +7s | +7s | +7s |
| 输入分辨率 | 768p | 720p | 720p |
| 成本 | ¥0.95 | ¥0.95 | ¥2.52 |
| 音频 | ✅ 自动 | ✅ 自动 | ✅ 自动 |

**结论**: Video Extend 固定添加约 7s 新内容，与输入视频长度无关。Fast 成本稳定在 ¥0.95。

## 4. Video Edit 深度分析

### 4.1 Kling O3 Pro vs O3 Std Video Edit

#### API 参数（两者相同）
```
- prompt: STRING (required, max 5000 chars)
- videoUrl: VIDEO (required, max 50MB)
- imageUrls: IMAGE (optional, multiple, max 4 images, max 50MB)
- keepOriginalSound: BOOLEAN (required, default true)
```

#### ⭐ 重大发现: O3 Pro 自动升分辨率！

| 维度 | O3 Pro Edit | O3 Std Edit |
|------|-------------|-------------|
| 输入分辨率 | 1280×720 | 1280×720 |
| **输出分辨率** | **1920×1080 ⬆️** | 1280×720 (不变) |
| 输出大小 | 17.6MB | 15.7MB |
| 帧率 | 24fps | 24fps |
| 音频 | ✅ 保留 | ✅ 保留 |
| 处理时间 | **175s** (更快!) | 300s |
| 成本 | ¥1.20 | ¥0.88 |

### 4.2 O3 Pro Edit 特性深度

1. **自动超分辨率**: 720p → 1080p！Pro 层级内置了分辨率提升能力
   - 这意味着 O3 Pro Edit = 场景编辑 + 分辨率提升 的二合一
   - 之前在 PostGrad#5 的 O3 Std 测试中是 720p→720p，今天进一步确认
   
2. **Pro 竟然更快**: 175s vs 300s（Std 慢了 71%！）
   - 可能原因：Pro 使用更强算力资源，Std 排队更久
   - 或者 Pro 的模型架构本身更高效

3. **多图参考编辑**: `imageUrls` 支持最多 4 张参考图
   - 例如: "将角色的盔甲换成图1的样式" 
   - 这是比纯 prompt 编辑更强大的能力

4. **保留原始音频**: `keepOriginalSound=true` 可以保留源视频音频
   - 编辑后音频完整保留，无需重新生成

5. **最大 50MB 输入**: 比 Video Extend 的 10MB 限制宽松 5x

### 4.3 Kling Video Edit 全系列对比

| 端点 | 模型 | 分辨率变化 | 多图参考 | Mode | 成本 | 速度 |
|------|------|-----------|---------|------|------|------|
| O3 Pro Edit | kling-video-o3-pro | 720→1080 ⬆️ | ✅ 4图 | — | ¥1.20 | 175s |
| O3 Std Edit | kling-video-o3-std | 保持原分辨率 | ✅ 4图 | — | ¥0.88 | 300s |
| O1 Std Edit | kling-video-o1-std | 待测 | ✅ 多图 | std/pro | ¥0.55* | 待测 |

*O1 价格基于之前 PostGrad#5/8 测试推算

### 4.4 Video Edit vs 重新生成 I2V 决策树

```
需要修改视频内容？
├── 局部修改（换衣服/换道具）
│   └── → Video Edit + imageUrls（最精确）
├── 全局场景变换（日→夜、陆→水下）
│   └── → Video Edit (prompt only)
│       ├── 需要1080p? → O3 Pro (¥1.20, 含超分)
│       └── 720p即可? → O3 Std (¥0.88)
├── 完全重做
│   └── → 重新 I2V (可能更便宜)
└── 风格转换（写实→动漫）
    └── → rhart-video-g Edit (Grok, 720p/480p, 待测价格)
```

## 5. 完整视频生产管线设计

### 5.1 Extend + Edit 组合管线

```
[T2I ¥0.03] → [I2V 8s ¥0.04] → [Extend +7s ¥0.95] → [Edit 场景 ¥1.20]
   │                │                    │                    │
   30s             130s                 115s                175s
                                                            ↓
                                              15s/1080p/带音频最终视频
                                              总成本: ¥2.22 / 总耗时: ~450s
```

### 5.2 最低成本管线

```
[T2I ¥0.03] → [I2V rhart-s ¥0.02] → [Extend Fast ¥0.95]
                                           ↓
                                    15s/720p/带音频
                                    总成本: ¥1.00
```

### 5.3 最高质量管线

```
[T2I 2K ¥0.03] → [I2V Kling V3 Pro ¥0.75] → [Extend Pro ¥2.52] → [O3 Pro Edit ¥1.20]
                                                                         ↓
                                                              15s/1080p/带音频/编辑后
                                                              总成本: ¥4.50
```

## 6. ComfyUI 工作流映射分析

### 6.1 Video Extend 在 ComfyUI 中的实现

Veo 3.1 Video Extend 目前在 ComfyUI Partner Nodes 中的集成状态：

```
ComfyUI Partner Nodes (comfy_api_nodes):
├── Veo3.1 相关节点:
│   ├── Veo3TextToVideoNode (T2V)
│   ├── Veo3ImageToVideoNode (I2V)
│   └── ❌ VideoExtendNode — 暂未发现官方扩展节点
│
├── 要实现 Video Extend，需要:
│   ├── 方案A: 自定义节点（调用 Veo 3.1 Video Extend API）
│   ├── 方案B: RunningHub 代理节点
│   └── 方案C: 等待 Comfy.org 官方添加
```

### 6.2 Video Edit 在 ComfyUI 中的实现

```
ComfyUI Kling Partner Nodes:
├── KlingImageToVideoNode (I2V ✅)
├── KlingTextToVideoNode (T2V ✅)
├── KlingMotionControlNode (Motion ✅)
├── KlingCameraControlI2VNode (Camera ✅)
├── KlingOmniEditModel (O3 Ref2V ✅)
├── ❓ KlingVideoEditNode — 需要确认是否已添加
│
├── 第三方替代:
│   └── ComfyUI-KLingAI-API (社区维护, 可能支持 edit)
```

### 6.3 理想的 ComfyUI 工作流架构

```json
{
  "Stage 1: 关键帧生成": "Flux T2I → SaveImage",
  "Stage 2: 视频生成": "LoadImage → KlingI2V → VIDEO",
  "Stage 3: 视频扩展": "VIDEO → VeoExtend → ExtendedVIDEO",
  "Stage 4: 视频编辑": "ExtendedVIDEO → KlingEdit → FinalVIDEO",
  "Stage 5: 音频增强": "FinalVIDEO → V2A/TTS → MergeAV"
}
```

## 7. rhart-video-g (Grok Imagine) Video Edit 分析

### 7.1 Grok Video Edit 端点参数
```
Endpoint: rhart-video-g-official/edit-video
Engine: xai/grok-imagine-official
Parameters:
  - prompt: STRING (default: 吉卜力风格转换)
  - videoUrl: VIDEO (required)
  - resolution: LIST ['720p', '480p'] (default: 480p)
特点:
  - 最高仅 720p（vs Kling O3 Pro 1080p）
  - 无 imageUrls 参考（纯 prompt 驱动）
  - 无 keepOriginalSound 选项
  - 适合风格转换（默认 prompt 就是吉卜力风格）
```

### 7.2 Kling O1 Std Edit 特殊参数
```
Endpoint: kling-video-o1-std/edit-video
特殊参数:
  - mode: LIST ['std', 'pro'] — 同一端点支持两种模式！
  - imageUrls: IMAGE (optional, multiple)
  - keepOriginalSound: BOOLEAN
这意味着 O1 端点可以通过 mode 切换 std/pro 层级。
```

## 8. 关键洞察总结

### 8.1 Video Extend
1. Veo 3.1 Fast Extend 是最佳性价比选择（¥0.95 / +7s）
2. Pro Extend 贵 2.65x 但扩展量相同，不推荐常规使用
3. 扩展固定约 +7s，与输入时长无关
4. 自动延续/生成音频是杀手级特性
5. Prompt 引导扩展方向（8000 字符限制，非常充裕）

### 8.2 Video Edit
1. **Kling O3 Pro = 编辑 + 超分 二合一**（720p→1080p 自动升级）
2. O3 Pro 竟然比 Std 更快（175s vs 300s）
3. 多图参考编辑是独特能力（最多 4 张引导图）
4. 保留原始音频，编辑不破坏音轨
5. 50MB 输入限制，支持较长/高清视频
6. O1 端点支持 mode 切换（std/pro），灵活性更高

### 8.3 生产建议
- **15s 短视频**: T2I + I2V(8s) + Extend Fast = ¥1.00
- **15s 高清编辑短视频**: + O3 Pro Edit = ¥2.22
- **长视频**: 多次 Extend（注意累积质量损失）
- **内容修改**: Video Edit 比重新生成更快更可控

## 9. 模型选择策略更新

### Video Extend 选择
```
需要延长视频？
├── 性价比优先 → Veo 3.1 Fast Extend (¥0.95/+7s)
├── 最高质量 → Veo 3.1 Pro Extend (¥2.52/+7s)
└── 需要 >7s → 多次 Extend 串联
```

### Video Edit 选择
```
需要编辑视频？
├── 场景变换 + 超分 → Kling O3 Pro (¥1.20, 自动1080p)
├── 场景变换（保持分辨率）→ Kling O3 Std (¥0.88)
├── 参考图引导编辑 → Kling O3 Pro/Std + imageUrls
├── 风格转换（动漫等）→ rhart-video-g (Grok, 720p, 价格待测)
└── O1 级编辑 → kling-video-o1-std mode=std/pro (¥0.55)
```

## 10. 与之前 PostGrad Session 的知识关联

- **PostGrad#5**: 首次测试 Veo 3.1 fast Extend（5.9→12.9s）和 O3 Std Edit
- **PostGrad#8**: O3 Std Video Edit 日→夜转换
- **PostGrad#10**: FLF 三模型对比 + Extend 首测
- **PostGrad#11**: Budget 管线设计（Kling V2A 源码分析）
- **PostGrad#13**: Kling V3.0 I2V+Audio 首测
- **本轮**: Video Extend Fast vs Pro 首次直接对比 + O3 Pro Edit 首测（发现超分能力）
