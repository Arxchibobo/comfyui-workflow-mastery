# Day 28: SD 微调技术全景 + ComfyUI 工作流工程化

> 学习时间: 2026-03-23 02:05 UTC | 轮次: 36
> 主题: Textual Inversion / DreamBooth / Hypernetwork 完整对比 + Subgraph / Registry / App Mode 工程化

---

## 第一部分: SD 微调技术全景 (Fine-tuning Ecosystem)

### 1. 微调方法总览

SD 生态中有 **5 种** 主要微调方法，按修改范围从小到大排列:

```
修改范围: 小 ←——————————————————————————————————→ 大
          Textual Inversion  Hypernetwork  LoRA  DreamBooth  Full Fine-tune
          (~数KB)            (~数MB)       (~数十MB)  (~数GB)    (~数GB)
          仅改 Embedding     仅改 CrossAttn 改部分权重  改全部权重  改全部权重
```

### 2. Textual Inversion (文本反转) — 深度解析

#### 2.1 论文背景
- **论文**: "An Image is Worth One Word: Personalizing Text-to-Image Generation using Textual Inversion" (Gal et al., 2022, arXiv:2208.01618)
- **核心思想**: 不修改模型任何权重，只在 CLIP 的 token embedding 空间中找到一个新的向量来表示目标概念

#### 2.2 数学原理

**训练目标**: 找到最优 embedding 向量 v*

```
v* = argmin_v  E_{z~E(x), y, ε~N(0,1), t} [ ||ε - ε_θ(z_t, t, c_θ(y_v))||² ]
```

其中:
- `v` 是要学习的 embedding 向量（768d for SD1.5, 1024d for SDXL CLIP-L）
- `c_θ(y_v)` 是包含占位符 token 的文本经过 CLIP Text Encoder 的编码
- `ε_θ` 是 U-Net 噪声预测器（**冻结不训练**）
- `z_t` 是在 timestep t 的带噪潜空间
- 本质上与标准 SD 训练相同的 loss，但**只优化一个 embedding 向量**

**关键约束**: 梯度只回传到新增的 token embedding，**冻结所有其他 token embedding + 整个 U-Net + VAE**

```python
# 训练核心伪代码
for step in range(num_steps):
    # 1. 获取训练图片，编码到 latent
    latents = vae.encode(images)
    
    # 2. 添加噪声
    noise = torch.randn_like(latents)
    timesteps = torch.randint(0, scheduler.num_train_timesteps, (batch_size,))
    noisy_latents = scheduler.add_noise(latents, noise, timesteps)
    
    # 3. 获取文本 embedding（包含可学习的新 token）
    # prompt: "a photo of <sks>"  其中 <sks> 对应可学习的 v
    encoder_hidden_states = text_encoder(tokenizer(prompt))
    
    # 4. U-Net 预测噪声
    noise_pred = unet(noisy_latents, timesteps, encoder_hidden_states)
    
    # 5. 计算 loss
    loss = F.mse_loss(noise_pred, noise)
    loss.backward()
    
    # 6. 关键：只更新新 token 的 embedding，零出其他梯度
    grads = text_encoder.get_input_embeddings().weight.grad
    # 创建 mask，只保留新 token 的梯度
    mask = torch.zeros_like(grads)
    mask[placeholder_token_id] = 1.0
    grads.data *= mask
    
    optimizer.step()
```

#### 2.3 多 Token Embedding

- 一个概念可以用 **多个 token** 表示（1-16 个）
- 更多 token = 更多容量 = 能编码更复杂概念
- 但也**占用更多 prompt 空间**（SD1.5 限制 77 tokens）
- 推荐: 简单风格 1-2 tokens, 复杂角色/物体 3-8 tokens

```
单 token: v ∈ R^768          → "embedding:mystyle"  占 1 token
多 token: V ∈ R^{n×768}      → "embedding:mychar"   占 n tokens
```

#### 2.4 训练参数推荐

