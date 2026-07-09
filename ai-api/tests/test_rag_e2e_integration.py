import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval_cache import reset_retrieval_cache


ALLOWED_SUPPORT_LEVELS = {"strong", "moderate", "weak", "none"}
FORBIDDEN_RESPONSE_TEXT = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    "Creation requirements",
    "Retrieved dataset examples",
    "RAG support: Dataset support",
)


def clear_provider_env(monkeypatch):
    for name in (
        "AI_PROVIDER",
        "AI_MODEL",
        "AI_MAX_OUTPUT_TOKENS",
        "AI_TIMEOUT_SECONDS",
        "AI_PROVIDER_DEBUG",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_FALLBACK_MODEL",
        "OPENAI_ENABLE_LIVE_TESTS",
        "RECIPE_DATASET_DIR",
        "RECIPE_DATASET_INDEX_LIMIT",
        "AI_RETRIEVAL_CACHE_ENABLED",
        "AI_RETRIEVAL_CACHE_MAX_ENTRIES",
        "AI_RETRIEVAL_CACHE_TTL_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def write_rag_e2e_dataset(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "cheesecake-1,Classic Baked Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham cracker crust; melted butter\",\"Preheat oven; Press graham cracker crust into pan; Beat cream cheese sugar vanilla and eggs; Bake until just set; Cool and chill overnight\",dessert\n"
        "carbonara-1,Spaghetti Carbonara,\"spaghetti; eggs; parmesan; pancetta; black pepper; pasta water\",\"Boil spaghetti; Crisp pancetta; Whisk eggs with parmesan; Toss pasta off heat with egg mixture and pasta water; Finish with black pepper\",dinner\n"
        "omelet-1,Cheese Omelet,\"eggs; cheddar cheese; onion; butter\",\"Beat eggs; Melt butter in skillet; Cook soft curds; Add cheddar and onions; Fold the omelet\",breakfast\n"
        "casserole-1,Chicken and Rice Casserole,\"cooked chicken; rice; cream of chicken soup; cheddar cheese\",\"Preheat oven; Combine chicken rice soup and cheese; Bake until hot and bubbly\",dinner\n"
        "crumble-1,Apple Crumble with Cream,\"apples; sugar; butter; cream; oats\",\"Slice apples; Mix oat topping; Bake until bubbly\",dessert\n"
        "cream-pasta-1,Creamy Garlic Pasta,\"pasta; heavy cream; garlic; parmesan\",\"Boil pasta; Simmer cream sauce; Toss together\",dinner\n"
        "toast-1,Egg Toast,\"bread; egg; butter\",\"Toast bread; Fry egg; Serve\",breakfast\n"
        "rice-bowl-1,Rice Bowl,\"rice; vegetables; soy sauce\",\"Cook rice; Top with vegetables\",lunch\n",
        encoding="utf-8",
    )


@pytest.fixture()
def rag_e2e_client(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    reset_retrieval_cache()
    dataset_dir = tmp_path / "dataset"
    write_rag_e2e_dataset(dataset_dir)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_ENABLED", "true")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_MAX_ENTRIES", "128")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_TTL_SECONDS", "900")
    return TestClient(app), dataset_dir


