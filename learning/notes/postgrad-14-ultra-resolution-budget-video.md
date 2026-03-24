# PostGrad#14: Ultra 8K 图像生成 + Budget 视频管线新端点

> 日期: 2026-03-24 14:04 UTC | 轮次: 58 | 实验: #60-#64

## 主题概述

本轮探索三个方向：
1. **Ultra 分辨率图像生成** — rhart-image-n-pro-official Ultra 模式（4K/8K）
2. **Seedance V1 Lite Ref2V** — 低成本参考生视频
3. **Hailuo 02 Standard FLF** — 首尾帧功能确认

---

## 1. Ultra 分辨率图像生成

### 1.1 端点发现

RunningHub 有两个 Ultra 端点，此前未测试：

| 端点 | 任务 | 分辨率选项 | 价格 |
|------|------|-----------|------|
| `rhart-image-n-pro-official/text-to-image-ultra` | T2I | **4K / 8K** | ¥0.16 |
| `rhart-image-n-pro-official/edit-ultra` | I2I | **4K / 8K** | ¥0.14 |

对比普通端点：
| 端点 | 分辨率选项 | 价格 |
|------|-----------|------|
| `rhart-image-n-pro/text-to-image` | 1K / 2K | ¥0.03 |
| `rhart-image-n-pro/edit` | 1K / 2K | ¥0.03 |

### 1.2 实验 #60: Ultra 8K T2I

**参数：**
- Prompt: 龙虾武士+日式庭院+85mm浅景深
- resolution: 8k
- aspectRatio: 16:9

**结果：**
```
分辨率: 10965 × 6120 = 67.1 MP (百万像素)
文件大小: 89.5 MB (PNG)
耗时: 105s
费用: ¥0.16
```

**关键发现：**
- **真正的 8K+**：10965×6120 远超标准 8K (7680×4320)，约等于 11K 分辨率
- **67.1 MP** 是普通 2K 模式 (4.2 MP) 的 **16 倍像素量**
- 价格仅为 ¥0.16，是 2K 的 5.3 倍，性价比极高
- 输出为 PNG 格式（无损），适合印刷级应用
- 生成时间约 105s，比 2K 慢约 2.5 倍

### 1.3 实验 #62: Ultra 4K Edit

**参数：**
- 输入: 1024×1024 龙虾厨师参考图
- Prompt: 将背景变为中世纪城堡厨房，加金冠
- resolution: 4k
- aspectRatio: 16:9

**结果：**
```
分辨率: 5483 × 3060 = 16.8 MP
文件大小: 19.7 MB (PNG)
耗时: 85s
费用: ¥0.14
```

**关键发现：**
- Ultra Edit 接受低分辨率输入（1024×1024），输出高达 5483×3060
- 相当于 **5.3 倍超分 + 场景变换** 一步完成
- 支持最多 **10 张输入图片**（multi-image 编辑）
- Prompt 限制 4000 字符（比普通版更长）
- 角色保持能力良好，同时完成场景重建

### 1.4 实验 #64: Pro 2K 基线对比

**同 prompt 对比：**
```
Pro 2K:    2752 × 1536 = 4.2 MP,   3.4MB,  40s, ¥0.03
Ultra 8K: 10965 × 6120 = 67.1 MP, 89.5MB, 105s, ¥0.16
```

| 维度 | Pro 2K | Ultra 8K | 倍率 |
|------|--------|----------|------|
| 宽度 | 2752 | 10965 | 4.0x |
| 高度 | 1536 | 6120 | 4.0x |
| 像素 | 4.2MP | 67.1MP | 16.0x |
| 文件 | 3.4MB | 89.5MB | 26.3x |
| 耗时 | 40s | 105s | 2.6x |
| 费用 | ¥0.03 | ¥0.16 | 5.3x |
| 每MP成本 | ¥0.007 | ¥0.0024 | 0.34x (Ultra更便宜) |

**结论：Ultra 按像素计算反而更便宜！每百万像素成本仅为 Pro 的 34%。**

### 1.5 Ultra 模式的 ComfyUI 工作流映射

Ultra 对应 ComfyUI 的 **两种管线范式**：

