# Dataset Preparation for Wan 2.2 Video LoRA

## Golden Rules

### 1. One Category, One Action
> "一个品类，一个动作，动作结构基本一致" — bobooo

The single most important rule. A LoRA learns patterns from consistency. If your dataset has 5 different dance styles, the model learns the average of all 5 (which is nothing useful).

**Good datasets:**
- 30 clips of "Call Back" arm wave choreo
- 40 clips of amapiano leg work
- 25 clips of a single TikTok trend dance

**Bad datasets:**
- 10 hip-hop + 10 ballet + 10 contemporary + 5 random
- Clips with completely different movement structures

### 2. Quality Over Quantity
- 30 high-quality, consistent clips > 100 mixed/low-quality clips
- Every clip that doesn't match the target motion is noise, not signal

### 3. Visual Consistency Matters
- Similar lighting conditions
- Similar framing (full body preferred)
- Minimal text overlays, watermarks, effects
- Clean backgrounds preferred (but not required)

## Video Specifications

| Spec | Value | Notes |
|------|-------|-------|
| Format | MP4 (H.264) | Standard codec |
| Resolution | 480p training / 720p source | Downscale during training |
| Duration | 3-5 seconds per clip | Sweet spot for 41 frames |
| FPS | 16 fps | Wan 2.2 native rate |
| Frames | 41 (40+1) | Divisible requirements |
| Aspect | 9:16 portrait | Match TikTok/Reels format |

## Clip Processing Pipeline

### Step 1: Source Collection
```bash
# Download from TikTok/Instagram using yt-dlp
yt-dlp -o "raw/%(id)s.%(ext)s" "https://www.tiktok.com/..."
```

### Step 2: Trim & Normalize
```bash
# Trim to 4-second segment starting at 2s mark
ffmpeg -i raw/input.mp4 -ss 00:00:02 -t 4 \
  -vf "scale=480:-2" \
  -r 16 \
  -c:v libx264 -preset fast -crf 18 \
  clips/clip_001.mp4
```

### Step 3: Quality Review
Manually review each clip for:
- [ ] Consistent motion type (matches target dance)
- [ ] Clear visibility of body movement
- [ ] No scene changes within clip
- [ ] No heavy text overlays or effects
- [ ] Reasonable lighting (not too dark/blown out)
- [ ] Single person preferred (multi-person clips are harder to learn)

### Step 4: Caption Generation
Create `.txt` file with same name as video:

```
clips/clip_001.mp4
clips/clip_001.txt  ← caption file
```

Caption format:
```
{trigger_word} {detailed motion description}, {style}, {quality cues}
```

Examples:
```
dance_trend a young woman performing smooth Call Back choreography, fluid arm wave movements flowing left to right, hypnotic rhythm, indoor studio, good lighting, professional quality

dance_trend a person doing the Call Back dance trend, gentle arm undulations, relaxed body movement, TikTok style, natural lighting
```

### Caption Best Practices
- Always start with trigger word (`dance_trend`)
- Describe the actual motion (not just "dancing")
- Include direction of movement when applicable
- Mention style/mood
- Keep captions varied but structurally similar
- 1-3 sentences per caption

## Pitfalls to Avoid

| Pitfall | Why it's bad | Fix |
|---------|-------------|-----|
| Mixed dance styles | Model can't converge on a motion pattern | Curate ONE style |
| Short clips (<2s) | Not enough motion context | Use 3-5s clips |
| Heavy effects/filters | Model learns the effect, not the motion | Use clean source |
| Inconsistent framing | Close-up + full body confuses spatial learning | Standardize framing |
| Too few clips (<20) | Overfits to individual videos | Aim for 30-50 |
| Bad captions | Model won't respond to trigger word | Review all captions |

## Dataset Size Guidelines

| Clips | Expected Result |
|-------|----------------|
| <20 | Likely overfit, motion too rigid |
| 20-35 | Minimum viable, works with careful curation |
| 35-50 | Good quality, recommended range |
| 50-100 | Excellent, more variation while maintaining consistency |
| >100 | Diminishing returns (unless motion is very complex) |
