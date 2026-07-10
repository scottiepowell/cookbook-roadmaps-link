from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.recipe_requirements import extract_recipe_requirements
from app.recipe_session import default_recipe_session_store
from app.retrieval_cache import reset_retrieval_cache


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


def test_message_chatter_and_formatting_do_not_refresh(session_client):
    client, dataset_dir = session_client
    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper no heavy cream"},
    ).json()

    for text in ("thanks", "make it shorter"):
        response = client.post(f"/ai/recipe-session/{started['interaction_id']}/message", json={"text": text})
        assert response.status_code == 200
        data = response.json()
        _assert_safe_response(response.text, dataset_dir)
        assert data["response_state"] == "no_material_change"
        assert data["rag_refreshed"] is False
        assert data["changed_fields"] == []


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
