import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.meal_plan_endpoint import create_meal_plan
from app.providers.base import LLMProvider, LLMRequest, LLMResponse, StructuredLLMRequest, StructuredLLMResponse
from app.schemas import MealPlanRequest


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


def create_meal_plan_fixture_db(path):
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
        (
            3,
            "Cucumber Salad",
            "Cold lunch",
            '["cucumber", "parsley", "lemon"]',
            "Chop vegetables\nToss together",
            "lunch\nvegetarian",
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


def test_meal_plan_rejects_invalid_request_values():
    response = TestClient(app).post("/ai/meal-plan", json={"days": 0})

    assert response.status_code == 422


def test_meal_plan_endpoint_uses_mock_and_returns_saved_citations(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_meal_plan_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post(
        "/ai/meal-plan",
        json={"days": 1, "meals_per_day": 2, "preferences": "lemon vegetarian"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["model"] == "mock-basic"
    assert data["selection"]["candidate_count"] == 2
    assert data["selection"]["matched_recipe_ids"] == ["1", "3"]
    assert [citation["recipe_id"] for citation in data["citations"]] == ["1", "3"]
    planned_ids = [
        meal["recipe_id"]
        for day in data["plan"]["days"]
        for meal in day["meals"]
    ]
    assert set(planned_ids).issubset({"1", "3"})
    assert "OPENAI_API_KEY" not in response.text
    assert "sk-" not in response.text
    assert "Authorization" not in response.text


def test_provider_prompt_receives_only_selected_candidate_context(tmp_path, monkeypatch):
    db_path = tmp_path / "recipes.sqlite"
    create_meal_plan_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))
    provider = RecordingStructuredProvider()

    response = create_meal_plan(
        MealPlanRequest(days=1, meals_per_day=1, preferences="pasta"),
        provider=provider,
    )

    assert response.selection.matched_recipe_ids == ["2"]
    assert "Pasta Bake" in provider.last_prompt
    assert "Lemon Beans" not in provider.last_prompt
    assert "Cucumber Salad" not in provider.last_prompt


def test_no_match_response_does_not_call_provider_or_invent_recipes(tmp_path, monkeypatch):
    db_path = tmp_path / "recipes.sqlite"
    create_meal_plan_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = create_meal_plan(
        MealPlanRequest(days=1, meals_per_day=1, preferences="saffron"),
        provider=FailingStructuredProvider(),
    )

    assert response.provider == "none"
    assert response.plan.days == []
    assert response.citations == []
    assert response.selection.candidate_count == 0
    assert "no provider call" in response.warnings[-1]


def test_not_enough_candidates_returns_partial_plan_and_warning(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_meal_plan_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post(
        "/ai/meal-plan",
        json={"days": 2, "meals_per_day": 2, "preferences": "dinner", "candidate_limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    planned_ids = [
        meal["recipe_id"]
        for day in data["plan"]["days"]
        for meal in day["meals"]
    ]
    assert set(planned_ids).issubset(set(data["selection"]["matched_recipe_ids"]))
    assert data["selection"]["candidate_count"] == 2
    assert any("partial" in warning.lower() for warning in data["warnings"])


def test_meal_plan_endpoint_does_not_write_to_database(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    db_path = tmp_path / "recipes.sqlite"
    create_meal_plan_fixture_db(db_path)
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(db_path))

    response = TestClient(app).post(
        "/ai/meal-plan",
        json={"days": 1, "meals_per_day": 1, "preferences": "lemon"},
    )

    assert response.status_code == 200
    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, title FROM recipes ORDER BY id").fetchall()
    connection.close()
    assert rows == [(1, "Lemon Beans"), (2, "Pasta Bake"), (3, "Cucumber Salad")]


class RecordingStructuredProvider(LLMProvider):
    name = "recording"
    model = "recording-model"

    def __init__(self) -> None:
        self.last_prompt = ""

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="", provider=self.name, model=self.model)

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        self.last_prompt = request.prompt
        return StructuredLLMResponse(
            data={
                "days": [
                    {
                        "day": 1,
                        "meals": [
                            {
                                "slot": "meal 1",
                                "recipe_id": "2",
                                "title": "Pasta Bake",
                                "reason": "Selected from saved recipe candidates.",
                            }
                        ],
                    }
                ]
            },
            provider=self.name,
            model=self.model,
            usage={"input_tokens": 10, "output_tokens": 5},
        )


class FailingStructuredProvider(LLMProvider):
    name = "failing"
    model = "failing-model"

    def generate_text(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("Provider should not be called for no-match meal plans.")

    def generate_structured(self, request: StructuredLLMRequest) -> StructuredLLMResponse:
        raise AssertionError("Provider should not be called for no-match meal plans.")
