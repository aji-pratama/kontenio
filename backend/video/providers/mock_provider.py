import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from .base import (
    ImageGenerationProvider,
    LLMProvider,
    TranscriptSegment,
    TranscriptionProvider,
    VisualPrompt,
)


class MockTranscriptionProvider(TranscriptionProvider):
    @property
    def name(self) -> str:
        return "Mock Transcriber"

    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        return [
            TranscriptSegment(start=0.0, end=3.0, text="Welcome to the AI Video Factory demonstration."),
            TranscriptSegment(start=3.0, end=6.0, text="This system is designed to automate vertical video creation."),
            TranscriptSegment(start=6.0, end=9.0, text="We are currently testing the mock provider pipeline."),
            TranscriptSegment(start=9.0, end=12.0, text="It allows developers to verify the layout and rendering."),
            TranscriptSegment(start=12.0, end=15.0, text="The top panel displays AI-generated visual assets."),
            TranscriptSegment(start=15.0, end=18.0, text="The bottom panel shows the original raw footage."),
            TranscriptSegment(start=18.0, end=21.0, text="A glassmorphism overlay presents the dynamic subtitles."),
            TranscriptSegment(start=21.0, end=24.0, text="Everything is orchestrated by Django and rendered by Remotion."),
            TranscriptSegment(start=24.0, end=27.0, text="This automation saves hours of manual editing time."),
            TranscriptSegment(start=27.0, end=30.0, text="Final check complete. Ready for production usage!"),
        ]


class MockLLMProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "Mock LLM"

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return "Mock AI response"

    def generate_visual_prompts(
        self,
        transcript: List[Dict[str, Any]],
        style_hint: str = "modern"
    ) -> List[VisualPrompt]:
        return [
            VisualPrompt(time=0.0, prompt="Futuristic factory interior with robotic arms", duration=5.0),
            VisualPrompt(time=5.0, prompt="Digital code scrolling on a vertical screen", duration=5.0),
            VisualPrompt(time=10.0, prompt="abstract 3D neural network connection mesh", duration=5.0),
            VisualPrompt(time=15.0, prompt="Cinematic close-up of a high-tech processor", duration=5.0),
            VisualPrompt(time=20.0, prompt="Vibrant cyberpunk city street at night", duration=5.0),
            VisualPrompt(time=25.0, prompt="Minimalist clean studio with a single glowing Cube", duration=5.0),
        ]


class MockImageProvider(ImageGenerationProvider):
    @property
    def name(self) -> str:
        return "Mock Image Gen"

    def generate(self, prompt: str, output_path: str) -> str:
        # Create a tiny placeholder if pillow is available, otherwise just copy a file
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1080, 1920), color=(73, 109, 137))
            d = ImageDraw.Draw(img)
            d.text((100, 100), f"MOCK: {prompt[:30]}...", fill=(255, 255, 0))
            img.save(output_path)
        except ImportError:
            # Fallback: copy project logo or just create empty file
            Path(output_path).touch()
        
        return output_path
