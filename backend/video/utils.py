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


def generate_render_props(
    video_filename: str,
    transcript: List[Dict[str, Any]],
    visuals: List[Dict[str, Any]],
    output_path: str
):
    # STRATEGY: ULTIMATE ROBUSTNESS
    # We will spin up a dedicated "python -m http.server 9005" in services.py
    # This bypasses 'file://' security blocks AND is faster/stable than Django dev server.
    base_url = "http://localhost:9005"
    

    
    # Convert visuals to properly joined URL
    visuals_http = []
    for visual in visuals:
        src = visual.get('src', '')
        if src.startswith('/media/'):
            # Convert /media/assets/file.jpg -> http://localhost:9005/assets/file.jpg
            # Note: The static server will be rooted at backend/media
            relative_path = src.replace('/media/', '') # removing leading /media/ to get local path
            
            # Construct URL: localhost:9005/assets/image.jpg
            full_url = f"{base_url}/{relative_path}".replace('//', '/').replace('http:/', 'http://')
            visuals_http.append({
                **visual,
                'src': full_url
            })
        else:
            visuals_http.append(visual)
    
    # Handle Video Path
    # filename comes as "raw/video.mov". Server root is backend/media.
    # So URL should be http://localhost:9005/raw/video.mov
    if video_filename.startswith('raw/'):
         video_url_path = video_filename
    else:
         video_url_path = f"raw/{video_filename}"
         
    video_url = f"{base_url}/{video_url_path}".replace('//', '/').replace('http:/', 'http://')

    props = {
        'videoUrl': video_url,
        'transcript': transcript,
        'visuals': visuals_http,
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
        # If it's a directory but not a symlink, back it up
        try:
            public_media.rename(public_media.with_suffix('.bak'))
        except Exception:
            pass

    public_media.parent.mkdir(parents=True, exist_ok=True)
    try:
        public_media.symlink_to(backend_media)
    except Exception:
        # Fallback if symlink fails (e.g. permission or OS issue)
        pass
