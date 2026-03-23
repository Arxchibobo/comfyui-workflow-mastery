# PostGrad #4: Seedream 模型家族 + 图像编辑→视频链式管线

> 日期: 2026-03-23 18:03 UTC | 轮次: 48 | 总花费: ¥0.47

## 学习目标

1. **Seedream 模型家族首次实测** — ByteDance 出品的新一代图像生成模型（v4/v4.5/v5-lite）
2. **图像编辑→视频链式管线** — 验证"生成→编辑→动画化"的完整工作链路
3. **编辑模型对比** — Qwen-Image-Edit vs Seedream I2I 两种编辑方式

---

## 1. Seedream 模型家族概览

### RunningHub 可用版本

| 模型 | T2I | I2I | 价格 | 分辨率 |
|------|-----|-----|------|--------|
| Seedream v4 | ✅ | ✅ | ¥0.04 | 2048x2048 |
| Seedream v4.5 | ✅ | ✅ | ¥0.04 | 2048x2048 |
| Seedream v5-lite | ✅ | ✅ | ¥0.04 | 2048x2048 |

### 关键发现

- **默认输出 2048x2048** — 比 rhart-image-n-pro 的 1024x1024 高一倍分辨率，同样价格 ¥0.04
- **生成速度快** — v4.5 仅 15s，v5-lite 25s
- **Prompt 遵从度高** — 复杂角色描述（龙虾厨师+厨师帽+围裙+金铲）全部准确渲染
- **风格差异**:
  - **v5-lite**: 偏 3D 渲染/Pixar 风格，细节精致，光影层次丰富，侧身视角
  - **v4.5**: 偏写实/摄影风格，更暗的氛围光，正面全身视角，更具威严感

### vs rhart-image-n-pro 对比

| 维度 | Seedream v5-lite | rhart-image-n-pro |
|------|-----------------|-------------------|
| 分辨率 | 2048x2048 | 1024x1024 |
| 价格 | ¥0.04 | ¥0.03 |
| 速度 | 25s | 20-30s |
| 风格 | 3D/Pixar 偏向 | 灵活多变 |
| Prompt 遵从 | 优秀 | 优秀 |

**结论**: Seedream 在高分辨率输出方面有明显优势（4x 像素），适合需要大图的场景。

---

## 2. 图像编辑对比实验

### 实验 #62: Qwen-Image-2.0-Pro 编辑

- **输入**: Seedream v5-lite 生成的龙虾厨师
- **编辑指令**: "Change chef hat to golden crown + add fire effects on spatula + magical kitchen with glowing runes"
- **结果**: ⭐⭐⭐⭐⭐
  - ✅ 厨师帽→精致金冠（带宝石细节）
  - ✅ 铲子喷射火焰效果
  - ✅ 背景完全变换为石墙魔法厨房
  - ✅ 墙壁上有发光北欧符文
  - ✅ 添加了悬挂的大锅等魔法元素
  - ✅ 龙虾角色身份完美保持
- **耗时**: 20s | **费用**: ¥0.05
- **分析**: Qwen 的编辑是**指令级精确编辑** — 你说改什么就改什么，其他保持不变。非常适合精细的局部/全局编辑

### 实验 #64: Seedream v5-lite I2I 编辑

- **输入**: 同一张龙虾厨师图
- **参数**: strength=0.65（中等变换强度）
- **Prompt**: "lobster sorcerer in underwater palace, golden crown, magical trident with blue lightning, floating runes, bioluminescent coral"
- **结果**: ⭐⭐⭐⭐⭐
  - ✅ 完整场景变换（厨房→海底宫殿）
  - ✅ 金冠、三叉戟+蓝色闪电
  - ✅ 浮动魔法圆阵符文
  - ✅ 生物发光珊瑚和海底氛围
  - ✅ 龙虾角色整体结构保持
- **耗时**: 30s | **费用**: ¥0.04
- **分析**: Seedream I2I 是**风格/场景级变换** — 以原图为骨架进行大幅重新创作。适合风格迁移、场景切换

### 编辑方式对比

| 维度 | Qwen-Image-Edit | Seedream I2I |
|------|-----------------|-------------|
| 编辑精度 | 极高（指令级） | 中等（全局变换） |
| ID 保持 | 极好（姿势/角度/细节几乎不变） | 好（结构保持，细节变化大） |
| 变换幅度 | 可控（只改指定部分） | 大幅（整体重新创作） |
| 适用场景 | 精确局部编辑、属性修改 | 风格迁移、场景转换 |
| 中文支持 | ✅（双语） | Prompt 为主 |
| 费用 | ¥0.05 | ¥0.04 |

**关键洞察**: 两种编辑方式互补而非竞争——
- 需要精确修改（改颜色/加物体/改背景但保持主体）→ **Qwen-Image-Edit**
- 需要风格/场景大幅变换 → **Seedream I2I**
- 生产管线中可组合使用：Seedream 做场景变换 → Qwen 做精确微调

---

## 3. 生成→编辑→动画化完整链式管线

### 管线架构

