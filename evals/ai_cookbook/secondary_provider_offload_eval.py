from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CASES_PATH = Path(__file__).with_name("secondary_provider_offload_cases.yaml")
PRIMARY_BASELINE_PROVIDER = "openai"
PRIMARY_BASELINE_MODEL = "gpt-5.4-nano"
WINDOWS_HOME_MARKER = "C:" + "\\Users" + "\\"
UNIX_HOME_MARKER = "/" + "home" + "/"
ALLOWED_TASK_CLASSES = {
    "query_expansion",
    "ingredient_synonym_expansion",
    "dataset_metadata_cleanup_suggestions",
    "title_or_slug_suggestions",
    "non_final_clarification_candidate_generation",
    "context_compression",
    "draft_critique_against_quality_checklist",
    "formatting_only_rewrites_where_factual_content_is_already_fixed",
}
BLOCKED_TASK_CLASSES = {
    "final_user_answer_generation",
    "final_recipe_draft_generation",
    "food_safety_advice",
    "medical_allergy_diet_nutrition_claims",
    "citation_truth_or_faithfulness_final_decisions",
    "safety_refusal_decisions",
    "admin_operator_decisions",
    "provider_budget_decisions",
    "invite_session_security_decisions",
    "private_user_recipe_data_processing_without_explicit_future_privacy_decision",
    "any_task_that_can_publish_or_persist_data",
}
FORBIDDEN_PATTERNS = (
    "OPENAI_API_KEY",
    "sk" + "-",
    "Authorization:",
    ".env",
    WINDOWS_HOME_MARKER,
    UNIX_HOME_MARKER,
    "glm" + "-key",
)
PRIVATE_DATA_MARKERS = (
    "full name",
    "home address",
    "medical history",
    "password",
    "social security",
)
UNSUPPORTED_CLAIM_MARKERS = (
    "doctor-approved",
    "immune-boosting",
    "detox",
    "cure",
)
UNRELATED_EXPANSION_MARKERS = (
    "bitcoin",
    "chocolate cake",
    "stock market",
)


@dataclass(frozen=True)
class EvalResult:
    case_id: str
    passed: bool
    summary: str


def load_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or CASES_PATH
    return json.loads(case_path.read_text(encoding="utf-8"))


def evaluate_case(case: dict[str, Any]) -> EvalResult:
    case_id = str(case["id"])
    mode = str(case["mode"])
    task_class = str(case["task_class"])
    errors: list[str] = []

    _assert_safe_case(case_id, case, errors)
    _assert_required_behavior(case_id, case, errors)
    _assert_task_class(case_id, task_class, mode, errors)

    if task_class == "query_expansion":
        _check_query_expansion(case, errors)
    elif task_class == "context_compression":
        _check_context_compression(case, errors)
    elif task_class == "title_or_slug_suggestions":
        _check_title_slug(case, errors)
    elif task_class == "non_final_clarification_candidate_generation":
        _check_clarification(case, errors)
    elif task_class == "draft_critique_against_quality_checklist":
        _check_draft_critique(case, errors)
    elif task_class in BLOCKED_TASK_CLASSES:
        pass
    else:
        errors.append(f"unknown task_class={task_class}")

    if mode == "allow" and errors:
        return EvalResult(case_id=case_id, passed=False, summary=f"{case_id} rejected unexpectedly: {'; '.join(errors)}")
    if mode == "reject" and not errors:
        return EvalResult(case_id=case_id, passed=False, summary=f"{case_id} should have been rejected")
    if mode == "reject":
        return EvalResult(case_id=case_id, passed=True, summary=f"{case_id} rejected as expected")
    return EvalResult(case_id=case_id, passed=True, summary=f"{case_id} accepted as advisory-only")


def main() -> int:
    failures: list[str] = []
    results = [evaluate_case(case) for case in load_cases()]
    for result in results:
        prefix = "PASS" if result.passed else "FAIL"
        print(f"{prefix}: {result.summary}")
        if not result.passed:
            failures.append(result.summary)

    if failures:
        print(f"Secondary provider offload eval failed: {len(failures)} cases.", file=sys.stderr)
        return 1

    print(f"Secondary provider offload eval passed: {len(results)} cases.")
    return 0