**范式 A：直接超高分辨率生成（Ultra T2I）**
- 等效于: DiT 模型原生高分辨率推理 + 多步精炼
- 对标 ComfyUI: Flux dev 4K + Tile ControlNet 放大到 8K
- 优势: 一步到位，无拼接痕迹

**范式 B：超分+编辑一体（Ultra Edit）**
- 等效于: 输入图 → VAEEncode → DiT 编辑 → 超分输出
- 对标 ComfyUI: ICEdit + Topaz 放大管线
- 优势: 编辑和超分同步完成，无需两个步骤

**ComfyUI Partner Node 映射（推测）：**
```
RHArtUltraTextToImage:
  - prompt: STRING (max 4000)
  - resolution: ["4k", "8k"]
  - aspectRatio: ["1:1", "3:2", ..., "21:9"]
  → IMAGE (超高分辨率输出)

RHArtUltraEdit:
  - images: IMAGE[] (max 10)
  - prompt: STRING (max 4000)
  - resolution: ["4k", "8k"]
  - aspectRatio: 同上
  → IMAGE (超高分辨率输出)
```

### 1.6 Ultra 模式使用场景

| 场景 | 推荐 | 原因 |
|------|------|------|
| 社交媒体/网页 | Pro 2K | 分辨率足够，费用低 |
| 电商详情页 | Ultra 4K | 需要 zoom-in 看细节 |
| **印刷/海报** | **Ultra 8K** | **300DPI@36×20英寸** |
| **壁纸/大屏展示** | **Ultra 8K** | **原生超高分辨率** |
| 视频素材 | Pro 2K | 视频通常 1080p/4K |
| 3D 纹理 | Ultra 4K | 高分辨率纹理贴图 |
| 批量生产 | Pro 2K | 成本×数量考量 |

---

## 2. Seedance V1 Lite Ref2V

### 2.1 端点规格

```
端点: seedance-v1-lite/reference-to-video
参数:
  - imageUrls: IMAGE[] (max 4, 必选)
  - prompt: STRING (max 5000, 必选)
  - duration: 2-12s (选择列表)
  - resolution: 720p / 480p
  - aspectRatio: 16:9/9:16/4:3/3:4/21:9/1:1
  - cameraFixed: true/false
```

### 2.2 实验 #61: Seedance V1 Lite Ref2V

**参数：**
- 输入: 1024×1024 龙虾厨师参考图
- Prompt: 厨师翻煎饼动作
- duration: 5s, resolution: 720p, aspectRatio: 16:9

**结果：**
```
分辨率: 1248 × 704
帧率: 24fps
时长: 5.0s
耗时: 60s
费用: ¥0.15
音频: 无
```

### 2.3 Seedance Lite vs Pro Ref2V 对比

| 维度 | V1 Lite | V1.5 Pro |
|------|---------|----------|
| 分辨率 | 1248×704 (720p) | 1280×720 (720p) |
| 最大分辨率 | 720p | 1080p |
| 最长时长 | 12s | 10s |
| 参考图数量 | 4 | 4 |
| cameraFixed | ✅ | ✅ |
| 音频 | ❌ | ❌ |
| 帧率 | 24fps | 24fps |
| 费用 | **¥0.15** | ¥0.30 |
| 速度 | ~60s | ~125s |
| 480p选项 | ✅ | ❌ |
| Prompt长度 | 5000 | 5000 |

**Lite 优势：**
- **半价**（¥0.15 vs ¥0.30）
- **更快**（60s vs 125s）
- 支持更长视频（12s vs 10s）
- 有 480p 低分辨率选项（更低成本？）

**Lite 劣势：**
- 分辨率略低（1248 vs 1280，微差）
- 无 1080p 选项
- 可能运动质量/角色一致性不如 Pro（需更多对比）

### 2.4 性价比排名更新 (Ref2V)

| 模型 | 费用 | 时长 | 分辨率 | 速度 | ¥/秒 |
|------|------|------|--------|------|------|
| **Seedance Lite** | **¥0.15** | 5s | 1248×704 | 60s | **¥0.030** |
| Seedance Pro | ¥0.30 | 5s | 1280×720 | 125s | ¥0.060 |
| Kling O3 Std | ¥0.50 | 5s | 1280×720 | ~120s | ¥0.100 |
| Wan 2.6 | ¥0.65 | 5s | 1280×720 | ~180s | ¥0.130 |
| rhart V3.1 Pro | ¥1.36 | 8s | 1280×720 | ~300s | ¥0.170 |

