# Day 19 — 性能优化（TensorRT / 量化 / 显存管理）

> 学习时间: 2026-03-22 02:03 UTC | 轮次: 27

## 1. ComfyUI 显存 (VRAM) 管理体系

### 1.1 VRAM 消耗的三大来源

| 来源 | 缩放行为 | 典型占用 (SDXL) | 优化策略 |
|------|---------|----------------|---------|
| **模型权重** | 恒定（与分辨率无关） | ~6.5GB (FP16) | 量化/卸载 |
| **激活值 (Activations)** | 线性（分辨率翻倍→~2x） | 可变 | Gradient Checkpointing |
| **注意力矩阵** | **二次方**（分辨率翻倍→~4x） | 可变，高分辨率时暴涨 | xFormers/Flash/Sage |

> 🔑 关键洞察：注意力的二次方缩放是高分辨率 OOM 的根本原因。1024x1024 的注意力内存约为 512x512 的 4 倍。

### 1.2 PyTorch 内存分配器行为

- **块分配**：PyTorch 按 chunk 分配内存，非精确分配
- **碎片化**：长时间运行后，总空闲 VRAM 足够但无连续大块
- `torch.cuda.memory_allocated()` vs `torch.cuda.memory_reserved()`：差值 = 碎片/预分配
- **实践建议**：切换大模型（如 SDXL → Flux）后重启 ComfyUI 清碎片

### 1.3 ComfyUI 内置 VRAM 管理机制

#### Smart Memory（默认启用）
```
model_management.py → load_models_gpu() → free_memory()
```
- 维护全局 `current_loaded_models` 列表，追踪所有已加载模型及内存占用
- `LoadedModel` 类包装每个模型，管理 GPU/CPU 生命周期
- **智能驱逐策略**：需要加载新模型时，按 LRU 策略卸载最久未用模型
- 支持**部分加载/卸载**（只在 GPU 放模型的一部分）

#### Dynamic VRAM（2025年底默认启用）
- ComfyUI 0.5.0+ 引入的大型内存优化
- 核心：动态管理模型在 GPU/CPU 间的分布
- 根据当前工作流需求自适应调整内存分配

#### 启动参数控制 VRAM 策略

| 参数 | 行为 | 适用场景 |
|------|------|---------|
| `--gpu-only` | 全部模型留 GPU，不卸载 | 24GB+ GPU，最快速度 |
| `--highvram` | 尽量多留 GPU | 16GB+ GPU |
| （默认） | Smart Memory 自动管理 | 大多数用户 |
| `--lowvram` | 激进卸载，只保留计算部分 | 4-8GB GPU，速度严重下降 |
| `--novram` / `--cpu` | 全 CPU | 无 GPU / 调试 |
| `--reserve-vram N` | 预留 N GB 给系统 | 共享 GPU 场景 |
| `--disable-smart-memory` | 关闭智能管理 | 调试 / 极低 VRAM |

---

## 2. 精度与量化 — 模型压缩全景

### 2.1 精度格式对比

| 格式 | 位宽 | SDXL 模型大小 | VRAM 占用 | 质量 (vs FP16) | GPU 要求 |
|------|------|-------------|----------|---------------|---------|
| **FP32** | 32-bit | ~13GB | 最高 | 参考 | 任意 |
| **BF16** | 16-bit | ~6.5GB | 中 | ≈100% | Ampere+ (RTX 30xx+) |
| **FP16** | 16-bit | ~6.5GB | 中 | 100%（金标准） | 任意 |
| **FP8** | 8-bit | ~3.25GB | 低 | 95-98% | Ada Lovelace+ (RTX 40xx+) |
| **GGUF Q8_0** | 8-bit | ~3.5GB | 中低 | 90-95% | 广泛兼容 |
| **GGUF Q5_K** | 5-bit | ~2.2GB | 低 | 85-90% | 广泛兼容 |
| **NF4** | 4-bit | ~1.6GB | 最低 | 75-85% | 需 BitsAndBytes |
| **NVFP4** | 4-bit | ~1.6GB | 最低 | 90-95% | Blackwell (RTX 50xx) |

### 2.2 FP16 vs BF16 选择

```
FP16: 精度 ~3 位有效数字, 范围 5.96e-8 ~ 65504
      → 精度高但范围窄，VAE 解码偶尔 NaN
      
BF16: 精度 ~2 位有效数字, 范围 ~1e-38 ~ 1e38
      → 精度略低但范围等同 FP32，数值更稳定
      → 需要 Ampere+ GPU (RTX 30xx/40xx/A100)
```

