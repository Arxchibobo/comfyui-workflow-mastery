# ComfyUI 工作流知识库

## ComfyUI 简介

ComfyUI 是一个基于节点的 AI 图像/视频生成工具，采用图形化编程方式构建复杂的 AI 工作流。用户通过连接不同功能的节点来创建从简单的文本生图到复杂的视频编辑的完整管线。

## 工作流概念

### 核心原理
- **节点 (Nodes)**: 每个节点执行特定功能（加载模型、编码文本、采样等）
- **连接 (Links)**: 节点间的数据流，将一个节点的输出连接到另一个节点的输入
- **数据类型**: MODEL、CLIP、VAE、CONDITIONING、LATENT、IMAGE、VIDEO 等
- **执行顺序**: 基于依赖关系自动确定，从输入节点开始，沿连接传递数据到输出节点

### 典型工作流结构
```
输入 → 预处理 → 模型推理 → 后处理 → 输出
```

## JSON 格式规范

ComfyUI 支持两种 JSON 格式，我们重点关注 **API format**，它更适合程序化生成和执行。

### UI Format vs API Format

#### UI Format (workflow.json)
- 用于 ComfyUI Web 界面的可视化编辑
- 包含节点位置、连接线样式等 UI 信息
- 结构复杂，包含 `nodes`、`links`、`groups` 等顶级字段

#### API Format (workflow_api.json) ⭐ **推荐使用**
- 用于程序化执行工作流
- 结构简洁，只关注节点逻辑和数据流
- 每个节点是一个 key-value 对，key 是节点 ID（字符串）

### API Format 详细规范

#### 基本结构
```json
{
  "节点ID": {
    "inputs": {
      "参数名": "参数值",
      "连接输入": ["源节点ID", 输出索引]
    },
    "class_type": "节点类型名",
    "_meta": {
      "title": "节点显示名称"
    }
  }
}
```

#### 连接格式 `["node_id", output_index]`
- **node_id**: 源节点的 ID（字符串）
- **output_index**: 源节点的输出索引（从 0 开始的整数）

示例：
```json
{
  "3": {
    "inputs": {
      "model": ["4", 0],        // 连接到节点4的第0个输出
      "positive": ["6", 0],     // 连接到节点6的第0个输出
      "negative": ["7", 0]      // 连接到节点7的第0个输出
    },
    "class_type": "KSampler"
  }
}
```

#### 节点 ID 命名规则
- **必须是字符串**（如 "1", "2", "3" 而不是数字）
- 通常使用连续数字，但可以是任意字符串
- 在同一工作流中必须唯一

#### 输入类型
1. **直接值**: 字符串、数字、布尔值等
   ```json
   "seed": 685468484323813,
   "steps": 20,
   "cfg": 8.0,
   "sampler_name": "euler"
   ```

2. **连接引用**: `["源节点ID", 输出索引]`
   ```json
   "model": ["4", 0],
   "images": ["8", 0]
   ```

#### 完整示例 - 基础文生图工作流
```json
{
  "3": {
    "inputs": {
      "seed": 685468484323813,
      "steps": 20,
      "cfg": 8.0,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1.0,
      "model": ["4", 0],
      "positive": ["6", 0],
      "negative": ["7", 0],
      "latent_image": ["5", 0]
    },
    "class_type": "KSampler",
    "_meta": {"title": "KSampler"}
  },
  "4": {
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly-fp16.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {"title": "Load Checkpoint"}
  },
  "5": {
    "inputs": {"width": 512, "height": 512, "batch_size": 1},
    "class_type": "EmptyLatentImage",
    "_meta": {"title": "Empty Latent Image"}
  },
  "6": {
    "inputs": {
      "text": "beautiful scenery nature glass bottle landscape",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "CLIP Text Encode (Positive)"}
  },
  "7": {
    "inputs": {
      "text": "text, watermark",
      "clip": ["4", 1]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {"title": "CLIP Text Encode (Negative)"}
  },
  "8": {
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    },
    "class_type": "VAEDecode",
    "_meta": {"title": "VAE Decode"}
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["8", 0]
    },
    "class_type": "SaveImage",
    "_meta": {"title": "Save Image"}
  }
}
```

## 目录结构

```
comfyui-knowledge-base/
├── README.md                 # 本文件 - 总览和格式规范
├── node-reference.md         # 节点参考手册
├── model-compatibility.md    # 模型兼容性表
└── workflow-templates/       # 工作流模板目录
    ├── text-to-image.md     # 文生图工作流
    ├── image-editing.md     # 图片编辑工作流
    ├── image-to-video.md    # 图生视频工作流
    ├── text-to-video.md     # 文生视频工作流
    ├── controlnet.md        # ControlNet 工作流
    ├── upscale.md           # 超分辨率工作流
    ├── face-swap-lipsync.md # 换脸和唇同步工作流
    ├── audio.md             # 音频生成工作流
    ├── 3d-generation.md     # 3D 模型生成工作流
    └── advanced-patterns.md # 高级模式工作流
```

## 使用指南

1. **新手入门**: 先阅读本 README，了解基本概念
2. **节点查询**: 查看 `node-reference.md` 了解具体节点用法
3. **工作流构建**: 从 `workflow-templates/` 目录选择合适的模板
4. **模型选择**: 参考 `model-compatibility.md` 选择兼容的模型
5. **参数调优**: 根据模板中的调参建议进行优化

## 重要提醒

⚠️ **使用 API Format**: 所有工作流模板都使用 API format，可直接通过 ComfyUI API 执行
⚠️ **节点 ID**: 必须是字符串类型，如 "1" 而不是 1
⚠️ **连接格式**: 严格使用 `["node_id", output_index]` 格式
⚠️ **完整链路**: 确保每个工作流都包含从输入到输出的完整节点链路