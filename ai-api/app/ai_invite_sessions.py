from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from app.ai_access_models import (
    AiAccessGrant,
    AiAccessGrantStatus,
    AiAccessGrantType,
    AiAccessWorkflow,
    AiAdminAuditAction,
    AiAdminAuditEvent,
    AiDemoSession,
    AiDemoSessionStatus,
    AiDemoSessionType,
    AiProviderBudgetStatus,
    AiProviderMeterEvent,
    AiProviderMeterStatus,
    utc_now,
)
from app.ai_budget_guard import check_provider_budget
from app.ai_operator_gate import check_operator_gate, operator_gate_http_exception
from app.config import (
    InviteSessionSettings,
    ProviderBudgetSettings,
    get_invite_session_settings,
    get_operator_gate_settings,
    get_provider_budget_settings,
)
from app.observability import log_ai_workflow
from app.schemas import (
    AiInviteGrantCreateRequest,
    AiInviteGrantResponse,
    AiInviteRedeemRequest,
    AiInviteSessionResponse,
    AiInviteStatusResponse,
)


router = APIRouter(prefix="/ai/invite", tags=["invite-demo-session"])
invite_router = router

INVITE_TOKEN_HEADER = "x-ai-demo-session-token"
AUTHORIZATION_HEADER = "authorization"
LOCAL_HOST_MARKERS = {"127.0.0.1", "::1", "localhost", "testclient"}
DEFAULT_STORE_MAX_GRANTS = 64
DEFAULT_STORE_MAX_SESSIONS = 128


@dataclass(frozen=True)
class InviteGrantResult:
    grant: AiAccessGrant
    invite_token: str
    audit_event: AiAdminAuditEvent


@dataclass(frozen=True)
class InviteSessionResult:
    grant: AiAccessGrant
    session: AiDemoSession
    session_token: str
    budget_snapshot: AiBudgetSnapshot | None
    meter_event: AiProviderMeterEvent | None
    audit_event: AiAdminAuditEvent


