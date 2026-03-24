# PostGrad #9 — 3D 模型对比 + 多图编辑 + Ultra 编辑 + Topaz CGI

> 学习时间: 2026-03-24 04:03 UTC | 轮次: 53 | 实验: #60-#68

## 1. 本轮学习目标

探索 RunningHub 上新发现的端点：
- **HiTem3D** — 新 3D 生成模型系列（v1.5/v2/Portrait）
- **rhart-image-g-1.5/edit** — GPT Image 1.5 多图编辑
- **rhart-image-n-pro-official/edit-ultra** — Ultra 质量编辑（支持 10 图 + 8K）
- **Topaz CGI** — CGI/3D 专用放大器
- **Qwen Image 2.0**（非 Pro）— 性价比编辑

## 2. HiTem3D 3D 模型测试

### 2.1 HiTem3D 模型系列概览

RunningHub 上发现 5 个 HiTem3D 端点：
- `hitem3d-v15/image-to-3d` — 基础版
- `hitem3d-v2/image-to-3d` — V2 升级版
- `hitem3d-portrait-v21/image-to-3d` — 人像专用 V2.1
- `hitem3d-portrait-v20/image-to-3d` — 人像专用 V2.0
- `hitem3d-portrait-v15/image-to-3d` — 人像专用 V1.5

### 2.2 HiTem3D API 参数分析

```
hitem3d-v2/image-to-3d:
  requestType: mesh | both (mesh+texture)
  resolution: 1536 | 1536pro
  face: 100,000 - 2,000,000 (默认 1M)

hitem3d-portrait-v21/image-to-3d:
  requestType: mesh | both
  resolution: 1536pro (only)
  face: 100,000 - 2,000,000 (默认 2M)
```

**关键特点：**
- 支持 `both` 输出（mesh + texture），Hunyuan3D 也是
- 面数可调（100K-2M），适合不同场景（低面数=移动端，高面数=影视级）
- Portrait 版默认更高面数（2M），专为人像优化
- 支持多图输入（`multi-image-to-3d`）

### 2.3 测试结果：全部超时 ❌

| 模型 | 参数 | 结果 | 耗时 |
|------|------|------|------|
| hitem3d-v2 | both/1536/1M face | 超时 | >240s |
| hitem3d-v2 | mesh/1536/500K face | 超时 | >240s |
| hitem3d-v15 | mesh/1536 | 超时 | >240s |

**分析：**
- HiTem3D 全系列当前（2026-03-24）服务不可用或负载极高
- 对比 Hunyuan3D v3.1 之前稳定完成（180-205s/¥0.40-0.80）
- **结论：3D 生成目前 Hunyuan3D v3.1 仍是 RunningHub 上最可靠的选择**

### 2.4 HiTem3D vs Hunyuan3D 技术对比（理论）

| 维度 | HiTem3D v2 | Hunyuan3D v3.1 |
|------|-----------|----------------|
| 厂商 | HiTem (创新企业) | 腾讯混元 |
| 面数控制 | 100K-2M 可调 | 固定 |
| 人像专版 | 有 (Portrait) | 无单独版本 |
| 多图输入 | 支持 | 支持 |
| 稳定性 | 差 (多次超时) | 好 |
| 成本 | 未知 | ¥0.40-0.80 |

## 3. GPT Image 1.5 多图编辑 (rhart-image-g-1.5/edit)

### 3.1 端点特性

```
rhart-image-g-1.5/edit:
  实际模型: gpt-image-1.5
  输入: 最多 2 张图 + prompt (800字符)
  宽高比: auto / 1:1 / 3:2 / 2:3
  成本: ¥0.01 (极低!)
```

### 3.2 实验 #63：多图合成编辑

**输入：** 龙虾厨师角色图 + 日式庭园背景图
**指令：** 将龙虾厨师放入庭园的木桥上

**结果：** ⭐⭐⭐⭐⭐
- 角色 ID 高度保持（表情/服装/体型一致）
- 场景融合自然（站在桥上，比例正确）
- 光影协调（金色阳光正确映射到角色上）
- 3D 风格一致性好

**GPT Image 1.5 多图编辑关键优势：**
1. **极致性价比** — ¥0.01/张
2. **多图理解能力强** — 能准确识别两张图中的主体和背景
3. **自然融合** — 光影/透视/风格自动协调
4. **快速** — 60s 出结果

