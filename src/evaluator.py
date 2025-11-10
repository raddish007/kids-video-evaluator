"""
Claude-based video evaluation using Anthropic SDK
"""
import os
import base64
import logging
from pathlib import Path
from typing import List
import anthropic
from .rubric import get_evaluation_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoEvaluator:
    def __init__(self, api_key: str = None):
        """
        Initialize Claude evaluator using Anthropic SDK

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
        """
        # Get API key from environment or parameter
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise RuntimeError(
                "Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.\n"
                "Get your API key from: https://console.anthropic.com/settings/keys"
            )

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("✓ Claude API client initialized")

    def evaluate_video(
        self,
        frame_paths: List[str],
        transcript: str,
        video_name: str
    ) -> str:
        """
        Evaluate video using Claude with frames and transcript

        Args:
            frame_paths: List of paths to frame images
            transcript: Formatted transcript text
            video_name: Name of video being evaluated

        Returns:
            Claude's evaluation response
        """
        logger.info(f"Evaluating video: {video_name}")
        logger.info(f"  Sending {len(frame_paths)} frames to Claude API")

        # Build the text prompt
        text_prompt = self._build_evaluation_prompt(transcript, video_name, len(frame_paths))

        # Build message content with images
        content = []

        # Add all frame images first
        for i, frame_path in enumerate(frame_paths):
            image_data = self._encode_image(frame_path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": image_data,
                }
            })

        # Add the text prompt last
        content.append({
            "type": "text",
            "text": text_prompt
        })

        try:
            logger.info("  Calling Claude API...")

            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Latest Sonnet model
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            )

            # Extract text from response
            result_text = response.content[0].text
            logger.info("  ✓ Claude evaluation complete")

            return result_text

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling Claude API: {e}")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API"""
        with open(image_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')

    def _build_evaluation_prompt(self, transcript: str, video_name: str, num_frames: int) -> str:
        """Build the complete evaluation prompt"""
        rubric_prompt = get_evaluation_prompt()

        prompt = f"""# Educational Video Evaluation Task

VIDEO: {video_name}
FRAMES PROVIDED: {num_frames} frames (sampled from video at regular intervals)

{rubric_prompt}

---

## VIDEO TRANSCRIPT

{transcript}

---

## ATTACHED IMAGES

I've attached {num_frames} frame images from the video, sampled at regular intervals throughout the video duration. Please analyze these frames along with the transcript to provide your evaluation.

Please provide a comprehensive evaluation following the framework above. Be specific, cite timestamps from the transcript, and provide actionable feedback for parents.
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
            except anthropic.RateLimitError as e:
                if attempt < max_retries:
                    logger.warning(f"  Attempt {attempt + 1} hit rate limit, waiting and retrying...")
                    import time
                    time.sleep(5)  # Wait 5 seconds before retry
                else:
                    raise RuntimeError("Claude API rate limit exceeded after all retries")
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"  Attempt {attempt + 1} failed: {e}, retrying...")
                else:
                    raise
