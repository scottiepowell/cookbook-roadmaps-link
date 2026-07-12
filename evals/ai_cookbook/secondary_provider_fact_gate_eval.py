from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CASES_PATH = Path(__file__).with_name("secondary_provider_fact_gate.yaml")
PRIMARY_BASELINE_PROVIDER = "openai"
PRIMARY_BASELINE_MODEL = "gpt-5.4-nano"
WINDOWS_HOME_MARKER = "C:" + "\\Users" + "\\"
UNIX_HOME_MARKER = "/" + "home" + "/"
FORBIDDEN_PATTERNS = (
    "OPENAI_API_KEY",
    "sk" + "-",
    "Authorization:",
    ".env",
    WINDOWS_HOME_MARKER,
    UNIX_HOME_MARKER,
    "glm" + "-key",
)
REQUIRED_FACTS = (
    "provider_identity",
    "model_identifier",
    "primary_documentation_references",
    "api_protocol_and_auth",
    "request_response_schema",
    "structured_output_support",
    "streaming_support",
    "context_window",
    "max_output_tokens",
    "rate_limits",
    "quota_behavior",
    "pricing_input_tokens",
    "pricing_output_tokens",
    "free_tier_or_trial_terms",
    "privacy_policy",
    "data_retention_policy",
    "training_data_use_policy",
    "regional_availability",
    "account_and_billing_requirements",
    "safety_policy_or_usage_restrictions",
    "timeout_and_retry_guidance",
    "error_response_shape",
    "logging_redaction_requirements",
    "allowed_offload_tasks",
    "blocked_tasks",
    "fallback_requirements",
    "verification_owner_or_method",
    "verification_date",
    "implementation_gate_decision",
)
UNVERIFIED_MARKERS = {"", "unknown", "unverified", "not approved"}
ALLOWED_TASKS = {
    "query_expansion",
    "ingredient_synonym_expansion",
    "dataset_metadata_cleanup_suggestions",
    "title_or_slug_suggestions",
    "non_final_clarification_candidate_generation",
    "context_compression",
    "draft_critique_against_quality_checklist",
    "formatting_only_rewrites_where_factual_content_is_already_fixed",
}
REQUIRED_BLOCKED_TASKS = {
    "final_user_answer_generation",
    "private_user_recipe_data_processing_without_explicit_future_privacy_decision",
}


@dataclass(frozen=True)
class GateEvalResult:
    case_id: str
    passed: bool
    summary: str


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or CASES_PATH
    return json.loads(case_path.read_text(encoding="utf-8"))


def evaluate_case(case: dict[str, Any]) -> GateEvalResult:
    case_id = str(case["id"])
    expected_gate = str(case["expected_gate"])
    facts = case.get("facts") or {}
    errors: list[str] = []

    _assert_safe_case(case_id, case, errors)
    actual_gate, reasons = _gate_decision(facts)
    if actual_gate != expected_gate:
        errors.append(f"expected_gate={expected_gate} actual_gate={actual_gate}")
    if facts.get("implementation_gate_decision") != expected_gate:
        errors.append(
            f"implementation_gate_decision={facts.get('implementation_gate_decision')!r} expected {expected_gate!r}"
        )
    expected_reason_contains = case.get("expected_reason_contains")
    if expected_reason_contains:
        joined = " | ".join(reasons)
        if str(expected_reason_contains) not in joined:
            errors.append(f"missing expected reason fragment {expected_reason_contains!r}")

    if errors:
        return GateEvalResult(case_id=case_id, passed=False, summary=f"{case_id}: {'; '.join(errors)}")

    return GateEvalResult(case_id=case_id, passed=True, summary=f"{case_id}: gate={actual_gate} reasons={len(reasons)}")


def main() -> int:
    results = [evaluate_case(case) for case in load_cases()]
    failures = [result.summary for result in results if not result.passed]
    for result in results:
        prefix = "PASS" if result.passed else "FAIL"
        print(f"{prefix}: {result.summary}")

    if failures:
        print(f"Secondary provider fact gate eval failed: {len(failures)} cases.", file=sys.stderr)
        return 1

    print(f"Secondary provider fact gate eval passed: {len(results)} cases.")
    return 0


def _assert_safe_case(case_id: str, case: dict[str, Any], errors: list[str]) -> None:
    serialized = json.dumps(case, sort_keys=True)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in serialized:
            errors.append(f"{case_id} leaked forbidden pattern {pattern!r}")


def _gate_decision(facts: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    for fact_name in REQUIRED_FACTS:
        value = facts.get(fact_name)
        if _is_unverified(value):
            reasons.append(f"{fact_name} is unverified")

    allowed_offload_tasks = {str(item) for item in facts.get("allowed_offload_tasks") or []}
    if not allowed_offload_tasks:
        reasons.append("allowed_offload_tasks is empty")
    elif not allowed_offload_tasks.issubset(ALLOWED_TASKS):
        reasons.append("allowed_offload_tasks contains blocked or unknown task classes")

    blocked_tasks = {str(item) for item in facts.get("blocked_tasks") or []}
    if not REQUIRED_BLOCKED_TASKS.issubset(blocked_tasks):
        reasons.append("blocked_tasks is missing required blocked classes")

    fallback_text = str(facts.get("fallback_requirements") or "")
    baseline_marker = PRIMARY_BASELINE_PROVIDER in fallback_text.lower() and PRIMARY_BASELINE_MODEL in fallback_text.lower()
    if not baseline_marker:
        reasons.append("fallback_requirements must point back to the OpenAI gpt-5.4-nano baseline")

    if str(facts.get("provider_identity") or "").lower() == "glm":
        references = facts.get("primary_documentation_references")
        if _is_unverified(references):
            reasons.append("primary provider documentation was not available in this task")

    actual_gate = "blocked" if reasons else "approved"
    return actual_gate, reasons


def _is_unverified(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in UNVERIFIED_MARKERS
    if isinstance(value, (list, tuple, set)):
        if not value:
            return True
        return any(_is_unverified(item) for item in value)
    if isinstance(value, dict):
        return not value
    return False


if __name__ == "__main__":
    raise SystemExit(main())
