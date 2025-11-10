"""
Claude-based video evaluation using Claude Code CLI
Uses the Read tool to analyze images from disk
"""
import subprocess
import os
import json
import logging
from pathlib import Path
from typing import List
from .rubric import get_evaluation_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoEvaluatorClaudeCode:
    def __init__(self):
        """Initialize Claude Code evaluator"""
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

    def evaluate_video(
        self,
        frame_paths: List[str],
        transcript: str,
        video_name: str
    ) -> str:
        """
        Evaluate video using Claude Code with frames and transcript

        Args:
            frame_paths: List of paths to frame images
            transcript: Formatted transcript text
            video_name: Name of video being evaluated

        Returns:
            Claude's evaluation response
        """
        logger.info(f"Evaluating video: {video_name}")
        logger.info(f"  Analyzing {len(frame_paths)} frames with Claude Code")

        # Build the prompt that asks Claude to read the images
        prompt = self._build_evaluation_prompt_with_read_instructions(
            frame_paths, transcript, video_name
        )

        try:
            logger.info("  Calling Claude Code CLI...")

            # Call Claude with --print mode and bypass permissions for Read tool
            result = subprocess.run(
                [
                    'claude',
                    '--print',
                    '--dangerously-skip-permissions',
                    prompt
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for analysis
                cwd=os.getcwd()
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"  Claude CLI stderr: {result.stderr}")
                logger.error(f"  Claude CLI stdout: {result.stdout}")
                logger.error(f"  Return code: {result.returncode}")
                raise RuntimeError(f"Claude Code CLI failed: {error_msg}")

            response = result.stdout.strip()
            logger.info("  ✓ Claude evaluation complete")

            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude evaluation timed out after 10 minutes")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling Claude: {e}")

    def _build_evaluation_prompt_with_read_instructions(
        self,
        frame_paths: List[str],
        transcript: str,
        video_name: str
    ) -> str:
        """Build prompt that instructs Claude to read the images"""
        rubric_prompt = get_evaluation_prompt()

        # Convert paths to absolute paths
        abs_frame_paths = [os.path.abspath(p) for p in frame_paths]

        # Create the prompt
        prompt = f"""# Educational Video Evaluation Task

VIDEO: {video_name}
FRAMES: {len(frame_paths)} frames extracted at regular intervals

## Instructions

I have extracted {len(frame_paths)} frames from this educational video. Please read and analyze ALL of these frames along with the transcript below.

**IMPORTANT**: First, use the Read tool to view each of these image files:

"""

        # Add each frame path for Claude to read
        for i, frame_path in enumerate(abs_frame_paths, 1):
            prompt += f"{i}. {frame_path}\n"

        prompt += f"""
After reading all {len(frame_paths)} frames, analyze them along with the transcript to provide a comprehensive evaluation.

---

{rubric_prompt}

---

## VIDEO TRANSCRIPT

{transcript}

---

## Your Task

1. First, read all {len(frame_paths)} frame images using the Read tool
2. Then analyze them comprehensively using the evaluation framework above
3. Provide specific examples with timestamps from the transcript
4. Give actionable feedback for parents

Please provide a thorough evaluation following the rubric framework.
"""
        return prompt

    def evaluate_with_retry(
        self,
        frame_paths: List[str],
        transcript: str,
        video_name: str,
        max_retries: int = 2
    ) -> str:
        """
        Evaluate video with retry logic

        Args:
            frame_paths: Paths to frame images
            transcript: Formatted transcript
            video_name: Video name
            max_retries: Maximum number of retry attempts

        Returns:
            Evaluation response
        """
        for attempt in range(max_retries + 1):
            try:
                return self.evaluate_video(frame_paths, transcript, video_name)
            except subprocess.TimeoutExpired:
                if attempt < max_retries:
                    logger.warning(f"  Attempt {attempt + 1} timed out, retrying...")
                else:
                    raise RuntimeError("Claude evaluation timed out after all retries")
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"  Attempt {attempt + 1} failed: {e}, retrying...")
                else:
                    raise