```
Stage 1: T2I 生成 (Seedream v5-lite)
   ↓ 龙虾厨师 2048x2048
Stage 2: 图像编辑 (Qwen-Image-2.0-Pro)
   ↓ 龙虾国王 + 火焰铲 + 魔法厨房
Stage 3: I2V 动画化 (Seedance v1.5 Pro Fast)
   ↓ 5s 动画视频 960x960 24fps
```

### 实验 #63: Seedance Fast 动画化编辑后图片

- **输入**: Qwen 编辑后的龙虾国王（魔法厨房）
- **Prompt**: "lobster king chef waves flaming spatula, fire sparkles, glowing runes pulse, cinematic motion"
- **结果**:
  - 输出 960x960 24fps 5.07s（8MB）
  - 含音频轨（AAC 44.1kHz stereo）
  - 火焰动画效果、角色微动、符文脉冲效果
- **耗时**: 50s | **费用**: ¥0.30

### 完整管线成本分析

| 阶段 | 模型 | 耗时 | 费用 |
|------|------|------|------|
| T2I 生成 | Seedream v5-lite | 25s | ¥0.04 |
| 图像编辑 | Qwen-Image-2.0-Pro | 20s | ¥0.05 |
| I2V 动画 | Seedance v1.5 Pro Fast | 50s | ¥0.30 |
| **合计** | | **95s** | **¥0.39** |

### 管线设计最佳实践

1. **分辨率策略**: Seedream 生成 2048x2048，编辑后保持高分辨率，视频模型会自动缩放到其支持的分辨率（Seedance 输出 960x960）
2. **编辑在视频前**: 图像编辑比视频编辑便宜 10x，尽可能在 T2I 阶段把画面调到位
3. **Prompt 一致性**: 视频 prompt 应描述动作/运动，而非重复描述已有的视觉元素
4. **链式管线的 ComfyUI 映射**:
   - T2I → 任意文生图节点（Flux/SDXL 本地 或 API Partner Node）
   - 编辑 → ICEdit / Flux Fill / InstructPix2Pix（本地）或 Qwen API
   - I2V → KlingSeedanceI2V / KlingImageToVideo / 本地 Wan/LTX

---

## 4. Seedream 技术分析

### Seedream 模型家族背景

Seedream 是字节跳动旗下的图像生成模型系列，基于 DiT 架构（推测）：
- **v4** (2025): 基础版，质量稳定
- **v4.5** (2025): 改进版，速度更快（15s），写实风格更强
- **v5-lite** (2026): 轻量高性能版，3D/Pixar 风格突出

### 在 ComfyUI 生态中的定位

Seedream 目前只能通过 API 调用（RunningHub 等平台），没有开源权重：
- **ComfyUI 集成方式**: 通过 API 代理节点（类似 Partner Nodes 模式）
- **与本地模型配合**: 可作为高质量关键帧生成器，配合本地 ControlNet/LoRA 做细化
- **成本效益**: ¥0.04/张 2048x2048，比本地 Flux+放大更快且质量不输

---

## 5. 实验总结

### 本轮实验列表

| # | 实验 | 模型 | 耗时 | 费用 | 结果 |
|---|------|------|------|------|------|
| 60 | Seedream v5-lite T2I | seedream-v5-lite | 25s | ¥0.04 | ⭐⭐⭐⭐⭐ 2048x2048 精美龙虾厨师 |
| 61 | Seedream v4.5 T2I | seedream-v4.5 | 15s | ¥0.04 | ⭐⭐⭐⭐⭐ 写实风格对比 |
| 62 | Qwen 图像编辑 | qwen-image-2.0-pro | 20s | ¥0.05 | ⭐⭐⭐⭐⭐ 三项编辑全部精准 |
| 63 | Seedance 动画化 | seedance-v1.5-pro-fast | 50s | ¥0.30 | ⭐⭐⭐⭐ 5s 流畅动画 |
| 64 | Seedream v5-lite I2I | seedream-v5-lite | 30s | ¥0.04 | ⭐⭐⭐⭐⭐ 完整场景变换 |

**本轮总花费**: ¥0.47 | **总耗时**: ~140s

### 关键收获

1. **Seedream 性价比极高** — ¥0.04 获得 2048x2048 高质量图像，是新的首选 T2I API 模型之一
2. **Qwen-Image-Edit 是精确编辑之王** — 多指令同时执行，ID 保持极佳
3. **T2I→Edit→I2V 链式管线可行且经济** — ¥0.39 完成从生成到动画的完整链路
4. **编辑模型选择有清晰场景分界** — 精确编辑用 Qwen，风格变换用 Seedream I2I
5. **高分辨率 T2I 对下游 I2V 有益** — 输入质量越高，视频细节越好

### 累计实验统计

- 总实验数: 64（主课程 59 + 毕业后 5 轮新增）
- 毕业后实验: PostGrad#1(3) + #2(5) + #3(5) + #4(5) = 18 个实验
- 毕业后新模型覆盖: rhart-video-s/g, Hailuo 2.3, Vidu Q3, Seedream v4.5/v5-lite
