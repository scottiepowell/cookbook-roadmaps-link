from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.ai_access_models import (
    AiAccessGrant,
    AiAccessGrantStatus,
    AiAccessGrantType,
    AiAccessWorkflow,
    AiDemoSession,
    AiDemoSessionStatus,
    AiDemoSessionType,
    AiQualityEvent,
    AiQualityStatus,
)
from app.ai_budget_guard import check_provider_budget, reset_provider_budget_tracker
from app.ai_invite_sessions import default_invite_session_store
from app.ai_operator_gate import fingerprint_operator_token
from app.ai_usage_report import (
    build_ai_usage_report,
    default_usage_report_collector,
    reset_usage_report_collector,
)
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


def _now() -> datetime:
    # Keep seeded active grants ahead of the current clock used by endpoint tests.
    return datetime(2030, 7, 10, 12, 0, tzinfo=UTC)


def _session(
    session_id: str,
    *,
    grant_id: str | None,
    status: AiDemoSessionStatus,
    expires_at: datetime,
    provider_call_count: int = 0,
    estimated_cost_usd: Decimal = Decimal("0.00"),
    max_provider_calls: int | None = 5,
    max_estimated_cost_usd: Decimal | None = Decimal("1.00"),
) -> AiDemoSession:
    return AiDemoSession(
        session_id=session_id,
        session_type=AiDemoSessionType.INVITE if grant_id else AiDemoSessionType.LOCAL_OPERATOR,
        status=status,
        created_at=_now(),
        expires_at=expires_at,
        revoked_at=_now() if status in {AiDemoSessionStatus.REVOKED, AiDemoSessionStatus.COMPLETED} else None,
        revoked_reason=f"{status.value} for report test" if status in {AiDemoSessionStatus.REVOKED, AiDemoSessionStatus.COMPLETED} else None,
        operator_label="local-operator",
        access_grant_id=grant_id,
        session_token_fingerprint=f"fp_{session_id}",
        allowed_workflows=[AiAccessWorkflow.IMPORTER],
        max_provider_calls=max_provider_calls,
        max_estimated_cost_usd=max_estimated_cost_usd,
        request_count=provider_call_count,
        provider_call_count=provider_call_count,
        estimated_cost_usd=estimated_cost_usd,
        last_activity_at=_now(),
        metadata_fingerprint=f"fp_meta_{session_id}",
    )


def _grant(
    grant_id: str,
    *,
    status: AiAccessGrantStatus,
    expires_at: datetime | None,
    max_sessions: int,
    used_at: datetime | None = None,
    revoked_at: datetime | None = None,
    max_provider_calls: int | None = 5,
    max_estimated_cost_usd: Decimal | None = Decimal("1.00"),
) -> AiAccessGrant:
    return AiAccessGrant(
        grant_id=grant_id,
        grant_type=AiAccessGrantType.INVITE_CODE if status != AiAccessGrantStatus.ACTIVE else AiAccessGrantType.LOCAL_OPERATOR,
        status=status,
        created_at=_now(),
        expires_at=expires_at,
        used_at=used_at,
        revoked_at=revoked_at,
        revoked_reason=f"{status.value} for report test" if status in {AiAccessGrantStatus.REVOKED} else None,
        max_sessions=max_sessions,
        max_provider_calls=max_provider_calls,
        max_estimated_cost_usd=max_estimated_cost_usd,
        allowed_workflows=[AiAccessWorkflow.IMPORTER],
        notes=f"{status.value} grant for report test",
        metadata_fingerprint=f"fp_meta_{grant_id}",
        invite_token_fingerprint=f"fp_invite_{grant_id}",
    )


