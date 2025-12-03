"""
Gemini Flash-based video evaluator using Google's Generative AI API
Free tier: 1,500 requests per day with native vision support
"""

import os
import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path
import base64

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .base import VideoEvaluator
from ..cost_tracker import calculate_cost, log_evaluation_cost

logger = logging.getLogger(__name__)


class GeminiEvaluator(VideoEvaluator):
    """
    Evaluator using Google's Gemini Flash API.

    Uses single-pass evaluation with all frames analyzed together.
    Free tier: 1,500 requests/day, 1M tokens/minute.
    """

    def __init__(
        self,
        rubric_name: str,
        rubric_prompt: str,
        model_name: str = "models/gemini-2.5-flash",
        sampling_strategy: str = "even",
        max_frames: int = 50,
        timeout: int = 600
    ):
        """
        Initialize Gemini evaluator.

        Args:
            rubric_name: Name of rubric (e.g., "content_safety", "ai_quality")
            rubric_prompt: Full rubric prompt text
            model_name: Gemini model identifier (default: models/gemini-2.5-flash)
            sampling_strategy: Frame sampling strategy
            max_frames: Maximum frames to send (Gemini can handle many frames)
            timeout: Evaluation timeout in seconds
        """
        super().__init__(
            evaluator_name="gemini-flash",
            rubric_name=rubric_name,
            model_name=model_name,
            version="1.0.0"
        )

        if genai is None:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )

        self.rubric_prompt = rubric_prompt
        self.sampling_strategy = sampling_strategy
        self.max_frames = max_frames
        self.timeout = timeout

        self._configure_gemini()

    def _configure_gemini(self):
        """Configure Gemini API with API key"""
        api_key = os.environ.get('GEMINI_API_KEY')

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable not set. "
                "Get your free API key from: https://aistudio.google.com/app/apikey\n"
                "Then set it: export GEMINI_API_KEY='your-key-here'"
            )

        genai.configure(api_key=api_key)
        logger.info(f"✓ Gemini API configured")
        logger.info(f"✓ Model: {self.model_name}")

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
        Evaluate video using Gemini Flash API.

        Args:
            video_id: Video identifier
            frames: List of frame file paths
            transcript: Formatted transcript text
            metadata: Video metadata from ingestion

        Returns:
            Evaluation result dictionary
        """
        start_time = datetime.now()

        # Sample frames
        selected_frames = self.sample_frames(
            frames,
            sampling_strategy=self.sampling_strategy,
            max_frames=self.max_frames
        )

        logger.info(f"Evaluating {video_id} with Gemini Flash")
        logger.info(f"  Model: {self.model_name}")
        logger.info(f"  Frames: {len(selected_frames)}/{len(frames)}")
        logger.info(f"  Rubric: {self.rubric_name}")

        # Build prompt and call Gemini
        try:
            evaluation_text, usage_metadata = self._call_gemini(
                video_id=video_id,
                frame_paths=selected_frames,
                transcript=transcript,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Gemini evaluation failed: {e}")
            raise

        # Log cost
        if usage_metadata:
            input_tokens = usage_metadata.get("prompt_token_count", 0)
            output_tokens = usage_metadata.get("candidates_token_count", 0)
            cost = calculate_cost(self.model_name, input_tokens, output_tokens)

            logger.info(f"  Tokens: {input_tokens:,} in / {output_tokens:,} out")
            logger.info(f"  Cost: ${cost:.4f}")

            log_evaluation_cost(
                model=self.model_name,
                video_id=video_id,
                rubric=self.rubric_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost
            )

        # Calculate metrics
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

        logger.info(f"✓ Gemini evaluation complete in {processing_time:.1f}s")

        return result

    def _call_gemini(
        self,
        video_id: str,
        frame_paths: List[str],
        transcript: str,
        metadata: Dict
    ) -> tuple:
        """
        Call Gemini API with frames and transcript.

        Args:
            video_id: Video identifier
            frame_paths: List of frame file paths
            transcript: Video transcript
            metadata: Video metadata

        Returns:
            Tuple of (evaluation_text, usage_metadata)
        """
        # Load frame images
        logger.info("  Loading frame images...")
        frame_images = []
        for frame_path in frame_paths:
            try:
                with open(frame_path, 'rb') as f:
                    image_data = f.read()
                    # Gemini accepts PIL Images or raw bytes
                    frame_images.append({
                        'mime_type': 'image/jpeg',
                        'data': image_data
                    })
            except Exception as e:
                logger.warning(f"  Failed to load frame {frame_path}: {e}")
                continue

        if not frame_images:
            raise RuntimeError("No frames could be loaded")

        logger.info(f"  Loaded {len(frame_images)} frame images")

        # Build prompt
        duration = metadata.get('duration_seconds', 'unknown')

        prompt_text = f"""# Video Evaluation Task

VIDEO ID: {video_id}
DURATION: {duration} seconds
FRAMES: {len(frame_images)} frames extracted at regular intervals

## Instructions

You are analyzing {len(frame_images)} frames from this video along with its transcript. These frames represent the full video at regular intervals.

## EVALUATION RUBRIC

{self.rubric_prompt}

---

## VIDEO TRANSCRIPT

{transcript}

---

## Your Task

Analyze all {len(frame_images)} frames shown above along with the transcript to provide a comprehensive evaluation following the rubric framework exactly.

1. Review all frames to understand the full video content
2. Analyze both visual content and transcript together
3. Provide specific examples with timestamps
4. Follow the rubric's output format requirements precisely

Please provide a thorough evaluation following the rubric framework.
"""

        # Build content list for Gemini (interleave text and images)
        content = [prompt_text]
        content.extend(frame_images)

        # Call Gemini API
        logger.info("  Calling Gemini Flash API...")
        call_start = datetime.now()

        try:
            model = genai.GenerativeModel(self.model_name)

            # Disable safety filters for educational content evaluation
            # This tool evaluates children's content quality - the rubric discusses
            # content concerns which can trigger false positives
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            response = model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=16384,
                    temperature=0.7,
                ),
                safety_settings=safety_settings
            )

            call_duration = (datetime.now() - call_start).total_seconds()
            logger.info(f"  ✓ Gemini API call completed in {call_duration:.1f}s")

            # Check for blocked responses
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = response.candidates[0].finish_reason
                # finish_reason 2 = SAFETY blocked
                if finish_reason == 2:
                    safety_ratings = response.candidates[0].safety_ratings if response.candidates[0].safety_ratings else []
                    blocked_categories = [r.category.name for r in safety_ratings if r.blocked]
                    raise RuntimeError(
                        f"Response blocked by safety filters. Categories: {blocked_categories}. "
                        "Try simplifying the rubric or video content."
                    )

            if not response.text:
                raise RuntimeError("Gemini returned empty response")

            # Extract usage metadata
            usage_metadata = None
            if hasattr(response, 'usage_metadata'):
                usage_metadata = {
                    "prompt_token_count": response.usage_metadata.prompt_token_count,
                    "candidates_token_count": response.usage_metadata.candidates_token_count,
                    "total_token_count": response.usage_metadata.total_token_count
                }

            return response.text, usage_metadata

        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")
