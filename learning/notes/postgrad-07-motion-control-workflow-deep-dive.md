# PostGrad #7: Kling Motion Control 实战 + ComfyUI 工作流编写

> 学习时间: 2026-03-24 00:03 UTC | 轮次: 51
> 主题: Motion Control 首次实测 + ComfyUI Partner Node 工作流 JSON + 新模型探索

---

## 1. Kling V3.0 Motion Control 技术深度

### 1.1 Motion Control 核心概念

Motion Control（动作控制/动作迁移）是视频生成中的高级控制技术，核心功能：
- **输入**: 参考图像（角色外观）+ 参考视频（动作来源）
- **输出**: 角色执行参考视频中动作的新视频
- **本质**: 将一个视频中的运动模式迁移到另一个角色上

### 1.2 Kling V3.0 Motion Control API 参数

```json
{
  "endpoint": "kling-v3.0-std/motion-control",
  "params": [
    {
      "key": "imageUrl",
      "type": "IMAGE",
      "required": true,
      "maxSizeMB": 10,
      "note": "角色参考图 — 定义外观/服装/身份"
    },
    {
      "key": "videoUrl",
      "type": "VIDEO",
      "required": true,
      "maxSizeMB": 10,
      "note": "动作参考视频 — 定义运动模式/姿态序列"
    },
    {
      "key": "characterOrientation",
      "type": "LIST",
      "options": ["image", "video"],
      "default": "video",
      "note": "角色朝向来源：image=遵循参考图朝向, video=遵循动作视频朝向"
    },
    {
      "key": "prompt",
      "type": "STRING",
      "maxLength": 2500,
      "note": "文本描述，辅助控制场景/风格/动作细节"
    },
    {
      "key": "negativePrompt",
      "type": "STRING",
      "maxLength": 2500,
      "note": "负面提示词"
    },
    {
      "key": "keepOriginalSound",
      "type": "BOOLEAN",
      "default": true,
      "note": "是否保留动作参考视频的原始音频"
    }
  ]
}
```

### 1.3 characterOrientation 参数深度解析

这是 Motion Control 最关键的参数之一：

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `video` (默认) | 角色朝向跟随动作视频中人物的朝向 | 正面舞蹈、简单动作 |
| `image` | 角色保持参考图中的朝向/姿态基准 | 侧面角色、特定角度、多角度一致性 |

**选择策略**:
- 参考图是正面全身 → `video` 模式效果通常更好
- 参考图有特定角度/构图 → `image` 模式保持一致性
- 面部一致性要求高 → `image` 模式（V3.0 Element Binding 增强）

### 1.4 Kling V3.0 vs V2.6 Motion Control 对比

| 维度 | V2.6 | V3.0 |
|------|------|------|
| 面部一致性 | 有限 | Element Binding 系统增强 |
| 复杂表情 | 容易变形 | 精确复杂表情 |
| 遮挡恢复 | 差 | 遮挡后自动恢复特征 |
| 镜头运动 | 固定 | 支持镜头运动中保持清晰 |
| 多角度稳定 | 侧面易失真 | 多角度面部稳定 |

### 1.5 Motion Control 管线设计原理

```
完整 Motion Control 管线:

Step 1: 角色参考图生成/准备
  ├── T2I 生成（Flux/SDXL/rhart）
  ├── 真实照片
  └── 要求: 清晰全身、简洁背景、高分辨率

Step 2: 动作参考视频获取
  ├── T2V 生成（Seedance/rhart-video-s）
  ├── 真实拍摄视频
  ├── 运动素材库
  └── 要求: 清晰人体动作、正面角度、适当时长

Step 3: Motion Control 执行
  ├── Kling V3.0 std/pro（API 调用）
  ├── characterOrientation 选择
  └── Prompt 辅助控制

Step 4: 后处理
  ├── 视频放大（Topaz/ESRGAN 逐帧）
  ├── 帧插值（RIFE）
  ├── 色彩校正
  └── 音频添加
```

---

## 2. ComfyUI Kling Motion Control Partner Node 源码分析