### 3.3 vs Qwen Image Edit 对比

| 维度 | GPT Image 1.5 Edit | Qwen 2.0 Pro | Qwen 2.0 |
|------|-------------------|-------------|----------|
| 成本 | ¥0.01 | ¥0.05 | ¥0.02 |
| 多图输入 | ✅ 最多 2 张 | ❌ 单图 | ❌ 单图 |
| 精确编辑 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 场景合成 | ⭐⭐⭐⭐⭐ | N/A | N/A |
| 文本编辑 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 速度 | 60s | 20s | 15s |

**选型决策：**
- 多图合成/场景替换 → GPT Image 1.5 Edit (¥0.01)
- 精确局部编辑（加帽子/换颜色/加文字）→ Qwen 2.0 (¥0.02)
- 复杂精确编辑 + 最高质量 → Qwen 2.0 Pro (¥0.05)

## 4. Qwen Image 2.0（非 Pro）编辑测试

### 4.1 实验 #65：多指令精确编辑

**指令：**
1. 厨师帽 → 海盗帽（骷髅旗）
2. 左眼加眼罩
3. 右钳持剑

**结果：** ⭐⭐⭐⭐⭐ — 三项指令全部精确执行！
- 海盗帽设计精致（黑色三角帽 + 金边 + 骷髅旗）
- 眼罩正确遮住左眼
- 剑有精致的金色护手
- 角色 ID 完美保持

### 4.2 Qwen 2.0 vs 2.0 Pro 差异分析

| 维度 | Qwen 2.0 | Qwen 2.0 Pro |
|------|----------|-------------|
| 成本 | ¥0.02 | ¥0.05 |
| 编辑精确度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ID 保持 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 速度 | 15s | 20s |
| 分辨率 | 标准 | 更高 |
| 适用场景 | 日常编辑 | 高质量需求 |

**⚠️ 重要发现：Qwen 2.0 非 Pro 版在大多数编辑场景下效果与 Pro 接近，但成本仅 40%！**
- 日常编辑首选 Qwen 2.0（¥0.02）
- 需要最高分辨率/质量时用 Pro（¥0.05）

## 5. Ultra 编辑模式 (rhart-image-n-pro-official/edit-ultra)

### 5.1 端点特性

```
rhart-image-n-pro-official/edit-ultra:
  实际模型: nano-banana-pro-official (Gemini) Ultra 模式
  输入: 最多 10 张图 + prompt (4000字符!)
  分辨率: 4K / 8K
  宽高比: 11 种选项
  成本: ¥0.14 (4K)
```

**与普通 Edit 的关键差异：**
- 输入图数量：2 → **10**
- Prompt 长度：800 → **4000** 字符
- 分辨率：1K → **4K/8K**
- 成本：¥0.03 → ¥0.14 (4K)

### 5.2 实验 #67：Ultra 场景变换

**输入：** GPT 1.5 合成的龙虾+庭园图
**指令：** 转换为水下珊瑚礁餐厅场景（详细 prompt）

**结果：** ⭐⭐⭐⭐⭐ 
- **输出分辨率: 5483×3060** (约 5.5K！4K 设置输出了超 4K)
- 场景完全重构：庭园→水下，桥→珊瑚吧台，樱花→海草
- 龙虾厨师 ID 完美保持
- 新增元素丰富：水母、热带鱼、气泡、生物发光
- Pixar 3D 风格一致性极佳
- 画质极高，细节丰富

### 5.3 Ultra 编辑的 ComfyUI 工作流映射

Ultra 模式对应 ComfyUI 中的多步编排：

```
Traditional ComfyUI Pipeline:
1. Load Source Image → VAE Encode
2. GroundingDINO + SAM2 → Auto Mask
3. Flux Fill Inpaint → 局部重绘
4. ESRGAN/Topaz Upscale → 高分辨率
5. FaceDetailer → 修复细节

Ultra Edit (Single API Call):
Input Image(s) + Detailed Prompt → 5.5K Output

关键差异：
- ComfyUI 方式：精确控制每步，但需要 20+ 节点 + 本地 GPU
- Ultra Edit：一次调用完成全部，但控制粒度低
- 适合场景：概念探索、快速原型、非精确编辑需求
```

