#!/usr/bin/env python3
"""
Kids Video Evaluator - Main CLI Entry Point

Analyzes children's educational videos by extracting frames and transcribing audio,
then uses Claude to evaluate educational quality against a comprehensive rubric.

Usage:
    python evaluate.py [--videos-dir PATH] [--frames-per-batch N] [--frame-interval N] [--whisper-model MODEL]

Examples:
    # Process all videos in default 'videos' folder
    python evaluate.py

    # Specify custom videos directory
    python evaluate.py --videos-dir /path/to/videos

    # Send 40 frames to Claude, extract 1 frame every 3 seconds, use medium Whisper
    python evaluate.py --frames-per-batch 40 --frame-interval 3 --whisper-model medium
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


def process_video(
    video_path: str,
    frame_extractor: FrameExtractor,
    audio_transcriber: AudioTranscriber,
    evaluator: VideoEvaluatorClaudeCode,
    report_generator: ReportGenerator,
    frames_per_batch: int,
    temp_dir: str
) -> tuple:
    """
    Process a single video: extract frames, transcribe, evaluate

    Returns:
        Tuple of (video_name, report_path, processing_time)
    """
    video_name = Path(video_path).stem
    start_time = time.time()

    logger.info(f"\n{'='*80}")
    logger.info(f"PROCESSING: {video_name}")
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

        # Step 3: Evaluate with Claude
        logger.info("Step 3/4: Evaluating with Claude...")
        evaluation = evaluator.evaluate_with_retry(
            selected_frames,
            transcript_formatted,
            video_name
        )
        logger.info("")

        # Step 4: Generate report
        logger.info("Step 4/4: Generating report...")
        processing_time = time.time() - start_time
        report_path = report_generator.generate_report(
            video_name=video_name,
            video_path=video_path,
            evaluation=evaluation,
            transcript_summary=transcript_summary,
            num_frames=len(selected_frames),
            processing_time=processing_time
        )

        logger.info(f"\n✓ Video processed successfully in {processing_time:.1f} seconds")

        return (video_name, report_path, processing_time)

    except Exception as e:
        logger.error(f"✗ Error processing video: {e}")
        raise

    finally:
        # Keep transcripts, but clean up frames
        frames_dir = os.path.join(video_temp_dir, 'frames')
        if os.path.exists(frames_dir):
            shutil.rmtree(frames_dir)
            logger.info(f"Cleaned up frame files (transcript saved)")


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate educational videos for children',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all videos in default videos/ folder
  python evaluate.py

  # Analyze YouTube video
  python evaluate.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"

  # Process videos from custom directory
  python evaluate.py --videos-dir /path/to/my/videos

  # Use more frames and different Whisper model
  python evaluate.py --frames-per-batch 50 --whisper-model medium

Whisper models (speed vs accuracy):
  - tiny:   Fastest, lowest accuracy
  - base:   Good balance (default)
  - small:  Better accuracy
  - medium: High accuracy, slower
  - large:  Best accuracy, slowest
        """
    )

    parser.add_argument(
        '--videos-dir',
        type=str,
        default='videos',
        help='Directory containing videos to evaluate (default: videos/)'
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
        help='Maximum frames to send to Claude per video (default: 30)'
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

    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep temporary files (frames, transcripts) after processing'
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

        logger.info(f"Found {len(video_files)} video(s) to process:")
        for i, vf in enumerate(video_files, 1):
            logger.info(f"  {i}. {Path(vf).name}")
        logger.info("")

    # Initialize components
    try:
        logger.info("Initializing components...")
        frame_extractor = FrameExtractor(interval_seconds=args.frame_interval)
        audio_transcriber = AudioTranscriber(model_name=args.whisper_model)
        evaluator = VideoEvaluatorClaudeCode()
        report_generator = ReportGenerator(output_dir='output/reports')
        logger.info("✓ All components initialized\n")

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
            logger.warning("\n\nProcess interrupted by user")
            break

        except Exception as e:
            logger.error(f"Failed to process {Path(video_path).name}: {e}")
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
    logger.info("PROCESSING COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total time: {total_time / 60:.1f} minutes")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"\nReports saved to: output/reports/")

    if not args.keep_temp:
        logger.info("Cleaning up temporary files...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
