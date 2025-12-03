#!/usr/bin/env python3
"""
Sync existing video evaluation data to Supabase database.

This script scans the data/videos directory and imports all video metadata
and evaluation results into the Supabase database.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import VideoEvaluatorDB, Video, Evaluation, EvaluationStatus


class DataSyncManager:
    """Manages syncing filesystem data to Supabase database."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize sync manager.

        Args:
            data_dir: Path to data directory (relative to project root)
        """
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / data_dir
        self.db = VideoEvaluatorDB()
        self.stats = {
            "videos_found": 0,
            "videos_created": 0,
            "videos_updated": 0,
            "videos_skipped": 0,
            "evaluations_found": 0,
            "evaluations_created": 0,
            "evaluations_updated": 0,
            "evaluations_skipped": 0,
            "errors": []
        }

    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from various formats."""
        if not timestamp_str:
            return None

        # Try ISO format
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            pass

        # Try other common formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except:
                continue

        return None

    def load_json(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Load JSON file safely."""
        try:
            if not filepath.exists():
                return None
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.stats["errors"].append(f"Error loading {filepath}: {e}")
            return None

    def import_video(self, video_dir: Path) -> bool:
        """
        Import a single video and its evaluations.

        Args:
            video_dir: Path to video directory

        Returns:
            True if successful
        """
        video_id = video_dir.name
        print(f"\n📹 Processing video: {video_id}")

        # Load metadata
        metadata_path = video_dir / "metadata.json"
        metadata = self.load_json(metadata_path)
        if not metadata:
            print(f"  ⚠️  No metadata.json found, skipping")
            self.stats["videos_skipped"] += 1
            return False

        # Load YouTube metadata if available
        youtube_metadata_path = video_dir / "youtube_metadata.json"
        youtube_metadata = self.load_json(youtube_metadata_path)

        # Extract video information
        video_title = "Unknown Video"
        youtube_id = None
        youtube_url = None

        if youtube_metadata:
            video_title = youtube_metadata.get("title", video_title)
            youtube_id = youtube_metadata.get("video_id")
            youtube_url = youtube_metadata.get("url")
        elif metadata.get("youtube_url"):
            youtube_url = metadata.get("youtube_url")
            # Extract video ID from URL
            if "v=" in youtube_url:
                youtube_id = youtube_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in youtube_url:
                youtube_id = youtube_url.split("youtu.be/")[1].split("?")[0]
            video_title = f"YouTube Video: {youtube_id}"

        # Check for local video files to get title
        if video_title == "Unknown Video":
            source_path = video_dir / "source.mp4"
            if source_path.exists():
                video_title = source_path.stem

        # Parse ingestion timestamp
        ingestion_date = None
        if metadata.get("ingestion_timestamp"):
            ingestion_date = self.parse_timestamp(metadata["ingestion_timestamp"])

        # Create Video object
        video = Video(
            id=video_id,
            title=video_title,
            filename=metadata.get("source_path", f"data/{video_id}/source.mp4"),
            filepath=str(video_dir / "source.mp4"),
            duration_seconds=metadata.get("duration_seconds"),
            frame_count=metadata.get("frame_count"),
            has_transcript=bool(metadata.get("transcript_word_count")),
            youtube_id=youtube_id,
            youtube_url=youtube_url,
            ingestion_date=ingestion_date,
            metadata={**metadata, **(youtube_metadata or {})}
        )

        # Insert or update video
        try:
            if self.db.video_exists(video_id):
                self.db.update_video(video_id, video.to_dict())
                print(f"  ✓ Updated video: {video_title}")
                self.stats["videos_updated"] += 1
            else:
                self.db.create_video(video)
                print(f"  ✓ Created video: {video_title}")
                self.stats["videos_created"] += 1
        except Exception as e:
            print(f"  ✗ Error saving video: {e}")
            self.stats["errors"].append(f"Video {video_id}: {e}")
            return False

        # Import evaluations
        evaluations_dir = video_dir / "evaluations"
        if evaluations_dir.exists():
            self.import_evaluations(video_id, evaluations_dir)

        return True

    def extract_rubric_from_filename(self, filename: str) -> Optional[str]:
        """Extract rubric name from evaluation filename."""
        # Expected format: {evaluator}_{rubric}_{timestamp}.json
        # e.g., gemini-flash_ai_quality_20251110_214747.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 2:
            # Find the rubric name (everything between evaluator and timestamp)
            # Known rubrics
            rubrics = [
                'academic', 'four_pillars', 'ai_quality', 'content_safety', 'media_ethics',
                'production_metrics', 'values', 'educational', 'production'
            ]
            for rubric in rubrics:
                if rubric in filename:
                    return rubric
        return None

    def import_evaluations(self, video_id: str, evaluations_dir: Path) -> None:
        """
        Import all evaluations for a video.

        Args:
            video_id: Video ID
            evaluations_dir: Path to evaluations directory
        """
        evaluation_files = list(evaluations_dir.glob("*.json"))
        print(f"  📊 Found {len(evaluation_files)} evaluation(s)")

        for eval_file in evaluation_files:
            self.stats["evaluations_found"] += 1
            eval_data = self.load_json(eval_file)
            if not eval_data:
                continue

            # Extract information from evaluation data
            rubric_name = eval_data.get("rubric") or self.extract_rubric_from_filename(eval_file.name)
            if not rubric_name:
                print(f"    ⚠️  Could not determine rubric for {eval_file.name}, skipping")
                self.stats["evaluations_skipped"] += 1
                continue

            evaluator = eval_data.get("evaluator", "unknown")
            model_name = eval_data.get("model")
            timestamp_str = eval_data.get("timestamp")
            evaluation_markdown = eval_data.get("evaluation_markdown", "")

            # Parse timestamp
            completed_at = None
            if timestamp_str:
                completed_at = self.parse_timestamp(timestamp_str)

            # Extract cost if available
            cost = None
            if "cost_info" in eval_data:
                cost = eval_data["cost_info"].get("total_cost")

            # Calculate duration if available
            duration_seconds = None
            if "performance_metrics" in eval_data:
                duration_seconds = eval_data["performance_metrics"].get("processing_time_seconds")

            # Create summary from markdown (first 200 chars)
            summary = None
            if evaluation_markdown:
                # Extract first few lines
                lines = evaluation_markdown.split('\n')
                summary = ' '.join(lines[:3])[:200] + "..." if len(summary) > 200 else summary

            # Create Evaluation object
            evaluation = Evaluation(
                video_id=video_id,
                rubric_name=rubric_name,
                status=EvaluationStatus.COMPLETED,
                evaluator=evaluator,
                model_name=model_name,
                cost=cost,
                completed_at=completed_at,
                started_at=completed_at,  # Assume started and completed are same for existing data
                duration_seconds=duration_seconds,
                result=eval_data,
                summary=summary
            )

            # Insert or update evaluation
            try:
                if self.db.evaluation_exists(video_id, rubric_name):
                    self.db.update_evaluation(video_id, rubric_name, evaluation.to_dict())
                    print(f"    ✓ Updated: {rubric_name}")
                    self.stats["evaluations_updated"] += 1
                else:
                    self.db.create_evaluation(evaluation)
                    print(f"    ✓ Created: {rubric_name}")
                    self.stats["evaluations_created"] += 1
            except Exception as e:
                print(f"    ✗ Error saving evaluation {rubric_name}: {e}")
                self.stats["errors"].append(f"Evaluation {video_id}/{rubric_name}: {e}")

    def sync_all(self) -> Dict[str, Any]:
        """
        Sync all videos and evaluations from data directory.

        Returns:
            Statistics dictionary
        """
        print(f"🔄 Starting sync from: {self.data_dir}")
        print(f"=" * 60)

        # Check if data directory exists
        if not self.data_dir.exists():
            print(f"❌ Data directory not found: {self.data_dir}")
            print(f"   Make sure you're running this from the video-evaluator directory")
            return self.stats

        # Find all video directories (directories with metadata.json)
        video_dirs = [
            d for d in self.data_dir.iterdir()
            if d.is_dir() and (d / "metadata.json").exists()
        ]

        self.stats["videos_found"] = len(video_dirs)
        print(f"Found {len(video_dirs)} video(s) to sync\n")

        # Import each video
        for video_dir in video_dirs:
            self.import_video(video_dir)

        # Print summary
        print(f"\n{'=' * 60}")
        print(f"✅ Sync Complete!")
        print(f"=" * 60)
        print(f"\n📊 Summary:")
        print(f"  Videos:")
        print(f"    • Found:   {self.stats['videos_found']}")
        print(f"    • Created: {self.stats['videos_created']}")
        print(f"    • Updated: {self.stats['videos_updated']}")
        print(f"    • Skipped: {self.stats['videos_skipped']}")
        print(f"\n  Evaluations:")
        print(f"    • Found:   {self.stats['evaluations_found']}")
        print(f"    • Created: {self.stats['evaluations_created']}")
        print(f"    • Updated: {self.stats['evaluations_updated']}")
        print(f"    • Skipped: {self.stats['evaluations_skipped']}")

        if self.stats["errors"]:
            print(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:10]:  # Show first 10 errors
                print(f"    • {error}")
            if len(self.stats["errors"]) > 10:
                print(f"    ... and {len(self.stats['errors']) - 10} more")

        print(f"\n💾 Database URL: {self.db.url}")
        print(f"   View your data in the Supabase dashboard!")

        return self.stats


def main():
    """Main entry point."""
    print("=" * 60)
    print("📦 Video Evaluator Data Sync")
    print("=" * 60)
    print()

    # Check database connection
    try:
        db = VideoEvaluatorDB()
        if not db.health_check():
            print("❌ Database connection failed!")
            print("   Make sure:")
            print("   1. You've set up your .env file with SUPABASE_URL and SUPABASE_KEY")
            print("   2. You've run the schema.sql in your Supabase project")
            print("   3. Your internet connection is working")
            print()
            print("   See DATABASE_SETUP.md for instructions")
            sys.exit(1)
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("   Check your .env file and database setup")
        sys.exit(1)

    # Run sync
    syncer = DataSyncManager()
    stats = syncer.sync_all()

    # Exit with error code if there were failures
    if stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
