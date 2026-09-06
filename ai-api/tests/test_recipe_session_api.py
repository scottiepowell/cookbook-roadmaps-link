from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.importer import RecipeImportProviderError
from app.providers.errors import ProviderCallError
from app import recipe_session_routes
from app.recipe_requirements import extract_recipe_requirements
from app.recipe_revision_guard import validate_recipe_revision
from app.recipe_session import default_recipe_session_store, default_recipe_start_idempotency_store
from app.retrieval_cache import reset_retrieval_cache
from app.schemas import RecipeImportDraft, RecipeImportResponse


FORBIDDEN_RESPONSE_TEXT = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    ".env",
    "raw prompt",
    "raw provider",
    "provider response",
    "Creation requirements",
    "Retrieved dataset examples",
    "C:\\",
    "/Users/",
    "/home/",
    ".tmp-ai-demo",
    "Traceback",
    "COOKBOOK_DB_PATH",
    "cookbook_db_path",
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
        "AI_PROVIDER_CALLS_ENABLED",
        "AI_PROVIDER_GLOBAL_DISABLE",
        "AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION",
        "AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION",
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL",
        "AI_PROVIDER_BUDGET_MODE",
        "AI_PROVIDER_BUDGET_SESSION_ID",
        "AI_OPERATOR_GATE_ENABLED",
        "AI_OPERATOR_GATE_TOKEN_FINGERPRINT",
        "AI_OPERATOR_GATE_TOKEN",
        "AI_OPERATOR_GATE_ALLOWED_WORKFLOWS",
        "AI_OPERATOR_GATE_LOCAL_BYPASS",
    ):
        monkeypatch.delenv(name, raising=False)


def write_session_dataset(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "cheesecake-1,Classic Baked Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham cracker crust; melted butter\",\"Preheat oven; Press graham cracker crust; Beat cream cheese sugar vanilla and eggs; Bake until just set; Cool and chill\",dessert\n"
        "no-bake-cheesecake-1,No-Bake Cheesecake Bars,\"cream cheese; sugar; vanilla; graham cracker crust; butter\",\"Mix crust; Beat filling; Spread into crust; Chill until firm\",dessert\n"
        "carbonara-1,Spaghetti Carbonara,\"spaghetti; eggs; parmesan; pancetta; black pepper; pasta water\",\"Boil spaghetti; Crisp pancetta; Toss off heat with eggs parmesan and pasta water\",dinner\n"
        "omelet-1,Cheese Omelet,\"eggs; cheddar cheese; onion; butter\",\"Beat eggs; Cook in skillet; Add cheese; Fold omelet\",breakfast\n"
        "casserole-1,Chicken and Rice Casserole,\"cooked chicken; rice; cream of chicken soup; cheddar cheese\",\"Preheat oven; Combine ingredients; Bake until hot and bubbly\",dinner\n"
        "crumble-1,Apple Crumble with Cream,\"apples; sugar; butter; cream; oats\",\"Slice apples; Mix topping; Bake\",dessert\n",
        encoding="utf-8",
    )


@pytest.fixture()
def session_client(tmp_path, monkeypatch):
    clear_provider_env(monkeypatch)
    reset_retrieval_cache()
    default_recipe_session_store.clear()
    default_recipe_start_idempotency_store.clear()
    dataset_dir = tmp_path / "dataset"
    write_session_dataset(dataset_dir)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_ENABLED", "true")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_MAX_ENTRIES", "128")
    monkeypatch.setenv("AI_RETRIEVAL_CACHE_TTL_SECONDS", "900")
    yield TestClient(app), dataset_dir
    default_recipe_session_store.clear()
    default_recipe_start_idempotency_store.clear()


