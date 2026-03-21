# Day 10 — RunningHub 实操验证

> 日期: 2026-03-21 | 平台: RunningHub API (Shared Key) | 余额: $1899

## 实验总览

| # | 类型 | 模型 | Prompt 关键词 | AR | 耗时 | 费用 | 结果 |
|---|------|------|-------------|----|----|------|------|
| 01 | text2img | rhart-image-n-pro | 金毛山顶日出，写实摄影 | 1:1 | 20s | ¥0.03 | ✅ 极佳，rim lighting + 云海效果自然 |
| 02 | text2img | rhart-image-n-pro | 同上 | 16:9 | 20s | ¥0.03 | ✅ 横版构图更大气 |
| 03 | text2img | rhart-image-n-pro | 吉卜力动漫风+樱花园 | 1:1 | 25s | ¥0.03 | ✅ 水彩质感到位，小龙猫彩蛋 |
| 04 | text2img | rhart-image-n-pro | 赛博朋克战士狗 | 9:16 | 25s | ¥0.03 | ✅ 装甲+蓝色发光眼+霓虹雨街 |
| 05 | img2img | rhart-image-n-pro/edit | 01→油画风格 | 1:1 | 25s | ¥0.03 | ✅ 厚涂笔触+画布纹理，构图完整保留 |
| 06 | img2img | rhart-image-n-pro/edit | 04→水墨画风格 | 9:16 | 25s | ¥0.03 | ✅ 水墨留白+装甲细节全保留 |
| 07 | upscale | topazlabs-standard-v2 | 04放大 | - | 20s | ¥0.10 | ✅ 毛发细节显著增强 |
| 08 | text2img | rhart-image-g-4 | 同01 prompt | 16:9 | 85s | ¥1.00 | ✅ 更电影感，但贵33倍 |

### 总费用: ¥1.28 / 8 张图

## 关键发现

### 1. Prompt 工程验证
- **结构化 prompt** 效果显著: 主体 + 环境 + 光影 + 风格 + 质量词
- **风格关键词**对 img2img 效果决定性: "oil painting, impasto brushstrokes" vs "ink wash painting, sumi-e" 产生完全不同的风格迁移
- Negative prompt 不是所有端点都支持（rhart-image-n-pro 无此参数）

### 2. 模型对比: rhart-image-n-pro vs rhart-image-g-4
- **PRO**: ¥0.03/张, 20-25s, 质量已经很高
- **G-4**: ¥1.00/张, 85s, 更电影感但性价比低
- **结论**: 日常用 PRO，高质量需求用 G-4

### 3. Img2Img 风格迁移
- 保留原图构图+主体，只改变渲染风格 — 对应 Day5 学的 denoise 原理
- API 层面是直接的 edit endpoint，底层应该是较高 denoise (0.6-0.8) 的 img2img
- 水墨画甚至保留了"新東京""NEO-TOKYO" 文字（说明 ControlNet 或 attention 在底层起作用）

### 4. 图片放大
- topazlabs upscale 效果好，¥0.10/张
- 对应 Day6 学的 Tile ControlNet 超分原理 — 但 API 封装了底层实现

## 理论 → 实践映射

| 学过的理论 | 实操验证 | 差异/发现 |
|-----------|---------|----------|
| Day1 DDPM/LDM 扩散原理 | 所有生成都是扩散过程 | API 封装了底层，看不到 steps/sampler/CFG |
| Day2 采样器/Noise Schedule | 无法直接控制 | 标准 API 不暴露采样器参数，需用自定义工作流 |
| Day4 采样器对比实验 | 待通过 AI App 工作流验证 | 需要找到暴露 KSampler 参数的工作流 |
| Day5 Img2Img/denoise | 实验05-06 验证 | 风格迁移效果好，但无法控制 denoise 值 |
| Day6 ControlNet/Tile | 实验07 upscale | API 封装，底层可能用 Tile ControlNet |
| Day7 LoRA | 待验证 | 需要找到支持 LoRA 加载的自定义工作流 |

## 实验续 — 多模型对比 + 视频生成

| # | 类型 | 模型 | 耗时 | 费用 | 发现 |
|---|------|------|------|------|------|
| 09 | img2video | rhart-video-s | 185s | ¥0.10 | 赛博朋克狗动起来了！雨滴+霓虹闪烁自然 |
| 10 | text2img | seedream-v5-lite | 20s | ¥0.04 | 最低2048px，柔粉色调，更"甜"的风格 |
| 11 | text2img | rhart-image-v2-flash | 20s | ¥0.02 | 最便宜！质量不输PRO，云海细节更丰富 |
| 12 | text2img | rhart-image-g-1.5 | 25s | ¥0.01 | 最便宜的之一，暖金色调最浓 |

### 模型对比总结（同一 prompt: 金毛山顶日出）

```
模型              价格     耗时    风格特点                    推荐场景
──────────────────────────────────────────────────────────────────────────
rhart-PRO         ¥0.03   20s    均衡写实，细节好              日常首选
rhart-V2-flash    ¥0.02   20s    性价比之王，质量接近PRO        批量生成
rhart-G-1.5       ¥0.01   25s    最便宜，暖色调偏重            预算敏感
rhart-G-4         ¥1.00   85s    最电影感，景深最好            高端需求
seedream-v5       ¥0.04   20s    柔和粉调，最低2048px         插画/海报
```

### 图生视频关键发现
- rhart-video-s 是最便宜的图生视频（¥0.10/10s）
- 185秒生成时间，需要异步等待
- 动态效果：雨滴下落、霓虹灯闪烁、蒸汽升腾 — 但狗的身体基本不动（这是 img2video 的特点）
- 要让主体做大动作，需要用更高级模型（可灵 3.0 Pro 等）

## 实践心得

### 1. API 封装 vs ComfyUI 原生的差异
标准 API 把 ComfyUI 底层的所有节点封装成了黑箱：
- ✅ 简单：一个 prompt + 几个参数就出图
- ❌ 不透明：看不到 KSampler 用了什么采样器、多少步、什么 scheduler
- ❌ 不可控：无法调 denoise、CFG、seed 等核心参数
- 要做精细控制，必须用自定义 ComfyUI 工作流（AI App / workflow API）

### 2. 费用敏感度
- 图片生成：¥0.01-0.03 就够用，不要轻易用 G-4（¥1.00）
- 图片放大：¥0.10，值得
- 视频：¥0.10-1.00+，取决于模型和时长
- 12 个实验总费用 ¥1.48，非常经济

### 3. Prompt 工程实证
结构化 prompt 确实有效：
- `主体描述` + `环境/场景` + `光影条件` + `风格关键词` + `质量词`
- 动漫风加 "Studio Ghibli style, watercolor" 效果显著
- 赛博朋克加 "neon-lit, rain-soaked, blade runner" 效果显著
- 水墨风迁移 "ink wash painting, sumi-e, minimalist" 效果极佳

## 下一步计划
1. ⏳ 尝试通过 AI App 工作流运行带 KSampler 参数的自定义工作流
2. ⏳ ControlNet 实操（Canny/Depth 预处理 → 指导生成）
3. ⏳ LoRA 加载实验
4. ⏳ 更复杂的图生视频（可灵模型）
