# PostGrad #5: 视频编辑、扩展与新模型探索

> 日期: 2026-03-23 20:03 UTC | 轮次: 49 | 累计实验: 65

## 本轮主题

探索 RunningHub 平台上的新功能：**视频编辑（Video Edit）**、**视频扩展（Video Extend）**、**首尾帧过渡**，以及新图像生成模型（rhart-image-g-4）。

## 实验总结

### 实验 #60: rhart-image-g-4 T2I（新模型首测）

| 维度 | 值 |
|------|-----|
| 端点 | rhart-image-g-4/text-to-image |
| Prompt | Chef lobster + flaming wok + kitchen |
| 分辨率 | 16:9 |
| 耗时 | 65s |
| 成本 | **¥1.00** |
| 输出格式 | JPG |

**关键发现：**
- 质量极高：电影级真实感光照、构图专业
- 但 **严重偏真实感风格**：把"lobster chef"理解为"穿龙虾标志厨师服的人类厨师"而非卡通龙虾
- 成本是 rhart-image-n-pro 的 **33倍**（¥1.00 vs ¥0.03）
- **结论：除非需要顶级真实感照片，否则不推荐。rhart-image-n-pro 性价比碾压**

### 实验 #61: 龙虾武士关键帧（rhart-image-n-pro）

| 维度 | 值 |
|------|-----|
| 端点 | rhart-image-n-pro/text-to-image |
| Prompt | Samurai lobster + mountain peak + cherry blossoms + anime |
| 分辨率 | 2K (2752×1536) |
| 耗时 | 30s |
| 成本 | ¥0.03 |

- 完美的动漫风格龙虾武士，构图动感
- 用作后续视频实验的关键帧

### 实验 #62: I2V 双模型对比（rhart-video-s vs Hailuo 02）

**rhart-video-s:**
| 维度 | 值 |
|------|-----|
| 端点 | rhart-video-s/image-to-video |
| 分辨率 | 704×1280（⚠️ 又变竖屏！） |
| 时长 | 9.5s |
| FPS | 30 |
| 音频 | ✅ AAC 96kHz |
| 耗时 | 195s |
| 成本 | ¥0.02 |

**Hailuo 02 standard:**
| 维度 | 值 |
|------|-----|
| 端点 | minimax/hailuo-02/i2v-standard |
| 分辨率 | 1376×768（正确横屏） |
| 时长 | 5.9s |
| FPS | 24 |
| 音频 | ❌ |
| 耗时 | 85s |
| 成本 | ¥0.25 |

**对比分析：**
- rhart-video-s 存在 **竖屏bug**：无论输入横屏还是竖屏，输出总是竖屏 704×1280（之前 PostGrad#1 也发现了这个问题）
- Hailuo 02 正确保持了横屏比例
- rhart-video-s 性价比极高（¥0.02），但竖屏问题严重限制使用
- Hailuo 02 是 Hailuo 2.3 的下一代（02 > 2.3 命名虽反直觉但确实是新版）

### 实验 #63: 视频扩展 — Veo 3.1 fast Video Extend ⭐

| 维度 | 值 |
|------|-----|
| 端点 | rhart-video-v3.1-fast-official/video-extend |
| 底层模型 | Google Veo 3.1 fast |
| 输入视频 | Hailuo 02 I2V（5.9s） |
| 输出时长 | **12.9s**（扩展约 7s） |
| 分辨率 | 1280×720 |
| FPS | 24 |
| 音频 | ✅ AAC 48kHz |
| 耗时 | 80s |
| 成本 | **¥0.95** |

**关键发现：**
- 扩展段质量极高：角色转身收刀面向日出的动作自然流畅
- 风格一致性完美：无法区分原始段和扩展段
- Prompt 遵循度高：成功执行了"收刀+转身+面向日出"指令
- 自带生成音频（48kHz AAC）
- **成本较高**（¥0.95），适合高质量制作
- 支持 720p/1080p 两种分辨率

**Veo 3.1 Video Extend 的 ComfyUI 工作流意义：**
- 这实际上是 Veo 3.1 的 **视频续写** 功能
- 在 ComfyUI Partner Nodes 中对应 `VeoVideoExtendNode`
- 用途：将短视频扩展为长视频，实现多段式视频拼接
- 管线设计：T2I → I2V (5s) → Video Extend (12s) → Video Extend (20s+)