**Seedance Lite 是目前最低成本的 Ref2V 方案。**

---

## 3. Hailuo 02 Standard FLF

### 3.1 关键发现：隐藏的 FLF 能力

`minimax/hailuo-02/standard` 端点包含两个可选的 IMAGE 参数：
- `firstImageUrl` — 首帧图片
- `lastImageUrl` — 尾帧图片

这使它成为一个 **隐藏的首尾帧生视频端点**！

### 3.2 实验 #63: Hailuo 02 Standard FLF

**参数：**
- firstImageUrl: 龙虾厨师 1024×1024
- lastImageUrl: 龙虾厨师蛋糕场景 1792×1024
- Prompt: 厨师走过厨房做蛋糕
- duration: 6s

**结果：**
```
分辨率: 768 × 768
帧率: 24fps
时长: 5.9s
耗时: 80s
费用: ¥0.25
音频: 无
```

### 3.3 Hailuo 02 FLF 分析

**注意事项：**
- 当输入首帧为正方形（1024×1024）时，输出也是正方形（768×768）
- 这比 Hailuo 02 I2V standard（1376×768）分辨率更低
- 可能因为首帧决定了宽高比，768×768 是首帧缩放后的结果
- 费用 ¥0.25 与 I2V standard 相同

### 3.4 FLF 端点完整汇总（更新）

| 端点 | 费用 | 分辨率 | 时长 | 音频 | 备注 |
|------|------|--------|------|------|------|
| Veo 3.1 fast FLF | ¥0.04 | 1280×720 | 8s | ✅ | ⭐极致性价比 |
| **Seedance Lite Ref2V** | **¥0.15** | 1248×704 | 2-12s | ❌ | 多图参考 |
| Hailuo 02 Std FLF | ¥0.25 | ~768×768 | 5.9s | ❌ | 隐藏能力 |
| Hailuo 02 Std I2V | ¥0.25 | 1376×768 | 5.9s | ❌ | 单首帧 |
| Seedance Pro FLF | ¥0.30 | 1280×720 | 5s | ❌ | 高质量 |
| Kling O1 FLF | ¥0.55 | 1280×720 | 5s | ❌ | @Image引用 |
| Vidu Q3 Pro FLF | ¥0.88 | 1280×720 | 8s | ✅ | 含音频 |
| rhart V3.1 fast FLF | ¥0.04 | 1280×720 | 8s | ✅ | Veo同底层 |

---

## 4. ComfyUI 工作流设计模式

### 4.1 Ultra 图像管线模式

```
[Ultra T2I 管线]
CLIPTextEncode → RHArtUltraT2I(8K) → SaveImage
                                    → ImageScale(to 1080p) → I2V(Kling/Seedance)

适用场景: 需要超高分辨率输出 + 视频素材
关键: 8K 原图用于印刷，缩放版用于视频
```

```
[Ultra Edit 管线]
LoadImage(多张) → RHArtUltraEdit(4K/8K) → SaveImage
                                        → FaceDetailer → 最终输出

适用场景: 多图合成 + 超分 + 场景变换一步完成
优势: 10 张输入图同时处理
```

### 4.2 Budget 视频管线模式（更新）

最低成本视频生成方案：
```
Pro T2I(¥0.03) → Veo 3.1 fast I2V(¥0.04) → MiniMax Music(¥0.14) → FFmpeg合成
总计: ¥0.21 / 8s 含音频
```

最低成本 FLF 视频：
```
Pro T2I首帧(¥0.03) + Pro T2I尾帧(¥0.03) → Veo 3.1 fast FLF(¥0.04) → 输出含音频
总计: ¥0.10 / 8s 含音频
```

最低成本 Ref2V：
```
Pro T2I角色图(¥0.03) → Seedance Lite Ref2V(¥0.15) → MiniMax Music(¥0.14) → 合成
总计: ¥0.32 / 5s 含音频
```

### 4.3 分辨率-成本决策树

