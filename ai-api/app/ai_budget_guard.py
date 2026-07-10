from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.ai_access_models import (
    AiAccessWorkflow,
    AiBudgetSnapshot,
    AiProviderBudgetDecision,
    AiProviderBudgetStatus,
    AiProviderMeterEvent,
    AiProviderMeterStatus,
)
from app.config import ProviderBudgetSettings, get_provider_budget_settings


DEFAULT_TRACKER_MAX_SESSIONS = 128
DEFAULT_COST_PER_100K_TOKENS_USD = Decimal("1.00")


@dataclass(frozen=True)
class _TrackerEntry:
    provider_call_count: int = 0
    estimated_cost_usd: Decimal = Decimal("0.00")
    updated_at: float = field(default_factory=time.monotonic)


class AiProviderBudgetTracker:
    """Small process-local budget tracker for local demo and test flows only."""

    def __init__(self, *, max_sessions: int = DEFAULT_TRACKER_MAX_SESSIONS) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1")
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, _TrackerEntry] = OrderedDict()
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._sessions.clear()

    def record_allowed_call(self, session_key: str, meter_event: AiProviderMeterEvent) -> None:
        with self._lock:
            current = self._sessions.get(session_key)
            provider_call_count = (current.provider_call_count if current else 0) + 1
            estimated_cost_usd = (current.estimated_cost_usd if current else Decimal("0.00")) + _safe_decimal(
                meter_event.estimated_cost_usd
            )
            self._sessions[session_key] = _TrackerEntry(
                provider_call_count=provider_call_count,
                estimated_cost_usd=estimated_cost_usd,
                updated_at=time.monotonic(),
            )
            self._sessions.move_to_end(session_key)
            self._evict_if_needed()

    def record_blocked_call(self, session_key: str, meter_event: AiProviderMeterEvent) -> None:
        del meter_event
        with self._lock:
            if session_key in self._sessions:
                current = self._sessions[session_key]
                self._sessions[session_key] = _TrackerEntry(
                    provider_call_count=current.provider_call_count,
                    estimated_cost_usd=current.estimated_cost_usd,
                    updated_at=time.monotonic(),
                )
                self._sessions.move_to_end(session_key)
            else:
                self._sessions[session_key] = _TrackerEntry(updated_at=time.monotonic())
                self._sessions.move_to_end(session_key)
                self._evict_if_needed()

    def snapshot(
        self,
        session_key: str,
        *,
        grant_id: str | None = None,
        max_provider_calls: int | None = None,
        max_estimated_cost_usd: Decimal | None = None,
    ) -> AiBudgetSnapshot:
        with self._lock:
            entry = self._sessions.get(session_key)
            provider_call_count = entry.provider_call_count if entry else 0
            estimated_cost_usd = entry.estimated_cost_usd if entry else Decimal("0.00")
        return AiBudgetSnapshot(
            session_id=session_key,
            grant_id=grant_id,
            provider_call_count=provider_call_count,
            max_provider_calls=max_provider_calls,
            estimated_cost_usd=estimated_cost_usd,
            max_estimated_cost_usd=max_estimated_cost_usd,
        )

    def _evict_if_needed(self) -> None:
        while len(self._sessions) > self.max_sessions:
            self._sessions.popitem(last=False)


default_provider_budget_tracker = AiProviderBudgetTracker()


