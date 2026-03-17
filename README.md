# ComfyUI Workflow Mastery Skill

🎨 **ComfyUI 工作流大师** — AI Agent Skill for authoring and executing ComfyUI workflows from natural language.

## Features

- 🧠 **Deep Understanding**: Not just template-matching — truly understands node connections, data flow, and workflow architecture
- 🔧 **From-Scratch Compilation**: Can build any workflow from zero based on understanding of 206+ node types
- 🔗 **Technique Fusion**: Freely combines ControlNet + LoRA + Upscale + Inpaint in novel topologies
- 🚀 **RunningHub Integration**: Auto-compiles → uploads → executes → returns results
- 📚 **Comprehensive Knowledge Base**: 6 reference docs covering nodes, patterns, models, and real-world workflows

## Supported Workflows

| Pipeline | Description | Nodes |
|----------|------------|-------|
| text2img | Text to Image | 7 |
| img2img | Image to Image (style transfer) | 8 |
| text2img+lora | Text to Image with LoRA style | 8 |
| controlnet | Spatial control (Canny/Depth/Pose) | 11 |
| multi_controlnet | Multiple ControlNet mixing | 15 |
| inpaint | Selective region regeneration | 8 |
| outpaint | Canvas extension | 9 |
| upscale | Super-resolution (4x) | 4 |
| flux | Flux-style fast generation | 7 |
| wan_t2v | Text to Video (Wan2.x) | 9 |
| wan_i2v | Image to Video (Wan2.x) | 11 |
| fusion | Free combination of techniques | 10-20 |

## Architecture

```
User Request (natural language)
       ↓
  Skill Decision Tree
       ↓
  Workflow Compiler (scripts/workflow_compiler.py)
       ↓
  API Format JSON
       ↓
  RunningHub API (upload → create → poll → outputs)
       ↓
  Result Image/Video → User
```

## Knowledge Base

| File | Content |
|------|---------|
| `deep-learning-guide.md` | Core concepts, workflow types, advanced techniques |
| `workflow-patterns.md` | 9 topology patterns with full JSON examples |
| `node-reference.md` | 206+ node types with parameters and best practices |
| `model-compatibility.md` | SD1.5 vs SDXL vs Flux selection guide |
| `runninghub-workflows.md` | Analysis of 13 real RunningHub workflows |

## Verification

All workflow types verified with from-scratch compilation and execution on RunningHub:

- ✅ Text2Img (30s)
- ✅ Img2Img (12s)
- ✅ LoRA (12s)
- ✅ ControlNet (12s)
- ✅ Inpaint (14s)
- ✅ Upscale (12s)
- ✅ Fusion: ControlNet + LoRA + Upscale (11s)
- ✅ Flux-style (12s)

## Usage

### As OpenClaw Skill
Place in your skills directory and the agent will auto-trigger on image/video generation requests.

### Standalone
```bash
python3 scripts/workflow_compiler.py \
  --pipeline text2img \
  --prompt "a majestic lion at sunset" \
  --width 1024 --height 1024 \
  --steps 25 --cfg 7.5
```

## Requirements

- Python 3.8+
- RunningHub API key (`RUNNINGHUB_API_KEY`)
- RunningHub workspace (`RUNNINGHUB_WORKSPACE_ID`)
- `curl` for API calls

## License

MIT
