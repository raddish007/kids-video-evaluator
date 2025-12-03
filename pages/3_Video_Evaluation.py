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
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

from pipeline.evaluators.claude_evaluator import ClaudeEvaluator
from pipeline.evaluators.ollama_evaluator import OllamaEvaluator
from pipeline.evaluators.gemini_evaluator import GeminiEvaluator
from src.rubric_content_safety import get_content_safety_rubric
from src.rubric_ai_quality import get_ai_quality_rubric
from src.rubric_production_metrics import get_production_metrics_rubric
from src.rubric_media_ethics import get_media_ethics_rubric
from src.rubric_academic import get_academic_rubric
from src.rubric_fourPillars import get_brainrot_rubric
from src.database import VideoEvaluatorDB, Evaluation, EvaluationStatus

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize database
try:
    db = VideoEvaluatorDB()
    DB_AVAILABLE = True
except Exception as e:
    logger.warning(f"Database not available: {e}")
    DB_AVAILABLE = False


# Page config
st.set_page_config(
    page_title="Video Evaluation",
    page_icon="🎯",
    layout="wide"
)

st.title("🎬 Video Evaluation Tool")
st.markdown("Evaluate ingested videos with different rubrics and models")

# Database status indicator
if DB_AVAILABLE:
    st.success("✅ Database connected - evaluations will be synced automatically")
else:
    st.warning("⚠️ Database not available - evaluations will be saved locally only")

