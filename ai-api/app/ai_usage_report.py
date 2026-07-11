from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.ai_access_models import (
    AiAccessGrant,
    AiAccessGrantStatus,
    AiAdminAuditEvent,
    AiBudgetSnapshot,
    AiDemoSession,
    AiDemoSessionStatus,
    AiProviderMeterEvent,
    AiProviderMeterStatus,
    AiQualityEvent,
    AiQualityStatus,
    utc_now,
)
from app.config import get_invite_session_settings, get_operator_gate_settings, get_provider_budget_settings

REPORT_EXPIRY_SOON_WINDOW = timedelta(minutes=15)
REPORT_THRESHOLD_RATIO = Decimal("0.8")
DEFAULT_MAX_COLLECTED_EVENTS = 128


class AiUsageReportWarning(BaseModel):
    severity: str = "warning"
    code: str
    message: str
    session_id: str | None = None
    grant_id: str | None = None


class AiUsageReportSummary(BaseModel):
    active_session_count: int = 0
    expired_session_count: int = 0
    revoked_session_count: int = 0
    completed_session_count: int = 0
    active_grant_count: int = 0
    used_grant_count: int = 0
    revoked_grant_count: int = 0
    expired_grant_count: int = 0
    provider_calls_allowed: int = 0
    provider_calls_blocked: int = 0
    provider_calls_skipped: int = 0
    provider_calls_failed: int = 0
    estimated_cost_usd_total: Decimal = Decimal("0.00")
    remaining_estimated_cost_usd_total: Decimal = Decimal("0.00")
    quality_pass_count: int = 0
    quality_warning_count: int = 0
    quality_failure_count: int = 0
    threshold_warning_count: int = 0


class AiUsageReportThreshold(BaseModel):
    severity: str = "warning"
    code: str
    message: str
    session_id: str | None = None
    grant_id: str | None = None
    expires_at: datetime | None = None


class AiUsageReportSession(BaseModel):
    session_id: str
    session_type: str
    status: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    operator_label: str | None = None
    access_grant_id: str | None = None
    allowed_workflows: list[str] = Field(default_factory=list)
    max_provider_calls: int | None = None
    max_estimated_cost_usd: Decimal | None = None
    request_count: int = 0
    provider_call_count: int = 0
    estimated_cost_usd: Decimal = Decimal("0.00")
    last_activity_at: datetime | None = None
    metadata_fingerprint: str | None = None
    budget_snapshot: dict[str, Any] | None = None
    expires_soon: bool = False
    near_call_exhaustion: bool = False
    near_cost_exhaustion: bool = False


class AiUsageReportGrant(BaseModel):
    grant_id: str
    grant_type: str
    status: str
    created_at: datetime
    expires_at: datetime | None = None
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    max_sessions: int = 0
    max_provider_calls: int | None = None
    max_estimated_cost_usd: Decimal | None = None
    allowed_workflows: list[str] = Field(default_factory=list)
    notes: str | None = None
    metadata_fingerprint: str | None = None
    invite_token_fingerprint: str | None = None
    active_session_count: int = 0
    total_session_count: int = 0
    budget_snapshot: dict[str, Any] | None = None
    expires_soon: bool = False
    near_call_exhaustion: bool = False
    near_cost_exhaustion: bool = False


class AiUsageReport(BaseModel):
    summary: AiUsageReportSummary
    sessions: list[AiUsageReportSession] = Field(default_factory=list)
    grants: list[AiUsageReportGrant] = Field(default_factory=list)
    provider_meter_events: list[dict[str, Any]] = Field(default_factory=list)
    budget_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    quality_events: list[dict[str, Any]] = Field(default_factory=list)
    audit_events: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[AiUsageReportWarning] = Field(default_factory=list)
    thresholds: list[AiUsageReportThreshold] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)


