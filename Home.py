"""
Video Tools Dashboard - Master Page
Provides access to all video processing and evaluation tools
"""
import streamlit as st
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Video Tools Dashboard",
    page_icon="🎬",
    layout="wide"
)

# Header
st.title("🎬 Video Tools Dashboard")
st.markdown("### Your complete toolkit for video processing and evaluation")

st.markdown("---")

# Quick Launch Commands
st.header("🚀 Quick Launch Commands")
st.markdown("Run these commands from the `video-evaluator` directory:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**📥 Video Ingestion (Standalone)**")
    st.code("python3 -m streamlit run app.py", language="bash")

with col2:
    st.markdown("**🎯 Video Evaluation (Standalone)**")
    st.code("python3 -m streamlit run evaluate_ui.py", language="bash")

with col3:
    st.markdown("**📝 Subtitle Generator (Web UI Only)**")
    st.info("Use this dashboard or the CLI tool")

st.markdown("---")

# Tool Cards
col1, col2 = st.columns(2)

with col1:
    st.header("📥 Video Ingestion")
    st.markdown("""
    Upload videos or download from YouTube, then extract frames and transcribe audio.

    **Features:**
    - Upload local video files
    - Download from YouTube URLs
    - Extract frames at custom intervals
    - Transcribe audio with Whisper
    - Fetch YouTube metadata and captions

    **Standalone Web UI:**
    ```bash
    python3 -m streamlit run app.py
    ```

    **CLI Usage:**
    ```bash
    # Run the ingestion pipeline
    python3 evaluate.py path/to/video.mp4
    ```
    """)

    st.header("📝 Subtitle Generator")
    st.markdown("""
    Generate SRT subtitles and transcripts from video files using Whisper.

    **Features:**
    - Upload video files
    - Generate SRT subtitle files
    - Create timestamped transcripts
    - Multiple Whisper model options
    - Download subtitle and transcript files

    **Web UI:**
    - Use this dashboard (page in sidebar)
    - No standalone app available

    **CLI Usage:**
    ```bash
    # Generate subtitles (default: medium model)
    python3 create_subtitles.py video.mp4

    # Use a different model
    python3 create_subtitles.py video.mp4 --model base

    # Custom output directories
    python3 create_subtitles.py video.mp4 \\
        --subtitle-dir subs \\
        --transcript-dir transcripts
    ```

    **Whisper Models:**
    - `tiny`: Fastest (~1GB RAM)
    - `base`: Good balance (~1GB RAM)
    - `small`: Better accuracy (~2GB RAM)
    - `medium`: High accuracy (default) (~5GB RAM)
    - `large`: Best accuracy (~10GB RAM)
    """)

with col2:
    st.header("🎯 Video Evaluation")
    st.markdown("""
    Evaluate ingested videos using different rubrics and AI models.

    **⚠️ Important:** Videos must be ingested first before evaluation!

    **Available Rubrics:**
    - Content Safety (Kijkwijzer)
    - AI Quality & Fidelity
    - Production Metrics (Technical)
    - Media Ethics (Manipulation & Commercial)

    **Evaluator Options:**
    - Claude API (via CLI)
    - Gemini Flash (Free API)
    - Ollama (Local models)

    **Standalone Web UI:**
    ```bash
    python3 -m streamlit run evaluate_ui.py
    ```

    **CLI Usage - Parent Perspective:**
    ```bash
    # Evaluate for parents
    python3 evaluate.py path/to/video.mp4
    ```

    **CLI Usage - Creator Perspective:**
    ```bash
    # Evaluate for content creators
    python3 evaluate_creator.py path/to/video.mp4
    ```
    """)

st.markdown("---")

# Quick Stats
st.header("📊 Project Statistics")
col1, col2, col3, col4 = st.columns(4)

# Count videos in data directory
data_dir = Path("data")
ingested_videos = len(list(data_dir.glob("*"))) if data_dir.exists() else 0

# Count subtitles
subtitle_dir = Path("subtitles")
subtitle_count = len(list(subtitle_dir.glob("*.srt"))) if subtitle_dir.exists() else 0

# Count transcripts
transcript_dir = Path("transcripts")
transcript_count = len(list(transcript_dir.glob("*.txt"))) if transcript_dir.exists() else 0

# Count downloaded videos
download_dir = Path("downloaded_videos")
downloaded_count = len(list(download_dir.glob("*.mp4"))) if download_dir.exists() else 0

with col1:
    st.metric("Ingested Videos", ingested_videos)

with col2:
    st.metric("Downloaded Videos", downloaded_count)

with col3:
    st.metric("Generated Subtitles", subtitle_count)

with col4:
    st.metric("Transcripts", transcript_count)

st.markdown("---")

# Getting Started
st.header("🚀 Getting Started")

st.markdown("### 📋 Typical Workflows")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Workflow 1: Full Video Analysis**
    1. **Video Ingestion** → Upload/download video
    2. **Video Evaluation** → Select ingested video & evaluate
    3. Download evaluation report

    *Best for: Comprehensive content analysis*
    """)

with col2:
    st.markdown("""
    **Workflow 2: Quick Subtitles**
    1. **Subtitle Generator** → Upload video
    2. Generate SRT and transcript
    3. Download files

    *Best for: Just need subtitles/transcripts*
    """)

st.markdown("""
**Need Help?**
- Check the individual tool pages for detailed instructions
- See CLI commands above for command-line usage
- All tools support both web UI and command-line interfaces
- **Video Evaluation requires Video Ingestion first** (frames + transcripts needed)
""")

# Footer
st.markdown("---")
st.caption("🎬 Video Tools Dashboard | Built with Streamlit & Claude")
