# Video Evaluation Guide - Phase 2

This guide covers the evaluation pipeline for analyzing ingested videos.

## Overview

The evaluation pipeline is separate from ingestion. Videos must first be ingested (Phase 1) before they can be evaluated.

**Current Status**: Content Rating rubric is fully implemented as a vertical slice. Other rubrics coming soon.

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
python3 pipeline/evaluate_video.py --video-id VIDEO_ID --rubric content_rating

# With custom settings
python3 pipeline/evaluate_video.py \
  --video-id MyClip \
  --rubric content_rating \
  --sampling even \
  --max-frames 50
```

## Available Rubrics

### Content Rating (Kijkwijzer-based)
**Status**: ✅ Implemented

Evaluates age-appropriateness and content safety:
- Age classification (All Ages, 2+, 5+, 7+, 9+)
- Content descriptors (Violence, Fear, Sexual Content, Discrimination, Drugs, Language)
- Safety warnings and parental guidance
- Traffic-light rating (Green/Yellow/Red)

**Use Case**: Determine if video is safe and appropriate for target age group

### Coming Soon

- **Educational** - Pedagogical effectiveness
- **Production** - Technical quality
- **Creative** - Script and engagement
- **Creative Production** - Measurable metrics (WPM, cuts/min, color analysis)

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
  "rubric": "content_rating",
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
│   ├── rubric_content_rating.py    # Content rating rubric
│   ├── rubric_educational.py       # Educational rubric (coming soon)
│   ├── rubric_production.py        # Production rubric (coming soon)
│   ├── rubric_creative.py          # Creative rubric (coming soon)
│   └── rubric_creative_production.py  # Metrics rubric (coming soon)
└── data/
    └── <video_id>/
        ├── source.mp4
        ├── metadata.json
        ├── transcript.txt
        ├── frames/
        └── evaluations/            # Evaluation results saved here
            └── claude-cli_content_rating_20250110_143000.json
```

## CLI Examples

### Basic Evaluation
```bash
python3 pipeline/evaluate_video.py --video-id MyClip --rubric content_rating
```

### With Custom Settings
```bash
python3 pipeline/evaluate_video.py \
  --video-id dQw4w9WgXcQ \
  --rubric content_rating \
  --sampling even \
  --max-frames 50 \
  --timeout 900
```

### Batch Processing (future)
```bash
# Evaluate all ingested videos
for video_id in data/*/; do
  python3 pipeline/evaluate_video.py --video-id $(basename $video_id) --rubric content_rating
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
1. Add remaining rubrics (Educational, Production, Creative, Creative Production)
2. Add Ollama evaluators for local comparison
3. Add comparison tools to analyze multiple evaluations
4. Add report generation with templates

## Support

For issues:
1. Check this guide
2. Review console logs
3. Check evaluation JSON for errors
4. Verify Claude CLI is working: `claude --version`
