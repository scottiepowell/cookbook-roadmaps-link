from __future__ import annotations

import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


MAX_BUDGET_CENTS = 25
MAX_OUTPUT_TOKENS_LIMIT = 300
IMPORTER_MAX_OUTPUT_TOKENS_LIMIT = 1200
DEFAULT_IMPORTER_MAX_OUTPUT_TOKENS = 900
DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"
DEFAULT_BUDGET_SESSION_ID = "live-openai-demo-evals"
LIVE_CASES_PATH = Path("evals/ai_cookbook/live_cases.json")
IMPORTER_OUTPUT_TOKEN_ENV_NAMES = (
    "OPENAI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS",
    "AI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS",
)


@dataclass(frozen=True)
class GuardResult:
    should_run: bool
    exit_code: int
    message: str
    budget_cents: int | None = None
    model: str | None = None


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "ai-api"))
    sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)
    os.environ.setdefault("AI_PROVIDER_BUDGET_SESSION_ID", DEFAULT_BUDGET_SESSION_ID)

    guard = evaluate_live_eval_guard(os.environ)
    if not guard.should_run:
        print(guard.message)
        return guard.exit_code

    run_dir = _new_run_dir(repo_root)
    try:
        records, summary = run_live_eval_suite(run_dir=run_dir, expected_model=guard.model or DEFAULT_OPENAI_MODEL)
    except Exception as exc:
        safe_message = _safe_error(exc)
        print(f"FAIL: live OpenAI demo eval failed: {safe_message}", file=sys.stderr)
        return 1

    print(f"report={summary['summary_md_path']}")
    print(
        "status={status} workflows={passed}/{total} tokens={tokens} estimated_cost_usd={cost}".format(
            status="passed" if summary["overall_passed"] else "failed",
            passed=summary["passed_workflow_count"],
            total=summary["workflow_count"],
            tokens=summary["total_tokens"],
            cost=summary["estimated_cost_usd"],
        )
    )
    return 0 if all(record["overall_passed"] for record in records) else 1


def evaluate_live_eval_guard(env: dict[str, str]) -> GuardResult:
    if env.get("OPENAI_ENABLE_LIVE_TESTS") != "true":
        return GuardResult(False, 0, _requirements_message("OPENAI_ENABLE_LIVE_TESTS=true is required."))
    if env.get("AI_PROVIDER") != "openai":
        return GuardResult(False, 0, _requirements_message("AI_PROVIDER=openai is required."))
    if not env.get("OPENAI_API_KEY", "").strip():
        return GuardResult(False, 0, _requirements_message("OPENAI_API_KEY must be present."))
    if env.get("AI_PROVIDER_CALLS_ENABLED") == "false" or env.get("AI_PROVIDER_GLOBAL_DISABLE") == "true":
        return GuardResult(False, 0, _requirements_message("provider calls are disabled by budget settings."))

    raw_budget = env.get("OPENAI_LIVE_TEST_BUDGET_CENTS")
    if not raw_budget:
        return GuardResult(False, 0, _requirements_message("OPENAI_LIVE_TEST_BUDGET_CENTS is required."))
    try:
        budget = int(raw_budget)
    except ValueError:
        return GuardResult(False, 2, "FAIL: OPENAI_LIVE_TEST_BUDGET_CENTS must be an integer.")
    if budget < 1 or budget > MAX_BUDGET_CENTS:
        return GuardResult(False, 2, f"FAIL: live eval budget must be between 1 and {MAX_BUDGET_CENTS} cents.")

    model = env.get("OPENAI_MODEL", "").strip()
    if not model:
        return GuardResult(False, 0, _requirements_message(f"OPENAI_MODEL is required; expected default is {DEFAULT_OPENAI_MODEL}."))

    raw_tokens = env.get("AI_MAX_OUTPUT_TOKENS")
    if not raw_tokens:
        return GuardResult(False, 0, _requirements_message("AI_MAX_OUTPUT_TOKENS is required and must be capped for eval runs."))
    try:
        max_tokens = int(raw_tokens)
    except ValueError:
        return GuardResult(False, 2, "FAIL: AI_MAX_OUTPUT_TOKENS must be an integer.")
    if max_tokens < 1 or max_tokens > MAX_OUTPUT_TOKENS_LIMIT:
        return GuardResult(False, 2, f"FAIL: AI_MAX_OUTPUT_TOKENS must be between 1 and {MAX_OUTPUT_TOKENS_LIMIT}.")

    return GuardResult(True, 0, "RUN: live OpenAI demo evals enabled.", budget_cents=budget, model=model)


