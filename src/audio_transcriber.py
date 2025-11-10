"""
Audio transcription using OpenAI Whisper (local model)
"""
import whisper
import os
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioTranscriber:
    def __init__(self, model_name: str = "base"):
        """
        Initialize Whisper transcriber

        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
                - tiny: Fastest, least accurate (~1GB RAM)
                - base: Good balance for testing (~1GB RAM)
                - small: Better accuracy (~2GB RAM)
                - medium: High accuracy (~5GB RAM)
                - large: Best accuracy (~10GB RAM)
        """
        self.model_name = model_name
        logger.info(f"Loading Whisper model: {model_name}")
        self.model = whisper.load_model(model_name)
        logger.info(f"✓ Whisper model '{model_name}' loaded")

    def transcribe_video(self, video_path: str, output_dir: str = None) -> dict:
        """
        Transcribe audio from video file

        Args:
            video_path: Path to video file
            output_dir: Optional directory to save transcript JSON

        Returns:
            Dictionary containing transcript with timestamps
        """
        logger.info(f"Transcribing audio from: {Path(video_path).name}")

        # Transcribe with word-level timestamps
        result = self.model.transcribe(
            video_path,
            word_timestamps=True,
            verbose=False
        )

        logger.info(f"  ✓ Transcription complete")
        logger.info(f"  Detected language: {result.get('language', 'unknown')}")
        logger.info(f"  Text length: {len(result['text'])} characters")

        # Save transcript if output directory provided
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            video_name = Path(video_path).stem
            transcript_path = os.path.join(output_dir, f"{video_name}_transcript.json")

            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"  ✓ Transcript saved to: {transcript_path}")

        return result

    def format_transcript_for_claude(self, transcript_result: dict) -> str:
        """
        Format Whisper transcript for Claude analysis

        Args:
            transcript_result: Raw Whisper transcription result

        Returns:
            Formatted transcript string with timestamps
        """
        formatted_lines = []
        formatted_lines.append("=== VIDEO TRANSCRIPT ===\n")

        # Add full text first
        formatted_lines.append("FULL TEXT:")
        formatted_lines.append(transcript_result['text'].strip())
        formatted_lines.append("\n")

        # Add segments with timestamps
        formatted_lines.append("TIMESTAMPED SEGMENTS:")
        for segment in transcript_result.get('segments', []):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            text = segment['text'].strip()
            formatted_lines.append(f"[{start_time} - {end_time}] {text}")

        return "\n".join(formatted_lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def get_transcript_summary(self, transcript_result: dict) -> dict:
        """
        Get summary statistics about the transcript

        Args:
            transcript_result: Whisper transcription result

        Returns:
            Dictionary with summary stats
        """
        total_words = len(transcript_result['text'].split())
        num_segments = len(transcript_result.get('segments', []))
        duration = transcript_result.get('segments', [{}])[-1].get('end', 0) if num_segments > 0 else 0

        return {
            'total_words': total_words,
            'num_segments': num_segments,
            'duration_seconds': duration,
            'language': transcript_result.get('language', 'unknown'),
            'words_per_minute': (total_words / duration * 60) if duration > 0 else 0
        }
