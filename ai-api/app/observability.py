import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response

LOGGER_NAME = "app.observability"
logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> None:
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logger.setLevel(logging.INFO)


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _request_id(request.headers.get("x-request-id"))
    request.state.request_id = request_id
    started = time.perf_counter()
    status_code = 500
    error_type: str | None = None

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as exc:
        error_type = exc.__class__.__name__
        raise
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        log_event(
            "ai.request",
            request_id=request_id,
            endpoint_name=_endpoint_name(request),
            ui_workflow=_safe_header(request.headers.get("x-ai-demo-workflow")),
            status=status_code,
            duration_ms=duration_ms,
            safe_error_type=error_type,
        )


def log_ai_workflow(
    workflow: str,
    request: Request | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    status: str = "ok",
    retrieved_count: int | None = None,
    citation_count: int | None = None,
    warning_count: int | None = None,
    safe_error_type: str | None = None,
    provider_error_category: str | None = None,
    provider_error_type: str | None = None,
    safe_error_summary: str | None = None,
) -> None:
    log_event(
        "ai.workflow",
        request_id=get_request_id(request),
        endpoint_name=workflow,
        provider=provider,
        model=model,
        status=status,
        retrieved_count=retrieved_count,
        citation_count=citation_count,
        warning_count=warning_count,
        safe_error_type=safe_error_type,
        provider_error_category=provider_error_category,
        provider_error_type=provider_error_type,
        safe_error_summary=safe_error_summary,
    )


def get_request_id(request: Request | None) -> str | None:
    if request is None:
        return None
    return getattr(request.state, "request_id", None)


def log_event(event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
    }
    for key, value in fields.items():
        if value is not None:
            payload[key] = value
    logger.info(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _request_id(header_value: str | None) -> str:
    if header_value:
        safe = _safe_header(header_value)
        if safe:
            return safe[:64]
    return uuid.uuid4().hex


def _safe_header(header_value: str | None) -> str | None:
    if not header_value:
        return None
    safe = "".join(character for character in header_value if character.isalnum() or character in "-_")
    return safe[:64] or None


def _endpoint_name(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        return path
    return request.url.path
