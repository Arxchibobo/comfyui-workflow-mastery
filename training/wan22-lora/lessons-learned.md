# Lessons Learned — Wan 2.2 LoRA Training

实践中踩过的坑和积累的经验。持续更新。

---

## 🔴 Critical Mistakes

### 1. 数据集混合多种舞蹈风格
**日期**: 2026-03-23  
**问题**: 初始 35 clips 包含 hip-hop、amapiano、contemporary 等多种风格混合  
**后果**: 模型无法收敛到一个一致的运动模式  
**修复**: 重新收集数据，聚焦**单一动作类型**  
**教训**: "一个品类，一个动作，动作结构基本一致" → 这是 LoRA 训练的第一原则

### 2. HuggingFace Token 未配置导致模型下载失败
**日期**: 2026-03-23  
**问题**: Wan 2.2 14B 模型需要 HF 认证才能下载，训练环境缺少 HF_TOKEN  
**修复**: 配置 HF_TOKEN 或使用 `HF_HUB_OFFLINE=1`（如果模型已预装）  
**教训**: 训练开始前先确认模型访问权限

### 3. SSH 被防火墙阻断
**日期**: 2026-03-23  
**问题**: AIGate 服务器 SSH 端口被网络环境屏蔽  
**修复**: 改用 HTTPS Web UI API 操作  
**教训**: 云 GPU 环境优先准备 Web API 通路，不要假设 SSH 可用

---

## 🟡 Important Learnings

### 4. workspace API 的 setContent 不可靠
**问题**: 通过 API 往 workspace setContent 创建文件，存在缓存问题  
**修复**: 先 create 再操作，或直接用终端/git 操作  
**教训**: 训练平台 API 有坑，复杂文件操作走 git/terminal

### 5. 视频模型训练的性价比排序
通过实际对比得出的结论：
- **Seedance 1.5 Pro**: ¥0.30/次 — 性价比最高
- **Kling 3.0 Pro**: ¥0.75/次 — 质量最好
- **rhart-video-s**: ¥0.10/次 — 最便宜但质量一般
- **Wan 2.2 本地 LoRA**: 前期投入大，长期边际成本趋零

### 6. ComfyUI 节点调用云端模型
- 通过 API 节点可以在 ComfyUI 中调用 Kling、Seedance、Veo 3.1 等
- 本地跑 LTX-2 + AnimateDiff 做快速原型
- 正式出片用云端 API（质量更高）

---

## 🟢 Best Practices

### 数据收集
- 用 yt-dlp 下载 TikTok/Instagram 源视频
- ffmpeg 标准化：480p、16fps、4秒段
- 人工逐条审核（不要偷懒跳过）

### Caption 编写
- 必须包含 trigger word
- 描述具体动作方向和节奏，不要只写 "person dancing"
- 每个 caption 略有不同但结构一致

### 训练监控
- 每 500 步看一次 sample 输出
- 关注：trigger word 是否生效、动作是否连贯、是否过拟合
- 过拟合信号：动作过于机械/重复

### 环境准备 Checklist
- [ ] GPU 驱动 + CUDA 版本确认
- [ ] Python 环境 + ai-toolkit 安装
- [ ] HF_TOKEN 配置并测试
- [ ] 模型下载或 HF_HUB_OFFLINE 设置
- [ ] 数据集准备完毕（视频 + caption）
- [ ] 训练 config 参数确认
- [ ] 磁盘空间充足（模型 ~28GB + checkpoints）

---

*Last updated: 2026-03-23*
