# ComfyUI 学习进度追踪

## 当前状态
- **当前阶段**: 🎓 Post-Graduation Labs
- **当前天数**: Day 36+ — 毕业后实操巩固
- **上次学习时间**: 2026-03-23 22:03 UTC
- **累计学习轮数**: 50
- **状态**: 🎓 毕业！36天完整学习旅程结束 → 进入实操巩固阶段

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
| 24 | 2026-03-21 18:03 | Day16-综合实战视频管线 | 三阶段管线架构(关键帧→视频→后处理)+四种范式(全本地/混合/全API/RunningHub)+Flux+Kling混合工作流JSON+LTX-2.3两阶段工作流JSON+多分镜管线脚本(storyboard_pipeline.py)+三模型I2V对比(Seedance ¥0.30/Kling ¥0.75/Vidu首尾帧 ¥0.20)+关键帧生成+模型选择决策树+生产级错误处理+管线成本分析 | day16-comprehensive-video-pipeline.md |
| 25 | 2026-03-21 20:03 | Day17-模型合并 | Mode Connectivity/Linear Mode Connectivity理论基础+6种经典方法(Weighted Sum/SLERP/Add Difference/Block Weighted/Task Arithmetic)+3种高级方法(TIES-Merging/DARE/Git Re-Basin)+DARE-TIES组合方法+ComfyUI源码分析(nodes_model_merging.py全11节点+add_patches机制)+SD1.5/SDXL/Flux合并差异+合并策略决策树+最佳实践8条+3个工作流JSON(基础合并/Add Difference/分块合并)+实验#27概念图 | day17-model-merging.md |
| 26 | 2026-03-22 00:03 | Day18-API自动化+批量任务 | ComfyUI全API端点深度(30+路由/WebSocket 8种消息类型/prompt POST格式)+Python自动化工具生态(官方示例/comfyui_utils/comfy-nodekit/ComfyUI-to-Python/ComfyScript 5库对比)+生产部署方案(SaladTech无状态API/BentoML comfy-pack/Cloud平台)+批量4模式(串行/预提交/多WS并行/分布式)+参数扫描6维度+错误处理5类+生产级batch_api_runner.py(469行/CSV+JSON/重试/OOM恢复)+RunningHub批量实验#28(3风格龙,72.5s,¥0.09) | day18-comfyui-api-automation.md + batch_api_runner.py |
| 27 | 2026-03-22 02:03 | Day19-性能优化 | VRAM三大消耗源(权重/激活/注意力二次方缩放)+精度格式全景(FP32/BF16/FP16/FP8/GGUF Q2-Q8/NF4/NVFP4共8级对比)+GGUF量化深度(city96/block缩放/DiT vs U-Net适配性)+注意力优化5种方法(xFormers/FlashAttn/SageAttn/SDPA/Slicing)+卸载策略4级(TE/VAE/lowvram/novram)+Async Offloading+Pinned Memory(10-50%加速)+TensorRT(2-3x但不兼容LoRA/CN)+torch.compile(30%加速)+Tiled VAE(43%省VRAM)+NVFP4 Nunchaku(3x加速/Blackwell)+ComfyUI Dynamic VRAM+综合决策树(按GPU分4档)+7个性能节点包+实验#29概念图 | day19-performance-optimization.md |
| 28 | 2026-03-22 04:03 | Day20-高级条件控制与构图 | Conditioning数据结构深度(list of [tensor,dict])+四种操作数学本质(Combine=噪声预测级加权平均/Concat=torch.cat(dim=1)突破77token/Average=嵌入空间线性插值/SetArea+Combine=区域分离)+源码分析(nodes.py全8个条件节点+samplers.py的_calc_cond_batch/get_area_and_mult/cfg_function)+区域控制3方案(SetArea矩形+SetMask自由形状+Attention Couple注意力级)+时间维度(SetTimestepRange prompt调度)+GLIGEN接地式布局+CLIP Vision/unCLIP/Style Model+注意力操控(SAG/PAG/SEG/NAG)+ConditioningZeroOut+高级构图模式3种+决策树+实验#30区域构图(¥0.03)+实验#31超长prompt(¥0.03) | day20-advanced-conditioning-composition.md |
| 29 | 2026-03-22 08:03 | Day21-超分辨率与图像增强 | 两类放大方式(插值vs AI模型vs SD重绘)+Spandrel统一加载库(自动架构检测/15+架构)+ImageUpscaleWithModel源码深度(分块处理/OOM自动降级tile÷2/overlap融合/内存估算384x经验系数)+ESRGAN系列(RRDB/Real-ESRGAN真实退化/社区模型6款对比)+SwinIR(窗口自注意力/纹理保真)+HAT(Hybrid Attention SOTA)+6种超分工作流模式(纯模型/生成+放大/Hires Fix/Tile ControlNet/Ultimate SD Upscale/Latent放大)+denoise值调优(0.3-0.5推荐)+人脸修复(CodeFormer fidelity/GFPGAN/FaceDetailer 4步检测-裁剪-重绘-贴回)+CropAndStitch替代方案+三阶段管线最佳实践+模型选择决策树+Topaz放大实验#32#33(Standard vs HiFi V2,各¥0.10) | day21-upscaling-super-resolution.md |
| 30 | 2026-03-22 14:08 | Day22-角色一致性与人脸技术 | 角色一致性技术全景(训练型/零样本/人脸替换/组合4大类)+IP-Adapter架构深度(解耦交叉注意力/CLIP ViT-H→新Cross-Attn分支/22M参数/8种变体全对比)+IP-Adapter FaceID(ArcFace 512d→CLIP空间/Plus V2双路融合/需配套LoRA)+InstantID三组件(InsightFace AntelopeV2+IdentityNet ControlNet+IP-Adapter/零样本SDXL only)+PuLID架构(NeurIPS 2024/对比对齐+闪电T2I双分支训练/最小化模型污染/91%身份精度最高/PuLID-FLUX适配)+PhotoMaker(CVPR 2024/堆叠ID Embedding/多图融合)+ReActor深度(inswapper_128后处理/128px限制/必配FaceDetailer)+生产级组合4方案(PuLID+ReActor精修/InstantID+Canny多控/IPAdapter+AnimateDiff视频/LoRA+零样本混合)+全方法6维对比表+方法选择决策树+InsightFace基础设施(AntelopeV2组件/ArcFace 512d)+实验#34概念图(¥0.03)+实验#35角色参考生成(¥0.03)+实验#36图生图一致性(¥0.03) | day22-character-consistency-face-techniques.md |
| 31 | 2026-03-22 16:30 | Day23-高级蒙版与自动分割 | SAM架构深度(ViT-H/MAE/Prompt Encoder三种提示/Mask Decoder歧义感知3层级输出)+SAM2革新(Hiera层次骨干/Memory Bank流式记忆/Memory Attention跨帧传播/Occlusion Score/6x faster)+GroundingDINO架构(ECCV 2024/三阶段紧密融合A+B+C/Feature Enhancer双向Cross-Attn/Language-Guided Query Selection/Sub-Sentence文本表示)+Grounded-SAM管线(文本→bbox→mask)+Impact Pack SEGS体系深度(数据结构/FaceDetailer 4步管线/检测器体系/SEGS操作全集/denoise调优)+Florence-2统一视觉模型(caption+detect+segment+OCR)+背景移除(RMBG 2.0/BiRefNet/ComfyUI-RMBG统一节点)+ComfyUI内置Mask操作(MaskComposite 6种操作/Masquerade Nodes)+5种生产级工作流模式+方法选择决策树+实验#37概念图(¥0.03)+实验#38角色生成(¥0.03)+实验#39背景替换编辑(¥0.03) | day23-advanced-masking-segmentation.md |
| 32 | 2026-03-22 18:30 | Day24-视频后期处理与帧插值 | 帧插值技术全景(RIFE IFNet架构/多尺度粗到细/Privileged Distillation/版本4.0-4.15演进)+FILM(大运动/递归中点)+GIMM-VFI(NeurIPS 2024隐式运动建模/四变体)+IFRNet/AMT/GMFSS等14种VFI算法对比+ComfyUI-Frame-Interpolation节点体系(14算法/调度器/clear_cache)+视频放大技术(SeedVR2扩散式放大/Hann Window时间一致性/四阶段管线/Topaz Proteus v5/DiffVSR流式超分)+去闪烁4种方法(统计/光流引导/颜色匹配/FreeLong频谱)+色彩校正(LUT 3D查找表/4个ComfyUI LUT节点包/EasyColorCorrector)+视频编辑节点生态(VHS全节点体系/Mana-Nodes/VideoDirCombiner/速度控制)+生产级4阶段后期管线(修复→放大→插帧→调色)+参数速查+诊断表+实验#40龙虾冲浪关键帧(¥0.03)+实验#41 Seedance I2V(¥0.30)+实验#42 Topaz视频放大(¥0.11) | day24-video-post-processing-frame-interpolation.md |
| 33 | 2026-03-22 20:03 | Day25-高级视频控制技术 | 6维视频控制全景(镜头/运动/参考/首尾帧/编辑/多镜头)+Kling Camera Controls深度(6DOF参数/5种预设/KlingCameraControlI2V源码分析/硬编码限制)+Seedance prompt-driven镜头+AnimateDiff CameraCtrl本地方案(CameraCtrl_pruned/6种预设运动)+MotionCtrl学术方案(SIGGRAPH Asia/相机+物体解耦)+Kling 3.0 Motion Control(Element Binding面部一致性/characterOrientation双模式/30s连续)+Reference-to-Video全景(O3 vs O1 vs Wan2.6 vs Vidu)+首尾帧技术(语义理解vs像素插值/Vidu参数详解/最佳实践)+Kling V3/O1/O3全系列对比+ComfyUI 4种工作流模式+混合管线设计+实验#43关键帧生成(¥0.06)+实验#44 Vidu首尾帧(90s/¥0.20)+实验#45 Seedance镜头控制(70s/¥0.30) | day25-advanced-video-control-techniques.md |
| 34 | 2026-03-22 22:03 | Day26-音频生成与多模态工作流 | 音频AI三大方向(T2M/TTS/T2SFX)+两大范式(自回归Transformer+EnCodec vs 潜空间扩散DiT)+MusicGen架构深度(EnCodec 4 codebook×50Hz+延迟模式+Melody条件+Stereo)+Stable Audio Open架构(DiT 1057M+音频VAE 2048x压缩+Timing Conditioning)+AudioLDM2(GPT-2 LOA+AudioMAE)+MiniMax Music2.5/Speech2.8+ComfyUI音频节点全景(LTX-2.3原生音频/Stable Audio 2.5 Partner/Kling Audio Partner/comfyui-sound-lab/TTS-Audio-Suite等6+TTS节点)+音频VAE vs图像VAE对比+EnCodec RVQ原理+三种音视频同步策略(原生/后配音/音频驱动)+生产级四层管线设计+LTX-2.3音频I2V工作流JSON+唇同步5种方案(Wav2Lip/SadTalker/LatentSync/Kling/LTX)+LatentSync架构+完整短视频成本估算(¥0.59)+实验#46 MiniMax Music(60s/¥0.14)+实验#47 MiniMax Speech(10s/¥0.016) | day26-audio-generation-multimodal.md |
| 35 | 2026-03-23 00:03 | Day27-Wan视频生成深度解析 | Wan全系列版本演进(2.1→VACE→2.2→S2V→Animate→2.6)+Wan-VAE 3D因果卷积架构(时空压缩4×8×8/因果性/2.2新VAE 4×16×16)+UMT5-XXL编码器(多语言/4096d)+Wan 2.2 MoE(SNR时间步切换/高噪声=布局+低噪声=细节/27B total 14B active)+VACE统一编辑(8种任务单模型)+ComfyUI原生vs WanVideoWrapper对比+Wan扩展(S2V/Animate/2.6 API Only)+本地部署GPU需求矩阵+开源视频模型6家对比+5种工作流模式+实验#48 T2V(50s/¥0.63)+实验#49 I2V(210s/¥0.63) | day27-wan-video-generation-deep-dive.md |
| 36 | 2026-03-23 02:05 | Day28-微调技术全景+工作流工程化 | SD微调5方法全景(TI/HN/LoRA/DreamBooth/Full)+Textual Inversion数学原理(仅优化embedding向量/冻结全模型/多token机制)+DreamBooth深度(Prior Preservation Loss防遗忘/稀有token绑定/+LoRA最佳实践)+Hypernetwork原理与弃用(CrossAttn K/V修改/被LoRA全面替代)+5方法全维度对比表+ComfyUI Subgraph系统(vs Legacy Group Nodes/嵌套图/参数面板)+App Mode+App Builder+ComfyHub(workflow→app转化/URL分享)+Node Registry发布流程(pyproject.toml/comfy-cli/CI-CD)+5种工作流设计模式(管线/分支合并/多阶段精炼/条件路由/迭代循环)+工作流最佳实践+实验#50信息图(35s/¥0.03) | day28-finetuning-ecosystem-workflow-engineering.md |
| 37 | 2026-03-23 04:03 | Day29-Flux实战工作流生态 | Flux模型家族全景(FLUX.1 pro/dev/schnell/Ultra+Tools套件Fill/Depth/Canny/Redux+Kontext+FLUX.2 Klein)+Flux ControlNet生态(BFL官方Canny/Depth+Shakker-Labs Union-Pro-2.0+XLabs-AI+InstantX)+Flux Fill工作流(Inpainting/Outpainting)+Redux工作流(SigLIP→Style Adapter/AdvancedRefluxControl)+FLUX.2 Klein(4B/9B)+量化方案(BF16/NF4/GGUF/FP8/NVFP4)+最佳实践5大差异+2个工作流JSON+实验#51-#52(¥0.06) | day29-flux-practical-workflow-ecosystem.md |
| 38 | 2026-03-23 06:03 | Day30-快速推理与蒸馏技术 | 四大蒸馏家族(一致性/对抗/分布匹配/混合)+12+方法体系(CM/LCM/PCM/ECM/ADD/LADD/Lightning/DMD2/Hyper-SD/SANA-Sprint/AnimateLCM/CausVid)+CM原理(PF-ODE轨迹一致性/CD vs CT)+LCM潜空间蒸馏(增广PF-ODE/LCM-LoRA即插即用)+PCM分段解决三缺陷(NeurIPS 2024)+ADD→LADD演进(pixel→latent/噪声级别控制判别器/Flux Schnell)+Lightning渐进+对抗组合+DMD2分布匹配(NeurIPS Oral/FID 1.28超教师)+Hyper-SD(TSCD+Score Distillation覆盖4模型)+SANA-Sprint(0.03s/1024²)+ComfyUI 10方法配置速查+决策树+2工作流JSON+实验#53概念图(¥0.03) | day30-fast-inference-distillation-techniques.md |
| 39 | 2026-03-23 08:03 | Day31-图像编辑工作流 | 图像编辑三大范式(Training-Free/Fine-tuning/Hybrid)+InstructPix2Pix深度(双CFG机制/数据生成管线GPT-3+P2P/U-Net通道扩展)+CosXL Edit(SDXL版)+ICEdit(NeurIPS 2025/Diptych范式/LoRA-MoE混合微调/0.5%数据+1%参数/Early Filter推理缩放/超越GPT-4o ID保持/4GB MoE版)+Flux Fill高级(InpaintModelConditioning源码/Outpainting/自动Mask管线)+Flux Kontext(上下文感知编辑/多图输入/多轮迭代/prompt技巧)+VACE视频编辑(8种任务/WanVaceToVideo/视频Inpainting+Outpainting)+Qwen-Image-Edit(20B/双通路VLM+VAE/中英文精确文字编辑SOTA/Lightning 4步加速/Layered分层编辑)+OmniGen2(7B VLM+DiT统一/多图组合)+ComfyUI编辑节点体系总览+全方法9维对比+决策树+4种生产级工作流模式+实验#54-#56(概念图+风格编辑+Qwen编辑/¥0.11) | day31-image-editing-workflows.md |
| 40 | 2026-03-23 10:03 | Day32-3D生成与多视角 | 3D生成技术全景(三大技术路线对比)+五种3D表示深度(NeRF/3DGS/Mesh/Triplane/O-Voxel)+3DGS原理(高斯属性59浮点/Tile-based光栅化/自适应密度控制)+Mesh提取(MarchingCubes/DMTet/FlexiCubes)+TripoSR(LRM架构/<0.5s)+TripoSG(1.5B/Rectified Flow/草图输入)+Zero123++(6固定视图/SD2.1微调)+InstantMesh(Zero123++→LRM重建/FlexiCubes/~10s)+TRELLIS(CVPR'25 Spotlight/SLAT统一潜空间)+TRELLIS.2(O-Voxel/SC-VAE 16×/4B DiT/3-60s/1536³)+Hunyuan3D全版本(v1→v3.1/两阶段DiT+ShapeVAE+Paint/PBR/quad拓扑)+ComfyUI-3D-Pack节点(TripoSG/InstantMesh/TRELLIS/Hunyuan3D/3DGS/FlexiCubes)+5种工作流模式(快速重建/多视图/两阶段/高分辨率/3D→2D渲染回路)+3D辅助角色一致性+产品展示管线+商业平台对比+决策树+实验#57-#59(参考图+图生3D+文生3D/¥1.23) | day32-3d-generation-multiview.md |
| 41 | 2026-03-23 10:33 | Day33-生产部署与规模化 | 四种部署模式(本地/云GPU/Serverless/托管)+Docker容器化最佳实践(多阶段构建/分层策略/模型Volume)+六大云平台对比(ViewComfy/RunComfy/RunPod/Replicate/BentoCloud/SaladCloud)+RunPod Serverless架构+BentoML comfy-pack+ComfyDeploy+ComfyUI Manager v2+comfy-cli+extra_model_paths.yaml+模型缓存策略(LRU)+API网关负载均衡(5种策略)+Model Affinity路由+Prometheus+Grafana监控+五类错误处理+熔断器模式+安全清单+成本优化(7策略)+CI/CD+工作流测试 | day33-production-deployment-scaling.md |
| 42 | 2026-03-23 10:33 | Day34-多模型编排与生产管线 | 五种编排模式(线性/分支合并/条件路由/迭代精炼/DAG)+电商产品图管线(RMBG→Fill→ESRGAN→多尺寸裁剪)+短视频五阶段管线(关键帧→视频→音频→后期→合成/¥2.36)+角色一致性漫画8面板+实时头像SaaS+批量处理4模式+参数扫描+质量评估自动化+工作流模板化+版本管理+ComfyUI微服务架构+AI Agent集成+ComfyUI-R1自动工作流+性能基准+幂等性设计+断点续传+十大设计原则 | day34-multi-model-orchestration-production-pipelines.md |
| 43 | 2026-03-23 10:33 | Day35-2026前沿趋势 | Nodes 2.0 Vue迁移(V3 Schema)+App View/Builder+Desktop+Cloud+DiT统一化+AR+Diffusion混合架构+模型压缩(FLUX.2 Klein/GGUF/NF4/NVFP4)+实时生成(StreamDiffusion 100+FPS/SANA-Sprint 0.03s/CausVid实时视频)+Blackwell RTX 5090 NVFP4+AI辅助工作流(ComfyAgent/ComfyGPT/ComfyUI-R1)+游戏资产生成+数字人+电商自动化+开源生态格局+2026-2027预测 | day35-2026-frontiers-emerging-trends.md |
| 44 | 2026-03-23 10:33 | Day36-毕业总结🎓 | 完整知识图谱(20+领域/100+节点包/50+模型)+速查手册(模型选择/采样器/VRAM/成本)+能力自评(19维度A-A+)+学习统计(36天/44轮/36篇笔记/59实验/~600KB)+后续实操清单+持续跟踪建议+毕业宣言 | day36-graduation-summary-cheatsheet.md |
| 45 | 2026-03-23 12:03 | PostGrad#1-新视频模型对比 | rhart-video-s(¥0.02/9.5s/704×1280)+rhart-v3.1-fast(¥0.04/8s/1280×720)+Seedance基准(¥0.30/5s/1280×720)+性价比分析(rhart系列15-30x便宜)+发现rhart-s竖屏行为+模型选择决策更新 | postgrad-01-new-video-model-comparison.md |
| 46 | 2026-03-23 14:03 | PostGrad#2-Ref2V多模型对比 | 5模型Ref2V对比(Kling O3¥0.50/Wan2.6¥0.65/Seedance¥0.15/rhart V3.1¥1.36/Vidu余额不足)+Hailuo2.3 fast I2V(¥0.17)+性价比排名(Seedance>Kling O3>Wan>rhart)+ComfyUI Ref2V工作流JSON+混合管线设计(本地Flux+API Ref2V+本地后处理)+Partner Nodes源码分析 | postgrad-02-reference-to-video-comparison.md + kling-o3-ref2v-with-postprocess.json |
| 47 | 2026-03-23 16:03 | PostGrad#3-音视频多模态管线 | 端到端多模态管线(关键帧→I2V→BGM→旁白→FFmpeg合成)+新模型对比(Hailuo 2.3 fast-pro ¥0.29 1934×1080最佳性价比/Vidu Q3 Pro ¥0.55/Seedance Fast ¥0.30)+Vidu Q3首尾帧生视频(双图上传/自带音频)+FFmpeg多镜头(xfade交叉淡化+amix多轨混音)+多镜头短视频成品7.38s+管线成本结构分析(视频80%/音频2%)+rhart-video-g参数调试(failed但记录差异) | postgrad-03-audio-video-multimodal-pipeline.md |
| 48 | 2026-03-23 18:03 | PostGrad#4-Seedream+编辑→视频管线 | Seedream模型家族首测(v5-lite/v4.5/全部2048x2048/¥0.04)+Qwen-Image-2.0-Pro精确编辑(三项指令全部精准/ID保持极佳)+Seedream I2I场景变换(strength=0.65/厨房→海底宫殿)+T2I→Edit→I2V完整链式管线(¥0.39/95s)+编辑模型选择策略(精确用Qwen/变换用Seedream)+Seedance Fast动画化编辑图(960x960/5s/含音频) | postgrad-04-seedream-edit-to-video-pipeline.md |
| 49 | 2026-03-23 20:03 | PostGrad#5-视频编辑+扩展+新模型 | rhart-image-g-4首测(¥1.00/电影级真实感/偏写实不适合创意)+Hailuo 02 I2V(1376x768/5.9s/¥0.25/正确横屏)+Veo 3.1 fast Video Extend(5.9→12.9s/¥0.95/风格一致/自带音频)+Kling O3 std Video Edit(日→夜场景转换/樱花→萤火虫/¥0.55/效果惊艳)+Veo 3.1 fast首尾帧过渡(日→夜/8s/¥0.04/极致性价比/支持4K)+rhart-video-s竖屏bug第3次确认+视频编辑/扩展ComfyUI工作流映射 | postgrad-05-video-editing-extension-new-models.md |
| 50 | 2026-03-23 22:03 | PostGrad#6-VoiceClone+悠船MJ系+多模态 | 悠船v7/niji7首测(v7偏写实¥0.09/niji7拟人化极强¥0.09)+三模型Prompt理解差异对比(v7人类厨师/niji7龙虾角色/rhart龙虾本体)+悠船I2V(1264×704/5.2s/205s/¥0.27/无音频/支持首尾帧+循环)+Voice Clone声音克隆首测(MiniMax引擎/accuracy=0.8/15s/¥0.45/比普通TTS贵75x)+rhart-video-s realistic首测(30fps/1280×720/4.3s/¥0.50/支持真人)+FFmpeg多模态合成(视频+克隆音频→最终产品)+完整管线成本分析(¥0.786含VoiceClone/¥0.336不含)+模型选择策略更新(T2I 6选/I2V 4选/Audio 4选) | postgrad-06-voice-clone-youchuan-multimodal.md |

## Day 21 进度 (超分辨率与图像增强 — Upscaling & Super Resolution) ✅
- [x] 超分辨率技术全景
  - [x] 三大放大方式对比（传统插值 / AI 模型放大 / SD 重绘放大）
  - [x] 技术发展时间线（ESRGAN 2018 → PMRF 2024 → SPAN 2025）
- [x] ComfyUI 超分源码深度分析
  - [x] Spandrel 统一模型加载库（自动架构检测 / 15+ 支持架构列表）
  - [x] UpscaleModelLoader 源码（state_dict 前缀处理 / ImageModelDescriptor 类型检查）
  - [x] ImageUpscaleWithModel 源码深度（内存估算 384x 经验系数 / 分块处理 512 默认 / 32px overlap / OOM 自动降级 tile÷2 / 最小 128）
  - [x] tiled_scale 分块放大机制（网格分割 / 扩展 overlap / 线性渐变融合权重）
  - [x] ImageScale / ImageScaleBy 传统插值（nearest/bilinear/bicubic/lanczos/area 对比）
- [x] 超分模型架构深度对比
  - [x] ESRGAN 系列（RRDB 架构 / Real-ESRGAN 真实退化建模 / 6 款社区模型对比）
  - [x] SwinIR（Swin Transformer 窗口自注意力 / RSTB / 纹理保真最优）
  - [x] HAT（Hybrid Attention / OCAB / 当前学术 SOTA）
  - [x] PMRF / SPAN / DAT 新架构概述
  - [x] 模型选择决策树（按场景/速度/质量分支）
- [x] 6 种 ComfyUI 超分工作流模式
  - [x] 模式一：纯模型放大（2-3 节点）
  - [x] 模式二：生成+放大流水线
  - [x] 模式三：Hires Fix（低分辨率生成 + 放大 + 低 denoise 重采样）
  - [x] 模式四：Tile ControlNet 超分（最高质量 / strength 调优）
  - [x] 模式五：Ultimate SD Upscale（分块 SD 放大 / 任意大尺寸 / 参数详解）
  - [x] 模式六：Latent 放大（直接插值 latent tensor）
  - [x] denoise 值对放大的影响（0.2-0.3 保守 → 0.7+ 危险）
- [x] 人脸修复与细节增强
  - [x] CodeFormer（Transformer + CodeBook / fidelity 参数 0.5-0.7 推荐）
  - [x] GFPGAN（GAN + 通道注意力 / 更激进修复）
  - [x] FaceDetailer（Impact Pack / 4 步工作流: BBOX 检测→裁剪→重绘→贴回 / 关键参数 7 个）
  - [x] CropAndStitch 替代方案（2025 社区趋势 / 手动控制 / REACTOR 兼容）
- [x] 完整超分管线最佳实践
  - [x] 三阶段管线（ESRGAN 预放大 → SD 重采样 → 人脸修复）
  - [x] 分辨率规划表（1080p/2K/4K/8K）
  - [x] 常见问题诊断表（7 种症状→原因→解决方案）
- [x] RunningHub 实验
  - [x] 实验 #32: Topaz Standard V2 放大（1024→2048, 20s/¥0.10）
  - [x] 实验 #33: Topaz High Fidelity V2 放大（1024→2048, 20s/¥0.10）
  - [x] Standard vs High Fidelity 对比分析

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

## Day 16 进度 (综合实战 — 从零编排完整视频生成工作流) ✅
- [x] 三阶段管线架构设计（概念→关键帧→视频→后处理）
  - [x] 四种关键帧策略（单帧/首尾帧/多关键帧/参考帧）
  - [x] 三种 ComfyUI 编排范式（全本地/混合/全 API）
  - [x] 模型选择决策树（按 GPU/预算/需求分支）
- [x] ComfyUI 工作流 JSON 从零编写
  - [x] Flux T2I → Kling 3.0 I2V 混合管线（11 节点完整工作流）
  - [x] LTX-2.3 两阶段 T2V 管线（18 节点，低分辨率→潜空间上采样→解码）
- [x] 生产级管线工具编写
  - [x] storyboard_pipeline.py（分镜→关键帧→视频→拼接，带重试/报告）
  - [x] ComfyUI WebSocket API 客户端模板
  - [x] 错误处理与重试策略设计
  - [x] phoenix-storyboard.json 三幕分镜示例
- [x] RunningHub 多模型实验（4 个实验）
  - [x] 实验 #23: 凤凰关键帧生成（rhart-image-n-pro, 30s/¥0.03）
  - [x] 实验 #24: Seedance 1.5 Pro I2V（1280×720, 60s/¥0.30）
  - [x] 实验 #25: Kling 3.0 Pro I2V（1928×1076, 115s/¥0.75）
  - [x] 实验 #26: Vidu Q2 Pro 首尾帧视频（首帧+尾帧+prompt, 125s/¥0.20）
- [x] 三模型同图对比分析（分辨率/成本/速度/性价比）
- [x] 四种管线架构对比（GPU要求/控制精度/质量/成本/适用场景）
- [x] 关键帧质量对视频质量影响分析
- [x] Prompt 工程差异总结（图像 vs 视频）

## Day 17 进度 (模型合并 — Model Merging) ✅
- [x] 模型合并理论基础
  - [x] Mode Connectivity（Garipov 2018）— 独立训练模型可通过简单曲线连接
  - [x] Linear Mode Connectivity（Frankle 2020）— 同基础模型微调后线性插值安全
  - [x] 神经网络稀疏性 — 为什么合并时关键参数冲突概率低
  - [x] Task Vector 定义（τ = θ_ft - θ_base）
- [x] 6 种经典合并方法（数学公式 + ComfyUI 实现）
  - [x] Weighted Sum: (1-α)·A + α·B + 源码 add_patches 机制
  - [x] Add Difference: C + α·(A - B) + ModelSubtract/ModelAdd 源码
  - [x] SLERP: 球面线性插值（sin 公式 + 范数保持优势）
  - [x] Block Weighted Merge: input/middle/out 分块 + 最长前缀匹配源码
  - [x] Task Arithmetic: θ_base + Σαᵢ·τᵢ
  - [x] CosXL 转换案例
- [x] 3 种高级合并方法（2023-2025 前沿）
  - [x] TIES-Merging (NeurIPS 2023): Trim + Elect Sign + Merge 三步法
  - [x] DARE (2024): Random Drop + Rescale（可丢 90-99% delta 参数）
  - [x] DARE-TIES 组合方法
  - [x] Git Re-Basin: 排列对齐后合并
- [x] ComfyUI 源码深度分析（nodes_model_merging.py）
  - [x] 全 11 个内置节点（Model/CLIP 各 Simple/Subtract/Add + Blocks + 3 Save）
  - [x] add_patches(strength_patch, strength_model) 数学语义
  - [x] CLIP 合并跳过 position_ids/logit_scale 的原因
  - [x] CheckpointSave 元数据（modelspec 架构标记 + predict_key）
  - [x] 架构特定 MBW 节点（SD1/SD2/SDXL/SD3/Flux）
- [x] 第三方合并工具
  - [x] ComfyUI-DareMerge（DARE-TIES + Gradient + Mask + Normalize）
  - [x] SuperMerger / Chattiori-Model-Merger
- [x] SD 各架构合并差异（SD1.5/SDXL/Flux block 结构 + 注意事项）
- [x] LoRA 合并（合入模型 / 多 LoRA 叠加 / LoRA 间合并）
- [x] 合并质量评估与诊断（6 种症状→原因→方案）
- [x] 合并策略决策树
- [x] 3 个工作流 JSON
  - [x] model-merge-compare.json（Simple + Block 对比）
  - [x] add-difference-inpaint.json（三模型能力迁移）
- [x] RunningHub 实验 #27（模型合并概念信息图，25s/¥0.03）

## Day 18 进度 (ComfyUI API 自动化 + 批量任务) ✅
- [x] ComfyUI HTTP API 全端点深度分析
  - [x] 30+ 内置路由完整列表（Core API + User Data + Queue Management）
  - [x] /prompt POST 请求格式详解（prompt/client_id/prompt_id/extra_data/front/number）
  - [x] WebSocket 消息协议（8 种消息类型 + 二进制 latent preview 解码）
  - [x] 完整 API 调用流程（5 步：连接→提交→监听→查历史→下载）
- [x] Python 自动化工具生态对比
  - [x] 官方 websockets_api_example.py 源码分析
  - [x] 5 个第三方库对比（comfyui_utils/comfy-api-simplified/ComfyUI-to-Python/comfy-nodekit/ComfyScript）
  - [x] 各库适用场景决策树
- [x] 生产级部署方案分析
  - [x] SaladTechnologies/comfyui-api（无状态 API + Webhook + S3/Azure 存储 + LRU 缓存）
  - [x] BentoML/comfy-pack（环境快照 → Docker → 云部署）
  - [x] Cloud 平台生态（RunComfy / ViewComfy / Comfy.org Cloud）
- [x] 批量任务自动化模式
  - [x] 批量生成架构图（数据源→调度器→参数替换→队列→输出处理）
  - [x] 4 种批量模式对比（串行/预提交/多WS并行/分布式）
  - [x] 参数扫描 6 维度（Seed/CFG/Sampler/Prompt/LoRA/Resolution）
  - [x] XY Plot 节点（Efficiency Nodes 社区方案）
- [x] 错误处理与重试策略
  - [x] 5 种关键错误类型处理（CUDA OOM/WS 断连/验证失败/模型缺失/队列满）
  - [x] 指数退避重试模式
- [x] 高级自动化技术
  - [x] 工作流动态修改（参数注入）
  - [x] 图片上传 + Img2Img 批量流程
  - [x] ComfyUI Cloud API（wss 协议 + token 认证）
  - [x] 进度追踪 + 回调系统
  - [x] 模型预检查 + 环境验证
- [x] GUI 格式 vs API 格式对比 + 转换方法
- [x] 生产级 batch_api_runner.py（469 行）
  - [x] CSV/JSON 任务加载
  - [x] WebSocket 实时进度
  - [x] 指数退避重试（最多 3 次）
  - [x] CUDA OOM 自动恢复
  - [x] 结果摘要报告
- [x] RunningHub 实验 #28（批量 3 风格龙图，72.5s/¥0.09）

## Day 19 进度 (性能优化 — TensorRT / 量化 / 显存管理) ✅
- [x] VRAM 消耗原理深度分析
  - [x] 三大 VRAM 消耗源（模型权重/激活值/注意力矩阵）
  - [x] 注意力的二次方缩放行为（1024x1024 = 4x 512x512 注意力内存）
  - [x] PyTorch 内存分配器行为（块分配/碎片化/reserved vs allocated）
- [x] ComfyUI 内置 VRAM 管理机制
  - [x] Smart Memory 系统（load_models_gpu/free_memory/LRU 驱逐）
  - [x] Dynamic VRAM（0.5.0+ 默认启用）
  - [x] 启动参数全集（--gpu-only/--highvram/默认/--lowvram/--novram/--reserve-vram/--disable-smart-memory）
- [x] 精度格式全景对比（8 级）
  - [x] FP32/BF16/FP16/FP8/GGUF Q8_0/GGUF Q5_K/NF4/NVFP4 全维度对比
  - [x] FP16 vs BF16 选择策略（精度 vs 范围/NaN 问题）
  - [x] FP8 vs GGUF Q8 深度对比（硬件加速 vs block 缩放）
- [x] GGUF 量化深度解析
  - [x] city96/ComfyUI-GGUF 节点系统（Unet Loader GGUF / CLIPLoader GGUF）
  - [x] block 缩放机制原理（32 值一组 + 独立缩放因子）
  - [x] DiT vs U-Net 量化适配性（线性层 vs conv2d 敏感度差异）
  - [x] 预量化模型生态（Flux/SD3.5/T5 全系列）
  - [x] LoRA 实验性兼容
- [x] NF4 (BitsAndBytes) 与 NVFP4 (Nunchaku)
  - [x] NF4 正态分布假设 + 分位数编码
  - [x] NVFP4 SVDQuant（ICLR 2025 Spotlight）低秩分量吸收离群值
  - [x] Nunchaku 引擎 + ComfyUI-nunchaku 插件
  - [x] RTX 5090 上 3x 加速（需 cu130 PyTorch）
- [x] 注意力优化 5 种方法对比
  - [x] xFormers（分块/近线性/+20%/广泛兼容）
  - [x] Flash Attention（IO-Aware/融合/+25-30%/Ampere+）
  - [x] SageAttention（Triton kernel/+30-40%/需编译）
  - [x] PyTorch SDPA（自动选择/+15-25%/2.0+内置）
  - [x] Attention Slicing（极省内存/极慢/最后手段）
- [x] 卸载策略 4 级
  - [x] 文本编码器卸载（省 1-2GB/极小影响）
  - [x] VAE 卸载（省 160-320MB）
  - [x] lowvram 模式（5-10x 慢但能跑）
  - [x] novram/CPU 模式
- [x] Async Offloading + Pinned Memory（2025 年 12 月默认启用）
  - [x] Pinned Memory 原理（页锁定/DMA 直接访问）
  - [x] Async Offloading 原理（权重传输与计算异步并行）
  - [x] 10-50% 加速（仅卸载场景有效）
  - [x] PCIe 代数/通道数直接影响收益
- [x] TensorRT 加速
  - [x] 图优化/核融合/精度校准/GPU 特定优化
  - [x] ComfyUI_TensorRT 节点（Static vs Dynamic Engine）
  - [x] 性能 2-3x 加速
  - [x] ⚠️ 不兼容 ControlNet/LoRA（致命限制）
  - [x] 决策树（需要 CN/LoRA → 不用 TRT）
- [x] torch.compile 优化
  - [x] TorchCompileModel 内置节点
  - [x] GGUF Flux Q8_0 约 30% 加速
  - [x] LoRA-Safe TorchCompile 社区节点
- [x] VAE 分块处理（Tiled VAE）
  - [x] VAEDecodeTiled/VAEEncodeTiled 原理
  - [x] VRAM 从 14GB → 8GB（43% 节省，RTX 4090 实测）
- [x] 综合优化策略决策树
  - [x] 按 GPU VRAM 分 4 档（24GB+/12-16GB/8GB/4GB/Blackwell）
  - [x] 速度优化清单 7 条
  - [x] VRAM 节省清单 6 条
  - [x] 常见问题诊断表（7 种症状→原因→方案）
- [x] 性能相关自定义节点生态（7 个核心节点包）
- [x] RunningHub 实验 #29（性能优化概念信息图，30s/¥0.03）

## Day 20 进度 (高级条件控制与构图技术 — Advanced Conditioning & Composition) ✅
- [x] Conditioning 数据结构深度解析
  - [x] 内部表示：list of [tensor, metadata_dict]
  - [x] 元数据全字段：pooled_output/area/strength/mask/start_percent/end_percent/gligen/control/hooks/uuid
  - [x] 采样器消费流程：_calc_cond_batch → get_area_and_mult → 加权平均
- [x] 四种 Conditioning 操作的数学本质（源码级分析）
  - [x] Combine: Python list 拼接 → 噪声预测级加权平均（每条目独立 model forward）
  - [x] Concat: torch.cat(dim=1) → token 序列拼接（突破 77 token 限制）
  - [x] Average: α×t1 + (1-α)×t0 → 嵌入空间线性插值（单次 forward）
  - [x] 四种操作的混合层级/数学操作/Forward次数/用途对比表
- [x] 区域条件控制（Regional Prompting）
  - [x] ConditioningSetArea 源码（像素→latent 坐标转换 + 8px fuzz 渐变机制）
  - [x] ConditioningSetAreaPercentage（百分比版，分辨率无关）
  - [x] ConditioningSetMask 源码（mask×mask_strength + set_area_to_bounds 优化）
  - [x] SetArea vs SetMask 全维度对比
  - [x] 社区方案：Impact Pack RegionalConditioningByColorMask / ComfyCouple Attention Couple / Inspire Pack
- [x] 时间维度控制
  - [x] ConditioningSetTimestepRange 源码（start_percent/end_percent + 采样器 timestep 检查）
  - [x] Prompt Scheduling 设计模式（三阶段：构图→细节→质量）
  - [x] FizzNodes PromptSchedule（动画/视频用）
  - [x] comfyui-prompt-control（A1111 语法兼容）
- [x] GLIGEN 接地式布局控制
  - [x] 架构（gated self-attention + bounding box + text）
  - [x] ComfyUI 实现（gligen 元数据 → middle_patch 注入）
  - [x] 局限性（仅 SD1.5/SD2.1，被 ControlNet + Regional Prompting 替代）
- [x] CLIP Vision & unCLIP & Style Model
  - [x] CLIPVisionEncode（图像→向量）
  - [x] unCLIPConditioning（图像语义注入 + noise_augmentation）
  - [x] ApplyStyleModel（CLIP Vision → conditioning tokens → 拼接）
  - [x] 被 IP-Adapter 方案功能性替代
- [x] 注意力操控技术
  - [x] SAG（Self-Attention Guidance）：模糊 self-attention map 引导结构
  - [x] PAG（Perturbed-Attention Guidance，CVPR 2024）：恒等映射替换 self-attention
  - [x] sd-perturbed-attention 扩展生态（SEG/SWG/NAG/TPG/FDG/MG/SMC-CFG 共 8 种）
  - [x] Attention Couple vs 噪声预测级区域混合的本质差异
- [x] ConditioningZeroOut 特殊用途（Flux negative / 无文本引导测试）
- [x] 高级构图模式
  - [x] 方案 A: SetArea + Combine（简单矩形）
  - [x] 方案 B: SetMask + Combine（精确形状）
  - [x] 方案 C: Attention Couple（模型层面隔离）
  - [x] 多阶段 Prompt 策略
  - [x] Negative Prompt 分时段控制
- [x] 条件系统决策树
- [x] 关键源码函数速查表（7 个核心函数）
- [x] RunningHub 实验
  - [x] 实验 #30: 区域构图对比（红甲战士 vs 蓝衣法师，35s/¥0.03）
  - [x] 实验 #31: 超长 Prompt 细节测试（200 token 赛博朋克场景，40s/¥0.03）

## Day 22 进度 (角色一致性与人脸技术 — Character Consistency & Face Techniques) ✅
- [x] 角色一致性技术全景
  - [x] 四大技术路线分类（训练型 / 零样本型 / 人脸替换型 / 组合型）
  - [x] 技术演进时间线（IP-Adapter 2023.08 → PhotoMaker 2023.12 → InstantID 2024.02 → PuLID 2024.04 → PuLID-FLUX 2024.09）
  - [x] 核心问题定义（身份保真度 / 自然度 / Prompt 遵从度三角平衡）
- [x] IP-Adapter 架构深度解析
  - [x] 解耦交叉注意力核心公式 (Output = TextAttn + λ × ImageAttn)
  - [x] CLIP ViT-H/14 编码器 → 257 tokens 1024d → Trainable Projection → K_img, V_img
  - [x] IP-Adapter 变体全家族（8 种: 基础/Plus/Plus Face/FaceID/FaceID Plus V2/Portrait/SDXL/Flux）
  - [x] FaceID 技术细节（ArcFace 512d → CLIP 空间投影 / 需配套 LoRA 的原因）
  - [x] FaceID Plus V2 双路融合（InsightFace 身份 + CLIP 细节特征）
  - [x] ComfyUI_IPAdapter_plus 节点体系（cubiq, 4.93K⭐, 2025.04 维护模式）
  - [x] Weight Types 14 种注入方式详解（linear/ease in/ease out/style transfer/composition 等）
  - [x] start_at / end_at 参数调优策略
- [x] InstantID 架构深度解析
  - [x] 三组件架构（InsightFace AntelopeV2 + IdentityNet ControlNet + IP-Adapter）
  - [x] InsightFace 提供面部嵌入 512d + 5 点关键点
  - [x] IdentityNet = 定制 ControlNet（控制面部空间布局）
  - [x] IP-Adapter 模块（控制身份语义特征）
  - [x] vs IP-Adapter FaceID 关键区别（空间控制 / 模型依赖 / LoRA 需求）
  - [x] ComfyUI_InstantID 节点（ip_weight + cn_strength 分离控制）
  - [x] 关键参数推荐（ip_weight 0.8-1.2, cn_strength 0.4-0.7, noise 0.35）
- [x] PuLID 架构深度解析
  - [x] NeurIPS 2024 论文解读（对比对齐 + 闪电 T2I 双分支训练）
  - [x] 双分支训练架构（Standard Diffusion + Lightning T2I）
  - [x] Contrastive Alignment Loss（正样本 vs 负样本身份对比学习）
  - [x] Accurate ID Loss（InsightFace 特征空间余弦相似度）
  - [x] 纯净性 (Purity): FID 偏移 <0.5，无 ID 时 ≈ 原始模型
  - [x] PuLID-FLUX 适配（DiT Double-Stream Block 注入）
  - [x] vs InstantID 全维度对比（身份 91% vs 84% / 自然度 92% vs 86% / Prompt 83% vs 88%）
  - [x] ComfyUI PuLID 节点参数（weight / method: fidelity vs style）
- [x] PhotoMaker 架构解析
  - [x] CVPR 2024 论文（堆叠 ID Embedding）
  - [x] 多图输入 (1-4张) → CLIP Image Encoder → MLP Projection → 堆叠嵌入
  - [x] Trigger Token 机制（替换 prompt 中特殊 token）
  - [x] PhotoMaker V2 改进
- [x] ReActor 人脸替换深度解析
  - [x] 后处理型管线（InsightFace 检测 → inswapper_128 替换 → GFPGAN/CodeFormer 修复 → Mask 融合）
  - [x] 128px 致命限制（必须配合 FaceDetailer）
  - [x] vs ID 注入方法全维度对比（精度 98% vs 84-91% / 自然度 75% vs 81-92%）
  - [x] ComfyUI-ReActor 核心节点（FaceSwap / BuildFaceModel / RestoreFace）
- [x] 生产级组合工作流 4 方案
  - [x] 方案 A: PuLID 生成 + ReActor 精修（最高保真度）
  - [x] 方案 B: InstantID + ControlNet Canny（精确姿态控制）
  - [x] 方案 C: IP-Adapter + AnimateDiff（视频一致性）
  - [x] 方案 D: LoRA + 零样本混合（长期角色项目）
- [x] 全方法 6 维对比总结
  - [x] 身份精度 / 自然度 / Prompt 遵从 / VRAM / 速度 / 最佳场景
  - [x] 方法选择决策树（单图/视频/长期项目/多人场景分支）
  - [x] 2025-2026 趋势展望（Flux 主导 / 官方内置化 / 视频 ID 条件 / 组合管线标准化）
- [x] InsightFace 面部分析库详解
  - [x] AntelopeV2 模型 5 组件（3D关键点/2D关键点/性别年龄/人脸识别/人脸检测）
  - [x] ArcFace Embedding 512d + angular margin loss + 同一人阈值 cos_sim > 0.68
- [x] RunningHub 实验
  - [x] 实验 #34: 角色一致性技术全景概念图（35s/¥0.03）
  - [x] 实验 #35: 角色参考图生成（红发女性 1:1, 25s/¥0.03）
  - [x] 实验 #36: 图生图角色场景变换（赛博朋克场景, 30s/¥0.03）

## Day 23 进度 (高级蒙版与自动分割 — Advanced Masking & Segmentation) ✅
- [x] SAM (Segment Anything Model) 深度解析
  - [x] SAM 原始架构（Image Encoder ViT-H + Prompt Encoder + Mask Decoder）
  - [x] 三种提示类型（Point/Box/Mask）+ 歧义感知 3 层级输出
  - [x] SAM 模型变体全对比（ViT-H/L/B + SAM-HQ + MobileSAM）
- [x] SAM 2 架构革新
  - [x] Hiera 层次化骨干网络（多尺度金字塔 / 6x faster）
  - [x] Memory Bank 流式记忆机制（FIFO Queue / Memory Attention）
  - [x] 遮挡感知（Occlusion Score 预测）
  - [x] 视频分割统一架构（图像+视频 / SA-V 数据集 51K 视频）
  - [x] SAM2 模型变体（tiny/small/base_plus/large）
- [x] ComfyUI SAM/SAM2 节点体系
  - [x] kijai/ComfyUI-segment-anything-2（主流 SAM2 集成）
  - [x] Impact Pack SAMLoader + SAMDetector
  - [x] storyicon/comfyui_segment_anything（Grounded-SAM）
- [x] GroundingDINO 深度解析（ECCV 2024）
  - [x] 三阶段紧密融合架构（A: Feature Enhancer + B: Language-Guided Query Selection + C: Cross-Modality Decoder）
  - [x] Sub-Sentence 文本表示（避免语义污染）
  - [x] GroundingDINO vs YOLO 全维度对比
  - [x] 模型变体（SwinT 694MB / SwinB 938MB / 1.5 Pro）
- [x] Grounded-SAM 组合管线
  - [x] 文本→bbox→mask 完整流程
  - [x] ComfyUI 两种实现方式
- [x] Impact Pack 深度解析
  - [x] SEGS 数据结构详解（vs MASK 对比）
  - [x] FaceDetailer 4 步内部流程（Detection→Segmentation→Crop&Enhance→Paste）
  - [x] FaceDetailer 关键参数矩阵（denoise/guide_size/noise_mask 调优）
  - [x] 检测器体系（BBOX_DETECTOR / SEGM_DETECTOR / 常用模型文件）
  - [x] SEGS 操作节点全集（检测/过滤/像素操作/增强/转换）
- [x] Florence-2 统一视觉基础模型
  - [x] 多任务能力（Caption/Detection/Segmentation/OCR）
  - [x] vs GroundingDINO 对比与选择策略
- [x] 背景移除专用技术
  - [x] RMBG 2.0（BRIA AI / BiRefNet 架构）
  - [x] BiRefNet 多变体（general/portrait/matting/lite/dynamic）
  - [x] ComfyUI-RMBG 统一节点（1038lab / 支持 10+ 模型）
- [x] ComfyUI 内置 Mask 操作深度
  - [x] MASK tensor 格式（[B,H,W] float32 [0,1]）
  - [x] 内置节点全集（创建/操作/变换）
  - [x] MaskComposite 6 种操作详解（multiply/add/subtract/and/or/xor）
  - [x] Masquerade Nodes（Mask by Text / Combine Masks）
- [x] 5 种生产级组合工作流模式
  - [x] 模式一: 文本驱动精确分割（Grounded-SAM）
  - [x] 模式二: 人脸增强管线（FaceDetailer）
  - [x] 模式三: 分层 Inpainting（RMBG + 背景重绘）
  - [x] 模式四: 多区域独立控制（SEGS Filter + SEGSDetailer）
  - [x] 模式五: 视频帧一致性分割（SAM2 Video）
- [x] 方法选择决策树
- [x] RunningHub 实验
  - [x] 实验 #37: 分割技术全景概念图（30s/¥0.03）
  - [x] 实验 #38: 龙虾角色办公室场景生成（20s/¥0.03）
  - [x] 实验 #39: 图生图背景替换编辑（25s/¥0.03）

## Day 24 进度 (视频后期处理与帧插值 — Video Post-Processing & Frame Interpolation) ✅
- [x] 帧插值 (VFI) 技术全景
  - [x] 帧插值核心原理（前向/后向 warp / 中间流直接估计）
  - [x] RIFE 架构深度（IFNet 多尺度 / Privileged Distillation / Timestep 编码 / 版本 4.0-4.15 演进）
  - [x] FILM（大运动专用 / 递归中点插值）
  - [x] GIMM-VFI（NeurIPS 2024 / 隐式运动建模 / 四变体 R/F/R-P/F-P）
  - [x] IFRNet / AMT / GMFSS Fortuna / STMFNet / FLAVR / ATM-VFI / MoMo 等算法概述
  - [x] 算法选择决策树（实时/大运动/最高质量/AI视频/动画 分支）
- [x] ComfyUI 帧插值节点生态
  - [x] Fannovel16/ComfyUI-Frame-Interpolation（14 种 VFI 算法 / 调度器 / clear_cache）
  - [x] kijai/ComfyUI-GIMM-VFI（NeurIPS 2024 SOTA / ds_scale 高分辨率适配）
  - [x] ComfyUI-WhiteRabbit RIFE VFI（优化版）
  - [x] ComfyUI-Rife-TensorRT（GPU 加速 RIFE）
- [x] 视频放大 (Video Upscaling) 技术
  - [x] 图像放大 vs 视频放大核心区别（时间一致性挑战）
  - [x] SeedVR2 扩散式视频放大（DiT+VAE / Hann Window / 四阶段管线 / batch_size≥5 / RGBA / V3 兼容）
  - [x] Topaz Video AI（Proteus v5 改进 / 商业 API via RunningHub）
  - [x] ComfyUI-FL-DiffVSR（Stream-DiffVSR / 文本引导 / 流式架构）
  - [x] 逐帧放大 + 去闪烁折中方案
  - [x] 视频放大策略决策树
- [x] 去闪烁 (Deflicker) 与时间一致性
  - [x] 闪烁来源分析（独立生成/Vid2Vid/逐帧放大/权重波动）
  - [x] 统计去闪烁（SuperBeasts Deflicker + Pixel Deflicker）
  - [x] 光流引导一致性（comfyui-optical-flow / warp 前帧输出）
  - [x] 颜色匹配（histogram matching）
  - [x] FreeLong 频谱混合（NeurIPS 2024 / Wan 2.2 专用）
  - [x] 生产级去闪烁管线
- [x] 色彩校正与调色 (Color Grading)
  - [x] LUT 原理（1D / 3D LUT / 三线性插值）
  - [x] ComfyUI_essentials ImageApplyLUT+
  - [x] ComfyUI_LayerStyle LUT Apply
  - [x] ComfyUI-ProPost（Log LUT / 混合模式）
  - [x] ComfyUI-lut ImageToLUT（从参考图自动生成 LUT）
  - [x] ComfyUI-EasyColorCorrector（色温/HSL/AI 自动校色）
  - [x] 视频调色最佳实践
- [x] 视频编辑节点生态
  - [x] ComfyUI-VideoHelperSuite (VHS) 全节点体系（加载/输出/操作/音频 4 类）
  - [x] VHS_VideoCombine 详解（format/crf/pingpong/audio）
  - [x] ComfyUI-Mana-Nodes（Split/Merge/Speed/Reverse/Loop）
  - [x] ComfyUI-VideoDirCombiner（批量拼接 + 转场）
  - [x] 速度控制与慢动作 3 种方法（VHS 帧率 / AKatz Speed / Wan Motion Scale）
  - [x] ComfyUI 内置视频节点（TrimVideoLatent / CreateVideo）
- [x] 生产级视频后期管线
  - [x] 四阶段完整管线（基础修复 → 分辨率提升 → 帧率提升 → 调色输出）
  - [x] 关键参数速查表
  - [x] 常见问题诊断表（7 种症状→原因→方案）
  - [x] 工作流 JSON 示例（基础帧插值 + 放大+插帧+调色完整管线）
- [x] RunningHub 实验
  - [x] 实验 #40: 龙虾冲浪关键帧生成（rhart-image-n-pro, 20s/¥0.03）
  - [x] 实验 #41: Seedance Fast I2V 视频生成（50s/¥0.30）
  - [x] 实验 #42: Topaz 视频放大（75s/¥0.11）

## Day 25 进度 (高级视频控制技术 — Advanced Video Control Techniques) ✅
- [x] 视频控制技术全景
  - [x] 6 维控制维度分类（镜头/运动/参考/首尾帧/编辑/多镜头）
  - [x] 技术演进时间线（AnimateDiff 2023 → CameraCtrl → MotionCtrl → Kling O1 → O3 2025 → Seedance 1.5 2026）
- [x] 镜头运动控制 (Camera Control) 深度解析
  - [x] 6DOF 数学基础（3 平移 + 3 旋转）
  - [x] Kling Camera Controls 源码分析（KlingCameraControls / 6 个 float 参数 / 5 种预设 / VALIDATE_INPUTS 验证）
  - [x] KlingCameraControlI2VNode 源码（⚠️ 硬编码 kling-v1-5 / pro / 5s 限制）
  - [x] KlingCameraControlT2VNode（文生视频+相机控制）
  - [x] Seedance 镜头控制（cameraFixed 参数 + Prompt-driven 方式）
  - [x] AnimateDiff CameraCtrl 本地方案（CameraCtrl_pruned.safetensors / RT矩阵注入 / 6 种预设运动 / SD1.5 限制）
  - [x] MotionCtrl 学术方案（SIGGRAPH Asia 2024 / 相机+物体解耦控制 / SVD 版本）
  - [x] 5 种镜头控制方案全维度对比（精度/画质/成本/GPU/生态）
- [x] 运动控制 (Motion Control) 深度解析
  - [x] Motion Control 概念与原理（参考视频动作提取→迁移到目标角色）
  - [x] Kling 2.6 → 3.0 Motion Control 演进（Element Binding 面部一致性系统）
  - [x] 3.0 新能力（多角度面部稳定/精确复杂表情/遮挡恢复/镜头运动中保持清晰）
  - [x] Motion Control API 参数详解（characterOrientation video/image 双模式）
  - [x] ComfyUI KlingMotionControl 工作流（3 节点拓扑）
  - [x] 最佳实践（参考图/参考视频要求 + 常见陷阱）
- [x] 参考生视频 (Reference-to-Video) 深度解析
  - [x] 与 Motion Control 关键区别（动作迁移 vs 身份保持）
  - [x] Kling O3 Reference-to-Video（最强大: 视频+7图+声音克隆）
  - [x] Kling O1 / Wan 2.6 / Vidu / Seedance 方案对比
  - [x] ComfyUI KlingOmniEditModel 工作流
- [x] 首尾帧控制 (Start-End-to-Video) 深度解析
  - [x] 与传统帧插值的本质区别（语义理解 vs 像素插值）
  - [x] 6 大应用场景（过渡/变形/场景转换/动作序列/循环/Before-After）
  - [x] Vidu Start-End API 参数详解（duration/resolution/movementAmplitude/bgm）
  - [x] Kling O1 Start-to-End（@Image1/@Image2 prompt 引用）
  - [x] Seedance FLF2V ComfyUI Partner Node
  - [x] 首尾帧设计最佳实践（一致性/变化幅度匹配时长/运动幅度/Prompt引导）
- [x] Kling 模型系列全景（V3/O1/O3）
  - [x] V3 "导演"模式 vs O1 "导演+后期" vs O3 "全能"模式
  - [x] RunningHub 全端点映射表（T2V/I2V/MotionControl/Ref2V/StartEnd × V3/O1/O3）
  - [x] 选择决策树（按需求→模型映射）
- [x] ComfyUI 4 种高级视频控制工作流模式
  - [x] 模式一: 镜头控制 I2V（Camera Controls → I2V）
  - [x] 模式二: 动作迁移（Image + Video → MotionControl）
  - [x] 模式三: 首尾帧控制（首帧+尾帧 → FLF2V）
  - [x] 模式四: 参考生视频（多角度参考 → OmniEdit）
  - [x] 混合管线设计（本地关键帧 + API视频 + 本地后期）
- [x] 成本对比表（7 种功能 × RunningHub 价格）
- [x] RunningHub 实验
  - [x] 实验 #43: 功夫大师关键帧生成（首帧+尾帧，各 20s/¥0.03）
  - [x] 实验 #44: Vidu 首尾帧生视频（站立→飞踢过渡，90s/¥0.20）
  - [x] 实验 #45: Seedance Prompt 镜头控制（环绕式镜头，70s/¥0.30）

## Day 26 进度 (音频生成与多模态工作流 — Audio Generation & Multimodal Workflows) ✅
- [x] 音频生成技术全景
  - [x] 音频 AI 三大方向（Text-to-Music / Text-to-Speech / Text-to-SFX）
  - [x] 两大技术范式对比（自回归 Transformer + Codec vs 潜空间扩散 DiT）
- [x] 核心音频模型深度分析
  - [x] MusicGen 架构（EnCodec 4 codebook × 50Hz + 延迟交错模式 + T5 条件 + Melody Conditioning）
  - [x] MusicGen 模型变体（small 300M / medium 1.5B / large 3.3B / melody）
  - [x] Stable Audio Open 架构（arXiv:2407.14358 / DiT 1057M + 音频 VAE 2048x 压缩 + Timing Conditioning）
  - [x] Stable Audio 2.5 Partner Node（3 分钟 < 2 秒 / 商用许可 / Text-to-Audio + Audio-to-Audio + Inpainting）
  - [x] AudioLDM 2 架构（GPT-2 "Language of Audio" + AudioMAE 潜空间 + 多模态输入）
  - [x] MiniMax Music 2.5（自回归 Transformer / 完整歌曲含人声）
  - [x] MiniMax Speech 2.8（HD + Turbo 版本 / 多语言 / Voice Clone）
- [x] ComfyUI 音频节点生态全景
  - [x] LTX-2.3 原生音频节点体系（8 节点 / MultimodalGuider / 音频条件 I2V）
  - [x] Stable Audio 2.5 Partner Nodes（3 节点 / AUTH_TOKEN_COMFY_ORG）
  - [x] Kling 音频 Partner Nodes（T2V+Audio / I2V+Audio / V2A / LipSync）
  - [x] comfyui-sound-lab（MusicGen + Stable Audio Open 本地推理）
  - [x] TTS 节点生态（6+ 节点包: TTS-Audio-Suite / XTTS / F5-TTS / Qwen3-TTS / FishAudioS2 / StepAudio）
  - [x] Lip Sync 节点生态（Wav2Lip / LatentSync / SadTalker / Kling）
- [x] 音频模型架构对比
  - [x] 9 模型全维度对比表（类型/架构/参数/本地vs API/时长/用途）
  - [x] 音频 VAE vs 图像 VAE 深度对比（压缩比/潜空间/解码器/训练目标）
  - [x] EnCodec RVQ（残差向量量化）原理详解
- [x] 视频+音频多模态工作流
  - [x] 三种音视频同步策略（原生同时生成 / 视频→后配音 / 音频驱动视频）
  - [x] 生产级四层管线设计（视觉→音频→同步→后期）
  - [x] LTX-2.3 音频同步 I2V 工作流 JSON 骨架
  - [x] 后配音混音工作流设计
- [x] 唇形同步技术深度
  - [x] 5 种方案全维度对比（Wav2Lip / SadTalker / LatentSync / Kling / LTX-2.3）
  - [x] LatentSync 架构解析（Whisper + 潜空间扩散 / 无中间运动表示）
  - [x] 唇同步决策树
- [x] 完整短视频成本估算（30s 视频全栈 ¥0.59-0.62）
- [x] RunningHub 实验
  - [x] 实验 #46: MiniMax Music 2.5 音乐生成（60s/¥0.14/1.6MB）
  - [x] 实验 #47: MiniMax Speech 2.8 HD 语音合成（10s/¥0.016/213KB）

## Day 27 进度 (Wan 视频生成模型深度解析 — Wan Video Generation Deep Dive) ✅

- [x] Wan 全系列版本演进（2025.03-2026.03 完整时间线）
  - [x] Wan 2.1 首发（T2V-1.3B/14B + I2V-14B）
  - [x] Wan 2.1 VACE 统一视频编辑模型
  - [x] Wan 2.2 MoE 架构升级（T2V-A14B / I2V-A14B / TI2V-5B）
  - [x] Wan 2.2-S2V-14B 音频驱动视频
  - [x] Wan 2.2-Animate-14B 角色动画与替换
  - [x] Wan 2.6（API Only，未开源权重）
- [x] Wan-VAE 3D 因果变分自编码器深度
  - [x] 3D 因果卷积原理（时空压缩 4×8×8 = 256，因果性单向 padding）
  - [x] Wan 2.2 新 VAE（4×16×16 = 1024 超高压缩比，5B 专用）
  - [x] 第一帧独立编码（兼容图像输入）
- [x] UMT5-XXL 文本编码器
  - [x] 多语言原生支持（101 种语言）
  - [x] vs T5-XXL / mT5-XXL / Gemma 3 对比
  - [x] FP16 vs FP8 加载选择
- [x] Wan 2.2 MoE 架构革新
  - [x] SNR 阈值时间步切换机制
  - [x] 高噪声专家（布局/构图/主体）+ 低噪声专家（细节/纹理/精炼）
  - [x] 27B 总参数 / 14B 每步活跃（推理成本≈Wan 2.1）
  - [x] vs 传统逐 token MoE 路由的区别
  - [x] 训练数据增量（+65.6% 图片 / +83.2% 视频）
- [x] VACE 统一视频编辑框架
  - [x] 8 种任务单模型（T2V/I2V/V2V/运动迁移/局部替换/扩展/背景替换/参考生成）
  - [x] ComfyUI Bypass 节点切换模式
  - [x] 性能参考（4090: 640×640 49帧 ~7min, 720P 81帧 ~40min）
- [x] ComfyUI 集成对比
  - [x] 原生节点体系（Load Diffusion Model / CLIPLoader / EmptyHunyuanLatentVideo）
  - [x] kijai WanVideoWrapper（TeaCache/MagCache/GGUF/Animate/S2V/面部控制）
  - [x] 8 维度深度对比表
- [x] 本地部署 GPU 需求与优化
  - [x] VRAM 需求矩阵（6 种配置）
  - [x] 消费级 vs 数据中心优化策略
  - [x] 7 种前沿优化（TeaCache/MagCache/CausVid/GGUF/LightX2V/FastVideo/Cache-dit）
  - [x] 部署成本对比表
- [x] 开源视频模型生态对比
  - [x] 6 家模型全维度对比（Wan/HunyuanVideo/CogVideoX/LTX/Mochi/Open-Sora）
  - [x] Wan 2.2 vs 竞品 10 维度详细对比
- [x] 5 种 ComfyUI 工作流模式
  - [x] 纯本地 Wan / VACE 多任务 / 混合管线 / 多模态 S2V / 角色动画
- [x] RunningHub 实验
  - [x] 关键帧生成: rhart-image-n-pro T2I（25s/¥0.03）
  - [x] 实验 #48: Wan 2.6 T2V 龙虾厨师（50s/¥0.63）
  - [x] 实验 #49: Wan 2.6 I2V 金龙穿雾（210s/¥0.63）
  - [x] 总成本: ¥1.29

## Day 28 进度 (SD 微调技术全景 + ComfyUI 工作流工程化) ✅

- [x] SD 微调方法全景（5 种方法完整对比）
  - [x] 方法分类与修改范围排列（TI → HN → LoRA → DB → Full）
  - [x] 5 方法全维度对比表（12 个维度）
  - [x] 方法选择决策树
- [x] Textual Inversion 深度解析
  - [x] 论文原理（Gal et al., 2022, arXiv:2208.01618）
  - [x] 数学公式（仅优化 embedding 向量 v*，冻结 U-Net/VAE/其他 token）
  - [x] 训练核心伪代码（梯度 mask 只保留新 token）
  - [x] 多 Token Embedding（1-16 tokens / 容量 vs prompt 空间权衡）
  - [x] 训练参数推荐（SD1.5 vs SDXL）
  - [x] ComfyUI 使用方式（embedding:xxx 语法 / 加载机制源码分析）
  - [x] 文件格式（.pt 旧式 vs .safetensors 新式）
  - [x] 经典 Negative Embedding 案例（EasyNegative / badhandv4 / FastNegativeV2）
- [x] DreamBooth 深度解析
  - [x] 论文原理（Ruiz et al., Google, 2022, arXiv:2208.12242）
  - [x] 两步训练法（实例微调 + Prior Preservation Loss）
  - [x] Prior Preservation Loss 数学（L_total = L_instance + λ × L_prior）
  - [x] 防语言漂移/过拟合的机制
  - [x] DreamBooth + LoRA 现代最佳实践（kohya_ss 配置示例）
  - [x] DreamBooth vs Full Fine-tune 对比
- [x] Hypernetwork 原理与弃用
  - [x] Cross-Attention K/V 修改架构
  - [x] HN 小型 MLP 结构（Input → Linear → Dropout → GELU → Linear → Output）
  - [x] 弃用原因分析（LoRA 全面超越 4 个维度）
  - [x] 2024+ 社区共识：不应再使用
- [x] ComfyUI Subgraph 系统（现代标准）
  - [x] 概念与创建流程（选中 → 点击图标 → 自动分析 IO）
  - [x] 内部结构（Input/Output Slots + 内部节点图）
  - [x] Subgraph vs Group Nodes (Legacy) 全维度对比（6 个维度）
  - [x] 编辑模式与参数面板（v0.3.66+）
- [x] App Mode & App Builder & ComfyHub (2026 新特性)
  - [x] App Mode 概念（一键从节点图切换到用户界面）
  - [x] App Builder 配置（选择暴露的输入/输出）
  - [x] URL 分享机制（编码工作流 + 布局 + 绑定）
  - [x] ComfyHub 公共平台（创作者发布 App 和工作流）
- [x] ComfyUI Node Registry
  - [x] 发布流程（Publisher 账号 → pyproject.toml → comfy node publish）
  - [x] GitHub Actions CI/CD 自动发布配置
- [x] 工作流设计模式（5 种）
  - [x] 管线模式 / 分支合并 / 多阶段精炼 / 条件路由 / 迭代循环
  - [x] 最佳实践（命名规范 / 模块化原则 / 版本管理）
- [x] ComfyUI 生态系统全景 2026 Q1（开发层 + 平台层 + 用户层）
- [x] RunningHub 实验
  - [x] 实验 #50: 微调技术全景信息图（35s/¥0.03）

## Day 29 进度 (Flux 实战工作流生态) ✅

- [x] Flux 模型家族全景梳理
  - [x] FLUX.1 系列（pro/dev/schnell/Ultra）版本对比
  - [x] FLUX.1 Tools 套件（Fill/Depth/Canny/Redux）四大工具深度解析
  - [x] FLUX.1 Kontext（2025-05）— 上下文感知编辑模型
  - [x] FLUX.2 Klein（2026-01）— 4B/9B 紧凑高速模型（Apache 2.0）
  - [x] Flux 生态演进路线（2024-08 → 2026-01）
- [x] Flux ControlNet 生态深度解析
  - [x] BFL 官方 Canny Dev（完整模型 12B）
  - [x] BFL 官方 Depth Dev LoRA（适配器版）
  - [x] 完整版 vs LoRA 版对比（大小/质量/灵活性）
  - [x] Shakker-Labs ControlNet-Union-Pro-2.0（3.98GB/5 种模式/推荐参数）
  - [x] XLabs-AI ControlNet（Canny V3/Depth/HED + IP-Adapter beta）
  - [x] InstantX 独立 ControlNet + IP-Adapter
  - [x] ComfyUI 三种使用模式（完整/LoRA/Union）
- [x] Flux Fill 工作流详解
  - [x] Inpainting 核心节点链路（InpaintModelConditioning）
  - [x] Outpainting（Pad Image for Outpainting）
  - [x] Flux Fill vs 传统 SD Inpainting 对比
- [x] Flux Redux 工作流详解
  - [x] Redux 架构（SigLIP → Style Adapter）
  - [x] ComfyUI 节点链路（LoadStyleModel + CLIPVisionEncode + StyleModelApply）
  - [x] AdvancedRefluxControl 自定义节点（解决过强问题）
  - [x] Redux vs IP-Adapter 对比（6 个维度）
- [x] FLUX.2 Klein ComfyUI 工作流
  - [x] T2I / 图像编辑 / 多参考图编辑 三种工作流
  - [x] 4B vs 9B / base vs distilled 选型
- [x] Flux 量化方案与低 VRAM 实践
  - [x] BF16/NF4/GGUF Q5/Q4/FP8/NVFP4 六种方案对比
  - [x] NF4 工作流模式（UnetLoaderGGUF + guidance 参数调整）
- [x] Flux 工作流最佳实践
  - [x] Flux vs SD/SDXL 5 大工作流差异
  - [x] 组合模式（ControlNet+Redux / ControlNet+LoRA / Fill+ControlNet）
  - [x] 5 阶段生产级管线推荐
  - [x] 选型决策树
- [x] ComfyUI 工作流 JSON 编写
  - [x] flux-controlnet-canny-basic.json（Canny ControlNet 基础工作流）
  - [x] flux-fill-inpainting-basic.json（Fill Inpainting 基础工作流）
- [x] RunningHub 实验
  - [x] 实验 #51: T2I 日式庭园基准（rhart-image-n-pro, 20s/¥0.03）
  - [x] 实验 #52: I2I 风格迁移（写实→魔幻, 20s/¥0.03）

## Day 30 进度 (快速推理与蒸馏技术 — Fast Inference & Distillation Techniques) ✅

- [x] 蒸馏方法学术体系全景
  - [x] 四大蒸馏家族分类（一致性/对抗/分布匹配/混合）
  - [x] 完整技术演进时间线（2022.04 PD → 2025.03 SANA-Sprint）
  - [x] 12+ 种蒸馏方法系统梳理
- [x] 一致性蒸馏 (Consistency Distillation) 深度解析
  - [x] Consistency Models 原理（Song et al., ICML 2023）— PF-ODE 轨迹一致性 / 自一致性函数 / skip connection 参数化 / CD vs CT 两种训练
  - [x] LCM 潜空间一致性模型（增广 PF-ODE / CFG 内化 / LCM-LoRA 即插即用创新）
  - [x] PCM 分段一致性模型（NeurIPS 2024 — LCM 三个缺陷 / 分段 ODE 解决累积误差 / 灵活 CFG / 支持视频）
  - [x] ECM 易训一致性模型（ICLR 2025 — loss 权重修正 / 1 小时单卡 A100 / 训练成本降 100x）
- [x] 对抗式蒸馏 (Adversarial Distillation) 深度解析
  - [x] ADD 原理（Stability AI, 2023 — 三组件架构 / DINOv2 判别器 / 蒸馏+对抗双 loss → SDXL Turbo）
  - [x] ADD 的四大局限（固定分辨率 / pixel space / 不可控特征 / 训练不稳定）
  - [x] LADD 原理（SIGGRAPH Asia 2024 — 全潜空间蒸馏 / 扩散模型作判别器 / 噪声级别控制感知 / 任意分辨率 → SD3-Turbo / Flux Schnell）
  - [x] ADD vs LADD 全维度对比（6 个维度）
  - [x] SDXL-Lightning 原理（ByteDance — 渐进式+对抗式组合 / Full UNet + LoRA 双格式）
- [x] 分布匹配蒸馏
  - [x] DMD2 原理（NeurIPS 2024 Oral — 分布级 KL 散度匹配 / Two-timescale 更新 / FID 1.28 超越教师 / 500x 加速）
- [x] 混合蒸馏方法
  - [x] Hyper-SD 三阶段训练（ByteDance — TSCD + Score Distillation + 人类偏好 / 覆盖 SD1.5/SDXL/SD3/Flux / 1-8 step 全系列）
  - [x] SANA-Sprint 混合蒸馏（NVIDIA, ICCV 2025 — sCM + LADD / 0.03s 1024² / 比 Flux Schnell 快 64x）
- [x] 视频蒸馏
  - [x] AnimateLCM 解耦一致性学习（SIGGRAPH Asia 2024 — 先图像后视频 / 4 步视频生成 / ComfyUI AnimateDiff-Evolved 集成）
  - [x] CausVid 因果视频蒸馏（CVPR 2025 — 双向→因果自回归 / 实时流式视频）
- [x] Flux 快速推理特殊机制
  - [x] Flux Dev: Guidance Distillation（guidance scale 作为模型输入 / 单次 forward 替代双次）
  - [x] Flux Schnell: LADD 蒸馏（1-4 步 / Apache 2.0）
  - [x] FLUX.2 Klein: 架构蒸馏（12B → 4B/9B）
- [x] ComfyUI 快速推理实战汇总
  - [x] 10 种方法 ComfyUI 配置速查表（sampler/scheduler/steps/cfg 全参数）
  - [x] CFG 行为分类（内化 vs 灵活 vs 显式）
  - [x] 方法选择决策树（按基础模型+需求分支）
- [x] 蒸馏方法深度对比
  - [x] 学术指标对比（FID/CLIP Score/Aes Score）
  - [x] 实用维度对比（LoRA兼容/ControlNet兼容/Negative Prompt/灵活步数/分辨率）
- [x] 2 个 ComfyUI 工作流 JSON
  - [x] sdxl-lightning-4step-lora.json（SDXL-Lightning LoRA 快速工作流）
  - [x] lcm-lora-sdxl.json（LCM-LoRA 即插即用快速工作流）
- [x] RunningHub 实验
  - [x] 实验 #53: 蒸馏技术全景概念信息图（rhart-image-n-pro, 30s/¥0.03）

## Day 31 进度 (图像编辑工作流 — Image Editing Workflows) ✅

- [x] 图像编辑技术全景
  - [x] 三大编辑范式对比（Training-Free / Fine-tuning / Hybrid-InContext）
  - [x] 编辑任务分类（局部/全局/结构/文本/语义 5 大类）
  - [x] 技术演进时间线（2022.11 InstructPix2Pix → 2025.12 Qwen-Image-Layered）
- [x] InstructPix2Pix 深度解析
  - [x] 训练数据生成管线（GPT-3 + Prompt-to-Prompt + CLIP 过滤，454K 三元组）
  - [x] 架构修改（U-Net 输入通道 4→8，额外 4 通道零初始化）
  - [x] 双 Classifier-Free Guidance 机制（s_I 图像引导 + s_T 文本引导，三次前向传播）
  - [x] CosXL Edit（SDXL 版本，EDM2 cosine schedule）
  - [x] ComfyUI InstructPixToPixConditioning 节点分析
  - [x] 局限性分析（数据偏差/指令理解/ID保持/分辨率/不可逆编辑）
- [x] ICEdit In-Context 编辑新范式（NeurIPS 2025）
  - [x] Diptych 范式原理（左面板源图 + 右面板编辑结果 + IC Prompt 构造）
  - [x] DiT 原生上下文感知能力利用（零样本 baseline）
  - [x] LoRA-MoE 混合微调策略（多 Expert 动态路由 / 0.5% 数据 + 1% 参数）
  - [x] Early Filter 推理时间缩放（VLM-based 噪声筛选）
  - [x] 性能对比（超越 InstructPix2Pix/UltraEdit / VIE-Score 78.2 超商业系统 / ID 超 GPT-4o）
  - [x] ComfyUI 集成（ICEditNode / MoE 4GB VRAM / 高分辨率精炼模块）
  - [x] 与传统方法的本质区别（通道拼接 vs DiT 自注意力）
- [x] Flux Fill 高级 Inpainting/Outpainting
  - [x] 与传统 SD Inpainting 的区别（DiT 12B / 原生高分辨率 / 上下文理解）
  - [x] InpaintModelConditioning 源码分析（mask 置零 / latent 空间 mask / concat 注入）
  - [x] Inpainting 工作流（guidance=30.0 / euler+simple / 28步）
  - [x] Outpainting 工作流（PadImageForOutpainting / feathering / 分步扩展策略）
  - [x] 自动 Mask 生成管线（GroundingDINO + SAM2 + Flux Fill）
  - [x] 多区域迭代编辑模式
- [x] Flux Kontext 上下文感知编辑
  - [x] 模型版本（Pro/Max/Dev / arXiv:2506.15742）
  - [x] 五大核心能力（角色一致性/精确编辑/风格参考/多图输入/多轮迭代）
  - [x] 架构原理（image tokens + text tokens → joint attention → 编辑输出）
  - [x] ComfyUI Dev 工作流（FluxKontextImageEncode / guidance 2.5-10.0）
  - [x] Prompt 技巧（指令式 vs 描述式 / 负面约束 / 精确修改）
  - [x] Kontext vs Fill vs ICEdit 三方对比（6 维度）
- [x] VACE 统一视频/图像编辑框架
  - [x] 8 种任务覆盖（T2V/I2V/V2V/Motion/Replace/Extend/Background/Reference）
  - [x] 视频 Inpainting 工作流（WanVaceToVideo / mask 序列 / 动态编辑区域）
  - [x] 视频 Outpainting 工作流（WanVacePadAndMask）
  - [x] 图像编辑视角下的 VACE（单帧 V2V / 语义理解强 / 但 overkill）
- [x] Qwen-Image-Edit 双语文本编辑专家
  - [x] 20B 模型双通路架构（Qwen2.5-VL 语义控制 + VAE 外观控制）
  - [x] 文本编辑能力（添加/修改/删除 / 中英双语 / 保持字体样式）
  - [x] ComfyUI 原生集成（fp8 / Lightning 4步加速 / ScaleImageToTotalPixels）
  - [x] Qwen-Image-Layered 分层编辑扩展（RGBA 图层独立编辑）
- [x] OmniGen2 统一多模态
  - [x] 7B 架构（3B VLM + 4B DiT）
  - [x] 编辑能力（6 种操作 / 多图引用语法 <image_N>）
  - [x] ComfyUI 原生支持（2025-07+）
  - [x] 与专用编辑模型全维度对比
- [x] ComfyUI 编辑节点体系总览
  - [x] 内置节点（InstructPixToPix/InpaintModel/SetMask/PadImage/FluxGuidance/FluxKontextImageEncode）
  - [x] 第三方节点（ICEdit/QwenEditUtils/OmniGen2/Impact Pack/RMBG/SAM/Florence2）
  - [x] 9 种编辑任务推荐方案对照表
- [x] 全方法 9 维度对比 + 方法选择决策树
- [x] 4 种生产级编辑工作流模式
  - [x] 精确局部编辑管线（GroundingDINO+SAM2+Flux Fill+FaceDetailer）
  - [x] 多轮迭代编辑（Kontext→Fill→Qwen-Edit 链式）
  - [x] 批量产品图编辑（RMBG+Fill+Qwen-Edit 自动化）
  - [x] 图像→视频编辑管线（ICEdit→I2V→VACE）
- [x] RunningHub 实验
  - [x] 实验 #54: 图像编辑技术全景概念图（rhart-image-n-pro T2I, 35s/¥0.03）
  - [x] 实验 #55: 图生图风格编辑（rhart-image-n-pro edit, 30s/¥0.03）
  - [x] 实验 #56: Qwen 2.0 Pro 图像编辑（qwen-image-2.0-pro, 20s/¥0.05）

## Day 32 进度 (3D 生成与多视角 — 3D Generation & Multi-View) ✅

- [x] 3D 生成技术全景
  - [x] 核心范式演进时间线（NeRF 2020 → 3DGS 2023 → Feed-Forward 2024 → DiT 3D 2025 → 统一潜空间 2026）
  - [x] 三大技术路线分类（多视图扩散+重建 / 直接3D生成 / 前馈重建）
- [x] 五种核心 3D 表示深度对比
  - [x] NeRF（隐式函数 F(x,y,z,θ,φ)→RGB,σ / 体积渲染 / 位置编码 / Instant-NGP/TensoRF 变体）
  - [x] 3D Gaussian Splatting 深度解析（59 浮点属性/球谐函数/Tile-based光栅化/α-Blending/自适应密度控制 Clone/Split/Prune）
  - [x] Mesh（顶点+边+面 / UV映射 / PBR材质 / 工业标准格式 .obj/.glb/.fbx/.stl）
  - [x] Triplane（三正交平面特征图 / TripoSR/InstantMesh使用 / MarchingCubes转换）
  - [x] O-Voxel/Sparse Voxels（TRELLIS.2 / field-free稀疏体素 / Flexible Dual Grids / PBR属性）
  - [x] 5种表示全维度对比表（渲染速度/编辑性/工业兼容/内存/质量）
- [x] Mesh 提取算法
  - [x] Marching Cubes（1987经典 / 256构型查表 / 局限：分辨率/锐利特征）
  - [x] DMTet Deep Marching Tetrahedra（NeurIPS 2021 / NVIDIA / 可微分/SDF+偏移联合优化）
  - [x] FlexiCubes（SIGGRAPH 2023 / NVIDIA / 双网格 / 薄结构+锐利边缘 / InstantMesh使用）
- [x] 核心 3D 生成模型深度分析（7个模型）
  - [x] TripoSR（Tripo AI+Stability AI 2024 / LRM架构+DINOv2 / Triplane / <0.5s / 300M / MIT）
  - [x] TripoSG（Tripo AI 2025.04 / 1.5B / Rectified Flow直接3D / 高保真形状 / CFG蒸馏草图版 / MIT）
  - [x] Zero123++（SUDO-AI-3D 2023.10 / SD2.1微调 / 6固定视角一致多视图 / 条件机制 / 共享噪声）
  - [x] InstantMesh（TencentARC 2024.04 / Zero123++→LRM重建 / FlexiCubes / 训练可扩展性 / ~10s）
  - [x] TRELLIS（Microsoft CVPR'25 Spotlight / SLAT统一潜空间 / DINOv2特征 / TRELLIS-500K数据集）
  - [x] TRELLIS.2（Microsoft 2025.12 / O-Voxel / SC-VAE 16×下采样~9.6K tokens / 4B DiT / 3-60s / 1536³ / 任意拓扑+PBR）
  - [x] Hunyuan3D全系列（v1→v2→v2.1→v3→v3.1 / 两阶段DiT+ShapeVAE+Paint / 10B / PBR / quad拓扑 / 8视图重建）
- [x] ComfyUI 3D 节点生态
  - [x] ComfyUI-3D-Pack 核心节点（MrForExample / 10+生成模型 + 5算法 + 后处理 / 活跃维护）
  - [x] ComfyUI-Sharp（Apple SHARP / 单图→3DGS <1s）
  - [x] comfyui-3d-gs-renderer（3DGS渲染器节点）
  - [x] VAST-AI ComfyUI-Tripo（Tripo API官方节点）
  - [x] ComfyUI原生 Hunyuan3D 节点
- [x] 5种 ComfyUI 3D 工作流模式
  - [x] 模式一：单图快速重建（TripoSR/TripoSG, 1-5s）
  - [x] 模式二：多视图重建（Zero123++→InstantMesh→FlexiCubes, ~10s）
  - [x] 模式三：高质量两阶段（Hunyuan3D DiT+Paint, 20-60s）
  - [x] 模式四：TRELLIS.2 高分辨率（512³-1536³, 3-60s）
  - [x] 模式五：3D→2D渲染回路（3D辅助角色一致性/视频生成）
- [x] 3D + 2D 管线整合
  - [x] 3D辅助角色一致性（单图→mesh→多角度渲染→ControlNet参考）
  - [x] 3D驱动视频生成（mesh→关键帧序列→I2V）
  - [x] 产品展示管线（照片→RMBG→Hunyuan3D→PBR→360°视频）
- [x] 商业 3D 生成平台对比（Tripo/Rodin/Meshy/Hunyuan3D/TRELLIS.2）
- [x] 前沿方向（原生3D扩散/4D动画/PBR重光照）
- [x] 模型选择决策树
- [x] RunningHub 实验
  - [x] 实验 #57: 龙虾厨师3D参考图生成（rhart-image-n-pro T2I, 20s/¥0.03）
  - [x] 实验 #58: Hunyuan3D v3.1 图生3D（OBJ 34MB+纹理12.7MB+MTL, 180s/¥0.80）
  - [x] 实验 #59: Hunyuan3D v3.1 文生3D（OBJ 34.4MB+纹理14.3MB+MTL, 205s/¥0.40）
