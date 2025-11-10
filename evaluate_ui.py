"""
Streamlit UI for Video Evaluation
Select ingested videos and evaluate with different rubrics/models
"""

import streamlit as st
import json
import logging
from pathlib import Path
from datetime import datetime

# Import evaluators
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.evaluators.claude_evaluator import ClaudeEvaluator
from src.rubric_content_rating import get_content_rating_rubric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page config
st.set_page_config(
    page_title="Video Evaluator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Video Evaluation Tool")
st.markdown("Evaluate ingested videos with different rubrics and models")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Evaluation Settings")

    # Rubric selection (for now, just Content Rating)
    rubric_choice = st.selectbox(
        "Rubric",
        ["content_rating"],
        format_func=lambda x: {
            "content_rating": "Content Rating (Kijkwijzer)"
        }[x]
    )

    # Model selection
    model_choice = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514"],
        help="Claude model to use for evaluation"
    )

    # Frame sampling
    st.subheader("Frame Sampling")
    sampling_strategy = st.selectbox(
        "Sampling Strategy",
        ["even", "all", "first_n", "last_n"],
        help="How to select frames for analysis"
    )

    max_frames = st.slider(
        "Max Frames",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        help="Maximum number of frames to send to evaluator"
    )

    # Timeout
    timeout = st.slider(
        "Timeout (seconds)",
        min_value=60,
        max_value=1200,
        value=600,
        step=60,
        help="Maximum time to wait for evaluation"
    )


# Main content
# Step 1: Select video
st.header("1️⃣ Select Video")

data_dir = Path(__file__).parent / "data"

if not data_dir.exists():
    st.error(f"Data directory not found: {data_dir}")
    st.info("Please run the ingestion step first (app.py)")
    st.stop()

# Get all video directories
video_dirs = [d for d in data_dir.iterdir() if d.is_dir()]

if not video_dirs:
    st.warning("No ingested videos found!")
    st.info("Please run the ingestion step first (app.py) to process videos.")
    st.stop()

# Load video metadata for display
video_options = {}
for vdir in sorted(video_dirs):
    metadata_path = vdir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        video_id = vdir.name
        duration = metadata.get('duration_seconds', 0)
        frame_count = metadata.get('frame_count', 0)
        source_type = metadata.get('source_type', 'unknown')

        # Get YouTube title if available
        title = video_id
        youtube_metadata_path = vdir / "youtube_metadata.json"
        if youtube_metadata_path.exists():
            with open(youtube_metadata_path, 'r') as f:
                yt_meta = json.load(f)
                title = yt_meta.get('title', video_id)

        display_name = f"{title} ({duration:.0f}s, {frame_count} frames)"
        video_options[display_name] = {
            'video_id': video_id,
            'path': vdir,
            'metadata': metadata,
            'title': title
        }

selected_video_display = st.selectbox(
    "Select ingested video",
    options=list(video_options.keys())
)

if selected_video_display:
    selected_video = video_options[selected_video_display]
    video_id = selected_video['video_id']
    video_dir = selected_video['path']
    metadata = selected_video['metadata']

    # Show video info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Video ID", video_id)
    with col2:
        st.metric("Duration", f"{metadata.get('duration_seconds', 0):.1f}s")
    with col3:
        st.metric("Frames", metadata.get('frame_count', 0))

    # Show thumbnail if available
    thumbnail_path = video_dir / "thumbnail.jpg"
    if thumbnail_path.exists():
        st.image(str(thumbnail_path), caption=selected_video['title'], width=400)

    # Show existing evaluations if any
    evaluations_dir = video_dir / "evaluations"
    if evaluations_dir.exists():
        existing_evals = list(evaluations_dir.glob("*.json"))
        if existing_evals:
            with st.expander(f"📊 Existing Evaluations ({len(existing_evals)})"):
                for eval_path in sorted(existing_evals, reverse=True):
                    with open(eval_path, 'r') as f:
                        eval_data = json.load(f)

                    rubric = eval_data.get('rubric', 'unknown')
                    timestamp = eval_data.get('timestamp', 'unknown')
                    st.write(f"- **{rubric}** - {timestamp} - [{eval_path.name}]({eval_path})")

    st.markdown("---")

    # Step 2: Run Evaluation
    st.header("2️⃣ Run Evaluation")

    st.info(f"""
    **Configuration:**
    - Rubric: {rubric_choice}
    - Model: {model_choice}
    - Sampling: {sampling_strategy} (max {max_frames} frames)
    - Timeout: {timeout}s
    """)

    if st.button("▶️ Run Evaluation", type="primary", use_container_width=True):

        with st.spinner("Running evaluation..."):
            progress_bar = st.progress(0)
            status = st.empty()

            try:
                # Load rubric
                status.text("Loading rubric...")
                progress_bar.progress(10)

                if rubric_choice == "content_rating":
                    rubric_prompt = get_content_rating_rubric()
                else:
                    st.error(f"Unknown rubric: {rubric_choice}")
                    st.stop()

                # Initialize evaluator
                status.text("Initializing evaluator...")
                progress_bar.progress(20)

                evaluator = ClaudeEvaluator(
                    rubric_name=rubric_choice,
                    rubric_prompt=rubric_prompt,
                    model_name=model_choice,
                    sampling_strategy=sampling_strategy,
                    max_frames=max_frames,
                    timeout=timeout
                )

                # Load video data
                status.text("Loading video data...")
                progress_bar.progress(30)

                video_data = evaluator.load_video_data(video_id)

                frames = video_data['frames']
                transcript = video_data['transcript']
                metadata = video_data['metadata']

                # Run evaluation
                status.text(f"Evaluating with Claude ({len(frames)} frames)...")
                progress_bar.progress(40)

                result = evaluator.evaluate(
                    video_id=video_id,
                    frames=frames,
                    transcript=transcript,
                    metadata=metadata
                )

                # Save evaluation
                status.text("Saving evaluation...")
                progress_bar.progress(80)

                output_dir = video_dir / "evaluations"
                saved_path = evaluator.save_evaluation(
                    video_id=video_id,
                    evaluation_result=result,
                    output_dir=output_dir
                )

                progress_bar.progress(100)
                status.text("✓ Complete!")

                st.success(f"✓ Evaluation saved to: `{saved_path}`")

                # Display results
                st.markdown("---")
                st.header("3️⃣ Evaluation Results")

                # Metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Processing Time",
                        f"{result['performance_metrics']['processing_time_seconds']:.1f}s"
                    )
                with col2:
                    st.metric(
                        "Frames Analyzed",
                        f"{result['metadata']['frames_analyzed']}/{result['metadata']['total_frames_available']}"
                    )
                with col3:
                    st.metric(
                        "Words Analyzed",
                        result['metadata']['transcript_word_count']
                    )

                # Show evaluation text
                st.markdown("### Evaluation Report")
                st.markdown(result['evaluation_markdown'])

                # Download button
                st.download_button(
                    label="📥 Download Evaluation (JSON)",
                    data=json.dumps(result, indent=2),
                    file_name=f"{video_id}_{rubric_choice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

            except Exception as e:
                st.error(f"Evaluation failed: {str(e)}")
                logger.exception("Evaluation error:")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

else:
    st.info("👆 Select a video to begin")


# Footer
st.markdown("---")
st.caption("Video Evaluation Tool - Phase 2: Evaluation Pipeline")