| 参数 | SD1.5 推荐 | SDXL 推荐 | 说明 |
|------|-----------|-----------|------|
| 学习率 | 5e-4 ~ 5e-3 | 1e-4 ~ 1e-3 | TI 用较高 LR |
| 步数 | 2000-6000 | 3000-10000 | 取决于复杂度 |
| 图片数 | 3-10 | 5-20 | TI 需要的图少 |
| Token 数 | 1-8 | 1-4 | 复杂概念用更多 |
| Batch Size | 1-2 | 1 | 小 batch 即可 |
| 模板 | "a photo of {}" | "a photo of {}" | 随机模板增多样性 |

#### 2.5 ComfyUI 中使用 Embedding

**放置路径**: `ComfyUI/models/embeddings/`

**Prompt 语法**: 在 CLIPTextEncode 节点中使用
```
# 方式一：完整文件名
embedding:badhand_v4.pt

# 方式二：省略扩展名
embedding:badhand_v4

# 在 prompt 中
"a beautiful landscape, masterpiece, embedding:easynegative"
(negative prompt 中常用 embedding 来统一负面提示)
```

**ComfyUI 加载机制**（源码分析）:
```python
# comfy/sd1_clip.py - tokenize_with_weights()
# 1. 解析 prompt 文本
# 2. 遇到 "embedding:xxx" 时
# 3. 从 embeddings 目录加载对应 .pt/.safetensors 文件
# 4. 获取存储的 embedding 向量
# 5. 替换占位符 token 的 embedding
# 6. 如果是多 token embedding，扩展 token 序列
```

**文件格式**:
```python
# .pt 格式（旧式，PyTorch pickle）
data = {
    "string_to_token": {"*": 265},
    "string_to_param": {"*": tensor([...])},  # shape: [n_tokens, embed_dim]
    "name": "concept_name",
    "step": 5000,
    "sd_checkpoint_name": "...",
}

# .safetensors 格式（新式，推荐）
# 直接存储 tensor，key 通常为 "emb_params"
```

#### 2.6 经典 Embedding 案例

**Negative Embeddings**（最广泛使用的 TI 应用）:
- **EasyNegative**: 编码了常见生成缺陷（6 fingers, bad anatomy...）
- **badhandv4**: 专门修复手部问题
- **FastNegativeV2**: 2023 优化版
- **verybadimagenegative_v1.3**: 更强的通用负面
- 原理: 将大量负面概念编码到一个 embedding 中，用一个 token 替代长串 negative prompt

**Style Embeddings**:
- 编码特定画风（水彩、赛博朋克、浮世绘等）
- 比 LoRA 更轻量但效果弱

### 3. DreamBooth — 深度解析

#### 3.1 论文背景
- **论文**: "DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation" (Ruiz et al., Google, 2022, arXiv:2208.12242)
- **核心思想**: 微调**整个模型**（U-Net + 可选 Text Encoder）来绑定稀有 token 与特定主体

#### 3.2 训练方法

**Step 1: 实例微调**
```
训练数据: 3-5 张目标主体图片
Prompt: "a photo of [V] dog"
       ↑ 稀有 token identifier（如 sks, ohwx）
Loss: 标准扩散去噪 loss，但更新整个 U-Net
```

**Step 2: Prior Preservation Loss（先验保持损失）**
```
L_total = L_instance + λ × L_prior

L_instance = E[||ε - ε_θ(z_t, t, c("a photo of [V] dog"))||²]
L_prior    = E[||ε - ε_θ(z_t, t, c("a photo of a dog"))||²]
                                    ↑ 用类别 prompt 生成正则化样本
```

**Prior Preservation 的作用**:
- 防止"语言漂移"（model 忘记 "dog" 的一般概念）
- 防止过拟合（只能生成训练图那几个姿势）
- 保持模型的多样性和泛化能力
- 实现方式: 用原始模型先生成 200-400 张 "a photo of a dog" 图片作为正则化数据

#### 3.3 DreamBooth + LoRA

现代实践中，DreamBooth 几乎总是与 LoRA 结合使用（避免生成完整模型副本）:

