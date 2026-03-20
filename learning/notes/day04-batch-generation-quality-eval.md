# Day 4 — 批量生成与质量评估方法论

> 学习时间: 2026-03-20 14:03 UTC (第 10 轮)

---

## 1. 图像生成质量评估指标体系

图像生成质量评估分为三大类：**分布级指标**（衡量整体生成能力）、**图像级指标**（衡量单张图片质量）、**对齐级指标**（衡量图文一致性）。

### 1.1 分布级指标（Distribution-level Metrics）

#### FID — Fréchet Inception Distance

**核心思想**: 比较真实图像分布和生成图像分布在 Inception-v3 特征空间中的距离。

**数学公式**:
```
FID = ||μ_r - μ_g||² + Tr(Σ_r + Σ_g - 2(Σ_r · Σ_g)^{1/2})
```

其中：
- `μ_r, Σ_r` = 真实图像在 Inception-v3 pool3 层（2048维）的均值和协方差
- `μ_g, Σ_g` = 生成图像的均值和协方差
- `Tr` = 矩阵的迹（trace）

**计算流程**:
1. 收集真实图像集 R（通常 ≥10K 张）和生成图像集 G（≥10K 张）
2. 将每张图像通过 Inception-v3 提取 2048 维特征向量
3. 分别计算 R 和 G 的多元高斯分布参数 (μ, Σ)
4. 计算两个高斯分布的 Fréchet 距离

**解读**:
- **越低越好**，0 = 完全相同的分布
- 典型范围：优秀模型 FID < 10，一般模型 10-50，差模型 > 50
- SD 1.5 在 COCO-30K 上约 FID ≈ 8-12
- SDXL 约 FID ≈ 6-9

**局限性**:
- 假设特征服从高斯分布（实际不一定）
- 对样本量敏感：<10K 张时估计不稳定
- 不能评估单张图片
- 对模式崩塌（mode collapse）有一定盲区

#### KID — Kernel Inception Distance

**改进 FID 的思路**: 使用 MMD（Maximum Mean Discrepancy）替代 Fréchet 距离，不需要高斯假设。

```
KID = MMD²(f_r, f_g)  （使用多项式核 k(x,y) = (x·y/d + 1)³）
```

**优势**: 无偏估计，小样本时比 FID 更稳定，有置信区间。

#### IS — Inception Score

```
IS = exp(E_x[KL(p(y|x) || p(y))])
```

- `p(y|x)` = Inception 对单张生成图的分类分布（应尖锐 → 质量好）
- `p(y)` = 所有生成图的边际分布（应均匀 → 多样性好）

**局限**: 不使用真实数据做参考，对 ImageNet 类别外的图像不敏感。现在逐渐被 FID 替代。

### 1.2 图像级指标（Image-level Metrics）

#### LPIPS — Learned Perceptual Image Patch Similarity

**用途**: 有参考图时，衡量两张图的感知相似度。

```
LPIPS(x, x₀) = Σ_l (1/H_l·W_l) · Σ_{h,w} ||w_l ⊙ (φ_l(x) - φ_l(x₀))||²
```

- `φ_l` = VGG/AlexNet 第 l 层的特征
- `w_l` = 学习到的每层权重

**解读**: 越低越好（更相似）。主要用于 img2img / inpainting / super-resolution 等有参考图的场景。

#### SSIM — Structural Similarity Index

经典的结构相似度指标，比较亮度、对比度、结构三个维度。

```
SSIM(x, y) = [l(x,y)]^α · [c(x,y)]^β · [s(x,y)]^γ
```

**局限**: 对高频细节敏感但对整体感知不够好，逐渐被 LPIPS 取代。

#### 无参考质量评估（No-Reference IQA）

- **NIQE**: 基于自然场景统计的无参考质量评估
- **BRISQUE**: 基于空间域自然场景统计
- **MUSIQ**: 多尺度图像质量 Transformer

### 1.3 对齐级指标（Alignment Metrics）— 最适合 Text2Img

#### CLIP Score

**核心思想**: 利用 CLIP 模型衡量生成图像与文本提示的语义对齐程度。

**计算**:
```
CLIP Score = max(cos(E_img(image), E_txt(text)) × 100, 0)
```

- `E_img` = CLIP 图像编码器
- `E_txt` = CLIP 文本编码器
- 余弦相似度 × 100 归一化

**解读**:
- **越高越好**，表示图文越匹配
- 典型范围：25-35 为正常，>30 为好
- **无需参考图像**，直接评估提示词→图像的对齐

**局限**:
- CLIP 本身的理解能力有限（复杂空间关系、数量计数等）
- 对艺术风格的判断不如人类
- 容易被"CLIP hack"欺骗（高CLIP分≠高质量）

#### ImageReward（NeurIPS 2023）

**核心**: 第一个通用的 text-to-image 人类偏好奖励模型。