def check_provider_budget(
    workflow: AiAccessWorkflow,
    provider: str,
    model: str | None,
    estimated_input_tokens: int | None,
    requested_output_tokens: int | None,
    session_state: Any | None,
    settings: ProviderBudgetSettings | None = None,
    *,
    tracker: AiProviderBudgetTracker | None = None,
) -> AiProviderBudgetDecision:
    active_settings = settings or get_provider_budget_settings()
    active_tracker = tracker or default_provider_budget_tracker
    provider_name = (provider or "").strip().lower() or "unknown"
    model_name = model.strip() if isinstance(model, str) and model.strip() else None
    session_key = _session_key(session_state, provider_name, workflow)
    effective_max_provider_calls = _session_limit_int(
        session_state,
        "max_provider_calls",
        default=active_settings.max_calls_per_demo_session,
    )
    effective_max_estimated_cost_usd = _session_limit_decimal(
        session_state,
        "max_estimated_cost_usd",
        default=active_settings.max_estimated_cost_usd_per_session,
    )
    estimated_input_tokens = max(0, int(estimated_input_tokens or 0))
    requested_output_tokens = max(0, int(requested_output_tokens or 0))
    call_estimated_cost = _estimate_cost_usd(estimated_input_tokens, requested_output_tokens)

    if provider_name != "openai":
        snapshot = active_tracker.snapshot(
            session_key,
            grant_id=_grant_id(session_state),
            max_provider_calls=effective_max_provider_calls,
            max_estimated_cost_usd=effective_max_estimated_cost_usd,
        )
        event = _build_meter_event(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            status=AiProviderMeterStatus.SKIPPED,
            reason="Mock or local provider call treated as zero-cost.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=Decimal("0.00"),
            safe_metadata=_safe_budget_metadata(active_settings, provider_name, session_key, "skipped"),
        )
        return AiProviderBudgetDecision(
            allowed=True,
            status=AiProviderBudgetStatus.SKIPPED,
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            reason="Mock or local provider call treated as zero-cost.",
            safe_message="Mock provider call treated as zero-cost and allowed.",
            provider_call_count=snapshot.provider_call_count,
            max_provider_calls=effective_max_provider_calls,
            estimated_cost_usd=snapshot.estimated_cost_usd,
            max_estimated_cost_usd=effective_max_estimated_cost_usd,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=requested_output_tokens,
            max_input_tokens=active_settings.max_input_tokens_per_call,
            max_output_tokens=active_settings.max_output_tokens_per_call,
            budget_snapshot=snapshot,
            meter_event=event,
            safe_metadata=_safe_budget_metadata(active_settings, provider_name, session_key, "skipped"),
        )

    if active_settings.validation_errors:
        snapshot = active_tracker.snapshot(
            session_key,
            grant_id=_grant_id(session_state),
            max_provider_calls=effective_max_provider_calls,
            max_estimated_cost_usd=effective_max_estimated_cost_usd,
        )
        event = _build_meter_event(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            status=AiProviderMeterStatus.FAILED,
            reason="Provider budget configuration is invalid or incomplete.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
            safe_metadata=_safe_budget_metadata(active_settings, provider_name, session_key, "misconfigured"),
        )
        active_tracker.record_blocked_call(session_key, event)
        return _decision(
            allowed=False,
            status=AiProviderBudgetStatus.MISCONFIGURED,
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            reason="Provider budget configuration is invalid or incomplete.",
            safe_message="Provider budget configuration is invalid or incomplete.",
            snapshot=snapshot,
            event=event,
            settings=active_settings,
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
        )

    if not active_settings.calls_enabled or active_settings.global_disable:
        snapshot = active_tracker.snapshot(
            session_key,
            grant_id=_grant_id(session_state),
            max_provider_calls=effective_max_provider_calls,
            max_estimated_cost_usd=effective_max_estimated_cost_usd,
        )
        event = _build_meter_event(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            status=AiProviderMeterStatus.BLOCKED,
            reason="Provider calls are disabled for this local demo.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
            safe_metadata=_safe_budget_metadata(active_settings, provider_name, session_key, "disabled"),
        )
        active_tracker.record_blocked_call(session_key, event)
        return _decision(
            allowed=False,
            status=AiProviderBudgetStatus.DISABLED,
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            reason="Provider calls are disabled for this local demo.",
            safe_message="Provider calls are disabled for this local demo.",
            snapshot=snapshot,
            event=event,
            settings=active_settings,
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
        )

    if estimated_input_tokens > active_settings.max_input_tokens_per_call:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.BLOCKED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Estimated input tokens exceed the configured demo cap.",
            safe_message="Estimated input token limit exceeds the configured demo cap.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
        )

    if requested_output_tokens > active_settings.max_output_tokens_per_call:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.BLOCKED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Requested output tokens exceed the configured demo cap.",
            safe_message="Requested output token limit exceeds the configured demo cap.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
        )

    total_tokens = estimated_input_tokens + requested_output_tokens
    if total_tokens > active_settings.max_total_tokens_per_call:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.BLOCKED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Estimated total tokens exceed the configured demo cap.",
            safe_message="Estimated total token limit exceeds the configured demo cap.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
        )

    current_snapshot = active_tracker.snapshot(
        session_key,
        grant_id=_grant_id(session_state),
        max_provider_calls=effective_max_provider_calls,
        max_estimated_cost_usd=effective_max_estimated_cost_usd,
    )
    next_call_count = current_snapshot.provider_call_count + 1
    next_estimated_cost = current_snapshot.estimated_cost_usd + call_estimated_cost

    if next_call_count > effective_max_provider_calls:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.EXHAUSTED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Provider call budget exhausted for this demo session.",
            safe_message="Provider call budget exhausted for this demo session.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
            current_snapshot=current_snapshot,
        )

    if call_estimated_cost > active_settings.max_estimated_cost_usd_per_call:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.BLOCKED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Estimated provider cost exceeds the configured demo budget.",
            safe_message="Estimated provider cost exceeds the configured demo budget.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
            current_snapshot=current_snapshot,
        )

    if next_estimated_cost > effective_max_estimated_cost_usd:
        return _blocked_decision(
            workflow=workflow,
            provider=provider_name,
            model=model_name,
            session_key=session_key,
            settings=active_settings,
            tracker=active_tracker,
            status=AiProviderBudgetStatus.EXHAUSTED,
            meter_status=AiProviderMeterStatus.BLOCKED,
            reason="Estimated provider cost exceeds the configured demo budget for this session.",
            safe_message="Estimated provider cost exceeds the configured demo budget for this session.",
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_cost_usd=call_estimated_cost,
            current_snapshot=current_snapshot,
        )

    snapshot = AiBudgetSnapshot(
        session_id=session_key,
        grant_id=_grant_id(session_state),
        provider_call_count=next_call_count,
        max_provider_calls=effective_max_provider_calls,
        estimated_cost_usd=next_estimated_cost,
        max_estimated_cost_usd=effective_max_estimated_cost_usd,
    )
    event = _build_meter_event(
        workflow=workflow,
        provider=provider_name,
        model=model_name,
        session_key=session_key,
        status=AiProviderMeterStatus.ALLOWED,
        reason="Provider call allowed within budget.",
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        estimated_cost_usd=call_estimated_cost,
        safe_metadata=_safe_budget_metadata(active_settings, provider_name, session_key, "allowed"),
    )
    active_tracker.record_allowed_call(session_key, event)
    return _decision(
        allowed=True,
        status=AiProviderBudgetStatus.ALLOWED,
        workflow=workflow,
        provider=provider_name,
        model=model_name,
        reason="Provider call allowed within budget.",
        safe_message="Provider call allowed within budget.",
        snapshot=snapshot,
        event=event,
        settings=active_settings,
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        estimated_cost_usd=call_estimated_cost,
    )


