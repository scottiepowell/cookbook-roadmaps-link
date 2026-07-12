from __future__ import annotations

from app.importer import import_recipe_text
from app.schemas import RecipeImportRequest
from tests.test_importer import CapturingProvider, clear_provider_env


def test_import_recipe_no_bake_cheesecake_regression(monkeypatch):
    clear_provider_env(monkeypatch)
    provider = CapturingProvider(
        {
            "title": "No-Bake Cheesecake",
            "description": "A chilled cheesecake.",
            "servings": None,
            "ingredients": [
                {"name": "cream cheese", "quantity": None, "unit": None, "note": None},
                {"name": "sugar", "quantity": None, "unit": None, "note": None},
                {"name": "vanilla", "quantity": None, "unit": None, "note": None},
                {"name": "graham cracker crust", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [{"step": 1, "text": "Make cheesecake."}],
            "tags": ["dessert"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(text="cheesecake, no-bake, for 4 people"),
        provider=provider,
    )

    assert response.draft is not None
    joined = " ".join(instruction.text.lower() for instruction in response.draft.instructions)
    assert any(term in joined for term in ("chill", "refrigerate", "serve cold"))
    for forbidden in ("preheat", "oven", "bake", "center is just set"):
        assert forbidden not in joined


def test_import_recipe_baked_cheesecake_regression(monkeypatch):
    clear_provider_env(monkeypatch)
    provider = CapturingProvider(
        {
            "title": "Classic Baked Cheesecake",
            "description": "A baked cheesecake.",
            "servings": None,
            "ingredients": [
                {"name": "cream cheese", "quantity": None, "unit": None, "note": None},
                {"name": "sugar", "quantity": None, "unit": None, "note": None},
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
                {"name": "vanilla", "quantity": None, "unit": None, "note": None},
                {"name": "graham cracker crust", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [{"step": 1, "text": "Make cheesecake."}],
            "tags": ["dessert"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(
            text="classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight"
        ),
        provider=provider,
    )

    assert response.draft is not None
    joined = " ".join(instruction.text.lower() for instruction in response.draft.instructions)
    assert "preheat" in joined
    assert "oven" in joined
    assert "bake" in joined