# Sidebar - Settings
with st.sidebar:
    st.header("⚙️ Evaluation Settings")

    # Rubric selection
    rubric_choice = st.selectbox(
        "Rubric",
        ["four_pillars", "academic", "content_safety", "ai_quality", "production_metrics", "media_ethics"],
        format_func=lambda x: {
            "academic": "🎓 Academic (4-Pillar Pedagogical Quality)",
            "four_pillars": "🧠 Four Pillars (Brainrot Detector)",
            "content_safety": "Content Safety (Kijkwijzer)",
            "ai_quality": "AI Quality & Fidelity",
            "production_metrics": "Production Metrics (Technical)",
            "media_ethics": "Media Ethics (Manipulation & Commercial)"
        }[x]
    )

    st.markdown("---")

    # Evaluator selection
    evaluator_type = st.selectbox(
        "Evaluator",
        ["claude", "gemini", "ollama"],
        format_func=lambda x: {
            "claude": "Claude API (via CLI)",
            "gemini": "Gemini Flash (Free API)",
            "ollama": "Ollama (Local)"
        }[x],
        help="Choose between Claude API, Gemini Flash (free), or local Ollama models"
    )

    # Evaluator-specific settings
    if evaluator_type == "claude":
        st.subheader("Claude Settings")
        model_choice = st.selectbox(
            "Model",
            ["claude-sonnet-4-20250514", "claude-opus-4-5-20251101", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            format_func=lambda x: {
                "claude-sonnet-4-20250514": "Claude Sonnet 4 (Recommended)",
                "claude-opus-4-5-20251101": "Claude Opus 4.5 (Most Capable)",
                "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Previous Gen)",
                "claude-3-haiku-20240307": "Claude 3 Haiku (Fast & Cheap)"
            }[x],
            help="Claude model to use"
        )
        st.caption("⚠️ Claude API limit: max 100 images per request")

    elif evaluator_type == "gemini":
        st.subheader("Gemini Settings")
        model_choice = st.selectbox(
            "Model",
            ["models/gemini-2.5-flash", "models/gemini-2.5-pro", "models/gemini-flash-latest"],
            format_func=lambda x: {
                "models/gemini-2.5-flash": "Gemini 2.5 Flash (Stable, Free Tier)",
                "models/gemini-2.5-pro": "Gemini 2.5 Pro (More Capable)",
                "models/gemini-flash-latest": "Gemini Flash Latest"
            }[x],
            help="Gemini model to use (Flash is free tier)"
        )

        st.info("💡 Gemini 2.5 Flash is free: 1,500 requests/day, 1M tokens/minute")
        st.caption("Set GEMINI_API_KEY environment variable. Get key: https://aistudio.google.com/app/apikey")

    else:  # ollama
        st.subheader("Ollama Settings")
        vision_model = st.selectbox(
            "Vision Model",
            ["llava:34b", "llava:13b", "phi3.5-vision", "qwen2.5-vl:7b"],
            help="Local vision model for frame analysis"
        )

        synthesis_model = st.selectbox(
            "Synthesis Model",
            ["llama3.2:3b", "llama3.1:8b", "llama3.1:70b"],
            help="Text model for combining batch analyses (smaller = faster, use 3b or 8b to avoid crashes)"
        )

        batch_size = st.slider(
            "Batch Size",
            min_value=4,
            max_value=12,
            value=8,
            step=2,
            help="Number of frames per batch (smaller = more thorough, slower)"
        )

    st.markdown("---")

    # Frame sampling (common to both)
    st.subheader("Frame Sampling")

    # Frame selection with clearer options
    frame_selection = st.selectbox(
        "Frames to Analyze",
        [
            "all",
            "50%",
            "25%",
            "10%",
            "max_50",
            "max_100",
            "max_200",
            "max_500"
        ],
        format_func=lambda x: {
            "all": "All frames (recommended)",
            "50%": "50% of frames (evenly sampled)",
            "25%": "25% of frames (evenly sampled)",
            "10%": "10% of frames (evenly sampled)",
            "max_50": "Maximum 50 frames",
            "max_100": "Maximum 100 frames",
            "max_200": "Maximum 200 frames",
            "max_500": "Maximum 500 frames"
        }[x],
        help="How many frames to send for analysis. 'All frames' is recommended for thorough evaluation."
    )

    # Convert selection to sampling_strategy and max_frames
    if frame_selection == "all":
        sampling_strategy = "all"
        max_frames = 9999  # Effectively unlimited
    elif frame_selection.endswith("%"):
        sampling_strategy = "even"
        # Will be calculated based on video frame count when video is selected
        percentage = int(frame_selection.replace("%", ""))
        max_frames = percentage  # Store percentage temporarily, will recalculate
    else:
        sampling_strategy = "even"
        max_frames = int(frame_selection.replace("max_", ""))

    # Timeout
    timeout = st.slider(
        "Timeout (seconds)",
        min_value=60,
        max_value=1800,
        value=900 if evaluator_type == "ollama" else 600,
        step=60,
        help="Maximum time to wait for evaluation"
    )


# Main content
# Step 1: Select video
st.header("1️⃣ Select Video")

# Fix path - go up to video-evaluator directory from pages/
data_dir = Path(__file__).parent.parent / "data"

if not data_dir.exists():
    st.warning("No videos have been ingested yet.")
    st.info("""
    **To evaluate a video, you need to ingest it first:**

    **Option 1: Use the Video Ingestion Page**
    - Go to "Video Ingestion" in the sidebar
    - Upload a video or paste a YouTube URL
    - The video will be processed and saved to the data directory

    **Option 2: Use the CLI**
    ```bash
    # From the video-evaluator directory:
    python3 evaluate.py path/to/video.mp4
    ```

    Once a video is ingested, it will appear here for evaluation.
    """)
    st.stop()

# Get all video directories
video_dirs = [d for d in data_dir.iterdir() if d.is_dir()]

if not video_dirs:
    st.warning("No ingested videos found!")
    st.info("""
    **To evaluate a video, you need to ingest it first:**

    **Option 1: Use the Video Ingestion Page**
    - Go to "Video Ingestion" in the sidebar
    - Upload a video or paste a YouTube URL
    - The video will be processed and saved to the data directory

    **Option 2: Use the CLI**
    ```bash
    # From the video-evaluator directory:
    python3 evaluate.py path/to/video.mp4
    ```

    Once a video is ingested, it will appear here for evaluation.
    """)
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

    # Show configuration summary
    frame_desc = {
        "all": "All frames",
        "50%": "50% of frames",
        "25%": "25% of frames",
        "10%": "10% of frames",
        "max_50": "Max 50 frames",
        "max_100": "Max 100 frames",
        "max_200": "Max 200 frames",
        "max_500": "Max 500 frames"
    }.get(frame_selection, frame_selection)

    if evaluator_type == "claude":
        config_summary = f"""
        **Configuration:**
        - Evaluator: Claude API
        - Rubric: {rubric_choice}
        - Model: {model_choice}
        - Frames: {frame_desc}
        - Timeout: {timeout}s
        """
    elif evaluator_type == "gemini":
        config_summary = f"""
        **Configuration:**
        - Evaluator: Gemini Flash API
        - Rubric: {rubric_choice}
        - Model: {model_choice}
        - Frames: {frame_desc}
        - Timeout: {timeout}s
        """
    else:  # ollama
        config_summary = f"""
        **Configuration:**
        - Evaluator: Ollama (Local)
        - Rubric: {rubric_choice}
        - Vision Model: {vision_model}
        - Synthesis Model: {synthesis_model}
        - Batch Size: {batch_size} frames/batch
        - Frames: {frame_desc}
        - Timeout: {timeout}s
        """

    st.info(config_summary)

    if st.button("▶️ Run Evaluation", type="primary", use_container_width=True):

        with st.spinner("Running evaluation..."):
            progress_bar = st.progress(0)
            status = st.empty()

            try:
                # Load rubric
                status.text("Loading rubric...")
                progress_bar.progress(10)

                if rubric_choice == "academic":
                    rubric_prompt = get_academic_rubric()
                elif rubric_choice == "four_pillars":
                    rubric_prompt = get_brainrot_rubric()
                elif rubric_choice == "content_safety":
                    rubric_prompt = get_content_safety_rubric()
                elif rubric_choice == "ai_quality":
                    rubric_prompt = get_ai_quality_rubric()
                elif rubric_choice == "production_metrics":
                    rubric_prompt = get_production_metrics_rubric()
                elif rubric_choice == "media_ethics":
                    rubric_prompt = get_media_ethics_rubric()
                else:
                    st.error(f"Unknown rubric: {rubric_choice}")
                    st.stop()

                # Calculate actual max_frames for percentage selections
                total_frames = metadata.get('frame_count', 100)
                if frame_selection.endswith("%"):
                    percentage = int(frame_selection.replace("%", ""))
                    max_frames = max(1, int(total_frames * percentage / 100))
                    status.text(f"Using {percentage}% of frames ({max_frames} of {total_frames})...")

                # Initialize evaluator
                status.text("Initializing evaluator...")
                progress_bar.progress(20)

                if evaluator_type == "claude":
                    evaluator = ClaudeEvaluator(
                        rubric_name=rubric_choice,
                        rubric_prompt=rubric_prompt,
                        model_name=model_choice,
                        sampling_strategy=sampling_strategy,
                        max_frames=max_frames,
                        timeout=timeout
                    )
                elif evaluator_type == "gemini":
                    evaluator = GeminiEvaluator(
                        rubric_name=rubric_choice,
                        rubric_prompt=rubric_prompt,
                        model_name=model_choice,
                        sampling_strategy=sampling_strategy,
                        max_frames=max_frames,
                        timeout=timeout
                    )
                else:  # ollama
                    evaluator = OllamaEvaluator(
                        rubric_name=rubric_choice,
                        rubric_prompt=rubric_prompt,
                        vision_model=vision_model,
                        synthesis_model=synthesis_model,
                        batch_size=batch_size,
                        sampling_strategy=sampling_strategy,
                        max_frames=max_frames
                    )

                # Load video data
                status.text("Loading video data...")
                progress_bar.progress(30)

                video_data = evaluator.load_video_data(video_id)

                frames = video_data['frames']
                transcript = video_data['transcript']
                metadata = video_data['metadata']

                # Run evaluation
                if evaluator_type == "claude":
                    eval_label = "Claude"
                elif evaluator_type == "gemini":
                    eval_label = f"Gemini ({model_choice})"
                else:
                    eval_label = f"Ollama ({vision_model})"

                status.text(f"Evaluating with {eval_label} ({len(frames)} frames)...")
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

                # Sync to database
                if DB_AVAILABLE:
                    status.text("Syncing to database...")
                    progress_bar.progress(90)

                    try:
                        # Extract summary from evaluation result
                        eval_markdown = result.get('evaluation_markdown', '')
                        summary = ' '.join(eval_markdown.split('\n')[:3])[:200] if eval_markdown else None

                        # Create Evaluation object
                        evaluation = Evaluation(
                            video_id=video_id,
                            rubric_name=rubric_choice,
                            status=EvaluationStatus.COMPLETED,
                            evaluator=evaluator_type,
                            model_name=result.get('model', model_choice if evaluator_type != "ollama" else vision_model),
                            cost=result.get('cost_info', {}).get('total_cost'),
                            started_at=datetime.now(),
                            completed_at=datetime.now(),
                            duration_seconds=result.get('performance_metrics', {}).get('processing_time_seconds'),
                            result=result,
                            summary=summary
                        )

                        # Upsert to database
                        db.upsert_evaluation(evaluation)
                        logger.info(f"✓ Synced evaluation to database: {video_id}/{rubric_choice}")

                    except Exception as e:
                        logger.error(f"Database sync failed: {e}")
                        st.warning(f"⚠️ Database sync failed: {e}. Evaluation saved locally.")

                progress_bar.progress(100)
                status.text("✓ Complete!")

                st.success(f"✓ Evaluation saved to: `{saved_path}`")
                if DB_AVAILABLE:
                    st.success("✓ Synced to database")

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