def reset_provider_budget_tracker() -> None:
    default_provider_budget_tracker.reset()


def _blocked_decision(
    *,
    workflow: AiAccessWorkflow,
    provider: str,
    model: str | None,
    session_key: str,
    settings: ProviderBudgetSettings,
    tracker: AiProviderBudgetTracker,
    status: AiProviderBudgetStatus,
    meter_status: AiProviderMeterStatus,
    reason: str,
    safe_message: str,
    estimated_input_tokens: int,
    requested_output_tokens: int,
    estimated_cost_usd: Decimal,
    current_snapshot: AiBudgetSnapshot | None = None,
) -> AiProviderBudgetDecision:
    snapshot = current_snapshot or tracker.snapshot(
        session_key,
        grant_id=None,
        max_provider_calls=settings.max_calls_per_demo_session,
        max_estimated_cost_usd=settings.max_estimated_cost_usd_per_session,
    )
    event = _build_meter_event(
        workflow=workflow,
        provider=provider,
        model=model,
        session_key=session_key,
        status=meter_status,
        reason=reason,
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        safe_metadata=_safe_budget_metadata(settings, provider, session_key, status.value),
    )
    tracker.record_blocked_call(session_key, event)
    return _decision(
        allowed=False,
        status=status,
        workflow=workflow,
        provider=provider,
        model=model,
        reason=reason,
        safe_message=safe_message,
        snapshot=snapshot,
        event=event,
        settings=settings,
        estimated_input_tokens=estimated_input_tokens,
        requested_output_tokens=requested_output_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )


