from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai_access_models import AiAccessWorkflow, AiProviderBudgetStatus
from app.ai_budget_guard import (
    AiProviderBudgetTracker,
    check_provider_budget,
    reset_provider_budget_tracker,
)
from app.config import ProviderBudgetSettings, get_provider_budget_settings
from app.importer import import_recipe_text
from app.main import app
from app.recipe_session import default_recipe_session_store
from app.providers.base import StructuredLLMResponse
from app.schemas import RecipeImportDraft, RecipeImportRequest, RecipeIngredientDraft, RecipeInstructionDraft


FORBIDDEN_STRINGS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    "X-AI-Operator-Token",
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


def _safe_budget_settings(**overrides) -> ProviderBudgetSettings:
    data = {
        "calls_enabled": True,
        "global_disable": False,
        "max_calls_per_demo_session": 10,
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


class _FakeStructuredProvider:
    name = "openai"
    model = "gpt-5.4-nano"

    def __init__(self) -> None:
        self.calls = 0

    def generate_structured(self, request):
        del request
        self.calls += 1
        return StructuredLLMResponse(
            data=RecipeImportDraft(
                title="Classic Baked Cheesecake",
                servings=4,
                ingredients=[
                    RecipeIngredientDraft(name="cream cheese", quantity="16", unit="ounces"),
                    RecipeIngredientDraft(name="sugar", quantity="3/4", unit="cup"),
                    RecipeIngredientDraft(name="eggs", quantity="4", unit="large"),
                    RecipeIngredientDraft(name="vanilla", quantity="1", unit="teaspoon"),
                    RecipeIngredientDraft(name="graham cracker crust", quantity="1", unit="crust"),
                ],
                instructions=[
                    RecipeInstructionDraft(step=1, text="Preheat the oven and press the crust into the pan."),
                    RecipeInstructionDraft(step=2, text="Beat the filling until smooth."),
                    RecipeInstructionDraft(step=3, text="Bake until just set."),
                    RecipeInstructionDraft(step=4, text="Cool and chill before slicing."),
                ],
                notes="Mock live provider draft.",
            ).model_dump(),
            provider=self.name,
            model=self.model,
            usage={"input_tokens": 120, "output_tokens": 300, "total_tokens": 420},
        )


@pytest.fixture(autouse=True)
def _clear_tracker(monkeypatch):
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
    reset_provider_budget_tracker()
    default_recipe_session_store.clear()
    yield
    reset_provider_budget_tracker()
    default_recipe_session_store.clear()


def test_mock_provider_allowed_with_zero_cost():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        80,
        300,
        None,
        _safe_budget_settings(calls_enabled=False, global_disable=True, configured=False),
    )

    assert decision.allowed is True
    assert decision.status == AiProviderBudgetStatus.SKIPPED
    assert decision.meter_event.status.value == "skipped"
    assert decision.budget_snapshot.provider_call_count == 0
    assert decision.budget_snapshot.estimated_cost_usd == Decimal("0.00")
    _assert_safe(decision.safe_view())


def test_global_disable_blocks_live_provider_call():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        None,
        _safe_budget_settings(global_disable=True),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.DISABLED
    assert "disabled" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_provider_calls_disabled_setting_blocks_live_provider_call():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        None,
        _safe_budget_settings(calls_enabled=False),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.DISABLED
    _assert_safe(decision.safe_view())


def test_input_token_cap_blocks_safely():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        12001,
        300,
        None,
        _safe_budget_settings(),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.BLOCKED
    assert "input token" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_output_token_cap_blocks_safely():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        1201,
        None,
        _safe_budget_settings(),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.BLOCKED
    assert "output token" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_total_token_cap_blocks_safely():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        11000,
        1000,
        None,
        _safe_budget_settings(max_total_tokens_per_call=11000),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.BLOCKED
    assert "total token" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_per_call_cost_cap_blocks_safely():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        600,
        600,
        None,
        _safe_budget_settings(max_estimated_cost_usd_per_call=Decimal("0.01")),
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.BLOCKED
    assert "cost" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_per_session_call_count_cap_blocks_safely():
    settings = _safe_budget_settings(max_calls_per_demo_session=1)
    session_state = type("SessionState", (), {"interaction_id": "session-budget-001"})()

    first = check_provider_budget(
        AiAccessWorkflow.RECIPE_SESSION,
        "openai",
        "gpt-5.4-nano",
        80,
        300,
        session_state,
        settings,
    )
    second = check_provider_budget(
        AiAccessWorkflow.RECIPE_SESSION,
        "openai",
        "gpt-5.4-nano",
        80,
        300,
        session_state,
        settings,
    )

    assert first.allowed is True
    assert second.allowed is False
    assert second.status == AiProviderBudgetStatus.EXHAUSTED
    assert "budget" in second.safe_message.lower()
    _assert_safe(second.safe_view())


