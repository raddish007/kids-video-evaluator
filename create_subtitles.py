#!/usr/bin/env python3
"""
Subtitle Generation Tool
Creates transcript and SRT subtitle files from video using Whisper
"""
import os
import sys
import argparse
from pathlib import Path
from src.audio_transcriber import AudioTranscriber


def format_srt_timestamp(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format: HH:MM:SS,mmm

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def create_srt_file(transcript_result: dict, output_path: str) -> None:
    """
    Create an SRT subtitle file from Whisper transcript

    Args:
        transcript_result: Whisper transcription result with segments
        output_path: Path where to save the SRT file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for idx, segment in enumerate(transcript_result.get('segments', []), start=1):
            # SRT index
            f.write(f"{idx}\n")

            # Timestamps
            start_time = format_srt_timestamp(segment['start'])
            end_time = format_srt_timestamp(segment['end'])
            f.write(f"{start_time} --> {end_time}\n")

            # Text content
            text = segment['text'].strip()
            f.write(f"{text}\n")

            # Blank line between subtitles
            f.write("\n")


def create_transcript_file(transcript_result: dict, output_path: str) -> None:
    """
    Create a plain text transcript file with timestamps

    Args:
        transcript_result: Whisper transcription result
        output_path: Path where to save the transcript
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== VIDEO TRANSCRIPT ===\n\n")

        # Full text
        f.write("FULL TEXT:\n")
        f.write(transcript_result['text'].strip())
        f.write("\n\n")

        # Timestamped segments
        f.write("TIMESTAMPED SEGMENTS:\n")
        for segment in transcript_result.get('segments', []):
            start_time = format_timestamp_readable(segment['start'])
            end_time = format_timestamp_readable(segment['end'])
            text = segment['text'].strip()
            f.write(f"[{start_time} - {end_time}] {text}\n")


def format_timestamp_readable(seconds: float) -> str:
    """Format seconds to readable MM:SS format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def process_video(video_path: str, model_name: str = "base",
                  subtitle_dir: str = "subtitles",
                  transcript_dir: str = "transcripts") -> None:
    """
    Process a video file to create transcript and subtitle files

    Args:
        video_path: Path to the video file
        model_name: Whisper model size (tiny, base, small, medium, large)
        subtitle_dir: Directory to save subtitle files
        transcript_dir: Directory to save transcript files
    """
    # Validate video file
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    video_path_obj = Path(video_path)
    video_name = video_path_obj.stem

    # Create output directories
    os.makedirs(subtitle_dir, exist_ok=True)
    os.makedirs(transcript_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Processing: {video_path_obj.name}")
    print(f"{'='*60}\n")

    # Initialize transcriber
    print(f"Loading Whisper model: {model_name}")
    transcriber = AudioTranscriber(model_name=model_name)

    # Transcribe video
    print(f"\nTranscribing audio...")
    transcript_result = transcriber.transcribe_video(video_path)

    # Create output file paths
    srt_path = os.path.join(subtitle_dir, f"{video_name}.srt")
    transcript_path = os.path.join(transcript_dir, f"{video_name}_transcript.txt")

    # Generate SRT file
    print(f"\nCreating subtitle file...")
    create_srt_file(transcript_result, srt_path)
    print(f"✓ Subtitles saved: {srt_path}")

    # Generate transcript file
    print(f"\nCreating transcript file...")
    create_transcript_file(transcript_result, transcript_path)
    print(f"✓ Transcript saved: {transcript_path}")

    # Print summary
    summary = transcriber.get_transcript_summary(transcript_result)
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Language: {summary['language']}")
    print(f"Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"Total words: {summary['total_words']}")
    print(f"Segments: {summary['num_segments']}")
    print(f"Words per minute: {summary['words_per_minute']:.1f}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate transcripts and SRT subtitles from video files using Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default model (medium)
  python create_subtitles.py video.mp4

  # Use a faster model
  python create_subtitles.py video.mp4 --model base

  # Custom output directories
  python create_subtitles.py video.mp4 --subtitle-dir subs --transcript-dir transcripts

Whisper Models (accuracy vs speed):
  - tiny:   Fastest, least accurate (~1GB RAM)
  - base:   Good balance (~1GB RAM)
  - small:  Better accuracy (~2GB RAM)
  - medium: High accuracy (default) (~5GB RAM)
  - large:  Best accuracy (~10GB RAM)
        """
    )

    parser.add_argument(
        'video',
        help='Path to the video file'
    )

    parser.add_argument(
        '--model',
        default='medium',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model size (default: medium)'
    )

    parser.add_argument(
        '--subtitle-dir',
        default='subtitles',
        help='Directory to save subtitle files (default: subtitles)'
    )

    parser.add_argument(
        '--transcript-dir',
        default='transcripts',
        help='Directory to save transcript files (default: transcripts)'
    )

    args = parser.parse_args()

    # Process the video
    process_video(
        video_path=args.video,
        model_name=args.model,
        subtitle_dir=args.subtitle_dir,
        transcript_dir=args.transcript_dir
    )


if __name__ == "__main__":
    main()