class InviteSessionError(RuntimeError):
    def __init__(self, status_code: int, response_state: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_state = response_state
        self.message = message


class AiInviteSessionStore:
    """Small process-local invite/session store for local demos and tests only."""

    def __init__(self, *, max_grants: int = DEFAULT_STORE_MAX_GRANTS, max_sessions: int = DEFAULT_STORE_MAX_SESSIONS) -> None:
        if max_grants < 1:
            raise ValueError("max_grants must be at least 1")
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        self.max_grants = max_grants
        self.max_sessions = max_sessions
        self._grants: OrderedDict[str, AiAccessGrant] = OrderedDict()
        self._sessions: OrderedDict[str, AiDemoSession] = OrderedDict()
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._grants.clear()
            self._sessions.clear()

    def expire(self, now: datetime | None = None) -> int:
        current_time = now or utc_now()
        expired = 0
        with self._lock:
            for grant_id, grant in list(self._grants.items()):
                if grant.expires_at and grant.expires_at <= current_time:
                    self._grants[grant_id] = grant.model_copy(update={"status": AiAccessGrantStatus.EXPIRED, "revoked_at": grant.revoked_at})
                    self._grants.pop(grant_id, None)
                    expired += 1
            for session_id, session in list(self._sessions.items()):
                if session.expires_at <= current_time:
                    self._sessions.pop(session_id, None)
                    expired += 1
        return expired

    def count_grants(self, *, now: datetime | None = None) -> int:
        self.expire(now)
        with self._lock:
            return len(self._grants)

    def count_sessions(self, *, now: datetime | None = None) -> int:
        self.expire(now)
        with self._lock:
            return len(self._sessions)

    def count_sessions_for_grant(self, grant_id: str, *, now: datetime | None = None) -> int:
        self.expire(now)
        with self._lock:
            return sum(1 for session in self._sessions.values() if session.access_grant_id == grant_id)

    def count_active_sessions_for_grant(self, grant_id: str, *, now: datetime | None = None) -> int:
        self.expire(now)
        with self._lock:
            return sum(
                1
                for session in self._sessions.values()
                if session.access_grant_id == grant_id and session.status == AiDemoSessionStatus.ACTIVE
            )

    def create_grant(
        self,
        request: AiInviteGrantCreateRequest,
        *,
        settings: InviteSessionSettings | None = None,
        now: datetime | None = None,
        actor_label: str | None = None,
    ) -> InviteGrantResult:
        invite_settings = settings or get_invite_session_settings()
        if not invite_settings.enabled:
            raise InviteSessionError(404, "disabled", "Invite-only demo sessions are disabled.")
        if not invite_settings.local_operator_create_enabled:
            raise InviteSessionError(403, "blocked", "Local operator creation is disabled.")
        current_time = now or utc_now()
        self.expire(current_time)
        grant_id = f"ig_{uuid4().hex[:12]}"
        invite_token = _normalize_token(request.token) or _generate_token("inv")
        invite_token_fingerprint = _fingerprint_token(invite_token)
        allowed_workflows = _parse_allowed_workflows(request.allowed_workflows or invite_settings.allowed_workflows)
        ttl_seconds = request.ttl_seconds or invite_settings.grant_ttl_seconds
        expires_at = current_time + timedelta(seconds=ttl_seconds)
        grant = AiAccessGrant(
            grant_id=grant_id,
            grant_type=AiAccessGrantType.INVITE_CODE,
            status=AiAccessGrantStatus.ACTIVE,
            created_at=current_time,
            expires_at=expires_at,
            max_sessions=request.max_sessions or invite_settings.max_sessions_per_grant,
            max_provider_calls=request.max_provider_calls
            if request.max_provider_calls is not None
            else invite_settings.default_max_provider_calls,
            max_estimated_cost_usd=request.max_estimated_cost_usd
            if request.max_estimated_cost_usd is not None
            else invite_settings.default_max_estimated_cost_usd,
            allowed_workflows=allowed_workflows,
            notes=request.notes,
            metadata_fingerprint=_metadata_fingerprint(
                grant_id,
                invite_token_fingerprint,
                allowed_workflows,
                request.max_sessions or invite_settings.max_sessions_per_grant,
            ),
            invite_token_fingerprint=invite_token_fingerprint,
        )
        with self._lock:
            self._grants[grant_id] = grant
            self._grants.move_to_end(grant_id)
            self._evict_over_limit()
        audit_event = AiAdminAuditEvent(
            event_id=f"ga_{uuid4().hex[:12]}",
            actor_label=actor_label or "local-operator",
            action=AiAdminAuditAction.GRANT_CREATED,
            target_type="invite_grant",
            target_id=grant_id,
            reason="Local invite grant created.",
            safe_metadata={
                "grant_id": grant_id,
                "invite_token_fingerprint": invite_token_fingerprint[:12],
                "allowed_workflows": ",".join(workflow.value for workflow in allowed_workflows),
            },
        )
        return InviteGrantResult(grant=grant, invite_token=invite_token, audit_event=audit_event)

    def redeem_invite_token(
        self,
        invite_token: str,
        *,
        settings: InviteSessionSettings | None = None,
        budget_settings: ProviderBudgetSettings | None = None,
        now: datetime | None = None,
        actor_label: str | None = None,
    ) -> InviteSessionResult:
        invite_settings = settings or get_invite_session_settings()
        if not invite_settings.enabled:
            raise InviteSessionError(404, "disabled", "Invite-only demo sessions are disabled.")
        current_time = now or utc_now()
        self.expire(current_time)
        token_value = _normalize_token(invite_token)
        if not token_value:
            raise InviteSessionError(403, "blocked", "Invite token is required.")
        grant = self._find_grant_by_token(token_value)
        if grant is None:
            raise InviteSessionError(404, "not_found", "Invite grant was not found or has expired.")
        if grant.status == AiAccessGrantStatus.REVOKED:
            raise InviteSessionError(403, "revoked", "Invite grant has been revoked.")
        if grant.expires_at and grant.expires_at <= current_time:
            self._expire_grant(grant.grant_id)
            raise InviteSessionError(404, "expired", "Invite grant has expired.")

        session_count = self._grant_session_count(grant.grant_id)
        if session_count >= grant.max_sessions:
            self._mark_grant_used(grant.grant_id, current_time)
            raise InviteSessionError(403, "used", "Invite grant has already been redeemed.")

        session_id = f"is_{uuid4().hex[:12]}"
        session_token = _generate_token("its")
        session_token_fingerprint = _fingerprint_token(session_token)
        session_expires_at = current_time + timedelta(seconds=invite_settings.session_ttl_seconds)
        session = AiDemoSession(
            session_id=session_id,
            session_type=AiDemoSessionType.INVITE,
            status=AiDemoSessionStatus.ACTIVE,
            created_at=current_time,
            expires_at=session_expires_at,
            operator_label=actor_label or "invite-session",
            access_grant_id=grant.grant_id,
            session_token_fingerprint=session_token_fingerprint,
            allowed_workflows=list(grant.allowed_workflows),
            max_provider_calls=grant.max_provider_calls,
            max_estimated_cost_usd=grant.max_estimated_cost_usd,
            metadata_fingerprint=_metadata_fingerprint(
                grant.grant_id,
                session_token_fingerprint,
                grant.allowed_workflows,
                session_id,
            ),
        )
        with self._lock:
            self._sessions[session_id] = session
            self._sessions.move_to_end(session_id)
            self._evict_over_limit()
            self._update_grant_status_after_session(grant.grant_id, current_time)

        budget_snapshot = check_provider_budget(
            AiAccessWorkflow.IMPORTER,
            "mock",
            "mock-basic",
            0,
            0,
            session,
            budget_settings or get_provider_budget_settings(),
        ).budget_snapshot
        audit_event = AiAdminAuditEvent(
            event_id=f"ga_{uuid4().hex[:12]}",
            actor_label=actor_label or "invite-session",
            action=AiAdminAuditAction.GRANT_REDEEMED,
            target_type="invite_session",
            target_id=session_id,
            reason="Invite token redeemed into a demo session.",
            safe_metadata={
                "grant_id": grant.grant_id,
                "session_id": session_id,
                "session_token_fingerprint": session_token_fingerprint[:12],
            },
        )
        return InviteSessionResult(
            grant=grant,
            session=session,
            session_token=session_token,
            budget_snapshot=budget_snapshot,
            meter_event=None,
            audit_event=audit_event,
        )

    def get_grant(self, grant_id: str, *, now: datetime | None = None) -> AiAccessGrant | None:
        self.expire(now)
        with self._lock:
            grant = self._grants.get(grant_id)
            if grant is None:
                return None
            self._grants.move_to_end(grant_id)
            return self._refresh_grant_state(grant, now or utc_now())

    def get_session(self, session_id: str, *, now: datetime | None = None) -> AiDemoSession | None:
        self.expire(now)
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            self._sessions.move_to_end(session_id)
            return self._refresh_session_state(session, now or utc_now())

    def revoke_grant(self, grant_id: str, *, reason: str | None = None, now: datetime | None = None) -> AiAccessGrant | None:
        current_time = now or utc_now()
        self.expire(current_time)
        with self._lock:
            grant = self._grants.get(grant_id)
            if grant is None:
                return None
            updated = grant.model_copy(
                update={
                    "status": AiAccessGrantStatus.REVOKED,
                    "revoked_at": current_time,
                    "revoked_reason": reason or "Local operator revoked the invite grant.",
                }
            )
            self._grants[grant_id] = updated
            self._grants.move_to_end(grant_id)
            return updated

    def revoke_session(self, session_id: str, *, reason: str | None = None, now: datetime | None = None) -> AiDemoSession | None:
        current_time = now or utc_now()
        self.expire(current_time)
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            updated = session.model_copy(
                update={
                    "status": AiDemoSessionStatus.REVOKED,
                    "revoked_at": current_time,
                    "revoked_reason": reason or "Local operator revoked the invite session.",
                }
            )
            self._sessions[session_id] = updated
            self._sessions.move_to_end(session_id)
            return updated

    def status(self, *, now: datetime | None = None) -> AiInviteStatusResponse:
        settings = get_invite_session_settings()
        self.expire(now)
        with self._lock:
            active_grants = sum(1 for grant in self._grants.values() if grant.status == AiAccessGrantStatus.ACTIVE)
            active_sessions = sum(1 for session in self._sessions.values() if session.status == AiDemoSessionStatus.ACTIVE)
            revoked_grants = sum(1 for grant in self._grants.values() if grant.status == AiAccessGrantStatus.REVOKED)
            expired_grants = sum(1 for grant in self._grants.values() if grant.status == AiAccessGrantStatus.EXPIRED)
            revoked_sessions = sum(1 for session in self._sessions.values() if session.status == AiDemoSessionStatus.REVOKED)
            expired_sessions = sum(1 for session in self._sessions.values() if session.status == AiDemoSessionStatus.EXPIRED)
        status_text = "configured" if settings.enabled and settings.configured else "disabled" if not settings.enabled else "misconfigured"
        message = (
            "Invite sessions are disabled."
            if not settings.enabled
            else "Invite sessions are available for local/private demo use only."
            if settings.configured
            else "Invite sessions are enabled, but the configuration needs attention."
        )
        return AiInviteStatusResponse(
            enabled=settings.enabled,
            configured=settings.configured,
            status=status_text,
            message=message,
            allowed_workflows=list(settings.allowed_workflows),
            local_operator_create_enabled=settings.local_operator_create_enabled,
            grant_ttl_seconds=settings.grant_ttl_seconds,
            session_ttl_seconds=settings.session_ttl_seconds,
            max_sessions_per_grant=settings.max_sessions_per_grant,
            default_max_provider_calls=settings.default_max_provider_calls,
            default_max_estimated_cost_usd=settings.default_max_estimated_cost_usd,
            active_grants=active_grants,
            active_sessions=active_sessions,
            warnings=list(settings.validation_errors),
        )

    def resolve_session_from_token(
        self,
        token: str,
        *,
        now: datetime | None = None,
    ) -> AiDemoSession | None:
        self.expire(now)
        token_value = _normalize_token(token)
        if not token_value:
            return None
        fingerprint = _fingerprint_token(token_value)
        with self._lock:
            for session in self._sessions.values():
                if session.session_token_fingerprint and hmac.compare_digest(session.session_token_fingerprint, fingerprint):
                    refreshed = self._refresh_session_state(session, now or utc_now())
                    if refreshed.status != AiDemoSessionStatus.ACTIVE:
                        return None
                    return refreshed
        return None

    def resolve_grant_by_token(self, token: str, *, now: datetime | None = None) -> AiAccessGrant | None:
        self.expire(now)
        token_value = _normalize_token(token)
        if not token_value:
            return None
        grant = self._find_grant_by_token(token_value)
        if grant is None:
            return None
        return self._refresh_grant_state(grant, now or utc_now())

    def _find_grant_by_token(self, token: str) -> AiAccessGrant | None:
        fingerprint = _fingerprint_token(token)
        with self._lock:
            for grant in self._grants.values():
                if grant.invite_token_fingerprint and hmac.compare_digest(grant.invite_token_fingerprint, fingerprint):
                    return grant
        return None

    def _grant_session_count(self, grant_id: str) -> int:
        with self._lock:
            return sum(1 for session in self._sessions.values() if session.access_grant_id == grant_id)

    def _update_grant_status_after_session(self, grant_id: str, now: datetime) -> None:
        with self._lock:
            grant = self._grants.get(grant_id)
            if grant is None:
                return
            count = self._grant_session_count(grant_id)
            status = AiAccessGrantStatus.USED if count >= grant.max_sessions else AiAccessGrantStatus.ACTIVE
            self._grants[grant_id] = grant.model_copy(update={"status": status, "used_at": now})

    def _mark_grant_used(self, grant_id: str, now: datetime) -> None:
        with self._lock:
            grant = self._grants.get(grant_id)
            if grant is None:
                return
            self._grants[grant_id] = grant.model_copy(update={"status": AiAccessGrantStatus.USED, "used_at": now})

    def _expire_grant(self, grant_id: str) -> None:
        with self._lock:
            grant = self._grants.get(grant_id)
            if grant is None:
                return
            self._grants[grant_id] = grant.model_copy(update={"status": AiAccessGrantStatus.EXPIRED})

    def _refresh_grant_state(self, grant: AiAccessGrant, now: datetime) -> AiAccessGrant:
        if grant.status in {AiAccessGrantStatus.REVOKED, AiAccessGrantStatus.EXPIRED}:
            return grant
        if grant.expires_at and grant.expires_at <= now:
            refreshed = grant.model_copy(update={"status": AiAccessGrantStatus.EXPIRED})
            with self._lock:
                self._grants[grant.grant_id] = refreshed
            return refreshed
        if self._grant_session_count(grant.grant_id) >= grant.max_sessions:
            refreshed = grant.model_copy(update={"status": AiAccessGrantStatus.USED, "used_at": grant.used_at or now})
            with self._lock:
                self._grants[grant.grant_id] = refreshed
            return refreshed
        return grant

    def _refresh_session_state(self, session: AiDemoSession, now: datetime) -> AiDemoSession:
        if session.status in {AiDemoSessionStatus.REVOKED, AiDemoSessionStatus.EXPIRED, AiDemoSessionStatus.COMPLETED}:
            return session
        if session.expires_at <= now:
            refreshed = session.model_copy(update={"status": AiDemoSessionStatus.EXPIRED})
            with self._lock:
                self._sessions[session.session_id] = refreshed
            return refreshed
        grant = self._grants.get(session.access_grant_id) if session.access_grant_id else None
        if grant and grant.status == AiAccessGrantStatus.REVOKED:
            refreshed = session.model_copy(update={"status": AiDemoSessionStatus.REVOKED, "revoked_at": now, "revoked_reason": "Invite grant was revoked."})
            with self._lock:
                self._sessions[session.session_id] = refreshed
            return refreshed
        return session

    def _evict_over_limit(self) -> None:
        while len(self._grants) > self.max_grants:
            self._grants.popitem(last=False)
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)


