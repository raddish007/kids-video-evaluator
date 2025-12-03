#!/usr/bin/env python3
"""
Quick test of the evaluation pipeline
Tests Content Rating evaluation on an ingested video
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.evaluators.claude_evaluator import ClaudeEvaluator
from src.rubric_content_safety import get_content_safety_rubric

def test_evaluation():
    print("="*80)
    print("TESTING EVALUATION PIPELINE")
    print("="*80)

    # Use the first available video
    video_id = "wQ2cIAbpRhs"  # YouTube video

    print(f"\nVideo ID: {video_id}")
    print(f"Rubric: content_safety")
    print(f"Model: claude-sonnet-4-20250514")

    # Load rubric
    print("\n1. Loading rubric...")
    rubric_prompt = get_content_safety_rubric()
    print(f"   ✓ Rubric loaded ({len(rubric_prompt)} characters)")

    # Initialize evaluator
    print("\n2. Initializing evaluator...")
    evaluator = ClaudeEvaluator(
        rubric_name="content_safety",
        rubric_prompt=rubric_prompt,
        model_name="claude-sonnet-4-20250514",
        sampling_strategy="even",
        max_frames=20,  # Use fewer frames for quick test
        timeout=600
    )
    print(f"   ✓ Evaluator initialized: {evaluator}")

    # Load video data
    print("\n3. Loading video data...")
    try:
        video_data = evaluator.load_video_data(video_id)
        print(f"   ✓ Video data loaded")
        print(f"     - Frames available: {len(video_data['frames'])}")
        print(f"     - Transcript words: {len(video_data['transcript'].split())}")
        print(f"     - Duration: {video_data['metadata'].get('duration_seconds', 0):.1f}s")
    except FileNotFoundError as e:
        print(f"   ✗ Error: {e}")
        print("\n   Available videos:")
        data_dir = Path(__file__).parent / "data"
        for vdir in sorted(data_dir.iterdir()):
            if vdir.is_dir() and not vdir.name.startswith('.'):
                print(f"     - {vdir.name}")
        return False

    # Run evaluation
    print("\n4. Running evaluation...")
    print("   (This will take 1-2 minutes...)")

    try:
        result = evaluator.evaluate(
            video_id=video_id,
            frames=video_data['frames'],
            transcript=video_data['transcript'],
            metadata=video_data['metadata']
        )
        print(f"   ✓ Evaluation complete!")
        print(f"     - Processing time: {result['performance_metrics']['processing_time_seconds']:.1f}s")
        print(f"     - Frames analyzed: {result['metadata']['frames_analyzed']}")

    except Exception as e:
        print(f"   ✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Save evaluation
    print("\n5. Saving evaluation...")
    video_dir = Path(__file__).parent / "data" / video_id
    output_dir = video_dir / "evaluations"

    saved_path = evaluator.save_evaluation(
        video_id=video_id,
        evaluation_result=result,
        output_dir=output_dir
    )
    print(f"   ✓ Saved to: {saved_path}")

    # Show preview
    print("\n6. Evaluation preview:")
    print("-"*80)
    eval_text = result['evaluation_markdown']
    preview = eval_text[:800] + "..." if len(eval_text) > 800 else eval_text
    print(preview)
    print("-"*80)

    print("\n" + "="*80)
    print("✓ TEST COMPLETE!")
    print("="*80)
    print(f"\nFull evaluation saved to:")
    print(f"  {saved_path}")
    print(f"\nYou can now:")
    print(f"  1. View full evaluation in the saved JSON file")
    print(f"  2. Run the Streamlit UI: python3 -m streamlit run evaluate_ui.py")
    print(f"  3. Run CLI tool: python3 pipeline/evaluate_video.py --video-id {video_id} --rubric content_safety")

    return True

if __name__ == '__main__':
    success = test_evaluation()
    sys.exit(0 if success else 1)