@dataclass
class AiUsageReportCollector:
    max_events: int = DEFAULT_MAX_COLLECTED_EVENTS

    def __post_init__(self) -> None:
        if self.max_events < 1:
            raise ValueError("max_events must be at least 1")
        self._quality_events: OrderedDict[str, AiQualityEvent] = OrderedDict()
        self._audit_events: OrderedDict[str, AiAdminAuditEvent] = OrderedDict()

    def reset(self) -> None:
        self._quality_events.clear()
        self._audit_events.clear()

    def record_quality_event(self, event: AiQualityEvent) -> None:
        self._quality_events[event.event_id] = event
        self._quality_events.move_to_end(event.event_id)
        self._evict(self._quality_events)

    def record_audit_event(self, event: AiAdminAuditEvent) -> None:
        self._audit_events[event.event_id] = event
        self._audit_events.move_to_end(event.event_id)
        self._evict(self._audit_events)

    def quality_events(self) -> list[AiQualityEvent]:
        return list(self._quality_events.values())

    def audit_events(self) -> list[AiAdminAuditEvent]:
        return list(self._audit_events.values())

    def _evict(self, events: OrderedDict[str, Any]) -> None:
        while len(events) > self.max_events:
            events.popitem(last=False)


default_usage_report_collector = AiUsageReportCollector()


def reset_usage_report_collector() -> None:
    default_usage_report_collector.reset()


def record_usage_report_quality_event(event: AiQualityEvent) -> None:
    default_usage_report_collector.record_quality_event(event)


def record_usage_report_audit_event(event: AiAdminAuditEvent) -> None:
    default_usage_report_collector.record_audit_event(event)


def build_ai_usage_report(*, now: datetime | None = None) -> AiUsageReport:
    current_time = now or utc_now()
    invite_settings = get_invite_session_settings()
    operator_settings = get_operator_gate_settings()
    budget_settings = get_provider_budget_settings()

    from app.ai_budget_guard import default_provider_budget_tracker
    from app.ai_invite_sessions import default_invite_session_store

    sessions = default_invite_session_store.list_sessions(now=current_time)
    grants = default_invite_session_store.list_grants(now=current_time)
    sessions_by_grant = _sessions_by_grant(sessions)
    meter_events = default_provider_budget_tracker.list_meter_events()
    quality_events = default_usage_report_collector.quality_events()
    audit_events = default_usage_report_collector.audit_events()

    thresholds: list[AiUsageReportThreshold] = []
    thresholds.extend(_thresholds_from_sessions(sessions, current_time))
    thresholds.extend(_thresholds_from_grants(grants, current_time))
    thresholds.extend(_config_thresholds(invite_settings, operator_settings, budget_settings))
    thresholds.extend(_meter_thresholds(meter_events))
    thresholds.extend(_quality_thresholds(quality_events))
    budget_snapshots = _budget_snapshots(sessions, grants)
    summary_budget_snapshots = _summary_budget_snapshots(sessions, grants, sessions_by_grant)

    summary = _build_summary(sessions, grants, meter_events, quality_events, summary_budget_snapshots)
    summary.threshold_warning_count = len(thresholds)

    budget_snapshots_rows = [snapshot.safe_view() for snapshot in budget_snapshots]
    warnings = [
        AiUsageReportWarning(
            severity=item.severity,
            code=item.code,
            message=item.message,
            session_id=item.session_id,
            grant_id=item.grant_id,
        )
        for item in thresholds
    ]

    session_rows = [_session_row(session, current_time) for session in sessions]
    grant_rows = [
        _grant_row(
            grant,
            sessions_by_grant.get(grant.grant_id, []),
            active_session_count=default_invite_session_store.count_active_sessions_for_grant(grant.grant_id, now=current_time),
            total_session_count=default_invite_session_store.count_sessions_for_grant(grant.grant_id, now=current_time),
            now=current_time,
        )
        for grant in grants
    ]

    return AiUsageReport(
        summary=summary,
        sessions=session_rows,
        grants=grant_rows,
        provider_meter_events=[event.safe_view() for event in meter_events],
        budget_snapshots=budget_snapshots_rows,
        quality_events=[event.safe_view() for event in quality_events],
        audit_events=[event.safe_view() for event in audit_events],
        warnings=warnings,
        thresholds=thresholds,
        generated_at=current_time,
    )


