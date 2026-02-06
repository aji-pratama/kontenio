"""
AI Services Module
------------------
Contains wrappers for:
- OpenAI Whisper (Audio Transcription)
- GPT-4o (Visual Prompt Generation)
- Image Generation (DALL-E 3 or Stable Diffusion)
"""

import os
import json
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from django.conf import settings

# Try to import openai (may not be installed in development)
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import whisper (local execution)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class TranscriptionService:
    """
    Handles audio transcription using OpenAI Whisper.
    Supports both local execution and API-based transcription.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the transcription service.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        
    def _load_model(self):
        """Lazy load the Whisper model."""
        if self.model is None and WHISPER_AVAILABLE:
            self.model = whisper.load_model(self.model_name)
        return self.model
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file using ffmpeg.
        
        Args:
            video_path: Path to the input video file
            output_path: Optional path for output audio file
            
        Returns:
            Path to the extracted audio file
        """
        video_path = Path(video_path)
        if output_path is None:
            output_path = video_path.with_suffix('.wav')
        else:
            output_path = Path(output_path)
            
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # WAV format
            '-ar', '16000',  # 16kHz sample rate (optimal for Whisper)
            '-ac', '1',  # Mono
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)
    
    def transcribe_local(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio using local Whisper model.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of segments with start, end, and text
        """
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper is not installed. Run: pip install openai-whisper")
            
        model = self._load_model()
        result = model.transcribe(audio_path, word_timestamps=True)
        
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip()
            })
            
        return segments
    
    def transcribe_api(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of segments with start, end, and text
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK is not installed. Run: pip install openai")
            
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        with open(audio_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        segments = []
        for segment in response.segments:
            segments.append({
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip()
            })
            
        return segments
    
    def transcribe(self, video_path: str, use_api: bool = False) -> List[Dict[str, Any]]:
        """
        Main transcription method. Extracts audio and transcribes.
        
        Args:
            video_path: Path to the video file
            use_api: Whether to use OpenAI API (True) or local model (False)
            
        Returns:
            List of transcript segments
        """
        # Extract audio
        audio_path = self.extract_audio(video_path)
        
        try:
            if use_api:
                return self.transcribe_api(audio_path)
            else:
                return self.transcribe_local(audio_path)
        finally:
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)


class VisualMappingService:
    """
    Uses GPT-4o to analyze transcript and generate visual prompts.
    """
    
    SYSTEM_PROMPT = """You are a creative director for vertical video content. 
Your job is to analyze transcript segments and generate image prompts that will 
visually complement the spoken content.

For each section of the transcript, create a vivid, detailed image prompt that:
1. Captures the essence of what's being discussed
2. Uses modern, engaging visual styles (cyberpunk, minimalist, cinematic)
3. Avoids text in images - focus on visual metaphors
4. Is suitable for AI image generation

Return your response as a JSON array with this structure:
[
  {"time": <start_second>, "prompt": "<detailed image generation prompt>", "duration": <suggested_duration_seconds>}
]

Group related segments together - aim for 3-5 second visual segments.
"""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK is not installed. Run: pip install openai")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_visual_prompts(
        self, 
        transcript: List[Dict[str, Any]], 
        style_hint: str = "modern, cinematic"
    ) -> List[Dict[str, Any]]:
        """
        Generate visual prompts based on transcript.
        
        Args:
            transcript: List of transcript segments
            style_hint: Optional style guidance for visuals
            
        Returns:
            List of visual prompts with timing info
        """
        # Prepare transcript for GPT
        transcript_text = "\n".join([
            f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
            for seg in transcript
        ])
        
        user_prompt = f"""Analyze this transcript and create visual prompts:

{transcript_text}

Style preference: {style_hint}

Generate appropriate visual prompts for this content."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        try:
            result = json.loads(response.choices[0].message.content)
            # Handle both direct array and wrapped response
            if isinstance(result, list):
                return result
            elif 'prompts' in result:
                return result['prompts']
            elif 'visuals' in result:
                return result['visuals']
            else:
                # Try to find any array in the response
                for key, value in result.items():
                    if isinstance(value, list):
                        return value
                return []
        except json.JSONDecodeError:
            return []


class ImageGenerationService:
    """
    Generates images using DALL-E 3 or Stable Diffusion.
    """
    
    def __init__(self, provider: str = "dalle"):
        """
        Initialize image generation service.
        
        Args:
            provider: "dalle" for DALL-E 3 or "stable_diffusion" for local SD
        """
        self.provider = provider
        if provider == "dalle":
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI SDK is not installed. Run: pip install openai")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_image_dalle(
        self, 
        prompt: str, 
        output_path: str,
        size: str = "1024x1792"  # Vertical format for 9:16
    ) -> str:
        """
        Generate image using DALL-E 3.
        
        Args:
            prompt: Image generation prompt
            output_path: Where to save the image
            size: Image dimensions
            
        Returns:
            Path to the generated image
        """
        import urllib.request
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download and save the image
        urllib.request.urlretrieve(image_url, output_path)
        
        return output_path
    
    def generate_image_sd(
        self,
        prompt: str,
        output_path: str,
        negative_prompt: str = "text, watermark, blurry, low quality"
    ) -> str:
        """
        Generate image using local Stable Diffusion.
        
        Placeholder for Stable Diffusion integration.
        Implement based on your SD setup (ComfyUI, Automatic1111, etc.)
        """
        raise NotImplementedError(
            "Stable Diffusion integration not yet implemented. "
            "Use 'dalle' provider or implement your SD pipeline."
        )
    
    def generate(self, prompt: str, output_path: str) -> str:
        """
        Main generation method.
        
        Args:
            prompt: Image prompt
            output_path: Where to save the image
            
        Returns:
            Path to generated image
        """
        if self.provider == "dalle":
            return self.generate_image_dalle(prompt, output_path)
        else:
            return self.generate_image_sd(prompt, output_path)
    
    def generate_batch(
        self, 
        prompts: List[Dict[str, Any]], 
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple images from visual prompts.
        
        Args:
            prompts: List of visual prompt objects with 'time' and 'prompt' keys
            output_dir: Directory to save images
            
        Returns:
            List of visual objects with 'start' and 'src' keys for Remotion
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        visuals = []
        for i, prompt_obj in enumerate(prompts):
            filename = f"visual_{i:03d}_{int(prompt_obj['time'])}s.jpg"
            output_path = output_dir / filename
            
            try:
                self.generate(prompt_obj['prompt'], str(output_path))
                visuals.append({
                    'start': prompt_obj['time'],
                    'src': f"/media/assets/{filename}"
                })
            except Exception as e:
                print(f"Warning: Failed to generate image {i}: {e}")
                continue
                
        return visuals
