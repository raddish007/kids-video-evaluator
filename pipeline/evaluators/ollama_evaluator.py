"""
Ollama-based video evaluator using local vision models
Uses batch-then-synthesize approach for handling multiple frames
"""

import logging
from typing import List, Dict
from datetime import datetime
from pathlib import Path

try:
    import ollama
except ImportError:
    ollama = None

from .base import VideoEvaluator

logger = logging.getLogger(__name__)


class OllamaEvaluator(VideoEvaluator):
    """
    Evaluator using Ollama local vision models.

    Uses batch-then-synthesize approach:
    1. Split frames into batches
    2. Analyze each batch with vision model (focused prompts)
    3. Synthesize all partial analyses into final report (text model)
    """

    def __init__(
        self,
        rubric_name: str,
        rubric_prompt: str,
        vision_model: str = "llava:34b",
        synthesis_model: str = "llama3.1:8b-instruct",
        batch_size: int = 8,
        sampling_strategy: str = "even",
        max_frames: int = 50
    ):
        """
        Initialize Ollama evaluator.

        Args:
            rubric_name: Name of rubric (e.g., "content_safety", "ai_quality")
            rubric_prompt: Full rubric prompt text
            vision_model: Ollama vision model (e.g., "llava:34b", "llava:13b", "phi3.5-vision")
            synthesis_model: Text model for final synthesis (e.g., "llama3.1:8b-instruct")
            batch_size: Number of frames per batch (6-10 recommended)
            sampling_strategy: Frame sampling strategy
            max_frames: Maximum frames to analyze
        """
        super().__init__(
            evaluator_name=f"ollama-{vision_model.split(':')[0]}",
            rubric_name=rubric_name,
            model_name=vision_model,
            version="1.0.0"
        )

        if ollama is None:
            raise ImportError("ollama package not installed. Run: pip install ollama")

        self.rubric_prompt = rubric_prompt
        self.vision_model = vision_model
        self.synthesis_model = synthesis_model
        self.batch_size = batch_size
        self.sampling_strategy = sampling_strategy
        self.max_frames = max_frames

        self._verify_ollama()

    def _verify_ollama(self):
        """Verify Ollama is running and models are available"""
        try:
            # Check if Ollama is running
            models = ollama.list()
            logger.info(f"✓ Ollama server connected")

            # Check if vision model is available
            model_names = [m.model for m in models.get('models', [])]
            if self.vision_model not in model_names:
                logger.warning(f"Vision model '{self.vision_model}' not found locally")
                logger.warning(f"Available models: {', '.join(model_names)}")
                logger.warning(f"Download with: ollama pull {self.vision_model}")
            else:
                logger.info(f"✓ Vision model found: {self.vision_model}")

            # Check if synthesis model is available
            if self.synthesis_model not in model_names:
                logger.warning(f"Synthesis model '{self.synthesis_model}' not found locally")
                logger.warning(f"Download with: ollama pull {self.synthesis_model}")
            else:
                logger.info(f"✓ Synthesis model found: {self.synthesis_model}")

        except Exception as e:
            raise RuntimeError(
                f"Could not connect to Ollama server. "
                f"Make sure Ollama is running: ollama serve\n"
                f"Error: {e}"
            )

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
        Evaluate video using Ollama batch-then-synthesize approach.

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

        logger.info(f"Evaluating {video_id} with Ollama")
        logger.info(f"  Vision model: {self.vision_model}")
        logger.info(f"  Synthesis model: {self.synthesis_model}")
        logger.info(f"  Frames: {len(selected_frames)}/{len(frames)}")
        logger.info(f"  Batch size: {self.batch_size}")

        # Step 1: Batch frames and analyze each batch
        logger.info(f"  Step 1: Analyzing frame batches...")
        partial_analyses = self._analyze_batches(selected_frames, transcript, metadata)
        logger.info(f"  ✓ Completed {len(partial_analyses)} batch analyses")

        # Step 2: Synthesize into final report
        logger.info(f"  Step 2: Synthesizing final evaluation...")
        final_evaluation = self._synthesize_evaluation(
            video_id=video_id,
            partial_analyses=partial_analyses,
            transcript=transcript,
            metadata=metadata
        )
        logger.info(f"  ✓ Synthesis complete")

        # Calculate metrics
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Build result
        result = {
            "video_id": video_id,
            "evaluator": self.evaluator_name,
            "rubric": self.rubric_name,
            "model": self.vision_model,
            "timestamp": datetime.now().isoformat(),
            "evaluation_markdown": final_evaluation,
            "metadata": {
                "video_metadata": metadata,
                "frames_analyzed": len(selected_frames),
                "total_frames_available": len(frames),
                "sampling_strategy": self.sampling_strategy,
                "batch_size": self.batch_size,
                "num_batches": len(partial_analyses),
                "vision_model": self.vision_model,
                "synthesis_model": self.synthesis_model,
                "transcript_word_count": len(transcript.split())
            },
            "performance_metrics": {
                "processing_time_seconds": processing_time,
                "frames_processed": len(selected_frames),
                "batches_processed": len(partial_analyses)
            }
        }

        logger.info(f"✓ Ollama evaluation complete in {processing_time:.1f}s")

        return result

    def _analyze_batches(
        self,
        frames: List[str],
        transcript: str,
        metadata: Dict
    ) -> List[Dict]:
        """
        Analyze frames in batches using vision model.

        Args:
            frames: List of frame paths
            transcript: Video transcript
            metadata: Video metadata

        Returns:
            List of partial analysis results
        """
        batches = self._create_batches(frames)
        partial_analyses = []

        for i, batch in enumerate(batches, 1):
            batch_start = datetime.now()
            logger.info(f"    Batch {i}/{len(batches)}: {len(batch)} frames")

            try:
                analysis = self._analyze_single_batch(
                    batch_num=i,
                    total_batches=len(batches),
                    frame_paths=batch,
                    video_duration=metadata.get('duration_seconds', 'unknown')
                )

                batch_duration = (datetime.now() - batch_start).total_seconds()
                logger.info(f"      ✓ Batch {i} completed in {batch_duration:.1f}s")

                partial_analyses.append({
                    'batch_num': i,
                    'frames': batch,
                    'analysis': analysis
                })

            except Exception as e:
                logger.error(f"    Batch {i} failed: {e}")
                # Continue with other batches
                partial_analyses.append({
                    'batch_num': i,
                    'frames': batch,
                    'analysis': f"[Batch analysis failed: {e}]"
                })

        return partial_analyses

    def _create_batches(self, frames: List[str]) -> List[List[str]]:
        """Split frames into batches"""
        batches = []
        for i in range(0, len(frames), self.batch_size):
            batch = frames[i:i + self.batch_size]
            batches.append(batch)
        return batches

    def _analyze_single_batch(
        self,
        batch_num: int,
        total_batches: int,
        frame_paths: List[str],
        video_duration: float
    ) -> str:
        """
        Analyze a single batch of frames for content safety.

        Uses focused prompt for quick analysis of key safety concerns.
        """
        prompt = f"""You are analyzing batch {batch_num} of {total_batches} from a children's educational video (duration: {video_duration}s).

I will show you {len(frame_paths)} frames. Analyze them for CONTENT SAFETY and AGE-APPROPRIATENESS.

Focus on identifying:
1. **Violence**: Any physical aggression, fighting, or harmful behavior
2. **Fear/Scary Content**: Frightening characters, monsters, scary visuals, dark threatening scenes
3. **Inappropriate Content**: Sexual content, drugs, alcohol, or other inappropriate elements
4. **Language Concerns**: Any visible text with profanity, crude language, or inappropriate messaging
5. **Discrimination**: Stereotypes, biased representations, or exclusionary content
6. **Dangerous Behaviors**: Activities children might imitate dangerously
7. **Visual Stimulation**: Color intensity, visual complexity, overly stimulating elements

For each concern you find, note:
- What you see
- Severity (none/mild/moderate/significant)
- Which frame(s) show it

If frames are appropriate and safe, say so clearly.

Be thorough but concise. This is a partial analysis that will be combined with other batches.
"""

        # Call vision model with batch of frames
        try:
            response = ollama.chat(
                model=self.vision_model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': frame_paths
                }]
            )

            return response['message']['content']

        except Exception as e:
            logger.error(f"Ollama vision call failed: {e}")
            raise

    def _synthesize_evaluation(
        self,
        video_id: str,
        partial_analyses: List[Dict],
        transcript: str,
        metadata: Dict
    ) -> str:
        """
        Synthesize partial analyses into final rubric-compliant evaluation.

        Uses text model to combine insights from all batches.
        """
        synthesis_start = datetime.now()

        # Build synthesis prompt
        synthesis_prompt = self._build_synthesis_prompt(
            video_id=video_id,
            partial_analyses=partial_analyses,
            transcript=transcript,
            metadata=metadata
        )

        prompt_length = len(synthesis_prompt)
        logger.info(f"    Built synthesis prompt ({prompt_length:,} chars, ~{prompt_length//4:,} tokens)")

        # Call text model for synthesis
        try:
            logger.info(f"    Calling {self.synthesis_model} for synthesis...")
            call_start = datetime.now()

            response = ollama.chat(
                model=self.synthesis_model,
                messages=[{
                    'role': 'user',
                    'content': synthesis_prompt
                }]
            )

            call_duration = (datetime.now() - call_start).total_seconds()
            synthesis_duration = (datetime.now() - synthesis_start).total_seconds()
            response_length = len(response['message']['content'])

            logger.info(f"    ✓ Synthesis API call completed in {call_duration:.1f}s")
            logger.info(f"    ✓ Total synthesis time: {synthesis_duration:.1f}s")
            logger.info(f"    ✓ Response length: {response_length:,} chars")

            return response['message']['content']

        except Exception as e:
            logger.error(f"Ollama synthesis call failed: {e}")
            raise

    def _build_synthesis_prompt(
        self,
        video_id: str,
        partial_analyses: List[Dict],
        transcript: str,
        metadata: Dict
    ) -> str:
        """Build comprehensive synthesis prompt"""

        duration = metadata.get('duration_seconds', 'unknown')
        total_frames = len([f for batch in partial_analyses for f in batch['frames']])

        prompt = f"""# Video Evaluation Synthesis Task

You are synthesizing multiple partial analyses into a comprehensive content rating evaluation.

VIDEO ID: {video_id}
DURATION: {duration} seconds
TOTAL FRAMES ANALYZED: {total_frames} frames across {len(partial_analyses)} batches

---

## PARTIAL VISUAL ANALYSES

"""

        # Add each batch analysis
        for batch_data in partial_analyses:
            batch_num = batch_data['batch_num']
            analysis = batch_data['analysis']
            prompt += f"""
### Batch {batch_num} Analysis:
{analysis}

"""

        prompt += f"""
---

## VIDEO TRANSCRIPT

{transcript}

---

## YOUR TASK

Using the visual analyses above AND the transcript, create a COMPREHENSIVE content rating evaluation following this rubric:

{self.rubric_prompt}

---

## IMPORTANT INSTRUCTIONS

1. **Combine visual and transcript analysis**: Use both the frame analyses above AND the transcript content
2. **Follow the rubric format exactly**: Provide all sections as specified in the rubric
3. **Be specific with evidence**: Reference specific batch findings and transcript quotes
4. **Estimate timestamps**: Based on batch numbers and video duration, estimate timestamps for concerning content
5. **Provide complete ratings**: Include all required sections, metrics, and ratings from the rubric
6. **Be thorough**: This is the final evaluation - make it comprehensive and actionable

Create the full evaluation now, following the rubric structure precisely.
"""

        return prompt