def test_per_session_estimated_cost_cap_blocks_safely():
    settings = _safe_budget_settings(max_estimated_cost_usd_per_session=Decimal("0.01"))
    session_state = type("SessionState", (), {"interaction_id": "session-budget-002"})()

    decision = check_provider_budget(
        AiAccessWorkflow.RECIPE_SESSION,
        "openai",
        "gpt-5.4-nano",
        600,
        600,
        session_state,
        settings,
    )

    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.EXHAUSTED
    assert "cost" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_invalid_budget_config_blocks_live_provider_calls_safely(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL", "not-an-int")
    settings = get_provider_budget_settings()
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        80,
        300,
        None,
        settings,
    )

    assert settings.configured is False
    assert decision.allowed is False
    assert decision.status == AiProviderBudgetStatus.MISCONFIGURED
    assert "invalid" in decision.safe_message.lower()
    _assert_safe(decision.safe_view())


def test_allowed_live_call_decision_creates_safe_meter_event_without_real_network_call():
    tracker = AiProviderBudgetTracker()
    session_state = type("SessionState", (), {"interaction_id": "session-budget-003"})()
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        session_state,
        _safe_budget_settings(),
        tracker=tracker,
    )

    assert decision.allowed is True
    assert decision.status == AiProviderBudgetStatus.ALLOWED
    assert decision.meter_event.status.value == "allowed"
    assert decision.budget_snapshot.provider_call_count == 1
    assert decision.budget_snapshot.estimated_cost_usd > Decimal("0.00")
    _assert_safe(decision.safe_view())


def test_blocked_decision_does_not_invoke_provider_when_testable(tmp_path, monkeypatch):
    _write_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_PROVIDER_GLOBAL_DISABLE", "true")
    monkeypatch.setenv("AI_PROVIDER_CALLS_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.setenv("AI_MODEL", "mock-basic")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def _fail_if_called(*args, **kwargs):  # pragma: no cover - defensive guard.
        raise AssertionError("provider should not be invoked when budget is disabled")

    monkeypatch.setattr("app.importer.get_provider", _fail_if_called)

    response = import_recipe_text(RecipeImportRequest(text="omelet with eggs cheese maybe onions cooked in butter fold it over"))
    assert response.provider == "none"
    assert response.draft is None
    assert any("disabled" in warning.lower() for warning in response.warnings)
    _assert_safe(response.model_dump())


def test_route_blocked_before_provider_when_live_selected_and_global_disable_is_true(tmp_path, monkeypatch):
    _write_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_PROVIDER_GLOBAL_DISABLE", "true")
    monkeypatch.setenv("AI_PROVIDER_CALLS_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def _fail_if_called(*args, **kwargs):  # pragma: no cover - defensive guard.
        raise AssertionError("provider should not be invoked when budget is disabled")

    monkeypatch.setattr("app.importer.get_provider", _fail_if_called)

    response = TestClient(app).post(
        "/ai/import-recipe",
        json={"text": "omelet with eggs cheddar onions butter folded in a skillet"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["draft"] is None
    assert any("disabled" in warning.lower() for warning in data["warnings"])
    _assert_safe(response.text)


def test_recipe_session_route_blocks_before_provider_when_budget_exhausted(tmp_path, monkeypatch):
    _write_dataset(tmp_path)
    monkeypatch.setenv("RECIPE_DATASET_DIR", str(tmp_path))
    monkeypatch.setenv("RECIPE_DATASET_INDEX_LIMIT", "5000")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_PROVIDER_CALLS_ENABLED", "true")
    monkeypatch.setenv("AI_PROVIDER_GLOBAL_DISABLE", "false")
    monkeypatch.setenv("AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION", "1")
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    fake_provider = _FakeStructuredProvider()
    monkeypatch.setattr("app.importer.get_provider", lambda: fake_provider)

    client = TestClient(app)
    start_response = client.post(
        "/ai/recipe-session/start",
        json={"text": "classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight"},
    )
    assert start_response.status_code == 200
    start_data = start_response.json()
    assert start_data["response_state"] == "draft_generated"
    assert start_data["draft"] is not None

    follow_up = client.post(
        f"/ai/recipe-session/{start_data['interaction_id']}/message",
        json={"text": "actually make it no-bake"},
    )
    assert follow_up.status_code == 200
    follow_up_data = follow_up.json()
    assert follow_up_data["response_state"] == "rejected"
    assert follow_up_data["draft"] is not None
    assert any("budget" in warning.lower() or "disabled" in warning.lower() for warning in follow_up_data["warnings"])
    assert fake_provider.calls == 1
    _assert_safe(follow_up.text)


def test_budget_tracker_reset_works():
    tracker = AiProviderBudgetTracker()
    session_state = type("SessionState", (), {"interaction_id": "session-budget-004"})()
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        session_state,
        _safe_budget_settings(),
        tracker=tracker,
    )
    assert decision.allowed is True
    tracker.reset()
    snapshot = tracker.snapshot("session-budget-004", max_provider_calls=10, max_estimated_cost_usd=Decimal("1.00"))
    assert snapshot.provider_call_count == 0
    assert snapshot.estimated_cost_usd == Decimal("0.00")


def test_safe_serialization_excludes_forbidden_strings():
    decision = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        120,
        300,
        None,
        _safe_budget_settings(),
    )

    view = decision.safe_view()
    serialized = json.dumps(view, sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in serialized
