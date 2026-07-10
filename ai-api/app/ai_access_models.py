from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AiDemoSessionType(StrEnum):
    LOCAL_OPERATOR = "local_operator"
    INVITE = "invite"
    PUBLIC_PREVIEW = "public_preview"


class AiDemoSessionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPLETED = "completed"


class AiAccessGrantType(StrEnum):
    LOCAL_OPERATOR = "local_operator"
    INVITE_CODE = "invite_code"
    ADMIN_OVERRIDE = "admin_override"


class AiAccessGrantStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    USED = "used"


class AiProviderMeterStatus(StrEnum):
    ALLOWED = "allowed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    FAILED = "failed"


class AiProviderBudgetStatus(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    EXHAUSTED = "exhausted"
    MISCONFIGURED = "misconfigured"
    SKIPPED = "skipped"


class AiQualityStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class AiAdminAuditAction(StrEnum):
    GRANT_CREATED = "grant_created"
    GRANT_REVOKED = "grant_revoked"
    SESSION_REVOKED = "session_revoked"
    PROVIDER_DISABLED = "provider_disabled"
    BUDGET_LIMIT_CHANGED = "budget_limit_changed"
    LIVE_ACCESS_ENABLED = "live_access_enabled"
    LIVE_ACCESS_DISABLED = "live_access_disabled"


class AiAccessWorkflow(StrEnum):
    IMPORTER = "importer"
    DATASET_ASK = "dataset_ask"
    RECIPE_SESSION = "recipe_session"
    ASK_MY_COOKBOOK = "ask_my_cookbook"
    MEAL_PLAN = "meal_plan"


class AiOperatorGateStatus(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    DISABLED = "disabled"
    MISCONFIGURED = "misconfigured"


SAFE_METADATA_VALUE = str | int | float | bool | None
SAFE_METADATA = dict[str, SAFE_METADATA_VALUE]

FORBIDDEN_SAFE_VALUE_MARKERS = (
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


def utc_now() -> datetime:
    return datetime.now(UTC)


def safe_operator_view(model: BaseModel) -> dict[str, Any]:
    """Return the model's safe operator view through a uniform helper."""

    if hasattr(model, "safe_view"):
        view = model.safe_view()
        if isinstance(view, dict):
            return view
    return model.model_dump(mode="json")


class SafeAccessModel(BaseModel):
    @field_validator("safe_metadata", mode="before", check_fields=False)
    @classmethod
    def _validate_safe_metadata(cls, value: object) -> SAFE_METADATA:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("safe_metadata must be a dictionary")
        safe: SAFE_METADATA = {}
        for key, item in value.items():
            key_text = str(key)
            _raise_if_forbidden(key_text)
            if isinstance(item, Decimal):
                item = float(item)
            if item is not None and not isinstance(item, (str, int, float, bool)):
                raise ValueError("safe_metadata values must be scalar")
            if isinstance(item, str):
                _raise_if_forbidden(item)
            safe[key_text] = item
        return safe


class AiDemoSession(SafeAccessModel):
    session_id: str
    session_type: AiDemoSessionType = AiDemoSessionType.LOCAL_OPERATOR
    status: AiDemoSessionStatus = AiDemoSessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    operator_label: str | None = None
    access_grant_id: str | None = None
    request_count: int = Field(default=0, ge=0)
    provider_call_count: int = Field(default=0, ge=0)
    estimated_cost_usd: Decimal = Field(default=Decimal("0.00"), ge=0)
    last_activity_at: datetime | None = None
    metadata_fingerprint: str | None = None

    @field_validator("session_id", "operator_label", "access_grant_id", "revoked_reason", "metadata_fingerprint")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiAccessGrant(SafeAccessModel):
    grant_id: str
    grant_type: AiAccessGrantType = AiAccessGrantType.LOCAL_OPERATOR
    status: AiAccessGrantStatus = AiAccessGrantStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    max_sessions: int = Field(default=1, ge=0)
    max_provider_calls: int | None = Field(default=None, ge=0)
    max_estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    allowed_workflows: list[AiAccessWorkflow] = Field(default_factory=list)
    notes: str | None = None
    metadata_fingerprint: str | None = None

    @field_validator("grant_id", "revoked_reason", "notes", "metadata_fingerprint")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiProviderMeterEvent(SafeAccessModel):
    event_id: str
    session_id: str | None = None
    workflow: AiAccessWorkflow
    provider: str
    model: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    status: AiProviderMeterStatus = AiProviderMeterStatus.ALLOWED
    reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    request_id: str | None = None
    safe_metadata: SAFE_METADATA = Field(default_factory=dict)

    @model_validator(mode="after")
    def _fill_total_tokens(self) -> AiProviderMeterEvent:
        if self.total_tokens is None and self.input_tokens is not None and self.output_tokens is not None:
            self.total_tokens = self.input_tokens + self.output_tokens
        return self

    @field_validator("event_id", "session_id", "provider", "model", "reason", "request_id")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiQualityEvent(SafeAccessModel):
    event_id: str
    session_id: str | None = None
    workflow: AiAccessWorkflow
    eval_group: str | None = None
    case_id: str | None = None
    status: AiQualityStatus
    support_level: str | None = None
    retrieved_count: int | None = Field(default=None, ge=0)
    citation_count: int | None = Field(default=None, ge=0)
    warning_count: int | None = Field(default=None, ge=0)
    latency_ms: float | None = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    safe_summary: str | None = None

    @field_validator("event_id", "session_id", "eval_group", "case_id", "support_level", "safe_summary")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiAdminAuditEvent(SafeAccessModel):
    event_id: str
    actor_label: str
    action: AiAdminAuditAction
    target_type: str
    target_id: str
    created_at: datetime = Field(default_factory=utc_now)
    reason: str | None = None
    safe_metadata: SAFE_METADATA = Field(default_factory=dict)

    @field_validator("event_id", "actor_label", "target_type", "target_id", "reason")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiBudgetSnapshot(BaseModel):
    session_id: str | None = None
    grant_id: str | None = None
    provider_call_count: int = Field(default=0, ge=0)
    max_provider_calls: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    remaining_provider_calls: int | None = None
    remaining_estimated_cost_usd: Decimal | None = None
    is_exhausted: bool = False
    status_reason: str = "within_budget"
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _calculate_remaining_budget(self) -> AiBudgetSnapshot:
        if self.max_provider_calls is None:
            self.remaining_provider_calls = None
        else:
            self.remaining_provider_calls = max(0, self.max_provider_calls - self.provider_call_count)

        if self.max_estimated_cost_usd is None:
            self.remaining_estimated_cost_usd = None
        else:
            remaining_cost = self.max_estimated_cost_usd - self.estimated_cost_usd
            self.remaining_estimated_cost_usd = max(Decimal("0.00"), remaining_cost)

        call_exhausted = self.remaining_provider_calls == 0 if self.remaining_provider_calls is not None else False
        cost_exhausted = (
            self.remaining_estimated_cost_usd == Decimal("0.00")
            if self.remaining_estimated_cost_usd is not None
            else False
        )
        self.is_exhausted = call_exhausted or cost_exhausted
        if call_exhausted and cost_exhausted:
            self.status_reason = "provider_call_and_cost_limits_exhausted"
        elif call_exhausted:
            self.status_reason = "provider_call_limit_exhausted"
        elif cost_exhausted:
            self.status_reason = "cost_limit_exhausted"
        else:
            self.status_reason = "within_budget"
        return self

    @field_validator("session_id", "grant_id")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiOperatorGateDecision(SafeAccessModel):
    enabled: bool
    allowed: bool
    workflow: AiAccessWorkflow
    reason: str
    status: AiOperatorGateStatus
    grant_type: str | None = None
    metadata_fingerprint: str | None = None
    safe_message: str
    safe_metadata: SAFE_METADATA = Field(default_factory=dict)

    @field_validator("reason", "grant_type", "metadata_fingerprint", "safe_message")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class AiProviderBudgetDecision(SafeAccessModel):
    allowed: bool
    status: AiProviderBudgetStatus
    workflow: AiAccessWorkflow
    provider: str
    model: str | None = None
    reason: str
    safe_message: str
    provider_call_count: int = Field(default=0, ge=0)
    max_provider_calls: int | None = Field(default=None, ge=0)
    estimated_cost_usd: Decimal = Field(default=Decimal("0.00"), ge=0)
    max_estimated_cost_usd: Decimal | None = Field(default=None, ge=0)
    estimated_input_tokens: int | None = Field(default=None, ge=0)
    estimated_output_tokens: int | None = Field(default=None, ge=0)
    max_input_tokens: int | None = Field(default=None, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=0)
    budget_snapshot: AiBudgetSnapshot | None = None
    meter_event: AiProviderMeterEvent | None = None
    safe_metadata: SAFE_METADATA = Field(default_factory=dict)

    @field_validator("provider", "model", "reason", "safe_message")
    @classmethod
    def _safe_strings(cls, value: str | None) -> str | None:
        _raise_if_forbidden(value)
        return value

    def safe_view(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def _raise_if_forbidden(value: str | None) -> None:
    if value is None:
        return
    for marker in FORBIDDEN_SAFE_VALUE_MARKERS:
        if marker in value:
            raise ValueError("value contains forbidden private or secret-like text")
