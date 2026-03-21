# ComfyUI 学习进度追踪

## 当前状态
- **当前阶段**: Phase 4 - 视频 & 动画专精 (学习路径已纠正)
- **当前天数**: Day 15 — Flux / SD3 新架构
- **上次学习时间**: 2026-03-21 16:03 UTC
- **累计学习轮数**: 23

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
| 16 | 2026-03-21 06:03 | Day9-LoRA训练管线+参数深度 | 训练工具生态(sd-scripts/kohya_ss/OneTrainer/SimpleTuner/ai-toolkit)+数据准备全流程(质量>数量/SD1.5:30-100/SDXL:20-50/Flux:10-30/Tag vs NL打标/触发词/正则化)+核心参数深度(dim/alpha/分层LR/6种Optimizer/6种Scheduler/NoiseOffset/MinSNR/GradCheckpoint)+训练循环伪代码(ε-pred vs v-pred/MinSNR数学)+三架构对比(SD1.5/SDXL/Flux全维度)+Loss曲线诊断+三套快速启动配置 | day09-lora-training.md + lora-training/sd15-character-lora-config.toml + sdxl-style-lora-config.toml + flux-character-lora-config.toml + lora-strength-evaluation.json + prepare_dataset.py |
| 19 | 2026-03-21 08:30 | Day11-LTX-2.3工作流深度 | LTX-2.3全47节点体系分析(5类:加载/潜空间/条件/采样/后处理)+两阶段管线原理(latent upscale>pixel upscale)+sigma序列分析(蒸馏从0.85/完整从1.0)+I2V两模式对比(Inplace vs ConditionOnly)+IC-LoRA Union Control原理+Wan 2.6 T2V+Ref2V实验+LTX vs Wan架构对比 | day11-ltx2-workflow-deep-dive.md |
| 20 | 2026-03-21 10:03 | Day12-ComfyUI API节点体系 | Partner Nodes架构(ApiEndpoint/SynchronousOp/PollingOp三层抽象+AUTH_TOKEN_COMFY_ORG+VIDEO原生类型)+Kling 3.0全节点体系(T2V/I2V/Audio/MotionControl/Element Binding)+Seedance Pro(1080p/cameraFixed/首尾帧)+Veo 3.1(8s固定/800字符)+第三方节点生态(fal-API/Kie-API/wavespeed)+混合工作流范式+Kling vs Veo对比实验(¥0.75 vs ¥0.10) | day12-comfyui-api-node-ecosystem.md |
| 22 | 2026-03-21 14:03 | Day14-自定义节点开发 | 节点类4必需属性(CATEGORY/INPUT_TYPES/RETURN_TYPES/FUNCTION)+INPUT_TYPES三级字典(required/optional/hidden)+全数据类型系统(14种)+执行控制(缓存/IS_CHANGED/VALIDATE_INPUTS)+高级特性7项(自定义类型/通配符/动态输入/Lazy Eval/ExecutionBlocker/Node Expansion/List处理)+前后端通信(send_sync/aiohttp路由/JS扩展)+V3规范+Vue迁移+真实世界4种模式分析 | day14-custom-node-development.md |
| 23 | 2026-03-21 16:03 | Day15-Flux/SD3新架构 | Rectified Flow数学(v-prediction vs ε-prediction/线性插值/OT路径/Logit-Normal采样)+SD3 MMDiT架构(Joint Attention with Separate Weights/三编码器CLIP-L+G+T5/adaLN/QKV RMSNorm)+SD3.5变体对比(Medium 2.5B MMDiT-X/Large 8B/Turbo ADD蒸馏)+Flux.1架构逆向(19 Double-Stream+38 Single-Stream/渐进融合设计/RoPE位置编码/16通道VAE)+Flux变体(Pro/Dev Guidance Distillation/Schnell LADD)+ComfyUI工作流差异(SD3专用节点/Flux无negative prompt/CFG=1/FluxGuidance)+LoRA训练差异+社区生态对比+架构概念图实验 | day15-flux-sd3-new-architectures.md |

