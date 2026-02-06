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
    parent_dir = Path(output_path).parent
    # os.path.isdir returns False for broken symlinks, which is what we want
    if not os.path.isdir(str(parent_dir)):
        parent_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(props, f, indent=2)
    return output_path


def ensure_symlink():
    """Best effort symlink to allow Remotion access to media if needed."""
    project_root = Path(settings.PROJECT_ROOT)
    public_media = project_root / 'public' / 'media'
    # Target path INSIDE the container
    backend_media_in_container = "/app/backend/media"
    
    # Check if the path exists (could be a broken symlink)
    if os.path.lexists(str(public_media)):
        # If it's a symlink, check where it points
        if os.path.islink(str(public_media)):
            target = os.readlink(str(public_media))
            # If it points to a host path (e.g. /Users/...) or is simply wrong, remove it
            if target.startswith('/Users/') or target != backend_media_in_container:
                try:
                    os.unlink(str(public_media))
                except Exception:
                    pass
            else:
                # Already points to the correct container path
                return
        else:
            # It's a real directory or file, but we want a symlink. 
            # Leave it if it has content, but usually we want to replace it.
            # For safety, let's just return if it's a real dir to avoid data loss.
            if os.path.isdir(str(public_media)):
                return
            os.remove(str(public_media))

    try:
        public_media.parent.mkdir(parents=True, exist_ok=True)
        # Use absolute container path for the symlink target
        os.symlink(backend_media_in_container, str(public_media))
        print(f"✅ Created symlink: {public_media} -> {backend_media_in_container}")
    except Exception as e:
        if not isinstance(e, FileExistsError):
             print(f"⚠️ Symlink warning: {e}")
