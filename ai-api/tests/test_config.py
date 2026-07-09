from fastapi.testclient import TestClient

from app.config import get_ai_settings
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