## Day 9 进度 (LoRA 训练 — kohya_ss / sd-scripts)
- [x] LoRA 训练工具生态概览
  - [x] sd-scripts / kohya_ss GUI / OneTrainer / SimpleTuner / ai-toolkit 对比
  - [x] sd-scripts 仓库结构分析（train_network.py / networks/lora.py / library/）
- [x] 训练管线完整流程
  - [x] 数据收集→筛选→预处理→打标→目录结构→训练→评估
  - [x] 训练步数计算公式（图片数 × 重复 × epoch / batch_size）
- [x] 数据准备深度解析
  - [x] 图片质量标准与数量推荐（SD1.5/SDXL/Flux 差异）
  - [x] 多样性维度（角度/姿势/光照/背景/距离）
  - [x] 打标方法（Tag 式 vs 自然语言 / WD14 vs BLIP / 触发词策略）
  - [x] kohya 目录结构（repeats_class_token 格式）
  - [x] 正则化图片的作用与使用方法
- [x] 训练核心参数深度解析
  - [x] Network Dimension (rank) 与 Network Alpha 关系
  - [x] 分层学习率（unet_lr vs text_encoder_lr）
  - [x] Optimizer 全对比（AdamW8bit/Adafactor/Prodigy/CAME/Lion/DAdapt）
  - [x] LR Scheduler 全系列（constant/cosine/cosine_with_restarts/warmup/linear/polynomial）
  - [x] Batch Size / Noise Offset / Min-SNR Gamma / Gradient Checkpointing / Cache Latents / Mixed Precision / Clip Skip
- [x] 训练循环内部机制
  - [x] train_network.py 核心训练循环伪代码重建
  - [x] 损失函数（ε-prediction vs v-prediction）
  - [x] Min-SNR Weighting 数学原理与代码实现
- [x] SD1.5 vs SDXL vs Flux 训练差异对比
  - [x] 脚本/模块/分辨率/VRAM/dim/LR/TE/数据集规模/标注风格/容错性全维度对比
  - [x] Flux flow-matching 特殊性（连续 t / velocity field / DiT / lora_flux.py）
  - [x] SDXL 双 TE / 微条件 / bucket 特殊考量
- [x] 训练诊断与质量评估
  - [x] Loss 曲线解读（理想/过拟合/欠拟合）
  - [x] 常见问题诊断表（6 种症状→原因→方案）
  - [x] 推理测试清单（权重/灵活性/兼容性/负面/风格迁移 5 维度）
- [x] 新手快速启动配置（SD1.5角色/SDXL风格/Flux角色 三套推荐参数）
- [ ] train_network.py 源码逐行分析（下一轮续）
- [ ] 实际训练演练（需 GPU 环境）

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

## Day 11 进度 (LTX-2.3 视频工作流深度)
- [x] LTX-2.3 模型架构与规格梳理
  - [x] 22B DiT + Gemma 3 12B 文本编码器 + 新 VAE + 原生音频
  - [x] vs LTX-2.0 的 6 大改进
- [x] ComfyUI 节点体系完整分析（5 类 47 节点）
  - [x] 模型加载类（CheckpointLoader / LTXAVTextEncoderLoader / AudioVAELoader）
  - [x] 潜空间创建类（EmptyLTXVLatentVideo / EmptyLatentAudio / ConcatAVLatent）
  - [x] 条件编码类（LTXVConditioning / ImgToVideoInplace / ConditionOnly / GemmaAPI）
  - [x] 采样类（SamplerCustomAdvanced / CFGGuider / MultimodalGuider / ManualSigmas）
  - [x] 后处理类（SeparateAVLatent / LatentUpsampler / VAEDecodeTiled / CreateVideo）
- [x] 两阶段管线原理深入
  - [x] Stage 1 低分辨率快速生成 + Stage 2 潜空间上采样精炼
  - [x] Sigma 序列分析（蒸馏 vs 完整模式差异）