def test_start_request_replay_returns_same_session_without_second_generation(session_client, monkeypatch):
    client, _dataset_dir = session_client
    original_import = recipe_session_routes.import_recipe_text
    calls = 0

    def counted_import(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original_import(*args, **kwargs)

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", counted_import)
    payload = {
        "text": "green chile enchiladas with chicken cauliflower and cheese",
        "request_id": "opaque_initial_request_0001",
    }

    first = client.post("/ai/recipe-session/start", json=payload)
    second = client.post("/ai/recipe-session/start", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["interaction_id"] == second.json()["interaction_id"]
    assert calls == 1
    assert default_recipe_session_store.count() == 1


def test_start_request_retry_resumes_failed_session(session_client, monkeypatch):
    client, _dataset_dir = session_client
    original_import = recipe_session_routes.import_recipe_text
    calls = 0

    def fail_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RecipeImportProviderError("safe transient failure")
        return original_import(*args, **kwargs)

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", fail_once)
    payload = {
        "text": "green chile enchiladas with chicken cauliflower and cheese",
        "request_id": "opaque_initial_request_0002",
    }

    first = client.post("/ai/recipe-session/start", json=payload)
    second = client.post("/ai/recipe-session/start", json=payload)

    assert first.status_code == 503
    assert second.status_code == 200
    assert calls == 2
    assert default_recipe_session_store.count() == 1
    assert second.json()["revision_count"] == 0


def test_start_request_rejects_conflicting_key_reuse(session_client):
    client, _dataset_dir = session_client
    request_id = "opaque_initial_request_0003"

    first = client.post(
        "/ai/recipe-session/start",
        json={"text": "green chile enchiladas with chicken", "request_id": request_id},
    )
    conflict = client.post(
        "/ai/recipe-session/start",
        json={"text": "black bean soup with carrots", "request_id": request_id},
    )

    assert first.status_code == 200
    assert conflict.status_code == 409
    assert default_recipe_session_store.count() == 1


def test_start_detailed_cheesecake_generates_draft(session_client):
    client, dataset_dir = session_client

    response = client.post(
        "/ai/recipe-session/start",
        json={
            "text": "classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight"
        },
    )

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "draft_generated"
    assert data["interaction_id"]
    assert data["draft"]["title"]
    assert data["draft_summary"]["servings"] == 4
    assert data["requirements"]["dish_intent"]["value"] == "cheesecake"
    assert data["requirements"]["confidence_label"] == "high"
    assert data["retrieval"]["retrieved_count"] > 0
    assert data["citations"]
    assert data["support_level"] in {"strong", "moderate", "weak", "none"}


def test_start_vague_request_returns_one_clarification_without_draft(session_client):
    client, dataset_dir = session_client

    response = client.post("/ai/recipe-session/start", json={"text": "make dessert"})

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "clarification_needed"
    assert data["clarification_question"]
    assert len(data["requirements"]["open_questions"]) == 1
    assert data["draft"] is None
    assert data["retrieval"] is None
    assert data["citations"] == []


def test_start_unusable_input_returns_rejected(session_client):
    client, dataset_dir = session_client

    for text in ("", "!!!!!"):
        response = client.post("/ai/recipe-session/start", json={"text": text})

        assert response.status_code == 200
        data = response.json()
        _assert_safe_response(response.text, dataset_dir)
        assert data["response_state"] == "rejected"
        assert data["draft"] is None
        assert data["retrieval"] is None
        assert data["warnings"]


def test_get_existing_session_returns_safe_state(session_client):
    client, dataset_dir = session_client
    started = client.post("/ai/recipe-session/start", json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet"}).json()

    response = client.get(f"/ai/recipe-session/{started['interaction_id']}")

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["interaction_id"] == started["interaction_id"]
    assert data["requirements"]["dish_intent"]["value"] == "omelet"
    assert data["revision_count"] == 0
    assert data["expires_at"]


def test_message_no_bake_refreshes_rag_and_revises_draft(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    ).json()

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "actually make it no-bake"},
    )

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "rag_refreshed"
    assert data["rag_refreshed"] is True
    assert "cooking_method" in data["changed_fields"]
    assert "no-bake" in data["requirements"]["cooking_method"]["value"]
    assert data["draft"] is not None
    assert data["retrieval"] is not None
    assert data["revision_count"] == 1
    assert data["requirement_diff"]["previous_revision"] == 0
    assert data["requirement_diff"]["current_revision"] == 1
    assert "cooking_method" in data["requirement_diff"]["changed_fields"]
    assert "RAG refreshed" in data["revision_summary"]
    _assert_no_bake_cheesecake_draft(data)
    assert any(term in (data["retrieval"]["query"] or "").lower() for term in ("no-bake", "no bake"))


def test_general_recipe_follow_up_revises_current_draft(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "green chile enchiladas with chicken", "provider_mode": "mock"},
    ).json()
    assert started["draft"] is not None

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "add avocado and lime", "provider_mode": "mock"},
    )
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert response.status_code == 200
    assert data["draft"] is not None
    assert data["revision_count"] == 1
    assert data["max_changes"] == 10