### 2.1 KlingMotionControlNode 工作流映射

基于 Day 12 的 Partner Nodes 架构分析，Kling Motion Control 在 ComfyUI 中的节点拓扑：

```
[LoadImage] → imageUrl
                        ↘
[KlingMotionControl] → [VIDEO output] → [SaveVideo/Preview]
                        ↗
[LoadVideo] → videoUrl
```

### 2.2 ComfyUI 工作流 JSON（Kling V3.0 Motion Control）

```json
{
  "1": {
    "class_type": "LoadImage",
    "inputs": {
      "image": "character_reference.png"
    }
  },
  "2": {
    "class_type": "VHS_LoadVideo",
    "inputs": {
      "video": "motion_reference.mp4",
      "force_rate": 0,
      "force_size": "Disabled",
      "frame_load_cap": 0,
      "skip_first_frames": 0,
      "select_every_nth": 1
    }
  },
  "3": {
    "class_type": "KlingMotionControlNode",
    "_meta": {
      "title": "Kling V3.0 Motion Control"
    },
    "inputs": {
      "image": ["1", 0],
      "video": ["2", 0],
      "character_orientation": "image",
      "prompt": "A martial arts warrior performing graceful movements",
      "negative_prompt": "blurry, distorted, low quality",
      "keep_original_sound": false,
      "AUTH_TOKEN_COMFY_ORG": "hidden"
    }
  },
  "4": {
    "class_type": "VHS_VideoCombine",
    "inputs": {
      "images": ["3", 0],
      "frame_rate": 24,
      "loop_count": 0,
      "filename_prefix": "motion_control_output",
      "format": "video/h264-mp4",
      "pingpong": false,
      "save_output": true
    }
  }
}
```

### 2.3 Partner Node 内部执行流程

```python
# 简化的 KlingMotionControlNode 执行流程（基于 Partner Nodes 架构）

class KlingMotionControlNode(PollingOperation):
    """Kling V3.0 Motion Control - 三层抽象中的 PollingOperation"""
    
    CATEGORY = "api_node/video/kling"
    RETURN_TYPES = ("VIDEO",)
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),           # 角色参考图
                "video": ("VIDEO",),           # 动作参考视频
                "character_orientation": (["image", "video"],),
            },
            "optional": {
                "prompt": ("STRING", {"multiline": True}),
                "negative_prompt": ("STRING", {"multiline": True}),
                "keep_original_sound": ("BOOLEAN", {"default": True}),
            },
            "hidden": {
                "AUTH_TOKEN_COMFY_ORG": ("STRING",),
            }
        }
    
    def execute(self, image, video, character_orientation, **kwargs):
        # Step 1: 上传图像到 Kling CDN
        image_url = self.upload_image(image)
        
        # Step 2: 上传视频到 Kling CDN
        video_url = self.upload_video(video)
        
        # Step 3: 提交 Motion Control 任务
        task = self.api.create_motion_control_task(
            image_url=image_url,
            video_url=video_url,
            character_orientation=character_orientation,
            prompt=kwargs.get("prompt", ""),
            negative_prompt=kwargs.get("negative_prompt", ""),
            keep_original_sound=kwargs.get("keep_original_sound", True),
        )
        
        # Step 4: 轮询等待结果（PollingOperation 基类提供）
        result = self.poll_until_complete(task.id)
        
        # Step 5: 下载视频 → VIDEO 类型 tensor
        video_tensor = self.download_video(result.video_url)
        
        return (video_tensor,)
```

### 2.4 VIDEO 原生数据类型（ComfyUI PR #7844）

Motion Control 的输出是 `VIDEO` 类型，这是 ComfyUI 在 2025 年引入的原生类型：

```
VIDEO 数据结构:
{
    "frames": Tensor[B, F, H, W, C],  # 帧序列 (batch, frames, height, width, channels)
    "fps": float,                      # 帧率
    "audio": Optional[AudioData],      # 可选音频轨道
    "metadata": {
        "duration": float,
        "codec": str,
        "source": str
    }
}
```

