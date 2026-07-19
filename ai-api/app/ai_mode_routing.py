"""Safe request-scoped mode resolution for local AI workflows."""

from dataclasses import dataclass, replace
import os

from app.config import AISettings, get_ai_settings
from app.providers import LLMProvider, get_provider

LIVE_MODEL = "gpt-5.4-nano"
MOCK_MODEL = "mock-basic"


@dataclass(frozen=True)
class AiModeResolution:
    requested_mode: str
    effective_provider: str | None
    effective_model: str | None
    live_available: bool
    safe_unavailable_reason: str | None = None

    def provider(self) -> LLMProvider | None:
        if self.effective_provider is None:
            return None
        settings = get_ai_settings()
        if self.effective_provider == "mock":
            return get_provider(replace(settings, provider="mock", model=MOCK_MODEL))
        return get_provider(replace(settings, provider="openai", openai_model=LIVE_MODEL))


def resolve_ai_mode(provider_mode: str | None, model: str | None) -> AiModeResolution:
    mode = (provider_mode or "mock").strip().lower()
    if mode in {"offline", "mock"}:
        if model not in {None, MOCK_MODEL}:
            return AiModeResolution(mode, None, None, False, "Mock mode only supports mock-basic.")
        return AiModeResolution(mode, "mock", MOCK_MODEL, False)
    if mode not in {"live", "openai"}:
        return AiModeResolution(mode, None, None, False, "Unsupported AI mode.")
    settings = get_ai_settings()
    if model not in {None, LIVE_MODEL}:
        return AiModeResolution(mode, None, None, False, "Only gpt-5.4-nano is available for live mode.")
    if not settings.openai_live_tests_enabled:
        return AiModeResolution(mode, None, None, False, "Live mode requires explicit local live opt-in.")
    if not os.getenv("OPENAI_API_KEY"):
        return AiModeResolution(mode, None, None, False, "Live provider configuration is unavailable.")
    return AiModeResolution(mode, "openai", LIVE_MODEL, True)
