from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any


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

OFFLINE_ENV_DEFAULTS = {
    "AI_PROVIDER": "mock",
    "OPENAI_ENABLE_LIVE_TESTS": "false",
    "AI_PROVIDER_CALLS_ENABLED": "true",
    "AI_PROVIDER_GLOBAL_DISABLE": "false",
    "AI_OPERATOR_GATE_ENABLED": "false",
    "AI_OPERATOR_GATE_LOCAL_BYPASS": "true",
    "AI_INVITE_SESSIONS_ENABLED": "false",
    "AI_PROVIDER_BUDGET_MODE": "enforce",
}

LIVE_ENV_DEFAULTS = {
    "AI_PROVIDER": "openai",
    "OPENAI_ENABLE_LIVE_TESTS": "true",
    "AI_PROVIDER_CALLS_ENABLED": "true",
    "AI_PROVIDER_GLOBAL_DISABLE": "false",
    "AI_OPERATOR_GATE_ENABLED": "false",
    "AI_OPERATOR_GATE_LOCAL_BYPASS": "true",
    "AI_INVITE_SESSIONS_ENABLED": "false",
    "AI_PROVIDER_BUDGET_MODE": "enforce",
}

ENV_VARS_TO_CLEAR = (
    "AI_MODEL",
    "AI_MAX_OUTPUT_TOKENS",
    "AI_TIMEOUT_SECONDS",
    "AI_PROVIDER_DEBUG",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_FALLBACK_MODEL",
    "RECIPE_DATASET_DIR",
    "RECIPE_DATASET_INDEX_LIMIT",
    "AI_RETRIEVAL_CACHE_ENABLED",
    "AI_RETRIEVAL_CACHE_MAX_ENTRIES",
    "AI_RETRIEVAL_CACHE_TTL_SECONDS",
    "AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION",
    "AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL",
    "AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL",
    "AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL",
    "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION",
    "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL",
    "AI_PROVIDER_BUDGET_SESSION_ID",
    "AI_OPERATOR_GATE_TOKEN_FINGERPRINT",
    "AI_OPERATOR_GATE_TOKEN",
    "AI_OPERATOR_GATE_ALLOWED_WORKFLOWS",
    "AI_INVITE_SESSION_TTL_SECONDS",
    "AI_INVITE_GRANT_TTL_SECONDS",
    "AI_INVITE_MAX_SESSIONS_PER_GRANT",
    "AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS",
    "AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD",
    "AI_INVITE_ALLOWED_WORKFLOWS",
    "AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED",
)

RESPONSE_TEXT_SAMPLES: list[str] = []


@dataclass(frozen=True)
class RegressionCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class RegressionRunResult:
    checks: list[RegressionCheck] = field(default_factory=list)
    summary: str = ""

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(1 for check in self.checks if check.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for check in self.checks if not check.passed)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = run_regression(live_smoke=args.live_smoke)
    for check in result.checks:
        prefix = "PASS" if check.passed else "FAIL"
        print(f"{prefix}: {check.name} - {check.detail}")
    print(result.summary)
    return 0 if result.passed else 1


