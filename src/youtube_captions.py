"""
YouTube caption downloader using yt-dlp
Downloads manual and auto-generated captions in multiple formats
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeCaptionDownloader:
    """Download captions/subtitles from YouTube videos"""

    def download_captions(self, url: str, output_dir: str) -> Dict:
        """
        Download all available captions from a YouTube video

        Args:
            url: YouTube video URL
            output_dir: Directory to save caption files

        Returns:
            Dictionary with caption download results

        Raises:
            RuntimeError: If caption fetch fails
        """
        logger.info(f"Fetching captions for: {url}")

        os.makedirs(output_dir, exist_ok=True)

        # Configure yt-dlp to fetch caption info
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,  # Don't download video, just get info
        }

        results = {
            'has_captions': False,
            'manual_captions': [],
            'auto_captions': [],
            'downloaded_files': [],
            'caption_info': {}
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id', 'unknown')

                # Check for manual (uploaded) captions
                manual_subs = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})

                results['caption_info'] = {
                    'manual_languages': list(manual_subs.keys()),
                    'auto_languages': list(auto_subs.keys())
                }

                # Download manual captions (prioritize these)
                if manual_subs:
                    logger.info(f"  Found manual captions in {len(manual_subs)} languages")
                    results['has_captions'] = True

                    for lang, formats in manual_subs.items():
                        caption_file = self._download_caption_format(
                            formats, lang, 'manual', output_dir, video_id
                        )
                        if caption_file:
                            results['manual_captions'].append({
                                'language': lang,
                                'type': 'manual',
                                'file': caption_file
                            })
                            results['downloaded_files'].append(caption_file)

                # Download auto-generated captions
                if auto_subs:
                    logger.info(f"  Found auto-generated captions in {len(auto_subs)} languages")
                    results['has_captions'] = True

                    for lang, formats in auto_subs.items():
                        caption_file = self._download_caption_format(
                            formats, lang, 'auto', output_dir, video_id
                        )
                        if caption_file:
                            results['auto_captions'].append({
                                'language': lang,
                                'type': 'auto',
                                'file': caption_file
                            })
                            results['downloaded_files'].append(caption_file)

                if results['has_captions']:
                    logger.info(f"  ✓ Downloaded {len(results['downloaded_files'])} caption files")
                else:
                    logger.info("  No captions available for this video")

                # Save caption metadata
                metadata_path = os.path.join(output_dir, 'youtube_captions_info.json')
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

                return results

        except Exception as e:
            logger.warning(f"Failed to download captions: {e}")
            return results

    def _download_caption_format(self, formats: List[Dict], lang: str,
                                  caption_type: str, output_dir: str,
                                  video_id: str) -> Optional[str]:
        """
        Download caption in best available format (prefer SRT)

        Args:
            formats: List of available caption formats
            lang: Language code
            caption_type: 'manual' or 'auto'
            output_dir: Directory to save captions
            video_id: YouTube video ID

        Returns:
            Path to downloaded caption file, or None if failed
        """
        # Prefer SRT format, fallback to VTT, then JSON3
        preferred_order = ['srv1', 'vtt', 'json3']

        for format_ext in preferred_order:
            for fmt in formats:
                if fmt.get('ext') == format_ext:
                    url = fmt.get('url')
                    if not url:
                        continue

                    # Determine file extension (convert srv1 to srt)
                    file_ext = 'srt' if format_ext == 'srv1' else format_ext

                    # Create filename: captions_manual_en.srt or captions_auto_en.srt
                    filename = f"captions_{caption_type}_{lang}.{file_ext}"
                    output_path = os.path.join(output_dir, filename)

                    try:
                        # Download caption file
                        import requests
                        response = requests.get(url, timeout=30)
                        response.raise_for_status()

                        with open(output_path, 'wb') as f:
                            f.write(response.content)

                        logger.info(f"  ✓ Downloaded {caption_type} captions ({lang}): {filename}")
                        return output_path

                    except Exception as e:
                        logger.warning(f"  Failed to download {lang} captions: {e}")
                        continue

        return None

    def get_primary_caption_path(self, output_dir: str) -> Optional[str]:
        """
        Get path to the primary (best) caption file

        Priority:
        1. Manual English captions
        2. Auto English captions
        3. First manual caption in any language
        4. First auto caption in any language

        Args:
            output_dir: Directory where captions were saved

        Returns:
            Path to primary caption file, or None if no captions
        """
        # Check for metadata file
        metadata_path = os.path.join(output_dir, 'youtube_captions_info.json')

        if not os.path.exists(metadata_path):
            return None

        with open(metadata_path, 'r', encoding='utf-8') as f:
            results = json.load(f)

        if not results['has_captions']:
            return None

        # Priority 1: Manual English
        for caption in results.get('manual_captions', []):
            if caption['language'].startswith('en'):
                return caption['file']

        # Priority 2: Auto English
        for caption in results.get('auto_captions', []):
            if caption['language'].startswith('en'):
                return caption['file']

        # Priority 3: First manual caption
        if results.get('manual_captions'):
            return results['manual_captions'][0]['file']

        # Priority 4: First auto caption
        if results.get('auto_captions'):
            return results['auto_captions'][0]['file']

        return None