- [x] I2V 两种模式对比（Inplace vs ConditionOnly）
- [x] IC-LoRA Union Control 工作原理
- [x] LTX vs Kling vs Seedance vs AnimateDiff 集成方式对比
- [x] RunningHub 实验
  - [x] 实验 15: Wan 2.6 T2V（金龙穿雾山，45s/¥0.38）
  - [x] 实验 16: Wan 2.6 Ref2V（赛博朋克狗参考生视频，75s/¥0.40）
- [x] LTX-2.3 vs Wan 2.6 架构对比（DiT + Flow Matching 共性与差异）
- [ ] ComfyUI API 调用 LTX 完整实操（需本地 GPU 环境）

## Day 12 进度 (ComfyUI API 节点体系 — Partner Nodes / Kling / Seedance / Veo3.1)
- [x] Partner Nodes 架构总览
  - [x] Partner Nodes 设计理念（内置/统一认证/Opt-in/Credits）
  - [x] 技术架构（ApiEndpoint/SynchronousOperation/PollingOperation 三层抽象）
  - [x] 源码分析（以 KlingTextToVideoNode 为例的三步模式）
  - [x] AUTH_TOKEN_COMFY_ORG 隐藏参数注入机制
  - [x] VIDEO 原生数据类型（PR #7844）
- [x] 视频生成 Partner Nodes 全景分析
  - [x] Kling 3.0 节点体系（T2V/I2V/Audio/MotionControl/CameraControl/StartEnd）
  - [x] Kling 3.0 Motion Control + Element Binding 面部一致性
  - [x] Seedance Pro 节点体系（T2V/I2V/FirstLastFrame/1080p/cameraFixed）
  - [x] Veo 3.1 节点（Google DeepMind / 8s固定 / 800字符限制）
  - [x] MiniMax Hailuo / Luma Ray2 / PixVerse / Pika / Wan 2.6 概览
- [x] 三大模型 ComfyUI 集成深度对比（Kling vs Seedance vs Veo）
- [x] 第三方 API 节点生态
  - [x] ComfyUI-fal-API / ComfyUI-Kie-API / wavespeed-comfyui / ComfyUI-KLingAI-API
  - [x] Partner Nodes vs 第三方节点全维度对比
  - [x] Headless API Key Integration 机制
- [x] 视频工作流编排模式
  - [x] 三层集成层次（封装API / Partner Nodes / 本地模型）
  - [x] 混合工作流范式（Local ControlNet + Cloud API + Local Upscale）
- [x] RunningHub 实验
  - [x] 实验 17: Kling 3.0 Pro I2V（samurai 动画化, 150s/¥0.75）
  - [x] 实验 18: Veo 3.1 Pro I2V（同图对比, 125s/¥0.10）
  - [x] Kling 3.0 vs Veo 3.1 全维度对比分析

## Day 13 进度 (AnimateDiff 运动模块)
- [x] AnimateDiff 论文深度解析 (ICLR 2024 Spotlight)
  - [x] 三阶段训练流程（Domain Adapter → Motion Module → MotionLoRA）
  - [x] Motion Module 架构（Temporal Transformer + 正弦位置编码）
  - [x] 时间自注意力机制（沿帧维度 self-attention，冻结空间权重）
  - [x] 即插即用原理（时间/空间注意力解耦）
  - [x] 维度变换 [B,C,H,W] → [B×H×W, C, F] → temporal attn → 恢复
- [x] AnimateDiff 版本演进（v1 → v2 → v3 → SDXL）
  - [x] v2 MotionLoRA（8种镜头运动，每个~74MB）
  - [x] v3 SparseCtrl（RGB/涂鸦条件编码器，关键帧控制）
  - [x] 社区微调模型（Stabilized/TemporalDiff/FP16 版本）