- 基于 BLIP 架构 fine-tune
- 训练数据：137K 专家标注的 pair-wise 比较
- 比 CLIP Score 准确率高 38.6%，比 Aesthetic Score 高 39.6%

```python
import ImageReward as RM
model = RM.load("ImageReward-v1.0")
score = model.score("prompt text", "image_path.png")
# 也支持排序：model.inference_rank(prompt, [img1, img2, img3])
```

#### HPS v2 — Human Preference Score v2

- 基于 CLIP ViT-H/14 fine-tune
- 训练数据：798K 人类偏好标注
- 覆盖动画、照片、概念艺术、绘画 4 个类别

```python
import hpsv2
scores = hpsv2.score(images, "prompt text")
```

#### PickScore

- 基于 Pick-a-Pic 数据集（500K+ 用户偏好对）
- CLIP ViT-H backbone
- 强调"用户真实偏好"而非专家标注

### 1.4 指标选择决策树

```
目标：评估 Text2Img 生成质量
│
├─ 需要和真实数据集比较？
│  ├─ 是 → FID（≥10K 样本）或 KID（<10K 样本）
│  └─ 否 ↓
│
├─ 需要评估图文对齐？
│  ├─ 快速粗略 → CLIP Score
│  ├─ 接近人类判断 → ImageReward 或 HPS v2
│  └─ 否 ↓
│
├─ 有参考图？（img2img/inpainting）
│  ├─ 是 → LPIPS + SSIM
│  └─ 否 → NIQE / BRISQUE（无参考 IQA）
│
└─ 日常工作流优化？
   → CLIP Score + ImageReward 组合
     + 人眼主观评估（仍是金标准）
```

---

## 2. ComfyUI 批量生成方法论

### 2.1 方法概览

ComfyUI 支持三种批量生成方式：

| 方法 | 复杂度 | 灵活性 | 适用场景 |
|------|--------|--------|---------|
| **EmptyLatentImage batch_size** | ★☆☆ | 低 | 同参数多 seed 变体 |
| **RepeatLatentBatch 节点** | ★★☆ | 中 | img2img 批量变体 |
| **API 脚本循环** | ★★★ | 高 | 多 prompt/参数系统对比 |

### 2.2 方法 A: EmptyLatentImage batch_size（最简单）

**原理**: 在 EmptyLatentImage 节点设置 `batch_size > 1`，KSampler 会为每个 latent 样本使用不同的 noise（基于 seed 递增）。

**适用**: 快速生成同 prompt 的多个变体，评估 seed 对结果的影响。

**关键参数**: EmptyLatentImage → `batch_size: N`

**注意**: 
- batch_size 增大会线性增加显存占用
- 每个 batch item 的 seed = base_seed + batch_index
- 所有 batch item 共享相同的 prompt、sampler、steps 等参数

### 2.3 方法 B: RepeatLatentBatch + LatentBatchSeedBehavior

**RepeatLatentBatch**: 将一个 latent 复制 N 次，形成 batch。
**LatentBatchSeedBehavior**: 控制 batch 内各 latent 的 seed 行为：
- `random`: 每个 batch item 用不同 seed（默认）→ 生成多种变体
- `fixed`: 所有 batch item 用相同 seed → 适合 A/B 对比（改变其他参数时保持 seed 不变）

**适用**: img2img 场景生成多个变体，或需要精细控制 seed 行为时。

### 2.4 方法 C: API 脚本循环（最灵活，推荐用于系统性实验）

**核心流程**:
1. 在 ComfyUI UI 中设计好基础工作流
2. 开启 Dev Mode → Save (API Format) 导出 JSON
3. 用 Python 脚本加载 JSON，循环修改参数，逐个提交到 ComfyUI API

**API 端点**:
- `POST /prompt` — 提交工作流到队列
- `GET /history/{prompt_id}` — 查询执行结果
- `WebSocket /ws` — 实时进度监听
- `GET /view?filename=xxx` — 获取生成的图片

**Python 脚本核心结构**:

```python
import json, random, time
from urllib import request

SERVER = "http://127.0.0.1:8188"

def queue_prompt(workflow):
    """提交工作流到 ComfyUI 队列"""
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = request.Request(f"{SERVER}/prompt", data=data,
                         headers={'Content-Type': 'application/json'})
    return json.loads(request.urlopen(req).read())

def wait_for_completion(prompt_id, timeout=300):
    """轮询等待执行完成"""
    start = time.time()
    while time.time() - start < timeout:
        resp = json.loads(request.urlopen(f"{SERVER}/history/{prompt_id}").read())
        if prompt_id in resp:
            return resp[prompt_id]
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} timed out")

# 加载基础工作流
workflow = json.load(open('workflow_api.json'))

# 实验参数矩阵
prompts = ["a cat on a beach", "a mountain landscape", "portrait of a woman"]
seeds = [42, 123, 456, 789]
samplers = ["euler", "dpmpp_2m", "dpmpp_sde"]

# 遍历所有组合
for prompt in prompts:
    for seed in seeds:
        for sampler in samplers:
            # 修改工作流参数（节点 ID 需要根据实际工作流调整）
            workflow["6"]["inputs"]["text"] = prompt
            workflow["3"]["inputs"]["seed"] = seed
            workflow["3"]["inputs"]["sampler_name"] = sampler
            workflow["9"]["inputs"]["filename_prefix"] = f"{sampler}_s{seed}"
            
            # 提交并等待
            result = queue_prompt(workflow)
            prompt_id = result["prompt_id"]
            output = wait_for_completion(prompt_id)
            print(f"Done: {sampler}, seed={seed}, prompt={prompt[:30]}...")
```