**选择策略**：
- 大多数推理 → FP16（兼容性最好）
- 数值不稳定（NaN）→ 尝试 BF16
- 训练 → BF16 优先（梯度稳定性）
- FP32 → 仅调试用，永不生产

### 2.3 GGUF 量化深度解析

**来源**: 来自 llama.cpp 生态，city96 将其引入 SD 生态

**核心原理**：
- 按 block 存储权重（如 32 个值一组）
- 每个 block 有独立的缩放因子 → 有效范围远超等位宽的浮点
- Q8_0: 每值 8 位 + block 缩放因子
- Q4_K_M: 每值 4 位 + 多级缩放（K-quant）

**ComfyUI 集成**（city96/ComfyUI-GGUF）：
```
安装: git clone → pip install gguf
节点: "Unet Loader (GGUF)" 替换 "Load Diffusion Model"
模型放: ComfyUI/models/unet/
LoRA: 实验性支持，使用内置 LoRA Loader
```

**关键限制**：
- 传统 U-Net 模型（conv2d）量化质量损失大
- DiT/Transformer 模型（Flux/SD3）量化效果好 ← 因为线性层为主
- GGUF 速度通常比 FP8 慢（需要反量化步骤）
- 但 VRAM 占用可以更低（Q4/Q5 比 FP8 更省）

**可用预量化模型**：
- city96/FLUX.1-dev-gguf (Q2_K ~ Q8_0)
- city96/FLUX.1-schnell-gguf
- city96/stable-diffusion-3.5-large-gguf
- city96/t5-v1_1-xxl-encoder-gguf (文本编码器也可量化)

### 2.4 FP8 vs GGUF Q8 对比

| 维度 | FP8 | GGUF Q8_0 |
|------|-----|----------|
| 存储方式 | 原生 8-bit 浮点 | 8-bit 整数 + block 缩放 |
| GPU 加速 | RTX 40xx+ 原生 FP8 硬件 | 需反量化，CPU-like 操作 |
| 速度 | 快（有硬件加速） | 中等（反量化开销） |
| 质量 | 略优（保留浮点特性） | 接近（block 缩放补偿） |
| VRAM | 约等 | 约等（含缩放因子略大） |
| LoRA 兼容 | 好 | 实验性 |
| 适用 | 有 RTX 40xx+ 的用户 | 广泛兼容，低端 GPU |

### 2.5 NF4 (BitsAndBytes) 与 NVFP4 (Nunchaku)

#### NF4 — 4-bit Normal Float
- 来自 QLoRA 论文的量化方法
- 假设权重服从正态分布 → 用 4-bit 编码分位数
- 通过 BitsAndBytes 库实现
- 质量损失明显但可用，适合极低 VRAM 场景

#### NVFP4 — NVIDIA Blackwell 原生 4-bit
- **SVDQuant** (ICLR 2025 Spotlight): 用低秩分量吸收离群值
- Nunchaku 引擎: `nunchaku-ai/nunchaku` + `ComfyUI-nunchaku`
- RTX 5090 上相比 BF16 约 **3x 加速**
- 相比 INT4 质量显著更好（保留浮点动态范围）

**ComfyUI 原生 NVFP4 支持** (blog.comfy.org 2026-01-09):
- 需要 PyTorch cu130 才能获得完整加速
- 否则 NVFP4 反而比 FP8 慢 2x
- 仅限 Blackwell GPU（RTX 50xx 系列）

---

## 3. 注意力优化

### 3.1 注意力优化方法对比

| 方法 | 内存缩放 | 速度 | GPU 要求 | 安装 |
|------|---------|------|---------|------|
| **标准 PyTorch** | O(L²) 二次方 | 基准 | 任意 | 内置 |
| **xFormers** | O(L) 近线性 | +20% | CUDA | `pip install xformers` |
| **Flash Attention** | O(L) 近线性 | +25-30% | Ampere+ | 内置/编译 |
| **SageAttention** | O(L) 近线性 | +30-40% | 需 Triton | 需编译 |
| **PyTorch SDPA** | 自动选择 | +15-25% | PyTorch 2.0+ | 内置 |
| **Attention Slicing** | O(chunk) | -50-75% | 任意 | 内置 |

### 3.2 启用方式（ComfyUI 启动参数）

