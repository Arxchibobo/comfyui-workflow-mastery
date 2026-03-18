# ComfyUI 知识体系 — 目录索引

> 目标：针对任意需求，能快速返回工作流 JSON + 运行方式 + 设计原理

## 📂 目录结构

```
comfyui-learning/
├── knowledge-graph/        # 🧠 知识图谱
│   ├── INDEX.md            # 总索引（节点→能力→工作流 映射）
│   ├── nodes.md            # 节点百科（每个核心节点的输入/输出/用途）
│   ├── data-types.md       # 数据类型关系图
│   ├── model-architectures.md  # SD1.5/SDXL/SD3/Flux 架构对比
│   └── sampler-guide.md    # 采样器选择决策树
│
├── error-book/             # 📕 错题集
│   ├── INDEX.md            # 错误分类索引
│   └── YYYY-MM-DD-*.md     # 每个错误：现象→原因→解决→教训
│
├── knowledge-base/         # 📚 知识库
│   ├── sd-algorithm.md     # SD 算法原理精华
│   ├── conditioning.md     # 条件控制技术大全
│   ├── training.md         # 模型训练（LoRA/DreamBooth/TI）
│   ├── optimization.md     # 性能优化
│   └── custom-nodes.md     # 自定义节点开发
│
├── sample-workflows/       # 📋 样本工作流（经过验证的标准工作流）
│   ├── INDEX.md            # 需求→工作流 快速查找表
│   ├── basic/              # 基础工作流
│   │   ├── text2img.json
│   │   ├── img2img.json
│   │   └── inpaint.json
│   ├── controlnet/         # ControlNet 系列
│   ├── lora/               # LoRA 相关
│   ├── video/              # 视频生成
│   └── advanced/           # 高级组合工作流
│
├── refactored-workflows/   # 🔧 重构工作流（优化过的精简版）
│   ├── INDEX.md            # 重构记录：原始→优化→改了什么→为什么
│   └── *.json
│
├── notes/                  # 📝 每日学习笔记
│   └── dayNN-*.md
│
├── experiments/            # 🧪 实验记录和生成的图片
│
└── STUDY_PLAN.md           # 学习计划
```

## 🎯 最终交付标准

1. **需求→工作流** 秒级响应：给定需求描述，立即返回对应工作流 JSON
2. **工作流→原理** 能解释：每个节点为什么在这里，数据怎么流动
3. **报错→修复** 自主排查：遇到错误查错题集 + 知识库，自己解决
4. **质量优先** 精简有序：只保留验证过的最佳实践，不堆垃圾