def run_live_eval_suite(run_dir: Path, expected_model: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from app.config import get_ai_settings
    from app.dataset_retrieval import search_dataset_recipes
    from app.dataset_rag import ask_dataset_recipes
    from app.demo_data import seed_demo_data
    from app.importer import import_recipe_text
    from app.main import demo_readiness
    from app.meal_plan_endpoint import create_meal_plan
    from app.providers import get_provider
    from app.rag import ask_cookbook
    from app.schemas import AskRequest, DatasetAskRequest, RecipeImportRequest, MealPlanRequest
    from evals.ai_cookbook.expected_checks import score_workflow

    fixtures_dir = run_dir / "fixtures"
    responses_dir = run_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    paths = seed_demo_data(fixtures_dir)
    importer_max_output_tokens = _resolve_importer_output_tokens(os.environ)

    old_env = {name: os.environ.get(name) for name in ("COOKBOOK_DB_PATH", "RECIPE_DATASET_DIR", "RECIPE_DATASET_INDEX_LIMIT")}
    os.environ["COOKBOOK_DB_PATH"] = str(paths["db_path"])
    os.environ["RECIPE_DATASET_DIR"] = str(paths["dataset_dir"])
    os.environ["RECIPE_DATASET_INDEX_LIMIT"] = "25"

    try:
        provider = get_provider(get_ai_settings())
        cases = load_cases(Path.cwd() / LIVE_CASES_PATH)
        dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "readiness": lambda case: demo_readiness(),
            "importer": lambda case: _run_importer_case(
                case,
                provider=provider,
                max_output_tokens=importer_max_output_tokens,
            ),
            "ask_my_cookbook": lambda case: ask_cookbook(AskRequest(**case["request"]), provider=provider),
            "dataset_search": lambda case: search_dataset_recipes(**case["request"]),
            "dataset_ask": lambda case: ask_dataset_recipes(DatasetAskRequest(**case["request"]), provider=provider),
            "meal_plan": lambda case: create_meal_plan(MealPlanRequest(**case["request"]), provider=provider),
        }

        records = []
        for case in cases:
            record = run_case(case, dispatch[case["workflow"]], responses_dir, expected_model, score_workflow)
            records.append(record)

        summary = write_run_outputs(run_dir=run_dir, records=records, cases=cases, expected_model=expected_model)
        return records, summary
    finally:
        for name, value in old_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def run_case(
    case: dict[str, Any],
    runner: Callable[[dict[str, Any]], Any],
    responses_dir: Path,
    expected_model: str,
    scorer: Callable[[str, dict[str, Any], str], Any],
) -> dict[str, Any]:
    from evals.ai_cookbook.expected_checks import assert_no_secret_leaks, estimate_cost

    workflow = case["workflow"]
    started = time.perf_counter()
    error_type = None
    caught_exc: BaseException | None = None
    payload: dict[str, Any]
    try:
        response = runner(case)
        payload = _to_plain_dict(response)
    except Exception as exc:
        caught_exc = exc
        error_type = exc.__class__.__name__
        payload = {"error": _safe_error(exc)}
    latency_ms = int((time.perf_counter() - started) * 1000)

    if _looks_like_budget_block(payload):
        error_type = "BudgetBlocked"
        payload.setdefault("error", "Provider call was blocked by budget settings.")

    failure_info = _classify_live_eval_failure(workflow, payload, caught_exc, error_type)
    assert_no_secret_leaks(payload)
    response_path = responses_dir / f"{workflow}.json"
    response_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checks = scorer(workflow, payload, expected_model) if error_type is None else []
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    input_quality = payload.get("input_quality") if isinstance(payload.get("input_quality"), dict) else {}
    provider_called = _provider_called(workflow, payload)
    cost_estimate = estimate_cost(
        usage,
        model=str(payload.get("model") or expected_model),
        input_cost_per_1m=_float_env("OPENAI_INPUT_COST_PER_1M_TOKENS"),
        output_cost_per_1m=_float_env("OPENAI_OUTPUT_COST_PER_1M_TOKENS"),
    )
    record = {
        "workflow": workflow,
        "endpoint": case.get("endpoint"),
        "provider": payload.get("provider", "none"),
        "model": payload.get("model", "none"),
        "input_summary": case.get("input_summary"),
        "expected_checks": case.get("expected_checks", []),
        "actual_answer_summary": _answer_summary(workflow, payload),
        "checks": [check.to_dict() for check in checks],
        "overall_passed": error_type is None and bool(checks) and all(check.passed for check in checks),
        "warning_count": len(payload.get("warnings") or []),
        "citation_count": len(payload.get("citations") or []),
        "retrieved_count": _retrieved_count(payload),
        "input_quality_status": input_quality.get("status"),
        "input_quality_reason": input_quality.get("reason"),
        "clarification_question_present": bool(input_quality.get("clarifying_question")),
        "rejected_before_provider": input_quality.get("status") == "rejected" and not provider_called,
        "provider_called": provider_called,
        **failure_info,
        "latency_ms": latency_ms,
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0) or int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0),
        **cost_estimate.to_record_fields(),
        "raw_response_path": str(response_path),
        "error_type": error_type,
    }
    assert_no_secret_leaks(record)
    return record


