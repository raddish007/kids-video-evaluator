"""
YouTube video downloader using yt-dlp
Downloads videos permanently to a dedicated folder
"""
import os
import logging
from pathlib import Path
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download YouTube videos for analysis"""

    def __init__(self, download_dir: str = "downloaded_videos"):
        """
        Initialize YouTube downloader

        Args:
            download_dir: Directory to save downloaded videos permanently
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    def download(self, url: str) -> str:
        """
        Download YouTube video

        Args:
            url: YouTube video URL

        Returns:
            Path to downloaded video file

        Raises:
            RuntimeError: If download fails
        """
        logger.info(f"Downloading video from: {url}")

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Prefer MP4, fallback to best available
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'merge_output_format': 'mp4',  # Ensure final output is MP4
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                logger.info("Extracting video information...")
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'video')

                logger.info(f"Title: {video_title}")
                logger.info(f"Duration: {info.get('duration', 'unknown')} seconds")

                # Download the video
                logger.info("Downloading video...")
                info = ydl.extract_info(url, download=True)

                # Get the actual filename that was downloaded
                filename = ydl.prepare_filename(info)

                if not os.path.exists(filename):
                    raise RuntimeError(f"Downloaded file not found: {filename}")

                logger.info(f"✓ Video downloaded: {filename}")
                return filename

        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"Failed to download video: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error downloading video: {e}")

    def is_youtube_url(self, url: str) -> bool:
        """
        Check if string is a YouTube URL

        Args:
            url: String to check

        Returns:
            True if it's a YouTube URL
        """
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'www.youtube.com',
            'm.youtube.com'
        ]

        url_lower = url.lower()
        return any(domain in url_lower for domain in youtube_domains)