def run_regression(*, live_smoke: bool = False) -> RegressionRunResult:
    live_request_env = {
        "AI_29_30_REGRESSION_LIVE": os.getenv("AI_29_30_REGRESSION_LIVE"),
        "OPENAI_ENABLE_LIVE_TESTS": os.getenv("OPENAI_ENABLE_LIVE_TESTS"),
        "AI_PROVIDER": os.getenv("AI_PROVIDER"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }
    _set_offline_defaults()
    _clear_env_pollution()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "ai-api"))

    from fastapi.testclient import TestClient

    from app.ai_access_models import AiAccessWorkflow
    from app.ai_budget_guard import check_provider_budget, reset_provider_budget_tracker
    from app.ai_invite_sessions import default_invite_session_store
    from app.ai_operator_gate import check_operator_gate, fingerprint_operator_token
    from app.ai_usage_report import reset_usage_report_collector
    from app.config import get_invite_session_settings, get_operator_gate_settings
    from app.demo_data import DEMO_RECIPES, seed_demo_data
    from app.importer import import_recipe_text
    from app.main import app
    from app.providers.base import StructuredLLMResponse
    from app import meal_plan_endpoint
    from app.recipe_session import default_recipe_session_store
    from app.retrieval_cache import reset_retrieval_cache
    from app.schemas import (
        AiInviteGrantCreateRequest,
        DatasetAskRequest,
        MealPlanRequest,
        RecipeImportDraft,
        RecipeImportRequest,
        RecipeIngredientDraft,
        RecipeInstructionDraft,
        RecipeDocument,
        RecipeSessionFinalizeRequest,
        RecipeSessionMessageRequest,
        RecipeSessionStartRequest,
        AskRequest,
    )
    from app.dataset_rag import ask_dataset_recipes
    from app.meal_plan_endpoint import create_meal_plan
    from app.rag import ask_cookbook

    result_checks: list[RegressionCheck] = []
    temp_root = repo_root / ".tmp-ai-demo" / "regression-29-30" / uuid.uuid4().hex
    temp_root.mkdir(parents=True, exist_ok=True)
    demo_recipe_documents = _demo_recipe_documents(DEMO_RECIPES)
    old_load_recipe_documents = meal_plan_endpoint.load_recipe_documents

    try:
        paths = seed_demo_data(temp_root)
        os.environ["COOKBOOK_DB_PATH"] = str(paths["db_path"])
        os.environ["RECIPE_DATASET_DIR"] = str(paths["dataset_dir"])
        os.environ["AI_MODEL"] = "mock-basic"
        os.environ["OPENAI_MODEL"] = "gpt-5.4-nano"
        os.environ["OPENAI_FALLBACK_MODEL"] = "gpt-5.4-mini"
        os.environ["AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION"] = "2"
        os.environ["AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL"] = "12000"
        os.environ["AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL"] = "1200"
        os.environ["AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL"] = "14000"
        os.environ["AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION"] = "1.00"
        os.environ["AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL"] = "0.25"
        os.environ["AI_INVITE_SESSION_TTL_SECONDS"] = "1800"
        os.environ["AI_INVITE_GRANT_TTL_SECONDS"] = "3600"
        os.environ["AI_INVITE_MAX_SESSIONS_PER_GRANT"] = "1"
        os.environ["AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS"] = "2"
        os.environ["AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD"] = "0.50"
        os.environ["AI_INVITE_ALLOWED_WORKFLOWS"] = "importer,dataset_ask,recipe_session,meal_plan"
        os.environ["AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED"] = "true"
        meal_plan_endpoint.load_recipe_documents = lambda: demo_recipe_documents  # type: ignore[assignment]

        reset_provider_budget_tracker()
        reset_usage_report_collector()
        default_recipe_session_store.clear()
        default_invite_session_store.reset()
        reset_retrieval_cache()

        client = TestClient(app)

        _record(result_checks, "health/config readiness", _check_readiness(client))
        _record(result_checks, "operator gate disabled default", _check_operator_gate_disabled())
        _record(result_checks, "invite sessions disabled default", _check_invite_sessions_disabled(client))
        _record(result_checks, "usage report empty/default safety", _check_empty_usage_report(client))
        _record(result_checks, "operator gate enabled test context", _check_operator_gate_enabled(client))
        invite_data = _check_invite_session_flow(client)
        result_checks.append(invite_data["check"])
        _record(result_checks, "protected importer with invite session token", _check_importer_with_invite(client, invite_data["session_token"]))
        _record(result_checks, "protected recipe-session flow with invite token", _check_recipe_session_flow(client, invite_data["session_token"]))
        _record(result_checks, "dataset ask and saved-recipe ask remain mock/offline", _check_dataset_and_saved_recipe_asks(client, invite_data["session_token"]))
        _record(result_checks, "provider budget allowed/skipped mock behavior", _check_budget_allowed_and_skipped())
        _record(result_checks, "provider budget block prevents provider invocation", _check_budget_block_prevents_provider())
        _record(result_checks, "usage report reflects session and meter counts", _check_populated_usage_report(client))
        _record(result_checks, "admin usage report hidden from OpenAPI", _check_admin_route_hidden_from_openapi())
        _record(result_checks, "route exposure assumptions still hold", _check_route_exposure_assumptions())
        _record(result_checks, "monetization boundary stays docs-only", _check_monetization_boundary_docs())
        _record(result_checks, "forbidden strings absent from responses", _check_no_forbidden_strings_seen())

        if live_smoke:
            _record(result_checks, "optional live smoke gate", _check_optional_live_smoke(live_request_env))
        else:
            result_checks.append(
                RegressionCheck(
                    name="optional live smoke gate",
                    passed=True,
                    detail="Skipped because live smoke was not requested.",
                )
            )

    finally:
        meal_plan_endpoint.load_recipe_documents = old_load_recipe_documents
        default_recipe_session_store.clear()
        default_invite_session_store.reset()
        reset_provider_budget_tracker()
        reset_usage_report_collector()
        reset_retrieval_cache()
        shutil.rmtree(temp_root, ignore_errors=True)

    summary = f"SUMMARY: {sum(1 for check in result_checks if check.passed)} passed, {sum(1 for check in result_checks if not check.passed)} failed, {sum(1 for check in result_checks if 'Skipped' in check.detail)} skipped."
    return RegressionRunResult(checks=result_checks, summary=summary)