def _decision(
    *,
    allowed: bool,
    status: AiProviderBudgetStatus,
    workflow: AiAccessWorkflow,
    provider: str,
    model: str | None,
    reason: str,
    safe_message: str,
    snapshot: AiBudgetSnapshot,
    event: AiProviderMeterEvent,
    settings: ProviderBudgetSettings,
    estimated_input_tokens: int,
    requested_output_tokens: int,
    estimated_cost_usd: Decimal,
) -> AiProviderBudgetDecision:
    return AiProviderBudgetDecision(
        allowed=allowed,
        status=status,
        workflow=workflow,
        provider=provider,
        model=model,
        reason=reason,
        safe_message=safe_message,
        provider_call_count=snapshot.provider_call_count,
        max_provider_calls=snapshot.max_provider_calls,
        estimated_cost_usd=estimated_cost_usd,
        max_estimated_cost_usd=snapshot.max_estimated_cost_usd,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=requested_output_tokens,
        max_input_tokens=settings.max_input_tokens_per_call,
        max_output_tokens=settings.max_output_tokens_per_call,
        budget_snapshot=snapshot,
        meter_event=event,
        safe_metadata=_safe_budget_metadata(settings, provider, snapshot.session_id or "local-demo", status.value),
    )


def _build_meter_event(
    *,
    workflow: AiAccessWorkflow,
    provider: str,
    model: str | None,
    session_key: str,
    status: AiProviderMeterStatus,
    reason: str,
    estimated_input_tokens: int,
    requested_output_tokens: int,
    estimated_cost_usd: Decimal,
    safe_metadata: dict[str, str | int | float | bool | None],
) -> AiProviderMeterEvent:
    total_tokens = estimated_input_tokens + requested_output_tokens
    return AiProviderMeterEvent(
        event_id=_fingerprint(
            "|".join(
                [
                    session_key,
                    workflow.value,
                    provider,
                    model or "",
                    status.value,
                    str(estimated_input_tokens),
                    str(requested_output_tokens),
                    str(estimated_cost_usd),
                ]
            )
        ),
        session_id=session_key,
        workflow=workflow,
        provider=provider,
        model=model,
        input_tokens=estimated_input_tokens,
        output_tokens=requested_output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        status=status,
        reason=reason,
        request_id=None,
        safe_metadata=safe_metadata,
    )


def _safe_budget_metadata(
    settings: ProviderBudgetSettings,
    provider: str,
    session_key: str,
    status: str,
) -> dict[str, str | int | float | bool | None]:
    return {
        "provider": provider,
        "budget_mode": settings.budget_mode,
        "calls_enabled": settings.calls_enabled,
        "global_disable": settings.global_disable,
        "budget_status": status,
        "session_key_hint": _fingerprint(session_key)[:12],
    }


def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> Decimal:
    total_tokens = max(0, input_tokens) + max(0, output_tokens)
    return (Decimal(total_tokens) / Decimal("100000")) * DEFAULT_COST_PER_100K_TOKENS_USD


def _session_key(session_state: Any | None, provider: str, workflow: AiAccessWorkflow) -> str:
    if session_state is not None:
        for attribute in ("interaction_id", "session_id", "grant_id"):
            value = getattr(session_state, attribute, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
    env_key = os.getenv("AI_PROVIDER_BUDGET_SESSION_ID")
    if env_key and env_key.strip():
        return env_key.strip()
    return f"{provider}:{workflow.value}"


def _grant_id(session_state: Any | None) -> str | None:
    if session_state is None:
        return None
    for attribute in ("grant_id", "access_grant_id"):
        value = getattr(session_state, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _session_limit_int(session_state: Any | None, attribute: str, *, default: int) -> int:
    if session_state is not None:
        value = getattr(session_state, attribute, None)
        if isinstance(value, int):
            return max(0, value)
    return default


def _session_limit_decimal(session_state: Any | None, attribute: str, *, default: Decimal) -> Decimal:
    if session_state is not None:
        value = getattr(session_state, attribute, None)
        if isinstance(value, Decimal):
            return max(Decimal("0.00"), value)
        if isinstance(value, (int, float, str)) and str(value).strip():
            try:
                return max(Decimal("0.00"), Decimal(str(value)))
            except Exception:
                pass
    return default


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_decimal(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return value