def test_initial_session_forwards_every_user_ingredient_to_generation(session_client, monkeypatch):
    client, dataset_dir = session_client
    original_import = recipe_session_routes.import_recipe_text
    captured = []

    def capture_import(request, *args, **kwargs):
        captured.append(request.text)
        return original_import(request, *args, **kwargs)

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", capture_import)
    user_text = "green chile enchiladas with chicken, cauliflower, and cheese"
    response = client.post(
        "/ai/recipe-session/start",
        json={"text": user_text, "provider_mode": "mock"},
    )
    data = response.json()

    assert response.status_code == 200
    assert captured == [user_text]
    assert {item["value"] for item in data["requirements"]["required_ingredients"]} >= {
        "chicken",
        "cauliflower",
        "cheese",
    }
    _assert_safe_response(response.text, dataset_dir)


def test_failed_recipe_change_does_not_mutate_draft_or_revision(session_client, monkeypatch):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "green chile enchiladas with chicken", "provider_mode": "mock"},
    ).json()

    def fail_generation(*args, **kwargs):
        del args, kwargs
        provider_error = ProviderCallError(
            "temporary provider failure",
            failure_category="output_cap_or_incomplete_response",
            exception_type="IncompleteResponseError",
            safe_summary="provider output incomplete",
        )
        raise RecipeImportProviderError("Recipe importer provider failed.") from provider_error

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", fail_generation)
    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "add mushrooms", "provider_mode": "mock"},
    )
    current = default_recipe_session_store.get_session(started["interaction_id"])

    assert response.status_code == 503
    assert response.json()["detail"]["retryable"] is True
    assert current is not None
    assert current.revision_count == 0
    assert current.draft.model_dump() == started["draft"]
    assert "mushrooms" not in current.requirements.latest_user_text.lower()
    _assert_safe_response(response.text, dataset_dir)


def test_drifted_pasta_revision_is_retryable_and_does_not_mutate_session(session_client, monkeypatch):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={
            "text": "rigatoni pasta bake with chicken cream cheese and riced cauliflower",
            "provider_mode": "mock",
        },
    ).json()
    existing = default_recipe_session_store.get_session(started["interaction_id"])
    assert existing is not None
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "ingredients": [{"name": "rigatoni"}, {"name": "chicken"}, {"name": "cream cheese"}],
            "instructions": [
                {"step": 1, "text": "Boil the rigatoni until just tender."},
                {"step": 2, "text": "Combine the pasta with chicken and cream cheese, then bake."},
            ],
        }
    )
    stored = default_recipe_session_store.update_session(
        started["interaction_id"], existing.requirements, draft=previous
    )
    assert stored is not None
    drifted_data = previous.model_dump()
    drifted_data["instructions"] = [
        {"step": 1, "text": "Preheat the oven and grease a casserole dish."},
        {"step": 2, "text": "Combine rice, soup, cheese, and seasoning in the dish."},
        {"step": 3, "text": "Fold in chicken and enough liquid for the rice to cook evenly."},
        {"step": 4, "text": "Cover and bake until the rice is tender."},
    ]
    drifted = RecipeImportDraft.model_validate(drifted_data)

    def drift_generation(*args, **kwargs):
        del args, kwargs
        return RecipeImportResponse(draft=drifted, provider="mock", model="mock-basic")

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", drift_generation)
    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "add a vegetable", "provider_mode": "mock"},
    )
    current = default_recipe_session_store.get_session(started["interaction_id"])

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "unavailable",
        "safe_unavailable_category": "revision_identity_drift",
        "safe_guidance": "Cookbook AI could not preserve this recipe. One bounded retry is allowed.",
        "retryable": True,
    }
    assert current is not None
    assert current.revision_count == 0
    assert current.draft.model_dump() == previous.model_dump()
    _assert_safe_response(response.text, dataset_dir)