### 2.5 高级: WebSocket 实时监控

```python
import websocket

ws = websocket.WebSocket()
ws.connect("ws://127.0.0.1:8188/ws?clientId=my_batch_script")

# 提交 prompt 后，通过 WebSocket 接收进度
while True:
    msg = json.loads(ws.recv())
    if msg["type"] == "progress":
        print(f"Step {msg['data']['value']}/{msg['data']['max']}")
    elif msg["type"] == "executed":
        print("Done!")
        break
```

---

## 3. 质量评估实践方案

### 3.1 人工评估（仍是金标准）

对于日常工作流优化，最实用的方法是 **结构化人工评估**：

**评分维度**（每项 1-5 分）：
1. **技术质量**: 清晰度、无伪影、无变形
2. **美学质量**: 构图、色彩、光影
3. **提示忠实度**: 与 prompt 描述的匹配程度
4. **细节丰富度**: 纹理、背景、微小细节

**A/B 对比法**:
- 固定 seed，只改变一个变量（采样器/步数/CFG 等）
- 让多人独立评分，取平均
- 记录偏好胜率（Win Rate）

### 3.2 自动化评估流水线（API Script + 评估脚本）

完整流水线：
```
参数矩阵定义 → ComfyUI API 批量生成 → 图片收集 → 自动评估 → 报告生成
```

**评估脚本（Python，使用 pyiqa 或 torchmetrics）**:

```python
# pip install pyiqa torch torchvision
import pyiqa
import torch
from pathlib import Path

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 初始化评估器
niqe = pyiqa.create_metric('niqe', device=device)      # 无参考质量
# clip_score 需要 torchmetrics
from torchmetrics.multimodal import CLIPScore
clip_metric = CLIPScore(model_name_or_path="openai/clip-vit-large-patch14").to(device)

def evaluate_batch(image_dir, prompts_map):
    """评估一批生成图像"""
    results = []
    for img_path in Path(image_dir).glob("*.png"):
        # 无参考质量
        niqe_score = niqe(str(img_path)).item()
        
        # CLIP Score（需要对应的 prompt）
        prompt = prompts_map.get(img_path.stem, "")
        if prompt:
            # 读取图像 tensor...
            clip_s = clip_metric(img_tensor, prompt).item()
        
        results.append({
            "file": img_path.name,
            "niqe": niqe_score,
            "clip_score": clip_s
        })
    return results
```

### 3.3 ComfyUI 内置对比方案

不使用外部脚本，纯 ComfyUI 内对比：
- 使用 **Image Comparer** 自定义节点（并排对比）
- 使用 **SaveImage** 带 `filename_prefix` 编码参数（如 `euler_s20_cfg7`）
- 使用 **PreviewImage** 节点快速查看中间结果

---

## 4. 实践经验总结

### 4.1 批量生成最佳实践

1. **控制变量**: 每次只改一个参数，其他全部固定（尤其是 seed）
2. **命名规范**: `{sampler}_{scheduler}_s{steps}_cfg{cfg}_seed{seed}.png`
3. **元数据保存**: ComfyUI 默认在 PNG 中嵌入工作流元数据（Settings → Metadata），确保开启
4. **显存管理**: batch_size 不要太大（4-8 为宜），大模型（SDXL）建议 batch_size=1 循环
5. **结果归档**: 每组实验建一个文件夹，附带参数记录 CSV

### 4.2 质量评估最佳实践

1. **FID/KID**: 适合论文级评估，日常不需要（需要大量参考图）
2. **CLIP Score**: 快速可用，但要注意其局限性
3. **ImageReward/HPS v2**: 最接近人类偏好，推荐作为自动评估首选
4. **人工评估**: 始终是最终决策依据，自动指标只做辅助筛选
5. **多指标组合**: 不要只看一个指标，建议 CLIP Score + ImageReward + 人工抽检

### 4.3 从批量实验中学到什么

通过系统性批量实验，可以回答以下关键问题：
- 哪个采样器在给定步数下质量最好？
- CFG 的甜蜜点在哪里？（通常 SD1.5: 7-9, SDXL: 5-8, Flux: 3.5-4）
- 在什么步数之后，增加步数不再有显著提升？
- 同一 prompt 不同 seed 的质量方差有多大？（方差大 = 模型不稳定）