def _assert_safe_case(case_id: str, case: dict[str, Any], errors: list[str]) -> None:
    serialized = json.dumps(case, sort_keys=True)
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in serialized:
            errors.append(f"{case_id} leaked forbidden pattern {pattern!r}")


def _assert_required_behavior(case_id: str, case: dict[str, Any], errors: list[str]) -> None:
    behavior = case.get("required_behavior") or {}
    if behavior.get("advisory_only") is not True:
        errors.append(f"{case_id} missing advisory_only=true")
    if behavior.get("final_answer_provider") != PRIMARY_BASELINE_PROVIDER:
        errors.append(f"{case_id} final_answer_provider must remain {PRIMARY_BASELINE_PROVIDER}")
    if not behavior.get("fallback"):
        errors.append(f"{case_id} missing fallback description")


def _assert_task_class(case_id: str, task_class: str, mode: str, errors: list[str]) -> None:
    if mode == "allow" and task_class not in ALLOWED_TASK_CLASSES:
        errors.append(f"{case_id} task_class={task_class} is not in the allowlist")
    if task_class in BLOCKED_TASK_CLASSES and mode == "reject":
        errors.append(f"blocked task_class={task_class}")
    if task_class in BLOCKED_TASK_CLASSES and mode != "reject":
        errors.append(f"{case_id} blocked task_class={task_class} must be rejected")


def _check_query_expansion(case: dict[str, Any], errors: list[str]) -> None:
    expansions = [str(item).lower() for item in (case.get("output") or {}).get("expansions", [])]
    if not expansions:
        errors.append("query expansion output missing expansions")
        return
    if any(marker in " ".join(expansions) for marker in UNRELATED_EXPANSION_MARKERS):
        errors.append("query expansion introduced unrelated terms")


def _check_context_compression(case: dict[str, Any], errors: list[str]) -> None:
    required_ids = [str(item) for item in case.get("required_citation_ids", [])]
    observed_ids = [str(item) for item in (case.get("output") or {}).get("citation_ids", [])]
    if not observed_ids:
        errors.append("context compression missing citation_ids")
        return
    missing = [item for item in required_ids if item not in observed_ids]
    invented = [item for item in observed_ids if item not in required_ids]
    if missing:
        errors.append(f"missing citation ids: {','.join(missing)}")
    if invented:
        errors.append(f"invented citation ids: {','.join(invented)}")


def _check_title_slug(case: dict[str, Any], errors: list[str]) -> None:
    output = case.get("output") or {}
    title = str(output.get("title") or "").lower()
    slug = str(output.get("slug") or "").lower()
    if not title or not slug:
        errors.append("title/slug suggestion missing title or slug")
        return
    combined = f"{title} {slug}"
    if any(marker in combined for marker in UNSUPPORTED_CLAIM_MARKERS):
        errors.append("title/slug suggestion introduced unsupported claims")


def _check_clarification(case: dict[str, Any], errors: list[str]) -> None:
    question = str((case.get("output") or {}).get("question") or "").lower()
    if not question:
        errors.append("clarification candidate missing question")
        return
    if any(marker in question for marker in PRIVATE_DATA_MARKERS):
        errors.append("clarification candidate requested private data")


def _check_draft_critique(case: dict[str, Any], errors: list[str]) -> None:
    output = case.get("output") or {}
    combined = json.dumps(output, sort_keys=True).lower()
    if "final answer" in combined and "advisory" not in combined:
        errors.append("draft critique attempted to become the final answer")
    if "final recipe" in combined:
        errors.append("draft critique attempted to become the final recipe")
    if not output.get("checklist_findings") and "advisory critique only" not in combined and case["mode"] == "allow":
        errors.append("draft critique did not stay checklist-shaped")


if __name__ == "__main__":
    raise SystemExit(main())
