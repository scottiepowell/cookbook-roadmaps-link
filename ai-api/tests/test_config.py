from fastapi.testclient import TestClient

from app.config import DEFAULT_COOKBOOK_TARGET_URL, get_ai_settings, get_cookbook_target_url
from app.main import app


def test_ai_config_reports_provider_booleans(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-nano")
    monkeypatch.setenv("OPENAI_FALLBACK_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-secret-value")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-google-secret-value")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local:11434")

    response = TestClient(app).get("/ai/config")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "providers": {
            "mock": {"configured": True},
            "openai": {"configured": True},
            "anthropic": {"configured": False},
            "google": {"configured": True},
            "ollama": {"configured": True},
        }
    }

    response_text = response.text
    assert "fake-openai-secret-value" not in response_text
    assert "fake-google-secret-value" not in response_text
    assert "ollama.local" not in response_text
    assert "gpt-5.4-nano" not in response_text
    assert "gpt-5.4-mini" not in response_text
    assert "openai" in response_text


def test_ai_config_defaults_to_unconfigured(monkeypatch):
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "OLLAMA_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

    response = TestClient(app).get("/ai/config")

    assert response.status_code == 200
    assert response.json() == {
        "providers": {
            "mock": {"configured": True},
            "openai": {"configured": False},
            "anthropic": {"configured": False},
            "google": {"configured": False},
            "ollama": {"configured": False},
        }
    }


def test_ai_settings_reads_provider_debug_flag(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_DEBUG", "true")

    settings = get_ai_settings()

    assert settings.provider_debug is True


def test_cookbook_target_defaults_to_local_compose(monkeypatch):
    monkeypatch.delenv("COOKBOOK_TARGET_URL", raising=False)

    assert get_cookbook_target_url() == DEFAULT_COOKBOOK_TARGET_URL


def test_cookbook_target_accepts_public_http_or_https_url(monkeypatch):
    monkeypatch.setenv("COOKBOOK_TARGET_URL", "https://cookbook.roadmaps.link")
    assert get_cookbook_target_url() == "https://cookbook.roadmaps.link/"

    monkeypatch.setenv("COOKBOOK_TARGET_URL", "http://cookbook.local/app")
    assert get_cookbook_target_url() == "http://cookbook.local/app"


def test_cookbook_target_rejects_unsafe_or_ambiguous_values(monkeypatch):
    for value in (
        "javascript:alert(1)",
        "https://user:password@example.com/",
        "https://example.com/?token=secret",
        "https://example.com/#private",
        "not-a-url",
    ):
        monkeypatch.setenv("COOKBOOK_TARGET_URL", value)
        assert get_cookbook_target_url() == DEFAULT_COOKBOOK_TARGET_URL
