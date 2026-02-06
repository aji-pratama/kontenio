"""
Video Utilities
---------------
Helper functions for file handling, video metadata, and asset management.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from django.conf import settings


def get_media_paths() -> Dict[str, Path]:
    """
    Get all media directory paths.
    Creates them if they don't exist.
    
    Returns:
        Dictionary with paths for raw, assets, and output directories
    """
    paths = {
        'media_root': Path(settings.MEDIA_ROOT),
        'raw': Path(settings.MEDIA_ROOT) / 'raw',
        'assets': Path(settings.MEDIA_ROOT) / 'assets',
        'output': Path(settings.MEDIA_ROOT) / 'output',
    }
    
    # Ensure all directories exist
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    
    return paths


def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    Extract metadata from video file using ffprobe.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary containing duration, fps, width, height, etc.
    """
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(video_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    
    # Find video stream
    video_stream = None
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'video':
            video_stream = stream
            break
    
    if video_stream is None:
        raise ValueError("No video stream found in file")
    
    # Parse frame rate (might be in format "30/1" or "30000/1001")
    fps_str = video_stream.get('r_frame_rate', '30/1')
    fps_parts = fps_str.split('/')
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else float(fps_parts[0])
    
    duration = float(data.get('format', {}).get('duration', 0))
    
    return {
        'duration': duration,
        'fps': fps,
        'width': int(video_stream.get('width', 1920)),
        'height': int(video_stream.get('height', 1080)),
        'codec': video_stream.get('codec_name', 'unknown'),
        'total_frames': int(duration * fps)
    }


def generate_render_props(
    video_filename: str,
    transcript: list,
    visuals: list,
    output_path: Optional[str] = None
) -> str:
    """
    Generate the props JSON file for Remotion.
    
    Args:
        video_filename: Name of the raw video file
        transcript: List of transcript segments
        visuals: List of visual objects with timing and paths
        output_path: Optional custom output path
        
    Returns:
        Path to the generated props file
    """
    if output_path is None:
        # Default to public/media/render_props.json
        output_path = Path(settings.PROJECT_ROOT) / 'public' / 'media' / 'render_props.json'
    else:
        output_path = Path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    props = {
        'videoUrl': f'/media/raw/{video_filename}',
        'transcript': transcript,
        'visuals': visuals
    }
    
    with open(output_path, 'w') as f:
        json.dump(props, f, indent=2)
    
    return str(output_path)


def calculate_duration_in_frames(duration_seconds: float, fps: int = 30) -> int:
    """
    Convert duration in seconds to frames.
    
    Args:
        duration_seconds: Duration in seconds
        fps: Frames per second (default 30)
        
    Returns:
        Duration in frames
    """
    return int(duration_seconds * fps)


def ensure_symlink():
    """
    Ensure the public/media symlink points to backend/media.
    This is required for Remotion to access Django-managed media files.
    """
    public_media = Path(settings.PROJECT_ROOT) / 'public' / 'media'
    backend_media = Path(settings.MEDIA_ROOT)
    
    # Remove existing symlink or directory if it exists
    if public_media.is_symlink():
        public_media.unlink()
    elif public_media.exists():
        # Don't remove if it's a real directory with content
        if any(public_media.iterdir()):
            print(f"Warning: {public_media} exists and is not empty. Not creating symlink.")
            return False
        public_media.rmdir()
    
    # Create parent directory if needed
    public_media.parent.mkdir(parents=True, exist_ok=True)
    
    # Create symlink
    public_media.symlink_to(backend_media)
    
    return True


def cleanup_temp_files(session_id: str):
    """
    Clean up temporary files from a rendering session.
    
    Args:
        session_id: Unique identifier for the session
    """
    paths = get_media_paths()
    
    # Clean up temporary audio files
    for audio_file in paths['raw'].glob(f'{session_id}*.wav'):
        audio_file.unlink()


def validate_video_file(video_path: str) -> Tuple[bool, str]:
    """
    Validate that a file is a valid video.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(video_path)
    
    if not path.exists():
        return False, f"File not found: {video_path}"
    
    if not path.is_file():
        return False, f"Not a file: {video_path}"
    
    # Check extension
    valid_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid video extension: {path.suffix}"
    
    # Try to get metadata (validates file is actually a video)
    try:
        get_video_metadata(str(path))
        return True, ""
    except Exception as e:
        return False, f"Invalid video file: {str(e)}"
