from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SECRET_PATTERNS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization:",
    "raw provider config",
    "CLOUDFLARE_TUNNEL_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
)

KNOWN_SAVED_RECIPE_TITLES = (
    "Lemon Herb White Beans",
    "Weeknight Tomato Pasta",
    "Chickpea Cucumber Bowls",
)

KNOWN_DATASET_TITLES = (
    "Tomato Pasta Skillet",
    "Lemon White Bean Toasts",
    "Cucumber Chickpea Salad",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


def score_workflow(workflow: str, payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    if workflow == "readiness":
        return score_readiness(payload, expected_model)
    if workflow == "importer":
        return score_importer(payload, expected_model)
    if workflow == "ask_my_cookbook":
        return score_ask_my_cookbook(payload, expected_model)
    if workflow == "dataset_search":
        return score_dataset_search(payload)
    if workflow == "dataset_ask":
        return score_dataset_ask(payload, expected_model)
    if workflow == "meal_plan":
        return score_meal_plan(payload, expected_model)
    return [CheckResult("known workflow", False, f"Unknown workflow: {workflow}")]


def score_readiness(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    return [
        _check("sidecar is healthy", payload.get("service", {}).get("ok") is True),
        _check("provider mode is openai", payload.get("provider", {}).get("mode") == "openai"),
        _check("model matches configured OPENAI_MODEL", payload.get("provider", {}).get("model") == expected_model),
        _check("saved recipes are available", payload.get("saved_recipes", {}).get("available") is True),
        _check("dataset is available", payload.get("dataset", {}).get("available") is True),
    ]


def score_importer(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
    return [
        _check("response parses as expected schema", bool(draft)),
        _check("title is non-empty", bool(str(draft.get("title", "")).strip())),
        _check("ingredient list is non-empty", bool(draft.get("ingredients"))),
        _check("instructions are non-empty", bool(draft.get("instructions"))),
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check("no warnings unless justified", len(payload.get("warnings") or []) == 0),
    ]


def score_ask_my_cookbook(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    citations = payload.get("citations") or []
    answer = str(payload.get("answer") or "")
    cited_titles = {str(citation.get("title") or "") for citation in citations if isinstance(citation, dict)}
    mentioned_known_titles = _mentioned_titles(answer, KNOWN_SAVED_RECIPE_TITLES)
    retrieved_count = payload.get("retrieval", {}).get("retrieved_count", 0)
    return [
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check(
            "answer mentions or cites Lemon Herb White Beans",
            "Lemon Herb White Beans" in answer or "Lemon Herb White Beans" in cited_titles,
        ),
        _check("at least one citation is returned", bool(citations)),
        _check(
            "citation includes saved recipe id 1 or matching title",
            any(
                str(citation.get("recipe_id")) == "1" or citation.get("title") == "Lemon Herb White Beans"
                for citation in citations
                if isinstance(citation, dict)
            ),
        ),
        _check("retrieved count greater than zero", int(retrieved_count or 0) > 0),
        _check(
            "no hallucinated recipe title outside retrieved citations",
            mentioned_known_titles.issubset(cited_titles),
            f"mentioned={sorted(mentioned_known_titles)} cited={sorted(cited_titles)}",
        ),
    ]


def score_dataset_search(payload: dict[str, Any]) -> list[CheckResult]:
    results = payload.get("results") or []
    return [
        _check("deterministic baseline returns at least one result", bool(results)),
        _check("top results include Tomato Pasta Skillet", any(_title(result) == "Tomato Pasta Skillet" for result in results)),
        _check("result source id includes demo-dataset-1", any(result.get("source_id") == "demo-dataset-1" for result in results if isinstance(result, dict))),
        _check("provider is not used", "provider" not in payload and "model" not in payload),
    ]


def score_dataset_ask(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    citations = payload.get("citations") or []
    answer = str(payload.get("answer") or "")
    cited_titles = {str(citation.get("title") or "") for citation in citations if isinstance(citation, dict)}
    mentioned_known_titles = _mentioned_titles(answer, KNOWN_DATASET_TITLES)
    retrieved_count = payload.get("retrieval", {}).get("retrieved_count", 0)
    return [
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check(
            "answer mentions or cites Tomato Pasta Skillet",
            "Tomato Pasta Skillet" in answer or "Tomato Pasta Skillet" in cited_titles,
        ),
        _check("at least one citation is returned", bool(citations)),
        _check(
            "citation source id includes demo-dataset-1",
            any(citation.get("source_id") == "demo-dataset-1" for citation in citations if isinstance(citation, dict)),
        ),
        _check("retrieved count greater than zero", int(retrieved_count or 0) > 0),
        _check(
            "answer does not invent unsupported dataset recipes",
            mentioned_known_titles.issubset(cited_titles),
            f"mentioned={sorted(mentioned_known_titles)} cited={sorted(cited_titles)}",
        ),
    ]


def score_meal_plan(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    days = payload.get("plan", {}).get("days") or []
    meals = [meal for day in days if isinstance(day, dict) for meal in day.get("meals", []) if isinstance(meal, dict)]
    citations = payload.get("citations") or []
    candidate_ids = set(payload.get("selection", {}).get("matched_recipe_ids") or [])
    meal_ids = {str(meal.get("recipe_id")) for meal in meals if meal.get("recipe_id") is not None}
    citation_titles = {str(citation.get("title") or "") for citation in citations if isinstance(citation, dict)}
    return [
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check("plan has at least one day and one meal", bool(days) and bool(meals)),
        _check("selected recipe is from retrieved saved recipe candidates", bool(meal_ids) and meal_ids.issubset(candidate_ids)),
        _check("expected likely recipe is Lemon Herb White Beans", "1" in candidate_ids or "Lemon Herb White Beans" in citation_titles),
        _check("citations are present", bool(citations)),
        _check("no invented recipe ids", meal_ids.issubset(candidate_ids), f"meal_ids={sorted(meal_ids)} candidate_ids={sorted(candidate_ids)}"),
    ]


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    passed = sum(1 for record in records if record.get("overall_passed") is True)
    total_cost = sum(float(record.get("estimated_cost_usd") or 0.0) for record in records)
    input_tokens = sum(int(record.get("input_tokens") or 0) for record in records)
    output_tokens = sum(int(record.get("output_tokens") or 0) for record in records)
    total_tokens = sum(int(record.get("total_tokens") or 0) for record in records)
    return {
        "overall_passed": total > 0 and passed == total,
        "workflow_count": total,
        "passed_workflow_count": passed,
        "failed_workflow_count": total - passed,
        "total_latency_ms": sum(int(record.get("latency_ms") or 0) for record in records),
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "total_tokens": total_tokens or input_tokens + output_tokens,
        "estimated_cost_usd": round(total_cost, 8) if total_cost else None,
    }


def estimate_cost_usd(
    usage: dict[str, int] | None,
    *,
    input_cost_per_1m: float | None,
    output_cost_per_1m: float | None,
) -> float | None:
    if not usage or input_cost_per_1m is None or output_cost_per_1m is None:
        return None
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cost = (input_tokens / 1_000_000 * input_cost_per_1m) + (output_tokens / 1_000_000 * output_cost_per_1m)
    return round(cost, 8)


def assert_no_secret_leaks(value: Any) -> None:
    import json

    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern in text:
            raise AssertionError(f"secret-like pattern leaked: {pattern}")


def _check(name: str, passed: bool, detail: str | None = None) -> CheckResult:
    return CheckResult(name=name, passed=bool(passed), detail=detail or ("passed" if passed else "failed"))


def _mentioned_titles(answer: str, titles: tuple[str, ...]) -> set[str]:
    lowered = answer.lower()
    return {title for title in titles if title.lower() in lowered}


def _title(value: Any) -> str:
    return str(value.get("title") or "") if isinstance(value, dict) else ""
