from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.ai_access_models import AiAccessWorkflow, AiDemoSession, AiDemoSessionStatus, AiDemoSessionType
from app.ai_budget_guard import check_provider_budget
from app.ai_operator_gate import fingerprint_operator_token
from app.config import ProviderBudgetSettings
from app.main import app


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


def _budget_settings(**overrides) -> ProviderBudgetSettings:
    data = {
        "calls_enabled": True,
        "global_disable": False,
        "max_calls_per_demo_session": 5,
        "max_input_tokens_per_call": 12000,
        "max_output_tokens_per_call": 1200,
        "max_total_tokens_per_call": 14000,
        "max_estimated_cost_usd_per_session": Decimal("1.00"),
        "max_estimated_cost_usd_per_call": Decimal("0.25"),
        "budget_mode": "enforce",
        "configured": True,
        "validation_errors": (),
    }
    data.update(overrides)
    return ProviderBudgetSettings(**data)


def _clear_state(monkeypatch) -> None:
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
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.setenv("AI_PROVIDER_CALLS_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER_GLOBAL_DISABLE", "false")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "true")
    monkeypatch.setenv("AI_INVITE_SESSIONS_ENABLED", "false")


def _route_inventory() -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    schema = app.openapi()
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            inventory.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "purpose": _route_purpose(path, method),
                    "openapi_visible": True,
                    "can_trigger_provider_calls": _can_trigger_provider_calls(path, method),
                    "uses_operator_gate": _uses_operator_gate(path, method),
                    "uses_invite_sessions": _uses_invite_sessions(path, method),
                    "uses_provider_budget_guard": _uses_provider_budget_guard(path, method),
                    "returns_admin_operator_data": _returns_admin_operator_data(path, method),
                    "recommended_exposure": _recommended_exposure(path, method),
                    "summary": operation.get("summary"),
                }
            )

    for method, path in (
        ("GET", "/demo"),
        ("GET", "/demo/ai"),
        ("GET", "/demo/readiness"),
        ("GET", "/ai/admin/usage-report"),
    ):
        inventory.append(
            {
                "method": method,
                "path": path,
                "purpose": _route_purpose(path, method),
                "openapi_visible": False,
                "can_trigger_provider_calls": _can_trigger_provider_calls(path, method),
                "uses_operator_gate": _uses_operator_gate(path, method),
                "uses_invite_sessions": _uses_invite_sessions(path, method),
                "uses_provider_budget_guard": _uses_provider_budget_guard(path, method),
                "returns_admin_operator_data": _returns_admin_operator_data(path, method),
                "recommended_exposure": _recommended_exposure(path, method),
                "summary": None,
            }
        )

    deduped: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in inventory:
        key = (str(row["method"]), str(row["path"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _route_purpose(path: str, method: str) -> str:
    if path in {"/demo", "/demo/ai"}:
        return "Static local demo UI"
    if path == "/demo/readiness":
        return "Local readiness/status summary"
    if path == "/health":
        return "Liveness check"
    if path == "/ai/config":
        return "Non-secret provider availability summary"
    if path in {"/recipes/search", "/dataset/search"}:
        return "Deterministic local search"
    if path == "/dataset/ask":
        return "Dataset question answering"
    if path == "/ai/import-recipe":
        return "Structured recipe import/create"
    if path == "/ai/ask":
        return "Saved-recipe question answering"
    if path == "/ai/meal-plan":
        return "Saved-recipe meal planning"
    if path == "/ai/invite/status":
        return "Invite session status summary"
    if path == "/ai/invite/redeem":
        return "Redeem invite token into a demo session"
    if path == "/ai/invite/grants":
        return "Create invite grants"
    if path == "/ai/invite/grants/{grant_id}":
        return "Inspect invite grant state"
    if path == "/ai/invite/sessions/{session_id}":
        return "Inspect invite session state"
    if path.endswith("/revoke") and "/ai/invite/" in path:
        return "Revoke invite grant or session"
    if path.startswith("/ai/recipe-session/"):
        return "Recipe Session Alpha workflow"
    if path == "/ai/admin/usage-report":
        return "Safe operator usage report"
    return method.upper()


def _recommended_exposure(path: str, method: str) -> str:
    if path == "/health":
        return "public_candidate"
    if path in {"/demo", "/demo/ai"}:
        return "public_candidate"
    if path in {"/ai/import-recipe", "/dataset/ask", "/ai/ask", "/ai/meal-plan"}:
        return "invite_only_candidate"
    if path == "/ai/invite/redeem":
        return "invite_only_candidate"
    if path.startswith("/ai/recipe-session/"):
        return "invite_only_candidate"
    if path in {"/ai/invite/grants", "/ai/invite/grants/{grant_id}/revoke", "/ai/invite/sessions/{session_id}/revoke"}:
        return "operator_only"
    if path in {"/ai/invite/status", "/ai/invite/grants/{grant_id}", "/ai/invite/sessions/{session_id}", "/demo/readiness", "/ai/config", "/recipes/search", "/dataset/search"}:
        return "internal_status"
    if path == "/ai/admin/usage-report":
        return "never_public"
    return "local_only"


def _can_trigger_provider_calls(path: str, method: str) -> bool:
    return path in {"/dataset/ask", "/ai/import-recipe", "/ai/ask", "/ai/meal-plan"} or path.startswith("/ai/recipe-session/")


def _uses_operator_gate(path: str, method: str) -> bool:
    return path in {"/ai/admin/usage-report", "/ai/import-recipe", "/dataset/ask", "/ai/ask", "/ai/meal-plan"} or path.startswith("/ai/recipe-session/")


def _uses_invite_sessions(path: str, method: str) -> bool:
    return path in {
        "/ai/invite/redeem",
        "/ai/invite/grants/{grant_id}",
        "/ai/invite/sessions/{session_id}",
        "/ai/invite/grants/{grant_id}/revoke",
        "/ai/invite/sessions/{session_id}/revoke",
    } or path.startswith("/ai/recipe-session/") or path in {"/ai/import-recipe", "/dataset/ask", "/ai/ask", "/ai/meal-plan"}


def _uses_provider_budget_guard(path: str, method: str) -> bool:
    return path in {
        "/ai/invite/redeem",
        "/ai/invite/grants/{grant_id}",
        "/ai/invite/sessions/{session_id}",
    } or path.startswith("/ai/recipe-session/") or path in {"/dataset/ask", "/ai/import-recipe", "/ai/ask", "/ai/meal-plan"}


def _returns_admin_operator_data(path: str, method: str) -> bool:
    return path in {
        "/ai/admin/usage-report",
        "/ai/invite/status",
        "/ai/invite/grants",
        "/ai/invite/grants/{grant_id}",
        "/ai/invite/sessions/{session_id}",
        "/ai/invite/grants/{grant_id}/revoke",
        "/ai/invite/sessions/{session_id}/revoke",
        "/ai/config",
        "/demo/readiness",
    }


def _route_row(inventory: list[dict[str, object]], path: str, method: str) -> dict[str, object]:
    for row in inventory:
        if row["path"] == path and row["method"] == method:
            return row
    raise AssertionError(f"Route not found: {method} {path}")


def test_openapi_hides_admin_usage_report_and_demo_routes():
    schema = app.openapi()
    assert "/ai/admin/usage-report" not in schema["paths"]
    assert "/demo" not in schema["paths"]
    assert "/demo/ai" not in schema["paths"]
    assert "/demo/readiness" not in schema["paths"]


def test_route_inventory_classifies_admin_operator_and_session_routes():
    inventory = _route_inventory()
    assert _route_row(inventory, "/ai/admin/usage-report", "GET")["recommended_exposure"] == "never_public"
    assert _route_row(inventory, "/ai/invite/grants", "POST")["recommended_exposure"] == "operator_only"
    assert _route_row(inventory, "/ai/invite/redeem", "POST")["recommended_exposure"] == "invite_only_candidate"
    assert _route_row(inventory, "/ai/recipe-session/start", "POST")["recommended_exposure"] == "invite_only_candidate"
    assert _route_row(inventory, "/health", "GET")["recommended_exposure"] == "public_candidate"
    assert _route_row(inventory, "/ai/config", "GET")["recommended_exposure"] == "internal_status"


def test_usage_report_endpoint_is_protected_and_safe_when_operator_gate_is_enabled(monkeypatch):
    _clear_state(monkeypatch)
    token = "operator-secret"
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", fingerprint_operator_token(token))
    monkeypatch.setenv("AI_OPERATOR_GATE_ALLOWED_WORKFLOWS", "importer,dataset_ask,recipe_session,meal_plan")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")

    client = TestClient(app)

    blocked = client.get("/ai/admin/usage-report")
    assert blocked.status_code == 403
    _assert_safe(blocked.text)

    allowed = client.get("/ai/admin/usage-report", headers={"X-AI-Operator-Token": token})
    assert allowed.status_code == 200
    payload = allowed.json()
    assert "summary" in payload
    assert "warnings" in payload
    _assert_safe(allowed.text)


def test_invite_only_workflows_stay_disabled_by_default(monkeypatch):
    _clear_state(monkeypatch)
    client = TestClient(app)

    status_response = client.get("/ai/invite/status")
    assert status_response.status_code == 200
    assert status_response.json()["enabled"] is False

    blocked = client.post("/ai/invite/grants", json={"notes": "demo"})
    assert blocked.status_code == 404
    assert blocked.json()["detail"]["response_state"] == "disabled"
    _assert_safe(blocked.text)


def test_live_provider_calls_remain_opt_in_and_budget_gated():
    session = AiDemoSession(
        session_id="route-review-budget",
        session_type=AiDemoSessionType.LOCAL_OPERATOR,
        status=AiDemoSessionStatus.ACTIVE,
        created_at=datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        expires_at=datetime(2026, 7, 10, 14, 0, tzinfo=UTC),
        max_provider_calls=5,
        max_estimated_cost_usd=Decimal("1.00"),
    )
    live_blocked = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        240,
        session,
        _budget_settings(global_disable=True),
    )
    assert live_blocked.allowed is False

    skipped = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        120,
        240,
        session,
        _budget_settings(calls_enabled=False, global_disable=True, configured=False),
    )
    assert skipped.allowed is True
    _assert_safe(skipped.safe_view())


def test_openapi_schema_remains_secret_free():
    schema_text = json.dumps(app.openapi(), sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in schema_text


def test_route_inventory_entries_are_secret_free():
    inventory = _route_inventory()
    _assert_safe(inventory)
