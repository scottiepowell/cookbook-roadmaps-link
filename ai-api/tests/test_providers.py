import pytest

from app.config import get_ai_settings
from app.providers import LLMRequest, StructuredLLMRequest, get_provider
from app.providers.errors import ProviderConfigError
from app.providers.mock import MockProvider
from app.providers.openai_provider import OpenAIProvider


def clear_provider_env(monkeypatch):
    for name in (
        "AI_PROVIDER",
        "AI_MODEL",
        "AI_MAX_OUTPUT_TOKENS",
        "AI_TIMEOUT_SECONDS",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_FALLBACK_MODEL",
        "OPENAI_ENABLE_LIVE_TESTS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_provider_is_mock(monkeypatch):
    clear_provider_env(monkeypatch)

    provider = get_provider()

    assert isinstance(provider, MockProvider)
    assert provider.name == "mock"
    assert provider.model == "mock-basic"


def test_mock_text_response_is_deterministic():
    provider = MockProvider()
    request = LLMRequest(prompt="Summarize pantry recipes.")

    first = provider.generate_text(request)
    second = provider.generate_text(request)

    assert first == second
    assert first.provider == "mock"
    assert first.model == "mock-basic"
    assert "Summarize pantry recipes." in first.text


def test_mock_structured_response_is_schema_shaped_and_deterministic():
    provider = MockProvider()
    request = StructuredLLMRequest(
        prompt="Extract a recipe.",
        schema_name="RecipeDraft",
        schema={
            "type": "object",
            "required": ["title", "servings", "ingredients"],
            "properties": {
                "title": {"type": "string"},
                "servings": {"type": "integer"},
                "ingredients": {"type": "array", "items": {"type": "string"}},
                "optional_note": {"type": "string"},
            },
        },
    )

    first = provider.generate_structured(request)
    second = provider.generate_structured(request)

    assert first == second
    assert first.provider == "mock"
    assert first.data["title"] == "mock-value"
    assert first.data["servings"] == 1
    assert first.data["ingredients"] == ["mock-value"]
    assert "optional_note" not in first.data
    assert first.data["_mock"]["schema_name"] == "RecipeDraft"


def test_openai_provider_missing_key_fails_without_leaking_secret(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")

    with pytest.raises(ProviderConfigError) as exc_info:
        get_provider()

    message = str(exc_info.value)
    assert "OPENAI_API_KEY" in message
    assert "sk-" not in message


def test_openai_provider_keeps_configured_models_without_live_call(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-offline-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_FALLBACK_MODEL", "gpt-5.4-mini")

    provider = OpenAIProvider(
        api_key="fake-offline-key",
        model=get_ai_settings().openai_model,
        fallback_model=get_ai_settings().openai_fallback_model,
    )

    assert provider.model == "gpt-5.4-nano"
    assert provider.fallback_model == "gpt-5.4-mini"
    assert provider._client is None


def test_unsupported_provider_returns_controlled_error(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "unknown")

    with pytest.raises(ProviderConfigError, match="Unsupported AI_PROVIDER"):
        get_provider()
