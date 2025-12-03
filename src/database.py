"""
Database module for Video Evaluator using Supabase.

Provides type-safe interfaces for storing and retrieving video metadata,
evaluation results, and rubric information.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================
# ENUMS
# ============================================

class EvaluationStatus(str, Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# DATA MODELS
# ============================================

@dataclass
class Video:
    """Video metadata model."""
    id: str
    title: str
    filename: str
    filepath: str
    duration_seconds: Optional[float] = None
    frame_count: Optional[int] = None
    has_transcript: bool = False
    youtube_id: Optional[str] = None
    youtube_url: Optional[str] = None
    ingestion_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion."""
        data = asdict(self)
        # Convert datetime to ISO string
        if self.ingestion_date:
            data['ingestion_date'] = self.ingestion_date.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data


@dataclass
class Evaluation:
    """Evaluation result model."""
    video_id: str
    rubric_name: str
    status: EvaluationStatus
    evaluator: Optional[str] = None
    model_name: Optional[str] = None
    version: int = 1  # Version number for multiple runs
    cost: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase insertion."""
        data = asdict(self)
        # Convert enum to string
        data['status'] = self.status.value if isinstance(self.status, EvaluationStatus) else self.status
        # Convert datetime to ISO string
        for field in ['started_at', 'completed_at', 'created_at', 'updated_at']:
            if data.get(field):
                data[field] = data[field].isoformat() if isinstance(data[field], datetime) else data[field]
        # Remove None id for inserts
        if data.get('id') is None:
            del data['id']
        return data


@dataclass
class Rubric:
    """Rubric definition model."""
    name: str
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    sort_order: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================
# DATABASE CLIENT
# ============================================

class VideoEvaluatorDB:
    """Supabase database client for Video Evaluator."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase API key (defaults to SUPABASE_KEY env var)
        """
        self.url = supabase_url or os.getenv("SUPABASE_URL")
        self.key = supabase_key or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials not found. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them to the constructor."
            )

        self.client: Client = create_client(self.url, self.key)

    # ============================================
    # VIDEOS
    # ============================================

    def create_video(self, video: Video) -> Dict[str, Any]:
        """
        Create a new video record.

        Args:
            video: Video object to create

        Returns:
            Created video data from database
        """
        response = self.client.table("videos").insert(video.to_dict()).execute()
        return response.data[0] if response.data else {}

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video by ID.

        Args:
            video_id: Video ID to retrieve

        Returns:
            Video data or None if not found
        """
        response = self.client.table("videos").select("*").eq("id", video_id).execute()
        return response.data[0] if response.data else None

    def get_all_videos(self, order_by: str = "ingestion_date", ascending: bool = False) -> List[Dict[str, Any]]:
        """
        Get all videos.

        Args:
            order_by: Field to sort by
            ascending: Sort order (default: descending)

        Returns:
            List of video records
        """
        query = self.client.table("videos").select("*")
        response = query.order(order_by, desc=not ascending).execute()
        return response.data

    def update_video(self, video_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a video record.

        Args:
            video_id: Video ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated video data
        """
        response = self.client.table("videos").update(updates).eq("id", video_id).execute()
        return response.data[0] if response.data else {}

    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video and all its evaluations (CASCADE).

        Args:
            video_id: Video ID to delete

        Returns:
            True if successful
        """
        response = self.client.table("videos").delete().eq("id", video_id).execute()
        return len(response.data) > 0

    def video_exists(self, video_id: str) -> bool:
        """Check if a video exists in the database."""
        return self.get_video(video_id) is not None

    # ============================================
    # EVALUATIONS
    # ============================================

    def create_evaluation(self, evaluation: Evaluation) -> Dict[str, Any]:
        """
        Create a new evaluation record.

        Args:
            evaluation: Evaluation object to create

        Returns:
            Created evaluation data
        """
        response = self.client.table("evaluations").insert(evaluation.to_dict()).execute()
        return response.data[0] if response.data else {}

    def get_evaluation(self, video_id: str, rubric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get an evaluation by video ID and rubric name.

        Args:
            video_id: Video ID
            rubric_name: Rubric name

        Returns:
            Evaluation data or None if not found
        """
        response = (
            self.client.table("evaluations")
            .select("*")
            .eq("video_id", video_id)
            .eq("rubric_name", rubric_name)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_video_evaluations(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get all evaluations for a video.

        Args:
            video_id: Video ID

        Returns:
            List of evaluation records
        """
        response = self.client.table("evaluations").select("*").eq("video_id", video_id).execute()
        return response.data

    def get_evaluations_by_status(self, status: EvaluationStatus) -> List[Dict[str, Any]]:
        """
        Get all evaluations with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of evaluation records
        """
        response = self.client.table("evaluations").select("*").eq("status", status.value).execute()
        return response.data

    def update_evaluation(
        self,
        video_id: str,
        rubric_name: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an evaluation record.

        Args:
            video_id: Video ID
            rubric_name: Rubric name
            updates: Dictionary of fields to update

        Returns:
            Updated evaluation data
        """
        response = (
            self.client.table("evaluations")
            .update(updates)
            .eq("video_id", video_id)
            .eq("rubric_name", rubric_name)
            .execute()
        )
        return response.data[0] if response.data else {}

    def upsert_evaluation(self, evaluation: Evaluation) -> Dict[str, Any]:
        """
        Insert a new evaluation version (auto-increments version number).

        Args:
            evaluation: Evaluation object to insert

        Returns:
            Inserted evaluation data
        """
        # Get the next version number
        next_version = self.get_next_version(evaluation.video_id, evaluation.rubric_name)
        evaluation.version = next_version

        # Insert as new record
        response = (
            self.client.table("evaluations")
            .insert(evaluation.to_dict())
            .execute()
        )
        return response.data[0] if response.data else {}

    def get_next_version(self, video_id: str, rubric_name: str) -> int:
        """
        Get the next version number for a video+rubric combination.

        Args:
            video_id: Video ID
            rubric_name: Rubric name

        Returns:
            Next version number (1 if no existing evaluations)
        """
        response = (
            self.client.table("evaluations")
            .select("version")
            .eq("video_id", video_id)
            .eq("rubric_name", rubric_name)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]["version"] + 1
        return 1

    def get_latest_evaluation(self, video_id: str, rubric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest version of an evaluation.

        Args:
            video_id: Video ID
            rubric_name: Rubric name

        Returns:
            Latest evaluation data or None
        """
        response = (
            self.client.table("evaluations")
            .select("*")
            .eq("video_id", video_id)
            .eq("rubric_name", rubric_name)
            .order("version", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_all_evaluation_versions(self, video_id: str, rubric_name: str) -> List[Dict[str, Any]]:
        """
        Get all versions of an evaluation.

        Args:
            video_id: Video ID
            rubric_name: Rubric name

        Returns:
            List of all evaluation versions, newest first
        """
        response = (
            self.client.table("evaluations")
            .select("*")
            .eq("video_id", video_id)
            .eq("rubric_name", rubric_name)
            .order("version", desc=True)
            .execute()
        )
        return response.data

    def evaluation_exists(self, video_id: str, rubric_name: str) -> bool:
        """Check if an evaluation exists."""
        return self.get_evaluation(video_id, rubric_name) is not None

    # ============================================
    # RUBRICS
    # ============================================

    def get_all_rubrics(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all rubrics.

        Args:
            active_only: Only return active rubrics

        Returns:
            List of rubric records
        """
        query = self.client.table("rubrics").select("*")
        if active_only:
            query = query.eq("is_active", True)
        response = query.order("sort_order").execute()
        return response.data

    def get_rubric(self, rubric_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a rubric by name.

        Args:
            rubric_name: Rubric name

        Returns:
            Rubric data or None if not found
        """
        response = self.client.table("rubrics").select("*").eq("name", rubric_name).execute()
        return response.data[0] if response.data else None

    # ============================================
    # VIEWS & AGGREGATIONS
    # ============================================

    def get_video_status(self, video_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get video status with evaluation aggregations.

        Args:
            video_id: Optional video ID to filter by

        Returns:
            List of video status records from the view
        """
        query = self.client.table("video_status").select("*")
        if video_id:
            query = query.eq("id", video_id)
        response = query.order("ingestion_date", desc=True).execute()
        return response.data

    def get_rubric_completion_stats(self) -> List[Dict[str, Any]]:
        """
        Get completion statistics for all rubrics.

        Returns:
            List of rubric completion stats from the view
        """
        response = self.client.table("rubric_completion_stats").select("*").execute()
        return response.data

    def get_recent_evaluations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent evaluation activity.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of recent evaluation records
        """
        response = (
            self.client.table("recent_evaluations")
            .select("*")
            .limit(limit)
            .execute()
        )
        return response.data

    # ============================================
    # UTILITIES
    # ============================================

    def get_total_cost(self, video_id: Optional[str] = None) -> float:
        """
        Get total cost of evaluations.

        Args:
            video_id: Optional video ID to filter by

        Returns:
            Total cost in dollars
        """
        query = self.client.table("evaluations").select("cost")
        if video_id:
            query = query.eq("video_id", video_id)
        response = query.execute()

        total = sum(row.get("cost", 0) or 0 for row in response.data)
        return round(total, 4)

    def health_check(self) -> bool:
        """
        Check if database connection is working.

        Returns:
            True if connection is healthy
        """
        try:
            response = self.client.table("rubrics").select("count", count="exact").limit(1).execute()
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def get_db() -> VideoEvaluatorDB:
    """Get a database client instance."""
    return VideoEvaluatorDB()


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Example usage
    db = get_db()

    # Health check
    if db.health_check():
        print("✓ Database connection successful")

        # Get all videos
        videos = db.get_all_videos()
        print(f"\nFound {len(videos)} videos")

        # Get rubrics
        rubrics = db.get_all_rubrics()
        print(f"Found {len(rubrics)} active rubrics")

        # Get video status
        status = db.get_video_status()
        print(f"\nVideo status overview: {len(status)} videos")
        for v in status[:3]:
            print(f"  - {v['title']}: {v['completed_count']}/{v['total_evaluations']} evaluations complete")

        # Get total cost
        total_cost = db.get_total_cost()
        print(f"\nTotal evaluation cost: ${total_cost:.4f}")
    else:
        print("✗ Database connection failed")
        print("Make sure SUPABASE_URL and SUPABASE_KEY are set in your .env file")