与 IMAGE 类型的关键区别：
- IMAGE: `[B, H, W, C]` — 批量图像
- VIDEO: `[B, F, H, W, C]` — 帧维度独立于批量维度

---

## 3. 实验记录

### 实验 #60: rhart-image-n-pro T2I — 角色参考图生成

| 项目 | 值 |
|------|-----|
| 端点 | rhart-image-n-pro/text-to-image |
| Prompt | "A young female martial arts warrior in a dynamic kung fu stance, wearing a flowing red silk outfit with gold dragon embroidery, hair tied in a high ponytail, athletic build, full body shot, studio lighting, white background, 8K ultra detailed" |
| 宽高比 | 9:16 (竖屏，全身展示) |
| 耗时 | ~20s |
| 成本 | ¥0.03 |
| 结果 | ✅ 高质量武术角色参考图，红色丝绸套装+金龙刺绣，清晰全身 |

### 实验 #60b: rhart-image-g-3 T2I — 新模型首测

| 项目 | 值 |
|------|-----|
| 端点 | rhart-image-g-3/text-to-image |
| 结果 | ❌ 模型繁忙(1011)，"当前模型负载较高，请稍后重试" |
| 分析 | g-3 基于 Gemini 3 Pro（推测），可能因高需求导致负载限制 |

### 实验 #61: Seedance T2V — 动作参考视频生成

| 项目 | 值 |
|------|-----|
| 端点 | seedance-v1.5-pro/text-to-video-fast |
| Prompt | "A person performing a slow graceful tai chi sequence, flowing movements, arms extending outward then pulling inward, weight shifting between legs, smooth continuous motion, filmed from front angle, plain studio background" |
| 宽高比 | 9:16 |
| 时长 | 5s |
| 耗时 | ~60s |
| 成本 | ¥0.30 |
| 结果 | ✅ 流畅的太极动作参考视频 |

### 实验 #62: Kling V3.0 Std Motion Control — 首次实测! ✅

| 项目 | 值 |
|------|-----|
| 端点 | kling-v3.0-std/motion-control |
| 角色参考 | 实验 #60 的武术角色图 (768x1376) |
| 动作参考 | 实验 #61 的太极动作视频 (5s) |
| characterOrientation | **image** |
| keepOriginalSound | false |
| Prompt | "A martial arts warrior performing graceful tai chi movements, flowing silk outfit, smooth motion" |
| 输出 | **720x1280, 30fps, 4.8s, 7.0MB** |
| 耗时 | **165s** (≈2.75min) |
| 成本 | **¥0.55** |
| 结果 | ✅ **成功！角色外观成功迁移到太极动作上** |

**关键观察**:
- 角色的红色丝绸服装和金龙刺绣被较好保留
- 太极动作流畅性良好
- 面部细节保持（V3.0 Element Binding 效果）
- characterOrientation=image 模式下角色朝向稳定

### 实验 #62b: characterOrientation=video 对比实验

| 项目 | 值 |
|------|-----|
| 端点 | kling-v3.0-std/motion-control |
| characterOrientation | **video** |
| 其他参数 | 与 #62 完全相同 |
| 结果 | ⏳ 任务已提交 (ID: 2036236883436380161)，但轮询超时 |
| 分析 | 可能因峰值时段排队延迟，Motion Control 比 I2V 更耗时 |

### 实验 #63: Topaz Low Resolution V2 放大

| 项目 | 值 |
|------|-----|
| 端点 | topazlabs/image-upscale/low-resolution-v2 |
| 输入 | 768x1376 (541KB) |
| 输出 | **1536x2752** (760KB) — 2x 放大 |
| 耗时 | ~15s |
| 成本 | ¥0.10 |
| 与 Standard V2 对比 | Low Resolution V2 专为低分辨率源图优化，适合 AI 生成图放大 |

**Topaz 放大模型选择指南（5种变体）**:

