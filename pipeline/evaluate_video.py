#!/usr/bin/env python3
"""
Evaluate Video CLI - Phase 2 Evaluation Pipeline

Evaluates ingested videos using specified rubric and evaluator.

Usage:
    python pipeline/evaluate_video.py --video-id VIDEO_ID --rubric content_rating
"""

import argparse
import sys
import logging
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.evaluators.claude_evaluator import ClaudeEvaluator
from src.rubric_content_rating import get_content_rating_rubric

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate ingested video with specified rubric',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate with content rating rubric
  python pipeline/evaluate_video.py --video-id MyClip --rubric content_rating

  # Use custom frame sampling
  python pipeline/evaluate_video.py --video-id dQw4w9WgXcQ --rubric content_rating --max-frames 50

  # Use different sampling strategy
  python pipeline/evaluate_video.py --video-id MyClip --rubric content_rating --sampling all
        """
    )

    parser.add_argument(
        '--video-id',
        type=str,
        required=True,
        help='Video ID (directory name in data/)'
    )

    parser.add_argument(
        '--rubric',
        type=str,
        choices=['content_rating'],
        default='content_rating',
        help='Evaluation rubric to use (default: content_rating)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='claude-sonnet-4-20250514',
        help='Claude model to use (default: claude-sonnet-4-20250514)'
    )

    parser.add_argument(
        '--sampling',
        type=str,
        choices=['even', 'all', 'first_n', 'last_n'],
        default='even',
        help='Frame sampling strategy (default: even)'
    )

    parser.add_argument(
        '--max-frames',
        type=int,
        default=30,
        help='Maximum frames to send to evaluator (default: 30)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Evaluation timeout in seconds (default: 600)'
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Base data directory (default: data/)'
    )

    args = parser.parse_args()

    logger.info(f"{'='*80}")
    logger.info(f"VIDEO EVALUATION")
    logger.info(f"{'='*80}")
    logger.info(f"Video ID: {args.video_id}")
    logger.info(f"Rubric: {args.rubric}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Sampling: {args.sampling} (max {args.max_frames} frames)")
    logger.info(f"")

    try:
        # Load rubric
        logger.info("Loading rubric...")
        if args.rubric == 'content_rating':
            rubric_prompt = get_content_rating_rubric()
        else:
            logger.error(f"Unknown rubric: {args.rubric}")
            return 1

        # Initialize evaluator
        logger.info("Initializing evaluator...")
        evaluator = ClaudeEvaluator(
            rubric_name=args.rubric,
            rubric_prompt=rubric_prompt,
            model_name=args.model,
            sampling_strategy=args.sampling,
            max_frames=args.max_frames,
            timeout=args.timeout
        )

        # Load video data
        logger.info("Loading video data...")
        video_data = evaluator.load_video_data(
            video_id=args.video_id,
            data_dir=Path(args.data_dir)
        )

        frames = video_data['frames']
        transcript = video_data['transcript']
        metadata = video_data['metadata']

        logger.info(f"  Frames available: {len(frames)}")
        logger.info(f"  Transcript words: {len(transcript.split())}")
        logger.info(f"  Duration: {metadata.get('duration_seconds', 0):.1f}s")
        logger.info("")

        # Run evaluation
        logger.info("Running evaluation...")
        result = evaluator.evaluate(
            video_id=args.video_id,
            frames=frames,
            transcript=transcript,
            metadata=metadata
        )

        # Save evaluation
        logger.info("Saving evaluation...")
        video_dir = Path(args.data_dir) / args.video_id
        output_dir = video_dir / "evaluations"
        saved_path = evaluator.save_evaluation(
            video_id=args.video_id,
            evaluation_result=result,
            output_dir=output_dir
        )

        logger.info(f"")
        logger.info(f"{'='*80}")
        logger.info(f"EVALUATION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Saved to: {saved_path}")
        logger.info(f"Processing time: {result['performance_metrics']['processing_time_seconds']:.1f}s")
        logger.info(f"Frames analyzed: {result['metadata']['frames_analyzed']}/{result['metadata']['total_frames_available']}")
        logger.info(f"")

        # Print evaluation summary
        logger.info("EVALUATION PREVIEW:")
        logger.info("-" * 80)
        eval_text = result['evaluation_markdown']
        # Print first 500 characters
        preview = eval_text[:500] + "..." if len(eval_text) > 500 else eval_text
        print(preview)
        logger.info("-" * 80)
        logger.info(f"Full evaluation saved to: {saved_path}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error(f"Make sure video '{args.video_id}' has been ingested first")
        return 1

    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
