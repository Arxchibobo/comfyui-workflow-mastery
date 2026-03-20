# Day 4 — 采样器系统性对比实验设计

> 日期: 2026-03-20 | 学习轮次: 8

## 1. 实验目的

通过**严格控制变量**的方法，系统性对比 6 种主流采样器在相同条件下的生成表现差异，建立对各采样器特性的直觉理解，为后续模型×采样器最优组合选择提供数据支撑。

### 核心问题
1. **质量差异**：相同步数下，哪些采样器能产生更高质量的图像？
2. **收敛速度**：哪些采样器能在更少步数内收敛到稳定输出？
3. **细节表现**：在纹理、边缘、光影等维度上，各采样器有何偏向？
4. **步数敏感度**：低步数（10）和高步数（30）时表现差异如何？

## 2. 选定的 6 种采样器

| 采样器 | 类型 | 阶数 | 每步 NFE | 核心特点 |
|--------|------|------|----------|---------|
| `euler` | ODE 求解器 | 一阶 | 1 | 最基础的一阶方法，速度最快，是所有采样器的 baseline |
| `dpmpp_2m` | 多步 ODE | 二阶 | 1 | DPM++ 2M 多步法，利用历史信息提升精度，性价比极高 |
| `dpmpp_sde` | SDE 求解器 | — | 1 | DPM++ SDE 变体，引入随机性，擅长平滑渐变和真实感纹理 |
| `ddim` | ODE 求解器 | 一阶 | 1 | 经典确定性采样，可通过 eta 控制随机性，稳定可预测 |
| `heun` | ODE 求解器 | 二阶 | 2 | 改进 Euler（预测-校正），收敛快但每步计算量翻倍 |
| `uni_pc` | 统一预测器-校正器 | 多阶 | 1 | UniPC 自适应阶数，少步数表现优异（5-10 步即可用） |

### 选择理由
- **euler**: 最基础 baseline，速度参考标杆
- **dpmpp_2m**: 社区公认性价比最高，SD1.5/SDXL 通用首选
- **dpmpp_sde**: SDE 类代表，引入随机性带来不同美学风格
- **ddim**: 经典方法，学术界标准参照
- **heun**: 二阶方法代表，展示精度 vs 速度权衡
- **uni_pc**: 新一代少步数采样器，展示算法进步

## 3. 控制变量方案

### 固定变量（不变）
| 变量 | 固定值 | 理由 |
|------|--------|------|
| **Checkpoint** | SD 1.5 base (v1-5-pruned-emaonly) | 最通用的基准模型 |
| **Prompt** | `"a majestic lion standing on a cliff at sunset, dramatic lighting, highly detailed fur, 8k, photorealistic"` | 包含多种细节要素：毛发纹理、光影、背景 |
| **Negative Prompt** | `"blurry, low quality, deformed, ugly, bad anatomy"` | 标准负面提示 |
| **Seed** | `42` | 经典固定种子，确保可复现 |
| **CFG Scale** | `7.0` | SD1.5 标准推荐值 |
| **Resolution** | `512×512` | SD1.5 原生分辨率 |
| **Scheduler** | `normal` | 最基础的线性 schedule |
| **Denoise** | `1.0` | 完全从噪声生成 |

### 自变量
| 变量 | 取值 | 说明 |
|------|------|------|
| **Sampler** | euler / dpmpp_2m / dpmpp_sde / ddim / heun / uni_pc | 6 种采样器 |
| **Steps** | 20 | 第一轮固定 20 步（后续实验可扩展） |

### 因变量（观察指标）
1. **视觉质量**：整体清晰度、细节丰富度（主观评分 1-5）
2. **纹理表现**：毛发质感、皮肤光滑度、背景自然度
3. **色彩饱和度**：色调是否自然、对比度是否合适
4. **伪影/瑕疵**：是否有噪点残留、色块、解剖错误
5. **风格倾向**：偏真实 vs 偏绘画 vs 偏平滑

## 4. 预期结果（基于社区研究和理论分析）