```python
# kohya_ss / sd-scripts 配置
# DreamBooth with LoRA = 最佳实践
training_method: "dreambooth"
network_module: "networks.lora"  # 用 LoRA 而非 full fine-tune
network_dim: 32
network_alpha: 16
prior_loss_weight: 1.0
class_data_dir: "./reg_images/"  # 正则化图片目录

# 输出: LoRA 权重文件（~50MB）而非完整模型副本（~4GB）
```

#### 3.4 DreamBooth vs Full Fine-tune

| 特性 | DreamBooth | Full Fine-tune |
|------|-----------|---------------|
| 关键创新 | Prior Preservation Loss + 稀有 Token | 标准训练 |
| 防遗忘 | ✅ Prior Loss 显式防止 | ❌ 无保护 |
| 数据需求 | 3-5 张 | 数百张+ |
| 典型场景 | 特定人物/物体/宠物 | 整体风格迁移 |
| 用途 | 个性化 | 风格化 |

### 4. Hypernetwork — 原理与现状

#### 4.1 架构
- **位置**: 注入到 U-Net 的 **交叉注意力层**（Cross-Attention）
- **机制**: 一个小型 MLP 网络修改 Cross-Attention 的 K（Key）和 V（Value）投影

```python
# 正常 Cross-Attention
Q = W_q @ latent_features
K = W_k @ text_embedding
V = W_v @ text_embedding
Attention = softmax(Q @ K^T / √d) @ V

# 有 Hypernetwork 时
K' = HN_k(K)   # 小 MLP 变换 Key
V' = HN_v(V)   # 小 MLP 变换 Value
Attention = softmax(Q @ K'^T / √d) @ V'
```

**HN 结构**:
```
Input(768d) → Linear → Dropout → GELU → Linear → Output(768d)
每个注意力层有独立的 K-HN 和 V-HN，共约 10-50 个层
```

#### 4.2 现状: 已基本弃用
- **原因**: LoRA 在所有维度上全面超越 Hypernetwork
  - LoRA 效果更好（修改更多层）
  - LoRA 更稳定（低秩约束）
  - LoRA 更灵活（可堆叠、可调权重）
  - LoRA 生态更好（模型更多、工具更全）
- **ComfyUI**: 有基础支持但社区几乎不用
- **A1111**: 仍保留但标记为 legacy
- **结论**: 2024 年后的新项目不应使用 Hypernetwork

### 5. 五种微调方法全维度对比

```
┌─────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│                 │  Textual     │  Hyper-      │  LoRA        │  DreamBooth  │  DreamBooth  │
│                 │  Inversion   │  network     │              │  (Full)      │  + LoRA      │
├─────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 修改范围        │ 仅 Embedding │ 仅 CrossAttn │ Attn 层低秩  │ 全 U-Net     │ LoRA 子空间  │
│ 输出文件大小    │ 数 KB        │ 数 MB        │ 10-200 MB    │ 2-6 GB       │ 10-200 MB    │
│ 训练数据量      │ 3-10 张      │ 20-100 张    │ 10-100 张    │ 3-5 张       │ 3-10 张      │
│ VRAM 需求       │ 6-8 GB       │ 8-12 GB      │ 8-16 GB      │ 16-24 GB     │ 12-16 GB     │
│ 训练速度        │ 快(分钟级)   │ 中(小时级)   │ 中(0.5-2h)   │ 慢(1-3h)     │ 中(0.5-2h)   │
│ 概念学习能力    │ 弱           │ 中           │ 强           │ 最强         │ 强           │
│ 风格学习能力    │ 弱-中        │ 中           │ 强           │ 强           │ 强           │
│ 泛化能力        │ 高           │ 中           │ 高           │ 中(需调参)   │ 高           │
│ 过拟合风险      │ 低           │ 高           │ 中           │ 高           │ 中           │
│ 可组合性        │ ✅ 天然      │ ⚠️ 有限     │ ✅ 可堆叠    │ ❌ 独占模型  │ ✅ 可堆叠    │
│ 模型兼容性      │ ✅ 跨模型    │ ⚠️ 绑模型   │ ⚠️ 近架构   │ ❌ 绑定模型  │ ⚠️ 近架构   │
│ 现代适用性      │ ⭐⭐⭐      │ ⭐           │ ⭐⭐⭐⭐⭐  │ ⭐⭐⭐      │ ⭐⭐⭐⭐⭐  │
│ ComfyUI 支持    │ ✅ 原生      │ ⚠️ 插件     │ ✅ 原生      │ 训练后LoRA用 │ ✅ 原生      │
└─────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### 6. 方法选择决策树

```
需要个性化 SD 模型?
├── 需要学习什么？
│   ├── 简单风格/概念 → Textual Inversion（最轻量、可跨模型）
│   ├── 复杂风格/角色 → LoRA（最佳平衡）
│   ├── 特定人物（3-5张照片）→ DreamBooth + LoRA
│   └── 负面概念打包 → Textual Inversion（Negative Embedding）
├── GPU 限制？
│   ├── ≤8GB → Textual Inversion
│   ├── 8-12GB → LoRA (4-bit QLoRA)
│   └── ≥16GB → DreamBooth + LoRA
├── 需要可组合？
│   ├── 是 → LoRA 或 Textual Inversion
│   └── 否 → DreamBooth (full) 也可
└── 2025+ 推荐
    └── 95% 场景用 LoRA（或 DreamBooth+LoRA）
    └── 5% 场景用 Textual Inversion（负面 embedding / 极轻量需求）
