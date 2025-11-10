"""
Streamlit Web UI for Video Ingestion Pipeline
Phase 1: Upload/Download -> Extract Frames -> Transcribe Audio -> Save Metadata
"""
import streamlit as st
import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime
import logging

from src.youtube_downloader import YouTubeDownloader
from src.youtube_metadata import YouTubeMetadataFetcher
from src.youtube_captions import YouTubeCaptionDownloader
from src.frame_extractor import FrameExtractor
from src.audio_transcriber import AudioTranscriber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Video Ingestion Pipeline",
    page_icon="🎬",
    layout="wide"
)

# Constants
DATA_DIR = "data"
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_FRAME_INTERVAL = 2
DEFAULT_WHISPER_MODEL = "medium"


def sanitize_video_id(filename: str) -> str:
    """
    Sanitize filename to create a valid video_id

    Args:
        filename: Original filename

    Returns:
        Sanitized video_id (alphanumeric, hyphens, underscores only)
    """
    # Remove extension
    name = Path(filename).stem

    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    return sanitized or "video"


def extract_youtube_video_id(url: str) -> str:
    """
    Extract video ID from YouTube URL

    Args:
        url: YouTube URL

    Returns:
        Video ID (11 characters)
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return "unknown"


def check_existing_video(video_id: str) -> tuple:
    """
    Check if video_id already exists and find next available iteration

    Args:
        video_id: Base video ID

    Returns:
        Tuple of (exists: bool, base_path: str, next_iteration: str)
    """
    base_path = os.path.join(DATA_DIR, video_id)
    exists = os.path.exists(base_path)

    # Find next available iteration
    iteration = 2
    next_iteration = f"{video_id}_v{iteration}"

    while os.path.exists(os.path.join(DATA_DIR, next_iteration)):
        iteration += 1
        next_iteration = f"{video_id}_v{iteration}"

    return exists, base_path, next_iteration


def save_metadata(video_id: str, metadata: dict, video_path: str,
                  frame_paths: list, transcript: dict,
                  frame_interval: int, whisper_model: str):
    """
    Save ingestion metadata to metadata.json

    Args:
        video_id: Video identifier
        metadata: Video metadata dict
        video_path: Path to source video
        frame_paths: List of extracted frame paths
        transcript: Whisper transcript result
        frame_interval: Frame extraction interval in seconds
        whisper_model: Whisper model used
    """
    video_dir = os.path.join(DATA_DIR, video_id)

    # Get video properties
    extractor = FrameExtractor(interval_seconds=frame_interval)
    duration = extractor.get_video_duration(video_path)

    # Create metadata object
    metadata_obj = {
        "video_id": video_id,
        "source_type": metadata.get("source_type", "local"),
        "source_path": f"data/{video_id}/source.mp4",
        "youtube_url": metadata.get("youtube_url"),
        "duration_seconds": duration,
        "fps": metadata.get("fps", 30),
        "frame_interval_seconds": frame_interval,
        "frame_count": len(frame_paths),
        "frame_list": [os.path.relpath(p, video_dir) for p in frame_paths],
        "whisper_model": whisper_model,
        "whisper_language": transcript.get("language", "en"),
        "transcript_word_count": len(transcript.get("text", "").split()),
        "ingestion_timestamp": datetime.now().isoformat(),
        "ingestion_complete": True
    }

    # Save metadata.json
    metadata_path = os.path.join(video_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_obj, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Metadata saved to: {metadata_path}")


def process_video(video_source, source_type: str, video_id: str,
                  frame_interval: int, whisper_model: str, process_mode: str = "overwrite"):
    """
    Complete video ingestion pipeline

    Args:
        video_source: Path to local video or YouTube URL
        source_type: 'local' or 'youtube'
        video_id: Video identifier
        frame_interval: Frame extraction interval in seconds
        whisper_model: Whisper model to use
        process_mode: 'overwrite' or 'add_missing'

    Returns:
        Dictionary with processing results
    """
    try:
        # Create video directory
        video_dir = os.path.join(DATA_DIR, video_id)
        os.makedirs(video_dir, exist_ok=True)

        frames_dir = os.path.join(video_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        results = {
            "video_id": video_id,
            "video_dir": video_dir,
            "source_type": source_type
        }

        # Check existing files for add_missing mode
        source_path = os.path.join(video_dir, "source.mp4")
        video_exists = os.path.exists(source_path)
        yt_metadata_path = os.path.join(video_dir, "youtube_metadata.json")
        metadata_exists = os.path.exists(yt_metadata_path)
        thumbnail_path = os.path.join(video_dir, "thumbnail.jpg")
        thumbnail_exists = os.path.exists(thumbnail_path)
        captions_dir = os.path.join(video_dir, "captions")
        captions_exist = os.path.exists(captions_dir) and len(os.listdir(captions_dir)) > 0
        frames_exist = os.path.exists(frames_dir) and len(os.listdir(frames_dir)) > 0
        transcript_json_path = os.path.join(video_dir, "transcript.json")
        transcript_exists = os.path.exists(transcript_json_path)

        # Step 1: Handle video source
        if source_type == "youtube":
            # Download video if needed
            if not video_exists or process_mode == "overwrite":
                st.write("📥 Downloading YouTube video...")
                downloader = YouTubeDownloader(download_dir=video_dir)
                downloaded_path = downloader.download(video_source)
                if downloaded_path != source_path:
                    shutil.move(downloaded_path, source_path)
                st.success("✓ Video downloaded")
            else:
                st.info("✓ Video already exists, skipping download")

            # Fetch YouTube metadata if needed
            if not metadata_exists or process_mode == "overwrite":
                st.write("📊 Fetching YouTube metadata...")
                metadata_fetcher = YouTubeMetadataFetcher()
                youtube_metadata = metadata_fetcher.fetch_metadata(
                    video_source,
                    save_thumbnail=True,
                    thumbnail_dir=video_dir
                )
                with open(yt_metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(youtube_metadata, f, indent=2, ensure_ascii=False)
                st.success(f"✓ Metadata fetched: {youtube_metadata['title']}")
            else:
                st.info("✓ Metadata already exists, loading from file")
                with open(yt_metadata_path, 'r', encoding='utf-8') as f:
                    youtube_metadata = json.load(f)

            # Download YouTube captions if needed
            if not captions_exist or process_mode == "overwrite":
                st.write("📝 Downloading YouTube captions...")
                caption_downloader = YouTubeCaptionDownloader()
                caption_results = caption_downloader.download_captions(video_source, captions_dir)
                if caption_results['has_captions']:
                    caption_count = len(caption_results['downloaded_files'])
                    st.success(f"✓ Downloaded {caption_count} caption file(s)")
                else:
                    st.info("No captions available for this video")
            else:
                st.info("✓ Captions already exist, skipping download")
                # Load caption info
                caption_info_path = os.path.join(captions_dir, 'youtube_captions_info.json')
                if os.path.exists(caption_info_path):
                    with open(caption_info_path, 'r', encoding='utf-8') as f:
                        caption_results = json.load(f)
                else:
                    caption_results = {'has_captions': False}

            results["youtube_metadata"] = youtube_metadata
            results["caption_results"] = caption_results
            results["video_path"] = source_path
            results["youtube_url"] = video_source

        else:  # local file
            if not video_exists or process_mode == "overwrite":
                st.write("📁 Processing local video...")
                with open(source_path, "wb") as f:
                    f.write(video_source.read())
                st.success("✓ Video saved")
            else:
                st.info("✓ Video already exists, skipping upload")

            results["video_path"] = source_path
            results["youtube_metadata"] = None

        # Step 2: Extract frames
        if not frames_exist or process_mode == "overwrite":
            st.write(f"🎞️ Extracting frames (1 frame every {frame_interval}s)...")
            extractor = FrameExtractor(interval_seconds=frame_interval)
            frame_paths = extractor.extract_frames(source_path, frames_dir)
            st.success(f"✓ Extracted {len(frame_paths)} frames")
        else:
            st.info("✓ Frames already exist, skipping extraction")
            frame_paths = [os.path.join(frames_dir, f) for f in sorted(os.listdir(frames_dir)) if f.endswith('.jpg')]

        results["frame_paths"] = frame_paths
        results["frame_count"] = len(frame_paths)

        # Step 3: Transcribe audio
        if not transcript_exists or process_mode == "overwrite":
            st.write(f"🎤 Transcribing audio (Whisper {whisper_model} model)...")
            transcriber = AudioTranscriber(model_name=whisper_model)
            transcript = transcriber.transcribe_video(source_path)

            # Save transcript files
            with open(transcript_json_path, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)

            transcript_txt_path = os.path.join(video_dir, "transcript.txt")
            with open(transcript_txt_path, 'w', encoding='utf-8') as f:
                f.write(transcript['text'])

            word_count = len(transcript['text'].split())
            st.success(f"✓ Transcription complete ({word_count} words)")
        else:
            st.info("✓ Transcript already exists, loading from file")
            with open(transcript_json_path, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            word_count = len(transcript['text'].split())

        results["transcript"] = transcript
        results["word_count"] = word_count

        # Step 4: Save metadata
        st.write("💾 Saving metadata...")

        metadata = {
            "source_type": source_type,
            "youtube_url": video_source if source_type == "youtube" else None,
            "fps": 30  # Default, can be extracted from video if needed
        }

        save_metadata(
            video_id=video_id,
            metadata=metadata,
            video_path=source_path,
            frame_paths=frame_paths,
            transcript=transcript,
            frame_interval=frame_interval,
            whisper_model=whisper_model
        )

        st.success("✓ Metadata saved")

        return results

    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        logger.error(f"Processing error: {e}", exc_info=True)
        raise


def main():
    st.title("🎬 Video Ingestion Pipeline")
    st.markdown("Phase 1: Upload videos and extract frames + transcripts for evaluation")

    # Sidebar settings
    st.sidebar.header("⚙️ Settings")

    frame_interval = st.sidebar.slider(
        "Frame Interval (seconds)",
        min_value=1,
        max_value=10,
        value=DEFAULT_FRAME_INTERVAL,
        help="Extract 1 frame every N seconds"
    )

    whisper_model = st.sidebar.selectbox(
        "Whisper Model",
        options=WHISPER_MODELS,
        index=WHISPER_MODELS.index(DEFAULT_WHISPER_MODEL),
        help="Larger models are more accurate but slower"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Model Guide:**")
    st.sidebar.markdown("- **tiny**: Fastest (~1GB RAM)")
    st.sidebar.markdown("- **base**: Good balance (~1GB RAM)")
    st.sidebar.markdown("- **small**: Better accuracy (~2GB RAM)")
    st.sidebar.markdown("- **medium**: High accuracy (~5GB RAM)")
    st.sidebar.markdown("- **large**: Best accuracy (~10GB RAM)")

    # Main content area
    st.header("📹 Input Video")

    # Input method tabs
    tab1, tab2 = st.tabs(["📁 Upload Local File", "🌐 YouTube URL"])

    with tab1:
        st.markdown("Upload a video file from your computer")
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=["mp4", "mov", "avi", "mkv"],
            help="Supported formats: MP4, MOV, AVI, MKV"
        )

        if uploaded_file:
            # Generate video ID from filename
            video_id = sanitize_video_id(uploaded_file.name)

            # Check if video exists
            exists, base_path, next_iteration = check_existing_video(video_id)

            if exists:
                st.warning(f"⚠️ Video '{video_id}' already exists in data directory")

                iteration_choice = st.radio(
                    "Choose action:",
                    options=[
                        "Overwrite all data",
                        "Add missing files only",
                        f"Create new iteration ({next_iteration})"
                    ],
                    help="Overwrite: Replace everything. Add missing: Keep existing files, add what's missing. New iteration: Create separate copy."
                )

                if iteration_choice.startswith("Create new"):
                    video_id = next_iteration
                    st.info(f"Will create new iteration: {video_id}")
                elif iteration_choice.startswith("Add missing"):
                    st.info(f"Will add missing files to: {base_path}")
                else:
                    st.info(f"Will overwrite all data in: {base_path}")

            st.markdown(f"**Video ID:** `{video_id}`")

            if st.button("🚀 Process Video", type="primary"):
                # Determine processing mode
                process_mode = "overwrite"
                if exists:
                    if iteration_choice.startswith("Add missing"):
                        process_mode = "add_missing"

                with st.spinner("Processing video..."):
                    results = process_video(
                        video_source=uploaded_file,
                        source_type="local",
                        video_id=video_id,
                        frame_interval=frame_interval,
                        whisper_model=whisper_model,
                        process_mode=process_mode
                    )

                    # Show success page
                    show_results(results)

    with tab2:
        st.markdown("Enter a YouTube video URL")
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste a YouTube video URL"
        )

        if youtube_url:
            # Validate URL
            downloader = YouTubeDownloader()

            if not downloader.is_youtube_url(youtube_url):
                st.error("⚠️ Invalid YouTube URL")
            else:
                # Extract video ID from URL
                video_id = extract_youtube_video_id(youtube_url)

                # Check if video exists
                exists, base_path, next_iteration = check_existing_video(video_id)

                if exists:
                    st.warning(f"⚠️ Video '{video_id}' already exists in data directory")

                    iteration_choice = st.radio(
                        "Choose action:",
                        options=[
                            "Overwrite all data",
                            "Add missing files only",
                            f"Create new iteration ({next_iteration})"
                        ],
                        help="Overwrite: Replace everything. Add missing: Keep existing files, add what's missing. New iteration: Create separate copy.",
                        key="youtube_iteration_choice"
                    )

                    if iteration_choice.startswith("Create new"):
                        video_id = next_iteration
                        st.info(f"Will create new iteration: {video_id}")
                    elif iteration_choice.startswith("Add missing"):
                        st.info(f"Will add missing files to: {base_path}")
                    else:
                        st.info(f"Will overwrite all data in: {base_path}")

                st.markdown(f"**Video ID:** `{video_id}`")

                if st.button("🚀 Download & Process Video", type="primary"):
                    # Determine processing mode
                    process_mode = "overwrite"
                    if exists:
                        if iteration_choice.startswith("Add missing"):
                            process_mode = "add_missing"

                    with st.spinner("Processing video..."):
                        results = process_video(
                            video_source=youtube_url,
                            source_type="youtube",
                            video_id=video_id,
                            frame_interval=frame_interval,
                            whisper_model=whisper_model,
                            process_mode=process_mode
                        )

                        # Show success page
                        show_results(results)


def show_results(results: dict):
    """
    Display processing results

    Args:
        results: Dictionary containing processing results
    """
    st.success("🎉 Video ingestion complete!")

    st.markdown("---")
    st.header("📊 Results")

    # Basic info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Video ID", results["video_id"])

    with col2:
        st.metric("Frames Extracted", results["frame_count"])

    with col3:
        st.metric("Transcript Words", results["word_count"])

    # YouTube metadata (if available)
    if results.get("youtube_metadata"):
        yt_meta = results["youtube_metadata"]

        st.markdown("---")
        st.subheader("🎥 YouTube Video Info")

        # Show thumbnail
        thumbnail_path = yt_meta.get("thumbnail_path")
        if thumbnail_path and os.path.exists(thumbnail_path):
            st.image(thumbnail_path, width=400)

        # Video details
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Title:** {yt_meta.get('title', 'N/A')}")
            st.markdown(f"**Channel:** {yt_meta.get('channel_name', 'N/A')}")
            st.markdown(f"**Duration:** {yt_meta.get('duration_seconds', 0)} seconds")

        with col2:
            st.markdown(f"**Views:** {yt_meta.get('view_count', 0):,}")
            st.markdown(f"**Likes:** {yt_meta.get('like_count', 0):,}")
            st.markdown(f"**Upload Date:** {yt_meta.get('upload_date', 'N/A')}")

        # Hashtags
        hashtags = yt_meta.get('hashtags', [])
        if hashtags:
            st.markdown(f"**Hashtags:** {', '.join(['#' + tag for tag in hashtags])}")

        # Caption info
        if results.get("caption_results") and results["caption_results"]["has_captions"]:
            st.markdown("---")
            st.subheader("📝 YouTube Captions")

            caption_results = results["caption_results"]
            manual_count = len(caption_results.get("manual_captions", []))
            auto_count = len(caption_results.get("auto_captions", []))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Manual Captions", manual_count)
            with col2:
                st.metric("Auto-Generated", auto_count)

            # Show available languages
            caption_info = caption_results.get("caption_info", {})
            if caption_info.get("manual_languages"):
                st.markdown(f"**Manual Caption Languages:** {', '.join(caption_info['manual_languages'])}")
            if caption_info.get("auto_languages"):
                st.markdown(f"**Auto Caption Languages:** {', '.join(caption_info['auto_languages'])}")

    # Data directory info
    st.markdown("---")
    st.subheader("📁 Data Location")

    video_dir = results["video_dir"]
    st.code(video_dir)

    st.markdown("**Directory Contents:**")
    st.markdown(f"- `source.mp4` - Original video file")
    st.markdown(f"- `metadata.json` - Ingestion metadata")
    if results.get("youtube_metadata"):
        st.markdown(f"- `youtube_metadata.json` - YouTube-specific metadata")
        st.markdown(f"- `thumbnail.jpg` - Video thumbnail")
        if results.get("caption_results") and results["caption_results"]["has_captions"]:
            caption_count = len(results["caption_results"]["downloaded_files"])
            st.markdown(f"- `captions/` - {caption_count} YouTube caption file(s)")
    st.markdown(f"- `frames/` - {results['frame_count']} extracted frames")
    st.markdown(f"- `transcript.json` - Full Whisper output with timestamps")
    st.markdown(f"- `transcript.txt` - Plain text transcript")

    # Transcript preview
    st.markdown("---")
    st.subheader("📝 Transcript Preview")

    transcript_text = results["transcript"]["text"]
    preview_length = 500

    if len(transcript_text) > preview_length:
        st.text(transcript_text[:preview_length] + "...")
    else:
        st.text(transcript_text)

    # Next steps
    st.markdown("---")
    st.info("✨ **Next Steps:** Use the evaluation pipeline to analyze this video with different rubrics and evaluators.")


if __name__ == "__main__":
    main()
