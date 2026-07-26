"""Local-only transport to the core-owned Cookbook verification boundary.

This client is intentionally not wired to the normal product UI.  It sends a
reviewed candidate only when every explicit local gate is enabled and only to
the loopback dev fixture route.  It never owns or forwards identity, session,
cookie, token, provider, or storage-grant values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.error import URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from app.cookbook_import_adapter import (
    CONTRACT_VERSION,
    RECIPE_SCHEMA_VERSION,
    CookbookImportDryRunResult,
    map_import_draft_to_candidate,
)

LOCAL_IMAGE = "local/vanilla-cookbook-adapter:0034f"
LOCAL_ROUTE = "/api/adapter/dev-only/recipes/import-candidate/verify-local-commit"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
FORBIDDEN_KEYS = frozenset(
    {
        "userId",
        "user_id",
        "owner",
        "session",
        "cookie",
        "token",
        "auth",
        "oauth_code",
        "provider_token",
        "storage_grant",
    }
)
SAFE_RESPONSE_KEYS = frozenset(
    {
        "status",
        "verification",
        "recipe_uid",
        "recipe_url",
        "commit_status",
        "read_after_write",
        "replay_status",
        "conflict_status",
        "duplicate_status",
        "rollback_status",
        "content_scope",
        "code",
        "next_action",
        "reasons",
    }
)


@dataclass(frozen=True)
class CoreTransportSettings:
    enabled: bool = False
    approved: bool = False
    runtime_verified: bool = False
    target_url: str = "http://127.0.0.1:3000/"
    image_marker: str = ""
    compose_project: str = "cookbook-local"


def _target_is_loopback(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "http"
        and parsed.hostname in LOOPBACK_HOSTS
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and port in (None, 3000)
    )


def local_core_transport_guard(
    settings: CoreTransportSettings,
    *,
    env: Mapping[str, str] | None = None,
) -> list[str]:
    environment = env or {}
    reasons: list[str] = []
    if not settings.enabled:
        reasons.append("disabled")
    if not settings.approved:
        reasons.append("approval_required")
    if not settings.runtime_verified:
        reasons.append("runtime_verification_required")
    if settings.compose_project != "cookbook-local":
        reasons.append("cookbook_local_project_required")
    if settings.image_marker != LOCAL_IMAGE:
        reasons.append("approved_local_image_required")
    if not _target_is_loopback(settings.target_url):
        reasons.append("loopback_target_required")
    if environment.get("NODE_ENV", "").lower() == "production":
        reasons.append("production_mode")
    if any(environment.get(name) for name in ("CI", "GITHUB_ACTIONS", "AWS_REGION", "CLOUDFLARE_TUNNEL_TOKEN", "TUNNEL_TOKEN")):
        reasons.append("deployment_or_ci_context")
    return reasons


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(key in FORBIDDEN_KEYS or _contains_forbidden_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _ingredient_line(item: Mapping[str, Any]) -> str:
    parts = [str(item.get(key) or "").strip() for key in ("quantity", "unit", "name")]
    line = " ".join(part for part in parts if part)
    note = str(item.get("note") or "").strip()
    return f"{line} ({note})" if note else line


def _core_candidate(draft: Mapping[str, Any], result: CookbookImportDryRunResult) -> dict[str, Any] | None:
    candidate = result.candidate
    if candidate is None:
        return None
    payload = candidate.payload
    source = payload.source or ""
    source_url = source if urlsplit(source).scheme in {"http", "https"} else None
    return {
        "title": payload.title,
        "description": payload.description,
        "servings": payload.servings,
        "ingredients": [_ingredient_line(item.model_dump()) for item in payload.ingredients],
        "instructions": [item.text for item in payload.instructions],
        "source": None if source_url else source,
        "source_url": source_url,
        "notes": payload.notes,
        "idempotency_key": candidate.idempotency_key,
        "contract_version": "cookbook-import-candidate.v1",
        "schema_version": "recipe.v1",
    }


def _safe_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"status": "unavailable", "code": "invalid_core_response"}
    return {key: value[key] for key in SAFE_RESPONSE_KEYS if key in value and key not in FORBIDDEN_KEYS}


def send_core_local_commit(
    draft: Mapping[str, Any],
    *,
    idempotency_key: str | None = None,
    approved: bool = False,
    settings: CoreTransportSettings | None = None,
    env: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    """Send one reviewed candidate to the local core fixture, never elsewhere."""

    effective = settings or CoreTransportSettings()
    reasons = local_core_transport_guard(effective, env=env)
    if reasons:
        return {"status": "unavailable", "code": "local_transport_blocked", "reasons": reasons}
    if approved is not True:
        return {"status": "unavailable", "code": "explicit_confirmation_required"}
    if not isinstance(draft, Mapping) or _contains_forbidden_key(draft):
        return {"status": "invalid", "code": "identity_assertion_rejected"}

    result = map_import_draft_to_candidate(draft, idempotency_key=idempotency_key)
    if result.status not in {"valid", "idempotent_replay"}:
        return {
            "status": "invalid",
            "code": "candidate_validation_failed",
            "field_errors": [error.model_dump() for error in result.errors],
            "warnings": result.warnings,
        }
    candidate = _core_candidate(draft, result)
    if candidate is None:
        return {"status": "invalid", "code": "candidate_mapping_failed"}

    body = json.dumps({"candidate": candidate, "approve_local_write": True}, separators=(",", ":")).encode("utf-8")
    target = urlsplit(effective.target_url)
    endpoint = urlunsplit((target.scheme, target.netloc, LOCAL_ROUTE, "", ""))
    request = Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with opener(request, timeout=60) as response:
            raw = response.read()
        parsed = json.loads(raw.decode("utf-8"))
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return {"status": "unavailable", "code": "core_transport_unavailable"}
    safe = _safe_result(parsed)
    return safe or {"status": "unavailable", "code": "invalid_core_response"}


__all__ = [
    "CoreTransportSettings",
    "LOCAL_IMAGE",
    "LOCAL_ROUTE",
    "local_core_transport_guard",
    "send_core_local_commit",
]
