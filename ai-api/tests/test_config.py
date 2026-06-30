from fastapi.testclient import TestClient

from app.main import app


def test_ai_config_reports_provider_booleans(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-secret-value")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-google-secret-value")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local:11434")

    response = TestClient(app).get("/ai/config")

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "providers": {
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


def test_ai_config_defaults_to_unconfigured(monkeypatch):
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "OLLAMA_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

    response = TestClient(app).get("/ai/config")

    assert response.status_code == 200
    assert response.json() == {
        "providers": {
            "openai": {"configured": False},
            "anthropic": {"configured": False},
            "google": {"configured": False},
            "ollama": {"configured": False},
        }
    }
