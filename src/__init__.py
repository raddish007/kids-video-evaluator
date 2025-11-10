"""Kids Video Evaluator - Analyze educational videos for children"""

from .frame_extractor import FrameExtractor
from .audio_transcriber import AudioTranscriber
from .evaluator import VideoEvaluator
from .report_generator import ReportGenerator
from .rubric import get_evaluation_prompt
from .youtube_downloader import YouTubeDownloader
from .youtube_metadata import YouTubeMetadataFetcher

__all__ = [
    'FrameExtractor',
    'AudioTranscriber',
    'VideoEvaluator',
    'ReportGenerator',
    'get_evaluation_prompt',
    'YouTubeDownloader',
    'YouTubeMetadataFetcher',
]