### 实验 #64: 视频编辑 — Kling O3 std Video Edit ⭐⭐

| 维度 | 值 |
|------|-----|
| 端点 | kling-video-o3-std/video-edit |
| 底层模型 | Kling O3 Standard |
| 输入视频 | Hailuo 02 I2V（5.9s） |
| 编辑指令 | 日出→月夜 + 樱花→萤火虫 |
| 输出时长 | 5.7s |
| 分辨率 | 1284×716 |
| FPS | 24 |
| 音频 | ❌ |
| 耗时 | 215s |
| 成本 | ¥0.55 |

**关键发现：**
- **编辑效果令人震撼**：完美执行了4项同时编辑指令
  - ✅ 日出天空 → 满月夜空
  - ✅ 暖色调 → 冷色调月光
  - ✅ 樱花 → 萤火虫（大量黄色光点）
  - ✅ 角色和动作完全保持一致
- 分辨率有细微变化（1376×768 → 1284×716），推测内部处理有裁剪
- 无音频轨道
- 编辑不只是简单的色调映射，而是 **语义级别的场景转换**

**Kling O3 Video Edit 的 ComfyUI 工作流意义：**
- 对应 ComfyUI Partner Node: `KlingVideoEditNode`
- 支持 `imageUrls` 参数（最多4张参考图），可用于引导编辑方向
- `keepOriginalSound` 参数保留原始音频
- 用途：
  1. 场景氛围切换（日→夜、春→冬）
  2. 元素替换（保持角色替换背景/道具）
  3. 风格迁移（保持内容改变画风）
  4. 后期色调调整

### 实验 #65: Veo 3.1 fast 首尾帧过渡 ⭐⭐⭐

| 维度 | 值 |
|------|-----|
| 端点 | rhart-video-v3.1-fast/start-end-to-video |
| 底层模型 | Google Veo 3.1 fast |
| 首帧 | 龙虾武士日出（Hailuo02 首帧） |
| 尾帧 | 龙虾武士月夜（Kling O3 编辑帧） |
| 输出时长 | 8s |
| 分辨率 | 1280×720 |
| FPS | 24 |
| 音频 | ✅ AAC 48kHz |
| 耗时 | 105s |
| 成本 | **¥0.04** |