def test_revision_identity_guard_accepts_coherent_addition_and_explicit_base_swap():
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "ingredients": [{"name": "rigatoni"}, {"name": "chicken"}, {"name": "cream cheese"}],
            "instructions": [
                {"step": 1, "text": "Boil the rigatoni until just tender."},
                {"step": 2, "text": "Combine the pasta with chicken and cream cheese, then bake."},
            ],
        }
    )
    with_spinach_data = previous.model_dump()
    with_spinach_data["ingredients"].append({"name": "spinach"})
    with_spinach_data["instructions"][1]["text"] = (
        "Fold spinach into the pasta with chicken and cream cheese, then bake."
    )
    with_spinach = RecipeImportDraft.model_validate(with_spinach_data)

    assert validate_recipe_revision(previous, with_spinach, "add spinach").valid is True

    rice_bake_data = previous.model_dump()
    rice_bake_data["title"] = "Chicken and Rice Bake"
    rice_bake_data["ingredients"][0]["name"] = "rice"
    rice_bake_data["instructions"] = [
        {"step": 1, "text": "Cook the rice until just tender."},
        {"step": 2, "text": "Combine the rice with chicken and cream cheese, then bake."},
    ]
    rice_bake = RecipeImportDraft.model_validate(rice_bake_data)

    assert validate_recipe_revision(previous, rice_bake, "replace the pasta with rice").valid is True


def test_revision_identity_guard_accepts_cauliflower_rice_alias_without_plain_rice_drift():
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "ingredients": [
                {"name": "rigatoni"},
                {"name": "riced cauliflower"},
                {"name": "chicken"},
            ],
            "instructions": [{"step": 1, "text": "Fold riced cauliflower into the rigatoni and bake."}],
        }
    )
    candidate = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "ingredients": [{"name": "rigatoni"}, {"name": "cauliflower rice"}, {"name": "chicken"}],
            "instructions": [{"step": 1, "text": "Fold cauliflower rice and spinach into the rigatoni and bake."}],
        }
    )

    assert validate_recipe_revision(previous, candidate, "add spinach").valid is True


def test_revision_prompt_locks_recipe_identity_and_instruction_coherence():
    draft = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "ingredients": [{"name": "rigatoni"}, {"name": "chicken"}],
            "instructions": [{"step": 1, "text": "Boil rigatoni and bake it with chicken."}],
        }
    )

    prompt = recipe_session_routes._revision_generation_text(draft, "add a vegetable")

    assert "LOCKED INVARIANTS" in prompt
    assert "preserve the dish identity, base starch, protein, cooking method" in prompt
    assert "Every instruction must still describe the current dish" in prompt
    assert "scale every numeric ingredient quantity" in prompt
    assert "Requested change: add a vegetable" in prompt