```

---

## 第二部分: ComfyUI 工作流工程化 (Workflow Engineering)

### 7. ComfyUI 模块化演进

```
时间线:
2023.Q3  Groups (视觉分组，纯 UI)
2024.Q1  Group Nodes (Legacy, 将一组节点打包为复合节点)
2025.Q3  Subgraph (现代方案，真正的嵌套图)
2026.Q1  App Mode + App Builder + ComfyHub
```

### 8. Subgraph 系统（现代标准）

#### 8.1 概念
- Subgraph = 工作流中的"文件夹"
- 将一组相关节点封装为单个可复用的 Subgraph Node
- **与 Group Nodes 的关键区别**: Subgraph 是真正的嵌套图，有独立的内部命名空间

#### 8.2 创建 Subgraph
```
步骤:
1. 选中要打包的节点
2. 点击工具栏的 Subgraph 图标
3. ComfyUI 自动分析输入/输出，创建 Subgraph 节点
4. 双击进入编辑模式，自定义 Input/Output Slots
```

#### 8.3 Subgraph 内部结构
```
[Subgraph Node]  ← 外部看到的是一个节点
  │
  ├── Input Slots  ← 暴露给外部的输入（可命名）
  │   ├── model (MODEL)
  │   ├── positive (CONDITIONING)
  │   └── seed (INT)
  │
  ├── [内部节点图]  ← 双击进入编辑
  │   ├── KSampler
  │   ├── VAEDecode
  │   └── ImageScale
  │
  └── Output Slots  ← 暴露给外部的输出
      └── image (IMAGE)
```

#### 8.4 Subgraph 操作
- 像普通节点一样: 变色、重命名、Bypass、Mute
- 双击空白区域进入编辑模式
- 导航栏返回上层
- 右键连接点可重命名/删除暴露的 Slot
- v0.3.66+ 支持 Parameters Panel 直接编辑参数（无需进入 Subgraph）

#### 8.5 Subgraph vs Group Nodes (Legacy)

| 特性 | Subgraph (现代) | Group Nodes (Legacy) |
|------|----------------|---------------------|
| 实现 | 真正的嵌套图 | 宏展开（运行时展平） |
| 内部命名空间 | ✅ 独立 | ❌ 共享全局 |
| 嵌套支持 | ✅ 可嵌套 | ❌ 不可嵌套 |
| 参数面板 | ✅ 外部可编辑 | ⚠️ 有限 |
| 分享/复用 | ✅ 可发布到 Registry | ⚠️ 需手动复制 |
| 维护状态 | ✅ 活跃开发 | ⚠️ 仅向后兼容维护 |

### 9. App Mode & App Builder (2026 新特性)

#### 9.1 App Mode
- **一键切换**: 点击 "Enter App Mode"，节点图消失
- **替换为**: 清晰的用户界面（只有必要的输入控件）
- **本质**: 同一个 ComfyUI 实例，同一个后端，同一个队列
- **意义**: 任何 ComfyUI 工作流都可以变成"应用"

#### 9.2 App Builder
- 选择哪些节点输入暴露为 App 输入
- 选择哪些节点输出暴露为 App 输出
- 其他参数锁定，对用户不可见
- 可重命名、重排序、分组输入控件

```
示例: text2img 工作流可能有几十个参数
App Builder 只暴露:
  - Prompt (文本框)
  - Style (下拉选择)
  - Aspect Ratio (下拉选择)
