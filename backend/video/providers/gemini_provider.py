import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from ..prompts import TRANSCRIPTION_PROMPT, get_visual_mapping_prompt
from .base import (
    ImageGenerationProvider,
    LLMProvider,
    TranscriptSegment,
    TranscriptionProvider,
    VisualPrompt,
)

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


def get_gemini_api_key() -> str:
    import os
    return (
        getattr(settings, 'GEMINI_API_KEY', '') or
        os.environ.get('GEMINI_API_KEY', '') or
        os.environ.get('GOOGLE_API_KEY', '')
    )


class GeminiTranscriptionProvider(TranscriptionProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google GenAI SDK not installed. Run: pip install google-genai")
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "Gemini Audio"

    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        audio_path = Path(audio_path)
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        mime_types = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4'}
        mime_type = mime_types.get(audio_path.suffix.lower(), 'audio/wav')

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Content(parts=[
                    types.Part.from_text(text=TRANSCRIPTION_PROMPT),
                    types.Part.from_bytes(data=audio_data, mime_type=mime_type)
                ])
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

        try:
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0]
            segments_data = json.loads(text)
            return [
                TranscriptSegment(
                    start=float(seg.get('start', 0)),
                    end=float(seg.get('end', 0)),
                    text=seg.get('text', '').strip()
                )
                for seg in segments_data
            ]
        except (json.JSONDecodeError, Exception):
            return [TranscriptSegment(start=0, end=10, text=response.text)]


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google GenAI SDK not installed. Run: pip install google-genai")
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return f"Gemini {self.model_name}"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents
        )
        return response.text

    def generate_visual_prompts(
        self,
        transcript: List[Dict[str, Any]],
        style_hint: str = "modern"
    ) -> List[VisualPrompt]:
        system_prompt = get_visual_mapping_prompt(style_hint)
        transcript_text = "\n".join([
            f"[{seg['start']:.1f}s - {seg['end']:.1f}s]: {seg['text']}"
            for seg in transcript
        ])
        prompt = f"{system_prompt}\n\nTranscript:\n{transcript_text}"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

        try:
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0]
            result = json.loads(text)
            prompts_list = result
            if isinstance(result, dict):
                for key in ['prompts', 'visuals', 'images']:
                    if key in result and isinstance(result[key], list):
                        prompts_list = result[key]
                        break
            return [
                VisualPrompt(
                    time=float(p.get('time', 0)),
                    prompt=p.get('prompt', ''),
                    duration=p.get('duration')
                )
                for p in prompts_list
            ]
        except (json.JSONDecodeError, KeyError):
            return []


class GeminiImageProvider(ImageGenerationProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "imagen-3.0-generate-002"):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google GenAI SDK not installed. Run: pip install google-genai")
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "Imagen 3"

    def generate(self, prompt: str, output_path: str) -> str:
        response = self.client.models.generate_images(
            model=self.model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="BLOCK_ONLY_HIGH",
                person_generation="ALLOW_ADULT"
            )
        )
        if response.generated_images:
            image = response.generated_images[0]
            with open(output_path, 'wb') as f:
                f.write(image.image.image_bytes)
            return output_path
        raise RuntimeError("No image generated")


class GeminiFlashImageProvider(ImageGenerationProvider):
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Google GenAI SDK not installed. Run: pip install google-genai")
        self.api_key = api_key or get_gemini_api_key()
        self.model_name = "gemini-2.0-flash-exp-image-generation"
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "Gemini Flash Image"

    def generate(self, prompt: str, output_path: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"Generate a vertical 9:16 image: {prompt}",
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])
        )
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                with open(output_path, 'wb') as f:
                    f.write(part.inline_data.data)
                return output_path
        raise RuntimeError("No image in response")
