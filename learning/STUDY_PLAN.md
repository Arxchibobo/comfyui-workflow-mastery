# ComfyUI & Stable Diffusion 深度学习计划

## 📅 总体规划（预计 2-3 周）

### Phase 1: 基础理论（Day 1-3）
- [ ] **Day 1**: Stable Diffusion 核心算法原理（扩散模型、去噪过程、U-Net、VAE、CLIP）
- [ ] **Day 2**: Latent Space、Sampling 算法（Euler/DPM/DDIM）、CFG 原理
- [ ] **Day 3**: ComfyUI 架构（节点系统、执行引擎、数据流）

### Phase 2: 核心工作流实操（Day 4-7）
- [ ] **Day 4**: Text2Img 全流程（各种采样器对比实验）
- [ ] **Day 5**: Img2Img、Inpainting、Outpainting
- [ ] **Day 6**: ControlNet 全系列（Canny/Depth/Pose/Tile/IP-Adapter）
- [ ] **Day 7**: LoRA 使用 + 多 LoRA 融合 + LoRA 权重调节

### Phase 3: 高级技术（Day 8-12）
- [ ] **Day 8**: SDXL 架构差异 + Refiner 工作流
- [ ] **Day 9**: LoRA 训练（kohya_ss / sd-scripts）
- [ ] **Day 10**: 自定义节点开发（Python API）
- [ ] **Day 11**: AnimateDiff / SVD 视频生成
- [ ] **Day 12**: Flux / SD3 新架构理解

### Phase 4: 专精方向（Day 13+）
- [ ] 模型合并（Model Merging）原理与实操
- [ ] Textual Inversion / DreamBooth
- [ ] ComfyUI API 自动化 + 批量任务
- [ ] 性能优化（TensorRT / 量化 / 显存管理）

## 📊 每日学习记录
| 日期 | 主题 | 时长 | 实操 | 笔记 |
|------|------|------|------|------|
| 2026-03-18 | Day 1 - SD算法原理 | 进行中 | - | notes/day01-sd-fundamentals.md |

## 🎯 学习原则
1. **理论+实操并重** — 每个概念都要跑通一遍
2. **写学习笔记** — 用自己的话总结，不是复制粘贴
3. **做实验对比** — 参数调整 → 观察差异 → 理解原理
4. **记录踩坑** — 错误和解决方案都是宝贵经验