```bash
# 推荐顺序: SageAttention > Flash Attention > xFormers > SDPA
python main.py --use-sage-attention      # 最快，需 Triton
python main.py --use-flash-attention     # 快+省，需 Ampere+
python main.py --use-xformers           # 可靠，广泛兼容
python main.py --use-pytorch-cross-attention  # 自动选择
python main.py --attention-slice        # 最后手段，极慢但极省
```

### 3.3 各方法原理简析

**xFormers Memory-Efficient Attention**:
- 分块（chunked）计算注意力，不一次性物化整个 L×L 矩阵
- 内存从 O(L²) 降到 O(L)
- 更好的缓存局部性 → 速度也提升

**Flash Attention** (Dao et al.):
- IO-Aware: 融合操作减少 HBM ↔ SRAM 传输
- Tiling + 在线 softmax + 重计算
- 无需中间 O(L²) 矩阵
- 比 xFormers 更快，但要求更严格

**SageAttention**:
- 自定义 Triton kernel
- 针对特定 GPU 架构深度优化
- 性能通常最优，但兼容性需要测试
- 高 CFG 下可能有轻微纹理伪影

---

## 4. 卸载与分层优化

### 4.1 组件卸载策略

| 卸载类型 | 节省 VRAM | 速度影响 | 启用方式 |
|---------|----------|---------|---------|
| **文本编码器卸载** | 1-2GB | 极小（几秒） | `--cpu-text-encoder` |
| **VAE 卸载** | 160-320MB | 小 | `--cpu-vae` |
| **模型卸载 (lowvram)** | 巨大 | 严重 (5-10x 慢) | `--lowvram` |
| **顺序卸载** | 最大 | 极严重 | `--novram` |

### 4.2 Async Offloading + Pinned Memory（2025年12月默认启用）

ComfyUI 官方优化，适用于所有 NVIDIA GPU：

**核心原理**：
- **Pinned Memory**: 将 CPU RAM 标记为"页锁定"，避免 OS 换页
  - GPU DMA 引擎可直接访问，减少传输延迟
- **Async Offloading**: 权重传输与 GPU 计算异步并行
  - 当前层计算时，下一层权重已在传输中
  - 需要 PCIe 带宽支持（PCIe 4.0 x16 效果好，PCIe 5.0 更佳）

**性能提升**：采样速度提升 10-50%（仅在需要卸载时有效）

**关键条件**：
- 只有当模型无法完全载入 VRAM 时才有效
- PCIe 代数和通道数直接影响收益
- PCIe 4.0 x8 效果不明显，4.0 x16 良好，5.0 x16 最佳

---

## 5. TensorRT 加速

### 5.1 原理

NVIDIA TensorRT = 推理优化 SDK：
1. **图优化**: 合并冗余操作、常量折叠
2. **核融合**: 多个 kernel 合并为一个（减少 launch 开销）
3. **精度校准**: 自动混合精度（FP16/INT8）
4. **特定 GPU 优化**: 为你的 GPU 生成定制 engine

### 5.2 ComfyUI_TensorRT 节点

**官方仓库**: `comfyanonymous/ComfyUI_TensorRT`

**支持模型**: SD 1.5 / 2.1 / 3.0 / SDXL / SDXL Turbo / SVD / SVD-XT / AuraFlow / Flux

**两种 Engine 类型**:

| 类型 | 分辨率 | 性能 | VRAM | 适用 |
|------|--------|------|------|------|
| **Static** | 固定分辨率+batch | 最优 | 最少 | 固定用途 |
| **Dynamic** | min/opt/max 范围 | 在 opt 时最优 | 较多 | 通用 |

**构建流程**:
1. Load Checkpoint → TensorRT Conversion Node（Static/Dynamic）
2. Queue Prompt → 等待 engine 构建（3-60分钟）
3. 使用 TensorRT Loader 加载 engine
4. 连接到 KSampler（CLIP/VAE 仍用原始 checkpoint）

**性能提升**: 
- SD 1.5: 约 **2-3x** 加速
- SDXL: 约 **1.5-2x** 加速
- RTX 3090 实测: 3x 加速 (Reddit 报告)

**重大限制**:
- ⚠️ **不兼容 ControlNet 和 LoRA**（截至 2026 年初）
- Engine 绑定特定 GPU（换卡需重建）
- 构建时间长
- 动态范围越宽 VRAM 占用越大

### 5.3 TensorRT 决策树

