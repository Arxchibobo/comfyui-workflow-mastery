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

### Phase 4: 视频 & 动画专精（Day 13-16）✅ 完成
- [x] **Day 13**: AnimateDiff 运动模块（基于 SD 的视频生成）
- [x] **Day 14**: 自定义节点开发（Python API）
- [x] **Day 15**: Flux / SD3 新架构
- [x] **Day 16**: 综合实战 — 从零编排完整视频生成工作流

### Phase 5: 专精方向（Day 17+）
- [x] 模型合并（Model Merging）
- [x] ComfyUI API 自动化 + 批量任务
- [x] 性能优化（TensorRT / 量化 / 显存管理）

### Phase 6: 高级控制与新方向（Day 20+）
- [x] **Day 20**: 高级条件控制与构图（四种 Conditioning 操作 + 区域提示 + 时间调度 + GLIGEN + 注意力操控）
- [x] **Day 21**: 超分辨率与图像增强（ESRGAN/SwinIR/HAT + 6种ComfyUI超分模式 + 人脸修复）
- [x] **Day 22**: 角色一致性与人脸技术（IP-Adapter/InstantID/PuLID/PhotoMaker/ReActor + 生产级组合工作流）
- [x] **Day 23**: 高级蒙版与自动分割（SAM/SAM2/GroundingDINO/Impact Pack/Florence-2/RMBG + 5种生产级工作流模式）

### Phase 7: 视频后期处理 & 生产管线（Day 24+）
- [x] **Day 24**: 视频后期处理与帧插值（VFI 14算法/RIFE/GIMM-VFI/视频放大SeedVR2/去闪烁/LUT调色/VHS节点/生产级4阶段管线）
- [x] **Day 25**: 高级视频控制技术（镜头运动6DOF/运动控制Motion Control/参考生视频/首尾帧Start-End/Kling V3-O1-O3全系列/ComfyUI工作流模式）
- [x] **Day 26**: 音频生成与多模态工作流（MusicGen/Stable Audio/AudioLDM架构+ComfyUI音频节点全景+TTS/唇同步+多模态管线设计）

### Phase 8: 模型生态深度 & 高级编排（Day 27+）🔧 进行中
- [x] **Day 27**: Wan 视频生成模型深度解析（Wan 2.1→VACE→2.2 MoE→S2V→Animate→2.6全系列 + ComfyUI 原生 vs WanVideoWrapper + 本地部署 + 开源生态对比）
- [x] **Day 28**: SD 微调技术全景 + ComfyUI 工作流工程化（TI/DreamBooth/HN 全对比 + Subgraph/Registry/App Mode）

### Phase 9: Flux 实战（Day 29）✅ 完成
- [x] **Day 29**: Flux 实战工作流生态（模型家族全景 + ControlNet/Fill/Redux 生态 + FLUX.2 Klein + 量化 + 最佳实践）

### Phase 10: 推理加速与前沿（Day 30+）✅ 完成
- [x] **Day 30**: 快速推理与蒸馏技术（四大蒸馏家族 + 12+ 方法 + ComfyUI 配置速查 + 决策树）
- [x] **Day 31**: 图像编辑工作流（InstructPix2Pix / ICEdit / Flux Fill / Flux Kontext / VACE / Qwen-Image-Edit / OmniGen2）
- [x] **Day 32**: 3D 生成与多视角（TripoSR / TripoSG / InstantMesh / Zero123++ / TRELLIS.2 / Hunyuan3D v3.1 / ComfyUI-3D-Pack / 3DGS）

### Phase 11: 生产工程化（Day 33-34）✅ 完成
- [x] **Day 33**: 生产部署与规模化（Docker / Serverless / 六大云平台 / Manager v2 / 监控 / 安全 / 成本）
- [x] **Day 34**: 多模型编排与真实生产管线（五种编排模式 / 电商/短视频/漫画/头像案例 / 批量处理 / CI-CD）

### Phase 12: 前沿与总结（Day 35-36）✅ 完成
- [x] **Day 35**: 2026 前沿趋势（Nodes 2.0 / DiT统一化 / 实时生成 / Blackwell / AI Agent）
- [x] **Day 36**: 毕业总结 — 知识图谱 + 速查手册 + 能力自评 🎓

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
| 3/21 | Day16 综合实战视频管线 | ~1.5h | 4实验(3模型I2V对比+首尾帧) | 1个笔记+4个工作流/脚本 |
| 3/21 | Day17 模型合并 | ~1h | 概念图(¥0.03) | 1个笔记+2个工作流JSON |
| 3/22 | Day18 API自动化+批量任务 | ~1h | 3张批量图(¥0.09) | 1个笔记+1个生产级脚本 |
| 3/22 | Day19 性能优化 | ~1h | 概念图(¥0.03) | 1个笔记 |
| 3/22 | Day20 高级条件控制与构图 | ~1h | 2个实验(¥0.06) | 1个笔记 |
| 3/22 | Day21 超分辨率与图像增强 | ~1h | 2个放大实验(¥0.20) | 1个笔记 |
| 3/22 | Day22 角色一致性与人脸技术 | ~1h | 3个实验(¥0.09) | 1个笔记 |
| 3/22 | Day23 高级蒙版与自动分割 | ~1h | 3个实验(¥0.09) | 1个笔记 |
| 3/22 | Day24 视频后期处理与帧插值 | ~1h | 3个实验(¥0.44) | 1个笔记 |
| 3/22 | Day25 高级视频控制技术 | ~1h | 3个实验(¥0.56) | 1个笔记 |
| 3/22 | Day26 音频生成与多模态工作流 | ~1h | 2个实验(¥0.156) | 1个笔记 |
| 3/23 | Day27 Wan视频生成深度解析 | ~1h | 3个实验(¥1.29) | 1个笔记 |
| 3/23 | Day28 微调技术全景+工作流工程化 | ~1h | 1个实验(¥0.03) | 1个笔记 |
| 3/23 | Day29 Flux实战工作流生态 | ~1h | 2个实验(¥0.06) | 1个笔记+2个工作流JSON |
| 3/23 | Day30 快速推理与蒸馏技术 | ~1h | 1个实验(¥0.03) | 1个笔记+2个工作流JSON |
| 3/23 | Day31 图像编辑工作流 | ~1h | 3个实验(¥0.11) | 1个笔记 |
| 3/23 | Day32 3D生成与多视角 | ~1h | 3个实验(¥1.23) | 1个笔记 |
| 3/23 | PostGrad#4 Seedream+编辑→视频 | ~0.5h | 5个实验(¥0.47) | 1个笔记 |
| 3/23 | Day33 生产部署与规模化 | ~0.5h | — | 1个笔记(16KB) |
| 3/23 | Day34 多模型编排与生产管线 | ~0.5h | — | 1个笔记(12KB) |
| 3/23 | Day35 2026前沿趋势 | ~0.5h | — | 1个笔记(8KB) |
| 3/23 | Day36 毕业总结🎓 | ~0.5h | — | 1个笔记(8KB) |
