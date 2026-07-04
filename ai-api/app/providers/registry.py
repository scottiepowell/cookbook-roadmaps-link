from app.config import AISettings, get_ai_settings
from app.providers.base import LLMProvider
from app.providers.errors import ProviderConfigError
from app.providers.mock import MockProvider
from app.providers.openai_provider import OpenAIProvider


def get_provider(settings: AISettings | None = None) -> LLMProvider:
    active_settings = settings or get_ai_settings()

    if active_settings.provider == "mock":
        return MockProvider(model=active_settings.model)

    if active_settings.provider == "openai":
        return OpenAIProvider(
            model=active_settings.openai_model,
            fallback_model=active_settings.openai_fallback_model,
            max_output_tokens=active_settings.max_output_tokens,
            timeout_seconds=active_settings.timeout_seconds,
        )

    raise ProviderConfigError(f"Unsupported AI_PROVIDER '{active_settings.provider}'.")
