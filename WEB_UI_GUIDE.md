# Video Tools - Web UI Guide

## Quick Start

### Option 1: Multi-Page Dashboard (Recommended)
Launch the complete dashboard with all tools:

```bash
cd video-evaluator
python3 -m streamlit run Home.py
```

The dashboard will open in your browser with access to all tools in the sidebar.

### Option 2: Standalone Tools
Run individual tools in standalone mode:

```bash
cd video-evaluator

# Video Ingestion only
python3 -m streamlit run app.py

# Video Evaluation only
python3 -m streamlit run evaluate_ui.py
```

Note: The Subtitle Generator is only available through the Home.py dashboard or CLI.

## Available Pages

### 🏠 Home Dashboard
Main landing page with:
- Overview of all available tools
- Quick CLI command reference
- Project statistics
- Getting started guide

### 📥 Video Ingestion
Upload videos or download from YouTube, then process them:
- Upload local video files (MP4, MOV, AVI, MKV, WebM)
- Download from YouTube URLs
- Extract frames at custom intervals
- Transcribe audio with Whisper
- Fetch YouTube metadata and captions
- Save all data to organized directories

**Features:**
- Automatic frame extraction
- Audio transcription with multiple Whisper models
- YouTube metadata fetching
- Caption/subtitle downloading from YouTube
- Organized data storage

### 📝 Subtitle Generator (NEW!)
Generate SRT subtitles and transcripts from any video:
- Upload video files
- Generate SRT subtitle files with proper timing
- Create timestamped transcripts
- Choose Whisper model (tiny, base, small, medium, large)
- Download generated files
- Browse previously generated subtitles

**Output:**
- `subtitles/video_name.srt` - SRT subtitle file
- `transcripts/video_name_transcript.txt` - Full transcript

**Whisper Models:**
- `tiny`: Fastest (~1GB RAM) - Good for quick tests
- `base`: Good balance (~1GB RAM)
- `small`: Better accuracy (~2GB RAM)
- `medium`: High accuracy (default) (~5GB RAM) - Recommended for best results
- `large`: Best accuracy (~10GB RAM)

### 🎯 Video Evaluation
Evaluate processed videos using AI models and rubrics:

**Available Rubrics:**
- Content Safety (Kijkwijzer) - Age appropriateness, safety concerns
- AI Quality & Fidelity - Technical quality of AI-generated content
- Production Metrics - Technical video quality metrics
- Media Ethics - Manipulation, commercial content detection

**Evaluator Options:**
- **Claude API** - Via Claude CLI (requires API key)
- **Gemini Flash** - Free Google API (1,500 requests/day)
- **Ollama** - Local models (requires Ollama installation)

## CLI Alternatives

All tools are also available via command line:

### Video Ingestion (CLI)
```bash
# Basic ingestion
python3 evaluate.py path/to/video.mp4

# Parent perspective
python3 evaluate.py video.mp4

# Creator perspective
python3 evaluate_creator.py video.mp4
```

### Subtitle Generation (CLI)
```bash
# Basic usage
python3 create_subtitles.py video.mp4

# Use specific model
python3 create_subtitles.py video.mp4 --model small

# Custom output directories
python3 create_subtitles.py video.mp4 \
    --subtitle-dir subs \
    --transcript-dir transcripts
```

### Video Evaluation (CLI)
```bash
# Parent evaluation
python3 evaluate.py video.mp4

# Creator evaluation
python3 evaluate_creator.py video.mp4
```

## File Structure

```
video-evaluator/
├── Home.py                  # Main dashboard (NEW!)
├── pages/                   # Streamlit pages (NEW!)
│   ├── 1_Video_Ingestion.py
│   ├── 2_Subtitle_Generator.py  # New subtitle tool
│   └── 3_Video_Evaluation.py
├── data/                    # Ingested video data
│   └── [video_id]/
│       ├── frames/
│       ├── metadata.json
│       └── transcript.json
├── subtitles/              # Generated SRT files (NEW!)
├── transcripts/            # Generated transcript files (NEW!)
├── downloaded_videos/      # YouTube downloads
├── output/                 # Evaluation reports
├── src/                    # Core modules
├── pipeline/              # Evaluation pipeline
├── evaluate.py            # CLI - Parent perspective
├── evaluate_creator.py    # CLI - Creator perspective
└── create_subtitles.py    # CLI - Subtitle generation (NEW!)
```

## Workflow Examples

### Example 1: YouTube Video Processing
1. **Video Ingestion**: Download and process a YouTube video
   - Paste YouTube URL
   - Extract frames every 2 seconds
   - Transcribe with Whisper (medium model)
   - Download captions if available

2. **Generate Subtitles**: Create SRT file from the same video
   - Use already downloaded video
   - Generate with small/medium model for accuracy

3. **Evaluate**: Assess content quality
   - Select content safety rubric
   - Choose evaluator (Gemini Flash for free tier)
   - Review evaluation report

### Example 2: Local Video Analysis
1. **Subtitle Generator**: Upload video to create subtitles
   - Upload MP4 file
   - Generate with base model
   - Download SRT for video editing

2. **Video Ingestion**: Process for detailed analysis
   - Upload same video
   - Extract more frames (every 1 second)
   - Get full transcription

3. **Evaluate**: Check production quality
   - Select production metrics rubric
   - Use Claude for detailed analysis
   - Export evaluation report

## Tips & Best Practices

### Subtitle Generation
- **Default `medium` model** provides high accuracy for most videos
- Use **`base` or `small`** for faster processing if needed
- **`tiny` model** is great for quick tests but may have more transcription errors
- **Processing time** increases with video length and model size
- SRT files can be imported into most video editing software

### Video Ingestion
- Lower frame intervals (1-2 seconds) for detailed analysis
- Higher intervals (5-10 seconds) for longer videos to save storage
- Medium Whisper model is recommended for transcription quality
- Check if YouTube captions are available before transcribing

### Video Evaluation
- **Gemini Flash** is free and fast - great for testing
- **Claude** provides more detailed analysis but costs money
- **Ollama** is completely free but requires local installation
- Different rubrics serve different purposes - choose based on your needs

## Troubleshooting

### Streamlit Not Found
```bash
pip install streamlit
```

### Port Already in Use
```bash
# Use a different port
python3 -m streamlit run Home.py --server.port 8502
```

### Whisper Model Issues
```bash
# Models download automatically on first use
# Ensure you have enough disk space:
# - tiny/base: ~1GB
# - small: ~2GB
# - medium: ~5GB
# - large: ~10GB
```

### Import Errors
Make sure you're running from the video-evaluator directory:
```bash
cd video-evaluator
python3 -m streamlit run Home.py
```

## Next Steps

1. **Explore the Dashboard** - Launch Home.py and familiarize yourself with the interface
2. **Try Subtitle Generator** - Upload a short video to test subtitle generation
3. **Process a Video** - Use Video Ingestion to fully process a video
4. **Run Evaluation** - Test different rubrics and evaluators

## Support

For issues or questions:
- Check the individual tool pages for specific help
- Review CLI command help: `python3 create_subtitles.py --help`
- See existing documentation in the repo (README.md, SETUP_COMPLETE.md, etc.)