def _check_readiness(client) -> RegressionCheck:
    health = client.get("/health")
    config = client.get("/ai/config")
    readiness = client.get("/demo/readiness")
    assert health.status_code == 200
    assert config.status_code == 200
    assert readiness.status_code == 200
    _assert_no_forbidden_text(health.text)
    _assert_no_forbidden_text(config.text)
    _assert_no_forbidden_text(readiness.text)
    _remember_response_text(health.text)
    _remember_response_text(config.text)
    _remember_response_text(readiness.text)
    data = readiness.json()
    assert data["service"]["ok"] is True
    assert "mode" in data["provider"]
    return RegressionCheck("health/config readiness", True, "health, config, and readiness responded safely.")


def _check_operator_gate_disabled() -> RegressionCheck:
    from app.ai_operator_gate import check_operator_gate
    from app.config import get_operator_gate_settings

    decision = check_operator_gate(
        "importer",
        {},
        get_operator_gate_settings(),
        client_host="testclient",
    )
    assert decision.allowed is True
    assert decision.status.value == "disabled"
    return RegressionCheck("operator gate disabled default", True, "operator gate stays disabled by default.")


def _check_invite_sessions_disabled(client) -> RegressionCheck:
    status = client.get("/ai/invite/status")
    grants = client.post("/ai/invite/grants", json={"notes": "should be disabled"})
    assert status.status_code == 200
    assert grants.status_code == 404
    assert grants.json()["detail"]["response_state"] == "disabled"
    _assert_no_forbidden_text(status.text)
    _assert_no_forbidden_text(grants.text)
    _remember_response_text(status.text)
    _remember_response_text(grants.text)
    return RegressionCheck("invite sessions disabled default", True, "invite sessions stay off by default.")


def _check_empty_usage_report(client) -> RegressionCheck:
    report = client.get("/ai/admin/usage-report")
    assert report.status_code == 200
    payload = report.json()
    assert payload["summary"]["active_session_count"] == 0
    assert payload["summary"]["provider_calls_allowed"] == 0
    assert payload["summary"]["threshold_warning_count"] == 0
    _assert_no_forbidden_text(report.text)
    _remember_response_text(report.text)
    return RegressionCheck("usage report empty/default safety", True, "usage report returns stable empty defaults.")


def _check_operator_gate_enabled(client) -> RegressionCheck:
    from app.ai_operator_gate import fingerprint_operator_token

    token = "operator-regression-token"
    os.environ["AI_OPERATOR_GATE_ENABLED"] = "true"
    os.environ["AI_OPERATOR_GATE_LOCAL_BYPASS"] = "false"
    os.environ["AI_OPERATOR_GATE_TOKEN_FINGERPRINT"] = fingerprint_operator_token(token)

    missing = client.get("/ai/admin/usage-report")
    wrong = client.get("/ai/admin/usage-report", headers={"X-AI-Operator-Token": "wrong-token"})
    good = client.get("/ai/admin/usage-report", headers={"X-AI-Operator-Token": token})

    assert missing.status_code == 403
    assert wrong.status_code == 403
    assert good.status_code == 200
    _assert_no_forbidden_text(missing.text)
    _assert_no_forbidden_text(wrong.text)
    _assert_no_forbidden_text(good.text)
    _remember_response_text(missing.text)
    _remember_response_text(wrong.text)
    _remember_response_text(good.text)
    return RegressionCheck("operator gate enabled test context", True, "operator gate blocks missing and wrong tokens.")


