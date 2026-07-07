import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.rag import ask_cookbook
from app.schemas import AskRequest, RecipeDocument


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


def create_rag_fixture_db(path):
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT,
            tags TEXT,
            source_url TEXT
        )
        """
    )
    rows = [
        (
            1,
            "Lemon Beans",
            "Bright pantry dinner",
            '["beans", "lemon", "olive oil"]',
            "Warm beans\nAdd lemon\nServe",
            "dinner\nvegetarian",
            None,
        ),
        (
            2,
            "Pasta Bake",
            "Comfort dinner",
            '["pasta", "tomato", "cheese"]',
            "Boil pasta\nBake with cheese",
            "dinner",
            None,
        ),
    ]
    connection.executemany(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()
    connection.close()


def test_ask_retrieves_context_and_returns_citations():
    provider = RecordingProvider()
    recipes = [
        RecipeDocument(
            id="1",
            title="Lemon Beans",
            description="Bright pantry dinner",
            ingredients=["beans", "lemon", "olive oil"],
            instructions=["Warm beans", "Add lemon", "Serve"],
            tags=["dinner"],
        ),
        RecipeDocument(
            id="2",
            title="Toast",
            ingredients=["bread"],
            instructions=["Toast bread"],
        ),
    ]

    response = ask_cookbook(AskRequest(question="What uses lemon?", limit=2), provider=provider, recipes=recipes)

    assert response.provider == "recording"
    assert response.model == "recording-model"
    assert response.answer == "Grounded answer from retrieved context."
    assert [citation.recipe_id for citation in response.citations] == ["1"]
    assert response.citations[0].title == "Lemon Beans"
    assert "lemon" in response.citations[0].snippet.lower()
    assert response.retrieval.retrieved_count == 1
    assert "Lemon Beans" in provider.last_prompt
    assert "Toast" not in provider.last_prompt


def test_no_match_does_not_call_provider_or_invent_recipe():
    provider = FailingProvider()
    response = ask_cookbook(
        AskRequest(question="Which recipe uses saffron?", limit=3),
        provider=provider,
        recipes=[
            RecipeDocument(
                id="1",
                title="Lemon Beans",
                ingredients=["beans", "lemon"],
                instructions=["Warm beans"],
            )
        ],
    )

    assert response.answer == "I could not find a matching saved recipe for that question."
    assert response.citations == []
    assert response.provider == "none"
    assert response.retrieval.retrieved_count == 0
    assert response.warnings == ["No matching saved recipes were found; no provider call was made."]


def test_ask_endpoint_uses_mock_provider_and_cites_recipes(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_rag_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post("/ai/ask", json={"question": "What can I make with lemon?", "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["model"] == "mock-basic"
    assert data["retrieval"]["retrieved_count"] == 1
    assert data["retrieval"]["matched_recipe_ids"] == ["1"]
    assert data["citations"][0]["recipe_id"] == "1"
    assert data["citations"][0]["title"] == "Lemon Beans"
    assert "raw" not in data["citations"][0]
    assert "OPENAI_API_KEY" not in response.text
    assert "sk-" not in response.text
    assert "Authorization" not in response.text


def test_ask_endpoint_no_match_returns_controlled_response(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_rag_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post("/ai/ask", json={"question": "Which saved recipe uses saffron?"})

    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []
    assert data["provider"] == "none"
    assert data["retrieval"]["retrieved_count"] == 0
    assert data["warnings"] == ["No matching saved recipes were found; no provider call was made."]
    assert "saffron" not in data["answer"].lower()


def test_ask_endpoint_rejects_empty_question(monkeypatch):
    clear_provider_env(monkeypatch)

    response = TestClient(app).post("/ai/ask", json={"question": "   "})

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["citations"] == []
    assert data["input_quality"]["status"] == "rejected"


def test_ask_endpoint_does_not_write_to_cookbook_db(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_rag_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post("/ai/ask", json={"question": "What can I make with pasta?"})

    assert response.status_code == 200
    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, title FROM recipes ORDER BY id").fetchall()
    connection.close()
    assert rows == [(1, "Lemon Beans"), (2, "Pasta Bake")]


class RecordingProvider(LLMProvider):
    name = "recording"
    model = "recording-model"

    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        self.last_prompt = request.prompt
        return LLMResponse(
            text="Grounded answer from retrieved context.",
            provider=self.name,
            model=self.model,
            usage={"input_tokens": 10, "output_tokens": 5},
        )

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        return StructuredLLMResponse(data={}, provider=self.name, model=self.model)


class FailingProvider(LLMProvider):
    name = "failing"
    model = "failing-model"

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("Provider should not be called for no-match questions.")

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        raise AssertionError("Provider should not be called for no-match questions.")