```
需要 ControlNet/LoRA?
├── 是 → ❌ 不要用 TensorRT，用 xFormers/SageAttention
└── 否 → 固定分辨率/batch?
    ├── 是 → Static Engine（最快）
    └── 否 → Dynamic Engine（opt 参数设为最常用分辨率）
```

---

## 6. torch.compile 优化

### 6.1 概述

PyTorch 2.0+ 引入 `torch.compile()`，JIT 编译模型图：
- 自动核融合
- 消除冗余计算
- 优化内存访问模式

### 6.2 ComfyUI 中的 torch.compile

**内置节点**: `TorchCompileModel`（ComfyUI 原生支持）

**使用方式**:
```
Load Model → TorchCompileModel → KSampler
```

**性能**:
- GGUF Q8_0 Flux: **~30% 加速** (Reddit 实测 with nightly PyTorch)
- 首次推理有编译开销（几十秒到几分钟）
- 后续推理速度持续受益
- 与 SageAttention 组合效果最佳

**注意事项**:
- PyTorch 版本敏感（2.7 在某些场景比 2.8 快）
- 与 Triton/SageAttention 的兼容性需要测试
- LoRA 切换可能触发重编译 → 有 "LoRA-Safe TorchCompile" 社区节点

---

## 7. VAE 分块处理（Tiled VAE）

### 7.1 原理

VAE 编码/解码是内存密集操作，尤其高分辨率时：
- 将图像切成小块（tiles）分别处理
- 块间有重叠（overlap）确保边缘平滑
- 块大小通常 512 或 256

### 7.2 ComfyUI 节点

- 内置: `VAEDecodeTiled` / `VAEEncodeTiled`
- 参数: `tile_size`（256-512 常用）

### 7.3 效果

- RTX 4090 实测: VRAM 从 14GB → 8GB（约 43% 节省）
- 速度: 增加约 1 秒（微小开销）
- 对质量几乎无影响（重叠区域平滑融合）

---

## 8. 综合优化策略决策树

```
你的 GPU VRAM 是多少？

24GB+ (4090/5090/A100):
├── 速度优先 → TensorRT (无LoRA/CN) 或 SageAttention + torch.compile + FP16
├── 灵活性优先 → SageAttention + FP16 + --highvram
└── 批量生产 → FP8 + xFormers + --gpu-only

12-16GB (4070Ti/4080/5070Ti):
├── FP16 能装下 → xFormers/Flash + 默认 smart memory
├── 装不下 → FP8 + xFormers + --cpu-text-encoder
└── 视频模型 → GGUF Q5_K + Tiled VAE + --cpu-text-encoder

8GB (3070/4060):
├── SD1.5/SDXL → FP16 + xFormers + Tiled VAE + --cpu-text-encoder --cpu-vae
├── Flux → GGUF Q4_K + Tiled VAE + --lowvram
└── 视频 → 几乎不可能本地，用 API

4GB (3050/1650):
└── GGUF Q2_K + --lowvram + Tiled VAE (非常慢但可能跑通 SD1.5)

Blackwell (RTX 50xx):
└── NVFP4 + SageAttention + cu130 PyTorch → 3x 加速
```

---

## 9. 生产环境最佳实践

### 9.1 速度优化清单

1. ✅ 启用 xFormers 或 SageAttention
2. ✅ 使用 FP16（或有硬件支持时 FP8）
3. ✅ 确保 Async Offloading + Pinned Memory 启用（ComfyUI 0.5.0+ 默认）
4. ✅ 高分辨率时用 Tiled VAE
5. ✅ 固定分辨率场景考虑 TensorRT Static Engine
6. ✅ 尝试 torch.compile（尤其 Flux/SD3 DiT 模型）
7. ✅ 选择合适的 Sampler + Scheduler（见 Day 4 笔记）

### 9.2 VRAM 节省清单

1. ✅ 卸载文本编码器（`--cpu-text-encoder`，省 1-2GB）
2. ✅ Tiled VAE（省 30-50% VAE 内存）
3. ✅ 量化模型（FP8 省 50%，GGUF Q4 省 75%）
4. ✅ 量化 T5 编码器（city96/t5-v1_1-xxl-encoder-gguf）
5. ✅ 合理设置 `--reserve-vram` 避免系统争抢
6. ✅ 定期重启清碎片（尤其切换大模型后）

### 9.3 常见问题诊断

