"""
Video frame extraction using OpenCV
"""
import cv2
import os
from pathlib import Path
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FrameExtractor:
    def __init__(self, interval_seconds: int = 2):
        """
        Initialize frame extractor

        Args:
            interval_seconds: Extract one frame every N seconds
        """
        self.interval_seconds = interval_seconds

    def extract_frames(self, video_path: str, output_dir: str, max_frames: int = None) -> List[str]:
        """
        Extract frames from video at specified intervals

        Args:
            video_path: Path to input video file
            output_dir: Directory to save extracted frames
            max_frames: Maximum number of frames to extract (None = no limit)

        Returns:
            List of paths to extracted frame images
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Open video file
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_seconds = total_frames / fps

        logger.info(f"Video: {Path(video_path).name}")
        logger.info(f"  Duration: {duration_seconds:.1f} seconds")
        logger.info(f"  FPS: {fps:.1f}")
        logger.info(f"  Total frames: {total_frames}")

        # Calculate frame interval
        frame_interval = int(fps * self.interval_seconds)
        logger.info(f"  Extracting 1 frame every {self.interval_seconds} seconds (every {frame_interval} frames)")

        extracted_paths = []
        frame_count = 0
        saved_count = 0

        while True:
            ret, frame = video.read()
            if not ret:
                break

            # Extract frame at intervals
            if frame_count % frame_interval == 0:
                if max_frames and saved_count >= max_frames:
                    logger.info(f"  Reached max frames limit ({max_frames})")
                    break

                timestamp_seconds = frame_count / fps
                output_path = os.path.join(
                    output_dir,
                    f"frame_{saved_count:04d}_t{timestamp_seconds:.1f}s.jpg"
                )

                # Resize frame if dimensions exceed Claude API limits (2000px max for multi-image)
                resized_frame = self._resize_for_api(frame)
                cv2.imwrite(output_path, resized_frame)
                extracted_paths.append(output_path)
                saved_count += 1

                if saved_count % 10 == 0:
                    logger.info(f"  Extracted {saved_count} frames...")

            frame_count += 1

        video.release()
        logger.info(f"  ✓ Extracted {saved_count} frames total")

        return extracted_paths

    def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        video = cv2.VideoCapture(video_path)
        fps = video.get(cv2.CAP_PROP_FPS)
        total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        video.release()
        return duration

    def sample_frames_evenly(self, frame_paths: List[str], target_count: int) -> List[str]:
        """
        Sample frames evenly from the extracted set

        Args:
            frame_paths: List of all extracted frame paths
            target_count: Number of frames to sample

        Returns:
            Evenly sampled subset of frame paths
        """
        if len(frame_paths) <= target_count:
            return frame_paths

        # Calculate step size to get evenly distributed frames
        step = len(frame_paths) / target_count
        indices = [int(i * step) for i in range(target_count)]

        sampled = [frame_paths[i] for i in indices]
        logger.info(f"Sampled {len(sampled)} frames from {len(frame_paths)} total")

        return sampled

    def _resize_for_api(self, frame, max_dimension: int = 1600):
        """
        Resize frame to fit Claude API limits (2000px max, using 1600 for safety)

        Args:
            frame: OpenCV frame (numpy array)
            max_dimension: Maximum width or height (default 1600px)

        Returns:
            Resized frame
        """
        height, width = frame.shape[:2]

        # Check if resize is needed
        if height <= max_dimension and width <= max_dimension:
            return frame

        # Calculate scaling factor
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Resize using high-quality interpolation
        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return resized
