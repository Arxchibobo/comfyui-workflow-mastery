# ComfyUI Workflow Generator Skill — 问题审计与修复方案

## 一、测试中暴露的问题

### 🔴 致命问题：workspace setContent 执行不可靠
- **现象**：`setContent` 保存新工作流后，`/task/openapi/create` 仍执行缓存的旧工作流
- **影响**：之前 52 个测试可能大部分是假阳性（输出都是同一个旧工作流的结果）
- **根因**：`setContent` 保存的是 UI 层内容，`/task/openapi/create` 用的是 workspace 上次通过 UI "Queue" 保存的 API format
- **受影响代码**：`workflow_compiler.py` 的 `save_and_execute()` 函数（第 1010-1070 行）

### 🔴 严重问题：没有验证输出
- **现象**：向用户发送了赛博朋克汽车图片而不是炭治郎角色
- **根因**：收到 `SUCCESS` 状态就直接下载发送，没有验证图片内容
- **缺失**：没有 output validation 步骤

### 🟡 架构问题：只有 workspace 一条执行路径
- **现状**：compiler 只能 workspace setContent → create
- **缺失**：没有集成 template+nodeInfoList（可靠）、runninghub.py（179 endpoints）、runninghub_app.py（AI App）
- **后果**：视频/音频/3D 都做不了，说"做不到"被批评

### 🟡 模板覆盖不足
- **现状**：只有 5 个官方模板（text2img/img2img/lora/upscale/controlnet）
- **缺失**：视频（Wan2.2/Kling/Vidu 等 65+）、音频（TTS/音乐 7+）、3D（Hunyuan3D 11+）

## 二、优缺点分析

### ✅ 优点
1. **节点知识库扎实**：206 种节点类型、65 种数据类型、完整的 producer/consumer 图
2. **编译能力强**：能从零编写 text2img/img2img/LoRA/ControlNet/Inpaint/Outpaint 等拓扑
3. **知识文档丰富**：14 个 MD 文件，覆盖深度学习指南、工作流模式、节点参考
4. **模板参数映射清晰**：5 个模板的 nodeId/fieldName/default 都已整理

### ❌ 缺点
1. **执行引擎是断的**：workspace setContent 方式不可靠
2. **单一执行路径**：没有 fallback，一条路不通就彻底失败
3. **视频/音频/3D 空白**：compiler 只能编译图像工作流
4. **没有集成现有工具**：runninghub.py (179 endpoints) 和 runninghub_app.py (AI App) 完全没用上
5. **缺少 output verification**：盲目信任 SUCCESS 状态

## 三、修复方案

### 修复 1：重写执行引擎（三路径 fallback）
```
路径 A：Template + nodeInfoList（图像基础任务）
  → 5 个官方模板 + 参数覆盖
  → 最可靠，延迟最低

路径 B：Standard API via runninghub.py（179 个端点）
  → 视频/音频/3D/文本/超分
  → 覆盖最广

路径 C：AI App via runninghub_app.py（复杂 ComfyUI 工作流）
  → 动作迁移/换脸/高清舞蹈等
  → 用 --info 获取节点 → --run 执行
```

### 修复 2：Task Router 决策树
```
用户需求 → 判断任务类型
  ├─ 图像生成/编辑 → 路径 A (template+nodeInfoList)
  ├─ 视频生成 → 路径 B (runninghub.py video endpoints)
  ├─ 音频/TTS → 路径 B (runninghub.py audio endpoints)
  ├─ 3D 模型 → 路径 B (runninghub.py 3d endpoints)
  ├─ 动作迁移/换脸 → 路径 C (AI App)
  └─ 自定义工作流 → 路径 C (AI App by webappId)
```

### 修复 3：Output Verification
- 每次输出下载后，用 `read` 验证图片内容
- 视频用 `ffprobe` 验证格式/时长
- 不匹配预期时自动重试或报警

### 修复 4：删除 workspace setContent 执行路径
- 从 compiler 中移除 `save_and_execute()` 函数
- 保留编译能力（生成 JSON），但执行走 template 或 API
