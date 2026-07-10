from __future__ import annotations

import hashlib
import json

from fastapi.testclient import TestClient

from app.ai_access_models import AiAccessWorkflow, AiOperatorGateStatus
from app.ai_operator_gate import check_operator_gate, fingerprint_operator_token
from app.config import OperatorGateSettings
from app.main import app
from app.recipe_session import default_recipe_session_store
from app.retrieval_cache import reset_retrieval_cache


FORBIDDEN_STRINGS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    ".env",
    ".tmp-ai-demo",
    "raw_provider_prompt",
    "raw_provider_response",
    "C:\\Users\\",
    "/home/",
    "postgres://",
    "redis://",
)


def _operator_token(text: str) -> str:
    return text.strip()


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assert_safe(text: str) -> None:
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in text


def _settings(
    *,
    enabled: bool = True,
    token: str = "",
    allowed_workflows: tuple[str, ...] = ("importer", "dataset_ask", "recipe_session", "meal_plan"),
    local_bypass: bool = True,
) -> OperatorGateSettings:
    return OperatorGateSettings(
        enabled=enabled,
        token_fingerprint=_fingerprint(token) if token else "",
        allowed_workflows=allowed_workflows,
        local_bypass=local_bypass,
    )


def _write_demo_dataset(path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "13k-recipes.csv").write_text(
        "recipe_id,title,ingredients,instructions,tags\n"
        "cheesecake-1,Classic Baked Cheesecake,\"cream cheese; sugar; eggs; vanilla; graham cracker crust; melted butter\",\"Preheat oven; Press graham cracker crust; Beat cream cheese sugar vanilla and eggs; Bake until just set; Cool and chill\",dessert\n"
        "carbonara-1,Spaghetti Carbonara,\"spaghetti; eggs; parmesan; pancetta; black pepper; pasta water\",\"Boil spaghetti; Crisp pancetta; Toss off heat with eggs parmesan and pasta water\",dinner\n"
        "omelet-1,Cheese Omelet,\"eggs; cheddar cheese; onion; butter\",\"Beat eggs; Cook in skillet; Add cheese; Fold omelet\",breakfast\n"
        "casserole-1,Chicken and Rice Casserole,\"cooked chicken; rice; cream of chicken soup; cheddar cheese\",\"Preheat oven; Combine ingredients; Bake until hot and bubbly\",dinner\n"
        "crumb-1,Apple Crumble,\"apples; sugar; butter; cream; oats\",\"Slice apples; Mix topping; Bake\",dessert\n",
        encoding="utf-8",
    )


def test_gate_disabled_allows_requests_without_token():
    decision = check_operator_gate(
        AiAccessWorkflow.IMPORTER,
        request_headers={},
        settings=_settings(enabled=False),
        client_host="203.0.113.7",
    )

    assert decision.allowed is True
    assert decision.status == AiOperatorGateStatus.DISABLED
    _assert_safe(json.dumps(decision.safe_view(), sort_keys=True, default=str))


def test_gate_allows_local_bypass_for_local_requests():
    decision = check_operator_gate(
        AiAccessWorkflow.RECIPE_SESSION,
        request_headers={},
        settings=_settings(enabled=True, token="", local_bypass=True),
        client_host="testclient",
    )

    assert decision.allowed is True
    assert decision.status == AiOperatorGateStatus.ALLOWED
    assert decision.grant_type == "local_bypass"
    _assert_safe(json.dumps(decision.safe_view(), sort_keys=True, default=str))


def test_gate_blocks_missing_token_when_not_bypassed():
    decision = check_operator_gate(
        AiAccessWorkflow.DATASET_ASK,
        request_headers={},
        settings=_settings(enabled=True, token="operator-secret", local_bypass=False),
        client_host="203.0.113.7",
    )

    assert decision.allowed is False
    assert decision.status == AiOperatorGateStatus.BLOCKED
    assert "required" in decision.reason.lower()
    _assert_safe(json.dumps(decision.safe_view(), sort_keys=True, default=str))


