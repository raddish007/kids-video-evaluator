"""
Subtitle Generator - Web UI
Generate SRT subtitles and transcripts from video files using Whisper
"""
import streamlit as st
import os
import tempfile
from pathlib import Path
from datetime import datetime
import logging

from src.audio_transcriber import AudioTranscriber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Subtitle Generator",
    page_icon="📝",
    layout="wide"
)

# Constants
SUBTITLE_DIR = "subtitles"
TRANSCRIPT_DIR = "transcripts"
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def format_timestamp_readable(seconds: float) -> str:
    """Format seconds to readable MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def create_srt_content(transcript_result: dict) -> str:
    """Generate SRT content from Whisper transcript"""
    srt_lines = []
    for idx, segment in enumerate(transcript_result.get('segments', []), start=1):
        # SRT index
        srt_lines.append(f"{idx}")

        # Timestamps
        start_time = format_srt_timestamp(segment['start'])
        end_time = format_srt_timestamp(segment['end'])
        srt_lines.append(f"{start_time} --> {end_time}")

        # Text content
        text = segment['text'].strip()
        srt_lines.append(text)

        # Blank line between subtitles
        srt_lines.append("")

    return "\n".join(srt_lines)


def create_transcript_content(transcript_result: dict) -> str:
    """Generate transcript text content"""
    lines = []
    lines.append("=== VIDEO TRANSCRIPT ===\n")

    # Full text
    lines.append("FULL TEXT:")
    lines.append(transcript_result['text'].strip())
    lines.append("\n")

    # Timestamped segments
    lines.append("TIMESTAMPED SEGMENTS:")
    for segment in transcript_result.get('segments', []):
        start_time = format_timestamp_readable(segment['start'])
        end_time = format_timestamp_readable(segment['end'])
        text = segment['text'].strip()
        lines.append(f"[{start_time} - {end_time}] {text}")

    return "\n".join(lines)


# Header
st.title("📝 Subtitle Generator")
st.markdown("Generate SRT subtitles and transcripts from video files using Whisper AI")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Settings")

    model_choice = st.selectbox(
        "Whisper Model",
        WHISPER_MODELS,
        index=3,  # default to 'medium'
        help="""
        Model accuracy vs speed:
        • tiny: Fastest, least accurate (~1GB RAM)
        • base: Good balance (~1GB RAM)
        • small: Better accuracy (~2GB RAM)
        • medium: High accuracy (recommended) (~5GB RAM)
        • large: Best accuracy (~10GB RAM)
        """
    )

    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("""
    - **base** model is good for most videos
    - Use **small** or **medium** for better accuracy
    - Larger models take longer but are more accurate
    - Processing time depends on video length
    """)

    st.markdown("---")
    st.markdown("### 📋 CLI Usage")
    st.code(f"""# Generate subtitles
python3 create_subtitles.py video.mp4

