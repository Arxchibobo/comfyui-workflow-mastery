# ComfyUI 学习状态总结

> 生成时间：2026-03-20 13:00 UTC | 学习启动：2026-03-18 10:00 UTC

## 📊 总体进度

| 指标 | 数据 |
|------|------|
| 学习天数 | 2.5 天（3/18 ~ 3/20） |
| 完成轮数 | 9 轮（其中 13 轮因超时浪费） |
| 完成阶段 | Phase 1 全部 ✅ + Phase 2 进行中（Day 4 / 共 4 天） |
| 笔记总量 | 7 个文件，4246 行，~157KB |
| 工作流 JSON | 5 个（1 基础 + 4 实验） |
| 实际运行验证 | ❌ 0 个（没有 ComfyUI 实例） |

## ✅ 已完成内容

### Phase 1: 基础理论（Day 1-3）— 全部完成 ✅

**Day 1 — SD 核心算法原理**（3 轮，~6h）
- DDPM/LDM 完整理论 + 两篇原始论文精读
- 采样器/CFG/步数系统性分类体系 + 决策树
- ComfyUI 源码阅读（execution.py + graph.py）
- 产出：`day01-sd-fundamentals.md`（796 行）

**Day 2 — Latent Space & Sampling 深入**（2 轮，~4h）
- ODE vs SDE 统一框架 + Score-based SDE 数学推导
- 5 种采样器完整数学推导对比
- Noise Schedule 设计原理（Linear/Cosine/Karras）
- 6 节点 text2img 工作流拓扑解析 + API JSON
- 产出：`day02-latent-space-sampling.md`（1239 行）+ `text2img.json`

**Day 3 — ComfyUI 架构深入**（2 轮，~10h）
- 节点注册机制 + 13 种核心数据类型
- 执行引擎 4 层缓存架构 + Lazy Eval + 异步并行
- REST API 全端点 + WebSocket 8 种消息协议
- 产出：3 个笔记文件（共 1713 行）

### Phase 2: 核心工作流实操（Day 4）— 进行中

**Day 4 — 采样器对比实验**（2 轮，~0.5h）
- 6 种采样器系统性对比实验设计
- SD1.5/SDXL/Flux 三架构采样器行为差异分析
- 9 种 Scheduler 数学公式源码分析
- Scheduler×Sampler 兼容性矩阵 + 快速决策树
- 产出：2 个笔记文件（498 行）+ 4 个工作流 JSON

## ❌ 未完成内容

### Day 4 剩余（~2 轮 = 4h）
- [ ] 批量生成与质量评估方法论（FID/CLIP Score）
- [ ] ComfyUI 批量生成工作流设计

### Phase 2 剩余（Day 5-7，~18 轮 = 3 天）
- [ ] **Day 5**: Img2Img / Inpainting / Outpainting
- [ ] **Day 6**: ControlNet 全系列（Canny/Depth/Pose/Tile/IP-Adapter）
- [ ] **Day 7**: LoRA 使用 + 多 LoRA 融合 + 权重调节

### Phase 3: 高级技术（Day 8-12，~30 轮 = 5 天）
- [ ] **Day 8**: SDXL Refiner 工作流
- [ ] **Day 9**: LoRA 训练（kohya_ss / sd-scripts）
- [ ] **Day 10**: 自定义节点开发（Python API）
- [ ] **Day 11**: AnimateDiff / SVD 视频生成
- [ ] **Day 12**: Flux / SD3 新架构

### Phase 4: 专精方向（Day 13+，~4 天）
- [ ] 模型合并
- [ ] Textual Inversion / DreamBooth
- [ ] ComfyUI API 自动化 + 批量任务
- [ ] 性能优化（TensorRT / 量化 / 显存管理）

## ⏱️ 时间预估

| 阶段 | 剩余天数 | 每天学习轮数 | 说明 |
|------|---------|------------|------|
| Day 4 剩余 | 0.5 天 | 2 轮 | 批量生成方法论 |
| Phase 2（Day 5-7） | 3 天 | 6 轮/天 | 核心工作流实操 |
| Phase 3（Day 8-12） | 5 天 | 6 轮/天 | 高级技术 |
| Phase 4（Day 13-16） | 4 天 | 6 轮/天 | 专精方向 |
| **总计** | **~12.5 天** | | **预计 4/1 前完成** |

## 🔴 最大问题：理论 vs 实践严重失衡

### 学了什么（理论）— 大量
- SD 扩散模型完整数学理论
- 采样器算法推导（5 种）
- ComfyUI 源码级架构理解
- 节点系统、缓存、执行引擎、API 协议

### 实践了什么 — 极少
- 编写了 5 个工作流 JSON（但从未实际运行）
- 没有生成过一张图
- 没有验证过任何工作流是否能跑通
- 没有做过真实的参数调优实验

### 能否自己编辑工作流？— 理论上能，实际未验证
- ✅ 理解节点连接逻辑和数据类型
- ✅ 能手写 API 格式的工作流 JSON
- ✅ 知道每个参数的含义和推荐值
- ❌ **从未在真实 ComfyUI 实例上验证过**
- ❌ 不知道实际运行中会遇到什么问题
- ❌ 没有调试工作流报错的实战经验

### 根因
没有可用的 ComfyUI 实例。所有"实验"都是纸上谈兵 — 写了工作流 JSON 但没跑过。

### 建议
1. **搭一个 ComfyUI 实例**（本机或 RunningHub）→ 立即验证已写的 5 个工作流
2. 后续学习改为 **先跑通再写笔记**，不要先理论后实践
3. Phase 2-4 每天至少生成 10 张图，用实际结果驱动学习

## 📁 文件清单

### 笔记（comfyui-learning/notes/）
| 文件 | 行数 | 主题 |
|------|------|------|
| day01-sd-fundamentals.md | 796 | SD 算法原理 + 论文精读 |
| day02-latent-space-sampling.md | 1239 | Latent Space + 采样器 + text2img 工作流 |
| day03-comfyui-architecture.md | 560 | 节点系统 + 自定义节点 |
| day03-execution-engine-deep-dive.md | 581 | 执行引擎 + 缓存架构 |
| day03-api-protocol.md | 572 | REST API + WebSocket 协议 |
| day04-sampler-experiments.md | 131 | 采样器对比实验设计 |
| day04-model-sampler-matrix.md | 367 | 模型×采样器矩阵 |

### 工作流 JSON（comfyui-learning/sample-workflows/）
| 文件 | 用途 | 已验证 |
|------|------|--------|
| basic/text2img.json | 基础文生图 | ❌ |
| experiments/sampler-comparison.json | 6 种采样器对比 | ❌ |
| experiments/scheduler-sampler-cross-sdxl.json | Scheduler×Sampler 交叉 | ❌ |
| experiments/flux-vs-sdxl-sampler-compare.json | Flux vs SDXL 对比 | ❌ |
| experiments/steps-quality-curve.json | 步数-质量曲线 | ❌ |
