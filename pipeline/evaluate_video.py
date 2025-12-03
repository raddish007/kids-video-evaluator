#!/usr/bin/env python3
"""
Evaluate Video CLI - Phase 2 Evaluation Pipeline

Evaluates ingested videos using specified rubric and evaluator.

Usage:
    python pipeline/evaluate_video.py --video-id VIDEO_ID --rubric content_safety
"""

import argparse
import sys
import logging
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass  # dotenv not installed, rely on shell environment

from pipeline.evaluators.claude_evaluator import ClaudeEvaluator
from pipeline.evaluators.gemini_evaluator import GeminiEvaluator
from src.rubric_content_safety import get_content_safety_rubric
from src.rubric_ai_quality import get_ai_quality_rubric
from src.rubric_production_metrics import get_production_metrics_rubric
from src.rubric_media_ethics import get_media_ethics_rubric
from src.rubric_academic import get_academic_rubric
from src.rubric_fourPillars import get_brainrot_rubric

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
  # Evaluate with content safety rubric
  python pipeline/evaluate_video.py --video-id MyClip --rubric content_safety

  # Evaluate with production metrics
  python pipeline/evaluate_video.py --video-id MyClip --rubric production_metrics

  # Evaluate media ethics
  python pipeline/evaluate_video.py --video-id MyClip --rubric media_ethics

  # Evaluate with academic rubric (4-pillar pedagogical quality)
  python pipeline/evaluate_video.py --video-id MyClip --rubric academic

  # Use Gemini instead of Claude
  python pipeline/evaluate_video.py --video-id MyClip --rubric academic --evaluator gemini

  # Use custom frame sampling
  python pipeline/evaluate_video.py --video-id dQw4w9WgXcQ --rubric ai_quality --max-frames 50

  # Use different sampling strategy
  python pipeline/evaluate_video.py --video-id MyClip --rubric production_metrics --sampling all
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
        choices=['content_safety', 'ai_quality', 'production_metrics', 'media_ethics', 'academic', 'four_pillars'],
        default='four_pillars',
        help='Evaluation rubric to use (default: four_pillars)'
    )

    parser.add_argument(
        '--evaluator',
        type=str,
        choices=['claude', 'gemini'],
        default='claude',
        help='Evaluator to use: claude or gemini (default: claude)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model to use. Claude: claude-sonnet-4-20250514 (default), claude-opus-4-5-20251101, claude-3-5-sonnet-20241022, claude-3-haiku-20240307. Gemini: models/gemini-2.5-flash (default), models/gemini-2.5-pro'
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

    # Set default model based on evaluator
    if args.model is None:
        if args.evaluator == 'gemini':
            args.model = 'models/gemini-2.5-flash'
        else:
            args.model = 'claude-sonnet-4-20250514'

    logger.info(f"{'='*80}")
    logger.info(f"VIDEO EVALUATION")
    logger.info(f"{'='*80}")
    logger.info(f"Video ID: {args.video_id}")
    logger.info(f"Rubric: {args.rubric}")
    logger.info(f"Evaluator: {args.evaluator}")
    logger.info(f"Model: {args.model}")
    logger.info(f"Sampling: {args.sampling} (max {args.max_frames} frames)")
    logger.info(f"")

    try:
        # Load rubric
        logger.info("Loading rubric...")
        if args.rubric == 'content_safety':
            rubric_prompt = get_content_safety_rubric()
        elif args.rubric == 'ai_quality':
            rubric_prompt = get_ai_quality_rubric()
        elif args.rubric == 'production_metrics':
            rubric_prompt = get_production_metrics_rubric()
        elif args.rubric == 'media_ethics':
            rubric_prompt = get_media_ethics_rubric()
        elif args.rubric == 'academic':
            rubric_prompt = get_academic_rubric()
        elif args.rubric == 'four_pillars':
            rubric_prompt = get_brainrot_rubric()
        else:
            logger.error(f"Unknown rubric: {args.rubric}")
            return 1

        # Initialize evaluator
        logger.info(f"Initializing {args.evaluator} evaluator...")
        if args.evaluator == 'gemini':
            evaluator = GeminiEvaluator(
                rubric_name=args.rubric,
                rubric_prompt=rubric_prompt,
                model_name=args.model,
                sampling_strategy=args.sampling,
                max_frames=args.max_frames,
                timeout=args.timeout
            )
        else:
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