def write_run_outputs(
    *,
    run_dir: Path,
    records: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    expected_model: str,
) -> dict[str, Any]:
    from evals.ai_cookbook.expected_checks import apply_threshold_checks, assert_no_secret_leaks, summarize_records

    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    summary_json_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"

    records = apply_threshold_checks(records)

    with results_path.open("w", encoding="utf-8") as handle:
        for record in records:
            assert_no_secret_leaks(record)
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    summary = {
        "created_at": datetime.now(UTC).isoformat(),
        "expected_model": expected_model,
        "case_count": len(cases),
        "results_path": str(results_path),
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        **summarize_records(records),
    }
    assert_no_secret_leaks(summary)
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md_path.write_text(render_markdown_summary(summary, records), encoding="utf-8")
    return summary


def render_markdown_summary(summary: dict[str, Any], records: list[dict[str, Any]]) -> str:
    lines = [
        "# Live OpenAI Demo Eval Summary",
        "",
        f"- Created: `{summary['created_at']}`",
        f"- Expected model: `{summary['expected_model']}`",
        f"- Overall passed: `{summary['overall_passed']}`",
        f"- Workflows passed: `{summary['passed_workflow_count']}/{summary['workflow_count']}`",
        f"- Total latency ms: `{summary['total_latency_ms']}`",
        f"- Total tokens: `{summary['total_tokens']}`",
        f"- Estimated cost USD: `{summary['estimated_cost_usd']}`",
        f"- Cost sources: `{', '.join(summary['cost_sources'])}`",
        f"- Threshold warnings: `{len(summary['threshold_warnings'])}`",
        f"- Threshold failures: `{len(summary['threshold_failures'])}`",
        "",
        "| Workflow | Result | Failure | Latency ms | Citations | Retrieved | Tokens | Cost USD | Cost Source | Response |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for record in records:
        result = "PASS" if record["overall_passed"] else "FAIL"
        lines.append(
            "| {workflow} | {result} | {failure} | {latency} | {citations} | {retrieved} | {tokens} | {cost} | {cost_source} | `{path}` |".format(
                workflow=record["workflow"],
                result=result,
                failure=record.get("failure_category") or "-",
                latency=record["latency_ms"],
                citations=record["citation_count"],
                retrieved=record["retrieved_count"],
                tokens=record["total_tokens"],
                cost=record.get("estimated_cost_usd"),
                cost_source=record.get("cost_source"),
                path=record["raw_response_path"],
            )
        )
    lines.append("")
    lines.append("## Failed Checks")
    lines.append("")
    failed_any = False
    for record in records:
        for check in record.get("checks", []):
            if not check.get("passed"):
                failed_any = True
                lines.append(f"- `{record['workflow']}`: {check['name']} - {check['detail']}")
        if record.get("error_type"):
            failed_any = True
            failure_bits = [record["error_type"]]
            if record.get("failure_category"):
                failure_bits.insert(0, str(record["failure_category"]))
            if record.get("provider_error_category"):
                provider_bits = [str(record["provider_error_category"])]
                if record.get("provider_error_type"):
                    provider_bits.append(str(record["provider_error_type"]))
                failure_bits.append("/".join(provider_bits))
            if record.get("safe_error_summary"):
                failure_bits.append(str(record["safe_error_summary"]))
            lines.append(f"- `{record['workflow']}` failed with {' | '.join(failure_bits)}.")
    if not failed_any:
        lines.append("- None.")
    lines.append("")
    lines.append("## Threshold Warnings")
    lines.append("")
    if summary["threshold_warnings"]:
        for warning in summary["threshold_warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("## Threshold Failures")
    lines.append("")
    if summary["threshold_failures"]:
        for failure in summary["threshold_failures"]:
            lines.append(f"- {failure}")
    else:
        lines.append("- None.")
    lines.append("")
    return "\n".join(lines)


def load_cases(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _new_run_dir(repo_root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return repo_root / ".tmp-ai-demo" / "live-evals" / timestamp


def _requirements_message(reason: str) -> str:
    return "\n".join(
        [
            f"SKIP: {reason}",
            "Required live eval settings: AI_PROVIDER=openai, OPENAI_ENABLE_LIVE_TESTS=true,",
            "OPENAI_API_KEY present, OPENAI_LIVE_TEST_BUDGET_CENTS within 1-25,",
            f"OPENAI_MODEL configured, and AI_MAX_OUTPUT_TOKENS between 1 and {MAX_OUTPUT_TOKENS_LIMIT}.",
        ]
    )


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return {"value": value}


def _answer_summary(workflow: str, payload: dict[str, Any]) -> str:
    if "error" in payload:
        return str(payload["error"])[:240]
    if workflow == "readiness":
        return f"provider={payload.get('provider', {}).get('mode')} saved={payload.get('saved_recipes', {}).get('count')}"
    if workflow == "importer":
        return str(payload.get("draft", {}).get("title") or "")[:240]
    if workflow == "dataset_search":
        return ", ".join(str(result.get("title")) for result in payload.get("results", [])[:3] if isinstance(result, dict))[:240]
    if workflow == "meal_plan":
        meals = [
            meal.get("title")
            for day in payload.get("plan", {}).get("days", [])
            for meal in day.get("meals", [])
            if isinstance(meal, dict)
        ]
        return ", ".join(str(meal) for meal in meals)[:240]
    return str(payload.get("answer") or "")[:240]


def _retrieved_count(payload: dict[str, Any]) -> int:
    if isinstance(payload.get("retrieval"), dict):
        return int(payload["retrieval"].get("retrieved_count") or 0)
    if isinstance(payload.get("selection"), dict):
        return int(payload["selection"].get("candidate_count") or 0)
    return int(payload.get("count") or 0)


def _provider_called(workflow: str, payload: dict[str, Any]) -> bool:
    if workflow in {"readiness", "dataset_search"}:
        return False
    return str(payload.get("provider") or "none") != "none"


def _float_env(name: str) -> float | None:
    raw = os.getenv(name)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _resolve_importer_output_tokens(env: dict[str, str]) -> int:
    for name in IMPORTER_OUTPUT_TOKEN_ENV_NAMES:
        raw = env.get(name)
        if raw is None or not raw.strip():
            continue
        try:
            value = int(raw)
        except ValueError as exc:
            raise ValueError(f"{name} must be an integer.") from exc
        if value < 1 or value > IMPORTER_MAX_OUTPUT_TOKENS_LIMIT:
            raise ValueError(
                f"{name} must be between 1 and {IMPORTER_MAX_OUTPUT_TOKENS_LIMIT}."
            )
        return value
    return DEFAULT_IMPORTER_MAX_OUTPUT_TOKENS


@contextmanager
def _temporary_env(overrides: dict[str, str | None]):
    original = {name: os.environ.get(name) for name in overrides}
    try:
        for name, value in overrides.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        yield
    finally:
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _run_importer_case(
    case: dict[str, Any],
    *,
    provider: Any,
    max_output_tokens: int,
) -> Any:
    from app.importer import import_recipe_text
    from app.schemas import RecipeImportRequest

    with _temporary_env(
        {
            "AI_MAX_OUTPUT_TOKENS": str(max_output_tokens),
            "AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL": str(max_output_tokens),
        }
    ):
        return import_recipe_text(RecipeImportRequest(**case["request"]), provider=provider)


def _classify_live_eval_failure(
    workflow: str,
    payload: dict[str, Any],
    exc: BaseException | None,
    error_type: str | None,
) -> dict[str, Any]:
    from app.importer import RecipeImportValidationError
    from app.providers.errors import describe_provider_exception, extract_provider_debug_details

    failure_category = None
    provider_error_category = None
    provider_error_type = None
    safe_error_summary = None

    if error_type is None and not _looks_like_budget_block(payload):
        return {
            "failure_category": None,
            "provider_error_category": None,
            "provider_error_type": None,
            "safe_error_summary": None,
        }

    if _looks_like_budget_block(payload):
        warning_text = " ".join(str(item) for item in payload.get("warnings") or [])
        safe_error_summary = str(payload.get("error") or warning_text or "Provider call was blocked by budget settings.")
        return {
            "failure_category": "budget_block_before_invocation",
            "provider_error_category": "budget_block_before_invocation",
            "provider_error_type": "BudgetBlocked",
            "safe_error_summary": _safe_error_text(safe_error_summary),
        }

    if exc is not None and isinstance(exc, RecipeImportValidationError):
        safe_error_summary = _safe_error(exc)
        return {
            "failure_category": "validation_schema_failure",
            "provider_error_category": "validation_schema_failure",
            "provider_error_type": exc.__class__.__name__,
            "safe_error_summary": safe_error_summary,
        }

    if exc is not None:
        details = extract_provider_debug_details(exc) or describe_provider_exception(exc)
        provider_error_category = details.category
        provider_error_type = details.exception_type
        safe_error_summary = details.safe_summary
        failure_category = "provider_call_failure"
        if provider_error_category == "output_cap_or_incomplete_response":
            failure_category = "provider_call_failure"
        return {
            "failure_category": failure_category,
            "provider_error_category": provider_error_category,
            "provider_error_type": provider_error_type,
            "safe_error_summary": safe_error_summary,
        }

    return {
        "failure_category": None,
        "provider_error_category": None,
        "provider_error_type": None,
        "safe_error_summary": None,
    }

def _safe_error(exc: BaseException) -> str:
    text = str(exc)
    for marker in ("OPENAI_API_KEY", "sk-", "Authorization:"):
        text = text.replace(marker, "[redacted]")
    return text[:500]


def _safe_error_text(text: str) -> str:
    for marker in ("OPENAI_API_KEY", "sk-", "Authorization:"):
        text = text.replace(marker, "[redacted]")
    return text[:500]


def _looks_like_budget_block(payload: dict[str, Any]) -> bool:
    provider = str(payload.get("provider") or "").lower()
    if provider != "none":
        return False
    warnings = " ".join(str(item) for item in payload.get("warnings") or [])
    lowered = warnings.lower()
    return any(token in lowered for token in ("budget", "disabled", "exhausted", "cap", "misconfigured"))


if __name__ == "__main__":
    raise SystemExit(main())