- [x] ComfyUI-AnimateDiff-Evolved 节点系统
  - [x] 核心节点分类（Motion Model / Context Options / Sample Settings / MotionLoRA）
  - [x] Context Options 滑动窗口机制（Standard vs Looped Uniform）
  - [x] FreeNoise 噪声优化原理（重复+shuffle > 独立随机）
  - [x] Gen2 多运动模型堆叠
  - [x] 高级功能（AnimateLCM / CameraCtrl / PIA / ContextRef / NaiveReuse）
  - [x] 典型工作流结构（基础 T2V / 带 ControlNet / 带 MotionLoRA）
- [x] AnimateDiff 在现代视频生成中的定位
  - [x] vs Wan 2.2/2.6、LTX-2、Kling/Seedance 全维度对比
  - [x] 优势：极强定制性 + ControlNet兼容 + 低VRAM + 社区生态
  - [x] 局限：画质上限受 SD1.5/SDXL 限制 + 运动复杂度有限
  - [x] 现代 ComfyUI 视频工作流四层策略
- [x] RunningHub 实验
  - [x] 实验 19: 关键帧图像生成 + Seedance 动画化（模拟 SparseCtrl 流程）
  - [x] 实验 20: Wan 2.6 T2V 对比（40s/¥0.38）
  - [x] AnimateDiff 工作流 vs 现代 API 模型的成本/质量/控制力对比

## Day 14 进度 (自定义节点开发 — Python API)
- [x] 节点类四个必需属性深度解析
  - [x] CATEGORY / INPUT_TYPES / RETURN_TYPES / FUNCTION 完整规范
  - [x] INPUT_TYPES 三级字典结构（required/optional/hidden）
  - [x] 所有内置数据类型（IMAGE/LATENT/MASK/MODEL/CLIP/VAE/CONDITIONING/NOISE/SAMPLER/SIGMAS/GUIDER/AUDIO + Python 原生 INT/FLOAT/STRING/BOOLEAN + COMBO）
  - [x] Hidden Inputs 特殊值（UNIQUE_ID/PROMPT/EXTRA_PNGINFO/DYNPROMPT）
  - [x] OPTIONS 参数全集（default/min/max/step/forceInput/defaultInput/lazy/rawLink/multiline/placeholder/dynamicPrompts/label_on/label_off）
- [x] 节点注册与生命周期
  - [x] 目录结构规范
  - [x] __init__.py 标准模板（NODE_CLASS_MAPPINGS/NODE_DISPLAY_NAME_MAPPINGS/WEB_DIRECTORY）
  - [x] ComfyUI 加载流程（扫描 → import → 检查导出 → 注册）
  - [x] comfy-cli scaffold 工具
- [x] 执行控制机制
  - [x] 缓存系统原理（OUTPUT_NODE 标记 + 反向依赖追踪）
  - [x] IS_CHANGED 正确用法（⚠️ 不能返回 bool！NaN 技巧）
  - [x] VALIDATE_INPUTS（常量验证 + 类型验证 + input_types 参数）
  - [x] SEARCH_ALIASES
- [x] 高级特性
  - [x] 自定义数据类型（forceInput 必需）
  - [x] 通配符输入（"*" + VALIDATE_INPUTS 跳过验证）
  - [x] 动态创建输入（ContainsAnyDict 技巧 + **kwargs）
  - [x] Lazy Evaluation（lazy 标记 + check_lazy_status 方法）
  - [x] ExecutionBlocker（静默阻断 vs 错误消息阻断 + 传播规则）
  - [x] Node Expansion（GraphBuilder + 子图缓存优势）
  - [x] List 处理（INPUT_IS_LIST / OUTPUT_IS_LIST / 默认逐元素处理）
- [x] 前后端通信
  - [x] Server → Client（PromptServer.send_sync）
  - [x] Client → Server（自定义 aiohttp 路由 @routes.post/get）
  - [x] 前端 JS 扩展（app.registerExtension / addEventListener / nodeCreated）
  - [x] WEB_DIRECTORY 规范（只 serve .js 文件）
