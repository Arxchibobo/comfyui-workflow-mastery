# ComfyUI & Stable Diffusion 深度学习计划

> ⚠️ 2026-03-21 路径纠正：bobooo 要求视频生成用 ComfyUI 工作流（API节点调Kling/Seedance/Veo3.1 或 LTX本地），不要只用封装 API

## 📅 总体规划

### Phase 1: 基础理论（Day 1-3）✅ 完成
- [x] **Day 1**: SD 核心算法原理（DDPM/LDM 论文精读 + 源码）
- [x] **Day 2**: Latent Space & Sampling（5种采样器数学推导 + text2img 工作流）
- [x] **Day 3**: ComfyUI 架构（节点系统 + 执行引擎 + API协议）

### Phase 2: 核心工作流实操（Day 4-7）✅ 完成
- [x] **Day 4**: 采样器对比 + 批量生成 + 质量评估方法论
- [x] **Day 5**: Img2Img / Inpainting / Outpainting
- [x] **Day 6**: ControlNet 全系列（Canny/Depth/Pose/Tile/IP-Adapter + 多CN组合）
- [x] **Day 7**: LoRA 完整体系（数学原理 + LyCORIS + ComfyUI源码 + 多LoRA融合）

### Phase 3: 高级技术（Day 8-12）🔧 进行中
- [x] **Day 8**: SDXL 架构 + Refiner（双编码器 + 微条件 + 交接机制）
- [x] **Day 9**: LoRA 训练管线（sd-scripts + 参数深度 + 3套配置）
- [x] **Day 10**: RunningHub 实操（12个实验 + 5模型对比 + 视频生成方案全景）
- [x] **Day 11**: LTX-2.3 视频工作流深度（47节点体系 + 两阶段管线 + Wan 2.6 对比）
- [x] **Day 12**: ComfyUI API 节点体系（Partner Nodes / Kling / Seedance / Veo3.1 集成）

### Phase 4: 视频 & 动画专精（Day 13-16）— 纠正后新增
- [x] **Day 13**: AnimateDiff 运动模块（基于 SD 的视频生成）
- [x] **Day 14**: 自定义节点开发（Python API）
- [x] **Day 15**: Flux / SD3 新架构
- [ ] **Day 16**: 综合实战 — 从零编排完整视频生成工作流

### Phase 5: 专精方向（Day 17+）
- [ ] 模型合并（Model Merging）
- [ ] ComfyUI API 自动化 + 批量任务
- [ ] 性能优化（TensorRT / 量化 / 显存管理）

## 📊 每日学习记录
| 日期 | 主题 | 时长 | 实操 | 笔记 |
|------|------|------|------|------|
| 3/18 | Day1-3 基础理论 | ~20h | text2img JSON | 7个笔记文件 |
| 3/20 | Day4-9 核心+高级 | ~12h | 28个工作流JSON | 7个笔记文件 |
| 3/21 | Day10 RunningHub实操 | ~2h | 14个实验(图/视频) | 2个笔记文件 |
| 3/21 | Day11 LTX-2.3工作流深度 | ~1h | Wan2.6 T2V+Ref2V | 1个笔记文件 |
| 3/21 | Day12 ComfyUI API节点体系 | ~1.5h | Kling 3.0 + Veo 3.1 I2V对比 | 1个笔记文件 |
| 3/21 | Day13 AnimateDiff运动模块 | ~2h | Seedance+Wan对比 | 1个笔记文件 |
| 3/21 | Day14 自定义节点开发 | ~1h | 架构概念图 | 1个笔记文件 |
| 3/21 | Day15 Flux/SD3新架构 | ~1.5h | 架构概念图实验 | 1个笔记文件 |
