from fractions import Fraction

import pytest

from app.recipe_scaling import (
    draft_contains_ingredient,
    is_additive_serving_change,
    is_serving_only_change,
    requested_serving_count,
    scale_additive_recipe_draft,
    scale_quantity_text,
    scale_recipe_draft,
    normalize_added_ingredient_quantities,
    normalize_scaled_ingredient,
)
from app.schemas import RecipeImportDraft, RecipeIngredientDraft


@pytest.mark.parametrize(
    ("message", "current", "expected"),
    (
        ("change to eight servings", 4, 8),
        ("make 16 servings", 8, 16),
        ("make it serve 8", 4, 8),
        ("servings: 12", 4, 12),
        ("double the recipe", 4, 8),
        ("halve this recipe", 8, 4),
        ("double the recipe", 16, None),
    ),
)
def test_requested_serving_count(message, current, expected):
    assert requested_serving_count(message, current) == expected


@pytest.mark.parametrize(
    ("message", "expected"),
    (
        ("change to eight servings", True),
        ("please double the recipe", True),
        ("make 8 servings and add spinach", False),
        ("add spinach", False),
    ),
)
def test_serving_only_change_detection(message, expected):
    assert is_serving_only_change(message, 4) is expected


def test_additive_serving_change_detection():
    assert is_additive_serving_change("add potato's and double the servings", 4) is True
    assert is_additive_serving_change("replace potato and double the servings", 4) is False


@pytest.mark.parametrize(
    ("quantity", "ratio", "expected"),
    (
        ("12", Fraction(2), "24"),
        ("1.5", Fraction(2), "3"),
        ("1 1/2", Fraction(2), "3"),
        ("1/2", Fraction(4), "2"),
        ("2-3", Fraction(2), "4-6"),
        ("1 to 2", Fraction(2), "2 to 4"),
        ("1½", Fraction(2), "3"),
        (None, Fraction(2), None),
        ("to taste", Fraction(2), "to taste"),
    ),
)
def test_scale_quantity_text(quantity, ratio, expected):
    assert scale_quantity_text(quantity, ratio) == expected


def test_scale_recipe_draft_preserves_identity_and_scales_every_numeric_quantity():
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "description": "A pasta bake.",
            "servings": 4,
            "ingredients": [
                {"name": "rigatoni", "quantity": "12", "unit": "oz"},
                {"name": "chicken", "quantity": "1 1/2", "unit": "lb"},
                {"name": "pepper", "quantity": "1/2", "unit": "tsp"},
                {"name": "spinach", "quantity": "2-3", "unit": "cups"},
                {"name": "salt", "quantity": None, "unit": None},
            ],
            "instructions": [{"step": 1, "text": "Boil rigatoni, combine, and bake."}],
            "tags": ["pasta"],
        }
    )
    inconsistent_candidate = RecipeImportDraft.model_validate(
        {
            "title": "Changed title",
            "servings": 2,
            "ingredients": [{"name": "rigatoni", "quantity": "12", "unit": "oz"}],
            "instructions": [
                {"step": 1, "text": "Boil the rigatoni and divide between two baking dishes."}
            ],
        }
    )

    scaled = scale_recipe_draft(previous, inconsistent_candidate, 8)

    assert scaled.title == previous.title
    assert scaled.description == previous.description
    assert scaled.servings == 8
    assert [item.name for item in scaled.ingredients] == [item.name for item in previous.ingredients]
    assert [item.quantity for item in scaled.ingredients] == ["24", "3", "1", "4-6", None]
    assert scaled.tags == ["pasta"]
    assert "two baking dishes" in scaled.instructions[0].text


