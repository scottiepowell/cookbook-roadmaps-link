from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai_access_models import AiAccessWorkflow, AiProviderBudgetStatus
from app.ai_budget_guard import check_provider_budget, reset_provider_budget_tracker
from app.ai_invite_sessions import AiInviteSessionStore, InviteSessionError, default_invite_session_store
from app.main import app
from app.recipe_session import default_recipe_session_store
from app.retrieval_cache import reset_retrieval_cache
from app.schemas import AiInviteGrantCreateRequest


FORBIDDEN_STRINGS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    "X-AI-Operator-Token",
    "X-AI-Demo-Session-Token: real",
    ".env",
    ".tmp-ai-demo",
    "raw_provider_prompt",
    "raw_provider_response",
    "C:\\Users\\",
    "/home/",
    "postgres://",
    "redis://",
)


def _assert_safe(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in serialized


def _write_dataset(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "cheesecake-1,Classic Baked Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham cracker crust; melted butter\",\"Preheat oven; Press crust; Beat filling; Bake until set; Cool and chill\",dessert\n"
        "carbonara-1,Spaghetti Carbonara,\"spaghetti; eggs; parmesan; pancetta; black pepper; pasta water\",\"Boil spaghetti; Crisp pancetta; Toss off heat\",dinner\n"
        "omelet-1,Cheese Omelet,\"eggs; cheddar cheese; onion; butter\",\"Beat eggs; Cook in skillet; Fold omelet\",breakfast\n"
        "casserole-1,Chicken and Rice Casserole,\"cooked chicken; rice; cream of chicken soup; cheddar cheese\",\"Combine; Bake until hot and bubbly\",dinner\n"
        "crumb-1,Apple Crumble,\"apples; sugar; butter; oats\",\"Bake until bubbly\",dessert\n",
        encoding="utf-8",
    )


@pytest.fixture(autouse=True)
def _clear_state(monkeypatch):
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
        "AI_INVITE_SESSIONS_ENABLED",
        "AI_INVITE_SESSION_TTL_SECONDS",
        "AI_INVITE_GRANT_TTL_SECONDS",
        "AI_INVITE_MAX_SESSIONS_PER_GRANT",
        "AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS",
        "AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD",
        "AI_INVITE_ALLOWED_WORKFLOWS",
        "AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    reset_provider_budget_tracker()
    default_recipe_session_store.clear()
    default_invite_session_store.reset()
    reset_retrieval_cache()
    yield
    reset_provider_budget_tracker()
    default_recipe_session_store.clear()
    default_invite_session_store.reset()
    reset_retrieval_cache()


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    dataset_dir = tmp_path / "dataset"
    _write_dataset(dataset_dir)
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_PROVIDER_CALLS_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER_GLOBAL_DISABLE", "false")
    monkeypatch.setenv("AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION", "10")
    monkeypatch.setenv("AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL", "12000")
    monkeypatch.setenv("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL", "1200")
    monkeypatch.setenv("AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL", "14000")
    monkeypatch.setenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION", "1.00")
    monkeypatch.setenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL", "0.25")
    monkeypatch.setenv("AI_PROVIDER_BUDGET_MODE", "enforce")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "true")
    monkeypatch.setenv("AI_INVITE_SESSIONS_ENABLED", "true")
    monkeypatch.setenv("AI_INVITE_SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("AI_INVITE_GRANT_TTL_SECONDS", "3600")
    monkeypatch.setenv("AI_INVITE_MAX_SESSIONS_PER_GRANT", "1")
    monkeypatch.setenv("AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS", "5")
    monkeypatch.setenv("AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD", "0.50")
    monkeypatch.setenv("AI_INVITE_ALLOWED_WORKFLOWS", "importer,dataset_ask,recipe_session,meal_plan")
    monkeypatch.setenv("AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED", "true")
    return TestClient(app)


def test_invite_feature_disabled_returns_safe_disabled_response(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    monkeypatch.setenv("AI_INVITE_SESSIONS_ENABLED", "false")

    response = client.post("/ai/invite/grants", json={"notes": "demo grant"})

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["response_state"] == "disabled"
    assert "disabled" in data["detail"]["message"].lower()
    _assert_safe(response.text)


def test_create_redeem_and_use_invite_session_token_allows_importer_workflow(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    create_response = client.post(
        "/ai/invite/grants",
        json={
            "allowed_workflows": ["importer"],
            "max_sessions": 1,
            "max_provider_calls": 2,
            "max_estimated_cost_usd": "0.25",
            "notes": "Invite for local recipe demo.",
            "operator_label": "scott-local",
        },
    )
    assert create_response.status_code == 200
    create_data = create_response.json()
    assert create_data["invite_token"]
    assert create_data["grant"]["invite_token_fingerprint"]
    assert create_data["grant"]["status"] in {"active", "used"}
    _assert_safe(create_response.text)

    grant_id = create_data["grant"]["grant_id"]
    invite_token = create_data["invite_token"]
    grant_status = client.get(f"/ai/invite/grants/{grant_id}")
    assert grant_status.status_code == 200
    assert grant_status.json()["invite_token"] is None

    redeem_response = client.post("/ai/invite/redeem", json={"invite_token": invite_token})
    assert redeem_response.status_code == 200
    redeem_data = redeem_response.json()
    session_id = redeem_data["session"]["session_id"]
    session_token = redeem_data["session_token"]
    assert session_token
    assert redeem_data["session"]["session_token_fingerprint"]
    assert redeem_data["session"]["access_grant_id"] == grant_id
    assert redeem_data["budget_snapshot"]["session_id"] == session_id
    _assert_safe(redeem_response.text)

    session_status = client.get(f"/ai/invite/sessions/{session_id}")
    assert session_status.status_code == 200
    session_status_data = session_status.json()
    assert session_status_data["session_token"] is None
    assert session_status_data["session"]["session_token_fingerprint"]
    _assert_safe(session_status.text)

    session_state = default_invite_session_store.get_session(session_id)
    assert session_state is not None
    budget_decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        session_state,
    )
    assert budget_decision.allowed is True
    assert budget_decision.budget_snapshot.session_id == session_id
    assert budget_decision.budget_snapshot.grant_id == grant_id
    assert budget_decision.status == AiProviderBudgetStatus.ALLOWED
    _assert_safe(budget_decision.safe_view())

    importer_response = client.post(
        "/ai/import-recipe",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "omelet with eggs cheddar onions butter folded in a skillet", "source": "invite-session"},
    )
    assert importer_response.status_code == 200
    importer_data = importer_response.json()
    assert importer_data["provider"] == "mock"
    assert importer_data["draft"] is not None
    assert importer_data["retrieval"]["retrieved_count"] >= 1
    _assert_safe(importer_response.text)


def test_redeem_wrong_token_blocks_safely(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    create_response = client.post("/ai/invite/grants", json={})
    invite_token = create_response.json()["invite_token"]

    response = client.post("/ai/invite/redeem", json={"invite_token": invite_token + "-wrong"})

    assert response.status_code == 404
    assert response.json()["detail"]["response_state"] == "not_found"
    _assert_safe(response.text)


def test_expired_grant_and_session_block_safely(tmp_path, monkeypatch):
    _client(tmp_path, monkeypatch)
    fixed_now = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)
    local_store = AiInviteSessionStore(max_grants=4, max_sessions=4)
    result = local_store.create_grant(
        AiInviteGrantCreateRequest(
            allowed_workflows=["importer"],
            ttl_seconds=1,
            max_sessions=1,
        ),
        now=fixed_now,
        actor_label="scott-local",
    )

    with pytest.raises(InviteSessionError) as exc_info:
        local_store.redeem_invite_token(result.invite_token, now=fixed_now + timedelta(hours=2))
    assert exc_info.value.response_state in {"expired", "not_found"}

    session_store = AiInviteSessionStore(max_grants=4, max_sessions=4)
    session_result = session_store.create_grant(
        AiInviteGrantCreateRequest(
            allowed_workflows=["importer"],
            ttl_seconds=3600,
            max_sessions=1,
        ),
        now=fixed_now,
        actor_label="scott-local",
    )
    session_result = session_store.redeem_invite_token(session_result.invite_token, now=fixed_now)
    session_result.session.expires_at = fixed_now - timedelta(seconds=1)
    session = session_store.resolve_session_from_token(session_result.session_token, now=fixed_now)
    assert session is None


def test_revoked_session_blocks_protected_workflow(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    create_response = client.post("/ai/invite/grants", json={"allowed_workflows": ["importer"]})
    invite_token = create_response.json()["invite_token"]
    redeem_response = client.post("/ai/invite/redeem", json={"invite_token": invite_token})
    session_token = redeem_response.json()["session_token"]
    session_id = redeem_response.json()["session"]["session_id"]

    revoke_response = client.post(f"/ai/invite/sessions/{session_id}/revoke")
    assert revoke_response.status_code == 200
    assert revoke_response.json()["session"]["status"] == "revoked"

    blocked = client.post(
        "/ai/import-recipe",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
    )
    assert blocked.status_code == 403
    _assert_safe(blocked.text)


def test_disallowed_workflow_blocks_protected_workflow(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    create_response = client.post("/ai/invite/grants", json={"allowed_workflows": ["dataset_ask"]})
    invite_token = create_response.json()["invite_token"]
    redeem_response = client.post("/ai/invite/redeem", json={"invite_token": invite_token})
    session_token = redeem_response.json()["session_token"]

    blocked = client.post(
        "/ai/import-recipe",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
    )
    assert blocked.status_code == 403
    assert "not allowed" in blocked.text.lower() or "workflow" in blocked.text.lower()
    _assert_safe(blocked.text)


def test_invite_status_endpoint_is_safe(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.get("/ai/invite/status")

    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "allowed_workflows" in data
    _assert_safe(response.text)


def test_safe_serialization_excludes_forbidden_strings(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    create_response = client.post("/ai/invite/grants", json={"allowed_workflows": ["importer"]})
    data = create_response.json()
    serialized = json.dumps(data, sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in serialized
