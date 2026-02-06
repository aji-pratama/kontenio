from typing import List, Optional

from .base import TranscriptSegment, VisualPrompt

try:
    from .whisper_provider import LocalWhisperProvider, WHISPER_AVAILABLE
except ImportError:
    WHISPER_AVAILABLE = False


class LocalWhisperProvider:
    def __init__(self, model_name: str = "base"):
        try:
            import whisper
            self._whisper = whisper
        except ImportError:
            raise RuntimeError("Whisper not installed. Run: pip install openai-whisper")

        self.model_name = model_name
        self._model = None

    @property
    def name(self) -> str:
        return f"Local Whisper ({self.model_name})"

    @property
    def model(self):
        if self._model is None:
            self._model = self._whisper.load_model(self.model_name)
        return self._model

    def transcribe(self, audio_path: str) -> List[TranscriptSegment]:
        result = self.model.transcribe(audio_path, word_timestamps=True)
        return [
            TranscriptSegment(
                start=segment['start'],
                end=segment['end'],
                text=segment['text'].strip()
            )
            for segment in result.get('segments', [])
        ]