default_invite_session_store = AiInviteSessionStore()


@router.get("/status", response_model=AiInviteStatusResponse)
def invite_status() -> AiInviteStatusResponse:
    return default_invite_session_store.status()


@router.post("/grants", response_model=AiInviteGrantResponse)
def create_invite_grant(payload: AiInviteGrantCreateRequest, request: Request) -> AiInviteGrantResponse:
    _require_local_operator_access(request)
    try:
        result = default_invite_session_store.create_grant(
            payload,
            actor_label=_actor_label(request),
        )
    except InviteSessionError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"response_state": exc.response_state, "message": exc.message}) from exc
    log_ai_workflow("invite.grant.create", request, status="created", warning_count=0)
    return AiInviteGrantResponse(
        grant=result.grant,
        invite_token=result.invite_token,
        session_count=default_invite_session_store.count_sessions_for_grant(result.grant.grant_id),
        active_session_count=default_invite_session_store.count_active_sessions_for_grant(result.grant.grant_id),
        audit_event=result.audit_event,
    )


@router.post("/redeem", response_model=AiInviteSessionResponse)
def redeem_invite(payload: AiInviteRedeemRequest, request: Request) -> AiInviteSessionResponse:
    try:
        result = default_invite_session_store.redeem_invite_token(
            payload.invite_token,
            actor_label=payload.operator_label or _actor_label(request),
        )
    except InviteSessionError as exc:
        raise HTTPException(status_code=exc.status_code, detail={"response_state": exc.response_state, "message": exc.message}) from exc
    log_ai_workflow(
        "invite.session.redeem",
        request,
        provider=result.session.session_type.value,
        status="redeemed",
        warning_count=0,
    )
    return AiInviteSessionResponse(
        grant=result.grant,
        session=result.session,
        session_token=result.session_token,
        budget_snapshot=result.budget_snapshot,
        audit_event=result.audit_event,
    )


