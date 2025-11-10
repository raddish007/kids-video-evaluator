# Kids Video Evaluator - MVP

A command-line tool that analyzes children's educational videos by extracting frames and transcribing audio, then uses Claude to evaluate educational quality against a comprehensive rubric.

## Overview

This tool helps you evaluate educational videos for children ages 0-8 (with primary focus on 2-5 year-olds) by:

1. **Extracting key frames** from video (1 frame every 2 seconds by default)
2. **Transcribing audio** using OpenAI's Whisper (local model)
3. **Analyzing content** with Claude's vision capabilities
4. **Generating detailed reports** with educational quality scores and actionable feedback

## Features

- **Comprehensive Evaluation Framework** based on early childhood education research
- **Multi-domain Assessment**: Literacy, Numeracy, Social-Emotional Learning, Movement, Nature/Science, Creativity
- **Content Safety Warnings**: Violence, inappropriate content, scary elements, language issues
- **Format Analysis**: Pacing, visual stimulation, audio quality, interactivity
- **Traffic-Light Rating System**: Green (recommended), Yellow (caution), Red (not recommended)
- **Parent Guidance**: Co-viewing tips, discussion questions, related activities
- **Timestamp-Specific Feedback**: Highlights key moments for discussion or concern

## Installation

### Prerequisites

- Python 3.8 or higher
- ffmpeg (for video processing)
- Claude Code CLI (for authentication)

### Install ffmpeg

On macOS with Homebrew:
```bash
brew install ffmpeg
```

### Install Python Dependencies

```bash
cd video-evaluator
pip install -r requirements.txt
```

This will install:
- `opencv-python` - Video frame extraction
- `openai-whisper` - Audio transcription
- `pillow` - Image processing
- `numpy` - Numerical operations
- `ffmpeg-python` - Video processing utilities

**Note:** The first time you run the tool, Whisper will download the model files (~1GB for the base model). This happens automatically.

## Usage

### Basic Usage

1. **Add videos to the `videos/` folder**
   ```bash
   # The videos/ folder is created automatically
   # Copy your .mp4, .mov, or other video files there
   ```

2. **Run the evaluator**
   ```bash
   python evaluate.py
   ```

3. **Find reports in `output/reports/`**
   - Individual markdown reports for each video
   - Summary report listing all evaluated videos

### Command-Line Options

```bash
# Process videos from a custom directory
python evaluate.py --videos-dir /path/to/my/videos

# Control frame sampling (send more/fewer frames to Claude)
python evaluate.py --frames-per-batch 40

# Change frame extraction interval (1 frame every N seconds)
python evaluate.py --frame-interval 3

# Use a different Whisper model (better accuracy, slower)
python evaluate.py --whisper-model medium

# Keep temporary files (frames, transcripts) after processing
python evaluate.py --keep-temp

# Combine options
python evaluate.py --videos-dir ~/Downloads/test-videos --frames-per-batch 50 --whisper-model small
```

### Whisper Model Options

Choose based on your Mac Studio M4's capabilities and desired speed/accuracy tradeoff:

| Model | Size | Speed | Accuracy | Recommended For |
|-------|------|-------|----------|-----------------|
| `tiny` | ~1GB | Fastest | Lowest | Quick testing |
| `base` | ~1GB | Fast | Good | **Default - balanced** |
| `small` | ~2GB | Moderate | Better | Higher quality |
| `medium` | ~5GB | Slow | High | Best quality |
| `large` | ~10GB | Slowest | Highest | Maximum accuracy |

**Recommendation**: Start with `base`, upgrade to `small` or `medium` if transcription quality is poor.

### Frame Sampling Strategy

The tool extracts frames at regular intervals, then samples them intelligently:

- **Default**: Extract 1 frame every 2 seconds
- **Sampling**: If >30 frames, sample evenly to stay within Claude's limits
- **Configurable**: Adjust `--frames-per-batch` to send more/fewer frames to Claude

**Examples:**
- 3-minute video: ~90 frames extracted → 30 sent to Claude (evenly sampled)
- 1-minute video: ~30 frames extracted → all 30 sent to Claude
- With `--frames-per-batch 50`: Up to 50 frames sent (better coverage for longer videos)

## Output

### Individual Video Reports

Each video gets a detailed markdown report (`output/reports/VIDEO_NAME_evaluation.md`) containing:

1. **Video Information**: Duration, frames analyzed, processing time
2. **Transcript Summary**: Language, word count, speaking pace
3. **Educational Evaluation**:
   - Age appropriateness (0-2, 2-5, 5-8)
   - Educational domain scores (Literacy, Math, SEL, etc.)
   - Content warnings (violence, language, mature themes)
   - Format analysis (pacing, visuals, audio)
   - Overall traffic-light rating (Green/Yellow/Red)
   - Specific scores (1-10): Educational Value, Production Quality, Safety
   - Timestamp-specific feedback
   - Parent guidance and activity suggestions

### Summary Report

A batch summary (`output/reports/_SUMMARY_YYYYMMDD_HHMMSS.md`) lists all processed videos with links to individual reports.

## Project Structure

