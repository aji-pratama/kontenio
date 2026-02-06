import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from django.conf import settings


def get_media_paths() -> Dict[str, Path]:
    media_root = Path(settings.MEDIA_ROOT)
    return {
        'raw': media_root / 'raw',
        'assets': media_root / 'assets',
        'output': media_root / 'output',
        'props': media_root / 'props',
    }


def ensure_directories():
    for path in get_media_paths().values():
        path.mkdir(parents=True, exist_ok=True)


def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """Get video metadata, with fallback if ffprobe is missing."""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': data.get('streams', [{}])[0].get('width', 1920),
            'height': data.get('streams', [{}])[0].get('height', 1080),
            'fps': 30.0
        }
    except (subprocess.CalledProcessError, FileNotFoundError, Exception):
        # Fallback for mock mode or missing ffprobe
        return {
            'duration': 10.0, 
            'width': 1080, 
            'height': 1920,
            'fps': 30.0
        }


def validate_video_file(video_path: str):
    """Simple validation: check if file exists."""
    path = Path(video_path)
    if not path.exists():
        return False, "File does not exist"
    return True, None
