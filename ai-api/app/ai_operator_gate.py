from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping
from dataclasses import dataclass

from fastapi import HTTPException

from app.ai_access_models import AiAccessWorkflow, AiOperatorGateDecision, AiOperatorGateStatus
from app.config import OperatorGateSettings, get_operator_gate_settings


OPERATOR_TOKEN_HEADER = "x-ai-operator-token"
AUTHORIZATION_HEADER = "authorization"

LOCAL_HOST_MARKERS = {
    "127.0.0.1",
    "::1",
    "localhost",
    "testclient",
}


@dataclass(frozen=True)
class OperatorToken:
    value: str
    source: str


def check_operator_gate(
    workflow: str | AiAccessWorkflow,
    request_headers: Mapping[str, str] | None = None,
    settings: OperatorGateSettings | None = None,
    *,
    client_host: str | None = None,
) -> AiOperatorGateDecision:
    settings = settings or get_operator_gate_settings()
    workflow_key = _workflow_key(workflow)
    workflow_model = _workflow_model(workflow_key)
    client_kind = _client_kind(client_host)
    metadata_fingerprint = _decision_fingerprint(settings, workflow_key, client_kind)

    if not settings.enabled:
        return AiOperatorGateDecision(
            enabled=False,
            allowed=True,
            workflow=workflow_model,
            reason="Operator gate is disabled.",
            status=AiOperatorGateStatus.DISABLED,
            grant_type="disabled",
            metadata_fingerprint=metadata_fingerprint,
            safe_message="Operator gate is disabled for this request.",
            safe_metadata={"client_host_kind": client_kind},
        )

    if workflow_key not in settings.allowed_workflows:
        return AiOperatorGateDecision(
            enabled=True,
            allowed=False,
            workflow=workflow_model,
            reason=f"Workflow '{workflow_key}' is not enabled by the operator gate.",
            status=AiOperatorGateStatus.BLOCKED,
            grant_type="workflow_not_allowed",
            metadata_fingerprint=metadata_fingerprint,
            safe_message="This workflow is not enabled by the local operator gate.",
            safe_metadata={"client_host_kind": client_kind},
        )

    token = _extract_operator_token(request_headers or {})
    if token is None and settings.local_bypass and _is_local_client(client_kind):
        return AiOperatorGateDecision(
            enabled=True,
            allowed=True,
            workflow=workflow_model,
            reason="Local bypass allowed this local request.",
            status=AiOperatorGateStatus.ALLOWED,
            grant_type="local_bypass",
            metadata_fingerprint=metadata_fingerprint,
            safe_message="Local operator bypass allowed this request.",
            safe_metadata={"client_host_kind": client_kind, "token_source": "local_bypass"},
        )

    if not settings.token_fingerprint:
        return AiOperatorGateDecision(
            enabled=True,
            allowed=False,
            workflow=workflow_model,
            reason="Operator gate is enabled but no token fingerprint is configured.",
            status=AiOperatorGateStatus.MISCONFIGURED,
            grant_type="misconfigured",
            metadata_fingerprint=metadata_fingerprint,
            safe_message="Operator gate is enabled, but it is not configured yet.",
            safe_metadata={"client_host_kind": client_kind},
        )

    if token is None:
        return AiOperatorGateDecision(
            enabled=True,
            allowed=False,
            workflow=workflow_model,
            reason="Operator token is required for this workflow.",
            status=AiOperatorGateStatus.BLOCKED,
            grant_type="token_required",
            metadata_fingerprint=metadata_fingerprint,
            safe_message="Operator token is required for this workflow.",
            safe_metadata={"client_host_kind": client_kind},
        )

    provided_fingerprint = fingerprint_operator_token(token.value)
    if hmac.compare_digest(provided_fingerprint, settings.token_fingerprint):
        return AiOperatorGateDecision(
            enabled=True,
            allowed=True,
            workflow=workflow_model,
            reason=f"Operator token matched via {token.source}.",
            status=AiOperatorGateStatus.ALLOWED,
            grant_type=token.source,
            metadata_fingerprint=_decision_fingerprint(
                settings,
                workflow_key,
                client_kind,
                token_source=token.source,
                token_fingerprint=provided_fingerprint,
            ),
            safe_message="Operator token was accepted.",
            safe_metadata={"client_host_kind": client_kind, "token_source": token.source},
        )

    return AiOperatorGateDecision(
        enabled=True,
        allowed=False,
        workflow=workflow_model,
        reason=f"Operator token fingerprint did not match for {token.source}.",
        status=AiOperatorGateStatus.BLOCKED,
        grant_type=token.source,
        metadata_fingerprint=_decision_fingerprint(
            settings,
            workflow_key,
            client_kind,
            token_source=token.source,
            token_fingerprint=provided_fingerprint,
        ),
        safe_message="Operator token was rejected.",
        safe_metadata={"client_host_kind": client_kind, "token_source": token.source},
    )


def require_operator_gate(
    workflow: str | AiAccessWorkflow,
    request_headers: Mapping[str, str] | None = None,
    settings: OperatorGateSettings | None = None,
    *,
    client_host: str | None = None,
) -> AiOperatorGateDecision:
    decision = check_operator_gate(
        workflow,
        request_headers=request_headers,
        settings=settings,
        client_host=client_host,
    )
    if decision.allowed:
        return decision
    raise operator_gate_http_exception(decision)


def operator_gate_http_exception(decision: AiOperatorGateDecision) -> HTTPException:
    status_code = 503 if decision.status == AiOperatorGateStatus.MISCONFIGURED else 403
    return HTTPException(status_code=status_code, detail=decision.safe_view())


def fingerprint_operator_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _workflow_key(workflow: str | AiAccessWorkflow) -> str:
    if isinstance(workflow, AiAccessWorkflow):
        return workflow.value
    return str(workflow).strip().lower()


def _workflow_model(workflow: str) -> AiAccessWorkflow:
    try:
        return AiAccessWorkflow(workflow)
    except ValueError:
        # This should not happen for the protected routes in this repo; keep the
        # failure explicit and safe if a new workflow is miswired.
        return AiAccessWorkflow.IMPORTER


def _client_kind(client_host: str | None) -> str:
    if not client_host:
        return "unknown"
    return client_host.strip().lower()


def _is_local_client(client_kind: str) -> bool:
    return client_kind in LOCAL_HOST_MARKERS


def _extract_operator_token(headers: Mapping[str, str]) -> OperatorToken | None:
    normalized_headers = {str(key).lower(): value for key, value in headers.items()}
    header_value = normalized_headers.get(OPERATOR_TOKEN_HEADER)
    if header_value and header_value.strip():
        return OperatorToken(value=header_value.strip(), source="x-ai-operator-token")

    auth_value = normalized_headers.get(AUTHORIZATION_HEADER)
    if not auth_value or not auth_value.strip():
        return None

    stripped = auth_value.strip()
    if stripped.lower().startswith("bearer "):
        token = stripped[7:].strip()
        if token:
            return OperatorToken(value=token, source="authorization-bearer")
    return None


def _decision_fingerprint(
    settings: OperatorGateSettings,
    workflow_key: str,
    client_kind: str,
    *,
    token_source: str | None = None,
    token_fingerprint: str | None = None,
) -> str:
    payload = {
        "enabled": settings.enabled,
        "allowed_workflows": list(settings.allowed_workflows),
        "local_bypass": settings.local_bypass,
        "workflow": workflow_key,
        "client_host_kind": client_kind,
        "token_source": token_source,
        "token_fingerprint": token_fingerprint[:12] if token_fingerprint else None,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