def test_additive_scale_scales_existing_items_and_keeps_new_ingredient():
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Omelet",
            "servings": 4,
            "ingredients": [
                {"name": "Eggs", "quantity": "8"},
                {"name": "Mushrooms", "quantity": "12", "unit": "oz"},
            ],
            "instructions": [{"step": 1, "text": "Cook the eggs and mushrooms."}],
        }
    )
    candidate = RecipeImportDraft.model_validate(
        {
            "title": "Potato Omelet",
            "servings": 4,
            "ingredients": [
                {"name": "eggs", "quantity": "8"},
                {"name": "mushroom", "quantity": "12", "unit": "oz"},
                {"name": "potatoes", "quantity": "2", "unit": "cups"},
            ],
            "instructions": [{"step": 1, "text": "Cook the potatoes, eggs, and mushrooms."}],
        }
    )

    scaled = scale_additive_recipe_draft(previous, candidate, 8)

    assert scaled.servings == 8
    assert [item.quantity for item in scaled.ingredients] == ["16", "24", "4"]
    assert [item.name for item in scaled.ingredients] == ["Eggs", "Mushrooms", "potatoes"]
    assert draft_contains_ingredient(scaled, "potato") is True


@pytest.mark.parametrize(
    ("quantity", "unit", "name", "expected_unit", "expected_name"),
    (("1", "tablespoon", "oil", "tablespoon", "oil"), ("2", "tablespoon", "oil", "tablespoons", "oil"),
     ("1", "cup", "water", "cup", "water"), ("2", "cup", "water", "cups", "water"),
     ("1", None, "onions", None, "onion"), ("2", None, "onion", None, "onions"),
     ("1", None, "cloves", None, "clove"), ("6", None, "clove", None, "cloves"),
     ("1", None, "eggs", None, "egg"), ("2", None, "egg", None, "eggs")),
)
def test_normalize_scaled_ingredient_grammar(quantity, unit, name, expected_unit, expected_name):
    ingredient = RecipeIngredientDraft(name=name, quantity=quantity, unit=unit)
    normalized = normalize_scaled_ingredient(ingredient)
    assert normalized.unit == expected_unit
    assert normalized.name == expected_name


def test_normalize_added_mushroom_outlier_for_baked_ziti():
    previous = RecipeImportDraft.model_validate({
        "title": "Baked Ziti", "servings": 4,
        "ingredients": [{"name": "ziti", "quantity": "16", "unit": "oz"}],
        "instructions": [{"step": 1, "text": "Bake the ziti."}],
    })
    candidate = RecipeImportDraft.model_validate({"title": "Baked Ziti", "servings": 8, "ingredients": [
        {"name": "ziti", "quantity": "32", "unit": "oz"},
        {"name": "mushrooms", "quantity": "32", "unit": "oz"},
    ], "instructions": [{"step": 1, "text": "Bake the ziti."}]})
    normalized = normalize_added_ingredient_quantities(previous, candidate, ("mushrooms",), 8)
    mushrooms = next(item for item in normalized.ingredients if "mushroom" in item.name.casefold())
    assert mushrooms.quantity == "16"
    assert "normalized" in (mushrooms.note or "")


def test_normalize_added_mushroom_accepts_reasonable_amounts_and_extra_override():
    previous = RecipeImportDraft.model_validate({
        "title": "Baked Ziti", "servings": 4,
        "ingredients": [{"name": "ziti", "quantity": "16", "unit": "oz"}],
        "instructions": [{"step": 1, "text": "Bake the ziti."}],
    })
    for amount in ("8", "12", "16"):
        candidate = RecipeImportDraft.model_validate({"title": "Baked Ziti", "servings": 8, "ingredients": [
            {"name": "ziti", "quantity": "32", "unit": "oz"},
            {"name": "mushrooms", "quantity": amount, "unit": "oz"},
        ], "instructions": [{"step": 1, "text": "Bake the ziti."}]})
        normalized = normalize_added_ingredient_quantities(previous, candidate, ("mushrooms",), 8)
        assert next(item for item in normalized.ingredients if "mushroom" in item.name.casefold()).quantity == amount
    extra = RecipeImportDraft.model_validate({"title": "Baked Ziti", "servings": 8, "ingredients": [
        {"name": "ziti", "quantity": "32", "unit": "oz"},
        {"name": "mushrooms", "quantity": "32", "unit": "oz"},
    ], "instructions": [{"step": 1, "text": "Bake the ziti."}]})
    assert next(item for item in normalize_added_ingredient_quantities(previous, extra, ("mushrooms",), 8, allow_extra=True).ingredients if "mushroom" in item.name.casefold()).quantity == "32"