def test_gate_accepts_header_and_bearer_tokens():
    token = _operator_token("operator-secret")
    settings = _settings(enabled=True, token=token, local_bypass=False)

    header_decision = check_operator_gate(
        AiAccessWorkflow.IMPORTER,
        request_headers={"X-AI-Operator-Token": token},
        settings=settings,
        client_host="203.0.113.7",
    )
    bearer_decision = check_operator_gate(
        AiAccessWorkflow.MEAL_PLAN,
        request_headers={"Authorization": f"Bearer {token}"},
        settings=settings,
        client_host="203.0.113.7",
    )

    assert header_decision.allowed is True
    assert header_decision.grant_type == "x-ai-operator-token"
    assert bearer_decision.allowed is True
    assert bearer_decision.grant_type == "authorization-bearer"
    _assert_safe(json.dumps(header_decision.safe_view(), sort_keys=True, default=str))
    _assert_safe(json.dumps(bearer_decision.safe_view(), sort_keys=True, default=str))


def test_gate_blocks_workflows_not_listed_in_configuration():
    token = _operator_token("operator-secret")
    decision = check_operator_gate(
        AiAccessWorkflow.RECIPE_SESSION,
        request_headers={"X-AI-Operator-Token": token},
        settings=_settings(enabled=True, token=token, allowed_workflows=("importer",), local_bypass=False),
        client_host="203.0.113.7",
    )

    assert decision.allowed is False
    assert decision.status == AiOperatorGateStatus.BLOCKED
    assert "not enabled" in decision.reason.lower()


def test_gate_reports_misconfigured_without_fingerprint():
    decision = check_operator_gate(
        AiAccessWorkflow.IMPORTER,
        request_headers={},
        settings=_settings(enabled=True, token="", local_bypass=False),
        client_host="203.0.113.7",
    )

    assert decision.allowed is False
    assert decision.status == AiOperatorGateStatus.MISCONFIGURED
    assert "configured" in decision.reason.lower()


def test_importer_and_session_routes_require_token_when_gate_enabled(tmp_path, monkeypatch):
    default_recipe_session_store.clear()
    reset_retrieval_cache()
    dataset_dir = tmp_path / "dataset"
    _write_demo_dataset(dataset_dir)

    token = "operator-secret"
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(dataset_dir))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.delenv("AI_PROVIDER_CALLS_ENABLED", raising=False)
    monkeypatch.delenv("AI_PROVIDER_GLOBAL_DISABLE", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION", raising=False)
    monkeypatch.delenv("AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL", raising=False)
    monkeypatch.delenv("AI_PROVIDER_BUDGET_MODE", raising=False)
    monkeypatch.delenv("AI_PROVIDER_BUDGET_SESSION_ID", raising=False)
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", fingerprint_operator_token(token))
    monkeypatch.setenv("AI_OPERATOR_GATE_ALLOWED_WORKFLOWS", "importer,dataset_ask,recipe_session,meal_plan")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")

    client = TestClient(app)

    blocked_importer = client.post("/ai/import-recipe", json={"text": "omelet with eggs and cheese"})
    assert blocked_importer.status_code == 403
    _assert_safe(blocked_importer.text)

    allowed_importer = client.post(
        "/ai/import-recipe",
        headers={"X-AI-Operator-Token": token},
        json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
    )
    assert allowed_importer.status_code == 200
    importer_data = allowed_importer.json()
    assert importer_data["draft"] is not None
    assert importer_data["retrieval"]["retrieved_count"] >= 1
    _assert_safe(allowed_importer.text)

    blocked_session = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    )
    assert blocked_session.status_code == 403
    _assert_safe(blocked_session.text)

    allowed_session = client.post(
        "/ai/recipe-session/start",
        headers={"X-AI-Operator-Token": token},
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill"},
    )
    assert allowed_session.status_code == 200
    session_data = allowed_session.json()
    assert session_data["response_state"] == "draft_generated"
    assert session_data["retrieval"]["retrieved_count"] >= 1
    _assert_safe(allowed_session.text)

    blocked_meal_plan = client.post(
        "/ai/meal-plan",
        json={"days": 1, "meals_per_day": 1, "preferences": "lemon dinner", "candidate_limit": 2},
    )
    assert blocked_meal_plan.status_code == 403
    _assert_safe(blocked_meal_plan.text)

    default_recipe_session_store.clear()
    reset_retrieval_cache()
