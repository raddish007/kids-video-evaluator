"""
Base Evaluator Class - Abstract interface for all video evaluators
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime


class VideoEvaluator(ABC):
    """
    Abstract base class for video evaluators.

    All evaluators must implement:
    - evaluate() method to perform the evaluation
    - get_rubric() method to return the rubric text

    Evaluators can customize:
    - Frame sampling strategy
    - Model/provider configuration
    - Evaluation parameters
    """

    def __init__(
        self,
        evaluator_name: str,
        rubric_name: str,
        model_name: str = None,
        version: str = "1.0.0"
    ):
        """
        Initialize base evaluator.

        Args:
            evaluator_name: Name of the evaluator (e.g., "claude-api", "ollama-llava")
            rubric_name: Name of the rubric (e.g., "content_safety", "ai_quality")
            model_name: Specific model identifier (e.g., "claude-sonnet-4-20250514")
            version: Evaluator version for tracking
        """
        self.evaluator_name = evaluator_name
        self.rubric_name = rubric_name
        self.model_name = model_name
        self.version = version

    @abstractmethod
    def evaluate(
        self,
        video_id: str,
        frames: List[str],
        transcript: str,
        metadata: Dict
    ) -> Dict:
        """
        Evaluate a video using this evaluator's strategy.

        Args:
            video_id: Video identifier
            frames: List of frame file paths to analyze
            transcript: Formatted transcript text
            metadata: Video metadata from ingestion

        Returns:
            Dictionary containing evaluation results with structure:
            {
                "video_id": str,
                "evaluator": str,
                "rubric": str,
                "model": str,
                "timestamp": str (ISO format),
                "evaluation_markdown": str,  # Full evaluation text
                "metadata": {...},  # Additional evaluator-specific data
                "performance_metrics": {...}  # Optional performance data
            }
        """
        pass

    @abstractmethod
    def get_rubric(self) -> str:
        """
        Return the rubric text for this evaluator.

        Returns:
            Rubric prompt as string
        """
        pass

    def sample_frames(
        self,
        all_frames: List[str],
        sampling_strategy: str = "even",
        max_frames: int = 30
    ) -> List[str]:
        """
        Sample frames according to strategy.

        Args:
            all_frames: List of all available frame paths
            sampling_strategy: Strategy to use ("even", "all", "first_n", "last_n")
            max_frames: Maximum number of frames to return

        Returns:
            List of selected frame paths
        """
        if len(all_frames) <= max_frames:
            return all_frames

        if sampling_strategy == "even":
            # Sample evenly across the video
            step = len(all_frames) / max_frames
            indices = [int(i * step) for i in range(max_frames)]
            return [all_frames[i] for i in indices]

        elif sampling_strategy == "first_n":
            return all_frames[:max_frames]

        elif sampling_strategy == "last_n":
            return all_frames[-max_frames:]

        elif sampling_strategy == "all":
            return all_frames

        else:
            raise ValueError(f"Unknown sampling strategy: {sampling_strategy}")

    def save_evaluation(
        self,
        video_id: str,
        evaluation_result: Dict,
        output_dir: Path
    ) -> str:
        """
        Save evaluation result to JSON file.

        Args:
            video_id: Video identifier
            evaluation_result: Result dictionary from evaluate()
            output_dir: Directory to save evaluation (typically data/<video_id>/evaluations/)

        Returns:
            Path to saved evaluation file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create filename: <evaluator>_<rubric>_<timestamp>.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.evaluator_name}_{self.rubric_name}_{timestamp}.json"
        filepath = output_dir / filename

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_video_data(self, video_id: str, data_dir: Path = None) -> Dict:
        """
        Load ingested video data (metadata, transcript, frames).

        Args:
            video_id: Video identifier
            data_dir: Base data directory (defaults to ./data)

        Returns:
            Dictionary with:
            {
                "metadata": {...},
                "transcript": str,
                "transcript_data": {...},
                "frames": [list of frame paths],
                "video_dir": Path
            }
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            data_dir = Path(data_dir)

        video_dir = data_dir / video_id

        if not video_dir.exists():
            raise FileNotFoundError(f"Video directory not found: {video_dir}")

        # Load metadata
        metadata_path = video_dir / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Load transcript text
        transcript_txt_path = video_dir / "transcript.txt"
        if not transcript_txt_path.exists():
            raise FileNotFoundError(f"Transcript not found: {transcript_txt_path}")

        with open(transcript_txt_path, 'r', encoding='utf-8') as f:
            transcript = f.read()

        # Load full transcript data (with timestamps)
        transcript_json_path = video_dir / "transcript.json"
        transcript_data = None
        if transcript_json_path.exists():
            with open(transcript_json_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)

        # Get frames
        frames_dir = video_dir / "frames"
        if not frames_dir.exists():
            raise FileNotFoundError(f"Frames directory not found: {frames_dir}")

        frames = sorted([str(f) for f in frames_dir.glob("*.jpg")])

        if not frames:
            raise FileNotFoundError(f"No frames found in: {frames_dir}")

        return {
            "metadata": metadata,
            "transcript": transcript,
            "transcript_data": transcript_data,
            "frames": frames,
            "video_dir": str(video_dir)
        }

    def __repr__(self):
        return f"{self.__class__.__name__}(evaluator={self.evaluator_name}, rubric={self.rubric_name}, model={self.model_name})"