@router.get("/grants/{grant_id}", response_model=AiInviteGrantResponse)
def get_invite_grant(grant_id: str, request: Request) -> AiInviteGrantResponse:
    grant = default_invite_session_store.get_grant(grant_id)
    if grant is None:
        raise _not_found("Invite grant was not found or has expired.")
    log_ai_workflow("invite.grant.get", request, status="ok", warning_count=0)
    return AiInviteGrantResponse(
        grant=grant,
        invite_token=None,
        session_count=default_invite_session_store.count_sessions_for_grant(grant.grant_id),
        active_session_count=default_invite_session_store.count_active_sessions_for_grant(grant.grant_id),
        audit_event=None,
    )


@router.get("/sessions/{session_id}", response_model=AiInviteSessionResponse)
def get_invite_session(session_id: str, request: Request) -> AiInviteSessionResponse:
    session = default_invite_session_store.get_session(session_id)
    if session is None:
        raise _not_found("Invite session was not found or has expired.")
    grant = default_invite_session_store.get_grant(session.access_grant_id or "")
    if grant is None:
        raise _not_found("Invite grant was not found or has expired.")
    budget_snapshot = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        0,
        0,
        session,
        get_provider_budget_settings(),
    ).budget_snapshot
    log_ai_workflow("invite.session.get", request, status="ok", warning_count=0)
    return AiInviteSessionResponse(
        grant=grant,
        session=session,
        session_token=None,
        budget_snapshot=budget_snapshot,
        audit_event=None,
    )