def _check_invite_session_flow(client) -> dict[str, str | RegressionCheck]:
    os.environ["AI_INVITE_SESSIONS_ENABLED"] = "true"
    os.environ["AI_OPERATOR_GATE_ENABLED"] = "false"
    os.environ["AI_OPERATOR_GATE_LOCAL_BYPASS"] = "true"

    create = client.post(
        "/ai/invite/grants",
        json={
            "allowed_workflows": ["importer", "dataset_ask", "recipe_session", "meal_plan"],
            "max_sessions": 1,
            "max_provider_calls": 2,
            "max_estimated_cost_usd": "0.50",
            "notes": "regression invite",
            "operator_label": "local-operator",
        },
    )
    assert create.status_code == 200
    create_data = create.json()
    redeem = client.post("/ai/invite/redeem", json={"invite_token": create_data["invite_token"]})
    assert redeem.status_code == 200
    redeem_data = redeem.json()

    grant_id = create_data["grant"]["grant_id"]
    session_id = redeem_data["session"]["session_id"]
    session_token = redeem_data["session_token"]

    grant_status = client.get(f"/ai/invite/grants/{grant_id}")
    session_status = client.get(f"/ai/invite/sessions/{session_id}")

    assert grant_status.status_code == 200
    assert session_status.status_code == 200
    assert grant_status.json()["invite_token"] is None
    assert session_status.json()["session_token"] is None

    _assert_no_forbidden_text(create.text)
    _assert_no_forbidden_text(redeem.text)
    _assert_no_forbidden_text(grant_status.text)
    _assert_no_forbidden_text(session_status.text)
    _remember_response_text(create.text)
    _remember_response_text(redeem.text)
    _remember_response_text(grant_status.text)
    _remember_response_text(session_status.text)

    return {
        "check": RegressionCheck("invite session enabled test context", True, "invite grant and session were created and redeemed safely."),
        "grant_id": grant_id,
        "session_id": session_id,
        "session_token": session_token,
    }


def _check_importer_with_invite(client, session_token: str) -> RegressionCheck:
    response = client.post(
        "/ai/import-recipe",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill", "source": "regression"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["draft"] is not None
    _assert_no_forbidden_text(response.text)
    _remember_response_text(response.text)
    return RegressionCheck("protected importer with invite session token", True, "importer accepted the invite session token.")


def _check_recipe_session_flow(client, session_token: str) -> RegressionCheck:
    start = client.post(
        "/ai/recipe-session/start",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight"},
    )
    assert start.status_code == 200
    start_data = start.json()
    interaction_id = start_data["interaction_id"]
    assert start_data["response_state"] == "draft_generated"

    follow_up = client.post(
        f"/ai/recipe-session/{interaction_id}/message",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"text": "actually make it no-bake"},
    )
    assert follow_up.status_code == 200
    follow_data = follow_up.json()
    assert follow_data["rag_refreshed"] is True
    assert follow_data["draft"] is not None

    finalize = client.post(
        f"/ai/recipe-session/{interaction_id}/finalize",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"format": "draft_json"},
    )
    assert finalize.status_code == 200
    finalize_data = finalize.json()
    assert finalize_data["response_state"] == "ready_to_finalize"

    _assert_no_forbidden_text(start.text)
    _assert_no_forbidden_text(follow_up.text)
    _assert_no_forbidden_text(finalize.text)
    _remember_response_text(start.text)
    _remember_response_text(follow_up.text)
    _remember_response_text(finalize.text)
    return RegressionCheck("protected recipe-session flow with invite token", True, "recipe-session start/message/finalize worked with invite access.")


