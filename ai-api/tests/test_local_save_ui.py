from fastapi.testclient import TestClient

from app import main
from app.cookbook_import_commit import LocalCookbookCommitService


def draft(**overrides):
    value = {
        "title": "Lemon Beans",
        "description": "Warm beans with lemon.",
        "servings": 4,
        "ingredients": [
            {"name": "beans", "quantity": "2", "unit": "cups", "note": None},
            {"name": "lemon", "quantity": "1", "unit": "medium", "note": None},
        ],
        "instructions": [
            {"step": 1, "text": "Warm the beans gently."},
            {"step": 2, "text": "Add lemon and serve."},
        ],
        "tags": ["dinner"],
        "source": "https://example.invalid/fixture",
        "notes": "Reviewed local fixture.",
    }
    value.update(overrides)
    return value


def enabled_local(monkeypatch, target="http://127.0.0.1:3000/"):
    monkeypatch.setenv("AI_LOCAL_SAVE_ENABLED", "true")
    monkeypatch.setenv("AI_LOCAL_SAVE_APPROVED", "true")
    monkeypatch.setenv("AI_LOCAL_COOKBOOK_RUNTIME_VERIFIED", "true")
    monkeypatch.setenv("COOKBOOK_TARGET_URL", target)


def test_demo_ui_contains_local_review_panel_and_no_production_claims():
    response = TestClient(main.app).get("/demo")

    assert response.status_code == 200
    assert "Unsaved AI draft" in response.text
    assert "Run local dry-run" in response.text
    assert "production" in response.text.lower()


def test_local_routes_are_unavailable_by_default_and_do_not_write():
    main._local_save_service = LocalCookbookCommitService()
    client = TestClient(main.app)
    payload = {"draft": draft(), "idempotency_key": "ui-test"}

    dry_run = client.post("/adapter/recipes/import-candidate/dry-run", json=payload)
    commit = client.post("/adapter/recipes/import-candidate/local-commit", json=payload)

    assert dry_run.status_code == 200
    assert dry_run.json()["status"] == "unavailable"
    assert any(error["code"] == "disabled" for error in dry_run.json()["errors"])
    assert commit.json()["status"] == "unavailable"
    assert "OPENAI_API_KEY" not in commit.text


def test_enabled_local_routes_return_dry_run_and_safe_commit(monkeypatch):
    enabled_local(monkeypatch)
    main._local_save_service = LocalCookbookCommitService()
    client = TestClient(main.app)
    payload = {"draft": draft(), "idempotency_key": "ui-test"}

    dry_run = client.post("/adapter/recipes/import-candidate/dry-run", json=payload)
    commit = client.post("/adapter/recipes/import-candidate/local-commit", json=payload)

    assert dry_run.json()["status"] == "ready"
    assert dry_run.json()["result"]["status"] == "valid"
    assert commit.json()["status"] == "committed"
    assert commit.json()["local_recipe_id"]
    assert "beans" not in commit.text
    assert "prompt" not in commit.text.lower()


def test_exposed_target_keeps_local_routes_unavailable(monkeypatch):
    enabled_local(monkeypatch, "https://cookbook.roadmaps.link/")
    client = TestClient(main.app)

    response = client.post("/adapter/recipes/import-candidate/dry-run", json={"draft": draft()})

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert any(error["code"] == "non_local_target" for error in response.json()["errors"])
    assert "cookbook.roadmaps.link" not in response.text


def test_invalid_draft_returns_safe_field_errors_when_local_enabled(monkeypatch):
    enabled_local(monkeypatch)
    response = TestClient(main.app).post(
        "/adapter/recipes/import-candidate/dry-run",
        json={"draft": draft(title="", instructions=[]), "idempotency_key": "invalid"},
    )

    assert response.json()["status"] == "ready"
    assert response.json()["result"]["status"] == "invalid"
    assert {error["field"] for error in response.json()["result"]["errors"]} >= {"title", "instructions"}
    assert "provider body" not in response.text.lower()