@router.post("/grants/{grant_id}/revoke", response_model=AiInviteGrantResponse)
def revoke_invite_grant(grant_id: str, request: Request) -> AiInviteGrantResponse:
    _require_local_operator_access(request)
    grant = default_invite_session_store.revoke_grant(grant_id, reason="Local operator revoked the invite grant.")
    if grant is None:
        raise _not_found("Invite grant was not found or has expired.")
    log_ai_workflow("invite.grant.revoke", request, status="revoked", warning_count=0)
    return AiInviteGrantResponse(
        grant=grant,
        invite_token=None,
        session_count=default_invite_session_store.count_sessions_for_grant(grant.grant_id),
        active_session_count=default_invite_session_store.count_active_sessions_for_grant(grant.grant_id),
        audit_event=_audit_event("grant_revoked", "invite_grant", grant_id, "Local operator revoked the invite grant."),
    )


@router.post("/sessions/{session_id}/revoke", response_model=AiInviteSessionResponse)
def revoke_invite_session(session_id: str, request: Request) -> AiInviteSessionResponse:
    _require_local_operator_access(request)
    session = default_invite_session_store.revoke_session(session_id, reason="Local operator revoked the invite session.")
    if session is None:
        raise _not_found("Invite session was not found or has expired.")
    grant = default_invite_session_store.get_grant(session.access_grant_id or "")
    if grant is None:
        raise _not_found("Invite grant was not found or has expired.")
    budget_snapshot = check_provider_budget(
        AiAccessWorkflow.IMPORTER,
        "mock",
        "mock-basic",
        0,
        0,
        session,
        get_provider_budget_settings(),
    ).budget_snapshot
    log_ai_workflow("invite.session.revoke", request, status="revoked", warning_count=0)
    return AiInviteSessionResponse(
        grant=grant,
        session=session,
        session_token=None,
        budget_snapshot=budget_snapshot,
        audit_event=_audit_event("session_revoked", "invite_session", session_id, "Local operator revoked the invite session."),
    )


