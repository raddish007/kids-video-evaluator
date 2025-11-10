"""
YouTube metadata extraction using yt-dlp
Fetches comprehensive video information including stats, channel data, and thumbnail
"""
import os
import json
import logging
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeMetadataFetcher:
    """Fetch comprehensive YouTube video metadata"""

    def fetch_metadata(self, url: str, save_thumbnail: bool = True, thumbnail_dir: Optional[str] = None) -> Dict:
        """
        Fetch comprehensive metadata for a YouTube video

        Args:
            url: YouTube video URL
            save_thumbnail: Whether to download the thumbnail image
            thumbnail_dir: Directory to save thumbnail (if None, uses temp)

        Returns:
            Dictionary containing all metadata

        Raises:
            RuntimeError: If metadata fetch fails
        """
        logger.info(f"Fetching YouTube metadata for: {url}")

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Extract video ID
                video_id = info.get('id', self._extract_video_id_from_url(url))

                # Extract hashtags from description
                description = info.get('description', '')
                hashtags = self._extract_hashtags(description)

                # Download thumbnail if requested
                thumbnail_path = None
                thumbnail_url = self._get_best_thumbnail_url(info)

                if save_thumbnail and thumbnail_url and thumbnail_dir:
                    os.makedirs(thumbnail_dir, exist_ok=True)
                    thumbnail_path = os.path.join(thumbnail_dir, 'thumbnail.jpg')
                    self._download_thumbnail(thumbnail_url, thumbnail_path)
                    logger.info(f"✓ Thumbnail downloaded: {thumbnail_path}")

                # Build comprehensive metadata dictionary
                metadata = {
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'description': description,
                    'hashtags': hashtags,
                    'url': url,
                    'thumbnail_url': thumbnail_url,
                    'thumbnail_path': thumbnail_path,

                    # Channel information
                    'channel_name': info.get('channel', info.get('uploader', '')),
                    'channel_id': info.get('channel_id', ''),
                    'channel_subscriber_count': info.get('channel_follower_count', 0),

                    # Video statistics
                    'upload_date': self._parse_upload_date(info.get('upload_date')),
                    'duration_seconds': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'comment_count': info.get('comment_count', 0),

                    # Video format
                    'width': info.get('width', 0),
                    'height': info.get('height', 0),
                    'aspect_ratio': f"{info.get('width', 0)}:{info.get('height', 0)}",
                    'fps': info.get('fps', 0),

                    # Content classification
                    'category': info.get('categories', [''])[0] if info.get('categories') else '',
                    'tags': info.get('tags', []),
                    'language': info.get('language', ''),
                    'has_captions': bool(info.get('subtitles') or info.get('automatic_captions')),
                    'age_restricted': info.get('age_limit', 0) > 0,
                    'availability': info.get('availability', 'public'),  # public, unlisted, private

                    # Content flags (raw data points - no interpretation)
                    'content_flags': {
                        'comments_enabled': info.get('comment_count', -1) != 0,
                        'ratings_enabled': info.get('like_count') is not None,
                        'is_embeddable': info.get('playable_in_embed', True),
                        'live_content': info.get('is_live_content', False) or info.get('was_live', False),
                    },

                    # Metadata fetch timestamp
                    'metadata_fetched_at': datetime.now().isoformat()
                }

                logger.info(f"✓ Metadata fetched: {metadata['title']}")
                logger.info(f"  Channel: {metadata['channel_name']}")
                logger.info(f"  Views: {metadata['view_count']:,}")
                logger.info(f"  Duration: {metadata['duration_seconds']}s")

                return metadata

        except yt_dlp.utils.DownloadError as e:
            raise RuntimeError(f"Failed to fetch YouTube metadata: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error fetching metadata: {e}")

    def _extract_video_id_from_url(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return 'unknown'

    def _extract_hashtags(self, description: str) -> List[str]:
        """Extract hashtags from video description"""
        if not description:
            return []

        # Find all hashtags (words starting with #)
        hashtags = re.findall(r'#(\w+)', description)

        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_hashtags.append(tag_lower)

        return unique_hashtags

    def _get_best_thumbnail_url(self, info: Dict) -> Optional[str]:
        """Get the highest quality thumbnail URL"""
        thumbnails = info.get('thumbnails', [])

        if not thumbnails:
            return None

        # Try to find maxresdefault (highest quality)
        for thumb in thumbnails:
            if 'maxresdefault' in thumb.get('url', ''):
                return thumb['url']

        # Fall back to highest resolution available
        thumbnails_sorted = sorted(
            thumbnails,
            key=lambda x: (x.get('width', 0) * x.get('height', 0)),
            reverse=True
        )

        if thumbnails_sorted:
            return thumbnails_sorted[0]['url']

        return None

    def _download_thumbnail(self, url: str, save_path: str):
        """Download thumbnail image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                f.write(response.content)

        except requests.RequestException as e:
            logger.warning(f"Failed to download thumbnail: {e}")
            raise

    def _parse_upload_date(self, upload_date: Optional[str]) -> Optional[str]:
        """Parse upload date from yt-dlp format (YYYYMMDD) to ISO format"""
        if not upload_date:
            return None

        try:
            # yt-dlp returns dates in YYYYMMDD format
            date_str = str(upload_date)
            if len(date_str) == 8:
                year = date_str[0:4]
                month = date_str[4:6]
                day = date_str[6:8]
                return f"{year}-{month}-{day}T00:00:00Z"
            return None
        except:
            return None

    def save_metadata_to_file(self, metadata: Dict, output_path: str):
        """Save metadata to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Metadata saved to: {output_path}")
