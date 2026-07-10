import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.ai_access_models import (
    AiAccessGrant,
    AiAccessGrantStatus,
    AiAccessGrantType,
    AiAccessWorkflow,
    AiAdminAuditAction,
    AiAdminAuditEvent,
    AiBudgetSnapshot,
    AiDemoSession,
    AiDemoSessionStatus,
    AiDemoSessionType,
    AiProviderMeterEvent,
    AiProviderMeterStatus,
    AiQualityEvent,
    AiQualityStatus,
    safe_operator_view,
)


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


def _now() -> datetime:
    return datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


def _assert_safe(payload: object) -> None:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in serialized


def test_demo_session_defaults_and_safe_view():
    session = AiDemoSession(
        session_id="ads_local_001",
        expires_at=_now() + timedelta(minutes=30),
        operator_label="local-operator",
        metadata_fingerprint="fp_session_123",
    )

    assert session.session_type == AiDemoSessionType.LOCAL_OPERATOR
    assert session.status == AiDemoSessionStatus.ACTIVE
    assert session.request_count == 0
    assert session.provider_call_count == 0
    assert session.estimated_cost_usd == Decimal("0.00")
    view = session.safe_view()
    assert view["session_id"] == "ads_local_001"
    _assert_safe(view)


def test_access_grant_defaults_and_workflows():
    grant = AiAccessGrant(
        grant_id="grant_local_001",
        expires_at=_now() + timedelta(hours=1),
        max_provider_calls=8,
        max_estimated_cost_usd=Decimal("0.25"),
        allowed_workflows=[AiAccessWorkflow.IMPORTER, AiAccessWorkflow.RECIPE_SESSION],
        notes="local operator demo",
        metadata_fingerprint="fp_grant_123",
    )

    assert grant.grant_type == AiAccessGrantType.LOCAL_OPERATOR
    assert grant.status == AiAccessGrantStatus.ACTIVE
    assert grant.max_sessions == 1
    view = grant.safe_view()
    assert view["allowed_workflows"] == ["importer", "recipe_session"]
    _assert_safe(view)


def test_provider_meter_event_supports_mock_offline_provider():
    event = AiProviderMeterEvent(
        event_id="meter_mock_001",
        session_id="ads_local_001",
        workflow=AiAccessWorkflow.RECIPE_SESSION,
        provider="mock",
        model="mock-basic",
        status=AiProviderMeterStatus.SKIPPED,
        reason="mock provider; no billable provider call",
        request_id="req_mock_001",
        safe_metadata={"offline": True, "provider_call": False},
    )

    assert event.estimated_cost_usd is None
    assert event.total_tokens is None
    _assert_safe(event.safe_view())


def test_provider_meter_event_calculates_total_tokens_and_serializes_cost():
    event = AiProviderMeterEvent(
        event_id="meter_openai_001",
        session_id="ads_invite_001",
        workflow=AiAccessWorkflow.IMPORTER,
        provider="openai",
        model="gpt-5.4-nano",
        input_tokens=700,
        output_tokens=250,
        estimated_cost_usd=Decimal("0.0031"),
        status=AiProviderMeterStatus.ALLOWED,
        request_id="req_live_001",
    )

    assert event.total_tokens == 950
    view = event.safe_view()
    assert view["estimated_cost_usd"] == "0.0031"
    _assert_safe(view)


def test_quality_event_safe_view():
    event = AiQualityEvent(
        event_id="quality_001",
        session_id="ads_local_001",
        workflow=AiAccessWorkflow.RECIPE_SESSION,
        eval_group="recipe_session",
        case_id="no_bake_refreshes_rag",
        status=AiQualityStatus.PASSED,
        support_level="strong",
        retrieved_count=3,
        citation_count=3,
        warning_count=0,
        latency_ms=42.5,
        safe_summary="RAG refreshed for method change",
    )

    view = safe_operator_view(event)
    assert view["status"] == "passed"
    assert view["retrieved_count"] == 3
    _assert_safe(view)


def test_admin_audit_event_safe_view():
    event = AiAdminAuditEvent(
        event_id="audit_001",
        actor_label="local-operator",
        action=AiAdminAuditAction.GRANT_REVOKED,
        target_type="access_grant",
        target_id="grant_local_001",
        reason="operator cleanup",
        safe_metadata={"grant_fingerprint": "fp_grant_123"},
    )

    view = event.safe_view()
    assert view["action"] == "grant_revoked"
    assert view["safe_metadata"]["grant_fingerprint"] == "fp_grant_123"
    _assert_safe(view)


def test_budget_snapshot_remaining_budget_calculations():
    snapshot = AiBudgetSnapshot(
        session_id="ads_local_001",
        grant_id="grant_local_001",
        provider_call_count=2,
        max_provider_calls=5,
        estimated_cost_usd=Decimal("0.07"),
        max_estimated_cost_usd=Decimal("0.25"),
    )

    assert snapshot.remaining_provider_calls == 3
    assert snapshot.remaining_estimated_cost_usd == Decimal("0.18")
    assert snapshot.is_exhausted is False
    assert snapshot.status_reason == "within_budget"
    _assert_safe(snapshot.safe_view())


def test_budget_snapshot_exhausted_by_calls():
    snapshot = AiBudgetSnapshot(
        session_id="ads_local_001",
        provider_call_count=5,
        max_provider_calls=5,
        estimated_cost_usd=Decimal("0.01"),
        max_estimated_cost_usd=Decimal("0.25"),
    )

    assert snapshot.remaining_provider_calls == 0
    assert snapshot.remaining_estimated_cost_usd == Decimal("0.24")
    assert snapshot.is_exhausted is True
    assert snapshot.status_reason == "provider_call_limit_exhausted"


def test_budget_snapshot_exhausted_by_cost():
    snapshot = AiBudgetSnapshot(
        session_id="ads_local_001",
        provider_call_count=1,
        max_provider_calls=5,
        estimated_cost_usd=Decimal("0.25"),
        max_estimated_cost_usd=Decimal("0.25"),
    )

    assert snapshot.remaining_provider_calls == 4
    assert snapshot.remaining_estimated_cost_usd == Decimal("0.00")
    assert snapshot.is_exhausted is True
    assert snapshot.status_reason == "cost_limit_exhausted"


@pytest.mark.parametrize(
    ("model_class", "kwargs"),
    [
        (
            AiAccessGrant,
            {
                "grant_id": "grant_001",
                "notes": "invite code sk-secret should not be stored",
            },
        ),
        (
            AiProviderMeterEvent,
            {
                "event_id": "meter_001",
                "workflow": AiAccessWorkflow.IMPORTER,
                "provider": "mock",
                "safe_metadata": {"raw_provider_prompt": "hidden"},
            },
        ),
        (
            AiAdminAuditEvent,
            {
                "event_id": "audit_001",
                "actor_label": "admin",
                "action": AiAdminAuditAction.LIVE_ACCESS_ENABLED,
                "target_type": "session",
                "target_id": "C:\\Users\\private\\session",
            },
        ),
    ],
)
def test_models_reject_forbidden_secret_or_path_like_values(model_class, kwargs):
    with pytest.raises(ValueError):
        model_class(**kwargs)
