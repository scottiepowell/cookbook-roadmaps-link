from fastapi.testclient import TestClient

from app.main import app


def test_app_imports_cleanly():
    assert app.title == "Cookbook AI API"


def test_health_endpoint():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-api"}
