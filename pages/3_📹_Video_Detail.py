"""
Video Detail Page - Shows detailed evaluation status for a specific video
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB

st.set_page_config(
    page_title="Video Detail",
    page_icon="📹",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .rubric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .rubric-card:hover {
        border-color: #0d6efd;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .rubric-completed {
        border-left: 5px solid #198754;
    }
    .rubric-pending {
        border-left: 5px solid #6c757d;
    }
    .rubric-in-progress {
        border-left: 5px solid #ffc107;
    }
    .rubric-failed {
        border-left: 5px solid #dc3545;
    }
    .rubric-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .rubric-meta {
        font-size: 0.9rem;
        color: #6c757d;
    }
    .video-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def format_duration(seconds):
    """Format duration."""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def get_status_emoji(status):
    """Get emoji for status."""
    emoji_map = {
        'completed': '✅',
        'in_progress': '⏳',
        'pending': '⭕',
        'failed': '❌'
    }
    return emoji_map.get(status, '❓')


def main():
    st.title("📹 Video Detail")

    # Check if video ID is in session state
    if 'selected_video_id' not in st.session_state:
        st.warning("No video selected. Please select a video from the All Videos page.")
        if st.button("← Go to All Videos"):
            st.switch_page("pages/1_📋_All_Videos.py")
        return

    video_id = st.session_state['selected_video_id']

    # Initialize database
    try:
        db = VideoEvaluatorDB()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    # Get video data
    try:
        video = db.get_video(video_id)
        if not video:
            st.error(f"Video not found: {video_id}")
            return

        video_status = db.get_video_status(video_id)
        if video_status:
            video_status = video_status[0]
        else:
            video_status = {}

        evaluations = db.get_video_evaluations(video_id)
        all_rubrics = db.get_all_rubrics()
    except Exception as e:
        st.error(f"Error loading video data: {e}")
        return

    # Back button
    if st.button("← Back to All Videos"):
        st.switch_page("pages/1_📋_All_Videos.py")

    st.markdown("---")

    # Video header
    st.markdown(f"""
    <div class="video-header">
        <h1>{video['title']}</h1>
        <p><strong>Video ID:</strong> {video['id']}</p>
        {f'<p>🔗 <a href="{video["youtube_url"]}" target="_blank" style="color: white;">View on YouTube</a></p>' if video.get('youtube_url') else ''}
    </div>
    """, unsafe_allow_html=True)

    # Video metadata
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Duration", format_duration(video.get('duration_seconds')))

    with col2:
        st.metric("Frames", video.get('frame_count', 'N/A'))

    with col3:
        completion = video_status.get('completion_percentage', 0)
        st.metric("Completion", f"{completion:.0f}%")

    with col4:
        cost = video_status.get('total_cost', 0)
        st.metric("Total Cost", f"${cost:.3f}")

    st.markdown("---")

    # Evaluation status
    st.markdown("## 📊 Evaluation Status")
    st.write(f"{video_status.get('completed_count', 0)}/{len(all_rubrics)} rubrics completed")

    # Create a map of evaluations by rubric name
    eval_map = {e['rubric_name']: e for e in evaluations}

    # Display rubrics
    for rubric in all_rubrics:
        rubric_name = rubric['name']
        evaluation = eval_map.get(rubric_name)

        if evaluation:
            status = evaluation['status']
            status_emoji = get_status_emoji(status)
            status_class = f"rubric-{status}"

            with st.container():
                st.markdown(f"""
                <div class="rubric-card {status_class}">
                    <div class="rubric-title">{status_emoji} {rubric['display_name']}</div>
                    <div class="rubric-meta">{rubric.get('description', 'No description')}</div>
                </div>
                """, unsafe_allow_html=True)

                # Show evaluation details
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.write(f"**Status:** {status.replace('_', ' ').title()}")
                    if evaluation.get('evaluator'):
                        st.write(f"**Evaluator:** {evaluation['evaluator']}")
                    if evaluation.get('model_name'):
                        st.write(f"**Model:** {evaluation['model_name']}")

                with col2:
                    if evaluation.get('completed_at'):
                        st.write(f"**Completed:** {evaluation['completed_at'][:19]}")
                    if evaluation.get('duration_seconds'):
                        st.write(f"**Duration:** {format_duration(evaluation['duration_seconds'])}")

                with col3:
                    if evaluation.get('cost'):
                        st.write(f"**Cost:** ${evaluation['cost']:.4f}")

                # View report button
                if status == 'completed':
                    if st.button(f"View Full Report →", key=f"view_report_{rubric_name}"):
                        st.session_state['selected_evaluation'] = evaluation
                        st.switch_page("pages/4_📄_Evaluation_Report.py")

                elif status == 'failed':
                    if evaluation.get('error_message'):
                        st.error(f"Error: {evaluation['error_message']}")

                st.markdown("---")

        else:
            # No evaluation exists for this rubric
            st.markdown(f"""
            <div class="rubric-card rubric-pending">
                <div class="rubric-title">⭕ {rubric['display_name']}</div>
                <div class="rubric-meta">{rubric.get('description', 'No description')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.write("**Status:** Not evaluated yet")
            st.markdown("---")

    # Video metadata expander
    with st.expander("📋 Full Video Metadata"):
        st.json(video.get('metadata', {}))

    # Quick actions
    st.markdown("## 🛠️ Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Re-run All Evaluations"):
            st.info("Feature coming soon: Trigger re-evaluation from dashboard")

    with col2:
        if st.button("📊 View Statistics"):
            st.switch_page("pages/2_📊_Statistics.py")

    with col3:
        if st.button("📋 All Videos"):
            st.switch_page("pages/1_📋_All_Videos.py")


if __name__ == "__main__":
    main()