| 模型 | 适用场景 | 特点 |
|------|---------|------|
| Standard V2 | 通用放大 | 平衡质量和速度 |
| High Fidelity V2 | 高质量需求 | 最大化细节保留 |
| **Low Resolution V2** | AI 生成图/小图 | 针对低分辨率源优化 |
| CGI | 3D渲染/CGI | 适合非照片内容 |
| Text Refine | 含文字图像 | 优化文字清晰度 |

---

## 4. ComfyUI Motion Control 完整工作流设计

### 4.1 全链式管线（关键帧→动作参考→Motion Control→后处理）

```
[CheckpointLoaderSimple] → MODEL, CLIP, VAE
         ↓
[CLIPTextEncode(+)] → CONDITIONING
[CLIPTextEncode(-)] → CONDITIONING  
         ↓
[EmptyLatentImage] → LATENT (9:16, 768x1344)
         ↓
[KSampler] → LATENT
         ↓
[VAEDecode] → IMAGE (角色参考图)
         ↓                              ↓
[SaveImage]              [KlingMotionControlNode]
                                        ↑
              [VHS_LoadVideo] → VIDEO (动作参考)
                                        ↓
                              [VIDEO output]
                                        ↓
                              [VHS_VideoCombine] → 最终视频
```

### 4.2 混合管线：本地生成 + API 视频 + 本地后处理

这是最实用的生产模式：

```
阶段 1: 本地关键帧生成（Flux/SDXL, 免费）
  ↓
阶段 2: API Motion Control（Kling V3.0, ¥0.50-0.75）
  ↓
阶段 3: 本地后处理（放大/插帧/调色, 免费）
```

成本估算:
- 关键帧: ¥0 (本地) 或 ¥0.03 (API)
- 动作参考: ¥0 (素材库) 或 ¥0.30 (T2V 生成)
- Motion Control: ¥0.50 (std) 或 ¥0.75 (pro)
- 后处理: ¥0 (本地)
- **总计: ¥0.50-1.08 per 视频**

---

## 5. rhart-image-g-3 模型分析

### 5.1 模型定位

rhart-image-g-3（全能图片X-3）是 RunningHub 平台上排名第 3 的文生图模型：

| 排名 | 模型 | 基础 | 特点 |
|------|------|------|------|
| #1 | rhart-image-n-pro | Gemini Pro | 高质量通用 |
| #2 | rhart-image-g-1.5 | Gemini 1.5 Pro | 平衡型 |
| #3 | **rhart-image-g-3** | Gemini 3 | 最新多模态 |
| #4 | rhart-image-g-4 | Gemini 4? | 电影级写实 |
| #5 | rhart-image-n-g31-flash | Gemini 3.1 Flash | 快速低成本 |

推测 g-3 基于 Google Gemini 3 Pro 图像生成能力（类似 nano-banana-pro），与 rhart-image-n-pro 的区别可能在于：
- g-3: 更强的多模态理解、更好的文字渲染
- n-pro: 更成熟的图像美学、更稳定的输出

### 5.2 也支持 I2I 和 T2I

从端点列表看，g-3 同时支持：
- `text-to-image` — 文生图
- `image-to-image` — 图生图编辑

---

## 6. Motion Control vs 相关技术对比

| 维度 | Motion Control | Reference-to-Video | Start-End-to-Video | I2V |
|------|---------------|--------------------|--------------------|-----|
| 输入 | 图+视频 | 图+多图+prompt | 首帧+尾帧 | 图+prompt |
| 控制维度 | 动作迁移 | 身份保持 | 过渡动画 | 简单动画化 |
| 复杂度 | 高 | 高 | 中 | 低 |
| 成本 | ¥0.50-0.75 | ¥0.50-0.65 | ¥0.20-0.55 | ¥0.30-0.75 |
| 最佳场景 | 角色执行指定动作 | 角色一致性多场景 | 状态过渡动画 | 静图动起来 |
| ComfyUI 节点 | KlingMotionControl | KlingOmniEditModel | SeedanceFLF2V/ViduS2E | KlingI2V/SeedanceI2V |

### 关键选择策略

