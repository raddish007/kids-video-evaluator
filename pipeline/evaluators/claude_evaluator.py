"""
Claude-based video evaluator using Claude Code CLI
Supports multiple rubrics with configurable settings
"""

import subprocess
import os
import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path

from .base import VideoEvaluator
from ..cost_tracker import calculate_cost, log_evaluation_cost

logger = logging.getLogger(__name__)


class ClaudeEvaluator(VideoEvaluator):
    """
    Evaluator using Claude API via Claude Code CLI.

    Uses the 'claude' command-line tool to analyze frames and transcript
    according to specified rubric.
    """

    def __init__(
        self,
        rubric_name: str,
        rubric_prompt: str,
        model_name: str = "claude-sonnet-4-20250514",
        sampling_strategy: str = "even",
        max_frames: int = 30,
        timeout: int = 600
    ):
        """
        Initialize Claude evaluator.

        Args:
            rubric_name: Name of rubric (e.g., "content_safety", "ai_quality")
            rubric_prompt: Full rubric prompt text
            model_name: Claude model identifier
            sampling_strategy: Frame sampling strategy ("even", "all", "first_n", "last_n")
            max_frames: Maximum number of frames to send
            timeout: Evaluation timeout in seconds (default: 10 minutes)
        """
        super().__init__(
            evaluator_name="claude-cli",
            rubric_name=rubric_name,
            model_name=model_name,
            version="1.0.0"
        )

        self.rubric_prompt = rubric_prompt
        self.sampling_strategy = sampling_strategy
        # Claude API has a hard limit of 100 images per request
        self.max_frames = min(max_frames, 100)
        self.timeout = timeout

        if max_frames > 100:
            logger.warning(f"Requested {max_frames} frames, but Claude API limit is 100. Capping at 100.")

        self._verify_claude_cli()

    def _verify_claude_cli(self):
        """Verify that Claude CLI is available"""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"✓ Claude Code CLI found: {result.stdout.strip()}")
            else:
                raise RuntimeError("Claude CLI not working properly")
        except FileNotFoundError:
            raise RuntimeError(
                "Claude CLI not found. Please ensure Claude Code is installed."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI check timed out")

    def get_rubric(self) -> str:
        """Return the rubric prompt"""
        return self.rubric_prompt

    def evaluate(
        self,
        video_id: str,
        frames: List[str],
        transcript: str,
        metadata: Dict
    ) -> Dict:
        """
        Evaluate video using Claude CLI.

        Args:
            video_id: Video identifier
            frames: List of frame file paths
            transcript: Formatted transcript text
            metadata: Video metadata from ingestion

        Returns:
            Evaluation result dictionary
        """
        start_time = datetime.now()

        # Sample frames according to strategy
        selected_frames = self.sample_frames(
            frames,
            sampling_strategy=self.sampling_strategy,
            max_frames=self.max_frames
        )

        logger.info(f"Evaluating {video_id} with {len(selected_frames)}/{len(frames)} frames")
        logger.info(f"  Rubric: {self.rubric_name}")
        logger.info(f"  Model: {self.model_name}")

        # Build prompt
        prompt = self._build_prompt(
            video_id=video_id,
            frame_paths=selected_frames,
            transcript=transcript,
            metadata=metadata
        )

        # Call Claude
        try:
            evaluation_text = self._call_claude_cli(prompt)
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            raise

        # Estimate token usage (Claude CLI doesn't return exact counts)
        # Rough approximation: ~4 characters per token
        input_tokens = len(prompt) // 4
        output_tokens = len(evaluation_text) // 4
        cost = calculate_cost(self.model_name, input_tokens, output_tokens)

        logger.info(f"  Tokens (estimated): {input_tokens:,} in / {output_tokens:,} out")
        logger.info(f"  Cost (estimated): ${cost:.4f}")

        log_evaluation_cost(
            model=self.model_name,
            video_id=video_id,
            rubric=self.rubric_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost
        )

        # Calculate performance metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Build result
        result = {
            "video_id": video_id,
            "evaluator": self.evaluator_name,
            "rubric": self.rubric_name,
            "model": self.model_name,
            "timestamp": datetime.now().isoformat(),
            "evaluation_markdown": evaluation_text,
            "metadata": {
                "video_metadata": metadata,
                "frames_analyzed": len(selected_frames),
                "total_frames_available": len(frames),
                "sampling_strategy": self.sampling_strategy,
                "transcript_word_count": len(transcript.split())
            },
            "performance_metrics": {
                "processing_time_seconds": processing_time,
                "frames_processed": len(selected_frames)
            }
        }

        logger.info(f"✓ Evaluation complete in {processing_time:.1f}s")

        return result

    def _build_prompt(
        self,
        video_id: str,
        frame_paths: List[str],
        transcript: str,
        metadata: Dict
    ) -> str:
        """Build evaluation prompt for Claude"""

        # Convert to absolute paths
        abs_frame_paths = [os.path.abspath(p) for p in frame_paths]

        # Get video duration from metadata
        duration = metadata.get('duration_seconds', 'unknown')

        prompt = f"""# Video Evaluation Task

VIDEO ID: {video_id}
DURATION: {duration} seconds
FRAMES: {len(frame_paths)} frames extracted at regular intervals

## Instructions

I have extracted {len(frame_paths)} frames from this video. Please read and analyze ALL of these frames along with the transcript below.

**IMPORTANT**: First, use the Read tool to view each of these image files:

"""

        # Add frame paths
        for i, frame_path in enumerate(abs_frame_paths, 1):
            prompt += f"{i}. {frame_path}\n"

        prompt += f"""
After reading all {len(frame_paths)} frames, analyze them along with the transcript to provide a comprehensive evaluation.

---

## EVALUATION RUBRIC

{self.rubric_prompt}

---

## VIDEO TRANSCRIPT

{transcript}

---

## Your Task

1. First, read all {len(frame_paths)} frame images using the Read tool
2. Then analyze them comprehensively using the evaluation framework above
3. Provide specific examples with timestamps from the transcript
4. Follow the rubric's output format requirements exactly

Please provide a thorough evaluation following the rubric framework.
"""

        return prompt

    def _call_claude_cli(self, prompt: str) -> str:
        """
        Call Claude CLI with prompt.

        Args:
            prompt: Full evaluation prompt

        Returns:
            Claude's response text
        """
        logger.info("  Calling Claude Code CLI...")

        try:
            result = subprocess.run(
                [
                    'claude',
                    '--print',
                    '--dangerously-skip-permissions',
                    prompt
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.getcwd()
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"  Claude CLI error: {error_msg}")
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            response = result.stdout.strip()

            if not response:
                raise RuntimeError("Claude returned empty response")

            logger.info("  ✓ Claude evaluation complete")
            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude evaluation timed out after {self.timeout}s")
        except Exception as e:
            raise RuntimeError(f"Error calling Claude: {e}")
