# Video Evaluation Guide - Phase 2

This guide covers the evaluation pipeline for analyzing ingested videos.

## Overview

The evaluation pipeline is separate from ingestion. Videos must first be ingested (Phase 1) before they can be evaluated.

**Current Status**: Content Safety rubric is fully implemented as a vertical slice. Other rubrics coming soon.

## Quick Start

### Option 1: Streamlit UI (Recommended)

```bash
cd video-evaluator
python3 -m streamlit run evaluate_ui.py
```

Then:
1. Select an ingested video from the dropdown
2. Configure evaluation settings (rubric, model, frame sampling)
3. Click "Run Evaluation"
4. View results and download JSON

### Option 2: Command Line

```bash
# Evaluate a video
python3 pipeline/evaluate_video.py --video-id VIDEO_ID --rubric content_safety

# With custom settings
python3 pipeline/evaluate_video.py \
  --video-id MyClip \
  --rubric content_safety \
  --sampling even \
  --max-frames 50
```

## Available Rubrics

### Content Safety (Kijkwijzer-based)
**Status**: ✅ Implemented

Evaluates age-appropriateness and universal safety concerns:
- Age classification (All Ages, 2+, 5+, 7+, 9+)
- Content descriptors (Violence, Fear, Sexual Content, Discrimination, Drugs, Language)
- Safety warnings and parental guidance
- Detailed safety analysis with timestamps
- Focuses on universal safety concerns only

**Use Case**: Determine if video is safe and appropriate for target age group

### AI Quality & Fidelity
**Status**: ✅ Implemented

Evaluates AI-generated content quality:
- AI artifact severity rating (0-3: None, Minor, Noticeable, Extreme)
- Artifact domains (Anatomy, Physics, Visual, Narrative, Audio, Instructional)
- Cognitive impact assessment (Confusion, Uncanny/Disturbing, Misinformation risks)
- Authenticity signals detection
- Factual analysis only (no recommendations)

**Use Case**: Assess quality of AI-generated videos and identify potential issues

### Values & Hot Button Topics
**Status**: 🚧 Placeholder Created

Documents values-based content for family decision-making:
- Religious/spiritual content
- Political content
- LGBTQ+ themes
- Other values-based topics (gender roles, authority, etc.)
- Non-judgmental, informational disclosure

**Use Case**: Help families make informed, values-aligned viewing decisions

### Media Ethics
**Status**: ✅ Implemented

Detects manipulative tactics and commercial pressure:
- Marketing pressure ("like and subscribe" demands)
- Attention hijacking (loud sounds, retention hooks)
- Artificial urgency (FOMO creation, cliffhangers)
- Parasocial manipulation (inappropriate intimacy)
- Commercial intent (product placement, purchase encouragement)
- Platform gaming (clickbait, algorithm optimization)
- Reward loops and emotional manipulation
- Factual documentation only (no recommendations)

**Use Case**: Identify ethical concerns regarding manipulation and commercial exploitation

### Coming Soon

- **Educational Objectives** - Learning objectives present and opportunities missed
- **Production Quality** - Technical quality assessment
- **Engagement** - Script and engagement analysis

## Evaluator Configuration

### Frame Sampling Strategies

- **even** (default): Sample frames evenly across video
- **all**: Send all frames (use for short videos or detailed analysis)
- **first_n**: First N frames only
- **last_n**: Last N frames only

### Max Frames

- Default: 30 frames
- Range: 10-100 frames
- More frames = more detailed analysis, longer processing time

### Model Selection

- **claude-sonnet-4-20250514** (default): Most capable Claude model

## Output

Evaluations are saved to:
```
data/<video_id>/evaluations/<evaluator>_<rubric>_<timestamp>.json
```

### JSON Structure

```json
{
  "video_id": "MyClip",
  "evaluator": "claude-cli",
  "rubric": "content_safety",
  "model": "claude-sonnet-4-20250514",
  "timestamp": "2025-01-10T14:30:00",
  "evaluation_markdown": "... full evaluation text ...",
  "metadata": {
    "video_metadata": {...},
    "frames_analyzed": 30,
    "total_frames_available": 90,
    "sampling_strategy": "even",
    "transcript_word_count": 245
  },
  "performance_metrics": {
    "processing_time_seconds": 145.2,
    "frames_processed": 30
  }
}
```