def _build_summary(
    sessions: list[AiDemoSession],
    grants: list[AiAccessGrant],
    meter_events: list[AiProviderMeterEvent],
    quality_events: list[AiQualityEvent],
    budget_snapshots: list[AiBudgetSnapshot],
) -> AiUsageReportSummary:
    summary = AiUsageReportSummary()
    summary.active_session_count = sum(1 for session in sessions if session.status == AiDemoSessionStatus.ACTIVE)
    summary.expired_session_count = sum(1 for session in sessions if session.status == AiDemoSessionStatus.EXPIRED)
    summary.revoked_session_count = sum(1 for session in sessions if session.status == AiDemoSessionStatus.REVOKED)
    summary.completed_session_count = sum(1 for session in sessions if session.status == AiDemoSessionStatus.COMPLETED)
    summary.active_grant_count = sum(1 for grant in grants if grant.status == AiAccessGrantStatus.ACTIVE)
    summary.used_grant_count = sum(1 for grant in grants if grant.status == AiAccessGrantStatus.USED)
    summary.revoked_grant_count = sum(1 for grant in grants if grant.status == AiAccessGrantStatus.REVOKED)
    summary.expired_grant_count = sum(1 for grant in grants if grant.status == AiAccessGrantStatus.EXPIRED)
    summary.provider_calls_allowed = sum(1 for event in meter_events if event.status == AiProviderMeterStatus.ALLOWED)
    summary.provider_calls_blocked = sum(1 for event in meter_events if event.status == AiProviderMeterStatus.BLOCKED)
    summary.provider_calls_skipped = sum(1 for event in meter_events if event.status == AiProviderMeterStatus.SKIPPED)
    summary.provider_calls_failed = sum(1 for event in meter_events if event.status == AiProviderMeterStatus.FAILED)
    summary.estimated_cost_usd_total = sum((_safe_decimal(snapshot.estimated_cost_usd) for snapshot in budget_snapshots), Decimal("0.00"))
    summary.remaining_estimated_cost_usd_total = sum(
        (_safe_decimal(snapshot.remaining_estimated_cost_usd) for snapshot in budget_snapshots),
        Decimal("0.00"),
    )
    summary.quality_pass_count = sum(1 for event in quality_events if event.status == AiQualityStatus.PASSED)
    summary.quality_warning_count = sum(1 for event in quality_events if event.status == AiQualityStatus.WARNING or (event.warning_count or 0) > 0)
    summary.quality_failure_count = sum(1 for event in quality_events if event.status == AiQualityStatus.FAILED)
    return summary


def _session_row(session: AiDemoSession, now: datetime) -> AiUsageReportSession:
    budget_snapshot = _budget_snapshot(session=session)
    return AiUsageReportSession(
        session_id=session.session_id,
        session_type=session.session_type.value,
        status=session.status.value,
        created_at=session.created_at,
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
        revoked_reason=session.revoked_reason,
        operator_label=session.operator_label,
        access_grant_id=session.access_grant_id,
        allowed_workflows=[workflow.value for workflow in session.allowed_workflows],
        max_provider_calls=session.max_provider_calls,
        max_estimated_cost_usd=session.max_estimated_cost_usd,
        request_count=session.request_count,
        provider_call_count=session.provider_call_count,
        estimated_cost_usd=session.estimated_cost_usd,
        last_activity_at=session.last_activity_at,
        metadata_fingerprint=session.metadata_fingerprint,
        budget_snapshot=budget_snapshot.safe_view() if budget_snapshot else None,
        expires_soon=_expires_soon(session.expires_at, now),
        near_call_exhaustion=_limit_ratio(session.provider_call_count, session.max_provider_calls) >= REPORT_THRESHOLD_RATIO if session.max_provider_calls else False,
        near_cost_exhaustion=_cost_ratio(session.estimated_cost_usd, session.max_estimated_cost_usd) >= REPORT_THRESHOLD_RATIO if session.max_estimated_cost_usd is not None else False,
    )


def _grant_row(
    grant: AiAccessGrant,
    sessions: list[AiDemoSession],
    *,
    active_session_count: int,
    total_session_count: int,
    now: datetime,
) -> AiUsageReportGrant:
    budget_snapshot = _grant_budget_snapshot(grant, sessions)
    return AiUsageReportGrant(
        grant_id=grant.grant_id,
        grant_type=grant.grant_type.value,
        status=grant.status.value,
        created_at=grant.created_at,
        expires_at=grant.expires_at,
        used_at=grant.used_at,
        revoked_at=grant.revoked_at,
        revoked_reason=grant.revoked_reason,
        max_sessions=grant.max_sessions,
        max_provider_calls=grant.max_provider_calls,
        max_estimated_cost_usd=grant.max_estimated_cost_usd,
        allowed_workflows=[workflow.value for workflow in grant.allowed_workflows],
        notes=grant.notes,
        metadata_fingerprint=grant.metadata_fingerprint,
        invite_token_fingerprint=grant.invite_token_fingerprint,
        active_session_count=active_session_count,
        total_session_count=total_session_count,
        budget_snapshot=budget_snapshot.safe_view() if budget_snapshot else None,
        expires_soon=_expires_soon(grant.expires_at, now),
        near_call_exhaustion=_limit_ratio(total_session_count, grant.max_sessions) >= REPORT_THRESHOLD_RATIO if grant.max_sessions else False,
        near_cost_exhaustion=_cost_ratio(budget_snapshot.estimated_cost_usd, grant.max_estimated_cost_usd) >= REPORT_THRESHOLD_RATIO if grant.max_estimated_cost_usd is not None else False,
    )


