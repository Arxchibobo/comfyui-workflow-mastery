# Day 6: ControlNet 全系列 — 基础原理 + 三大经典模型

> 学习时间: 2026-03-20 18:03 UTC (Session 12)
> 论文: Adding Conditional Control to Text-to-Image Diffusion Models (Zhang et al., 2023, arXiv:2302.05543)

---

## §1 ControlNet 架构原理

### 1.1 核心问题

Text2Img 只靠文字 prompt 控制生成，精确度有限：
- 无法精确控制人物姿势
- 无法保持建筑结构
- 无法指定边缘/轮廓
- 文字描述空间构图很困难

**ControlNet 的解决方案**: 额外提供一张「条件图像」（边缘图/深度图/姿势图等），作为空间层面的引导信号，在不改变原始扩散模型的前提下注入条件控制。

### 1.2 架构设计

ControlNet 的核心思想可以用一个公式概括：

```
y_c = F(x; Θ) + Z(F(x + Z(c; Θ_z1); Θ_c); Θ_z2)
```

其中：
- `F(x; Θ)` = 原始锁定的扩散模型（frozen copy）
- `F(·; Θ_c)` = 可训练的 ControlNet 分支（trainable copy）
- `Z(·; Θ_z)` = 零卷积层（zero convolution）
- `c` = 条件图像（如 Canny 边缘图）
- `x` = 带噪声的 latent + text prompt

**双副本架构**:
```
原始 SD U-Net（锁定，不训练）
  │
  ├── Encoder blocks ←── ControlNet 分支的输出通过零卷积注入
  ├── Middle block   ←── ControlNet 分支的输出通过零卷积注入
  └── Decoder blocks
  
ControlNet 分支（可训练副本）
  │
  ├── 条件图像 c → 4层卷积编码 → hint_channels → 与 noisy latent 拼接
  ├── 复制自 SD U-Net 的 Encoder blocks
  └── 复制自 SD U-Net 的 Middle block
  （注：ControlNet 只复制了 Encoder + Middle，没有 Decoder）
```

### 1.3 零卷积（Zero Convolution）详解

**定义**: 1×1 卷积层，权重和偏置都初始化为零。

```python
# 伪代码
class ZeroConv(nn.Conv2d):
    def __init__(self, in_channels, out_channels):
        super().__init__(in_channels, out_channels, kernel_size=1)
        nn.init.zeros_(self.weight)
        nn.init.zeros_(self.bias)
```

**关键性质**:
1. **训练开始时输出全零** → ControlNet 分支对原模型零影响
2. **渐进式学习** → 参数从零开始逐渐增长，稳定训练
3. **保护预训练模型** → 即使训练数据很少（<50k），也不会破坏原模型质量
4. **快速收敛** → 因为 backbone 已经具备强大的特征提取能力

**数学直觉**:
```
训练第 0 步: Z(·) = 0 → y_c = F(x; Θ) + 0 = y（跟没有 ControlNet 一样）
训练第 N 步: Z(·) 学到了有意义的映射 → y_c = F(x; Θ) + Δ（精确控制）
```

### 1.4 条件图像编码

条件图像通过 4 层卷积（`input_hint_block`）从像素空间映射到 latent 空间：

```python
# ComfyUI 源码 comfy/cldm/cldm.py 中的 hint 编码
# 输入: hint_channels (通常 3，RGB) 
# 输出: model_channels (与 U-Net 第一层通道数匹配)
self.input_hint_block = nn.Sequential(
    nn.Conv2d(hint_channels, 16, 3, padding=1),
    nn.SiLU(),
    nn.Conv2d(16, 16, 3, padding=1),
    nn.SiLU(),
    nn.Conv2d(16, 32, 3, padding=1, stride=2),  # 下采样 2x
    nn.SiLU(),
    nn.Conv2d(32, 32, 3, padding=1),
    nn.SiLU(),
    nn.Conv2d(32, 96, 3, padding=1, stride=2),  # 下采样 4x
    nn.SiLU(),
    nn.Conv2d(96, 96, 3, padding=1),
    nn.SiLU(),
    nn.Conv2d(96, 256, 3, padding=1, stride=2),  # 下采样 8x → 匹配 latent
    nn.SiLU(),
    zero_module(nn.Conv2d(256, model_channels, 3, padding=1)),  # 最后一层也是零初始化
)
```

