import sqlite3

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.meal_planner import select_meal_plan_candidates
from app.schemas import MealPlanFoundationRequest, RecipeDocument


def sample_recipes() -> list[RecipeDocument]:
    return [
        RecipeDocument(
            id="1",
            title="Lemon Beans",
            description="Bright pantry dinner",
            ingredients=["beans", "lemon", "olive oil"],
            instructions=["Warm beans", "Add lemon", "Serve"],
            tags=["dinner", "vegetarian"],
        ),
        RecipeDocument(
            id="2",
            title="Pasta Bake",
            description="Comfort dinner",
            ingredients=["pasta", "tomato", "cheese"],
            instructions=["Boil pasta", "Bake with cheese"],
            tags=["dinner"],
        ),
        RecipeDocument(
            id="3",
            title="Cucumber Salad",
            description="Cold lunch",
            ingredients=["cucumber", "parsley", "lemon"],
            instructions=["Chop vegetables", "Toss together"],
            tags=["lunch", "vegetarian"],
        ),
    ]


def test_meal_plan_foundation_schema_validation():
    request = MealPlanFoundationRequest(
        days=2,
        meals_per_day=2,
        query="   ",
        include_tags=[" Dinner ", "dinner", ""],
        exclude_ingredients=[" Cheese ", "cheese"],
        candidate_limit=4,
    )

    assert request.days == 2
    assert request.meals_per_day == 2
    assert request.query is None
    assert request.include_tags == ["dinner"]
    assert request.exclude_ingredients == ["cheese"]
    assert request.candidate_limit == 4

    with pytest.raises(ValidationError):
        MealPlanFoundationRequest(days=0)

    with pytest.raises(ValidationError):
        MealPlanFoundationRequest(meals_per_day=5)


def test_selects_saved_recipe_candidates_with_citations():
    response = select_meal_plan_candidates(
        sample_recipes(),
        MealPlanFoundationRequest(days=1, meals_per_day=2, query="lemon vegetarian", candidate_limit=5),
    )

    assert [candidate.recipe_id for candidate in response.candidates] == ["1", "3"]
    assert response.candidates[0].title == "Lemon Beans"
    assert "lemon" in response.candidates[0].snippet.lower()
    assert response.selection.requested_slots == 2
    assert response.selection.selected_count == 2
    assert response.warnings == []


def test_excluded_ingredients_filter_candidates_with_warning():
    response = select_meal_plan_candidates(
        sample_recipes(),
        MealPlanFoundationRequest(
            days=1,
            meals_per_day=2,
            query="dinner",
            exclude_ingredients=["cheese"],
            candidate_limit=5,
        ),
    )

    assert [candidate.recipe_id for candidate in response.candidates] == ["1"]
    assert response.selection.excluded_recipe_ids == ["2"]
    assert "filtered" in response.warnings[0]
    assert "Fewer saved recipe candidates" in response.warnings[1]


def test_selection_uses_saved_documents_only_and_does_not_invent_recipes():
    response = select_meal_plan_candidates(
        sample_recipes(),
        MealPlanFoundationRequest(days=2, meals_per_day=2, query="dinner", candidate_limit=10),
    )

    saved_ids = {recipe.id for recipe in sample_recipes()}
    assert {candidate.recipe_id for candidate in response.candidates}.issubset(saved_ids)
    assert response.selection.selected_count == 2
    assert response.selection.requested_slots == 4
    assert response.warnings == ["Fewer saved recipe candidates were found than requested meal slots."]


def test_selection_does_not_call_provider(monkeypatch):
    def fail_get_provider():
        raise AssertionError("Meal planner foundation must not call a provider.")

    monkeypatch.setattr("app.providers.registry.get_provider", fail_get_provider)

    response = select_meal_plan_candidates(
        sample_recipes(),
        MealPlanFoundationRequest(days=1, meals_per_day=1, query="pasta"),
    )

    assert [candidate.recipe_id for candidate in response.candidates] == ["2"]


def test_selection_does_not_write_to_database(tmp_path):
    db_path = tmp_path / "recipes.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE recipes (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    connection.execute("INSERT INTO recipes (title) VALUES ('Existing')")
    connection.commit()
    connection.close()

    response = select_meal_plan_candidates(
        [RecipeDocument(id="1", title="Existing", ingredients=["beans"], instructions=["Warm beans"])],
        MealPlanFoundationRequest(days=1, meals_per_day=1, query="beans"),
    )

    assert response.candidates[0].recipe_id == "1"
    connection = sqlite3.connect(db_path)
    rows = connection.execute("SELECT id, title FROM recipes ORDER BY id").fetchall()
    connection.close()
    assert rows == [(1, "Existing")]


def test_meal_plan_endpoint_is_not_added_in_foundation_task():
    response = TestClient(app).post("/ai/meal-plan", json={})

    assert response.status_code == 404