def _budget_snapshot(*, session: AiDemoSession | None = None, grant: AiAccessGrant | None = None) -> AiBudgetSnapshot | None:
    if session is not None:
        return AiBudgetSnapshot(
            session_id=session.session_id,
            grant_id=session.access_grant_id,
            provider_call_count=session.provider_call_count,
            max_provider_calls=session.max_provider_calls,
            estimated_cost_usd=session.estimated_cost_usd,
            max_estimated_cost_usd=session.max_estimated_cost_usd,
        )
    if grant is not None:
        return _grant_budget_snapshot(grant, [])
    return None


def _budget_snapshots(sessions: list[AiDemoSession], grants: list[AiAccessGrant]) -> list[AiBudgetSnapshot]:
    snapshots: list[AiBudgetSnapshot] = []
    for session in sessions:
        snapshot = _budget_snapshot(session=session)
        if snapshot is not None:
            snapshots.append(snapshot)
    for grant in grants:
        snapshot = _grant_budget_snapshot(grant, [session for session in sessions if session.access_grant_id == grant.grant_id])
        if snapshot is not None:
            snapshots.append(snapshot)
    return snapshots


def _summary_budget_snapshots(
    sessions: list[AiDemoSession],
    grants: list[AiAccessGrant],
    sessions_by_grant: dict[str, list[AiDemoSession]],
) -> list[AiBudgetSnapshot]:
    snapshots: list[AiBudgetSnapshot] = []
    for session in sessions:
        snapshot = _budget_snapshot(session=session)
        if snapshot is not None:
            snapshots.append(snapshot)
    for grant in grants:
        if sessions_by_grant.get(grant.grant_id):
            continue
        snapshots.append(_grant_budget_snapshot(grant, []))
    return snapshots


def _thresholds_from_sessions(sessions: list[AiDemoSession], now: datetime) -> list[AiUsageReportThreshold]:
    thresholds: list[AiUsageReportThreshold] = []
    for session in sessions:
        if session.status == AiDemoSessionStatus.ACTIVE and _expires_soon(session.expires_at, now):
            thresholds.append(
                AiUsageReportThreshold(
                    severity="warning",
                    code="session_expires_soon",
                    message="Active demo session expires soon.",
                    session_id=session.session_id,
                    grant_id=session.access_grant_id,
                    expires_at=session.expires_at,
                )
            )
        if session.status == AiDemoSessionStatus.ACTIVE and session.max_provider_calls and _limit_ratio(session.provider_call_count, session.max_provider_calls) >= REPORT_THRESHOLD_RATIO:
            thresholds.append(
                AiUsageReportThreshold(
                    severity="warning",
                    code="session_call_budget_near_exhaustion",
                    message="Session provider-call budget is close to exhaustion.",
                    session_id=session.session_id,
                    grant_id=session.access_grant_id,
                    expires_at=session.expires_at,
                )
            )
        if session.status == AiDemoSessionStatus.ACTIVE and session.max_estimated_cost_usd is not None and _cost_ratio(session.estimated_cost_usd, session.max_estimated_cost_usd) >= REPORT_THRESHOLD_RATIO:
            thresholds.append(
                AiUsageReportThreshold(
                    severity="warning",
                    code="session_cost_budget_near_exhaustion",
                    message="Session estimated-cost budget is close to exhaustion.",
                    session_id=session.session_id,
                    grant_id=session.access_grant_id,
                    expires_at=session.expires_at,
                )
            )
    return thresholds


