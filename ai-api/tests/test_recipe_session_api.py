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
    "Creation requirements",
    "Retrieved dataset examples",
    "C:\\",
    ".tmp-ai-demo",
    "Traceback",
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

    response = client.post("/ai/recipe-session/start", json={"text": "!!!!!"})

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


def test_missing_and_expired_sessions_return_safe_404(session_client):
    client, dataset_dir = session_client

    missing = client.get("/ai/recipe-session/not-real")
    assert missing.status_code == 404
    _assert_safe_response(missing.text, dataset_dir)
    assert missing.json()["detail"]["response_state"] == "not_found"

    expired_requirements = extract_recipe_requirements("cheesecake with cream cheese sugar eggs vanilla graham cracker crust")
    default_recipe_session_store.create_session(
        expired_requirements,
        now=datetime(2000, 1, 1, tzinfo=UTC),
        interaction_id="expired-session",
    )
    expired = client.get("/ai/recipe-session/expired-session")
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