总共 8x 下采样，将 512×512 的条件图像压缩到 64×64，与 latent space 对齐。

### 1.5 权重注入方式

ControlNet 分支的输出通过零卷积「加法注入」到原始 U-Net 的对应层：

```
原始 U-Net Encoder Layer i 的输出: h_i
ControlNet Layer i 的输出: c_i
零卷积后: z_i = ZeroConv(c_i)

最终注入: h_i' = h_i + z_i × strength
```

在 ComfyUI 中，这些输出被收集为 `{'input': [...], 'middle': [...], 'output': [...]}` 三个列表：
- `input`: encoder 各层的残差
- `middle`: middle block 的残差
- `output`: 对于 SD，ControlNet 不直接输出 decoder 残差

---

## §2 ComfyUI 源码分析

### 2.1 核心类层次

```
ControlBase (基类)
  ├── ControlNet (标准 ControlNet)
  │     └── QwenFunControlNet (Qwen/Fun 系列特化)
  ├── ControlLora (ControlNet 的 LoRA 版本)
  └── T2IAdapter (T2I-Adapter，轻量方案)
```

### 2.2 ControlBase 关键属性

```python
class ControlBase:
    def __init__(self):
        self.cond_hint_original = None     # 原始条件图像
        self.cond_hint = None              # 处理后的条件图像（缓存）
        self.strength = 1.0                # 控制强度 [0, 10]
        self.timestep_percent_range = (0.0, 1.0)  # 生效的时间步范围
        self.compression_ratio = 8          # 空间压缩比（SD=8, Flux可能不同）
        self.previous_controlnet = None     # 链式多 ControlNet
        self.strength_type = StrengthType.CONSTANT  # 恒定 or 线性递增
```

### 2.3 `get_control()` 执行流程

```python
def get_control(self, x_noisy, t, cond, batched_number, transformer_options):
    # 1. 递归调用前一个 ControlNet（链式）
    control_prev = self.previous_controlnet.get_control(...) if self.previous_controlnet else None
    
    # 2. 检查时间步范围
    if t[0] > self.timestep_range[0] or t[0] < self.timestep_range[1]:
        return control_prev  # 不在生效范围内，跳过
    
    # 3. 条件图像预处理：resize 到匹配 latent 尺寸
    self.cond_hint = common_upscale(self.cond_hint_original, 
                                     x_noisy.shape[-1] * compression_ratio,
                                     x_noisy.shape[-2] * compression_ratio)
    
    # 4. 如果需要 VAE（如 Flux ControlNet），先编码到 latent
    if self.vae is not None:
        self.cond_hint = self.vae.encode(self.cond_hint)
    
    # 5. 广播批次维度
    self.cond_hint = broadcast_image_to(self.cond_hint, x_noisy.shape[0], batched_number)
    
    # 6. 前向推理
    control = self.control_model(x=x_noisy, hint=self.cond_hint, timesteps=timestep, context=context)
    
    # 7. 合并控制信号
    return self.control_merge(control, control_prev, output_dtype=None)
```

### 2.4 `control_merge()` 多 ControlNet 合并

```python
def control_merge(self, control, control_prev, output_dtype):
    out = {'input':[], 'middle':[], 'output': []}
    
    for key in control:
        for i, x in enumerate(control[key]):
            if x is not None:
                # 应用 strength
                if self.strength_type == StrengthType.CONSTANT:
                    x *= self.strength
                elif self.strength_type == StrengthType.LINEAR_UP:
                    x *= (self.strength ** (len(control_output) - i))
    
    # 与前一个 ControlNet 的输出相加
    if control_prev is not None:
        for key in ['input', 'middle', 'output']:
            for i in range(len(control_prev[key])):
                out[key][i] = control_prev[key][i] + out[key][i]  # 直接相加！
    
    return out
```

**关键发现**: 多个 ControlNet 的控制信号是**直接相加**的，不是加权平均。所以多 ControlNet 组合时，每个的 strength 都要适当降低（通常 0.5-0.7），否则会过强。

### 2.5 ControlNetApplyAdvanced 节点分析

