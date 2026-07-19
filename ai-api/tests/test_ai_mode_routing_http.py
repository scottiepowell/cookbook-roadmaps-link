from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.demo_data import seed_demo_data
from app.main import app
from app.recipe_session import default_recipe_session_store


MOCK_PREFERENCE = {"provider_mode": "mock", "model": "mock-basic"}
LIVE_PREFERENCE = {"provider_mode": "openai", "model": "gpt-5.4-nano"}
FORBIDDEN = ("OPENAI_API_KEY", "sk-", "Authorization", "Traceback", ".env", "C:\\", "/home/")


@pytest.fixture(autouse=True)
def _clear_process_local_sessions():
    default_recipe_session_store.clear()
    yield
    default_recipe_session_store.clear()


def _configure_mock_demo(tmp_path, monkeypatch):
    paths = seed_demo_data(tmp_path)
    for name in ("OPENAI_API_KEY", "OPENAI_ENABLE_LIVE_TESTS", "OPENAI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("COOKBOOK_DB_PATH", str(paths["db_path"]))
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(paths["dataset_dir"]))
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.setenv("AI_INVITE_SESSIONS_ENABLED", "false")
    default_recipe_session_store.clear()
    return TestClient(app)


def _assert_safe(text: str, tmp_path) -> None:
    for forbidden in FORBIDDEN:
        assert forbidden not in text
    assert str(tmp_path) not in text


def test_all_provider_backed_routes_honor_explicit_mock_preference(tmp_path, monkeypatch):
    client = _configure_mock_demo(tmp_path, monkeypatch)
    responses = {
        "importer": client.post(
            "/ai/import-recipe",
            json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet", **MOCK_PREFERENCE},
        ),
        "ask": client.post("/ai/ask", json={"question": "What uses lemon?", "limit": 1, **MOCK_PREFERENCE}),
        "dataset": client.post(
            "/dataset/ask",
            json={"question": "What indexed recipe uses tomato pasta?", "limit": 1, "dataset_limit": 3, **MOCK_PREFERENCE},
        ),
        "meal": client.post(
            "/ai/meal-plan",
            json={"days": 1, "meals_per_day": 1, "preferences": "lemon", "candidate_limit": 2, **MOCK_PREFERENCE},
        ),
    }
    for name, response in responses.items():
        assert response.status_code == 200, name
        assert response.json()["provider"] == "mock"
        assert response.json()["model"] == "mock-basic"
        _assert_safe(response.text, tmp_path)

    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight", **MOCK_PREFERENCE},
    )
    assert started.status_code == 200
    assert started.json()["provider"] == "mock"
    assert started.json()["model"] == "mock-basic"
    interaction_id = started.json()["interaction_id"]
    revised = client.post(
        f"/ai/recipe-session/{interaction_id}/message",
        json={"text": "actually make it no-bake", **MOCK_PREFERENCE},
    )
    assert revised.status_code == 200
    assert revised.json()["provider"] == "mock"
    assert revised.json()["model"] == "mock-basic"
    _assert_safe(revised.text, tmp_path)


def test_live_request_without_opt_in_is_controlled_and_never_falls_back(tmp_path, monkeypatch):
    client = _configure_mock_demo(tmp_path, monkeypatch)
    requests = (
        ("/ai/import-recipe", {"text": "omelette with eggs", **LIVE_PREFERENCE}),
        ("/ai/ask", {"question": "What uses lemon?", **LIVE_PREFERENCE}),
        ("/dataset/ask", {"question": "What uses tomato pasta?", **LIVE_PREFERENCE}),
        ("/ai/meal-plan", {"days": 1, "meals_per_day": 1, **LIVE_PREFERENCE}),
        ("/ai/recipe-session/start", {"text": "omelette with eggs cheddar onions butter", **LIVE_PREFERENCE}),
    )
    for path, payload in requests:
        response = client.post(path, json=payload)
        assert response.status_code == 503
        assert "mock-basic" not in response.text
        _assert_safe(response.text, tmp_path)

    started = client.post(
        "/ai/recipe-session/start",
        json={"text": "omelette for 4 with eggs cheddar onions butter folded in a skillet", **MOCK_PREFERENCE},
    )
    assert started.status_code == 200
    response = client.post(
        f"/ai/recipe-session/{started.json()['interaction_id']}/message",
        json={"text": "actually make it no-bake", **LIVE_PREFERENCE},
    )
    assert response.status_code == 503
    assert "mock-basic" not in response.text
    _assert_safe(response.text, tmp_path)


def test_invalid_provider_and_model_preferences_are_rejected_safely(tmp_path, monkeypatch):
    client = _configure_mock_demo(tmp_path, monkeypatch)
    for preference in (
        {"provider_mode": "live", "model": "mock-basic"},
        {"provider_mode": "mock", "model": "arbitrary-model"},
        {"provider_mode": "other-provider", "model": "gpt-5.4-nano"},
    ):
        response = client.post("/ai/import-recipe", json={"text": "omelette with eggs", **preference})
        assert response.status_code == 503
        _assert_safe(response.text, tmp_path)