| 采样器 | 预期表现 |
|--------|---------|
| **euler** | 20 步基本收敛，细节中等，速度最快。作为 baseline 其他采样器与之比较 |
| **dpmpp_2m** | 20 步表现优于 euler（多步法利用历史），细节更锐利，性价比最优 |
| **dpmpp_sde** | 随机性带来更柔和的渐变和真实感纹理，但可能引入轻微噪点变化 |
| **ddim** | 稳定、可预测，细节偏平滑/保守，不容易出惊艳效果也不容易出错 |
| **heun** | 细节最精细（二阶精度），但实际耗时约 euler 的 2 倍（每步 2 次函数评估） |
| **uni_pc** | 20 步时表现与 dpmpp_2m 相当甚至更优，主要优势在低步数（5-10） |

### 关键预测
- **速度排名**（快→慢）：euler ≈ dpmpp_2m ≈ ddim ≈ uni_pc > dpmpp_sde > heun
- **20 步质量排名**（预测）：dpmpp_2m ≈ heun > uni_pc > dpmpp_sde > euler > ddim
- **低步数友好度**：uni_pc > dpmpp_2m > ddim > euler > dpmpp_sde > heun

## 5. 工作流设计说明

### 文件: `sample-workflows/experiments/sampler-comparison.json`

工作流使用 **6 组独立的 KSampler 节点**，共享同一个模型加载、CLIP 编码和空 Latent：

```
CheckpointLoaderSimple (节点 1)
    ├── CLIPTextEncode 正向 (节点 2)
    ├── CLIPTextEncode 负向 (节点 3)
    └── EmptyLatentImage 512x512 (节点 4)
         │
         ├── KSampler [euler] (节点 10) → VAEDecode (节点 20) → SaveImage (节点 30)
         ├── KSampler [dpmpp_2m] (节点 11) → VAEDecode (节点 21) → SaveImage (节点 31)
         ├── KSampler [dpmpp_sde] (节点 12) → VAEDecode (节点 22) → SaveImage (节点 32)
         ├── KSampler [ddim] (节点 13) → VAEDecode (节点 23) → SaveImage (节点 33)
         ├── KSampler [heun] (节点 14) → VAEDecode (节点 24) → SaveImage (节点 34)
         └── KSampler [uni_pc] (节点 15) → VAEDecode (节点 25) → SaveImage (节点 35)
```

### 设计要点
- **共享前端节点**：模型只加载一次，CLIP 编码只执行一次，节省显存和时间
- **独立后端管线**：每个采样器有独立的 KSampler → VAEDecode → SaveImage 链
- **文件名区分**：SaveImage 的 `filename_prefix` 设为 `sampler_comparison/euler` 等，输出自动按采样器分目录
- **ComfyUI 缓存利用**：由于前端节点共享，ComfyUI 的执行缓存会自动跳过重复计算

### 扩展建议
1. **步数对比**：复制工作流，修改 steps 为 10/30/50，观察各采样器的收敛曲线
2. **Scheduler 交叉**：替换 scheduler 为 karras/exponential，观察交互效应
3. **模型切换**：替换 checkpoint 为 SDXL/Flux，对比不同架构的采样器偏好
4. **多 Seed**：增加 seed 变体（42/123/456/789），减少随机性对结论的干扰

## 6. 社区研究总结

### 来自 comfyui.dev 官方文档
- `dpmpp_sde`: 引入 SDE 平滑，擅长干净渐变和真实感
- `dpmpp_2m_cfg_pp` + karras: 被评为 S-tier 组合
- `ddim`: 速度和质量的中间地带

### 来自 Reddit Flux-dev 社区测试（2024-08）
- Flux 模型下采样器表现与 SD1.5 差异很大
- euler/heun/ddim 在 Flux 下表现良好
- dpmpp 系列在 Flux 下表现不稳定（模型架构差异）
- 说明：**采样器选择必须考虑模型架构**

### 来自 Civitai 深度分析
- Heun 收敛更快但每步耗时翻倍（二阶方法的固有代价）
- SD1.5 上 Euler A 是速度首选
- SDXL 上建议 DPM++ 2M SDE Heun + Karras

### 关键洞察
- **没有万能采样器**：最优选择取决于模型架构 × 场景需求
- **DPM++ 2M 是通用安全牌**：在 SD1.5/SDXL 上几乎总是前三
- **Heun 的代价被低估**：虽然质量高，但 2× 的时间成本在生产中很显著
- **uni_pc 在少步数场景有独特优势**：5-10 步时可能是最佳选择