其余（sampler/steps/CFG/scheduler/model...）都锁定为预设值
```

#### 9.3 URL 分享
- 生成的 URL 编码了: 工作流配置 + App 布局 + 节点绑定
- 接收者可直接在浏览器打开运行（通过 Comfy Cloud）
- 无需安装任何东西

#### 9.4 ComfyHub
- 公共层: 创作者发布完成的 App 和工作流
- 与 Node Registry 互补: Registry 给开发者发布节点，ComfyHub 给创作者发布作品
- URL: comfy.org/workflows

### 10. ComfyUI Node Registry

#### 10.1 概念
- 自定义节点的**官方发布/分发平台**
- 替代旧的 ComfyUI-Manager + GitHub 直接安装方式
- 语义化版本管理 + 依赖声明

#### 10.2 发布流程

```
1. 创建 Publisher 账号 (registry.comfy.org)
   → 获得全局唯一 Publisher ID

2. 初始化元数据
   $ comfy node init
   → 生成 pyproject.toml

3. 配置 pyproject.toml
   [project]
   name = "my-awesome-node"
   version = "1.0.0"
   description = "..."
   dependencies = [...]

   [tool.comfy]
   PublisherId = "my-publisher-id"
   DisplayName = "My Awesome Node"

4. 发布
   $ comfy node publish
   或通过 GitHub Actions CI/CD 自动发布
```

#### 10.3 GitHub Actions 自动发布
```yaml
name: Publish to Comfy registry
on:
  push:
    branches: [main]
    paths: ["pyproject.toml"]
jobs:
  publish-node:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Comfy-Org/publish-node-action@main
        with:
          personal_access_token: ${{ secrets.REGISTRY_ACCESS_TOKEN }}
```

### 11. 工作流设计模式 (Workflow Design Patterns)

#### 11.1 模式一: 管线模式 (Pipeline)
```
[加载] → [预处理] → [生成] → [后处理] → [输出]
  │         │          │         │          │
  模型      裁剪/缩放   KSampler   放大/修复   保存/预览
  LoRA      ControlNet  CFG/步数   人脸修复
  Embedding 蒙版
```
- 线性流程，每步一个 Subgraph
- 最常见的基础工作流结构

#### 11.2 模式二: 分支合并模式 (Branch & Merge)
```
              ┌→ [区域 A 条件] ─┐
[共享基础] ──┤                  ├→ [合并] → [采样] → [输出]
              └→ [区域 B 条件] ─┘
```
- 区域 Prompt、多 ControlNet、条件组合
- 利用 Conditioning Combine / Set Area

#### 11.3 模式三: 多阶段精炼模式 (Multi-Stage Refinement)
```
[Stage 1: 低分辨率生成] → [Stage 2: 放大+轻 denoise] → [Stage 3: 细节修复]
     512x512                    1024x1024                  人脸/手部修复
     KSampler                   KSampler (denoise=0.3)     FaceDetailer
```
- Hires Fix / 超分管线
- 每阶段一个 Subgraph

#### 11.4 模式四: 条件路由模式 (Conditional Routing)
```
[输入] → [Switch/Route] ─┬→ [SD1.5 管线]
                          ├→ [SDXL 管线]
                          └→ [Flux 管线]
```
- 利用 Lazy Evaluation + ExecutionBlocker
- 动态选择执行路径

#### 11.5 模式五: 迭代循环模式 (Iterative Loop)
```
[初始生成] → [评估] → [满意?] ─ 否 → [调整参数] → [重新生成]
                        │
                       是 → [输出]
