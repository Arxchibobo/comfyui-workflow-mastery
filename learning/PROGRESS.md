# ComfyUI 学习进度追踪

## 当前状态
- **当前阶段**: Phase 2 - 核心工作流实操
- **当前天数**: Day 6 进行中（ControlNet 基础原理 + Canny/Depth/Pose 完成）
- **上次学习时间**: 2026-03-20 18:03 UTC
- **累计学习轮数**: 12

## Day 1 进度 (SD 核心算法原理)
- [x] DDPM 扩散模型原理（前向/反向、重参数化）
- [x] Stable Diffusion LDM 架构（VAE + U-Net + CLIP）
- [x] 采样算法概览（Euler/Heun/DDIM/DPM++）
- [x] CFG 原理
- [x] SD 版本演进（1.5 → SDXL → SD3）
- [x] ComfyUI 源码阅读（execution.py + graph.py）
- [x] 生成 SD 架构图
- [x] 采样器/CFG/步数对比实验（同 prompt 同 seed 系统性对比）
- [x] 阅读 DDPM 原始论文 arXiv:2006.11239
- [x] 阅读 LDM 原始论文 arXiv:2112.10752

## Day 2 待做 (Latent Space & Sampling 深入)
- [x] Latent Space 操作原理（插值、算术、编辑）
- [x] Sampling 算法数学细节（ODE vs SDE, 收敛性分析）
- [x] Euler vs DPM++ 2M vs DDIM 数学推导对比
- [x] Noise Schedule 设计（linear vs cosine vs karras）
- [x] 手搭 text2img 工作流并理解每个参数

## Day 3 待做 (ComfyUI 架构深入)
- [x] ComfyUI 节点系统源码（nodes.py 全系列）
  - [x] 节点注册机制（INPUT_TYPES / RETURN_TYPES / FUNCTION / CATEGORY）
  - [x] 数据类型系统（MODEL/CLIP/VAE/CONDITIONING/LATENT/IMAGE 等）
  - [x] 节点发现与加载流程（startup → scan → register）
- [x] 自定义节点加载机制
  - [x] custom_nodes/ 目录扫描与 __init__.py 规范
  - [x] NODE_CLASS_MAPPINGS / NODE_DISPLAY_NAME_MAPPINGS
  - [x] 常见自定义节点包结构分析
- [x] Execution engine 深入（cache/lazy/parallel）
  - [x] execution.py 执行流程：validate → topological sort → execute
  - [x] 缓存机制：哪些节点会被重新执行，哪些走缓存
  - [x] Lazy evaluation 与 parallel execution 策略
- [x] ComfyUI API 调用流程
  - [x] WebSocket 通信协议（/ws, /prompt, /history, /view）
  - [x] 进度回调与图片返回机制
  - [x] 队列管理与并发控制