| 症状 | 可能原因 | 解决方案 |
|------|---------|---------|
| CUDA OOM @ 采样 | 注意力矩阵过大 | xFormers/降分辨率/Tiled |
| CUDA OOM @ VAE 解码 | VAE 未分块 | 用 VAEDecodeTiled |
| NaN / 黑图 | FP16 溢出 | 换 BF16 / `--force-fp32` VAE |
| 速度异常慢 | lowvram 模式/碎片化 | 检查启动参数/重启 |
| TensorRT engine 失败 | VRAM 不足 | 关闭其他 GPU 程序 / Static 替代 Dynamic |
| GGUF 加载失败 | ComfyUI 版本过旧 | 更新到支持 custom ops 的版本 |
| NVFP4 反而更慢 | PyTorch 不是 cu130 | 安装 cu130 版 PyTorch |

---

## 10. 自定义节点生态（性能相关）

### 10.1 核心节点包

| 节点包 | 功能 | 地址 |
|--------|------|------|
| **ComfyUI_TensorRT** | TensorRT 加速 | comfyanonymous/ComfyUI_TensorRT |
| **ComfyUI-GGUF** | GGUF 量化模型加载 | city96/ComfyUI-GGUF |
| **ComfyUI-nunchaku** | NVFP4/SVDQuant 4-bit | nunchaku-ai/ComfyUI-nunchaku |
| **ComfyUI-Upscaler-Tensorrt** | TRT 加速超分 2-4x | yuvraj108c/ComfyUI-Upscaler-Tensorrt |
| **ComfyUI-DistorchMemoryManager** | 独立 VRAM 管理 | ussoewwin/ComfyUI-DistorchMemoryManager |
| **ComfyUI-KJNodes (VRAM Debug)** | VRAM 监控调试 | 社区节点 |
| **ComfyUI_LTX-2_VRAM_Memory** | LTX-2 内存优化（10x） | RandomInternetPreson/... |

### 10.2 LTX-2 VRAM Memory Management

特别值得注意的优化：
- 将推理峰值 VRAM 降低约 **10x**
- 使 LTX-2 能生成 800+ 帧视频
- 原理：分步计算 + 中间结果卸载

---

## 11. 实验记录

### 实验 #29: 性能优化概念信息图

- **模型**: rhart-image-n-pro (全能图片PRO)
- **类型**: text-to-image
- **Prompt**: GPU memory optimization hierarchy infographic showing precision pyramid (FP32→FP16→FP8→GGUF→NF4/NVFP4)
- **时间**: 30 秒
- **成本**: ¥0.03
- **输出**: `/tmp/rh-output/performance-optimization-concept.jpg`
- **结果**: ✅ 生成了性能优化概念图

---

## 12. 技术总结

### 12.1 优化技术演进时间线

```
2022: xFormers 成为标配
2023: TensorRT ComfyUI 集成 / Flash Attention 普及
2024: GGUF 从 LLM 引入 SD 生态 / FP8 原生支持 (RTX 40xx)
2025: SageAttention / Async Offloading / Pinned Memory 默认启用
      Nunchaku SVDQuant NVFP4 (ICLR 2025 Spotlight)
      torch.compile 在 ComfyUI 中实用化
      Dynamic VRAM 默认启用
2026: NVFP4 ComfyUI 原生支持 (需 cu130)
      Multi-GPU / DisTorch 支持初步
```

### 12.2 核心认知

1. **量化对 DiT 比 U-Net 友好**：Flux/SD3 等 Transformer 架构的线性层为主，量化损失小；SD1.5/SDXL 的 conv2d 对量化敏感
2. **注意力优化是性价比最高的**：几乎零质量损失，显著速度+内存提升
3. **TensorRT 强但限制多**：不支持 LoRA/ControlNet 是致命伤，适合固定管线
4. **GGUF 是低端 GPU 的救星**：Q4_K 可以在 4GB VRAM 跑 Flux
5. **Async Offloading 是免费午餐**：对需要卸载的场景，10-50% 加速
6. **NVFP4 是下一代方向**：4-bit 接近 FP16 质量，3x 加速，但需要 Blackwell GPU

---

## 13. Day 9 源码分析待做项（跳过）

PROGRESS.md 中 Day 9 的 `train_network.py 源码逐行分析` 和 `实际训练演练（需 GPU 环境）` 属于 LoRA 训练专题，不在当前性能优化范围内，标记为需 GPU 环境后续处理。
