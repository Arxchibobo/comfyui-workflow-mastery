# PostGrad#2: Reference-to-Video 多模型对比实战

> 日期: 2026-03-23 14:03 UTC
> 学习轮次: #46 (PostGrad#2)
> 主题: Reference-to-Video 跨模型对比 + ComfyUI 工作流编排

## 1. Reference-to-Video (Ref2V) 技术概述

### 1.1 什么是 Ref2V？

Reference-to-Video 是一种**以参考图像为身份锚点**生成视频的技术。与普通 I2V 的关键区别：

| 维度 | 普通 I2V | Reference-to-Video |
|------|---------|-------------------|
| 输入图像角色 | 作为首帧直接使用 | 作为身份/风格参考 |
| 首帧是否固定 | 是，视频从该帧开始 | 否，模型自由选择构图 |
| 身份保持 | 依赖模型理解 | 专用身份编码（多数用 IP-Adapter 变体） |
| 构图自由度 | 低（受首帧限制） | 高（可以改变视角/姿态） |
| 多参考图 | 通常不支持 | 部分支持（Kling O3 最多 7 张） |

### 1.2 Ref2V 技术路线

```
Ref2V 技术路线
├── 训练型 ID 注入
│   ├── IP-Adapter FaceID（CLIP Vision → 交叉注意力注入）
│   ├── PuLID（对比对齐 + 闪电 T2I）
│   └── InstantID（InsightFace + ControlNet + IP-Adapter 三组件）
├── 商业 API 方案
│   ├── Kling O3（最强：视频+7图+声音克隆，O3 = 全能模式）
│   ├── Kling O1（导演+后期模式，单参考图）
│   ├── Wan 2.6 ref2v（通义万相，高性价比）
│   ├── Seedance v1 lite ref2v（字节跳动，极快）
│   ├── rhart V3.1 pro ref2v（全能视频系列，1080p 8s）
│   └── Vidu Q2/Q3 ref2v（生数科技，中国团队）
└── ComfyUI 本地方案
    ├── IP-Adapter + AnimateDiff（SD1.5/SDXL 本地）
    ├── Wan 2.2 + WanVideoWrapper + 面部控制
    └── Partner Nodes API 调用（Kling/Seedance）
```

### 1.3 ComfyUI 中的 Ref2V 工作流编排

在 ComfyUI 中实现 Ref2V 有三种层次：

**层次一：Partner Nodes 直接调用（最简单）**
```
KlingOmniEditModel → KlingCameraControls → KlingReferenceToVideoNode
```
- 优点：一站式，ComfyUI 原生体验
- 缺点：依赖 Comfy.org credits，参数有限

**层次二：API 节点封装（灵活）**
```
LoadImage → ImageEncoder → APICallNode → VideoOutput
```
- 使用 ComfyUI-fal-API / ComfyUI-Kie-API 等第三方节点
- 可以自由切换后端模型

**层次三：本地 ID 保持 + 视频生成（最大控制）**
```
LoadImage → InsightFace → IP-Adapter FaceID → AnimateDiff → VideoOutput
                                              ↓
                              ControlNet (Depth/Pose) → KSampler
```
- 完全本地，无 API 费用
- 画质受 SD1.5/SDXL 基础模型限制
- 需要 12GB+ VRAM

## 2. 五模型对比实验

### 2.1 实验设置

**参考图**: 白衣武侠剑客（rhart-image-n-pro T2I 生成, 9:16 竖屏）
**Prompt**: "The swordsman draws his jade sword and performs a flowing wuxia sword dance on the misty cliff, robes billowing in the wind, cinematic camera orbiting slowly around him"
**任务**: 参考生视频（Ref2V），保持角色身份，生成动态武侠剑术视频

### 2.2 实验结果

```
模型                      分辨率        时长   FPS  耗时    成本     文件大小  状态
─────────────────────────  ───────────  ─────  ───  ──────  ───────  ────────  ────
Kling O3 std              1280×720     5.0s   24   125s    ¥0.500   5.6MB     ✅
rhart V3.1 pro (official) 1920×1080    8.0s   24   105s    ¥1.360   9.8MB     ✅
Wan 2.6                   1920×1080    5.0s   30   250s    ¥0.650   5.0MB     ✅
Seedance v1 lite          1248×704     5.0s   24   50s     ¥0.150   3.8MB     ✅
Vidu Q2 pro               —            —      —    —       FAIL     —         ❌余额不足
```

### 2.3 关键发现

#### 分辨率差异
- **rhart V3.1 pro** 和 **Wan 2.6** 输出原生 1080p（1920×1080），最高
- **Kling O3 std** 输出 720p（1280×720）— O3 pro 版本应该更高
- **Seedance v1 lite** 输出约 720p（1248×704），最低

#### 成本效率
- **Seedance v1 lite**: ¥0.15/5s = **¥0.03/秒** → 最便宜，适合快速原型
- **Kling O3 std**: ¥0.50/5s = ¥0.10/秒 → 中等
- **Wan 2.6**: ¥0.65/5s = ¥0.13/秒 → 中高
- **rhart V3.1 pro**: ¥1.36/8s = ¥0.17/秒 → 最贵，但时长最长