## 学习轮次日志
| 轮次 | 时间 (UTC) | 主题 | 完成内容 | 笔记文件 |
|------|-----------|------|---------|----------|
| 1 | 2026-03-18 10:00 | Day1-SD基础 | 理论全部+源码阅读+架构图 | day01-sd-fundamentals.md |
| 2 | 2026-03-18 12:00 | Day1-论文精读 | DDPM论文(ELBO→简化loss→Langevin连接)+LDM论文(两阶段解耦+CrossAttn+压缩比分析) | day01-sd-fundamentals.md §7 |
| 3 | 2026-03-18 14:03 | Day1完成+Day2开始 | 采样器/CFG/步数系统对比(分类体系+决策树)+Latent Space操作(SLERP/LERP/算术/编辑/ComfyUI节点) | day01-sd-fundamentals.md §8 + day02-latent-space-sampling.md §1 |
| 4 | 2026-03-18 18:03 | Day2-Sampling深入 | ODE vs SDE统一框架(Score-based SDE/PF-ODE/Anderson定理)+采样器数学推导(DDIM=一阶ODE/Euler等价/Heun/DPM++2M多步法精确公式)+Noise Schedule(Linear/Cosine/Karras设计原理与数学对比)+收敛性分析(LTE/guided instability/data prediction解决方案) | day02-latent-space-sampling.md §2-5 |
| 5 | 2026-03-18 20:03 | Day2完成-Text2Img工作流 | 6节点完整拓扑解析(Checkpoint/EmptyLatent/CLIPEncode/KSampler/VAEDecode/SaveImage)+KSampler全参数深度解析(seed/steps/cfg/sampler/scheduler/denoise交互效应)+API JSON格式+分辨率匹配表+采样器决策树+SD1.5/SDXL/Flux推荐配置 | day02-latent-space-sampling.md §6 + sample-workflows/basic/text2img.json |
| 6 | 2026-03-18 22:03 | Day3-节点系统+自定义节点 | 节点注册机制4要素(INPUT_TYPES/RETURN_TYPES/FUNCTION/CATEGORY)+数据类型系统(13种核心类型+IO枚举)+自定义节点加载流程(init_extra_nodes容错扫描)+graph.py深度分析(DynamicPrompt/TopologicalSort/ExecutionList/UX优先级调度)+Lazy Eval/OutputNode/PromptServer通信模式 | day03-comfyui-architecture.md §1-8 |
| 8 | 2026-03-20 11:33 | Day4-采样器对比实验 | 6种采样器系统性对比实验设计(euler/dpmpp_2m/dpmpp_sde/ddim/heun/uni_pc)+控制变量方案+可运行工作流JSON(共享前端+6独立采样管线)+社区研究总结+预期结果分析 | day04-sampler-experiments.md + sampler-comparison.json |
| 9 | 2026-03-20 12:03 | Day4-模型×采样器矩阵+Scheduler深度分析 | SD1.5/SDXL/Flux三架构对比(U-Net vs DiT/DDPM vs Rectified Flow/CFG差异)+各模型最优采样器推荐表+全9种Scheduler数学公式源码分析(karras/exponential/beta/normal/simple/ddim_uniform/sgm_uniform/linear_quadratic/kl_optimal)+Scheduler×Sampler兼容性矩阵+CFG×采样器交互分析+步数-质量曲线+快速决策树 | day04-model-sampler-matrix.md + scheduler-sampler-cross-sdxl.json + flux-vs-sdxl-sampler-compare.json + steps-quality-curve.json |
| 10 | 2026-03-20 14:03 | Day4完成-批量生成+质量评估 | FID/KID/IS分布级指标+LPIPS/SSIM/NIQE图像级指标+CLIP Score/ImageReward/HPS v2对齐级指标+指标选择决策树+3种ComfyUI批量方法(batch_size/RepeatLatentBatch/API脚本)+完整API批量生成Python脚本+自动质量评估脚本(NIQE/CLIP/ImageReward) | day04-batch-generation-quality-eval.md + batch-seed-variants.json + batch_generate_evaluate.py + evaluate_quality.py |
| 11 | 2026-03-20 16:03 | Day5-Img2Img+Inpainting+Outpainting | Img2Img原理(VAEEncode vs EmptyLatent/denoise sigma截断数学/参数速查)+Inpainting三种方法对比(SetLatentNoiseMask/VAEEncodeForInpaint/InpaintModelConditioning源码分析)+noise_mask全管线传递+mask灰色像素技巧+Outpainting(ImagePadForOutpaint源码/feathering/最佳实践)+denoise对比实验设计 | day05-img2img-inpainting-outpainting.md + img2img.json + inpainting-simple.json + inpainting-vae.json + outpainting.json + denoise-comparison.json |
| 12 | 2026-03-20 18:03 | Day6-ControlNet基础+三大经典 | ControlNet架构(零卷积/双副本/hint编码/权重注入)+ComfyUI源码分析(ControlBase/ControlNet/get_control/control_merge/ControlNetApplyAdvanced)+v1.1全14模型列表+Canny/Depth/OpenPose深度解析(原理/预处理器/strength调优/场景)+多ControlNet合并机制(信号相加)+start/end_percent策略+跨模型对比(SD1.5/SDXL/Flux)+Union ControlNet | day06-controlnet-fundamentals.md + controlnet/canny-controlnet.json + depth-controlnet.json + openpose-controlnet.json + multi-controlnet-depth-pose.json + canny-strength-comparison.json |

## Day 4 待做 (Text2Img 全流程 — 各种采样器对比实验)
- [x] 采样器系统性对比实验设计
  - [x] 控制变量法：固定 seed/prompt/模型，只变采样器
  - [x] 对比维度：生成质量、速度、步数敏感度、CFG 兼容性
- [x] SD 1.5 vs SDXL vs Flux 采样器行为差异
  - [x] 不同架构对采样器选择的影响
  - [x] 最优采样器×模型组合推荐
- [x] 高级参数调校
  - [x] Scheduler 与 Sampler 的交叉效应（karras/exponential/sgm_uniform）
  - [x] 步数-质量曲线绘制（5/10/15/20/30/50 步对比）
  - [x] CFG Scale 与采样器的交互（某些采样器对高 CFG 更稳定）
- [x] 批量生成与质量评估方法论
  - [x] 如何科学评估生成质量（FID/CLIP Score 原理）
  - [x] ComfyUI 批量生成工作流设计

## Day 5 待做 (Img2Img、Inpainting、Outpainting)
- [x] Img2Img 原理与 denoise 参数深入
  - [x] VAEEncode 流程 vs EmptyLatentImage 区别
  - [x] denoise 值对内容保持 vs 创意生成的平衡
  - [x] 最佳 denoise 范围（风格迁移/局部修改/大幅重绘）
- [x] Inpainting 原理与遮罩处理
  - [x] SetLatentNoiseMask 机制
  - [x] Inpainting 专用模型 vs 通用模型 + mask
  - [x] 遮罩羽化与边缘融合技巧
- [x] Outpainting 扩展画布
  - [x] Padding + Inpaint 方法
  - [x] 分辨率与构图一致性挑战

## Day 6 待做 (ControlNet 全系列)
- [x] ControlNet 基础原理
  - [x] ControlNet 架构（零卷积、权重注入方式）
  - [x] Preprocessor 与 ControlNet 模型的关系
- [x] Canny / Depth / Pose 三大经典 ControlNet
  - [x] 每种的最佳使用场景
  - [x] preprocessor 参数调优
- [ ] Tile / IP-Adapter 高级 ControlNet
  - [ ] Tile ControlNet 用于超分辨率
  - [ ] IP-Adapter 图像风格迁移
- [ ] 多 ControlNet 组合使用
  - [ ] 权重调节与冲突处理