@pytest.mark.parametrize(
    ("text", "expected_source_id", "expected_anchor"),
    [
        (
            "classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight",
            "cheesecake-1",
            "graham cracker crust",
        ),
        (
            "carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream",
            "carbonara-1",
            "carbonara",
        ),
        (
            "omelette for 4 with eggs cheddar onions butter folded in a skillet",
            "omelet-1",
            "omelet",
        ),
        (
            "chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly",
            "casserole-1",
            "chicken and rice",
        ),
    ],
)
def test_importer_rag_e2e_strong_cases_use_real_api_route(
    rag_e2e_client,
    text,
    expected_source_id,
    expected_anchor,
):
    client, dataset_dir = rag_e2e_client

    first = client.post("/ai/import-recipe", json={"text": text})
    second = client.post("/ai/import-recipe", json={"text": text})

    assert first.status_code == 200
    assert second.status_code == 200
    first_data = first.json()
    second_data = second.json()
    _assert_complete_import_response(first_data, first.text, dataset_dir)
    _assert_complete_import_response(second_data, second.text, dataset_dir)

    retrieval = first_data["retrieval"]
    assert retrieval["retrieved_count"] > 0
    assert retrieval["matched_result_ids"]
    assert first_data["citations"]
    assert first_data["citations"][0]["source_id"] == expected_source_id
    assert expected_source_id in [citation["source_id"] for citation in first_data["citations"]]
    assert any(expected_anchor in anchor for anchor in retrieval["anchors_used"])
    assert retrieval["support_level"] in {"strong", "moderate"}
    assert retrieval["should_claim_rag_grounded"] is True
    assert retrieval["packed_count"] <= retrieval["max_examples"]
    assert retrieval["packed_count"] <= retrieval["retrieved_count"]
    assert retrieval["packed_context_chars"] <= retrieval["max_context_chars"]
    assert retrieval["cache"]["cache_enabled"] is True
    assert retrieval["cache"]["index_cache_hit"] is False

    repeated_cache = second_data["retrieval"]["cache"]
    assert repeated_cache["cache_enabled"] is True
    assert repeated_cache["index_cache_hit"] is True
    assert repeated_cache["retrieval_cache_hit"] is True
    assert repeated_cache["index_cache_key"]
    assert repeated_cache["retrieval_cache_key"]
    assert str(dataset_dir) not in repeated_cache["index_cache_key"]
    assert str(dataset_dir) not in repeated_cache["retrieval_cache_key"]


def test_importer_rag_e2e_weak_support_is_labeled_honestly(rag_e2e_client):
    client, dataset_dir = rag_e2e_client

    response = client.post("/ai/import-recipe", json={"text": "make a dessert with sugar and cream"})

    assert response.status_code == 200
    data = response.json()
    assert data["input_quality"]["status"] in {"ready", "weak_but_usable", "needs_clarification"}
    assert str(dataset_dir) not in response.text
    for forbidden in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden not in response.text

    if data["input_quality"]["status"] == "needs_clarification":
        assert data["provider"] == "none"
        assert data["draft"] is None
        return

    _assert_complete_import_response(data, response.text, dataset_dir)
    support_level = data["retrieval"]["support_level"]
    assert support_level in {"weak", "none", "moderate"}
    assert data["retrieval"]["should_claim_rag_grounded"] is False
    assert "strong" not in (data["retrieval"]["support_message"] or "").lower()
    assert data["retrieval"]["support_message"]
    assert data["warnings"] or data["draft"].get("notes") or data["retrieval"]["should_show_weak_support_warning"]


def _assert_complete_import_response(data, response_text, dataset_dir):
    assert data["draft"] is not None
    assert data["draft"]["title"]
    assert 1 <= data["draft"]["servings"] <= 24
    assert data["draft"]["ingredients"]
    assert data["draft"]["instructions"]
    assert data["provider"] == "mock"
    assert data["model"] == "mock-basic"
    assert data["input_quality"]["status"] in {"ready", "weak_but_usable"}

    retrieval = data["retrieval"]
    assert retrieval is not None
    assert retrieval["retrieved_count"] >= 0
    assert retrieval["relevance_category"]
    assert retrieval["support_level"] in ALLOWED_SUPPORT_LEVELS
    assert retrieval["support_message"]
    assert retrieval["packed_count"] <= retrieval["max_examples"]
    assert retrieval["packed_context_chars"] <= retrieval["max_context_chars"]
    assert "cache" in retrieval
    assert retrieval["cache"]["cache_enabled"] is True
    assert retrieval["cache"]["cache_entry_count"] >= 0
    assert retrieval["cache"]["cache_max_entries"] == 128
    assert retrieval["index"]["document_count"] > 0
    assert retrieval["index"]["build_metadata"]["dataset_dir"] == "configured"

    if retrieval["support_level"] != "none":
        assert data["citations"]
    for citation in data["citations"]:
        assert citation["source_id"]
        assert citation["title"]
        assert citation["snippet"]
        assert citation["provenance"]["dataset"] == "Food Ingredients and Recipes Dataset with Images"
        assert citation["provenance"]["license"] == "CC BY-SA 3.0"
        assert citation["provenance"]["source_id"] == citation["source_id"]

    assert str(dataset_dir) not in response_text
    assert "C:\\" not in response_text
    for forbidden in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden not in response_text