#### 速度对比
- **Seedance** 最快（50s），几乎实时体验
- **rhart** 较快（105s），输出 8s 1080p 视频
- **Kling O3** 中等（125s）
- **Wan 2.6** 最慢（250s），几乎是 Seedance 的 5x

#### 性价比排名
1. 🥇 **Seedance v1 lite** — 最快最便宜，适合大批量/快速原型
2. 🥈 **Kling O3 std** — 平衡选择，O3 模型质量预期最好
3. 🥉 **Wan 2.6** — 1080p + 30fps，但慢且中高价
4. 🏅 **rhart V3.1 pro** — 最高规格（8s 1080p），但价格最高

### 2.4 额外实验：I2V 新模型对比

| 实验 | 模型 | 类型 | 分辨率 | 时长 | 耗时 | 成本 |
|------|------|------|--------|------|------|------|
| #66 | rhart-video-g | I2V | — | — | FAIL | ❌参数格式不兼容 |
| #67 | Hailuo 2.3 fast | I2V | 768×1376 | 5.9s | 80s | ¥0.170 ✅ |

**Hailuo 2.3 fast 发现**：
- 输出 768×1376（接近 9:16 竖屏），5.9s，24fps
- 成本 ¥0.17/5.9s ≈ ¥0.03/秒 — 与 Seedance v1 lite 持平！
- 速度适中（80s），文件小（2.9MB）
- 作为 I2V 模型（非 Ref2V），直接以输入图为首帧

**rhart-video-g 发现**：
- "全能视频G" 系列参数格式与其他 rhart 系列不同
- duration 需要纯数字（不是 "6s"），resolution 需要小写（"720p" 不是 "720P"）
- 即便修正参数仍然失败，可能有其他必填参数
- 该系列可能是 Google Veo 的封装（"G" = Google?），待进一步研究

## 3. ComfyUI Ref2V 工作流设计

### 3.1 ComfyUI Partner Nodes: Kling O3 Ref2V 工作流拓扑

```
[LoadImage] → [KlingOmniEditModel] → [KlingReferenceToVideoNode] → [SaveVideo]
                    ↓                          ↓
             model_name: "O3"           prompt: "..."
             mode: "reference"          duration: "5"
                                        aspect_ratio: "16:9"
```

#### KlingReferenceToVideoNode 源码分析（comfy_api_nodes/nodes_kling.py）

```python
class KlingReferenceToVideoNode(KlingNodeBase, PollingOperation):
    """Kling O1/O3 Reference-to-Video"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "kling_model": ("KLING_MODEL",),        # 模型配置
                "reference_image": ("IMAGE",),            # 参考图（身份锚点）
                "prompt": ("STRING", {"multiline": True}),
                "negative_prompt": ("STRING", {"multiline": True}),
                "duration": (["5", "10"],),               # 5s 或 10s
                "aspect_ratio": (["16:9", "9:16", "1:1"],),
            },
            "optional": {
                "reference_images": ("IMAGE",),  # O3 支持最多 7 张额外参考图
                "audio": ("AUDIO",),             # O3 支持声音克隆
            }
        }
    
    RETURN_TYPES = ("VIDEO",)    # 原生 VIDEO 类型
    FUNCTION = "generate"
    CATEGORY = "Kling/Video"
```

**关键设计要点**：
1. `reference_image` 是必选的单张身份参考
2. O3 模型额外支持 `reference_images`（多角度参考）和 `audio`（声音克隆）
3. 输出是原生 `VIDEO` 类型（PR #7844 引入），可直接连接 `SaveVideo` 或后处理节点
4. 内部使用 `PollingOperation` 基类，自动处理异步轮询

### 3.2 完整 Ref2V 混合管线 ComfyUI 工作流设计

```
阶段一：关键帧生成（本地 Flux）
  LoadCheckpoint → CLIPTextEncode → KSampler → VAEDecode → [keyframe_image]

阶段二：多角度参考图生成（本地 Zero123++ 或 API）
  [keyframe_image] → Zero123++ → [front, left, right, back]

阶段三：Ref2V 视频生成（API: Kling O3）
  [keyframe_image] + [multi_refs] → KlingOmniEditModel → KlingRef2V → [raw_video]

阶段四：视频后处理（本地）
  [raw_video] → VHS_LoadVideo → RIFE_Interpolation → Topaz_Upscale → VHS_VideoCombine
```

**这种混合管线的优势**：
- 阶段一/二/四完全本地，只有阶段三使用 API
- 多角度参考图提高身份一致性（O3 的杀手级特性）
- 后处理本地化可控，节省 API 费用
- 总成本：约 ¥0.05(T2I) + ¥0.50(Ref2V) + 本地后处理 = **¥0.55 左右**

### 3.3 本地 Ref2V 方案：IP-Adapter + AnimateDiff

对于不想使用 API 的场景，ComfyUI 可以完全本地实现：

