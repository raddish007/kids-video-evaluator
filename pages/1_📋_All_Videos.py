"""
All Videos Page - Shows video overview with status grid
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB

st.set_page_config(
    page_title="All Videos",
    page_icon="📋",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .video-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #dee2e6;
        margin-bottom: 1rem;
    }
    .video-title {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: #212529;
    }
    .video-meta {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 1rem;
    }
    .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .status-item {
        padding: 0.5rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 0.85rem;
        border: 1px solid #dee2e6;
    }
    .status-completed {
        background-color: #d1e7dd;
        border-color: #a3cfbb;
    }
    .status-pending {
        background-color: #f8f9fa;
        border-color: #dee2e6;
    }
    .status-in-progress {
        background-color: #fff3cd;
        border-color: #ffe69c;
    }
    .status-failed {
        background-color: #f8d7da;
        border-color: #f1aeb5;
    }
    .progress-bar {
        height: 8px;
        background-color: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .progress-fill {
        height: 100%;
        background-color: #0d6efd;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


def get_status_emoji(status):
    """Get emoji for status."""
    emoji_map = {
        'completed': '✅',
        'in_progress': '⏳',
        'pending': '⭕',
        'failed': '❌'
    }
    return emoji_map.get(status, '❓')


def format_duration(seconds):
    """Format duration in seconds to human readable."""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def main():
    st.title("📋 All Videos")
    st.markdown("View and manage all ingested videos and their evaluation status")
    st.markdown("---")

    # Initialize database
    try:
        db = VideoEvaluatorDB()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    # Get video status data
    try:
        video_status = db.get_video_status()
        all_rubrics = db.get_all_rubrics()
    except Exception as e:
        st.error(f"Error loading videos: {e}")
        return

    if not video_status:
        st.info("No videos found. Start by ingesting videos with Phase 1!")
        return

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        search = st.text_input("🔍 Search videos", placeholder="Enter video title or ID...")

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest First", "Oldest First", "Most Complete", "Least Complete", "Title A-Z"]
        )

    with col3:
        st.write("")  # Spacer
        st.write("")
        show_all = st.checkbox("Show all details", value=False)

    st.markdown("---")

    # Filter videos based on search
    filtered_videos = video_status
    if search:
        search_lower = search.lower()
        filtered_videos = [
            v for v in video_status
            if search_lower in v['title'].lower() or search_lower in v['id'].lower()
        ]

    # Sort videos
    if sort_by == "Newest First":
        filtered_videos.sort(key=lambda x: x.get('ingestion_date') or '', reverse=True)
    elif sort_by == "Oldest First":
        filtered_videos.sort(key=lambda x: x.get('ingestion_date') or '')
    elif sort_by == "Most Complete":
        filtered_videos.sort(key=lambda x: x.get('completion_percentage', 0), reverse=True)
    elif sort_by == "Least Complete":
        filtered_videos.sort(key=lambda x: x.get('completion_percentage', 0))
    elif sort_by == "Title A-Z":
        filtered_videos.sort(key=lambda x: x['title'])

    st.write(f"Showing {len(filtered_videos)} of {len(video_status)} videos")

    # Display videos
    for video in filtered_videos:
        with st.container():
            # Video card header
            col1, col2, col3 = st.columns([6, 2, 2])

            with col1:
                st.markdown(f'<div class="video-title">{video["title"]}</div>', unsafe_allow_html=True)
                meta_parts = [
                    f"🆔 {video['id'][:12]}...",
                ]
                if video.get('duration_seconds'):
                    meta_parts.append(f"⏱️ {format_duration(video['duration_seconds'])}")
                if video.get('frame_count'):
                    meta_parts.append(f"🖼️ {video['frame_count']} frames")
                if video.get('youtube_id'):
                    meta_parts.append(f"📺 YouTube")

                st.markdown(f'<div class="video-meta">{" • ".join(meta_parts)}</div>', unsafe_allow_html=True)

            with col2:
                completion = video.get('completion_percentage', 0)
                st.metric("Completion", f"{completion:.0f}%")

            with col3:
                if video.get('total_cost'):
                    st.metric("Cost", f"${video['total_cost']:.3f}")
                else:
                    st.metric("Cost", "$0.00")

            # Progress bar
            completion = video.get('completion_percentage', 0)
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {completion}%"></div>
            </div>
            """, unsafe_allow_html=True)

            # Evaluation status
            st.write(f"**Evaluations:** {video['completed_count']}/{video['total_evaluations']} complete")

            if show_all:
                # Get detailed evaluations for this video
                evaluations = db.get_video_evaluations(video['id'])

                # Create status grid
                cols = st.columns(len(all_rubrics))
                for idx, rubric in enumerate(all_rubrics):
                    with cols[idx]:
                        # Find evaluation for this rubric
                        eval_status = 'pending'
                        for eval_item in evaluations:
                            if eval_item['rubric_name'] == rubric['name']:
                                eval_status = eval_item['status']
                                break

                        # Status badge
                        status_class = f"status-{eval_status}"
                        emoji = get_status_emoji(eval_status)
                        st.markdown(f"""
                        <div class="status-item {status_class}">
                            {emoji}<br>
                            <small>{rubric['display_name'][:15]}</small>
                        </div>
                        """, unsafe_allow_html=True)

            # Action button
            if st.button(f"View Details →", key=f"view_{video['id']}", use_container_width=True):
                st.session_state['selected_video_id'] = video['id']
                st.switch_page("pages/3_📹_Video_Detail.py")

            st.markdown("---")

    # Summary footer
    st.markdown("### 📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Videos", len(video_status))
    with col2:
        total_evals = sum(v.get('total_evaluations', 0) for v in video_status)
        st.metric("Total Evaluations", total_evals)
    with col3:
        completed_evals = sum(v.get('completed_count', 0) for v in video_status)
        st.metric("Completed", completed_evals)
    with col4:
        total_cost = sum(v.get('total_cost', 0) for v in video_status)
        st.metric("Total Cost", f"${total_cost:.2f}")


if __name__ == "__main__":
    main()
