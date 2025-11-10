#!/usr/bin/env python3
"""
Kids Video Creator Evaluator - Provide production feedback for creators

Analyzes children's educational videos to provide actionable feedback
for content creators on script, production quality, pedagogy, and engagement.

Usage:
    python evaluate_creator.py [--videos-dir PATH] [options]

Examples:
    # Process all videos in default 'videos' folder
    python evaluate_creator.py

    # Specify custom videos directory
    python evaluate_creator.py --videos-dir /path/to/videos

    # Use more frames for detailed analysis
    python evaluate_creator.py --frames-per-batch 50
"""

import argparse
import sys
import time
import os
from pathlib import Path
from typing import List
import logging
import shutil

from src import (
    FrameExtractor,
    AudioTranscriber,
    ReportGenerator,
    YouTubeDownloader
)
from src.evaluator_claude_code import VideoEvaluatorClaudeCode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'}


def find_videos(directory: str) -> List[str]:
    """Find all video files in directory"""
    video_files = []
    for ext in VIDEO_EXTENSIONS:
        video_files.extend(Path(directory).glob(f'*{ext}'))
        video_files.extend(Path(directory).glob(f'*{ext.upper()}'))

    return sorted([str(f) for f in video_files])


class CreatorReportGenerator(ReportGenerator):
    """Extended report generator for creator feedback"""

    def generate_report(
        self,
        video_name: str,
        video_path: str,
        evaluation: str,
        transcript_summary: dict,
        num_frames: int,
        processing_time: float
    ) -> str:
        """Generate creator-focused markdown report"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create report content
        report_lines = []
        report_lines.append(f"# Creator Feedback Report: {video_name}")
        report_lines.append(f"\n**Generated:** {timestamp}")
        report_lines.append(f"**Report Type:** Production & Pedagogical Feedback\n")

        # Video metadata section
        report_lines.append("## Video Information\n")
        report_lines.append(f"- **File:** `{Path(video_path).name}`")
        report_lines.append(f"- **Duration:** {transcript_summary.get('duration_seconds', 0):.1f} seconds")
        report_lines.append(f"- **Frames Analyzed:** {num_frames}")
        report_lines.append(f"- **Analysis Time:** {processing_time:.1f} seconds")
        report_lines.append("")

        # Transcript metadata
        report_lines.append("## Transcript Analysis\n")
        report_lines.append(f"- **Language:** {transcript_summary.get('language', 'unknown')}")
        report_lines.append(f"- **Total Words:** {transcript_summary.get('total_words', 0)}")
        report_lines.append(f"- **Speaking Pace:** {transcript_summary.get('words_per_minute', 0):.1f} words/minute")
        report_lines.append("")

        # Divider before evaluation
        report_lines.append("---\n")

        # Claude's creator feedback
        report_lines.append("## Production Feedback & Recommendations\n")
        report_lines.append(evaluation)
        report_lines.append("")

        # Footer
        report_lines.append("\n---")
        report_lines.append(f"\n*Creator feedback report generated on {timestamp}*")
        report_lines.append(f"\n*This report is for CREATORS to improve production quality and pedagogical effectiveness.*")

        # Write report to file
        safe_name = self._sanitize_filename(video_name)
        report_filename = f"{safe_name}_creator_feedback.md"
        report_path = os.path.join(self.output_dir, report_filename)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"✓ Creator report saved: {report_path}")
        return report_path


def process_video(
    video_path: str,
    frame_extractor: FrameExtractor,
    audio_transcriber: AudioTranscriber,
    evaluator: VideoEvaluatorClaudeCode,
    report_generator: CreatorReportGenerator,
    frames_per_batch: int,
    temp_dir: str
) -> tuple:
    """
    Process a single video for creator feedback

    Returns:
        Tuple of (video_name, report_path, processing_time)
    """
    video_name = Path(video_path).stem
    start_time = time.time()

    logger.info(f"\n{'='*80}")
    logger.info(f"ANALYZING: {video_name}")
    logger.info(f"{'='*80}\n")

    # Create temp directory for this video
    video_temp_dir = os.path.join(temp_dir, video_name)
    frames_dir = os.path.join(video_temp_dir, 'frames')
    os.makedirs(frames_dir, exist_ok=True)

    try:
        # Step 1: Extract frames
        logger.info("Step 1/4: Extracting video frames...")
        all_frames = frame_extractor.extract_frames(video_path, frames_dir)

        # Sample frames if we have too many
        if len(all_frames) > frames_per_batch:
            logger.info(f"Sampling {frames_per_batch} frames from {len(all_frames)} total...")
            selected_frames = frame_extractor.sample_frames_evenly(all_frames, frames_per_batch)
        else:
            selected_frames = all_frames

        logger.info(f"Using {len(selected_frames)} frames for analysis\n")

        # Step 2: Transcribe audio
        logger.info("Step 2/4: Transcribing audio with Whisper...")
        transcript_result = audio_transcriber.transcribe_video(video_path, video_temp_dir)
        transcript_formatted = audio_transcriber.format_transcript_for_claude(transcript_result)
        transcript_summary = audio_transcriber.get_transcript_summary(transcript_result)
        logger.info("")

        # Step 3: Evaluate with Claude (using creator rubric)
        logger.info("Step 3/4: Getting creator feedback from Claude...")
        evaluation = evaluator.evaluate_with_retry(
            selected_frames,
            transcript_formatted,
            video_name
        )
        logger.info("")

        # Step 4: Generate report
        logger.info("Step 4/4: Generating creator feedback report...")
        processing_time = time.time() - start_time
        report_path = report_generator.generate_report(
            video_name=video_name,
            video_path=video_path,
            evaluation=evaluation,
            transcript_summary=transcript_summary,
            num_frames=len(selected_frames),
            processing_time=processing_time
        )

        logger.info(f"\n✓ Creator feedback complete in {processing_time:.1f} seconds")

        return (video_name, report_path, processing_time)

    except Exception as e:
        logger.error(f"✗ Error analyzing video: {e}")
        raise

    finally:
        # Keep transcripts, but clean up frames
        frames_dir = os.path.join(video_temp_dir, 'frames')
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir)
            logger.info(f"Cleaned up frame files (transcript saved)")


def main():
    parser = argparse.ArgumentParser(
        description='Generate creator feedback for educational videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all videos in default videos/ folder
  python evaluate_creator.py

  # Analyze YouTube video
  python evaluate_creator.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"

  # Analyze videos from custom directory
  python evaluate_creator.py --videos-dir /path/to/my/videos

  # Use more frames for detailed production analysis
  python evaluate_creator.py --frames-per-batch 50

This tool provides CREATOR-FOCUSED feedback on:
  - Script quality and educational content design
  - Production quality (audio, visual, editing)
  - Pedagogical effectiveness and teaching techniques
  - Engagement strategies and retention
  - Specific, timestamp-based improvement recommendations
        """
    )

    parser.add_argument(
        '--videos-dir',
        type=str,
        default='videos',
        help='Directory containing videos to analyze (default: videos/)'
    )

    parser.add_argument(
        '--youtube',
        type=str,
        help='YouTube URL to download and analyze (alternative to --videos-dir)'
    )

    parser.add_argument(
        '--frames-per-batch',
        type=int,
        default=30,
        help='Maximum frames to analyze per video (default: 30)'
    )

    parser.add_argument(
        '--frame-interval',
        type=int,
        default=2,
        help='Extract 1 frame every N seconds (default: 2)'
    )

    parser.add_argument(
        '--whisper-model',
        type=str,
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model size (default: base)'
    )

    args = parser.parse_args()

    # Handle YouTube URL if provided
    if args.youtube:
        logger.info("YouTube URL provided - downloading video first...")
        try:
            downloader = YouTubeDownloader(download_dir='downloaded_videos')
            if not downloader.is_youtube_url(args.youtube):
                logger.error(f"Invalid YouTube URL: {args.youtube}")
                return 1

            downloaded_path = downloader.download(args.youtube)
            video_files = [downloaded_path]
            logger.info(f"✓ Video ready for analysis: {Path(downloaded_path).name}\n")

        except Exception as e:
            logger.error(f"Failed to download YouTube video: {e}")
            return 1

    else:
        # Validate videos directory
        if not os.path.isdir(args.videos_dir):
            logger.error(f"Videos directory not found: {args.videos_dir}")
            logger.info(f"Creating directory: {args.videos_dir}")
            os.makedirs(args.videos_dir, exist_ok=True)
            logger.info("Please add video files to this directory and run again.")
            return 1

        # Find videos
        video_files = find_videos(args.videos_dir)
        if not video_files:
            logger.error(f"No video files found in {args.videos_dir}")
            logger.info(f"Supported formats: {', '.join(VIDEO_EXTENSIONS)}")
            return 1

        logger.info(f"Found {len(video_files)} video(s) for creator analysis:")
        for i, vf in enumerate(video_files, 1):
            logger.info(f"  {i}. {Path(vf).name}")
        logger.info("")

    # Initialize components with creator rubric
    try:
        logger.info("Initializing creator analysis components...")
        frame_extractor = FrameExtractor(interval_seconds=args.frame_interval)
        audio_transcriber = AudioTranscriber(model_name=args.whisper_model)

        # Use creator rubric
        from src.evaluator import VideoEvaluator
        from src.rubric_creator import get_creator_evaluation_prompt

        # Patch the evaluator to use creator rubric
        evaluator = VideoEvaluator()
        evaluator._original_build = evaluator._build_evaluation_prompt
        evaluator._build_evaluation_prompt = lambda transcript, video_name, num_frames: \
            _build_creator_prompt(transcript, video_name, num_frames)

        report_generator = CreatorReportGenerator(output_dir='output/reports')
        logger.info("✓ Creator analysis components initialized\n")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return 1

    # Process videos
    temp_dir = 'output/temp'
    os.makedirs(temp_dir, exist_ok=True)

    video_reports = []
    total_start_time = time.time()
    successful = 0
    failed = 0

    for i, video_path in enumerate(video_files, 1):
        logger.info(f"\n[Video {i}/{len(video_files)}]")
        try:
            result = process_video(
                video_path,
                frame_extractor,
                audio_transcriber,
                evaluator,
                report_generator,
                args.frames_per_batch,
                temp_dir
            )
            video_reports.append(result[:2])  # (name, report_path)
            successful += 1

        except KeyboardInterrupt:
            logger.warning("\n\nAnalysis interrupted by user")
            break

        except Exception as e:
            logger.error(f"Failed to analyze {Path(video_path).name}: {e}")
            failed += 1
            continue

    # Generate summary report
    total_time = time.time() - total_start_time

    if video_reports:
        logger.info(f"\n{'='*80}")
        logger.info("Generating summary report...")
        summary_path = report_generator.generate_summary_report(
            video_reports,
            total_time
        )

    # Final summary
    logger.info(f"\n{'='*80}")
    logger.info("CREATOR ANALYSIS COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total time: {total_time / 60:.1f} minutes")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"\nCreator feedback reports saved to: output/reports/")

    return 0 if failed == 0 else 1


def _build_creator_prompt(transcript: str, video_name: str, num_frames: int) -> str:
    """Build prompt with creator rubric"""
    from src.rubric_creator import get_creator_evaluation_prompt
    rubric_prompt = get_creator_evaluation_prompt()

    prompt = f"""# Creator Feedback Analysis

VIDEO: {video_name}
FRAMES ANALYZED: {num_frames} frames (sampled at regular intervals)

{rubric_prompt}

---

## VIDEO TRANSCRIPT

{transcript}

---

## YOUR TASK

Provide comprehensive CREATOR FEEDBACK following the framework above. Be specific with timestamps, actionable with recommendations, and constructive in tone.

Focus on helping the creator improve both THIS video and FUTURE videos.
"""
    return prompt


if __name__ == '__main__':
    sys.exit(main())
