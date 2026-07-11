from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAX_BUDGET_CENTS = 25
DEFAULT_TEXT = "omelet with eggs cheese maybe onions cooked in butter fold it over"
DEFAULT_MAX_OUTPUT_TOKENS = 900
DEFAULT_AI_TIMEOUT_SECONDS = 60
DEFAULT_BUDGET_SESSION_ID = "live-openai-importer-smoke"


@dataclass(frozen=True)
class GuardResult:
    should_run: bool
    exit_code: int
    message: str
    budget_cents: int | None = None


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "ai-api"))
    sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)

    args = parse_args(argv)
    _apply_overrides(args)
    os.environ.setdefault("AI_PROVIDER_BUDGET_SESSION_ID", DEFAULT_BUDGET_SESSION_ID)

    guard = evaluate_live_guard(os.environ)
    if not guard.should_run:
        print(guard.message)
        return guard.exit_code

    from app.config import get_ai_settings
    from app.importer import RecipeImportProviderError, RecipeImportValidationError, import_recipe_text
    from app.providers import get_provider
    from app.providers.errors import ProviderConfigError, ProviderError, extract_provider_debug_details
    from app.schemas import RecipeImportRequest

    try:
        settings = get_ai_settings()
        provider = get_provider(settings)
    except ProviderConfigError as exc:
        return _fail_safely(
            "provider configuration failed before live importer call: "
            f"{_safe_error(exc)}",
        )

    try:
        response = import_recipe_text(
            RecipeImportRequest(text=args.text, source="manual live importer smoke"),
            provider=provider,
        )
    except (RecipeImportProviderError, RecipeImportValidationError, ProviderError) as exc:
        return _fail_with_classification(exc, args.provider_debug)
    except Exception as exc:  # pragma: no cover - manual-only defensive guard.
        return _fail_safely(f"unexpected importer failure: {_safe_error(exc)}")

    if getattr(response, "provider", "none") != "openai":
        warnings = " ".join(getattr(response, "warnings", []) or [])
        if _looks_like_budget_block(warnings):
            return _fail_safely("live importer smoke blocked by budget settings.")
        return _fail_safely(
            f"live importer smoke did not use the openai provider: provider={getattr(response, 'provider', 'none')}"
        )

    summary = format_success_summary(response)
    _assert_no_secret_leaks(summary)
    print("\n".join(summary))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual live importer smoke test.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Importer input text.")
    parser.add_argument("--max-output-tokens", type=int, default=None, help="Optional output token cap override.")
    parser.add_argument("--ai-timeout-seconds", type=float, default=None, help="Optional provider timeout override.")
    parser.add_argument("--provider-debug", action="store_true", help="Enable sanitized provider debug output.")
    return parser.parse_args(argv)


def evaluate_live_guard(env: dict[str, str]) -> GuardResult:
    if env.get("OPENAI_ENABLE_LIVE_TESTS") != "true":
        return GuardResult(False, 0, "SKIP: live OpenAI importer smoke tests are disabled.")
    if env.get("AI_PROVIDER") != "openai":
        return GuardResult(False, 0, "SKIP: AI_PROVIDER is not openai.")
    if not env.get("OPENAI_API_KEY", "").strip():
        return GuardResult(False, 0, "SKIP: OpenAI API key is not configured.")
    if env.get("AI_PROVIDER_CALLS_ENABLED") == "false" or env.get("AI_PROVIDER_GLOBAL_DISABLE") == "true":
        return GuardResult(False, 0, "SKIP: provider calls are disabled by budget settings.")

    raw_budget = env.get("OPENAI_LIVE_TEST_BUDGET_CENTS") or str(MAX_BUDGET_CENTS)
    try:
        budget = int(raw_budget)
    except ValueError:
        return GuardResult(False, 2, "FAIL: live budget cap is missing or invalid.")
    if budget < 1 or budget > MAX_BUDGET_CENTS:
        return GuardResult(False, 2, f"FAIL: live budget cap must be between 1 and {MAX_BUDGET_CENTS} cents.")

    raw_tokens = env.get("AI_MAX_OUTPUT_TOKENS") or str(DEFAULT_MAX_OUTPUT_TOKENS)
    try:
        max_tokens = int(raw_tokens)
    except ValueError:
        return GuardResult(False, 2, "FAIL: AI_MAX_OUTPUT_TOKENS is invalid.")
    if max_tokens < 1:
        return GuardResult(False, 2, "FAIL: AI_MAX_OUTPUT_TOKENS must be greater than 0.")

    return GuardResult(True, 0, "RUN: live OpenAI importer smoke test enabled.", budget_cents=budget)


