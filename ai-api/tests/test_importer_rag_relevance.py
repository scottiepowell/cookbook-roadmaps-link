import pytest

from app.dataset_retrieval import search_dataset_recipes
from app.importer import import_recipe_text
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


def write_relevance_fixture_dataset(path):
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "cheesecake-1,Classic Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham crackers\",\"Preheat oven; Press the graham cracker crust into the pan; Beat cream cheese, sugar, and eggs until smooth; Bake until set; Cool and chill\",dessert\n"
        "crumble-1,Apple Crumble with Calvados and Creme Fraiche Ice Cream,\"apples; sugar; butter; cream; oats\",\"Prep apples; Mix topping; Bake until bubbly; Serve with ice cream\",dessert\n"
        "pearcake-1,Pear and Walnut Upside-Down Cake with Whipped Creme Fraiche,\"pears; walnuts; sugar; butter; flour\",\"Prep pan; Arrange pears; Bake the cake; Cool and invert\",dessert\n"
        "poached-1,Spiced Poached Pears with Creme Fraiche and Amaretto Cookies,\"pears; sugar; cream; spices\",\"Poach pears gently; Chill before serving\",dessert\n"
        "carbonara-1,Carbonara,\"spaghetti; eggs; parmesan; pancetta; black pepper\",\"Boil pasta; Whisk eggs and parmesan; Toss off heat with pancetta and pasta water; Serve immediately\",dinner\n"
        "cream-pasta-1,Creamy Garlic Pasta,\"pasta; cream; parmesan; garlic; butter\",\"Boil pasta; Simmer cream sauce; Toss together and serve\",dinner\n"
        "omelet-1,Cheese Omelet,\"eggs; cheese; butter; onion\",\"Beat the eggs; Cook in butter; Add cheese and onions; Fold and serve\",breakfast\n"
        "egg-toast-1,Egg Toast,\"bread; eggs; butter\",\"Toast bread; Fry an egg; Serve on toast\",breakfast\n"
        "toast-1,Tomato Toast,\"bread; tomato; butter\",\"Toast the bread; Top with tomato and butter\",breakfast\n"
        "casserole-1,Chicken and Rice Casserole,\"chicken; rice; cream soup; cheese; onion\",\"Preheat oven; Combine chicken, rice, soup, and cheese; Bake until hot and the chicken is cooked through\",dinner\n"
        "chicken-skillet-1,Lemon Chicken Skillet,\"chicken; lemon; butter; garlic\",\"Cook chicken in a skillet; Add lemon and butter; Serve\",dinner\n"
        "rice-bowl-1,Rice Bowl,\"rice; vegetables; soy sauce\",\"Cook rice; Top with vegetables and sauce\",lunch\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("query", "expected_top", "expected_distractors"),
    [
        (
            "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
            "cheesecake-1",
            ["crumble-1", "pearcake-1", "poached-1"],
        ),
        (
            "carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat",
            "carbonara-1",
            ["cream-pasta-1", "casserole-1", "rice-bowl-1"],
        ),
        (
            "omelet with eggs cheese maybe onions cooked in butter fold it over",
            "omelet-1",
            ["egg-toast-1", "toast-1", "chicken-skillet-1"],
        ),
        (
            "chicken and rice casserole chicken rice cream soup cheese bake until hot",
            "casserole-1",
            ["chicken-skillet-1", "rice-bowl-1", "cream-pasta-1"],
        ),
    ],
)
def test_importer_rag_search_prefers_dish_specific_matches(
    tmp_path,
    monkeypatch,
    query,
    expected_top,
    expected_distractors,
):
    clear_provider_env(monkeypatch)
    write_relevance_fixture_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))

    response = search_dataset_recipes(query, limit=10, dataset_limit=5000)

    assert response.count >= 3
    ordered_ids = [result.source_id for result in response.results]
    assert ordered_ids[0] == expected_top
    assert response.results[0].score >= response.results[1].score
    present_distractors = [distractor for distractor in expected_distractors if distractor in ordered_ids]
    assert present_distractors
    for distractor in present_distractors:
        assert ordered_ids.index(expected_top) < ordered_ids.index(distractor)


def test_importer_retrieval_reports_strong_matches_and_anchors(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    write_relevance_fixture_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    provider = CapturingProvider(
        {
            "title": "Classic Cheesecake (Graham Cracker Crust)",
            "description": "A cheesecake draft.",
            "ingredients": [
                {"name": "cream cheese", "quantity": None, "unit": None, "note": None},
                {"name": "graham crackers", "quantity": None, "unit": None, "note": None},
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [
                {"step": 1, "text": "Preheat the oven."},
                {"step": 2, "text": "Bake the cheesecake."},
                {"step": 3, "text": "Chill until firm."},
            ],
            "tags": ["dessert"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(text="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill"),
        provider=provider,
    )

    assert response.retrieval is not None
    assert response.retrieval.relevance_category == "strong"
    assert response.retrieval.support_level == "strong"
    assert response.retrieval.should_claim_rag_grounded is True
    assert response.retrieval.warning is None
    assert response.retrieval.retrieved_count >= 1
    assert response.retrieval.matched_result_scores == sorted(response.retrieval.matched_result_scores, reverse=True)
    assert any("cheesecake" in anchor for anchor in response.retrieval.anchors_used)
    assert any("graham cracker crust" in anchor for anchor in response.retrieval.anchors_used)
    assert response.citations[0].source_id == "cheesecake-1"
    assert "RAG support: Dataset support is strong" in provider.last_request.prompt


def test_importer_reports_weak_retrieval_warning_for_distractors_only(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    (tmp_path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "crumble-1,Apple Crumble with Calvados and Creme Fraiche Ice Cream,\"apples; sugar; butter; cream; oats\",\"Prep apples; Mix topping; Bake until bubbly; Serve with ice cream\",dessert\n"
        "pearcake-1,Pear and Walnut Upside-Down Cake with Whipped Creme Fraiche,\"pears; walnuts; sugar; butter; flour\",\"Prep pan; Arrange pears; Bake the cake; Cool and invert\",dessert\n"
        "poached-1,Spiced Poached Pears with Creme Fraiche and Amaretto Cookies,\"pears; sugar; cream; spices\",\"Poach pears gently; Chill before serving\",dessert\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    provider = CapturingProvider(
        {
            "title": "Classic Cheesecake",
            "description": "A cheesecake draft.",
            "ingredients": [
                {"name": "cream cheese", "quantity": None, "unit": None, "note": None},
                {"name": "sugar", "quantity": None, "unit": None, "note": None},
                {"name": "eggs", "quantity": None, "unit": None, "note": None},
            ],
            "instructions": [
                {"step": 1, "text": "Bake the cheesecake."},
                {"step": 2, "text": "Chill until firm."},
            ],
            "tags": ["dessert"],
            "source": None,
            "notes": None,
        }
    )

    response = import_recipe_text(
        RecipeImportRequest(text="cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill"),
        provider=provider,
    )

    assert response.retrieval is not None
    assert response.retrieval.relevance_category == "weak"
    assert response.retrieval.support_level == "weak"
    assert response.retrieval.should_claim_rag_grounded is False
    assert response.retrieval.warning is not None
    assert "weak matches" in response.retrieval.warning
    assert response.warnings[-1] == response.retrieval.warning
    assert response.citations[0].source_id == "crumble-1"


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