def require_demo_workflow_access(
    workflow: str | AiAccessWorkflow,
    request_headers: Mapping[str, str] | None,
    *,
    client_host: str | None = None,
    invite_settings: InviteSessionSettings | None = None,
) -> AiDemoSession | None:
    invite_settings = invite_settings or get_invite_session_settings()
    headers = request_headers or {}
    invite_token = _extract_invite_token(headers)
    if invite_settings.enabled and invite_token:
        session = default_invite_session_store.resolve_session_from_token(invite_token)
        if session is None:
            raise _invite_http_exception("Invite session token was not recognized.")
        workflow_key = _workflow_key(workflow)
        if workflow_key not in {item.value for item in session.allowed_workflows}:
            raise _invite_http_exception("Invite session is not allowed to access this workflow.")
        return session
    if invite_settings.enabled and invite_token is not None and not invite_token.strip():
        raise _invite_http_exception("Invite session token is required.")
    decision = check_operator_gate(
        workflow,
        request_headers,
        get_operator_gate_settings(),
        client_host=client_host,
    )
    if not decision.allowed:
        raise operator_gate_http_exception(decision)
    return None


def _require_local_operator_access(request: Request) -> None:
    decision = check_operator_gate(
        AiAccessWorkflow.IMPORTER,
        request.headers,
        get_operator_gate_settings(),
        client_host=request.client.host if request.client else None,
    )
    log_ai_workflow("operator.gate", request, status=decision.status.value, warning_count=0)
    if not decision.allowed:
        raise operator_gate_http_exception(decision)


