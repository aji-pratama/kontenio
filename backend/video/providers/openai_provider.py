import json
import urllib.request
from typing import Any, Dict, List, Optional

from django.conf import settings

from ..prompts import get_visual_mapping_prompt
from .base import (
    ImageGenerationProvider,
    LLMProvider,
    TranscriptSegment,
    TranscriptionProvider,
    VisualPrompt,
)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAITranscriptionProvider(TranscriptionProvider):
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK not installed. Run: pip install openai")
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=self.api_key)

    @property
    def name(self) -> str:
        return "OpenAI Whisper"

    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        with open(audio_path, 'rb') as audio_file:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

        return [
            TranscriptSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip()
            )
            for segment in response.segments
        ]


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK not installed. Run: pip install openai")
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    @property
    def name(self) -> str:
        return f"OpenAI {self.model}"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcript:\n{transcript_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        try:
            result = json.loads(response.choices[0].message.content)
            prompts_list = result
            if isinstance(result, dict):
                for key in ['prompts', 'visuals', 'images']:
                    if key in result and isinstance(result[key], list):
                        prompts_list = result[key]
                        break

            return [
                VisualPrompt(
                    time=p.get('time', 0),
                    prompt=p.get('prompt', ''),
                    duration=p.get('duration')
                )
                for p in prompts_list
            ]
        except (json.JSONDecodeError, KeyError):
            return []


class OpenAIImageProvider(ImageGenerationProvider):
    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI SDK not installed. Run: pip install openai")
        self.api_key = api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=self.api_key)

    @property
    def name(self) -> str:
        return "DALL-E 3"

    def generate(self, prompt: str, output_path: str) -> str:
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        urllib.request.urlretrieve(image_url, output_path)
        return output_path