- [x] ComfyUI 内置 API 路由全集（20+ 端点）
- [x] WebSocket 消息类型（status/execution_start/executing/progress/executed）
- [x] Nodes V3 规范分析
  - [x] V3 解决的核心问题（稳定性/依赖冲突/动态IO/模型管理/未来扩展）
  - [x] V3 Schema 对比（INPUT_TYPES → DEFINE_SCHEMA）
  - [x] API 版本化策略
  - [x] Nodes 2.0 Vue 迁移（LiteGraph.js → Vue.js 组件渲染）
- [x] 真实世界模式分析
  - [x] API 代理节点模式
  - [x] 图像处理管线模式
  - [x] 条件路由节点模式（Lazy + Switch）
  - [x] 模型加载/修补节点模式（clone + patch）
  - [x] 最佳实践总结（8 条）
- [x] RunningHub 实验 #21（架构概念图生成）

## Day 15 进度 (Flux / SD3 新架构)
- [x] 从 U-Net 到 DiT 的架构范式转移
  - [x] SD 架构演进时间线（SD1.5 → SDXL → SD3 → Flux）
  - [x] U-Net 瓶颈分析（可扩展性/全局上下文/多模态融合/Scaling Law）
- [x] Rectified Flow 训练范式
  - [x] DDPM ε-prediction vs Rectified Flow v-prediction 数学对比
  - [x] 线性插值 x_t = (1-t)x_0 + tx_1（直线 OT 路径）
  - [x] Logit-Normal 时间步采样（偏重中间步）
  - [x] 直线路径优势（误差累积少/步数效率高/理论保证）
- [x] SD3 MMDiT 架构深度解析
  - [x] Joint Attention with Separate Weights（取代 Cross-Attention）
  - [x] QKV 拼接 → 联合注意力 → split → 独立 FFN
  - [x] adaLN（Adaptive Layer Normalization）调制机制
  - [x] QKV RMSNorm 稳定混合精度训练
- [x] SD3 三文本编码器系统
  - [x] CLIP-L (768d) + CLIP-G (1280d) + T5-XXL (4096d)
  - [x] Pooled embedding → timestep / Token embedding → joint attention
  - [x] 训练时 40% dropout → 推理可去掉 T5 省 VRAM
- [x] SD3/SD3.5 版本变体对比
  - [x] SD3 Medium 2B / SD3.5 Medium 2.5B (MMDiT-X) / Large 8B / Large Turbo
  - [x] Turbo 的 ADD（Adversarial Diffusion Distillation）蒸馏
- [x] Flux.1 架构逆向分析（基于 arXiv:2507.09595 论文）
  - [x] 19 Double-Stream Blocks（模态特异性/独立权重/joint attention）
  - [x] 38 Single-Stream Blocks（共享权重/统一序列处理）
  - [x] 渐进融合设计哲学（先分后合）
  - [x] RoPE 位置编码（2D 网格 + 预留时间维度）
  - [x] 16 通道 VAE + Patchify 2×2
  - [x] CLIP-L + T5-XXL 双编码器（去掉 CLIP-G）
- [x] Flux.1 模型变体
  - [x] Pro（API only/完整训练）/ Dev（Guidance Distillation/CFG=1）/ Schnell（LADD/1-4步）
  - [x] Guidance Distillation 机制（guidance_scale 作为模型输入/单次推理替代 CFG）
- [x] SD3 vs Flux 全维度对比
  - [x] 架构/参数/编码器/VAE/位置编码/训练方式/性能
  - [x] 社区生态对比（LoRA/ControlNet/活跃度）
  - [x] 2025-2026 趋势判断
- [x] ComfyUI 工作流差异详解
  - [x] SD3 专用节点（CLIPTextEncodeSD3/EmptySD3LatentImage）
  - [x] Flux 工作流（FluxGuidance/DualCLIPLoader/CFG=1/euler sampler）
  - [x] Flux 无 negative prompt 的设计原因
- [x] Flux LoRA 训练与 SD3 LoRA 差异对比
- [x] RunningHub 实验 #22（架构对比概念图生成）
