# Wan 2.2 T2V 14B — LoRA Training Guide

## Overview
Train a LoRA adapter on Wan 2.2 Text-to-Video 14B model for specific motion/dance styles using ostris/ai-toolkit.

## Prerequisites
- **GPU**: 24GB+ VRAM (tested on 4090 48GB DDR5)
- **Framework**: [ostris/ai-toolkit](https://github.com/ostris/ai-toolkit)
- **Model**: `Wan-AI/Wan2.2-T2V-14B` (requires HuggingFace token)
- **Python**: 3.10+, CUDA 12.x

## Architecture Decisions

### Why LoRA (not full fine-tune)?
- 14B model is too large for full fine-tune on consumer GPUs
- LoRA rank 16 is sweet spot for motion learning with limited data
- NF4 quantization enables training on 24GB VRAM

### Key Parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| LoRA rank | 16 | Balance between capacity and VRAM |
| LoRA alpha | 16 | alpha=rank → effective lr multiplier = 1 |
| Learning rate | 2e-4 | Standard for video LoRA |
| Optimizer | AdamW 8-bit | Memory efficient |
| LR Scheduler | Cosine | Smooth decay prevents overfit |
| Batch size | 1 | VRAM constraint |
| Grad accum | 1 | Can increase to simulate larger batch |
| Steps | 3000 | 35 clips × ~85 steps/epoch |
| Quantize | NF4 | Required for 24GB VRAM |
| Timestep | Sigmoid balanced | Best for person/character content |

### Low VRAM Strategy
```yaml
low_vram: true
quantize: true
quantize_type: "nf4"
cache_text_encoders: true  # Offload text encoders after caching
multistage:
  stages: "both"           # Train high and low noise alternately
  switch_every: 15         # Switch every 15 steps (low VRAM friendly)
```

## Dataset Preparation

### Video Clips
- **Format**: MP4, 480p resolution (save VRAM during training)
- **Duration**: ~4 seconds at 16fps → 41 frames (40+1)
- **Quantity**: 30-50 high quality clips minimum
- **Content**: Single consistent action/style per LoRA

### ⚠️ Critical: Data Quality > Quantity
**One category, one action, structurally consistent movements.**

❌ Bad: 35 clips mixing hip-hop, ballet, amapiano, contemporary  
✅ Good: 35 clips of the same "Call Back" choreo from different angles/people

Mixing styles confuses the model — it learns noise instead of a coherent motion pattern.

### Captions
- Use trigger word prefix: `dance_trend`
- Describe the motion, not just "person dancing"
- Include style cues: "smooth arm movements", "rhythmic body isolation"
- Example: `dance_trend a person performing smooth Call Back choreography, fluid arm waves, hypnotic movement, good lighting`

### Clip Preparation Pipeline
```bash
# 1. Download source videos (TikTok/Instagram)
# 2. Trim to 4-second segments with consistent motion
ffmpeg -i source.mp4 -ss 00:02 -t 4 -c:v libx264 -vf scale=480:-2 clip.mp4

# 3. Generate captions (.txt files with same name as video)
# 4. Review: discard clips with scene changes, text overlays, or inconsistent motion
```

## Training Execution

### Environment Setup
```bash
git clone https://github.com/ostris/ai-toolkit
cd ai-toolkit
pip install -r requirements.txt

# HuggingFace token for model download
export HF_TOKEN=<your-token>
# Or set HF_HUB_OFFLINE=1 if model is pre-downloaded
```

### Run Training
```bash
python run.py configs/wan22_dance_lora.yaml
```

### Monitoring
- Samples generated every 500 steps
- Checkpoints saved every 500 steps (keep last 3)
- Watch for: motion coherence, trigger word response, overfitting

## Inference (ComfyUI)
Load the trained LoRA in ComfyUI with Wan 2.2 workflow:
1. Place `.safetensors` in `ComfyUI/models/loras/`
2. Use WanVideoLoraSelect node
3. Prompt must include trigger word: `dance_trend`
4. Recommended: 480×832, 41 frames, 16fps

## Common Issues

### Model download fails
- Need HuggingFace token with access to Wan-AI models
- If pre-downloaded: set `HF_HUB_OFFLINE=1`

### OOM during training
- Reduce `num_frames` (try 25 instead of 41)
- Ensure `cache_text_encoders: true`
- Ensure `quantize: true` with `nf4`
- Reduce resolution to 384

### Motion not learned
- Check dataset consistency (single action type!)
- Increase steps (try 5000)
- Check captions include trigger word
- Review sample outputs at each checkpoint

### Overfitting
- Motion becomes robotic/repetitive
- Reduce steps or increase dataset size
- Try lower learning rate (1e-4)
