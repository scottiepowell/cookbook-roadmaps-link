import sqlite3

from fastapi.testclient import TestClient

from app.importer import RecipeImportValidationError, import_recipe_text
from app.main import app
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.schemas import RecipeImportRequest


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


def test_importer_uses_mock_provider_by_default(monkeypatch):
    clear_provider_env(monkeypatch)

    response = TestClient(app).post(
        "/ai/import-recipe",
        json={
            "text": "Grandma beans: simmer beans with lemon and olive oil. Serve warm.",
            "source": "family notes",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["model"] == "mock-basic"
    assert data["draft"]["title"] == "mock-value"
    assert data["draft"]["ingredients"][0]["name"] == "mock-value"
    assert data["draft"]["instructions"][0]["step"] == 1
    assert data["draft"]["instructions"][0]["text"] == "mock-value"
    assert "OPENAI_API_KEY" not in response.text


def test_importer_service_validates_provider_output():
    provider = InvalidStructuredProvider()

    try:
        import_recipe_text(RecipeImportRequest(text="Toast bread."), provider=provider)
    except RecipeImportValidationError as exc:
        assert "invalid recipe draft" in str(exc)
    else:
        raise AssertionError("Expected invalid provider output to fail validation.")


def test_import_endpoint_rejects_empty_text(monkeypatch):
    clear_provider_env(monkeypatch)

    response = TestClient(app).post("/ai/import-recipe", json={"text": "   "})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["draft"] is None
    assert data["input_quality"]["status"] == "rejected"


def test_import_endpoint_does_not_write_to_cookbook_db(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE recipes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    connection.execute("INSERT INTO recipes (title) VALUES ('Existing')")
    connection.commit()
    connection.close()
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post(
        "/ai/import-recipe",
        json={"text": "New soup: simmer vegetables in broth."},
    )

    assert response.status_code == 200
    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, title FROM recipes ORDER BY id").fetchall()
    connection.close()
    assert rows == [(1, "Existing")]


def test_import_endpoint_returns_controlled_error_for_unsupported_provider(monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "unknown")

    response = TestClient(app).post("/ai/import-recipe", json={"text": "Toast bread."})

    assert response.status_code == 503
    assert response.json() == {"detail": "Recipe importer provider is not available."}


class InvalidStructuredProvider(LLMProvider):
    name = "invalid"
    model = "invalid-model"

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="", provider=self.name, model=self.model)

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        return StructuredLLMResponse(data={"title": "Missing body"}, provider=self.name, model=self.model)