```
需要超高分辨率（印刷/展示）？
├── 是 → Ultra 模式
│   ├── 需要编辑？ → Ultra Edit (¥0.14, 4K)
│   └── 纯生成？ → Ultra T2I (¥0.16, 8K)
└── 否 → Pro 模式
    ├── 用于视频源？ → Pro 1K (¥0.03, 足够)
    ├── 用于网页？ → Pro 2K (¥0.03)
    └── 用于详情页？ → Pro 2K 或 Ultra 4K
```

---

## 5. 实验总结

| # | 实验 | 端点 | 分辨率 | 耗时 | 费用 |
|---|------|------|--------|------|------|
| 60 | Ultra 8K T2I | rhart-official/t2i-ultra | 10965×6120 (67MP) | 105s | ¥0.16 |
| 61 | Seedance Lite Ref2V | seedance-v1-lite/ref2v | 1248×704 24fps 5s | 60s | ¥0.15 |
| 62 | Ultra 4K Edit | rhart-official/edit-ultra | 5483×3060 (17MP) | 85s | ¥0.14 |
| 63 | Hailuo 02 Std FLF | minimax/hailuo-02/standard | 768×768 24fps 5.9s | 80s | ¥0.25 |
| 64 | Pro 2K T2I (基线) | rhart-image-n-pro/t2i | 2752×1536 (4MP) | 40s | ¥0.03 |
| **总计** | | | | | **¥0.61** |

### 关键收获

1. **Ultra 8K 是真正的超高分辨率** — 67MP, 印刷级质量, 按像素计算比 2K 更便宜
2. **Ultra Edit 支持 10 图输入** — 最强大的多图编辑端点
3. **Seedance Lite 是最便宜的 Ref2V** — ¥0.15/5s, 半价版 Pro
4. **Hailuo 02 Standard 有隐藏 FLF** — firstImageUrl + lastImageUrl 双参数
5. **Veo 3.1 fast 仍是 FLF 性价比之王** — ¥0.04/8s 含音频

### 模型选择策略更新

**T2I 选择（按分辨率需求）：**
- 视频素材/社交媒体 → Pro 1K/2K (¥0.03)
- 电商/网页详情 → Ultra 4K (¥0.14-0.16)
- 印刷/海报/大屏 → Ultra 8K (¥0.16)

**Ref2V 选择（按预算）：**
- 极致低成本 → Seedance Lite (¥0.15)
- 标准质量 → Seedance Pro (¥0.30)
- 最强角色保持 → Kling O3 (¥0.50)

---

## 6. 与 ComfyUI 本地管线的对比

### Ultra 8K vs 本地 Flux + Topaz 放大

| 维度 | Ultra 8K API | Flux dev 2K → Topaz 4x |
|------|-------------|------------------------|
| 最终分辨率 | 10965×6120 | ~8192×4608 |
| 步骤 | 1步 | 2步(生成+放大) |
| 费用 | ¥0.16 | ¥0.03+¥0.10=¥0.13 |
| 时间 | 105s | ~60+15=75s |
| 质量 | 原生生成 | 可能有放大伪影 |
| 控制力 | 仅 prompt | ControlNet+LoRA+区域 |

**结论：** Ultra 更简单但控制力弱；本地管线更灵活但流程复杂。对于需要精确控制的场景选本地，对于快速高分辨率输出选 Ultra。

### Seedance Lite vs 本地 AnimateDiff Ref2V

| 维度 | Seedance Lite API | AnimateDiff + IP-Adapter |
|------|-------------------|-------------------------|
| 分辨率 | 1248×704 | 512×512 (SD1.5 限制) |
| 费用 | ¥0.15 | 免费(需GPU) |
| 角色一致性 | 高 | 中(取决于IP-Adapter weight) |
| 运动质量 | 高 | 中(16帧限制) |
| 控制力 | prompt+cameraFixed | MotionLoRA+ControlNet+FreeNoise |
| GPU 需求 | 无 | 8GB+ |

---

*本轮探索了超高分辨率和低成本视频的两个极端，丰富了管线选择矩阵。下一步可探索 Veo 3.1 pro video-extend（视频续写）和 Kling O3 Pro video-edit（高级视频编辑）。*