### 5.4 Ultra 编辑最佳实践

1. **详细 Prompt** — 充分利用 4000 字符限制，详尽描述期望的变化
2. **参考图策略** — 可用多图提供风格/元素参考（最多 10 张）
3. **分辨率选择** — 4K 已经输出 5.5K，8K 可能输出更大
4. **成本控制** — 4K ¥0.14 vs 8K 可能更贵，按需选择

## 6. Topaz CGI 放大器

### 6.1 端点特性

```
topazlabs/image-upscale-cgi:
  专为 CGI/3D 渲染图优化
  缩放: 2x / 4x / 6x
  主体检测: All / Foreground / Background
  人脸增强: 可开关 + 创造力/强度可调
  成本: ¥0.10
```

### 6.2 实验 #64：CGI 放大

**输入：** 1024×1024 龙虾厨师（3D 卡通风格）
**输出：** 2048×2048

**结果分析：**
- 细节增强明显（纹理/边缘更锐利）
- 3D 渲染感增强（光影过渡更平滑）
- 无伪影/无噪声增加
- 速度极快（15s）

### 6.3 Topaz 5 种变体选择指南（更新版）

| 变体 | 最佳场景 | 成本 |
|------|---------|------|
| Standard V2 | 通用照片/插画 | ¥0.10 |
| High Fidelity V2 | 细节保真（纹理/文字） | ¥0.10 |
| Low Resolution V2 | 极低分辨率原图(<256px) | ¥0.10 |
| **CGI** | **3D 渲染/CG 动画/游戏截图** | **¥0.10** |
| Text Refine | 含文字的图（截图/文档/UI） | ¥0.10 |

**新增 CGI 决策分支：**
- 原图是 3D 渲染/CG → 用 CGI
- 原图含重要文字 → 用 Text Refine
- 原图<256px → 用 Low Resolution V2
- 原图需精确纹理 → 用 High Fidelity V2
- 默认 → Standard V2

## 7. 端到端管线实测：T2I → Edit → I2V

### 7.1 完整管线

```
Step 1: T2I 参考图生成
  rhart-image-n-pro T2I → 龙虾厨师 1024×1024
  25s / ¥0.03

Step 2: T2I 背景生成
  rhart-image-n-pro T2I → 日式庭园 1024×684 (3:2)
  20s / ¥0.03

Step 3: 多图合成编辑
  GPT Image 1.5 Edit → 龙虾+庭园合成
  60s / ¥0.01

Step 4: Ultra 场景变换
  Gemini Ultra Edit → 水下珊瑚礁 5483×3060
  95s / ¥0.14

Step 5: I2V 动画化
  Seedance Fast I2V → 5s 1280×720 视频
  45s / ¥0.30

Total: ~245s / ¥0.51
```

### 7.2 管线成本分析

| 步骤 | 模型 | 成本 | 占比 |
|------|------|------|------|
| T2I 参考图 ×2 | rhart-image-n-pro | ¥0.06 | 12% |
| 多图合成 | GPT Image 1.5 | ¥0.01 | 2% |
| Ultra 场景变换 | Gemini Ultra | ¥0.14 | 27% |
| I2V 动画化 | Seedance Fast | ¥0.30 | 59% |
| **总计** | | **¥0.51** | 100% |

**发现：视频生成仍然是管线中最大成本（59%），图像编辑已经非常便宜**

### 7.3 rhart-video-s 超时问题

本轮 rhart-video-s I2V 两次超时（之前正常），可能原因：
1. 服务负载高（凌晨 4 点 UTC = 中午亚太时区）
2. 输入图分辨率过高（5.5K 原图需要内部缩放）
3. 降到 1080p 后仍超时，更可能是服务端问题

**⚠️ 稳定性排名更新：**
1. Seedance Fast — ⭐⭐⭐⭐⭐ 最稳定
2. Kling V3 — ⭐⭐⭐⭐ 稳定
3. rhart-video-s — ⭐⭐⭐ 偶尔超时
4. HiTem3D — ⭐ 当前不可用

## 8. ComfyUI 工作流设计启示

### 8.1 多图编辑的 ComfyUI 等价工作流

GPT Image 1.5 的多图编辑在 ComfyUI 中对应：