def format_success_summary(response: Any) -> list[str]:
    draft = getattr(response, "draft", None)
    retrieval = getattr(response, "retrieval", None)
    citations = getattr(response, "citations", None) or []
    usage = getattr(response, "usage", None) or {}
    ingredients = getattr(draft, "ingredients", None) or []
    instructions = getattr(draft, "instructions", None) or []
    return [
        f"provider={getattr(response, 'provider', 'none')}",
        f"model={getattr(response, 'model', 'none')}",
        f"title={getattr(draft, 'title', 'none')}",
        f"servings={getattr(draft, 'servings', 'none')}",
        f"ingredient_count={len(ingredients)}",
        f"instruction_count={len(instructions)}",
        f"retrieval_count={getattr(retrieval, 'retrieved_count', 0) if retrieval is not None else 0}",
        f"citation_count={len(citations)}",
        f"usage_input_tokens={usage.get('input_tokens', 0)}",
        f"usage_output_tokens={usage.get('output_tokens', 0)}",
        f"usage_total_tokens={usage.get('total_tokens', 0)}",
        "status=passed",
    ]


def _fail_with_classification(exc: BaseException, provider_debug: bool) -> int:
    from app.providers.errors import extract_provider_debug_details

    details = extract_provider_debug_details(exc)
    if details is None:
        return _fail_safely(f"live importer smoke failed: {_safe_error(exc)}")

    parts = [
        f"provider_error_category={details.category}",
        f"provider_error_type={details.exception_type}",
    ]
    if provider_debug:
        parts.append(f"safe_error_summary={details.safe_summary}")
    return _fail_safely("live importer smoke failed: " + " ".join(parts))


def _apply_overrides(args: argparse.Namespace) -> None:
    if args.max_output_tokens is not None:
        os.environ["AI_MAX_OUTPUT_TOKENS"] = str(args.max_output_tokens)
    else:
        os.environ["AI_MAX_OUTPUT_TOKENS"] = str(DEFAULT_MAX_OUTPUT_TOKENS)

    if args.ai_timeout_seconds is not None:
        os.environ["AI_TIMEOUT_SECONDS"] = str(args.ai_timeout_seconds)
    else:
        os.environ["AI_TIMEOUT_SECONDS"] = str(DEFAULT_AI_TIMEOUT_SECONDS)

    if args.provider_debug:
        os.environ["AI_PROVIDER_DEBUG"] = "true"


def _assert_no_secret_leaks(payload: Any) -> None:
    serialized = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    for pattern in (
        "OPENAI_API_KEY",
        "sk-",
        "Authorization:",
        ".env",
        "CLOUDFLARE_TUNNEL_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
    ):
        assert pattern not in serialized, f"secret-like pattern leaked: {pattern}"


def _safe_error(exc: BaseException) -> str:
    text = str(exc)
    for pattern in ("OPENAI_API_KEY", "sk-", "Authorization:", ".env"):
        text = text.replace(pattern, "[redacted]")
    return text


def _looks_like_budget_block(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("budget", "disabled", "exhausted", "cap", "misconfigured"))


def _fail_safely(message: str) -> int:
    _assert_no_secret_leaks(message)
    print(f"FAIL: {message}", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