## Workflow

### Typical Workflow

1. **Ingest video** (Phase 1):
   ```bash
   python3 -m streamlit run app.py
   # Upload video or provide YouTube URL
   ```

2. **Evaluate video** (Phase 2):
   ```bash
   python3 -m streamlit run evaluate_ui.py
   # Select video, choose rubric, run evaluation
   ```

3. **Review results**:
   - View in UI
   - Download JSON
   - Check `data/<video_id>/evaluations/`

### Testing Different Configurations

To experiment with evaluation settings:

1. Run same video with different frame counts:
   - 10 frames (quick test)
   - 30 frames (balanced)
   - 50 frames (detailed)

2. Compare sampling strategies:
   - Even sampling across video
   - All frames (for short clips)

3. Later: Compare different evaluators/models

## File Organization

```
video-evaluator/
├── app.py                          # Phase 1: Ingestion UI
├── evaluate_ui.py                  # Phase 2: Evaluation UI
├── pipeline/
│   ├── evaluate_video.py           # CLI evaluation tool
│   └── evaluators/
│       ├── base.py                 # Abstract evaluator class
│       └── claude_evaluator.py     # Claude implementation
├── src/
│   ├── rubric_content_safety.py    # Content safety rubric (universal safety concerns)
│   ├── rubric_ai_quality.py        # AI quality & fidelity rubric
│   ├── rubric_values_topics.py     # Values & hot button topics (religion, politics, LGBTQ+)
│   ├── rubric_media_ethics.py      # Media ethics rubric (manipulation, commercial pressure)
│   ├── rubric_production_metrics.py  # Production metrics rubric (measurements only)
│   ├── rubric_educational.py       # Educational rubric (coming soon)
│   ├── rubric_production.py        # Production rubric (coming soon)
│   ├── rubric_creative.py          # Creative rubric (coming soon)
│   └── archive/                    # Deprecated rubric versions
└── data/
    └── <video_id>/
        ├── source.mp4
        ├── metadata.json
        ├── transcript.txt
        ├── frames/
        └── evaluations/            # Evaluation results saved here
            └── claude-cli_content_safety_20250110_143000.json
```

## CLI Examples

### Basic Evaluation
```bash
python3 pipeline/evaluate_video.py --video-id MyClip --rubric content_safety
```

### With Custom Settings
```bash
python3 pipeline/evaluate_video.py \
  --video-id dQw4w9WgXcQ \
  --rubric content_safety \
  --sampling even \
  --max-frames 50 \
  --timeout 900
```

### Evaluate AI Quality
```bash
python3 pipeline/evaluate_video.py --video-id MyClip --rubric ai_quality
```

### Evaluate Media Ethics
```bash
python3 pipeline/evaluate_video.py --video-id MyClip --rubric media_ethics
```

### Batch Processing (future)
```bash
# Evaluate all ingested videos
for video_id in data/*/; do
  python3 pipeline/evaluate_video.py --video-id $(basename $video_id) --rubric content_safety
done
```

## Troubleshooting

### "Video directory not found"
Make sure the video has been ingested first:
```bash
ls data/  # Check if video_id exists
```

### "Metadata not found"
The video ingestion may not have completed. Re-run Phase 1.

### "Claude CLI not found"
Ensure Claude Code CLI is installed:
```bash
claude --version
```

### Evaluation timeout
Increase timeout or reduce max frames:
```bash
python3 pipeline/evaluate_video.py --video-id MyClip --max-frames 20 --timeout 1200
```

## Performance Notes

**Mac Studio M4** (typical times for 3-minute video):

| Configuration | Processing Time |
|---------------|-----------------|
| 10 frames | ~30-45s |
| 30 frames | ~60-90s |
| 50 frames | ~90-150s |
| 100 frames | ~180-300s |

Times vary based on:
- Video length
- Transcript length
- Network latency
- Claude API load

## Next Steps

After vertical slice is validated:
1. Add remaining rubrics (Educational, Production Quality, Creative Analysis)
2. Implement Tier 2 synthesis reports (Parent Report, Creator Report, Educator Report)
3. Add Ollama evaluators for local comparison
4. Add comparison tools to analyze multiple evaluations

## Support

For issues:
1. Check this guide
2. Review console logs
3. Check evaluation JSON for errors
4. Verify Claude CLI is working: `claude --version`
