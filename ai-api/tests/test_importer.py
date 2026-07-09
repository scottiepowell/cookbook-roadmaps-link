import sqlite3

from fastapi.testclient import TestClient

from app.importer import RecipeImportValidationError, _build_prompt, import_recipe_text
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
    assert data["draft"]["instructions"][0]["text"]
    assert data["draft"]["servings"] == 4
    assert "OPENAI_API_KEY" not in response.text


def test_importer_uses_dataset_rag_when_available(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,cuisine\n"
        "omelet-1,Cheese Omelet,\"eggs; cheese; butter\",\"Beat eggs; cook in butter; fold with cheese\",breakfast\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    provider = CapturingProvider(
        {
            "title": "Cheese Omelet",
            "description": "A simple cheese omelet.",
            "ingredients": [
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
                {"name": "cheese", "quantity": None, "unit": None, "note": None},
                {"name": "butter", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [{"step": 1, "text": "Cook the omelet in butter."}],
            "tags": ["breakfast"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(text="omelet with eggs cheese maybe onions cooked in butter fold it over"),
        provider=provider,
    )

    assert response.retrieval is not None
    assert response.retrieval.retrieved_count == 1
    assert response.citations[0].source_id == "omelet-1"
    assert "Retrieved dataset examples for structure only" in provider.last_request.prompt
    assert "Do not copy retrieved examples verbatim" in provider.last_request.prompt
    assert response.draft is not None
    assert response.draft.servings == 4
    assert response.draft.ingredients[0].quantity == "4"
    assert "estimated for 4 servings" in (response.draft.notes or "")
    assert "Beat the eggs" in response.draft.instructions[0].text


def test_importer_falls_back_when_dataset_unavailable(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path / "missing"))
    provider = CapturingProvider(
        {
            "title": "Carbonara Pasta",
            "description": "Pasta with eggs, parmesan, pancetta, and pepper.",
            "servings": None,
            "ingredients": [
                {"name": "spaghetti", "quantity": None, "unit": None, "note": None},
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
                {"name": "parmesan", "quantity": None, "unit": None, "note": None},
                {"name": "pancetta", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [
                {"step": 1, "text": "Boil pasta."},
                {"step": 2, "text": "Mix with eggs and cheese."},
            ],
            "tags": ["dinner"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(text="carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat"),
        provider=provider,
    )

    assert response.provider == "capture"
    assert response.retrieval is not None
    assert response.retrieval.retrieved_count == 0
    assert response.citations == []
    assert any("dataset" in warning.lower() for warning in response.warnings)
    assert response.draft is not None
    assert response.draft.servings == 4
    ingredient_names = [ingredient.name.lower() for ingredient in response.draft.ingredients]
    assert "heavy cream" not in ingredient_names


def test_importer_preserves_input_quality_provider_call_avoidance(monkeypatch):
    clear_provider_env(monkeypatch)
    provider = CapturingProvider({})

    response = import_recipe_text(RecipeImportRequest(text="make food"), provider=provider)

    assert response.provider == "none"
    assert response.draft is None
    assert response.input_quality is not None
    assert response.input_quality.status == "needs_clarification"
    assert provider.last_request is None


def test_importer_prompt_includes_servings_and_recipe_specific_guidance():
    prompt = _build_prompt(
        RecipeImportRequest(text="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill"),
        [],
    )

    assert "Use 4 servings unless the user states a different serving size." in prompt
    assert "Estimate missing quantities" in prompt
    assert "Cheesecake: include crust, filling, bake, cool, and chill" in prompt


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


class CapturingProvider(LLMProvider):
    name = "capture"
    model = "capture-model"

    def __init__(self, data: dict):
        self.data = data
        self.last_request: StructuredLLMRequest | None = None

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="", provider=self.name, model=self.model)

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        self.last_request = request
        return StructuredLLMResponse(data=self.data, provider=self.name, model=self.model)