def test_chained_serving_changes_override_provider_yield_and_scale_all_quantities(session_client, monkeypatch):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "rigatoni pasta bake with chicken and spinach", "provider_mode": "mock"},
    ).json()
    existing = default_recipe_session_store.get_session(started["interaction_id"])
    assert existing is not None
    previous = RecipeImportDraft.model_validate(
        {
            "title": "Chicken Rigatoni Pasta Bake",
            "servings": 4,
            "ingredients": [
                {"name": "rigatoni", "quantity": "12", "unit": "oz"},
                {"name": "chicken", "quantity": "1 1/2", "unit": "lb"},
                {"name": "spinach", "quantity": "2-3", "unit": "cups"},
                {"name": "salt", "quantity": None},
            ],
            "instructions": [{"step": 1, "text": "Boil the rigatoni, combine with chicken, and bake."}],
        }
    )
    stored = default_recipe_session_store.update_session(
        started["interaction_id"], existing.requirements, draft=previous
    )
    assert stored is not None

    def inconsistent_generation(*args, **kwargs):
        del args, kwargs
        candidate = previous.model_copy(update={"servings": 2}, deep=True)
        return RecipeImportResponse(draft=candidate, provider="mock", model="mock-basic")

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", inconsistent_generation)

    eight_response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "change to eight servings", "provider_mode": "mock"},
    )
    eight = eight_response.json()
    sixteen_response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "change to 16 servings", "provider_mode": "mock"},
    )
    sixteen = sixteen_response.json()

    assert eight_response.status_code == 200
    assert eight["draft"]["servings"] == 8
    assert [item["quantity"] for item in eight["draft"]["ingredients"]] == ["24", "3", "4-6", None]
    assert eight["requirements"]["serving_count"] == {"value": 8, "source": "user-provided"}
    assert eight["revision_count"] == 1
    assert sixteen_response.status_code == 200
    assert sixteen["draft"]["servings"] == 16
    assert [item["quantity"] for item in sixteen["draft"]["ingredients"]] == ["48", "6", "8-12", None]
    assert sixteen["requirements"]["serving_count"] == {"value": 16, "source": "user-provided"}
    assert sixteen["revision_count"] == 2
    _assert_safe_response(eight_response.text, dataset_dir)
    _assert_safe_response(sixteen_response.text, dataset_dir)


def test_mixed_serving_revision_rejects_wrong_provider_yield_without_mutation(session_client, monkeypatch):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "rigatoni pasta bake with chicken", "provider_mode": "mock"},
    ).json()
    previous = RecipeImportDraft.model_validate(started["draft"])
    wrong_yield = previous.model_copy(update={"servings": 2}, deep=True)

    def inconsistent_generation(*args, **kwargs):
        del args, kwargs
        return RecipeImportResponse(draft=wrong_yield, provider="mock", model="mock-basic")

    monkeypatch.setattr(recipe_session_routes, "import_recipe_text", inconsistent_generation)
    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "make 8 servings and add spinach", "provider_mode": "mock"},
    )
    current = default_recipe_session_store.get_session(started["interaction_id"])

    assert response.status_code == 503
    assert response.json()["detail"]["safe_unavailable_category"] == "serving_scale_mismatch"
    assert response.json()["detail"]["retryable"] is True
    assert current is not None
    assert current.revision_count == 0
    assert current.draft.model_dump() == started["draft"]
    _assert_safe_response(response.text, dataset_dir)


def test_new_recipe_intent_requires_confirmation_without_replacing_draft(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet"},
    ).json()

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "make lasagna instead"},
    )
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "new_recipe_confirmation"
    assert "start a new recipe" in data["clarification_question"].lower()
    assert data["draft"] == started["draft"]
    assert data["revision_count"] == 0


def test_ten_change_limit_blocks_another_revision(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet"},
    ).json()
    session = default_recipe_session_store.get_session(started["interaction_id"])
    limited_requirements = session.requirements.model_copy(update={"revision_count": 10}, deep=True)
    default_recipe_session_store.update_session(started["interaction_id"], limited_requirements)

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "add mushrooms"},
    )
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "change_limit_reached"
    assert data["revision_count"] == 10
    assert data["draft"] == started["draft"]


def test_message_chatter_reuses_draft_and_formatting_creates_revision(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper no heavy cream"},
    ).json()

    chatter = client.post(f"/ai/recipe-session/{started['interaction_id']}/message", json={"text": "thanks"})
    chatter_data = chatter.json()
    _assert_safe_response(chatter.text, dataset_dir)
    assert chatter_data["response_state"] == "no_material_change"
    assert chatter_data["revision_count"] == 0

    formatting = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "make it shorter"},
    )
    formatting_data = formatting.json()
    _assert_safe_response(formatting.text, dataset_dir)
    assert formatting_data["response_state"] == "draft_revised"
    assert formatting_data["rag_refreshed"] is False
    assert formatting_data["revision_count"] == 1
    assert formatting_data["draft"] is not None