def _seed_report_state() -> dict[str, AiDemoSession | AiAccessGrant]:
    now = _now()
    default_invite_session_store.reset()

    active_grant = _grant(
        "grant_active_001",
        status=AiAccessGrantStatus.ACTIVE,
        expires_at=now + timedelta(hours=2),
        max_sessions=3,
    )
    used_grant = _grant(
        "grant_used_001",
        status=AiAccessGrantStatus.USED,
        expires_at=now + timedelta(days=2),
        max_sessions=1,
        used_at=now,
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )
    revoked_grant = _grant(
        "grant_revoked_001",
        status=AiAccessGrantStatus.REVOKED,
        expires_at=now + timedelta(days=2),
        max_sessions=1,
        revoked_at=now,
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )
    expired_grant = _grant(
        "grant_expired_001",
        status=AiAccessGrantStatus.EXPIRED,
        expires_at=now - timedelta(hours=1),
        max_sessions=1,
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )

    active_session = _session(
        "session_active_001",
        grant_id=active_grant.grant_id,
        status=AiDemoSessionStatus.ACTIVE,
        expires_at=now + timedelta(days=2),
        provider_call_count=4,
        estimated_cost_usd=Decimal("0.80"),
    )
    revoked_session = _session(
        "session_revoked_001",
        grant_id=active_grant.grant_id,
        status=AiDemoSessionStatus.REVOKED,
        expires_at=now + timedelta(days=2),
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )
    completed_session = _session(
        "session_completed_001",
        grant_id=revoked_grant.grant_id,
        status=AiDemoSessionStatus.COMPLETED,
        expires_at=now + timedelta(days=2),
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )
    expired_session = _session(
        "session_expired_001",
        grant_id=expired_grant.grant_id,
        status=AiDemoSessionStatus.EXPIRED,
        expires_at=now - timedelta(minutes=1),
        max_provider_calls=0,
        max_estimated_cost_usd=Decimal("0.00"),
    )

    default_invite_session_store._grants[active_grant.grant_id] = active_grant
    default_invite_session_store._grants[used_grant.grant_id] = used_grant
    default_invite_session_store._grants[revoked_grant.grant_id] = revoked_grant
    default_invite_session_store._grants[expired_grant.grant_id] = expired_grant
    default_invite_session_store._sessions[active_session.session_id] = active_session
    default_invite_session_store._sessions[revoked_session.session_id] = revoked_session
    default_invite_session_store._sessions[completed_session.session_id] = completed_session
    default_invite_session_store._sessions[expired_session.session_id] = expired_session

    return {
        "active_grant": active_grant,
        "used_grant": used_grant,
        "revoked_grant": revoked_grant,
        "expired_grant": expired_grant,
        "active_session": active_session,
        "revoked_session": revoked_session,
        "completed_session": completed_session,
        "expired_session": expired_session,
    }


def _client() -> TestClient:
    return TestClient(app)


def _set_base_env(monkeypatch) -> None:
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


def _provider_events(session: AiDemoSession) -> None:
    allowed = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        100,
        100,
        session,
        _budget_settings(),
    )
    assert allowed.allowed is True

    skipped = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        100,
        100,
        session,
        _budget_settings(calls_enabled=False, global_disable=True, configured=False),
    )
    assert skipped.allowed is True

    blocked = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        12001,
        100,
        session,
        _budget_settings(),
    )
    assert blocked.allowed is False

    failed = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "openai",
        "gpt-5.4-nano",
        100,
        100,
        session,
        _budget_settings(configured=False, validation_errors=("AI_PROVIDER_CALLS_ENABLED invalid.",)),
    )
    assert failed.allowed is False


def _quality_events(session_id: str) -> None:
    default_usage_report_collector.record_quality_event(
        AiQualityEvent(
            event_id="quality_pass_001",
            session_id=session_id,
            workflow=AiAccessWorkflow.RECIPE_SESSION,
            eval_group="report",
            case_id="pass_case",
            status=AiQualityStatus.PASSED,
            support_level="strong",
            retrieved_count=3,
            citation_count=2,
            warning_count=0,
            latency_ms=25.0,
            safe_summary="Pass case",
        )
    )
    default_usage_report_collector.record_quality_event(
        AiQualityEvent(
            event_id="quality_warn_001",
            session_id=session_id,
            workflow=AiAccessWorkflow.RECIPE_SESSION,
            eval_group="report",
            case_id="warn_case",
            status=AiQualityStatus.WARNING,
            support_level="weak",
            retrieved_count=1,
            citation_count=0,
            warning_count=1,
            latency_ms=30.0,
            safe_summary="Warning case",
        )
    )
    default_usage_report_collector.record_quality_event(
        AiQualityEvent(
            event_id="quality_fail_001",
            session_id=session_id,
            workflow=AiAccessWorkflow.RECIPE_SESSION,
            eval_group="report",
            case_id="fail_case",
            status=AiQualityStatus.FAILED,
            support_level="weak",
            retrieved_count=0,
            citation_count=0,
            warning_count=0,
            latency_ms=40.0,
            safe_summary="Failure case",
        )
    )


def test_empty_report_returns_stable_defaults(monkeypatch):
    _set_base_env(monkeypatch)
    reset_provider_budget_tracker()
    reset_usage_report_collector()
    default_invite_session_store.reset()

    report = build_ai_usage_report(now=_now())

    assert report.summary.model_dump() == {
        "active_session_count": 0,
        "expired_session_count": 0,
        "revoked_session_count": 0,
        "completed_session_count": 0,
        "active_grant_count": 0,
        "used_grant_count": 0,
        "revoked_grant_count": 0,
        "expired_grant_count": 0,
        "provider_calls_allowed": 0,
        "provider_calls_blocked": 0,
        "provider_calls_skipped": 0,
        "provider_calls_failed": 0,
        "estimated_cost_usd_total": Decimal("0.00"),
        "remaining_estimated_cost_usd_total": Decimal("0.00"),
        "quality_pass_count": 0,
        "quality_warning_count": 0,
        "quality_failure_count": 0,
        "threshold_warning_count": 0,
    }
    assert report.sessions == []
    assert report.grants == []
    assert report.provider_meter_events == []
    assert report.budget_snapshots == []
    assert report.quality_events == []
    assert report.audit_events == []
    assert report.warnings == []
    assert report.thresholds == []
    _assert_safe(report.model_dump(mode="json"))