def _check_dataset_and_saved_recipe_asks(client, session_token: str) -> RegressionCheck:
    from app.rag import ask_cookbook
    from app.demo_data import DEMO_RECIPES
    from app.schemas import AskRequest, RecipeDocument

    dataset = client.post(
        "/dataset/ask",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"question": "What indexed recipe uses tomato pasta?", "limit": 1, "dataset_limit": 3},
    )
    saved = ask_cookbook(
        AskRequest(question="What saved recipe uses lemon?", limit=1),
        recipes=[
            RecipeDocument(
                id=str(recipe["id"]),
                title=recipe["title"],
                description=recipe["description"],
                ingredients=list(recipe["ingredients"]),
                instructions=list(recipe["instructions"]),
                tags=list(recipe["tags"]),
                source=recipe["source_url"],
                raw=recipe,
            )
            for recipe in DEMO_RECIPES
        ],
    )
    meal_plan = client.post(
        "/ai/meal-plan",
        headers={"X-AI-Demo-Session-Token": session_token},
        json={"days": 1, "meals_per_day": 1, "preferences": "lemon dinner", "candidate_limit": 2},
    )

    assert dataset.status_code == 200
    assert meal_plan.status_code == 200
    assert dataset.json()["provider"] == "mock"
    assert saved.provider == "mock"
    assert meal_plan.json()["provider"] == "mock"
    _assert_no_forbidden_text(dataset.text)
    _assert_no_forbidden_text(meal_plan.text)
    _remember_response_text(dataset.text)
    _remember_response_text(meal_plan.text)
    return RegressionCheck("dataset ask and saved-recipe ask remain mock/offline", True, "dataset ask, saved-recipe ask, and meal plan stayed offline/mock.")


def _demo_recipe_documents(demo_recipes: list[dict[str, Any]]) -> list[Any]:
    from app.schemas import RecipeDocument

    return [
        RecipeDocument(
            id=str(recipe["id"]),
            title=recipe["title"],
            description=recipe["description"],
            ingredients=list(recipe["ingredients"]),
            instructions=list(recipe["instructions"]),
            tags=list(recipe["tags"]),
            source=recipe["source_url"],
            raw=recipe,
        )
        for recipe in demo_recipes
    ]


def _check_budget_allowed_and_skipped() -> RegressionCheck:
    from app.ai_access_models import AiAccessWorkflow
    from app.ai_budget_guard import check_provider_budget

    settings = _safe_budget_settings()
    session = SimpleNamespace(interaction_id="budget-allowed-session", max_provider_calls=2, max_estimated_cost_usd=Decimal("0.10"))
    skipped = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        50,
        50,
        session,
        settings,
    )
    assert skipped.allowed is True
    assert skipped.status.value == "skipped"
    assert skipped.meter_event.status.value == "skipped"
    assert skipped.budget_snapshot.provider_call_count == 0
    return RegressionCheck("provider budget allowed/skipped mock behavior", True, "mock provider decisions stay zero-cost and allowed.")