def test_repeated_no_refresh_messages_keep_existing_draft_without_refresh(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet"},
    ).json()

    for text in ("thanks", "looks good"):
        response = client.post(f"/ai/recipe-session/{started['interaction_id']}/message", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        _assert_safe_response(response.text, dataset_dir)
        assert data["response_state"] == "no_material_change"
        assert data["rag_refreshed"] is False
        assert data["draft"] is not None
        assert data["changed_fields"] == []


def test_follow_up_before_draft_exists_stays_safe(session_client):
    client, dataset_dir = session_client
    started = client.post("/ai/recipe-session/start", json={"text": "make dessert"}).json()

    response = client.post(f"/ai/recipe-session/{started['interaction_id']}/message", json={"text": "thanks"})

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "no_material_change"
    assert data["draft"] is None
    assert data["retrieval"] is None


def test_material_follow_ups_refresh_for_equipment_and_exclusions(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    ).json()

    air_fryer = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "use air fryer instead"},
    )
    assert air_fryer.status_code == 200
    air_fryer_data = air_fryer.json()
    _assert_safe_response(air_fryer.text, dataset_dir)
    assert air_fryer_data["rag_refreshed"] is True
    assert "equipment_constraints" in air_fryer_data["changed_fields"]
    assert air_fryer_data["requirements"]["equipment_constraints"][0]["value"] == "air fryer"

    no_nuts = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "no nuts"},
    )
    assert no_nuts.status_code == 200
    no_nuts_data = no_nuts.json()
    _assert_safe_response(no_nuts.text, dataset_dir)
    assert no_nuts_data["rag_refreshed"] is True
    assert "excluded_ingredients" in no_nuts_data["changed_fields"]
    assert any(item["value"] == "nuts" for item in no_nuts_data["requirements"]["excluded_ingredients"])


def test_contradictory_method_follow_up_is_controlled_and_safe(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    ).json()

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "make it no-bake but bake it overnight"},
    )

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "rag_refreshed"
    assert data["rag_refreshed"] is True
    assert "cooking_method" in data["changed_fields"]
    assert data["draft"] is not None


def test_clarification_answer_updates_session_and_generates(session_client):
    client, dataset_dir = session_client
    started = client.post("/ai/recipe-session/start", json={"text": "make dessert"}).json()

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "cheesecake with cream cheese and graham cracker crust"},
    )

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] in {"rag_refreshed", "draft_revised"}
    assert data["requirements"]["dish_intent"]["value"] == "cheesecake"
    assert data["requirements"]["resolved_questions"]
    assert data["draft"] is not None
    assert data["revision_count"] == 0
    assert data["max_changes"] == 10


def test_clarification_answer_no_bake_cheesecake_preserves_method_in_draft(session_client):
    client, dataset_dir = session_client
    started = client.post("/ai/recipe-session/start", json={"text": "make dessert"}).json()

    response = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "cheesecake, no-bake, for 4 people"},
    )

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] in {"rag_refreshed", "draft_revised"}
    assert data["requirements"]["dish_intent"]["value"] == "cheesecake"
    assert data["requirements"]["cooking_method"]["value"] == "no-bake"
    assert data["requirements"]["resolved_questions"]
    assert data["requirements"]["open_questions"] == []
    assert data["draft"] is not None
    assert any(field in data["changed_fields"] for field in ("dish_intent", "cooking_method"))
    assert any(term in (data["retrieval"]["query"] or "").lower() for term in ("no-bake", "no bake"))
    _assert_no_bake_cheesecake_draft(data)