def test_report_counts_grants_sessions_and_thresholds(monkeypatch):
    _set_base_env(monkeypatch)
    reset_provider_budget_tracker()
    reset_usage_report_collector()

    state = _seed_report_state()
    _provider_events(state["active_session"])
    _quality_events(state["active_session"].session_id)

    report = build_ai_usage_report(now=_now())

    assert report.summary.active_grant_count == 1
    assert report.summary.used_grant_count == 1
    assert report.summary.revoked_grant_count == 1
    assert report.summary.expired_grant_count == 1
    assert report.summary.active_session_count == 1
    assert report.summary.revoked_session_count == 1
    assert report.summary.completed_session_count == 1
    assert report.summary.expired_session_count == 1
    assert report.summary.provider_calls_allowed == 1
    assert report.summary.provider_calls_blocked == 1
    assert report.summary.provider_calls_skipped == 1
    assert report.summary.provider_calls_failed == 1
    assert report.summary.estimated_cost_usd_total == Decimal("0.80")
    assert report.summary.remaining_estimated_cost_usd_total == Decimal("0.20")
    assert report.summary.quality_pass_count == 1
    assert report.summary.quality_warning_count == 1
    assert report.summary.quality_failure_count == 1
    assert report.summary.threshold_warning_count == 6

    session_map = {item.session_id: item for item in report.sessions}
    grant_map = {item.grant_id: item for item in report.grants}
    assert session_map["session_active_001"].budget_snapshot["remaining_provider_calls"] == 1
    assert session_map["session_active_001"].budget_snapshot["remaining_estimated_cost_usd"] == "0.20"
    assert session_map["session_active_001"].near_call_exhaustion is True
    assert session_map["session_active_001"].near_cost_exhaustion is True
    assert grant_map["grant_active_001"].budget_snapshot["provider_call_count"] == 4
    assert grant_map["grant_active_001"].budget_snapshot["remaining_estimated_cost_usd"] == "0.20"
    assert report.thresholds[0].code == "session_call_budget_near_exhaustion"
    assert {warning.code for warning in report.warnings} >= {
        "session_call_budget_near_exhaustion",
        "session_cost_budget_near_exhaustion",
        "provider_call_blocked",
        "provider_call_failed",
        "quality_failure",
        "quality_warning",
    }
    _assert_safe(report.model_dump(mode="json"))


def test_report_serialization_excludes_forbidden_strings(monkeypatch):
    _set_base_env(monkeypatch)
    reset_provider_budget_tracker()
    reset_usage_report_collector()
    _seed_report_state()

    report = build_ai_usage_report(now=_now())
    _assert_safe(report.model_dump(mode="json"))


def test_usage_report_endpoint_is_protected_when_gate_enabled(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")
    token = "operator-secret"
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", fingerprint_operator_token(token))

    client = _client()

    response = client.get("/ai/admin/usage-report")

    assert response.status_code == 403
    _assert_safe(response.text)


def test_usage_report_endpoint_hides_raw_tokens(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AI_INVITE_SESSIONS_ENABLED", "true")
    client = _client()

    create_response = client.post(
        "/ai/invite/grants",
        json={"allowed_workflows": ["importer"], "notes": "report token test"},
    )
    assert create_response.status_code == 200
    invite_token = create_response.json()["invite_token"]

    redeem_response = client.post("/ai/invite/redeem", json={"invite_token": invite_token})
    assert redeem_response.status_code == 200
    session_token = redeem_response.json()["session_token"]

    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")
    operator_token = "operator-secret"
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", fingerprint_operator_token(operator_token))

    report_response = client.get("/ai/admin/usage-report", headers={"X-AI-Operator-Token": operator_token})

    assert report_response.status_code == 200
    assert invite_token not in report_response.text
    assert session_token not in report_response.text
    _assert_safe(report_response.text)


def test_usage_report_endpoint_allows_report_with_operator_token(monkeypatch):
    _set_base_env(monkeypatch)
    monkeypatch.setenv("AI_OPERATOR_GATE_ENABLED", "true")
    monkeypatch.setenv("AI_OPERATOR_GATE_LOCAL_BYPASS", "false")
    token = "operator-secret"
    monkeypatch.setenv("AI_OPERATOR_GATE_TOKEN_FINGERPRINT", fingerprint_operator_token(token))
    _seed_report_state()
    client = _client()

    response = client.get("/ai/admin/usage-report", headers={"X-AI-Operator-Token": token})

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["active_session_count"] == 1
    assert data["summary"]["provider_calls_blocked"] == 0
    _assert_safe(response.text)