```
需求判断:
├── "让这个角色做这个动作" → Motion Control
├── "保持角色一致拍不同场景" → Reference-to-Video  
├── "从 A 状态变到 B 状态" → Start-End-to-Video
├── "让这张图动起来" → I2V
└── "生成角色跳舞视频" → Motion Control (最精确) 或 T2V (简单场景)
```

---

## 7. ComfyUI 工作流 JSON — 完整 Motion Control 管线

详见: `sample-workflows/video/kling-v3-motion-control.json`

这个工作流包含:
1. 角色图像加载节点
2. 动作视频加载节点（VHS_LoadVideo）
3. KlingMotionControlNode（Partner Node）
4. 视频输出节点（VHS_VideoCombine）
5. 可选: 后处理管线（放大+插帧）

---

## 8. 关键发现与经验总结

### 8.1 Motion Control 实操注意事项
1. **角色图要求**: 全身清晰、简洁背景、高分辨率（≥1024px 长边）
2. **动作视频要求**: 清晰人体动作、正面角度优先、5s 最佳（太长容易失真）
3. **characterOrientation**: 正面角色用 `video`，特定角度用 `image`
4. **Prompt 辅助**: 描述服装/场景细节可提升一致性，但不要与动作矛盾
5. **成本**: std ≈ ¥0.50, pro ≈ ¥0.75

### 8.2 两步法 vs 一步法
- **两步法**（推荐）: T2I 生成角色 → Motion Control 迁移动作（可控性强）
- **一步法**: 直接 T2V 生成（简单但不可控）

### 8.3 rhart-image-g-3 模型状态
- 2026-03-24 测试时模型负载过高（1011 错误）
- 排名第 3 说明需求旺盛
- 后续需在低峰时段重试对比

---

## 8b. Kling Elements（Element Binding 入口）分析

### API 参数

```json
{
  "endpoint": "kling-elements",
  "output_type": "string",  // 返回 element ID
  "params": [
    {"key": "name", "type": "STRING", "required": true},
    {"key": "description", "type": "STRING", "required": true},
    {"key": "imageUrl", "type": "IMAGE", "required": true},
    {"key": "elementReferList", "type": "IMAGE", "required": true, "multiple": true, "maxCount": 3}
  ]
}
```

### 工作原理

1. **创建阶段**: 上传角色参考图(1-3张) → Kling 提取角色特征 → 返回 element ID
2. **使用阶段**: 在 T2V/I2V/Motion Control 中引用 element ID → 确保角色一致性
3. **本质**: 预计算角色嵌入向量，运行时注入生成过程（类似 IP-Adapter 预计算）

### ComfyUI 映射

```
[LoadImage ×3] → [KlingElementBinding] → element_id (STRING)
                                              ↓
                               [KlingI2V / KlingMotionControl]
                               (element_id 作为隐藏输入注入)
```

**实测状态**: RunningHub 的文件上传 API 返回错误，Element Binding 实验暂时搁置。需要在 RunningHub 工作台 UI 中尝试。

---

## 9. 本轮实验成本汇总

| 实验 | 端点 | 成本 |
|------|------|------|
| #60 | rhart-image-n-pro T2I | ¥0.03 |
| #60b | rhart-image-g-3 T2I | ¥0 (模型繁忙) |
| #61 | Seedance T2V | ¥0.30 |
| #62 | Kling V3.0 Std Motion Control (image) | ¥0.55 |
| #62b | Kling V3.0 Std Motion Control (video) | ¥0.55 (超时但已扣费) |
| #63 | Topaz Low Resolution V2 | ¥0.10 |
| **总计** | | **¥1.53** |

---

## 10. 下一步计划

- [ ] 重试 rhart-image-g-3 T2I 对比测试
- [ ] 测试 Kling V3.0 Pro Motion Control（与 std 对比）
- [ ] 测试 characterOrientation=video 模式对比
- [ ] 编写 ComfyUI VACE Motion Transfer 本地工作流
- [ ] 探索 HiTem3D Portrait 3D 人像生成