def test_finalize_session_with_draft_is_demo_safe(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly"},
    ).json()

    response = client.post(f"/ai/recipe-session/{started['interaction_id']}/finalize", json={"format": "draft_json"})

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "ready_to_finalize"
    assert data["draft"] is not None
    assert any("no production cookbook write-back" in warning.lower() for warning in data["warnings"])


def test_finalize_before_draft_is_demo_safe(session_client):
    client, dataset_dir = session_client
    started = client.post("/ai/recipe-session/start", json={"text": "make dessert"}).json()

    response = client.post(f"/ai/recipe-session/{started['interaction_id']}/finalize", json={})

    assert response.status_code == 200
    data = response.json()
    _assert_safe_response(response.text, dataset_dir)
    assert data["response_state"] == "clarification_needed"
    assert data["draft"] is None
    assert any("no generated draft" in warning.lower() for warning in data["warnings"])


def test_repeated_finalize_is_idempotent_for_demo_warning(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly"},
    ).json()

    first = client.post(f"/ai/recipe-session/{started['interaction_id']}/finalize", json={})
    second = client.post(f"/ai/recipe-session/{started['interaction_id']}/finalize", json={})

    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    _assert_safe_response(second.text, dataset_dir)
    assert data["response_state"] == "ready_to_finalize"
    assert sum(1 for warning in data["warnings"] if "no production cookbook write-back" in warning.lower()) == 1


def test_missing_and_expired_sessions_return_safe_404(session_client):
    client, dataset_dir = session_client

    for method, path, kwargs in (
        ("get", "/ai/recipe-session/not-real", {}),
        ("post", "/ai/recipe-session/not-real/message", {"json": {"text": "thanks"}}),
        ("post", "/ai/recipe-session/not-real/finalize", {"json": {}}),
    ):
        missing = getattr(client, method)(path, **kwargs)
        assert missing.status_code == 404
        _assert_safe_response(missing.text, dataset_dir)
        assert missing.json()["detail"]["response_state"] == "not_found"

    expired_requirements = extract_recipe_requirements("cheesecake with cream cheese sugar eggs vanilla graham cracker crust")
    default_recipe_session_store.create_session(
        expired_requirements,
        now=datetime(2000, 1, 1, tzinfo=UTC),
        interaction_id="expired-session",
    )
    for method, path, kwargs in (
        ("get", "/ai/recipe-session/expired-session", {}),
        ("post", "/ai/recipe-session/expired-session/message", {"json": {"text": "thanks"}}),
        ("post", "/ai/recipe-session/expired-session/finalize", {"json": {}}),
    ):
        expired = getattr(client, method)(path, **kwargs)
        assert expired.status_code == 404
        _assert_safe_response(expired.text, dataset_dir)
        assert expired.json()["detail"]["response_state"] == "not_found"


def test_session_flow_e2e_start_message_get_finalize(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    ).json()
    revised = client.post(
        f"/ai/recipe-session/{started['interaction_id']}/message",
        json={"text": "actually make it no-bake"},
    ).json()
    loaded = client.get(f"/ai/recipe-session/{started['interaction_id']}")
    finalized = client.post(f"/ai/recipe-session/{started['interaction_id']}/finalize", json={})

    assert revised["rag_refreshed"] is True
    assert loaded.status_code == 200
    assert finalized.status_code == 200
    _assert_safe_response(loaded.text, dataset_dir)
    _assert_safe_response(finalized.text, dataset_dir)
    assert loaded.json()["revision_count"] == 1
    assert finalized.json()["response_state"] == "ready_to_finalize"


def _assert_safe_response(text, dataset_dir):
    assert str(dataset_dir) not in text
    for forbidden in FORBIDDEN_RESPONSE_TEXT:
        assert forbidden not in text


def _assert_no_bake_cheesecake_draft(data):
    instructions = " ".join(item["text"].lower() for item in data["draft"]["instructions"])
    assert any(term in instructions for term in ("chill", "refrigerate", "serve cold"))
    for forbidden in ("preheat", "oven", "bake", "center is just set"):
        assert forbidden not in instructions
