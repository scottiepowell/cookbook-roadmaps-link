from app.schemas import RecipeDocument
from app.search import search_recipes


def sample_recipes() -> list[RecipeDocument]:
    return [
        RecipeDocument(
            id="1",
            title="Lemon Beans",
            description="Bright pantry dinner",
            ingredients=["beans", "lemon", "olive oil"],
            instructions=["Warm beans", "Add lemon", "Serve"],
            tags=["dinner", "vegetarian"],
            source="https://example.test/lemon-beans",
        ),
        RecipeDocument(
            id="2",
            title="Bean Salad",
            description="Cold lunch",
            ingredients=["white beans", "cucumber", "parsley"],
            instructions=["Chop vegetables", "Toss with beans"],
            tags=["lunch"],
        ),
        RecipeDocument(
            id="3",
            title="Pasta Bake",
            ingredients=["pasta", "tomato", "cheese"],
            instructions=["Boil pasta", "Bake with cheese"],
            tags=["dinner"],
        ),
    ]


def test_title_match_ranks_first():
    results = search_recipes(sample_recipes(), query="salad", limit=10)

    assert [result.id for result in results] == ["2"]
    assert results[0].matched_fields == ["title"]


def test_ingredient_match_works():
    results = search_recipes(sample_recipes(), query="cucumber", limit=10)

    assert [result.id for result in results] == ["2"]
    assert results[0].matched_fields == ["ingredients"]
    assert "cucumber" in results[0].snippet.lower()


def test_tag_match_works():
    results = search_recipes(sample_recipes(), query="vegetarian", limit=10)

    assert [result.id for result in results] == ["1"]
    assert results[0].matched_fields == ["tags"]


def test_no_match_returns_empty_results():
    assert search_recipes(sample_recipes(), query="chocolate", limit=10) == []


def test_empty_query_returns_empty_results():
    assert search_recipes(sample_recipes(), query="   ", limit=10) == []


def test_limit_is_respected():
    results = search_recipes(sample_recipes(), query="dinner", limit=1)

    assert len(results) == 1
    assert results[0].id == "1"
