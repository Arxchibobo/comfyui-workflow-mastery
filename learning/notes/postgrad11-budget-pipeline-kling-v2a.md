# PostGrad#11: Budget Video Pipeline + ComfyUI Kling V2A 节点架构深度分析

**日期**: 2026-03-24  
**轮次**: Session 55 (PostGrad#11)  
**主题**: 低成本视频生产管线 + Kling Partner Node 源码架构分析  
**实验数量**: 5 个 API 实验 + 2 个工作流 JSON  
**花费**: ¥0.03(T2I) + ¥0.20(Wan) + ¥0.20(Vidu) + ¥0.25(Hailuo) + ¥0.30(Seedance) + ¥0.04(Veo) = ¥1.02

---

## 一、低成本 I2V 模型对比实验

### 实验设计
- **关键帧**: rhart-image-n-pro T2I 生成（武士龙虾，16:9）
- **统一 Prompt**: "The samurai lobster slowly draws its glowing katana, bamboo leaves swirl in the moonlight, camera slowly pushes in, cinematic movement"
- **对比模型**: 5 个预算级 I2V 模型

### 实验结果

```
┌──────────────────────────┬─────────┬──────────┬───────────┬─────────┬──────────┬─────────┐
│ 模型                      │ 花费    │ 生成时间  │ 分辨率     │ FPS    │ 时长      │ 音频    │
├──────────────────────────┼─────────┼──────────┼───────────┼─────────┼──────────┼─────────┤
│ Wan 2.6 Flash            │ ¥0.20   │ 25s ⭐   │ 1284×716  │ 30     │ 5.0s     │ ✅ 44.1k│
│ Vidu Q3 Turbo            │ ¥0.20   │ 55s      │ 1284×716  │ 24     │ 5.0s     │ ✅ 48k  │
│ Hailuo 2.3 Standard      │ ¥0.25   │ 85s      │ 1376×768  │ 24     │ 5.9s     │ ❌      │
│ Seedance v1.5 Pro Fast   │ ¥0.30   │ 125s     │ 1280×720  │ 24     │ 5.0s     │ ✅ 44.1k│
│ Veo 3.1 Fast (rhart)     │ ¥0.04   │ 110s     │ 1280×720  │ 24     │ 8.0s ⭐  │ ✅ 48k  │
└──────────────────────────┴─────────┴──────────┴───────────┴─────────┴──────────┴─────────┘
```

### 关键发现

#### 1. Veo 3.1 Fast 是极致性价比之王
- **¥0.005/秒** — 比第二名便宜 8 倍！
- 8 秒输出（其他模型 5 秒），自带音频
- 缺点：生成较慢（110s），画质略逊于 Pro 版
- **最佳场景**: 批量内容生产、原型快速验证、低预算项目

#### 2. Wan 2.6 Flash 是速度之王
- **25 秒生成** — 比最慢的快 5 倍
- 30fps（其他模型 24fps），文件最大（6.5MB）
- 画面细节丰富，运动流畅
- **最佳场景**: 实时预览、快速迭代、需要高帧率的场景

#### 3. Hailuo 2.3 Standard 分辨率最高但无音频
- 1376×768（比其他高约 7%）
- 无音频输出——需后期配音
- **最佳场景**: 需要纯画面质量、后期自行配音的项目

#### 4. 成本梯度
```
Veo 3.1 Fast:    ¥0.005/s  ████████████████████  极低
Wan 2.6 Flash:   ¥0.040/s  ██████████████        低
Vidu Q3 Turbo:   ¥0.040/s  ██████████████        低
Hailuo 2.3 Std:  ¥0.043/s  █████████████         低
Seedance Fast:   ¥0.060/s  ████████████          低偏中
```

---

## 二、ComfyUI Kling Partner Node 完整架构分析

### 2.1 源码规模与节点清单

**文件**: `comfy_api_nodes/nodes_kling.py` (136KB)  
**API 定义**: `comfy_api_nodes/apis/kling.py` (5.7KB)  
**节点总数**: 30 个 ComfyNode 类

```
┌─────────────────────────────────────┬──────────────────────────────┬───────────┐
│ 节点类名                             │ 显示名                       │ 功能类别   │
├─────────────────────────────────────┼──────────────────────────────┼───────────┤
│ KlingCameraControls                 │ Camera Controls              │ 工具节点   │
│ KlingTextToVideoNode                │ Text to Video                │ T2V       │
│ OmniProTextToVideoNode              │ 3.0 Omni Text to Video       │ T2V       │
│ OmniProFirstLastFrameNode           │ 3.0 Omni FLF to Video        │ I2V/FLF   │
│ OmniProImageToVideoNode             │ 3.0 Omni Image to Video      │ I2V       │
│ OmniProVideoToVideoNode             │ 3.0 Omni Video to Video      │ V2V       │
│ OmniProEditVideoNode                │ 3.0 Omni Edit Video          │ Video Edit│
│ OmniProImageNode                    │ 3.0 Omni Image               │ T2I       │
│ KlingCameraControlT2VNode           │ Camera Control T2V           │ T2V       │
│ KlingImage2VideoNode                │ Image to Video               │ I2V       │
│ KlingCameraControlI2VNode           │ Camera Control I2V           │ I2V       │
│ KlingStartEndFrameNode              │ Start End Frame              │ FLF       │
│ KlingVideoExtendNode                │ Video Extend                 │ Extend    │
│ KlingDualCharacterVideoEffectNode   │ Dual Character Effect        │ Effects   │
│ KlingSingleImageVideoEffectNode     │ Single Image Effect          │ Effects   │
│ KlingLipSyncAudioToVideoNode        │ Lip Sync with Audio          │ LipSync   │
│ KlingLipSyncTextToVideoNode         │ Lip Sync with Text           │ LipSync   │
│ KlingVirtualTryOnNode               │ Virtual Try On               │ Image     │
│ KlingImageGenerationNode            │ Image Generation             │ T2I       │
│ TextToVideoWithAudio                │ 2.6 T2V with Audio           │ T2V+Audio │
│ ImageToVideoWithAudio               │ 2.6 I2V with Audio           │ I2V+Audio │
│ MotionControl                       │ Motion Control               │ Motion    │
│ KlingVideoNode                      │ 3.0 Video                    │ T2V/I2V   │
│ KlingFirstLastFrameNode             │ 3.0 First Last Frame         │ FLF       │
│ KlingAvatarNode                     │ Avatar 2.0                   │ Avatar    │
└─────────────────────────────────────┴──────────────────────────────┴───────────┘
```

### 2.2 核心架构模式

#### 统一异步执行流
```
sync_op(create task) → poll_op(check status) → download result
```

所有节点遵循相同的三步模式：
1. **sync_op**: 同步发起任务（POST 到 `/proxy/kling/v1/...`）
2. **poll_op**: 轮询任务状态直到完成（带 estimated_duration 和 status_extractor）
3. **download**: 下载结果（`download_url_to_video_output` 或 `download_url_to_image_tensor`）

#### 关键设计决策

**1. Proxy 路由**: 所有 API 调用通过 `/proxy/kling/v1/...` 路由
- 不直接调用 Kling API
- ComfyUI 服务器做代理和认证
- 计费通过 `comfy.org` 账户系统

**2. 统一验证层**:
```python
validate_prompts()          # 长度检查
validate_input_image()      # 分辨率 ≥ 300x300, 宽高比 1:2.5 ~ 2.5:1
validate_video_dimensions() # 视频尺寸范围
validate_video_duration()   # 视频时长范围
validate_audio_duration()   # 音频时长范围
```

**3. 价格徽章系统** (PriceBadge):
```python
price_badge=IO.PriceBadge(
    depends_on=IO.PriceBadgeDepends(widgets=["duration", "generate_audio"]),
    expr="""{"type":"usd","usd": 0.07 * widgets.duration * (widgets.generate_audio ? 2 : 1)}"""
)
```
用 JSONata 表达式实时计算价格，显示在 UI 上。

### 2.3 Kling 2.6 Audio 集成架构

**关键发现**: Kling 2.6 是首个支持 `sound` 参数的模型系列

```python
# TextToVideoWithAudioRequest / ImageToVideoWithAudioRequest
class TextToVideoWithAudioRequest(BaseModel):
    model_name: str       # "kling-v2-6"
    sound: str            # "on" 或 "off" — 关键字段！
    multi_shot: bool      # 支持分镜
    multi_prompt: list    # 多段提示词
```

**音频生成开关**:
- `sound="on"`: 模型自动生成匹配画面的音效/配乐
- `sound="off"`: 仅生成无声视频
- 成本翻倍：开启音频 = 基础价 × 2

**与 Kling 3.0 Omni 的区别**:
- V2.6 使用独立的 `TextToVideoWithAudio` / `ImageToVideoWithAudio` 节点
- V3.0 Omni 在统一的 `OmniPro*` 节点中集成 `sound` 参数
- V3.0 支持更多高级功能（Storyboard、多镜头、OmniPro 统一入口）

### 2.4 LipSync 节点深度

**两种模式**:

| 模式 | 节点 | 输入 | 价格 |
|------|------|------|------|
| Audio → LipSync | KlingLipSyncAudioToVideoNode | 视频 + 音频文件 | ~$0.10 |
| Text → LipSync | KlingLipSyncTextToVideoNode | 视频 + 文本 + 语音选择 | ~$0.10 |

**Audio 模式流程**:
```
Video Upload → audio_url Upload → Kling LipSync API → Poll → Download
```

**Text 模式流程**:
```
Video Upload → TTS(voice_id + text) → Kling LipSync API → Poll → Download
```

**语音库**: 26 个英文 + 31 个中文语音角色
- 支持语速调节（0.8~2.0）
- 内建方言（东北、重庆、四川、潮汕、台湾、西安、天津）

### 2.5 Avatar 2.0 节点

**功能**: 从单张照片 + 音频生成"数字人"说话视频

```python
# API 路径: /proxy/kling/v1/videos/avatar/image2video
class KlingAvatarRequest(BaseModel):
    image: str       # base64 图片
    sound_file: str  # 音频 URL
    prompt: str      # 可选：控制表情、动作、镜头
    mode: str        # "std" 或 "pro"
```

**关键约束**:
- 图片：≥ 300×300px，宽高比 1:2.5 ~ 2.5:1
- 音频：2~300 秒
- 价格：std $0.056/秒，pro $0.112/秒
- 轮询上限：800 次（max_poll_attempts=800），因为长音频可能需要很长处理时间

### 2.6 MotionControl 节点

**功能**: 用参考视频驱动静态图片中的角色运动

```python
class MotionControlRequest(BaseModel):
    prompt: str                  # 文本提示
    image_url: str              # 角色参考图
    video_url: str              # 运动参考视频
    keep_original_sound: str    # "yes"/"no"
    character_orientation: str  # "video" 或 "image"
    mode: str                   # "pro"/"std"
    model_name: str             # "kling-v3" 或 "kling-v2-6"
```

**character_orientation 区别**:
- `"video"`: 角色朝向、运动、表情、镜头全部跟随参考视频
- `"image"`: 运动/表情跟随视频，但朝向保持参考图的方向

**约束**:
- image 模式：参考视频 3~10 秒
- video 模式：参考视频 3~30 秒
- 价格：std $0.07/秒，pro $0.112/秒

### 2.7 Omni Prompt Reference 规范化

```python
def normalize_omni_prompt_references(prompt: str) -> str:
    """
    @image → <<<image_1>>>
    @image2 → <<<image_2>>>
    @video → <<<video_1>>>
    """
```

ComfyUI 提供 UX shim，让用户在 prompt 中写 `@image1`（App 语法），自动转为 API 要求的 `<<<image_1>>>`。

---

## 三、低成本视频生产管线设计

### 推荐管线（成本优先）

```
Step 1: rhart-image-n-pro/text-to-image (¥0.03)
    ↓ 生成高质量关键帧
Step 2: rhart-video-v3.1-fast/image-to-video (¥0.04)  
    ↓ 8秒视频含音频，极致性价比
Step 3: [可选] topazlabs/image-upscale-standard-v2 放大关键帧
    ↓
Total: ¥0.07 — 一套完整的 T2I→I2V 管线
```

### 推荐管线（速度优先）

```
Step 1: rhart-image-n-pro/text-to-image (¥0.03, ~25s)
    ↓
Step 2: alibaba/wan-2.6/image-to-video-flash (¥0.20, ~25s)
    ↓ 30fps 高帧率，自带音频
Total: ¥0.23 / ~50s 端到端
```

### 推荐管线（质量优先，仍然低成本）

```
Step 1: rhart-image-n-pro/text-to-image (¥0.03)
    ↓
Step 2: seedance-v1.5-pro/image-to-video (标准版 ¥0.56)
    ↓ Seedance Pro 画质更好
Step 3: Kling LipSync Text (~$0.10) 如需口播
    ↓
Total: ¥0.59 + $0.10 = ¥1.30 左右
```

---

## 四、ComfyUI 工作流 JSON 产出

1. **budget-video-pipeline.json** — 完整 T2I→I2V→LipSync 生产管线
2. **budget-i2v-comparison.json** — 五模型并行对比模板（含详细 metadata）

---

## 五、核心经验总结

### 技术洞察
1. **Kling Partner Node 是标准模板** — 所有 30 个节点都遵循 sync_op→poll_op→download 模式，这是 ComfyUI API Node 的黄金范式
2. **Price Badge 用 JSONata** — 实时计算价格，依赖 widget 值动态变化
3. **Kling 2.6 是音频分水岭** — V2.6 引入 `sound` 参数，V3.0 Omni 继承并统一
4. **Avatar 2.0 max_poll=800** — 长音频场景需要更多轮询，这是生产级考量

### 成本洞察
1. **Veo 3.1 Fast = ¥0.005/秒**，这是目前测试过的所有模型中最便宜的
2. **完整 T2I→I2V 管线可以做到 ¥0.07**（关键帧 + 8秒视频含音频）
3. **Wan 2.6 Flash 25 秒生成** = 近实时预览，适合交互式工作流
4. **音频能力已成标配** — 5 个预算模型中 4 个自带音频

### RunningHub API 注意事项
- 需要 `imageUrl` 字段的端点必须用 `--image` 参数（自动上传 CDN）
- `inputImage` 已过时，RunningHub 统一用 `imageUrl`
- 不同端点的参数命名不一致（resolution/aspectRatio/duration 格式各异）
