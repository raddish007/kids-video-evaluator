"""
Video Evaluator Dashboard - Home Page

A Streamlit dashboard for viewing and managing video evaluations.
"""

import streamlit as st
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import VideoEvaluatorDB

# Page config
st.set_page_config(
    page_title="Video Evaluator Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 1rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)


def check_database_connection():
    """Check if database is accessible."""
    try:
        db = VideoEvaluatorDB()
        if db.health_check():
            return True, db
        return False, None
    except Exception as e:
        return False, str(e)


def main():
    """Main dashboard home page."""
    st.markdown('<h1 class="main-header">🎬 Video Evaluator Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Check database connection
    connected, db_or_error = check_database_connection()

    if not connected:
        st.error("❌ Database Connection Failed")
        st.write("Unable to connect to Supabase database.")
        st.code(f"Error: {db_or_error}" if isinstance(db_or_error, str) else "Database health check failed")
        st.info("""
        **Setup Instructions:**
        1. Make sure your `.env` file has `SUPABASE_URL` and `SUPABASE_KEY`
        2. Verify your Supabase project is running
        3. Check that you've run `schema.sql` in your Supabase project

        See `DATABASE_SETUP.md` for detailed instructions.
        """)
        return

    db = db_or_error
    st.success("✅ Connected to database")

    # Get overview statistics
    try:
        videos = db.get_all_videos()
        video_status = db.get_video_status()
        rubric_stats = db.get_rubric_completion_stats()
        total_cost = db.get_total_cost()
        recent_evals = db.get_recent_evaluations(limit=10)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # Overview stats
    st.markdown("## 📊 Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(videos)}</div>
            <div class="stat-label">Total Videos</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_evaluations = sum(v.get('total_evaluations', 0) for v in video_status)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{total_evaluations}</div>
            <div class="stat-label">Total Evaluations</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        completed_evaluations = sum(v.get('completed_count', 0) for v in video_status)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{completed_evaluations}</div>
            <div class="stat-label">Completed</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">${total_cost:.2f}</div>
            <div class="stat-label">Total Cost</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick links
    st.markdown("## 🚀 Quick Actions")
    st.info("👈 Use the sidebar to navigate to different pages")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    st.markdown("---")

    # Recent Activity
    st.markdown("## 🕒 Recent Activity")

    if recent_evals:
        for eval_item in recent_evals[:5]:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write(f"**{eval_item['video_title']}**")
                with col2:
                    rubric_display = eval_item.get('rubric_display_name', eval_item['rubric_name'])
                    status_emoji = "✅" if eval_item['status'] == 'completed' else "⏳"
                    st.write(f"{status_emoji} {rubric_display}")
                with col3:
                    if eval_item.get('completed_at'):
                        st.write(f"🕒 {eval_item['completed_at'][:19]}")
                st.markdown("---")
    else:
        st.info("No evaluation activity yet. Start by ingesting videos with Phase 1!")

    # System Info
    with st.expander("ℹ️ System Information"):
        st.write(f"**Database URL:** {db.url}")
        st.write(f"**Videos in database:** {len(videos)}")
        st.write(f"**Rubrics available:** {len(rubric_stats)}")
        st.write(f"**Total evaluations:** {total_evaluations}")

        if rubric_stats:
            st.markdown("### Rubrics Overview")
            for rubric in rubric_stats:
                st.write(f"- **{rubric['display_name']}**: {rubric['completed_count']} completed")


if __name__ == "__main__":
    main()