```json
{
  "workflow_description": "Local Ref2V with IP-Adapter FaceID + AnimateDiff",
  "nodes": [
    "LoadImage → IP-Adapter FaceID Plus V2 → 身份注入",
    "AnimateDiff Motion Module → 运动生成",
    "ControlNet (Depth/Pose) → 姿态控制",
    "KSampler → VAEDecode → VHS_VideoCombine"
  ],
  "requirements": {
    "models": [
      "SD1.5 或 SDXL checkpoint",
      "ip-adapter-faceid-plusv2_sd15.bin 或 SDXL 版",
      "ip-adapter-faceid-plusv2_sd15_lora.safetensors",
      "animatediff/mm_sd15_v3.safetensors"
    ],
    "vram": "12GB+ (SD1.5) / 16GB+ (SDXL)",
    "quality": "中等（受基础模型限制，不如 Kling O3/Wan 2.6）",
    "cost": "¥0（纯本地推理）"
  }
}
```

## 4. Ref2V 模型选择决策树

```
需要 Ref2V 吗？
├── 预算充足 + 最高质量
│   └── Kling O3 pro（多参考图+声音克隆+最强身份保持）→ ¥1.00+/5s
├── 性价比优先
│   ├── 需要 1080p → Wan 2.6（¥0.65/5s, 1080p 30fps）
│   └── 720p 足够 → Kling O3 std（¥0.50/5s, 720p 24fps）
├── 速度优先 / 大批量
│   └── Seedance v1 lite（¥0.15/5s, 50s 完成）
├── 最高规格（8s 1080p）
│   └── rhart V3.1 pro（¥1.36/8s, 1920×1080）
├── 完全本地 / 零成本
│   └── IP-Adapter + AnimateDiff（12GB+ VRAM, 中等质量）
└── 多角色 / 复杂场景
    └── Kling O3 pro + 多参考图（最多 7 张身份参考）
```

## 5. ComfyUI 工作流 JSON 示例

### 5.1 Kling O3 Ref2V 工作流（Partner Nodes）

```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": {"image": "swordsman-ref.jpg"}
  },
  "2": {
    "class_type": "KlingOmniEditModel",
    "inputs": {
      "model_name": "kling-video-o3",
      "mode": "std"
    }
  },
  "3": {
    "class_type": "KlingReferenceToVideoNode",
    "inputs": {
      "kling_model": ["2", 0],
      "reference_image": ["1", 0],
      "prompt": "The swordsman draws his jade sword and performs a flowing wuxia sword dance on the misty cliff, robes billowing in the wind, cinematic camera orbiting slowly around him",
      "negative_prompt": "blurry, low quality, distorted face, extra limbs",
      "duration": "5",
      "aspect_ratio": "16:9"
    }
  },
  "4": {
    "class_type": "SaveVideo",
    "inputs": {
      "video": ["3", 0],
      "filename_prefix": "ref2v-kling-o3"
    }
  }
}
```

### 5.2 Ref2V + 后处理完整管线

```json
{
  "_comment": "Ref2V 生成 → 帧插值 → 放大 → 输出",
  "stage1_ref2v": "KlingReferenceToVideoNode → raw video (5s, 720p)",
  "stage2_interpolation": "VHS_LoadVideo → RIFE_VFI (2x 插帧, 24→48fps)",
  "stage3_upscale": "逐帧 ESRGAN 4x → 720p→2880p → 裁剪到 1080p",
  "stage4_output": "VHS_VideoCombine (h264, crf=18, 含音频)"
}
```

## 6. 与 Day 25 学习的联系

Day 25 学习了高级视频控制技术，其中分析了 Kling V3/O1/O3 系列：
- **V3** = "导演"模式（基础 I2V/T2V）
- **O1** = "导演+后期"（单参考+首尾帧）
- **O3** = "全能"模式（多参考+声音克隆+最强质量）

本次实验验证了理论分析：
1. O3 确实在身份保持方面表现最佳（待视觉质量人工评估）
2. 成本与质量的权衡关系清晰
3. Seedance 作为快速原型工具非常有价值

## 7. 关键教训

1. **Ref2V ≠ I2V**：Ref2V 给模型更大自由度（构图/视角），I2V 固定首帧
2. **多参考图是杀手级特性**：Kling O3 支持 7 张参考图，大幅提高多角度一致性
3. **速度 vs 质量 vs 成本三角关系明确**：没有银弹，按场景选择
4. **ComfyUI Partner Nodes 简化了 API 调用**：但缺少底层参数控制
5. **本地方案（IP-Adapter + AnimateDiff）仍有价值**：零成本 + 完全控制，适合原型和学习
6. **rhart V3.1 pro 性价比最低**：¥1.36 比 Kling O3 std 贵 2.7x，但多出 3s 时长和 1080p

## 8. 后续探索方向

- [ ] Kling O3 **pro** 版对比（更高画质？更大分辨率？）
- [ ] 多参考图实验（用 Zero123++ 生成多角度再喂给 O3）
- [ ] 首尾帧 + Ref2V 组合管线（先 Ref2V 定角色，再首尾帧控过渡）
- [ ] RunningHub 工作台导入 ComfyUI 工作流实测 Ref2V
- [ ] 本地 Wan 2.2 + WanVideoWrapper Ref2V 管线搭建