def _thresholds_from_grants(grants: list[AiAccessGrant], now: datetime) -> list[AiUsageReportThreshold]:
    thresholds: list[AiUsageReportThreshold] = []
    for grant in grants:
        if grant.status == AiAccessGrantStatus.ACTIVE and _expires_soon(grant.expires_at, now):
            thresholds.append(
                AiUsageReportThreshold(
                    severity="warning",
                    code="grant_expires_soon",
                    message="Active invite grant expires soon.",
                    grant_id=grant.grant_id,
                    expires_at=grant.expires_at,
                )
            )
    return thresholds


def _config_thresholds(invite_settings: Any, operator_settings: Any, budget_settings: Any) -> list[AiUsageReportThreshold]:
    thresholds: list[AiUsageReportThreshold] = []
    if invite_settings.enabled and not operator_settings.enabled:
        thresholds.append(
            AiUsageReportThreshold(
                severity="warning",
                code="operator_gate_disabled_with_invites_enabled",
                message="Invite sessions are enabled while the operator gate is disabled.",
            )
        )
    if invite_settings.enabled and (not budget_settings.configured or not budget_settings.calls_enabled or budget_settings.global_disable):
        thresholds.append(
            AiUsageReportThreshold(
                severity="critical",
                code="budget_guard_disabled_or_misconfigured",
                message="Invite sessions are enabled while the provider budget guard is disabled or misconfigured.",
            )
        )
    if budget_settings.validation_errors:
        thresholds.append(
            AiUsageReportThreshold(
                severity="critical",
                code="budget_guard_validation_errors",
                message="Provider budget settings contain validation errors.",
            )
        )
    return thresholds


def _meter_thresholds(meter_events: list[AiProviderMeterEvent]) -> list[AiUsageReportThreshold]:
    thresholds: list[AiUsageReportThreshold] = []
    if any(event.status == AiProviderMeterStatus.BLOCKED for event in meter_events):
        thresholds.append(
            AiUsageReportThreshold(
                severity="warning",
                code="provider_call_blocked",
                message="At least one provider decision was blocked.",
            )
        )
    if any(event.status == AiProviderMeterStatus.FAILED for event in meter_events):
        thresholds.append(
            AiUsageReportThreshold(
                severity="critical",
                code="provider_call_failed",
                message="At least one provider decision failed.",
            )
        )
    return thresholds


def _quality_thresholds(quality_events: list[AiQualityEvent]) -> list[AiUsageReportThreshold]:
    thresholds: list[AiUsageReportThreshold] = []
    if any(event.status == AiQualityStatus.FAILED for event in quality_events):
        thresholds.append(
            AiUsageReportThreshold(
                severity="critical",
                code="quality_failure",
                message="At least one quality or eval event failed.",
            )
        )
    if any(event.status == AiQualityStatus.WARNING for event in quality_events):
        thresholds.append(
            AiUsageReportThreshold(
                severity="warning",
                code="quality_warning",
                message="At least one quality or eval event emitted a warning.",
            )
        )
    return thresholds


def _expires_soon(expires_at: datetime | None, now: datetime) -> bool:
    if expires_at is None:
        return False
    return now <= expires_at <= now + REPORT_EXPIRY_SOON_WINDOW


def _limit_ratio(current: int, maximum: int | None) -> Decimal:
    if not maximum:
        return Decimal("0.00")
    return Decimal(current) / Decimal(maximum)


def _cost_ratio(current: Decimal, maximum: Decimal | None) -> Decimal:
    if maximum is None or maximum == Decimal("0.00"):
        return Decimal("0.00")
    return _safe_decimal(current) / maximum


def _safe_decimal(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return value


def _grant_budget_snapshot(grant: AiAccessGrant, sessions: list[AiDemoSession]) -> AiBudgetSnapshot:
    provider_call_count = sum(session.provider_call_count for session in sessions)
    estimated_cost_usd = sum((session.estimated_cost_usd for session in sessions), Decimal("0.00"))
    return AiBudgetSnapshot(
        session_id=None,
        grant_id=grant.grant_id,
        provider_call_count=provider_call_count,
        max_provider_calls=grant.max_provider_calls,
        estimated_cost_usd=estimated_cost_usd,
        max_estimated_cost_usd=grant.max_estimated_cost_usd,
    )


def _sessions_by_grant(sessions: list[AiDemoSession]) -> dict[str, list[AiDemoSession]]:
    grouped: dict[str, list[AiDemoSession]] = {}
    for session in sessions:
        if not session.access_grant_id:
            continue
        grouped.setdefault(session.access_grant_id, []).append(session)
    return grouped