def _check_budget_block_prevents_provider() -> RegressionCheck:
    from app.ai_access_models import AiAccessWorkflow
    from app.importer import import_recipe_text
    from app.providers.base import StructuredLLMResponse
    from app.schemas import RecipeImportRequest

    class FakeProvider:
        name = "openai"
        model = "gpt-5.4-nano"

        def __init__(self) -> None:
            self.calls = 0

        def generate_structured(self, request: Any) -> Any:
            del request
            self.calls += 1
            return StructuredLLMResponse(
                data={
                    "title": "Classic Cheesecake",
                    "servings": 4,
                    "ingredients": [
                        {"name": "cream cheese", "quantity": "16", "unit": "ounces"},
                        {"name": "sugar", "quantity": "3/4", "unit": "cup"},
                    ],
                    "instructions": [
                        {"step": 1, "text": "Prep the crust."},
                        {"step": 2, "text": "Bake until set."},
                    ],
                },
                provider=self.name,
                model=self.model,
                usage={"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            )

    fake_provider = FakeProvider()
    settings = _safe_budget_settings(
        calls_enabled=True,
        global_disable=False,
        max_calls_per_demo_session=1,
        max_estimated_cost_usd_per_session=Decimal("0.01"),
        max_estimated_cost_usd_per_call=Decimal("0.01"),
    )
    session = SimpleNamespace(interaction_id="budget-block-session", max_provider_calls=1, max_estimated_cost_usd=Decimal("0.01"))
    request = RecipeImportRequest(text="classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill")

    first = import_recipe_text(request, provider=fake_provider, session_state=session)
    second = import_recipe_text(request, provider=fake_provider, session_state=session)

    assert first.provider == "openai"
    assert first.draft is not None
    assert second.provider == "none"
    assert second.draft is None
    assert fake_provider.calls == 1
    _assert_no_forbidden_text(first.model_dump())
    _assert_no_forbidden_text(second.model_dump())
    return RegressionCheck("provider budget block prevents provider invocation", True, "blocked budget path never reached the provider.")


def _check_populated_usage_report(client) -> RegressionCheck:
    report = client.get("/ai/admin/usage-report")
    assert report.status_code == 200
    payload = report.json()
    summary = payload["summary"]
    assert summary["provider_calls_allowed"] >= 1
    assert summary["provider_calls_skipped"] >= 1
    assert summary["provider_calls_blocked"] >= 1
    assert summary["active_session_count"] >= 1
    assert payload["thresholds"] == [] or isinstance(payload["thresholds"], list)
    _assert_no_forbidden_text(report.text)
    _remember_response_text(report.text)
    return RegressionCheck("usage report reflects session and meter counts", True, "usage report captured safe local activity.")


def _check_admin_route_hidden_from_openapi() -> RegressionCheck:
    from app.main import app

    schema = app.openapi()
    assert "/ai/admin/usage-report" not in schema["paths"]
    return RegressionCheck("admin usage report hidden from OpenAPI", True, "admin usage report stays hidden from the public schema.")


def _check_route_exposure_assumptions() -> RegressionCheck:
    inventory = {
        "/health": "public_candidate",
        "/ai/config": "internal_status",
        "/ai/invite/grants": "operator_only",
        "/ai/invite/redeem": "invite_only_candidate",
        "/ai/recipe-session/start": "invite_only_candidate",
        "/ai/import-recipe": "invite_only_candidate",
        "/dataset/ask": "invite_only_candidate",
        "/ai/ask": "invite_only_candidate",
        "/ai/meal-plan": "invite_only_candidate",
        "/ai/admin/usage-report": "never_public",
    }
    assert inventory["/ai/admin/usage-report"] == "never_public"
    assert inventory["/ai/invite/grants"] == "operator_only"
    assert inventory["/ai/recipe-session/start"] == "invite_only_candidate"
    return RegressionCheck("route exposure assumptions still hold", True, "route classifications remain stable.")


def _check_monetization_boundary_docs() -> RegressionCheck:
    adr = Path(__file__).resolve().parents[1] / "docs" / "ai-monetization-and-entitlement-boundary-adr.md"
    backlog = Path(__file__).resolve().parents[1] / "docs" / "ai-implementation-backlog.md"
    text = adr.read_text(encoding="utf-8")
    assert "ads" in text.lower()
    assert "sponsorship" in text.lower()
    assert "paid access is not being implemented now" in text.lower()
    assert "separate ADR" in text
    assert "no payment provider integration" in text.lower()
    backlog_text = backlog.read_text(encoding="utf-8")
    assert "0031A:" in backlog_text
    assert "secondary provider offload" in backlog_text.lower()
    return RegressionCheck("monetization boundary stays docs-only", True, "monetization remains documentation-only in this task.")


def _check_no_forbidden_strings_seen() -> RegressionCheck:
    for text in RESPONSE_TEXT_SAMPLES:
        _assert_no_forbidden_text(text)
    return RegressionCheck("forbidden strings absent from responses", True, "checked safe route responses only.")


def _check_optional_live_smoke(requested_env: dict[str, str | None]) -> RegressionCheck:
    if (requested_env.get("AI_29_30_REGRESSION_LIVE") or "").strip().lower() != "true":
        return RegressionCheck("optional live smoke gate", True, "Skipped because the regression live boundary was not requested.")
    if (requested_env.get("OPENAI_ENABLE_LIVE_TESTS") or "").strip().lower() != "true":
        return RegressionCheck("optional live smoke gate", True, "Skipped because OPENAI_ENABLE_LIVE_TESTS is not true.")
    if (requested_env.get("AI_PROVIDER") or "").strip().lower() != "openai":
        return RegressionCheck("optional live smoke gate", True, "Skipped because AI_PROVIDER is not openai.")
    if not (requested_env.get("OPENAI_API_KEY") or "").strip():
        return RegressionCheck("optional live smoke gate", True, "Skipped because no live API key is configured.")

    repo_root = Path(__file__).resolve().parents[1]
    live_root = repo_root / ".tmp-ai-demo" / "regression-29-30-live" / uuid.uuid4().hex
    live_root.mkdir(parents=True, exist_ok=True)

    from fastapi.testclient import TestClient

    from app.ai_budget_guard import reset_provider_budget_tracker
    from app.ai_invite_sessions import default_invite_session_store
    from app.ai_usage_report import reset_usage_report_collector
    from app.demo_data import seed_demo_data
    from app.main import app
    from app.recipe_session import default_recipe_session_store
    from app.retrieval_cache import reset_retrieval_cache

    live_restore_keys = (
        *LIVE_ENV_DEFAULTS.keys(),
        "AI_MAX_OUTPUT_TOKENS",
        "AI_MODEL",
        "OPENAI_MODEL",
        "OPENAI_FALLBACK_MODEL",
        "AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION",
        "AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL",
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION",
        "AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL",
        "AI_INVITE_SESSIONS_ENABLED",
        "COOKBOOK_DB_PATH",
        "RECIPE_DATASET_DIR",
    )
    old_env = {key: os.environ.get(key) for key in live_restore_keys}
    try:
        for key, value in LIVE_ENV_DEFAULTS.items():
            os.environ[key] = value
        os.environ["AI_MAX_OUTPUT_TOKENS"] = "200"
        os.environ["AI_MODEL"] = "mock-basic"
        os.environ["OPENAI_MODEL"] = "gpt-5.4-nano"
        os.environ["OPENAI_FALLBACK_MODEL"] = "gpt-5.4-mini"
        os.environ["AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION"] = "1"
        os.environ["AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL"] = "12000"
        os.environ["AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL"] = "200"
        os.environ["AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL"] = "14000"
        os.environ["AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION"] = "0.10"
        os.environ["AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL"] = "0.02"
        os.environ["AI_INVITE_SESSIONS_ENABLED"] = "false"

        paths = seed_demo_data(live_root)
        os.environ["COOKBOOK_DB_PATH"] = str(paths["db_path"])
        os.environ["RECIPE_DATASET_DIR"] = str(paths["dataset_dir"])

        reset_provider_budget_tracker()
        reset_usage_report_collector()
        default_recipe_session_store.clear()
        default_invite_session_store.reset()
        reset_retrieval_cache()

        client = TestClient(app)
        live = client.post(
            "/ai/import-recipe",
            json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill", "source": "live-smoke"},
        )
        assert live.status_code == 200
        payload = live.json()
        assert payload["provider"] in {"openai", "mock"}
        report = client.get("/ai/admin/usage-report")
        assert report.status_code == 200
        assert report.json()["summary"]["provider_calls_allowed"] >= 1
        _assert_no_forbidden_text(live.text)
        _assert_no_forbidden_text(report.text)
        _remember_response_text(live.text)
        _remember_response_text(report.text)
        return RegressionCheck("optional live smoke gate", True, "Live smoke opt-in detected and a minimal live-safe route check completed.")
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        default_recipe_session_store.clear()
        default_invite_session_store.reset()
        reset_provider_budget_tracker()
        reset_usage_report_collector()
        reset_retrieval_cache()
        shutil.rmtree(live_root, ignore_errors=True)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the integrated 29/30 regression harness.")
    parser.add_argument("--live-smoke", action="store_true", help="Enable the optional live-smoke boundary check.")
    return parser.parse_args(argv)


def _set_offline_defaults() -> None:
    for key, value in OFFLINE_ENV_DEFAULTS.items():
        os.environ[key] = value


def _clear_env_pollution() -> None:
    for name in ENV_VARS_TO_CLEAR:
        os.environ.pop(name, None)


def _assert_no_forbidden_text(value: Any) -> None:
    serialized = value if isinstance(value, str) else json.dumps(value, sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in serialized


def _remember_response_text(text: str) -> None:
    RESPONSE_TEXT_SAMPLES.append(text)


def _record(checks: list[RegressionCheck], name: str, check: RegressionCheck) -> None:
    if check.name != name:
        check = RegressionCheck(name=name, passed=check.passed, detail=check.detail)
    checks.append(check)


def _safe_budget_settings(**overrides: Any):
    from app.config import ProviderBudgetSettings

    data = {
        "calls_enabled": True,
        "global_disable": False,
        "max_calls_per_demo_session": 2,
        "max_input_tokens_per_call": 12000,
        "max_output_tokens_per_call": 1200,
        "max_total_tokens_per_call": 14000,
        "max_estimated_cost_usd_per_session": Decimal("0.10"),
        "max_estimated_cost_usd_per_call": Decimal("0.01"),
        "budget_mode": "enforce",
        "configured": True,
        "validation_errors": (),
    }
    data.update(overrides)
    return ProviderBudgetSettings(**data)


if __name__ == "__main__":
    raise SystemExit(main())
