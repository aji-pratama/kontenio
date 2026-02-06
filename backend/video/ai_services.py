import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from django.conf import settings

from .providers import ProviderFactory
from .providers.base import GeneratedImage, TranscriptSegment, VisualPrompt

try:
    from .providers.openai_provider import OPENAI_AVAILABLE
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .providers.gemini_provider import GEMINI_AVAILABLE
except ImportError:
    GEMINI_AVAILABLE = False


class TranscriptionService:
    def __init__(self, provider: str = "openai_whisper", model_name: str = "base"):
        self.provider_type = provider
        self.model_name = model_name
        self._factory = ProviderFactory()

    def _get_provider(self):
        if self.provider_type == "local_whisper":
            from .providers.whisper_provider import LocalWhisperProvider
            return LocalWhisperProvider(model_name=self.model_name)
        return self._factory.get_transcription_provider(self.provider_type)

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        video_path = Path(video_path)
        if output_path is None:
            output_path = video_path.with_suffix('.wav')
        else:
            output_path = Path(output_path)

        cmd = [
            'ffmpeg', '-y', '-i', str(video_path),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return str(output_path)

    def transcribe(self, video_path: str, use_api: bool = True) -> List[Dict[str, Any]]:
        if self.provider_type == 'mock':
            provider = self._get_provider()
            segments = provider.transcribe(video_path)
            return [seg.to_dict() for seg in segments]

        audio_path = self.extract_audio(video_path)
        try:
            if not use_api and self.provider_type == "openai_whisper":
                from .providers.whisper_provider import LocalWhisperProvider
                provider = LocalWhisperProvider(model_name=self.model_name)
            else:
                provider = self._get_provider()
            segments = provider.transcribe(audio_path)
            return [seg.to_dict() for seg in segments]
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)


class VisualMappingService:
    def __init__(self, provider: str = "openai_gpt4"):
        self.provider_type = provider
        self._factory = ProviderFactory()
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            self._provider = self._factory.get_llm_provider(self.provider_type)
        return self._provider

    def generate_visual_prompts(
        self,
        transcript: List[Dict[str, Any]],
        style_hint: str = "modern, cinematic"
    ) -> List[Dict[str, Any]]:
        provider = self._get_provider()
        prompts = provider.generate_visual_prompts(transcript, style_hint)
        return [p.to_dict() for p in prompts]


class ImageGenerationService:
    def __init__(self, provider: str = "dalle3"):
        self.provider_type = provider
        self._factory = ProviderFactory()
        self._provider = None

    def _get_provider(self):
        if self._provider is None:
            self._provider = self._factory.get_image_provider(self.provider_type)
        return self._provider

    def generate(self, prompt: str, output_path: str) -> str:
        return self._get_provider().generate(prompt, output_path)

    def generate_batch(
        self,
        prompts: List[Dict[str, Any]],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        provider = self._get_provider()
        prompt_objects = [
            VisualPrompt(
                time=p.get('time', 0) if isinstance(p, dict) else 0,
                prompt=p.get('prompt', '') if isinstance(p, dict) else str(p),
                duration=p.get('duration') if isinstance(p, dict) else None
            )
            for p in prompts if p # Skip nulls
        ]
        results = provider.generate_batch(prompt_objects, output_dir, progress_callback)
        return [r.to_visual_dict() for r in results]


class AIServices:
    def __init__(
        self,
        transcription_provider: str = "openai_whisper",
        llm_provider: str = "openai_gpt4",
        image_provider: str = "dalle3"
    ):
        self.transcription = TranscriptionService(provider=transcription_provider)
        self.visual_mapping = VisualMappingService(provider=llm_provider)
        self.image_generation = ImageGenerationService(provider=image_provider)

    @classmethod
    def with_openai(cls) -> "AIServices":
        return cls(
            transcription_provider="openai_whisper",
            llm_provider="openai_gpt4",
            image_provider="dalle3"
        )

    @classmethod
    def with_gemini(cls) -> "AIServices":
        return cls(
            transcription_provider="gemini",
            llm_provider="gemini_flash",
            image_provider="imagen"
        )