# Use specific model
python3 create_subtitles.py video.mp4 \\
    --model {model_choice}""", language="bash")

# Main content
tab1, tab2 = st.tabs(["📤 Upload & Generate", "📁 Browse Generated Files"])

with tab1:
    st.header("Upload Video File")

    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'mov', 'avi', 'mkv', 'webm'],
        help="Upload a video file to generate subtitles and transcript"
    )

    if uploaded_file:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.success(f"✓ File uploaded: **{uploaded_file.name}**")
            st.write(f"Size: {uploaded_file.size / (1024*1024):.2f} MB")

        with col2:
            generate_button = st.button(
                "🚀 Generate Subtitles",
                type="primary",
                use_container_width=True
            )

        if generate_button:
            # Create output directories
            os.makedirs(SUBTITLE_DIR, exist_ok=True)
            os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.read())
                video_path = tmp_file.name

            try:
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Load Whisper model
                status_text.text(f"Loading Whisper model: {model_choice}...")
                progress_bar.progress(10)

                transcriber = AudioTranscriber(model_name=model_choice)
                progress_bar.progress(30)

                # Transcribe
                status_text.text("Transcribing audio...")
                transcript_result = transcriber.transcribe_video(video_path)
                progress_bar.progress(70)

                # Generate files
                status_text.text("Generating subtitle and transcript files...")

                # Create file paths
                video_name = Path(uploaded_file.name).stem
                srt_filename = f"{video_name}.srt"
                transcript_filename = f"{video_name}_transcript.txt"

                srt_path = os.path.join(SUBTITLE_DIR, srt_filename)
                transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)

                # Generate SRT
                srt_content = create_srt_content(transcript_result)
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)

                # Generate transcript
                transcript_content = create_transcript_content(transcript_result)
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_content)

                progress_bar.progress(100)
                status_text.empty()

                # Success message
                st.success("✅ Subtitles and transcript generated successfully!")

                # Display summary
                summary = transcriber.get_transcript_summary(transcript_result)

                st.markdown("---")
                st.subheader("📊 Summary")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Language", summary['language'].upper())
                with col2:
                    st.metric("Duration", f"{summary['duration_seconds']:.1f}s")
                with col3:
                    st.metric("Total Words", summary['total_words'])
                with col4:
                    st.metric("WPM", f"{summary['words_per_minute']:.1f}")

                # Download buttons
                st.markdown("---")
                st.subheader("📥 Download Files")

                col1, col2 = st.columns(2)

                with col1:
                    st.download_button(
                        label="📥 Download SRT Subtitle File",
                        data=srt_content,
                        file_name=srt_filename,
                        mime="text/plain",
                        use_container_width=True
                    )

                with col2:
                    st.download_button(
                        label="📥 Download Transcript File",
                        data=transcript_content,
                        file_name=transcript_filename,
                        mime="text/plain",
                        use_container_width=True
                    )

                # Preview
                st.markdown("---")
                st.subheader("👀 Preview")

                preview_tab1, preview_tab2 = st.tabs(["SRT Subtitle", "Transcript"])

                with preview_tab1:
                    st.text_area(
                        "SRT Content (first 20 lines)",
                        "\n".join(srt_content.split("\n")[:20]),
                        height=300
                    )

                with preview_tab2:
                    st.text_area(
                        "Transcript Content",
                        transcript_result['text'][:1000] + "..." if len(transcript_result['text']) > 1000 else transcript_result['text'],
                        height=300
                    )

            except Exception as e:
                st.error(f"❌ Error generating subtitles: {str(e)}")
                logger.exception("Subtitle generation failed")

            finally:
                # Clean up temp file
                if os.path.exists(video_path):
                    os.unlink(video_path)

with tab2:
    st.header("Generated Files")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Subtitle Files (.srt)")
        subtitle_dir_path = Path(SUBTITLE_DIR)
        if subtitle_dir_path.exists():
            srt_files = sorted(subtitle_dir_path.glob("*.srt"), key=lambda x: x.stat().st_mtime, reverse=True)

            if srt_files:
                for srt_file in srt_files:
                    with st.expander(f"📄 {srt_file.name}"):
                        st.write(f"**Size:** {srt_file.stat().st_size / 1024:.2f} KB")
                        st.write(f"**Modified:** {datetime.fromtimestamp(srt_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")

                        # Download button
                        with open(srt_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        st.download_button(
                            label="📥 Download",
                            data=content,
                            file_name=srt_file.name,
                            mime="text/plain",
                            key=f"download_srt_{srt_file.name}"
                        )
            else:
                st.info("No subtitle files generated yet.")
        else:
            st.info("Subtitle directory doesn't exist yet. Generate your first subtitle!")

    with col2:
        st.subheader("📄 Transcript Files (.txt)")
        transcript_dir_path = Path(TRANSCRIPT_DIR)
        if transcript_dir_path.exists():
            txt_files = sorted(transcript_dir_path.glob("*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)

            if txt_files:
                for txt_file in txt_files:
                    with st.expander(f"📄 {txt_file.name}"):
                        st.write(f"**Size:** {txt_file.stat().st_size / 1024:.2f} KB")
                        st.write(f"**Modified:** {datetime.fromtimestamp(txt_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")

                        # Download button
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        st.download_button(
                            label="📥 Download",
                            data=content,
                            file_name=txt_file.name,
                            mime="text/plain",
                            key=f"download_txt_{txt_file.name}"
                        )
            else:
                st.info("No transcript files generated yet.")
        else:
            st.info("Transcript directory doesn't exist yet. Generate your first transcript!")

# Footer
st.markdown("---")
st.caption("📝 Subtitle Generator | Powered by OpenAI Whisper")