```python
class ControlNetApplyAdvanced:
    # 输入: positive + negative conditioning, control_net, image, strength, start/end_percent, vae(可选)
    
    def apply_controlnet(self, positive, negative, control_net, image, strength, start_percent, end_percent, vae=None):
        control_hint = image.movedim(-1, 1)  # BHWC → BCHW
        
        # 对 positive 和 negative 都应用同一个 ControlNet
        for conditioning in [positive, negative]:
            for t in conditioning:
                c_net = control_net.copy().set_cond_hint(control_hint, strength, (start_percent, end_percent), vae=vae)
                c_net.set_previous_controlnet(prev_cnet)  # 链式连接
                d['control'] = c_net
                d['control_apply_to_uncond'] = False  # 高级版分别处理 pos/neg
```

**与旧版 ControlNetApply 的区别**:
- 旧版: `control_apply_to_uncond = True` → ControlNet 同时应用于条件和无条件预测
- 新版: `control_apply_to_uncond = False` → 分别设置，更灵活
- 新版支持 `start_percent/end_percent` 控制 ControlNet 生效的去噪阶段
- 新版支持 `vae` 输入（某些 ControlNet 如 Flux 需要先 VAE 编码）

---

## §3 ControlNet v1.1 全模型列表

### 3.1 命名规则 (SCNNR - Standard ControlNet Naming Rules)

```
control_v11[质量标记]_sd15[_变体]_[类型]
```

质量标记:
- `p` = production-ready（生产可用）
- `e` = experimental（实验性）
- `f1` = fix 1（修复版）

### 3.2 14 个模型完整列表

| 模型文件 | 类型 | 状态 | 最佳使用场景 |
|---------|------|------|------------|
| control_v11p_sd15_canny | Canny 边缘 | ✅ Production | 保持物体轮廓和结构 |
| control_v11p_sd15_mlsd | M-LSD 直线 | ✅ Production | 建筑/室内设计/直线结构 |
| control_v11f1p_sd15_depth | Depth 深度 | ✅ Production | 保持空间关系/3D 结构 |
| control_v11p_sd15_normalbae | Normal 法线 | ✅ Production | 保持表面朝向/光照 |
| control_v11p_sd15_seg | Segmentation 分割 | ✅ Production | 语义区域控制 |
| control_v11p_sd15_inpaint | Inpainting | ✅ Production | 区域重绘 |
| control_v11p_sd15_lineart | Lineart 线稿 | ✅ Production | 线稿上色/保持线条 |
| control_v11p_sd15s2_lineart_anime | Lineart Anime | ✅ Production | 动漫线稿专用 |
| control_v11p_sd15_openpose | OpenPose 姿势 | ✅ Production | 人物姿势控制 |
| control_v11p_sd15_scribble | Scribble 涂鸦 | ✅ Production | 草图转精图 |
| control_v11p_sd15_softedge | SoftEdge 柔边 | ✅ Production | 比 Canny 更柔和的结构 |
| control_v11e_sd15_shuffle | Shuffle 打乱 | 🧪 Experimental | 风格迁移 |
| control_v11e_sd15_ip2p | InstructP2P | 🧪 Experimental | 指令编辑 |
| control_v11f1e_sd15_tile | Tile 分块 | 🧪 Experimental | 超分辨率/细节增强 |

---

## §4 三大经典 ControlNet 深度解析

### 4.1 Canny 边缘检测

**原理**: Canny 算法提取图像的边缘信息，生成二值（黑白）边缘图。

**Canny 算法步骤**:
1. 高斯模糊去噪
2. 计算梯度强度和方向（Sobel 算子）
3. 非极大值抑制（边缘细化）
4. 双阈值检测 + 滞后边缘跟踪

**ComfyUI 中的使用**:
- 预处理器: `CannyEdgePreprocessor`（来自 comfyui_controlnet_aux）
- 关键参数:
  - `low_threshold`: 低阈值，控制弱边缘敏感度（推荐 100-150）
  - `high_threshold`: 高阈值，控制强边缘敏感度（推荐 200-250）
  - 阈值越低 → 边缘越多越密 → 控制越严格
  - 阈值越高 → 只保留强边缘 → 给模型更多自由度

