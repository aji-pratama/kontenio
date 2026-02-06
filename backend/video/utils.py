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
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return {
        'duration': float(data.get('format', {}).get('duration', 0)),
        'width': data.get('streams', [{}])[0].get('width', 1920),
        'height': data.get('streams', [{}])[0].get('height', 1080),
    }


def generate_render_props(
    video_filename: str,
    transcript: List[Dict[str, Any]],
    visuals: List[Dict[str, Any]],
    output_path: str
):
    props = {
        'videoUrl': f'/media/raw/{video_filename}',
        'transcript': transcript,
        'visuals': visuals,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(props, f, indent=2)
    return output_path


def ensure_symlink():
    project_root = Path(settings.PROJECT_ROOT)
    public_media = project_root / 'public' / 'media'
    backend_media = Path(settings.MEDIA_ROOT)

    if public_media.exists():
        if public_media.is_symlink():
            return
        public_media.rename(public_media.with_suffix('.bak'))

    public_media.parent.mkdir(parents=True, exist_ok=True)
    public_media.symlink_to(backend_media)
