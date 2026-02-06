import os
from enum import Enum
from typing import Literal, Optional

from django.conf import settings

from .base import ImageGenerationProvider, LLMProvider, TranscriptionProvider


class TranscriptionProviderType(str, Enum):
    OPENAI_WHISPER = "openai_whisper"
    GEMINI = "gemini"
    LOCAL_WHISPER = "local_whisper"
    MOCK = "mock"


class LLMProviderType(str, Enum):
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT4_MINI = "openai_gpt4_mini"
    GEMINI_PRO = "gemini_pro"
    GEMINI_FLASH = "gemini_flash"
    MOCK = "mock"


class ImageProviderType(str, Enum):
    DALLE3 = "dalle3"
    IMAGEN = "imagen"
    GEMINI_FLASH = "gemini_flash"
    MOCK = "mock"


class ProviderFactory:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ):
        self.openai_api_key = (
            openai_api_key or
            getattr(settings, 'OPENAI_API_KEY', None) or
            os.environ.get('OPENAI_API_KEY', '')
        )
        self.gemini_api_key = (
            gemini_api_key or
            getattr(settings, 'GEMINI_API_KEY', None) or
            os.environ.get('GEMINI_API_KEY', '') or
            os.environ.get('GOOGLE_API_KEY', '')
        )

    def get_transcription_provider(self, provider_type: str) -> TranscriptionProvider:
        provider_type = TranscriptionProviderType(provider_type)

        if provider_type == TranscriptionProviderType.OPENAI_WHISPER:
            from .openai_provider import OpenAITranscriptionProvider
            return OpenAITranscriptionProvider(api_key=self.openai_api_key)

        if provider_type == TranscriptionProviderType.GEMINI:
            from .gemini_provider import GeminiTranscriptionProvider
            return GeminiTranscriptionProvider(api_key=self.gemini_api_key)

        if provider_type == TranscriptionProviderType.LOCAL_WHISPER:
            from .whisper_provider import LocalWhisperProvider
            return LocalWhisperProvider()

        if provider_type == TranscriptionProviderType.MOCK:
            from .mock_provider import MockTranscriptionProvider
            return MockTranscriptionProvider()

        raise ValueError(f"Unknown transcription provider: {provider_type}")

    def get_llm_provider(self, provider_type: str) -> LLMProvider:
        provider_type = LLMProviderType(provider_type)

        if provider_type == LLMProviderType.OPENAI_GPT4:
            from .openai_provider import OpenAILLMProvider
            return OpenAILLMProvider(api_key=self.openai_api_key, model="gpt-4o")

        if provider_type == LLMProviderType.OPENAI_GPT4_MINI:
            from .openai_provider import OpenAILLMProvider
            return OpenAILLMProvider(api_key=self.openai_api_key, model="gpt-4o-mini")

        if provider_type == LLMProviderType.GEMINI_PRO:
            from .gemini_provider import GeminiLLMProvider
            return GeminiLLMProvider(api_key=self.gemini_api_key, model="gemini-1.5-pro")

        if provider_type == LLMProviderType.GEMINI_FLASH:
            from .gemini_provider import GeminiLLMProvider
            return GeminiLLMProvider(api_key=self.gemini_api_key, model="gemini-2.0-flash")

        if provider_type == LLMProviderType.MOCK:
            from .mock_provider import MockLLMProvider
            return MockLLMProvider()

        raise ValueError(f"Unknown LLM provider: {provider_type}")

    def get_image_provider(self, provider_type: str) -> ImageGenerationProvider:
        provider_type = ImageProviderType(provider_type)

        if provider_type == ImageProviderType.DALLE3:
            from .openai_provider import OpenAIImageProvider
            return OpenAIImageProvider(api_key=self.openai_api_key)

        if provider_type == ImageProviderType.IMAGEN:
            from .gemini_provider import GeminiImageProvider
            return GeminiImageProvider(api_key=self.gemini_api_key)

        if provider_type == ImageProviderType.GEMINI_FLASH:
            from .gemini_provider import GeminiFlashImageProvider
            return GeminiFlashImageProvider(api_key=self.gemini_api_key)

        if provider_type == ImageProviderType.MOCK:
            from .mock_provider import MockImageProvider
            return MockImageProvider()

        raise ValueError(f"Unknown image provider: {provider_type}")


def get_provider(
    service: Literal["transcription", "llm", "image"],
    provider_type: str
):
    factory = ProviderFactory()
    if service == "transcription":
        return factory.get_transcription_provider(provider_type)
    if service == "llm":
        return factory.get_llm_provider(provider_type)
    if service == "image":
        return factory.get_image_provider(provider_type)
    raise ValueError(f"Unknown service: {service}")