**最佳场景**:
- ✅ 保持物体精确轮廓
- ✅ 建筑/机械等硬边缘物体
- ✅ 需要精确结构控制时
- ❌ 不适合柔和/有机物体（头发、云等，用 SoftEdge 更好）

**Strength 调优**:
- 0.3-0.5: 轻微引导，保留创意空间
- 0.6-0.8: 中等控制（推荐起步）
- 0.9-1.0: 严格遵循边缘
- >1.0: 过强，可能产生伪影

### 4.2 Depth 深度估计

**原理**: 使用深度估计模型（MiDaS/Leres/Zoe）预测图像每个像素的深度（距相机距离），生成灰度深度图。

**深度估计方法对比**:

| 方法 | 特点 | 推荐场景 |
|------|------|---------|
| MiDaS (Depth) | 通用、快速、稳定 | 默认首选 |
| Leres | 更精确的远距离深度 | 风景/大场景 |
| Zoe | 相对+绝对深度混合 | 室内/精确深度 |
| Depth Anything | 最新、最准 | 2024+ 首选 |

**v1.1 改进**:
- 训练数据增强：使用 MiDaS + Leres + Zoe 三种方法 × 256/384/512 三种分辨率
- 模型不偏向某种特定深度方法
- 可以直接使用 3D 渲染引擎的真实深度图

**最佳场景**:
- ✅ 保持空间构图（前景/背景关系）
- ✅ 场景重新风格化（同构图换风格）
- ✅ 3D 渲染 → 2D 转化
- ✅ 人物+背景的层次关系
- ❌ 不控制细节纹理（只控制空间关系）

**与 Canny 的关键区别**:
- Canny: 控制「边缘在哪里」→ 精确轮廓
- Depth: 控制「东西在多远」→ 空间布局
- Depth 给模型更多创意自由度（不限制具体形状）

### 4.3 OpenPose 人体姿势

**原理**: OpenPose 检测人体关键点（头、肩、肘、腕、髋、膝、踝等），生成骨骼/关键点图。

**检测层次**:
```
OpenPose 检测器层次:
├── Body (身体主骨架, 18 个关键点)
├── Face (面部 70 个关键点)
├── Hand (每只手 21 个关键点)
└── Full (Body + Face + Hand)
```

**ComfyUI 预处理器变体**:
- `OpenPosePreprocessor`: 标准身体检测
- `DWPosePreprocessor`: DWPose（更准确，推荐）
- 可选开关: `detect_hand`, `detect_body`, `detect_face`

**最佳场景**:
- ✅ 精确控制人物姿势
- ✅ 多人场景的姿势控制
- ✅ 手动绘制骨骼图来创建任意姿势
- ❌ 不控制衣服/外观细节（只控制姿势）
- ❌ 正面平面图像效果最好，复杂透视效果较差

**Strength 调优**:
- 0.5-0.7: 允许自然变化（推荐起步）
- 0.8-1.0: 严格跟随姿势
- 身体 > 手 > 面部（按重要性排序控制）

---

## §5 ControlNet 跨模型/架构对比

### 5.1 SD 1.5 vs SDXL vs Flux

| 维度 | SD 1.5 | SDXL | Flux |
|------|--------|------|------|
| ControlNet 成熟度 | ⭐⭐⭐⭐⭐ 最成熟 | ⭐⭐⭐ 逐渐完善 | ⭐⭐ 早期 |
| 模型数量 | 14+ 官方 | 社区贡献 (xinsir等) | 少数 |
| 架构 | U-Net ControlNet | U-Net ControlNet | DiT ControlNet |
| 典型大小 | ~1.4GB | ~2.5GB | ~3.5GB |
| 需要 VAE? | 不需要 | 不需要 | 某些需要 |
| Union Model | ✅ promax | ✅ promax | ✅ InstantX Union |

### 5.2 Union ControlNet

**概念**: 一个模型支持多种条件类型（canny、depth、pose 等），通过 control_type 参数切换。

ComfyUI 中通过 `SetUnionControlNetType` 节点设置:
```python
# 源码 comfy_extras/nodes_controlnet.py
UNION_CONTROLNET_TYPES = {
    "canny": 0, "tile": 1, "depth": 2, "blur": 3,
    "pose": 4, "gray": 5, "lq": 6, ...
}

# 设置为 "auto" 时，模型自动推断条件类型
control_net.set_extra_arg("control_type", [type_number])
```

