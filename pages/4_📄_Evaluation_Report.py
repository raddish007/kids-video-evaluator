"""
Evaluation Report Page - Display full evaluation report with formatting
"""

import streamlit as st
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB

st.set_page_config(
    page_title="Evaluation Report",
    page_icon="📄",
    layout="wide"
)


def format_duration(seconds):
    """Format duration."""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def main():
    st.title("📄 Evaluation Report")

    # Check if evaluation is in session state
    if 'selected_evaluation' not in st.session_state:
        st.warning("No evaluation selected. Please select an evaluation from the Video Detail page.")
        if st.button("← Go to All Videos"):
            st.switch_page("pages/1_📋_All_Videos.py")
        return

    evaluation = st.session_state['selected_evaluation']

    # Back button
    if st.button("← Back to Video Detail"):
        st.switch_page("pages/3_📹_Video_Detail.py")

    st.markdown("---")

    # Report header
    col1, col2 = st.columns([2, 1])

    with col1:
        # Get video info
        try:
            db = VideoEvaluatorDB()
            video = db.get_video(evaluation['video_id'])
            rubric = db.get_rubric(evaluation['rubric_name'])

            if video:
                st.markdown(f"### Video: {video['title']}")
            else:
                st.markdown(f"### Video ID: {evaluation['video_id']}")

            if rubric:
                st.markdown(f"**Rubric:** {rubric['display_name']}")
            else:
                st.markdown(f"**Rubric:** {evaluation['rubric_name']}")

        except Exception as e:
            st.error(f"Error loading video info: {e}")

    with col2:
        st.metric("Status", evaluation['status'].replace('_', ' ').title())
        if evaluation.get('cost'):
            st.metric("Cost", f"${evaluation['cost']:.4f}")

    # Evaluation metadata
    with st.expander("ℹ️ Evaluation Metadata", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Evaluator:** {evaluation.get('evaluator', 'N/A')}")
            st.write(f"**Model:** {evaluation.get('model_name', 'N/A')}")

        with col2:
            if evaluation.get('started_at'):
                st.write(f"**Started:** {evaluation['started_at'][:19]}")
            if evaluation.get('completed_at'):
                st.write(f"**Completed:** {evaluation['completed_at'][:19]}")

        with col3:
            if evaluation.get('duration_seconds'):
                st.write(f"**Duration:** {format_duration(evaluation['duration_seconds'])}")
            if evaluation.get('cost'):
                st.write(f"**Cost:** ${evaluation['cost']:.4f}")

    st.markdown("---")

    # Display evaluation report
    result = evaluation.get('result', {})

    if result:
        # Check if there's a markdown report
        markdown_report = result.get('evaluation_markdown') or result.get('report')

        if markdown_report:
            st.markdown("## 📋 Evaluation Report")

            # Display the markdown report
            st.markdown(markdown_report)

        else:
            st.info("No formatted report available. Showing raw JSON data:")
            st.json(result)

        # Additional sections
        st.markdown("---")

        # Performance metrics
        if 'performance_metrics' in result:
            with st.expander("⚡ Performance Metrics"):
                perf = result['performance_metrics']
                col1, col2, col3 = st.columns(3)

                with col1:
                    if 'processing_time_seconds' in perf:
                        st.metric("Processing Time", format_duration(perf['processing_time_seconds']))

                with col2:
                    if 'frames_processed' in perf:
                        st.metric("Frames Processed", perf['frames_processed'])

                with col3:
                    if 'total_frames_available' in perf:
                        st.metric("Total Frames", perf['total_frames_available'])

        # Cost info
        if 'cost_info' in result:
            with st.expander("💰 Cost Breakdown"):
                cost_info = result['cost_info']
                st.json(cost_info)

        # Full raw data
        with st.expander("🔍 Full Raw JSON Data"):
            st.json(result)

    else:
        st.warning("No evaluation result data available")

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Download JSON", use_container_width=True):
            # Create download link
            json_str = json.dumps(result, indent=2)
            st.download_button(
                label="Download Evaluation JSON",
                data=json_str,
                file_name=f"evaluation_{evaluation['video_id']}_{evaluation['rubric_name']}.json",
                mime="application/json"
            )

    with col2:
        if st.button("📄 Download Markdown", use_container_width=True):
            markdown_report = result.get('evaluation_markdown', 'No markdown report available')
            st.download_button(
                label="Download Markdown Report",
                data=markdown_report,
                file_name=f"evaluation_{evaluation['video_id']}_{evaluation['rubric_name']}.md",
                mime="text/markdown"
            )

    with col3:
        if st.button("← Back to Video", use_container_width=True):
            st.switch_page("pages/3_📹_Video_Detail.py")


if __name__ == "__main__":
    main()
