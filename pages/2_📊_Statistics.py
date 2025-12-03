"""
Statistics Page - Shows rubric completion stats and aggregated metrics
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB

st.set_page_config(
    page_title="Statistics",
    page_icon="📊",
    layout="wide"
)


def main():
    st.title("📊 Evaluation Statistics")
    st.markdown("Overview of evaluation completion across all rubrics")
    st.markdown("---")

    # Initialize database
    try:
        db = VideoEvaluatorDB()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    # Get statistics
    try:
        rubric_stats = db.get_rubric_completion_stats()
        video_status = db.get_video_status()
        all_videos = db.get_all_videos()
        total_cost = db.get_total_cost()
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
        return

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Videos", len(all_videos))

    with col2:
        total_evaluations = sum(r['total_evaluations'] for r in rubric_stats)
        st.metric("Total Evaluations", total_evaluations)

    with col3:
        completed_evaluations = sum(r['completed_count'] for r in rubric_stats)
        st.metric("Completed Evaluations", completed_evaluations)

    with col4:
        st.metric("Total Cost", f"${total_cost:.2f}")

    st.markdown("---")

    # Rubric completion stats
    st.markdown("## 📋 Rubric Completion Overview")

    if rubric_stats:
        # Create a table-like view
        for rubric in rubric_stats:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                with col1:
                    st.markdown(f"### {rubric['display_name']}")
                    st.caption(rubric.get('category', 'N/A').title())

                with col2:
                    completed = rubric['completed_count']
                    total = rubric['total_evaluations']
                    if total > 0:
                        completion_pct = (completed / total) * 100
                        st.metric("Completion", f"{completion_pct:.0f}%")
                    else:
                        st.metric("Completion", "0%")

                with col3:
                    st.metric("Completed", f"{rubric['completed_count']}")
                    if rubric.get('failed_count', 0) > 0:
                        st.caption(f"⚠️ {rubric['failed_count']} failed")

                with col4:
                    avg_cost = rubric.get('avg_cost', 0) or 0
                    st.metric("Avg Cost", f"${avg_cost:.3f}")
                    avg_duration = rubric.get('avg_duration_seconds', 0) or 0
                    if avg_duration > 0:
                        st.caption(f"⏱️ {int(avg_duration)}s avg")

                # Progress bar
                if rubric['total_evaluations'] > 0:
                    progress = rubric['completed_count'] / rubric['total_evaluations']
                    st.progress(progress)
                else:
                    st.progress(0.0)

                st.markdown("---")
    else:
        st.info("No statistics available yet. Start evaluating videos!")

    st.markdown("---")

    # Video completion distribution
    st.markdown("## 📹 Video Completion Distribution")

    if video_status:
        # Group videos by completion percentage
        completion_buckets = {
            "0%": 0,
            "1-25%": 0,
            "26-50%": 0,
            "51-75%": 0,
            "76-99%": 0,
            "100%": 0
        }

        for video in video_status:
            pct = video.get('completion_percentage', 0)
            if pct == 0:
                completion_buckets["0%"] += 1
            elif pct <= 25:
                completion_buckets["1-25%"] += 1
            elif pct <= 50:
                completion_buckets["26-50%"] += 1
            elif pct <= 75:
                completion_buckets["51-75%"] += 1
            elif pct < 100:
                completion_buckets["76-99%"] += 1
            else:
                completion_buckets["100%"] += 1

        # Display distribution
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        columns = [col1, col2, col3, col4, col5, col6]

        for idx, (bucket, count) in enumerate(completion_buckets.items()):
            with columns[idx]:
                st.metric(bucket, count)

    st.markdown("---")

    # Cost analysis
    st.markdown("## 💰 Cost Analysis")

    if video_status:
        videos_with_cost = [v for v in video_status if v.get('total_cost', 0) > 0]

        if videos_with_cost:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Cost", f"${total_cost:.2f}")

            with col2:
                avg_cost_per_video = total_cost / len(videos_with_cost)
                st.metric("Avg Cost/Video", f"${avg_cost_per_video:.2f}")

            with col3:
                if completed_evaluations > 0:
                    avg_cost_per_eval = total_cost / completed_evaluations
                    st.metric("Avg Cost/Evaluation", f"${avg_cost_per_eval:.3f}")
                else:
                    st.metric("Avg Cost/Evaluation", "$0.00")

            # Top 5 most expensive videos
            st.markdown("### 💸 Most Expensive Videos")
            expensive_videos = sorted(videos_with_cost, key=lambda x: x.get('total_cost', 0), reverse=True)[:5]

            for video in expensive_videos:
                col1, col2, col3 = st.columns([5, 2, 2])
                with col1:
                    st.write(f"**{video['title'][:50]}...**" if len(video['title']) > 50 else f"**{video['title']}**")
                with col2:
                    st.write(f"{video['completed_count']}/{video['total_evaluations']} complete")
                with col3:
                    st.write(f"💰 ${video['total_cost']:.3f}")

        else:
            st.info("No cost data available yet")

    st.markdown("---")

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 View All Videos", use_container_width=True):
            st.switch_page("pages/1_📋_All_Videos.py")
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.switch_page("app.py")


if __name__ == "__main__":
    main()