### 5.3 SDXL 推荐 ControlNet 模型

2024 年 xinsir 发布的 SDXL ControlNet 被社区认为质量最高:
- `xinsir/controlnet-canny-sdxl-1.0`
- `xinsir/controlnet-openpose-sdxl-1.0`
- `xinsir/controlnet-scribble-sdxl-1.0`
- `xinsir/controlnet-union-sdxl-1.0` (Union 版，一个模型多种条件)

### 5.4 Flux ControlNet 现状

- InstantX Union Pro: depth 效果好，canny 尚可，openpose 较弱
- Flux 官方 ControlNet: 有 canny 和 depth 的 checkpoint 版本（非 LoRA），效果优于 LoRA 版
- 工作流技巧: Flux ControlNet checkpoint + 标准 Flux FP8 模型混合使用，控制比例

---

## §6 实践经验总结

### 6.1 参数快速决策树

```
需要什么级别的控制？
├── 精确轮廓/结构 → Canny (strength 0.7-1.0)
├── 空间布局/构图 → Depth (strength 0.6-0.9)
├── 人物姿势 → OpenPose (strength 0.5-0.8)
├── 柔和结构引导 → SoftEdge (strength 0.6-0.8)
├── 线稿上色 → Lineart (strength 0.8-1.0)
├── 建筑/室内直线 → MLSD (strength 0.7-0.9)
├── 超分/细节 → Tile (strength 0.5-0.7)
└── 风格迁移 → Shuffle/IP-Adapter
```

### 6.2 start_percent / end_percent 策略

```
start_percent=0.0, end_percent=1.0  → 全程控制（默认）
start_percent=0.0, end_percent=0.5  → 只在前半程控制（结构确定后放开创意）
start_percent=0.3, end_percent=1.0  → 前 30% 自由发挥，后面跟随控制
start_percent=0.0, end_percent=0.3  → 只确定大构图，细节完全自由
```

**经验法则**:
- 结构类（Canny/Depth）: end_percent=0.8 通常就够了
- 姿势类（OpenPose）: end_percent=0.5 即可（早期确定姿势，后期自由细化）
- 细节类（Tile）: start_percent=0.3 开始即可

### 6.3 多 ControlNet 组合技巧

- 信号是**相加**的，所以每个 strength 要降低
- 典型组合: Depth(0.5) + OpenPose(0.5) = 同时控制空间和姿势
- 避免冲突: 不要同时用 Canny + SoftEdge（信息重叠）
- 推荐组合:
  - Depth + OpenPose: 人物场景（空间 + 姿势）
  - Depth + Canny: 建筑场景（空间 + 边缘）
  - OpenPose + Lineart: 角色创作（姿势 + 轮廓）

### 6.4 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 生成图像变形/失真 | strength 过高 | 降低到 0.5-0.7 |
| 控制效果不明显 | strength 过低或图像分辨率不匹配 | 提高 strength，确保条件图像尺寸正确 |
| 边缘/接缝可见 | 条件图像质量差 | 提高预处理器分辨率，检查阈值 |
| 颜色异常 | 条件图像泄漏灰度信息 | 用 _safe 变体（如 SoftEdge_HED_safe） |
| 多 ControlNet 打架 | 信号冲突 | 降低各自 strength，用 start/end_percent 分时段 |

---

## §7 参考资料

1. Zhang, L. et al. "Adding Conditional Control to Text-to-Image Diffusion Models" (arXiv:2302.05543)
2. ComfyUI 源码: `comfy/controlnet.py` — ControlBase/ControlNet/ControlLora 类
3. ComfyUI 源码: `nodes.py` — ControlNetApply/ControlNetApplyAdvanced 节点
4. ComfyUI 源码: `comfy_extras/nodes_controlnet.py` — Union ControlNet/Inpainting 节点
5. ControlNet v1.1 官方仓库: github.com/lllyasviel/ControlNet-v1-1-nightly
6. HuggingFace 模型: huggingface.co/lllyasviel/ControlNet-v1-1