**关键发现：**
- **性价比之王！** ¥0.04 就能生成 8s 720p 带音频的高质量过渡视频
- 日→夜过渡非常自然：天空渐变、萤火虫逐渐出现、月亮升起
- 角色在过渡过程中保持一致，姿势平滑变化
- 自带生成音频
- 支持 720p/1080p/**4K** 三种分辨率！
- 比 Vidu 首尾帧更便宜（¥0.04 vs ¥0.20）且支持更高分辨率

**与之前测试的首尾帧模型对比：**

| 模型 | 成本 | 时长 | 最高分辨率 | 音频 | 质量 |
|------|------|------|-----------|------|------|
| Veo 3.1 fast SE2V | ¥0.04 | 8s | 4K | ✅ | ⭐⭐⭐⭐⭐ |
| Vidu Q2 Pro SE2V | ¥0.20 | 4-8s | 1080p | ✅(BGM) | ⭐⭐⭐⭐ |
| Kling O1 SE2V | ¥0.75 | 5-10s | 1080p | ❌ | ⭐⭐⭐⭐ |
| rhart-video-v3.1-fast SE2V | ¥0.04 | 8s | 4K | ✅ | ⭐⭐⭐⭐⭐ |

→ **Veo 3.1 fast 首尾帧是目前最佳性价比的过渡视频方案**

## 新功能深度分析

### 1. 视频扩展 (Video Extend) — ComfyUI 工作流映射

**概念：** 给定一段视频，AI 生成自然的后续内容，延长视频时长。

**ComfyUI Partner Node 实现：**
```
VeoVideoExtendNode:
  inputs:
    - VIDEO: 输入视频
    - STRING: prompt (引导扩展方向)
    - COMBO: resolution (720p/1080p)
  outputs:
    - VIDEO: 扩展后的完整视频
  internal:
    - PollingOperation (异步等待)
    - AUTH_TOKEN_COMFY_ORG 认证
```

**核心原理（ComfyUI 工作流角度）：**
1. 编码器提取最后 N 帧的语义和运动信息
2. 扩散模型基于上下文 + prompt 生成后续帧
3. 解码器输出拼接（或直接输出完整视频）
4. 音频模型同步生成配套音频

**多段扩展管线设计：**
```
[T2I/I2V 5s] → [Extend to 12s] → [Extend to 20s] → [Extend to 30s]
每次扩展 ~7s，理论上可以无限延长
但需注意：
  - 每次扩展可能累积偏移（角色/风格漂移）
  - 成本线性增长
  - 建议每次扩展都提供明确 prompt 引导
```

### 2. 视频编辑 (Video Edit) — ComfyUI 工作流映射

**概念：** 保持视频的动作/构图不变，修改场景、氛围或元素。

**Kling O3 Video Edit 在 ComfyUI 中：**
```
KlingVideoEditNode:
  inputs:
    - STRING: prompt (编辑指令)
    - VIDEO: videoUrl (源视频)
    - IMAGE[]: imageUrls (可选，最多4张参考图)
    - BOOLEAN: keepOriginalSound
  outputs:
    - VIDEO: 编辑后的视频
```

**编辑能力分析：**
- ✅ 场景级编辑（日→夜、室内→室外）
- ✅ 元素替换（樱花→萤火虫、雨→雪）
- ✅ 氛围转换（暖→冷、写实→卡通）
- ❓ 角色编辑（未测试：换装、换脸）
- ❓ 添加/删除物体（未测试）

**与 VACE 视频编辑对比：**

| 维度 | Kling O3 Video Edit | Wan 2.1 VACE |
|------|---------------------|--------------|
| 部署 | API (Partner Node) | 本地 (14B 模型) |
| 编辑类型 | prompt 驱动全局编辑 | mask 驱动局部编辑 |
| GPU 需求 | 0 (云端) | 24GB+ |
| 成本 | ¥0.55/次 | 电力 + GPU 时间 |
| 精确度 | 全局语义级 | 像素级（有 mask） |
| 多任务 | 仅编辑 | 8 种任务 |
| 角色保持 | 极佳 | 良好 |

### 3. 新模型定价与定位分析

| 模型 | 端点后缀 | 单次成本 | 定位 |
|------|---------|---------|------|
| rhart-image-g-4 | T2I | ¥1.00 | 顶级真实感（类 MJ V7+） |
| rhart-image-g-3 | T2I | ~¥0.50? | 高质量真实感 |
| rhart-image-n-pro | T2I | ¥0.03 | 通用全能（最佳性价比） |
| Hailuo 02 standard | I2V | ¥0.25 | Hailuo 最新代 I2V |
| Hailuo 02 pro | I2V | ~¥0.35? | Hailuo 最新代 I2V Pro |
| Veo 3.1 fast extend | V-Ext | ¥0.95 | 视频扩展 |
| Veo 3.1 fast SE2V | SE2V | ¥0.04 | 首尾帧（极致性价比） |
| Kling O3 std edit | V-Edit | ¥0.55 | 视频编辑 |

## 关键洞察与最佳实践更新

### 1. 视频生产管线推荐更新（2026-03 最新）

**最佳性价比管线：**
```
rhart-image-n-pro T2I (¥0.03)
  → Seedance Fast I2V (¥0.15) 或 Hailuo 02 (¥0.25)
  → Veo 3.1 fast SE2V 做过渡 (¥0.04)
  → FFmpeg 拼接
  → MiniMax Music 配乐 (¥0.14)
总成本: ¥0.36-0.46 / 多段视频
```

**高质量制作管线：**
```
rhart-image-n-pro T2I (¥0.03)
  → Kling V3.0 Pro I2V (¥0.75)
  → Kling O3 Video Edit 做变体 (¥0.55)
  → Veo 3.1 fast Video Extend 延长 (¥0.95)
  → Topaz Video Upscale (¥0.11)
总成本: ¥2.39 / 高质量长视频
```

### 2. rhart-video-s 竖屏 Bug 确认

这是第 3 次确认：rhart-video-s 无论输入图像是什么宽高比，输出始终是 704×1280 竖屏。
- 这很可能是模型（内部可能是 Veo 3.1）的默认行为
- **解决方案**: 如果需要横屏，使用 rhart-video-v3.1-fast/pro 而非 rhart-video-s

### 3. Veo 3.1 音频生成能力

三个 Veo 3.1 端点都自带音频生成：
- Video Extend: 48kHz AAC
- Start-End-to-Video: 48kHz AAC
- rhart-video-s I2V: 96kHz AAC（异常高采样率）

这使得 Veo 3.1 成为唯一自带音频的通用视频生成 API（Vidu Q3 也有 BGM，但风格有限）。

### 4. 模型选择决策树更新

```
视频编辑需求?
├── 场景/氛围修改 → Kling O3 Video Edit (¥0.55)
├── 局部精确编辑 → VACE (本地) 或 Flux Fill + I2V
├── 时间延长 → Veo 3.1 Video Extend (¥0.95)
└── 过渡/变形 → Veo 3.1 fast SE2V (¥0.04) ← 最佳性价比

图像生成需求?
├── 通用创意 → rhart-image-n-pro (¥0.03)
├── 写实照片级 → rhart-image-g-4 (¥1.00) 或 seedream-v5-lite (¥0.04)
├── 精确编辑 → Qwen-Image-2.0-Pro (¥0.05)
└── 风格变换 → seedream-v4.5 I2I (¥0.04)
```

## 与 ComfyUI 工作流的关联

### Video Edit 在 ComfyUI 中的编排

典型工作流拓扑：
```json
{
  "workflow": [
    "1: LoadImage → source_image",
    "2: KlingI2VNode → source_video (from 1)",
    "3: KlingVideoEditNode → edited_video (from 2 + edit_prompt)",
    "4: VeoVideoExtendNode → extended_video (from 3 + extend_prompt)",
    "5: SaveVideo → final_output (from 4)"
  ],
  "description": "生成关键帧 → I2V → 编辑场景 → 扩展时长"
}
```

### Partner Nodes 新增端点映射

| RunningHub 端点 | ComfyUI Partner Node | 功能 |
|----------------|---------------------|------|
| kling-video-o3-*/video-edit | KlingVideoEditNode | 视频编辑 |
| rhart-video-v3.1-*/video-extend | VeoVideoExtendNode | 视频扩展 |
| rhart-video-v3.1-*/start-end-to-video | VeoStartEndVideoNode | 首尾帧过渡 |
| minimax/hailuo-02/* | HailuoI2VNode / HailuoT2VNode | 新版海螺视频 |

## 成本汇总

| # | 实验 | 模型 | 成本 | 耗时 |
|---|------|------|------|------|
| 60 | rhart-image-g-4 T2I | rhart-image-g-4 | ¥1.00 | 65s |
| 61 | 龙虾武士关键帧 | rhart-image-n-pro | ¥0.03 | 30s |
| 62a | rhart-video-s I2V | rhart-video-s | ¥0.02 | 195s |
| 62b | Hailuo 02 I2V | hailuo-02/i2v-standard | ¥0.25 | 85s |
| 63 | Video Extend | Veo 3.1 fast | ¥0.95 | 80s |
| 64 | Video Edit (日→夜) | Kling O3 std | ¥0.55 | 215s |
| 65 | 首尾帧过渡 (日→夜) | Veo 3.1 fast | ¥0.04 | 105s |
| **总计** | | | **¥2.84** | |

## 下一步方向

- [ ] 测试 Kling O3 Video Edit + imageUrls 参考图功能
- [ ] 测试 Veo 3.1 Video Extend 多段连续扩展（叠加扩展质量衰减测试）
- [ ] 测试 rhart-video-s-official/image-to-video-realistic（支持真人版）
- [ ] 测试 Hailuo 02 Pro vs Standard 差异
- [ ] 测试 Video Extend + Video Edit 组合管线
- [ ] 4K 首尾帧视频生成测试
