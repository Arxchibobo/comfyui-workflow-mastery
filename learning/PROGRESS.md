# ComfyUI 学习进度追踪

## 当前状态
- **当前阶段**: Phase 3 - 高级技术
- **当前天数**: Day 8 完成 → SDXL 架构差异 + Refiner 工作流，下一步 Day 9
- **上次学习时间**: 2026-03-21 00:03 UTC
- **累计学习轮数**: 15

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
| 13 | 2026-03-20 20:03 | Day6-Tile+IP-Adapter+多CN组合 | Tile ControlNet(局部语义感知/细节幻觉/Prompt冲突处理/三阶段超分管线ESRGAN→Tile→频率混合)+IP-Adapter架构(解耦双交叉注意力/CLIP ViT编码/22M参数/Plus vs FaceID变体)+多ControlNet组合(链式连接/区域分工vs多维控制/权重策略/start-end分时段/IP-Adapter+ControlNet天然兼容) | day06-tile-ipadapter-multi-controlnet.md + controlnet/tile-upscale.json + ip-adapter-style-transfer.json + triple-control-ipadapter-depth-pose.json |
| 14 | 2026-03-20 22:03 | Day7-LoRA基础+多LoRA融合 | LoRA数学原理(低秩分解W=W₀+α/r·B·A/参数压缩66x)+LyCORIS全家族(LoCon/LoHa/LoKR/DoRA/DyLoRA对比)+ComfyUI源码(load_lora_for_models/Clone+Patch延迟应用/KeyMapping多格式适配/weight_adapter统一系统/BypassLoRA)+多LoRA堆叠(线性叠加/model vs clip分离调优/冲突诊断)+strength对比实验+model×clip网格实验+API批量sweep脚本 | day07-lora-fundamentals.md + lora/single-lora.json + multi-lora-chain.json + lora-strength-comparison.json + model-vs-clip-strength-grid.json + lora_strength_sweep.py |
| 15 | 2026-03-21 00:03 | Day8-SDXL架构+Refiner工作流 | SDXL架构深度(2.6B U-Net/异构Transformer[0,2,10]/移除8x层)+双编码器(CLIP-L 768d+OpenCLIP-bigG 1280d=2048d拼接/Pooled Embedding)+微条件三件套(c_size/c_crop/c_ar Fourier编码→timestep)+CLIPTextEncodeSDXL源码(text_g/text_l分离/token长度补齐)+SDXL-VAE(batch256+EMA)+Refiner(ascore条件/只用OpenCLIP-bigG/step分割交接/80-20推荐比例)+社区共识(fine-tune替代/LoRA不兼容)+分辨率推荐表+SD1.5对照 | day08-sdxl-architecture-refiner.md + sdxl/sdxl-base-refiner-step-split.json + sdxl-micro-conditioning-experiment.json + refiner-ratio-comparison.json + sdxl_refiner_sweep.py |

## Day 7 待做 (LoRA 使用 + 多 LoRA 融合 + 权重调节)
- [x] LoRA 数学原理
  - [x] 低秩分解 W = W₀ + α/r · B·A，参数量压缩原理
  - [x] alpha 与 rank 的关系（有效缩放 = α/r）
  - [x] 在 SD 中的应用位置（交叉注意力层）
- [x] LoRA 变体家族（LyCORIS）
  - [x] LoCon（扩展到卷积层）
  - [x] LoHa（Hadamard 积，4 矩阵分解）
  - [x] LoKR（Kronecker 积）
  - [x] DoRA（方向+幅度分解）
  - [x] DyLoRA（动态 rank）
- [x] ComfyUI LoRA 源码深度分析
  - [x] load_lora_for_models() 完整流程
  - [x] Clone + Patch 延迟应用机制
  - [x] Key Mapping 系统（适配 kohya/OneTrainer/diffusers 等格式）
  - [x] weight_adapter 统一适配器系统
  - [x] Bypass LoRA 新模式
- [x] 多 LoRA 堆叠原理与实践
  - [x] 链式加载机制（线性叠加 W = W₀ + Σsᵢ·ΔWᵢ）
  - [x] 权重调节策略（model vs clip 分离控制）
  - [x] 冲突诊断与解决方案
  - [x] 区域化 LoRA 应用概念
- [ ] LoRA 与不同模型架构的差异（SD1.5/SDXL/Flux）实操验证
  - [x] 理论分析完成
  - [ ] 待有 GPU 环境时实操

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
- [x] Tile / IP-Adapter 高级 ControlNet
  - [x] Tile ControlNet 用于超分辨率
  - [x] IP-Adapter 图像风格迁移
- [x] 多 ControlNet 组合使用
  - [x] 权重调节与冲突处理

## Day 8 待做 (SDXL 架构差异 + Refiner 工作流)
- [x] SDXL 架构深度分析
  - [x] U-Net 参数对比（860M vs 2.6B）
  - [x] 异构 Transformer 分布 [0, 2, 10] vs SD1.5 的 [1,1,1,1]
  - [x] 移除 8x 下采样层级的设计考量
- [x] 双文本编码器系统
  - [x] CLIP ViT-L/14 (768d) + OpenCLIP ViT-bigG/14 (1280d)
  - [x] 拼接方式：逐 token 拼接 → 2048 维 cross-attention
  - [x] Pooled Embedding 的作用（加到 timestep embedding）
  - [x] ComfyUI CLIPTextEncodeSDXL 源码分析（text_g/text_l 分离）
- [x] SDXL 微条件系统（Micro-Conditioning）
  - [x] Size Conditioning c_size = (h_orig, w_orig)
  - [x] Crop Conditioning c_crop = (crop_top, crop_left)
  - [x] Multi-Aspect Conditioning c_ar = (h_target, w_target)
  - [x] Fourier Feature Encoding → timestep embedding 注入机制
- [x] SDXL-VAE 改进（batch 256 + EMA 权重追踪）
- [x] SDXL Refiner 深度解析
  - [x] Refiner 架构（只用 OpenCLIP-bigG，aesthetic score 条件）
  - [x] CLIPTextEncodeSDXLRefiner 源码（ascore 参数）
  - [x] Base→Refiner 交接机制（KSampler Advanced step 分割）
  - [x] 交接比例对比（60/40 ~ 90/10 的效果差异）
  - [x] add_noise/return_with_leftover_noise 的关键作用
- [x] Refiner 是否还值得用（2024-2025 社区共识总结）
  - [x] Fine-tune 模型替代 + LoRA 不兼容问题
  - [x] 现代替代方案（Hires Fix / Tile ControlNet / Flux）
- [x] SDXL 推荐分辨率与宽高比表
- [x] SDXL vs SD1.5 工作流差异对照表（节点/参数/prompt 策略）
