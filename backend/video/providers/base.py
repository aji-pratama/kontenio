from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"start": self.start, "end": self.end, "text": self.text}


@dataclass
class VisualPrompt:
    time: float
    prompt: str
    duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"time": self.time, "prompt": self.prompt}
        if self.duration:
            result["duration"] = self.duration
        return result


@dataclass
class GeneratedImage:
    path: str
    prompt: str
    start_time: float

    def to_visual_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start_time,
            "src": f"/media/assets/{self.path.split('/')[-1]}"
        }


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class LLMProvider(ABC):
    @abstractmethod
    def generate_visual_prompts(
        self,
        transcript: List[Dict[str, Any]],
        style_hint: str = "modern, cinematic"
    ) -> List[VisualPrompt]:
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class ImageGenerationProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: str) -> str:
        pass

    def generate_batch(
        self,
        prompts: List[VisualPrompt],
        output_dir: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[GeneratedImage]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, prompt_obj in enumerate(prompts):
            if progress_callback:
                progress_callback(i + 1, len(prompts))

            filename = f"visual_{i:03d}_{int(prompt_obj.time)}s.jpg"
            output_path = str(output_dir / filename)

            try:
                self.generate(prompt_obj.prompt, output_path)
                results.append(GeneratedImage(
                    path=output_path,
                    prompt=prompt_obj.prompt,
                    start_time=prompt_obj.time
                ))
            except Exception as e:
                print(f"Warning: Failed to generate image {i}: {e}")
                continue

        return results

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def supports_vertical(self) -> bool:
        return True