```
video-evaluator/
├── evaluate.py              # Main CLI entry point
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── rubric_v1.rtf          # Full evaluation framework (reference)
│
├── src/                    # Core modules
│   ├── __init__.py
│   ├── frame_extractor.py      # OpenCV frame extraction
│   ├── audio_transcriber.py    # Whisper transcription
│   ├── evaluator.py            # Claude API integration
│   ├── rubric.py               # Evaluation rubric/prompt
│   └── report_generator.py     # Markdown report generation
│
├── videos/                 # Input: Place your videos here
│   └── (your .mp4, .mov files)
│
└── output/
    ├── reports/           # Output: Evaluation reports (markdown)
    └── temp/             # Temporary files (auto-cleaned unless --keep-temp)
        ├── frames/       # Extracted video frames
        └── transcripts/  # JSON transcripts
```

## How It Works

1. **Frame Extraction** (`frame_extractor.py`)
   - Uses OpenCV to extract frames at specified intervals
   - Samples evenly if too many frames extracted
   - Saves frames with timestamps in filenames

2. **Audio Transcription** (`audio_transcriber.py`)
   - Uses local Whisper model to transcribe audio
   - Generates timestamped segments
   - Formats transcript for Claude analysis

3. **Claude Evaluation** (`evaluator.py`)
   - Calls Claude Code CLI with frames and transcript
   - Uses your existing console credentials (no API key needed)
   - Sends comprehensive rubric-based evaluation prompt

4. **Report Generation** (`report_generator.py`)
   - Creates formatted markdown reports
   - Includes metadata, scores, and recommendations
   - Generates batch summaries for multiple videos

## Evaluation Framework

The rubric evaluates videos across multiple dimensions:

### Educational Domains
- 📚 **Literacy & Language**: ABCs, phonics, vocabulary, storytelling
- 🔢 **Numeracy & Math**: Counting, shapes, patterns, basic arithmetic
- 🤝 **Social & Emotional Learning**: Empathy, sharing, emotional regulation
- 🏃 **Movement & Physical Activity**: Dance, exercise, motor skills
- 🌿 **Nature & Environment**: Animals, plants, outdoor exploration
- 🔬 **Science & Exploration**: STEM concepts, curiosity, problem-solving
- 🎨 **Creativity & Art**: Imagination, music, creative expression

### Content Safety
- Violence (none/mild/significant)
- Sexual content (should be none for ages 0-8)
- Drugs/alcohol (should be none)
- Language (profanity, crude language)
- Mature themes (scary, emotionally intense)

### Format Quality
- Pacing (slow/moderate/fast)
- Visual stimulation (calm/balanced/overwhelming)
- Audio quality (clear speech, music balance)
- Interactivity (call-and-response, viewer engagement)

### Traffic-Light Rating
- 🟢 **Green**: Recommended for target age
- 🟡 **Yellow**: Use with caution/parental guidance
- 🔴 **Red**: Not recommended for young children

## Troubleshooting

### "Claude CLI not found"
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### "Could not open video file"
- Ensure ffmpeg is installed: `brew install ffmpeg`
- Check video file isn't corrupted
- Verify file format is supported (.mp4, .mov, .avi, .mkv, .webm, .m4v)

### Whisper model download issues
- First run downloads ~1GB model files
- Ensure stable internet connection
- Models stored in `~/.cache/whisper/`

### Claude evaluation times out
- Try reducing `--frames-per-batch` (send fewer frames)
- Check your internet connection
- Longer videos naturally take longer to analyze

### Out of memory errors
- Use smaller Whisper model: `--whisper-model tiny`
- Reduce frames per batch: `--frames-per-batch 20`
- Close other applications

## Performance Expectations

On Mac Studio M4:

- **Frame Extraction**: ~10-30 seconds per video
- **Whisper Transcription** (base model): ~1-3 minutes for 10-minute video
- **Claude Evaluation**: ~30-60 seconds (depends on frames sent)
- **Total**: ~2-5 minutes per video

## Scaling Up

For processing many videos:

1. **Batch Processing**: The tool already handles multiple videos in a folder
2. **Parallel Processing**: Currently sequential; could add multiprocessing later
3. **Cost Monitoring**: Each video uses Claude API (via your console credits)
4. **Storage**: Temp files auto-cleaned; reports are lightweight markdown

## Future Enhancements

Potential improvements for production version:

- [ ] Web interface for easier use
- [ ] Database storage for video metadata and scores
- [ ] Comparison reports across multiple videos
- [ ] Customizable rubric weights/criteria
- [ ] Video editing recommendations
- [ ] Export to CSV/JSON for analysis
- [ ] Integration with YouTube API for channel analysis
- [ ] Automated scheduling for continuous monitoring

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the generated reports for error messages
3. Run with `--keep-temp` to inspect intermediate files
4. Check Claude Code CLI documentation: https://docs.anthropic.com/

## License

This is an internal tool for educational video evaluation.

---

**Built with:**
- OpenCV for video processing
- OpenAI Whisper for transcription
- Anthropic Claude for AI-powered evaluation
- Python 3.8+
