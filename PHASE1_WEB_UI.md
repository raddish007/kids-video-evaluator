# Phase 1: Video Ingestion Web UI

## Overview

The Streamlit web UI provides a clean, simple interface for ingesting videos into the evaluation pipeline. It handles:

1. **Video Input** - Upload local files or download from YouTube
2. **Frame Extraction** - Extract frames at configurable intervals (1-10 seconds)
3. **Audio Transcription** - Transcribe with Whisper (choice of model sizes)
4. **Metadata Collection** - Save all video information and YouTube metadata
5. **Iteration Handling** - Overwrite or create new versions when re-processing videos

## Quick Start

### Launch the Web UI

```bash
cd video-evaluator
python3 -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Interface

#### 1. Configure Settings (Sidebar)

- **Frame Interval**: 1-10 seconds (default: 2s)
  - Lower = more frames = better coverage, slower processing
  - Higher = fewer frames = faster processing
- **Whisper Model**: tiny/base/small/medium/large (default: base)
  - `tiny`: Fastest, ~1GB RAM
  - `base`: Good balance, ~1GB RAM (recommended)
  - `small`: Better accuracy, ~2GB RAM
  - `medium`: High accuracy, ~5GB RAM
  - `large`: Best accuracy, ~10GB RAM

#### 2. Choose Input Method

**Tab 1: Upload Local File**
- Click "Choose a video file"
- Select MP4, MOV, AVI, or MKV file
- Video ID generated from filename
- Click "Process Video"

**Tab 2: YouTube URL**
- Paste YouTube URL: `https://www.youtube.com/watch?v=...`
- Video ID extracted from URL
- Click "Download & Process Video"

#### 3. Handle Existing Videos

If the video ID already exists, you'll see two options:

- **Overwrite existing data**: Replace frames/transcript with new settings
  - Use when: Testing different intervals or models
- **Create new iteration (v2, v3...)**: Keep original, create separate version
  - Use when: Comparing different extraction strategies

#### 4. Review Results

After processing completes, you'll see:

- **Metrics**: Video ID, frame count, word count
- **YouTube Info** (if applicable): Title, channel, views, thumbnail
- **Data Location**: Directory structure and file listing
- **Transcript Preview**: First 500 characters

## Data Structure

Each processed video creates a directory: `data/<video_id>/`

```
data/
└── <video_id>/
    ├── source.mp4              # Original video
    ├── metadata.json           # Ingestion metadata
    ├── youtube_metadata.json   # YouTube-specific data (if applicable)
    ├── thumbnail.jpg           # Downloaded thumbnail (if YouTube)
    ├── captions/               # YouTube captions (if available)
    │   ├── captions_manual_en.srt      # Manual English captions
    │   ├── captions_auto_en.srt        # Auto-generated English captions
    │   ├── youtube_captions_info.json  # Caption metadata
    │   └── ...
    ├── frames/                 # Extracted frames
    │   ├── frame_0000_t0.0s.jpg
    │   ├── frame_0001_t2.0s.jpg
    │   └── ...
    ├── transcript.json         # Full Whisper output with timestamps
    └── transcript.txt          # Plain text transcript
```

## Metadata Schemas

### metadata.json (Ingestion)

```json
{
  "video_id": "MyClip",
  "source_type": "local" | "youtube",
  "source_path": "data/MyClip/source.mp4",
  "youtube_url": "https://...",
  "duration_seconds": 180.5,
  "fps": 30,
  "frame_interval_seconds": 2,
  "frame_count": 90,
  "frame_list": ["frames/frame_0001.jpg", ...],
  "whisper_model": "base",
  "whisper_language": "en",
  "transcript_word_count": 245,
  "ingestion_timestamp": "2024-11-10T14:30:00Z",
  "ingestion_complete": true
}
```

### youtube_metadata.json (YouTube-specific)

```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Video Title",
  "description": "Full description...",
  "hashtags": ["tag1", "tag2"],
  "url": "https://www.youtube.com/watch?v=...",
  "thumbnail_url": "https://...",
  "thumbnail_path": "data/.../thumbnail.jpg",
  "channel_name": "Channel Name",
  "channel_id": "UCxxxxx",
  "channel_subscriber_count": 1000000,
  "upload_date": "2024-01-01T00:00:00Z",
  "duration_seconds": 180,
  "view_count": 1000000,
  "like_count": 50000,
  "comment_count": 1000,
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "1920:1080",
  "fps": 30,
  "category": "Education",
  "tags": ["tag1", "tag2"],
  "language": "en",
  "has_captions": true,
  "age_restricted": false,
  "availability": "public",
  "content_flags": {
    "comments_enabled": true,
    "ratings_enabled": true,
    "is_embeddable": true,
    "live_content": false
  },
  "metadata_fetched_at": "2024-11-10T14:30:00Z"
}
```