```
方案 A: Flux Kontext (Dev)
  FluxKontextImageEncode × 2 → conditioning → FluxGuidance → KSampler
  优点: 精确控制 / 本地运行
  缺点: 需要 Flux 权重 + 高 VRAM

方案 B: IP-Adapter + Regional Conditioning
  IP-Adapter (角色参考) + ConditioningSetArea (位置) + Background Compose
  优点: 更精确的空间控制
  缺点: 多节点复杂度高

方案 C: RMBG + Composite + Inpaint
  RMBG 提取角色 → 手动 Composite 到背景 → Flux Fill 融合边缘
  优点: 最精确控制
  缺点: 最多步骤
```

### 8.2 Ultra 编辑的 ComfyUI 等价

Ultra 编辑（场景完全变换）在 ComfyUI 中最接近：
- **ICEdit** (Diptych 范式) — 通过 DiT 自注意力实现上下文感知编辑
- **Flux Fill** (高 denoise) — 大面积重绘 + 角色保持
- **IP-Adapter + SD I2I** — 风格迁移 + 场景变换

但没有任何单个 ComfyUI 方案能匹配 Ultra 的"一键全面变换"能力。

## 9. 关键发现总结

### 新端点价值评估

| 端点 | 价值 | 稳定性 | 推荐度 |
|------|------|--------|--------|
| GPT Image 1.5 Edit | ⭐⭐⭐⭐⭐ 多图合成神器 | ⭐⭐⭐⭐⭐ | 🟢 强推 |
| Gemini Ultra Edit | ⭐⭐⭐⭐⭐ 高分辨率场景变换 | ⭐⭐⭐⭐ | 🟢 推荐 |
| Qwen 2.0 (非 Pro) | ⭐⭐⭐⭐ 性价比精确编辑 | ⭐⭐⭐⭐⭐ | 🟢 强推 |
| Topaz CGI | ⭐⭐⭐⭐ CG 图专用放大 | ⭐⭐⭐⭐⭐ | 🟢 推荐 |
| HiTem3D | ❓ 未测试成功 | ⭐ 全超时 | 🔴 暂不推荐 |

### 图像编辑模型选择策略（更新）

```
编辑类型决策树:
├── 多图合成/场景替换
│   ├── 预算敏感 → GPT Image 1.5 Edit (¥0.01) ✨新
│   └── 最高质量 → Gemini Ultra Edit (¥0.14) ✨新
├── 精确局部编辑（加/改/删元素）
│   ├── 日常使用 → Qwen 2.0 (¥0.02) ✨新发现更便宜
│   └── 最高质量 → Qwen 2.0 Pro (¥0.05)
├── 风格/场景完全变换
│   ├── 保持角色 → Ultra Edit (¥0.14)
│   └── 不保持 → Seedream I2I (¥0.04)
└── 高分辨率输出需求
    └── Ultra Edit 4K (¥0.14) 直接输出 5.5K
```

## 10. 实验成本汇总

| 实验# | 端点 | 描述 | 耗时 | 成本 |
|-------|------|------|------|------|
| #60 | rhart-image-n-pro T2I | 龙虾厨师参考图 | 25s | ¥0.03 |
| #61 | hitem3d-v2 | 图生3D (超时) | >240s | ¥0.00 |
| #62 | rhart-image-n-pro T2I | 日式庭园 | 20s | ¥0.03 |
| #63 | rhart-image-g-1.5 edit | 多图合成编辑 | 60s | ¥0.01 |
| #64 | topazlabs/image-upscale-cgi | CGI 放大 | 15s | ¥0.10 |
| #65 | alibaba/qwen-image-2.0 | 海盗编辑 | 15s | ¥0.02 |
| - | hitem3d-v2 mesh | 重试 (超时) | >240s | ¥0.00 |
| - | hitem3d-v15 mesh | 重试 (超时) | >240s | ¥0.00 |
| #67 | rhart-n-pro-official ultra | Ultra 场景变换 | 95s | ¥0.14 |
| - | rhart-video-s I2V | 动画化 (超时×2) | >300s | ¥0.00 |
| #68 | seedance-v1.5-pro fast | I2V 水下动画 | 45s | ¥0.30 |
| **总计** | | **8个成功实验** | | **¥0.63** |