def _invite_http_exception(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail={"response_state": "blocked", "message": message})


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail={"response_state": "not_found", "message": message})


def _extract_invite_token(headers: Mapping[str, str]) -> str | None:
    normalized_headers = {str(key).lower(): value for key, value in headers.items()}
    header_value = normalized_headers.get(INVITE_TOKEN_HEADER)
    if header_value and header_value.strip():
        return header_value.strip()
    auth_value = normalized_headers.get(AUTHORIZATION_HEADER)
    if not auth_value or not auth_value.strip():
        return None
    stripped = auth_value.strip()
    if stripped.lower().startswith("bearer "):
        token = stripped[7:].strip()
        if token:
            return token
    return None


def _actor_label(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "local-operator"


def _workflow_key(workflow: str | AiAccessWorkflow) -> str:
    return workflow.value if isinstance(workflow, AiAccessWorkflow) else str(workflow).strip().lower()


def _normalize_token(token: str | None) -> str:
    return token.strip() if token and token.strip() else ""


def _generate_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def _fingerprint_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _metadata_fingerprint(grant_id: str, token_fingerprint: str, workflows: list[AiAccessWorkflow], value: int | str | None) -> str:
    payload = {
        "grant_id": grant_id,
        "token_fingerprint": token_fingerprint[:12],
        "workflows": [workflow.value for workflow in workflows],
        "value": value,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _parse_allowed_workflows(values: list[str]) -> list[AiAccessWorkflow]:
    workflows: list[AiAccessWorkflow] = []
    for value in values:
        try:
            workflow = AiAccessWorkflow(value.strip().lower())
        except ValueError:
            continue
        if workflow not in workflows:
            workflows.append(workflow)
    return workflows


def _audit_event(action: str, target_type: str, target_id: str, reason: str) -> AiAdminAuditEvent:
    return AiAdminAuditEvent(
        event_id=f"ga_{uuid4().hex[:12]}",
        actor_label="local-operator",
        action=AiAdminAuditAction(action),
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        safe_metadata={"target_id_hint": hashlib.sha256(target_id.encode("utf-8")).hexdigest()[:12]},
    )