```
- ComfyUI 原生不支持真正循环
- 通过 API 脚本实现（batch_api_runner.py 模式）
- 或用 Node Expansion 模拟

### 12. 工作流最佳实践

#### 12.1 命名规范
```
✅ 好的习惯:
- 节点标题描述功能: "Base KSampler (512x512)" 而非 "KSampler"
- Subgraph 命名: "Upscale 2x Pipeline" 而非 "Sub1"
- 颜色编码: 加载=蓝色, 条件=绿色, 采样=红色, 后处理=紫色

❌ 坏的习惯:
- 默认节点名称不改
- 线条交叉混乱
- 参数分散在各处
```

#### 12.2 模块化原则
```
1. 单一职责: 每个 Subgraph 做一件事
2. 接口最小化: 只暴露必要的输入/输出
3. 默认值合理: 内部参数设好默认值
4. 文档化: 节点标题即文档
5. 可测试: 每个 Subgraph 可独立运行测试
```

#### 12.3 版本管理
```
工作流文件管理:
comfyui-workflows/
├── production/           # 生产级工作流
│   ├── text2img-v2.1.json
│   └── video-pipeline-v1.0.json
├── experiments/          # 实验性工作流
│   └── flux-lora-test.json
├── templates/            # 可复用模板
│   ├── base-sdxl.json
│   └── upscale-2x.json
└── README.md             # 工作流文档
```

### 13. ComfyUI 生态系统全景 (2026 Q1)

```
┌──────────────────────────────────────────────────────┐
│                  ComfyUI 生态全景                      │
├──────────────┬───────────────┬────────────────────────┤
│   开发层      │   平台层       │   用户层              │
├──────────────┼───────────────┼────────────────────────┤
│ ComfyUI Core │ Node Registry │ App Mode               │
│ Custom Nodes │ ComfyHub      │ App Builder             │
│ Subgraph API │ Comfy Cloud   │ URL 分享               │
│ V3 Spec      │ comfy-cli     │ Workflow Templates     │
│ Vue Frontend │ CI/CD Actions │ ComfyHub 浏览          │
├──────────────┼───────────────┼────────────────────────┤
│ 开发者        │ 平台运营      │ 终端用户               │
│ 写节点/发布   │ 托管/分发     │ 使用/分享              │
└──────────────┴───────────────┴────────────────────────┘
```

---

## 第三部分: 实验与实操

### 实验 #50: 微调技术全景信息图

使用 RunningHub rhart-image-n-pro/text-to-image 生成一张微调技术对比概念图。

**Prompt**: "A comprehensive infographic comparing 5 AI model fine-tuning techniques arranged horizontally: Textual Inversion (tiny icon, brain with word), Hypernetwork (small network icon, crossed out), LoRA (medium icon, matrices), DreamBooth (large icon, camera), Full Fine-tune (huge icon, entire model). Each shows relative size and complexity. Clean tech illustration style, white background, labeled diagram"

### 实验 #51: Embedding 概念验证

使用 RunningHub 测试 negative embedding 效果 — 对比有无 negative embedding 的生成质量差异。

---

## 关键洞察

1. **Textual Inversion 的独特价值**: 虽然 LoRA 几乎全面替代了 TI，但 TI 在两个场景仍不可替代:
   - **Negative Embedding**: 将复杂负面概念打包为一个 token（EasyNegative 等）
   - **跨模型兼容**: 同架构模型间零成本迁移（LoRA 有版本绑定风险）

2. **DreamBooth 并未过时**: 与 LoRA 结合后（DreamBooth + LoRA），成为特定人物/物体个性化的最佳方案，因为 Prior Preservation Loss 提供了关键的防遗忘机制

3. **ComfyUI 工程化三件套**: Subgraph（模块化） + Registry（分发） + App Mode（用户友好化）构成了完整的工作流生产化管线

4. **Hypernetwork 已彻底弃用**: 2024 年后的社区共识，LoRA 在所有维度全面超越

5. **ComfyHub 的意义**: 从"工具"到"平台"的转变 — ComfyUI 不再只是开发者工具，而是有完整生态的创作平台