### youtube_captions_info.json (Caption metadata)

```json
{
  "has_captions": true,
  "manual_captions": [
    {
      "language": "en",
      "type": "manual",
      "file": "data/dQw4w9WgXcQ/captions/captions_manual_en.srt"
    }
  ],
  "auto_captions": [
    {
      "language": "en",
      "type": "auto",
      "file": "data/dQw4w9WgXcQ/captions/captions_auto_en.srt"
    }
  ],
  "downloaded_files": [
    "data/dQw4w9WgXcQ/captions/captions_manual_en.srt",
    "data/dQw4w9WgXcQ/captions/captions_auto_en.srt"
  ],
  "caption_info": {
    "manual_languages": ["en"],
    "auto_languages": ["en", "es", "fr"]
  }
}
```

## YouTube Captions

When processing YouTube videos, the pipeline automatically attempts to download available captions:

**Caption Types:**
- **Manual/Uploaded Captions**: Professionally created captions uploaded by the creator (higher quality)
- **Auto-Generated Captions**: YouTube's automatic speech recognition captions (available for most videos)

**Features:**
- Downloads all available languages (English prioritized)
- Saves in SRT format (SubRip) - compatible with most video editors
- Creates metadata file with language information
- Whisper transcription still runs for comparison

**Use Cases:**
- Compare Whisper quality against YouTube's captions
- Use professional captions if available (skip Whisper results)
- Multi-language caption availability
- Upload-ready subtitle files for video editing

**File Naming:**
- `captions_manual_en.srt` - Manual English captions
- `captions_auto_en.srt` - Auto-generated English captions
- `captions_manual_es.srt` - Manual Spanish captions (if available)

## Iteration Examples

### Example 1: Testing Different Frame Intervals

```
1. First ingestion:
   - Upload "MyVideo.mp4"
   - Frame interval: 2s
   - Creates: data/MyClip/

2. Re-process with more frames:
   - Upload "MyVideo.mp4" again
   - Frame interval: 1s
   - Choose: "Create new iteration (MyClip_v2)"
   - Creates: data/MyClip_v2/

Result: Now you have both versions to compare
```

### Example 2: Testing Different Whisper Models

```
1. First ingestion:
   - YouTube URL
   - Whisper model: base
   - Creates: data/dQw4w9WgXcQ/

2. Re-transcribe with better model:
   - Same YouTube URL
   - Whisper model: medium
   - Choose: "Create new iteration (dQw4w9WgXcQ_v2)"
   - Creates: data/dQw4w9WgXcQ_v2/

Result: Compare transcription quality between models
```

## Performance Expectations

For a 3-minute video on Mac Studio M4:

| Step | Time | Notes |
|------|------|-------|
| YouTube download | 10-30s | Network dependent |
| Metadata fetch | 2-5s | Includes thumbnail download |
| Frame extraction (2s interval) | <30s | ~90 frames |
| Whisper base transcription | ~2 min | Scales linearly with video length |
| **Total** | ~3 min | Local files skip download step |

## Troubleshooting

### "No module named streamlit"
```bash
pip3 install -r requirements.txt
```

### "Failed to download video"
- Check YouTube URL is valid
- Check internet connection
- Try a different video (some may be geo-restricted)

### "Whisper model loading failed"
- Whisper downloads models on first use (~1-10GB depending on model)
- Ensure sufficient disk space
- Check internet connection for first-time model download

### Slow transcription
- Use smaller Whisper model (tiny or base)
- Close other memory-intensive apps
- Consider processing shorter clips first

## Next Steps

After ingestion, videos are ready for evaluation:

```bash
# Phase 2: Evaluate with different strategies
python3 pipeline/evaluate_video.py --video-id MyClip --evaluator claude-api --rubric parent

# Phase 3: Generate reports
python3 pipeline/generate_report.py --video-id MyClip --evaluation latest --template parent
```

## Tips

- **Start with base model**: Good balance of speed and accuracy
- **Use 2s intervals**: Usually sufficient coverage for most videos
- **Create iterations when comparing**: Keep original data intact
- **Overwrite when refining**: Replace obviously wrong settings
- **Process in batches**: Keep Whisper model loaded for multiple videos
