# ComfyUI Workflow Mastery

An OpenClaw skill and learning repository for authoring and executing ComfyUI workflows from natural language. Covers the full stack: SD theory, node architecture, workflow compilation, RunningHub API integration, and LoRA fine-tuning.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Workflows](https://img.shields.io/badge/verified%20workflows-52-brightgreen.svg)
![Node Types](https://img.shields.io/badge/node%20types-206%2B-orange.svg)
![Pipelines](https://img.shields.io/badge/pipeline%20types-12-blue.svg)

---

## Overview

**ComfyUI Workflow Mastery** is a production-grade OpenClaw skill combined with an extensive knowledge base for mastering [ComfyUI](https://github.com/comfyanonymous/ComfyUI) — a node-based UI for Stable Diffusion and related AI image/video generation models.

The skill accepts natural language generation requests, compiles them into ComfyUI API-format JSON workflows, executes them via the RunningHub API, and returns image or video results. Behind the skill is a structured curriculum of 51 daily learning sessions (~29,000 lines of notes), 52 verified workflow examples, a 206-node reference database, and hands-on LoRA training guides.

**Why it exists:** To push past template-matching and build genuine understanding of ComfyUI's node graph — enabling arbitrary workflow compositions that no fixed template library could cover.

---

## Features

- **From-scratch workflow compilation** — translates natural language into ComfyUI API JSON using deep understanding of 206+ node types, not simple template lookups
- **12 pipeline types** — text2img, img2img, LoRA, ControlNet, multi-ControlNet, inpaint, outpaint, upscale, Flux, Wan T2V, Wan I2V, and free-form fusion
- **Technique fusion** — freely combines ControlNet + LoRA + Upscale + Inpaint in novel topologies; 52/52 verified across 4 test rounds
- **RunningHub integration** — auto-compiles → uploads → executes → polls → returns results
- **Comprehensive knowledge base** — 9 topology pattern docs, 206-node reference, model compatibility guide, 13 real-world workflow analyses
- **LoRA training knowledge** — end-to-end Wan 2.2 LoRA fine-tuning guides including dataset prep, config reference, and lessons learned
- **OpenClaw compatible** — auto-triggers on image/video generation requests when placed in your skills directory

---

## Supported Pipelines

| Pipeline | Description | Nodes | Verified |
|---|---|---|---|
| `text2img` | Text to image | 7 | ✅ ~30s |
| `img2img` | Image stylization / style transfer | 8 | ✅ ~12s |
| `text2img+lora` | Text to image with LoRA style | 8 | ✅ ~12s |
| `controlnet` | Spatial control (Canny / Depth / Pose) | 11 | ✅ ~12s |
| `multi_controlnet` | Multiple ControlNet mixing | 15 | ✅ |
| `inpaint` | Selective region regeneration | 8 | ✅ ~14s |
| `outpaint` | Canvas extension | 9 | ✅ |
| `upscale` | 4× super-resolution | 4 | ✅ ~12s |
| `flux` | Flux-style fast generation (cfg=1) | 7 | ✅ ~12s |
| `wan_t2v` | Text to video (Wan 2.x) | 9 | ✅ ~11s |
| `wan_i2v` | Image to video (Wan 2.x) | 11 | ✅ ~11s |
| `fusion` | Free combination of multiple techniques | 10–20 | ✅ 52/52 |

---

## Architecture

```
User Request (natural language)
        ↓
   Skill Decision Tree (SKILL.md)
        ↓
   Workflow Compiler  (scripts/workflow_compiler.py)
        ↓
   API-format JSON
        ↓
   RunningHub API  (upload → create task → poll → outputs)
        ↓
   Result image / video → User
```

---

## Usage

### As an OpenClaw Skill

Place the repository in your OpenClaw skills directory. The skill auto-triggers on image and video generation requests (keywords: `comfyui`, `generate image`, `draw`, `style transfer`, `text to video`, etc.).

Refer to `SKILL.md` for the full trigger list, decision tree, and execution guide.

### Standalone Compiler

```bash
python3 scripts/workflow_compiler.py \
  --pipeline text2img \
  --prompt "a majestic lion at sunset" \
  --width 1024 --height 1024 \
  --steps 25 --cfg 7.5
```

```bash
python3 scripts/workflow_compiler.py \
  --pipeline controlnet \
  --prompt "anime portrait" \
  --control_type canny \
  --image_path input.png
```

```bash
python3 scripts/workflow_compiler.py \
  --pipeline wan_t2v \
  --prompt "a cat walking through autumn leaves"
```

The compiler outputs a ComfyUI API-format JSON file ready for direct submission to any ComfyUI instance or the RunningHub API.

---

## Knowledge Base

Located in `knowledge-base/`:

| File | Description |
|---|---|
| `deep-learning-guide.md` | SD algorithm theory (DDPM/LDM), KSampler parameters, sampler strategies |
| `workflow-patterns.md` | 9 topology patterns with full JSON examples |
| `node-reference.md` | 206+ node types with inputs, outputs, and best practices |
| `model-compatibility.md` | SD 1.5 vs SDXL vs Flux selection guide |
| `runninghub-workflows.md` | Analysis of 13 real RunningHub workflows |
| `50-pipelines-knowledge.md` | Extended pipeline documentation |
| `model-catalog.md` | Model selection reference |

---

## Sample Workflows

Located in `sample-workflows/` and `learning/sample-workflows/`:

- **Basic** — `text2img.json`, `img2img.json`, `inpaint.json`
- **ControlNet** — Canny, Depth, Pose, Tile, IP-Adapter, Multi-ControlNet variants
- **LoRA** — single and multi-LoRA compositions
- **SDXL** — SDXL base + refiner pipeline
- **Video** — Wan 2.2 T2V/I2V, LTX-2, AnimateDiff
- **Experiments** — sampler comparisons, scheduler matrices, quality curves
- **Post-graduation** — cutting-edge models and multimodal pipelines

---

## Learning Curriculum

Located in `learning/notes/` — 51 daily session files (~29,000 lines):

| Phase | Days | Topics |
|---|---|---|
| Foundation | 1–10 | SD theory, latent space, sampling algorithms, ComfyUI architecture, basic workflows |
| Core techniques | 11–20 | LoRA, ControlNet, SDXL Refiner, video generation, performance tuning |
| Advanced | 21–36 | Upscaling, character consistency, audio synthesis, 3D generation, complex fusions |
| Post-graduation | PG 1–20 | Wan 2.2, new model families, multimodal pipelines, emotion TTS, fast inference |

---

## Training Knowledge

Located in `training/wan22-lora/`:

| File | Description |
|---|---|
| `training-guide.md` | End-to-end Wan 2.2 LoRA fine-tuning workflow |
| `config-reference.yaml` | Annotated training configuration with hyperparameters |
| `dataset-preparation.md` | Data quality rules and preparation pipeline |
| `dance-trends-research.md` | TikTok/Instagram trend analysis for dataset curation |
| `lessons-learned.md` | Documented mistakes and best practices |

---

## Requirements

- Python 3.8+
- `RUNNINGHUB_API_KEY` environment variable
- `RUNNINGHUB_WORKSPACE_ID` environment variable
- `curl` (for RunningHub API calls)

No additional Python packages are required beyond the standard library for the core compiler. See individual scripts for any optional dependencies.

---

## Repository Structure

```
comfyui-workflow-mastery/
├── scripts/                  # Python tools
│   ├── workflow_compiler.py  # Core compiler (206 node types, 12 pipelines)
│   ├── comfyui_workflow.py   # Executor & template manager
│   └── workflow_composer.py  # Composition utilities
├── knowledge-base/           # Reference documentation
├── sample-workflows/         # Verified workflow JSON files
├── learning/                 # 51-session curriculum & notes
│   └── notes/                # Daily lesson files
├── training/wan22-lora/      # LoRA fine-tuning guides
├── data/
│   ├── node_database.json    # 206+ node type definitions
│   └── templates.json        # 5 official pipeline templates
├── SKILL.md                  # OpenClaw skill guide & decision tree
└── LEARNING_STATUS.md        # Progress tracking
```

---

## License

MIT
