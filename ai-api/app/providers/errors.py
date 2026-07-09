from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDebugDetails:
    category: str
    exception_type: str
    safe_summary: str


class ProviderError(RuntimeError):
    """Base error for provider harness failures."""


class ProviderConfigError(ProviderError):
    """Raised for invalid or incomplete provider configuration."""


class ProviderCallError(ProviderError):
    """Raised when a provider request fails."""

    def __init__(
        self,
        message: str,
        *,
        failure_category: str | None = None,
        exception_type: str | None = None,
        safe_summary: str | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_category = failure_category
        self.exception_type = exception_type
        self.safe_summary = safe_summary

    @property
    def debug_details(self) -> ProviderDebugDetails | None:
        if not self.failure_category or not self.exception_type or not self.safe_summary:
            return None
        return ProviderDebugDetails(
            category=self.failure_category,
            exception_type=self.exception_type,
            safe_summary=self.safe_summary,
        )


def build_provider_call_error(message: str, exc: BaseException) -> ProviderCallError:
    details = describe_provider_exception(exc)
    return ProviderCallError(
        message,
        failure_category=details.category,
        exception_type=details.exception_type,
        safe_summary=details.safe_summary,
    )


def extract_provider_debug_details(exc: BaseException) -> ProviderDebugDetails | None:
    for item in _exception_chain(exc):
        if isinstance(item, ProviderCallError) and item.debug_details is not None:
            return item.debug_details
    return None


def describe_provider_exception(exc: BaseException) -> ProviderDebugDetails:
    chain = _exception_chain(exc)
    exception_type = chain[0].__class__.__name__
    raw_summary = " | ".join(_exception_message(item) for item in chain if _exception_message(item))
    safe_summary = _sanitize_secret_like_text(raw_summary or exception_type)
    category = _classify_provider_failure(chain, safe_summary)
    return ProviderDebugDetails(
        category=category,
        exception_type=exception_type,
        safe_summary=_truncate(safe_summary or exception_type, limit=240),
    )


def _exception_chain(exc: BaseException) -> list[BaseException]:
    chain: list[BaseException] = []
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        chain.append(current)
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return chain


def _exception_message(exc: BaseException) -> str:
    return str(exc).strip()


def _classify_provider_failure(chain: list[BaseException], safe_summary: str) -> str:
    class_names = " ".join(item.__class__.__name__.lower() for item in chain)
    summary = safe_summary.lower()

    if any(
        token in class_names or token in summary
        for token in (
            "length",
            "incomplete",
            "truncated",
            "truncation",
            "max_output_tokens",
            "output tokens",
            "finish reason",
            "response incomplete",
        )
    ):
        return "output_cap_or_incomplete_response"
    if any(token in class_names or token in summary for token in ("timeout", "timed out", "deadline exceeded")):
        return "timeout"
    if any(
        token in class_names or token in summary
        for token in (
            "authentication",
            "permission",
            "unauthorized",
            "invalid api key",
            "incorrect api key",
            "401",
            "403",
            "forbidden",
        )
    ):
        return "auth"
    if any(
        token in class_names or token in summary
        for token in ("ratelimit", "rate limit", "quota", "insufficient_quota", "429", "billing")
    ):
        return "quota_or_rate_limit"
    if any(
        token in class_names or token in summary
        for token in (
            "badrequest",
            "invalid schema",
            "json schema",
            "response_format",
            "schema",
            "additionalproperties",
            "required property",
        )
    ):
        return "schema_rejection"
    if any(token in class_names or token in summary for token in ("jsondecodeerror", "invalid json", "decode json", "could not be decoded")):
        return "invalid_json"
    if any(
        token in class_names or token in summary
        for token in ("model", "notfound", "does not exist", "unsupported model", "unknown model", "404", "unavailable")
    ):
        return "bad_model"
    if any(
        token in class_names or token in summary
        for token in (
            "connection",
            "connecterror",
            "apiconnection",
            "network",
            "dns",
            "ssl",
            "name resolution",
            "temporary failure",
        )
    ):
        return "network"
    return "provider_call_failed"


def _sanitize_secret_like_text(text: str) -> str:
    sanitized = " ".join(text.split())
    patterns = (
        (r"Authorization\s*:\s*Bearer\s+[^\s,;]+", "Authorization: Bearer [redacted]"),
        (r"Bearer\s+[^\s,;]+", "Bearer [redacted]"),
        (r"sk-[A-Za-z0-9_\-]+", "sk-[redacted]"),
        (r"(?i)(api[_ -]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s,;]+['\"]?", r"\1=[redacted]"),
        (
            r"(?i)(openai|anthropic|google|authorization)[_ -]?(api[_ -]?key|token|secret)?\s*[:=]\s*['\"]?[^'\"\s,;]+['\"]?",
            "[redacted]",
        ),
    )
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized


def _truncate(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
