from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


TOTAL_LATENCY_MS_WARN = 15000
IMPORTER_LATENCY_MS_WARN = 7000
WORKFLOW_LATENCY_MS_FAIL = 10000
TOTAL_TOKENS_WARN = 2500
IMPORTER_TOKENS_WARN = 900
WORKFLOW_TOKENS_FAIL = 1200
COST_SOURCE_ENV_OVERRIDE = "env_override"
COST_SOURCE_DEFAULT_MODEL_RATE = "default_model_rate"
COST_SOURCE_UNAVAILABLE = "unavailable"
DEFAULT_MODEL_COST_RATES_PER_1M_TOKENS = {
    "gpt-5.4-nano": {
        "input": 0.20,
        "output": 1.25,
    },
}

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

IMPORTER_INPUT_INGREDIENTS = ("white beans", "olive oil", "garlic", "lemon", "parsley", "toast")
IMPORTER_INGREDIENT_ALIASES = {
    "white beans": ("white beans", "beans", "bean"),
    "olive oil": ("olive oil", "oil"),
    "garlic": ("garlic",),
    "lemon": ("lemon", "lemon juice", "citrus"),
    "parsley": ("parsley", "herbs", "herb"),
    "toast": ("toast", "bread"),
}
UNRELATED_IMPORTER_FOODS = ("chicken", "beef", "paneer", "shrimp", "chocolate", "banana")
GENERIC_TITLES = ("mock-value", "recipe", "untitled", "dish", "meal")
GENERIC_FIELD_VALUES = (*GENERIC_TITLES, "mock value", "n/a", "none")
ACTION_VERBS = (
    "add",
    "bake",
    "boil",
    "combine",
    "cook",
    "finish",
    "heat",
    "mix",
    "serve",
    "simmer",
    "spoon",
    "stir",
    "toast",
    "toss",
    "warm",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class CostEstimate:
    estimated_cost_usd: float | None
    cost_source: str
    input_cost_per_1m_tokens: float | None = None
    output_cost_per_1m_tokens: float | None = None

    def to_record_fields(self) -> dict[str, object]:
        return {
            "estimated_cost_usd": self.estimated_cost_usd,
            "cost_source": self.cost_source,
        }


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
    title = str(draft.get("title", "")).strip()
    description = str(draft.get("description") or "")
    notes = str(draft.get("notes") or "")
    servings = draft.get("servings")
    raw_ingredients = draft.get("ingredients") or []
    ingredients = _ingredient_names(draft.get("ingredients") or [])
    instructions = _instruction_texts(draft.get("instructions") or [])
    citations = payload.get("citations") or []
    retrieval = payload.get("retrieval") if isinstance(payload.get("retrieval"), dict) else {}
    field_texts = [title, description, *ingredients, *instructions]
    structured_evidence = _importer_ingredient_evidence(field_texts)
    description_evidence = _importer_ingredient_evidence([description])
    unrelated = _mentioned_terms(field_texts, UNRELATED_IMPORTER_FOODS)
    generic_values = _generic_field_values([title, *ingredients, *instructions])
    quantity_count = _ingredient_quantity_count(raw_ingredients)
    all_text = " ".join(field_texts + [notes]).lower()
    return [
        _check("response parses as expected schema", bool(draft)),
        _check("title is non-empty", bool(title)),
        _check("ingredient list is non-empty", bool(draft.get("ingredients"))),
        _check("instructions are non-empty", bool(draft.get("instructions"))),
        _check("servings default to 4 when unspecified", servings == 4),
        _check("ingredients include generated quantities", quantity_count >= 2, f"quantity_count={quantity_count}"),
        _check("notes disclose estimated/default quantities", any(term in notes.lower() for term in ("estimated", "default", "4 servings", "quantities"))),
        _check("importer dataset citations are returned when available", bool(citations)),
        _check("importer retrieval metadata is returned", int(retrieval.get("retrieved_count") or 0) >= 1),
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check("no warnings unless justified", len(payload.get("warnings") or []) == 0),
        _check("title should not be a generic placeholder", bool(title) and title.lower() not in GENERIC_TITLES),
        _check(
            "draft should preserve at least two input ingredients across structured fields",
            len(structured_evidence) >= 2,
            f"evidence={sorted(structured_evidence)}",
        ),
        _check(
            "description should be ingredient-grounded when present",
            not description.strip() or bool(description_evidence),
            f"evidence={sorted(description_evidence)}",
        ),
        _check(
            "notes should mention missing quantities or unspecified details when source input is sparse",
            any(term in notes.lower() for term in ("missing", "unspecified", "quantity", "quantities", "not specified")),
        ),
        _check(
            "instructions should be concise and action-oriented",
            bool(instructions)
            and all(len(instruction.split()) <= 24 for instruction in instructions)
            and all(_starts_with_action_verb(instruction) for instruction in instructions),
        ),
        _check("instructions should have enough step depth", len(instructions) >= 3),
        _check(
            "omelet instructions should prepare eggs before cooking",
            "omelet" not in all_text or _contains_any(all_text, ("beat", "scramble", "whisk")),
        ),
        _check(
            "carbonara should not require heavy cream unless supplied",
            "carbonara" not in all_text or "heavy cream" not in all_text,
        ),
        _check(
            "cheesecake instructions should cover bake and chill",
            "cheesecake" not in all_text or ("bake" in all_text and "chill" in all_text and len(instructions) > 1),
        ),
        _check(
            "chicken casserole should include doneness or safety guidance",
            not ("chicken" in all_text and "casserole" in all_text) or _contains_any(all_text, ("165", "done", "doneness", "safe", "temperature")),
        ),
        _check("structured fields should not be generic placeholders", not generic_values, f"generic={generic_values}"),
        _check("draft should not include unrelated foods", not unrelated, f"unrelated={sorted(unrelated)}"),
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
        _check("answer should be concise", _word_count(answer) <= 90, f"words={_word_count(answer)}"),
        _check(
            "answer should not claim more than retrieved citations support",
            mentioned_known_titles.issubset(cited_titles),
            f"mentioned={sorted(mentioned_known_titles)} cited={sorted(cited_titles)}",
        ),
        _check("answer should include recipe titles from citations", bool(cited_titles) and all(title in answer for title in cited_titles)),
        _check(
            "answer should not include unsupported saved recipe titles",
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
    cited_source_ids = {str(citation.get("source_id") or "") for citation in citations if isinstance(citation, dict)}
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
        _check("answer should include cited source title", bool(cited_titles) and all(title in answer for title in cited_titles)),
        _check(
            "answer should include source id or enough provenance for traceability",
            any(source_id and source_id in answer for source_id in cited_source_ids) or bool(citations),
            f"source_ids={sorted(cited_source_ids)}",
        ),
        _check(
            "answer should not introduce unsupported dataset titles",
            mentioned_known_titles.issubset(cited_titles),
            f"mentioned={sorted(mentioned_known_titles)} cited={sorted(cited_titles)}",
        ),
    ]


def score_meal_plan(payload: dict[str, Any], expected_model: str) -> list[CheckResult]:
    days = payload.get("plan", {}).get("days") or []
    meals = [meal for day in days if isinstance(day, dict) for meal in day.get("meals", []) if isinstance(meal, dict)]
    citations = payload.get("citations") or []
    candidate_ids = set(payload.get("selection", {}).get("matched_recipe_ids") or [])
    requested_slots = int(payload.get("selection", {}).get("requested_slots") or 0)
    meal_ids = {str(meal.get("recipe_id")) for meal in meals if meal.get("recipe_id") is not None}
    citation_by_id = {str(citation.get("recipe_id")): str(citation.get("title") or "") for citation in citations if isinstance(citation, dict)}
    citation_titles = {title for title in citation_by_id.values() if title}
    return [
        _check("provider is OpenAI", payload.get("provider") == "openai"),
        _check("model matches configured OpenAI model", payload.get("model") == expected_model),
        _check("plan has at least one day and one meal", bool(days) and bool(meals)),
        _check("selected recipe is from retrieved saved recipe candidates", bool(meal_ids) and meal_ids.issubset(candidate_ids)),
        _check("expected likely recipe is Lemon Herb White Beans", "1" in candidate_ids or "Lemon Herb White Beans" in citation_titles),
        _check("citations are present", bool(citations)),
        _check("no invented recipe ids", meal_ids.issubset(candidate_ids), f"meal_ids={sorted(meal_ids)} candidate_ids={sorted(candidate_ids)}"),
        _check(
            "selected meal title should match cited recipe title",
            bool(meals) and all(str(meal.get("title") or "") == citation_by_id.get(str(meal.get("recipe_id"))) for meal in meals),
        ),
        _check(
            "reason should refer to user preference",
            bool(meals) and any(term in str(meal.get("reason") or "").lower() for meal in meals for term in ("lemon", "dinner")),
        ),
        _check("selected recipe ids must be a subset of retrieved candidate ids", bool(meal_ids) and meal_ids.issubset(candidate_ids)),
        _check("plan should not include invented extra meals", requested_slots == 0 or len(meals) <= requested_slots),
    ]


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    passed = sum(1 for record in records if record.get("overall_passed") is True)
    total_cost = sum(float(record.get("estimated_cost_usd") or 0.0) for record in records)
    input_tokens = sum(int(record.get("input_tokens") or 0) for record in records)
    output_tokens = sum(int(record.get("output_tokens") or 0) for record in records)
    total_tokens = sum(int(record.get("total_tokens") or 0) for record in records)
    cost_sources = sorted({str(record.get("cost_source")) for record in records if record.get("cost_source")})
    thresholds = evaluate_thresholds(records)
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
        "cost_sources": cost_sources or [COST_SOURCE_UNAVAILABLE],
        "threshold_warnings": thresholds["warnings"],
        "threshold_failures": thresholds["failures"],
    }


def apply_threshold_checks(records: list[dict[str, Any]], env: dict[str, str] | None = None) -> list[dict[str, Any]]:
    thresholds = _threshold_values(env)
    updated: list[dict[str, Any]] = []
    for record in records:
        copy = {**record}
        checks = [*copy.get("checks", [])]
        workflow = str(copy.get("workflow") or "")
        latency = int(copy.get("latency_ms") or 0)
        tokens = int(copy.get("total_tokens") or 0)
        if latency > thresholds["WORKFLOW_LATENCY_MS_FAIL"]:
            checks.append(
                CheckResult(
                    "workflow latency below failure threshold",
                    False,
                    f"{latency}ms > {thresholds['WORKFLOW_LATENCY_MS_FAIL']}ms",
                ).to_dict()
            )
        if tokens > thresholds["WORKFLOW_TOKENS_FAIL"]:
            checks.append(
                CheckResult(
                    "workflow token usage below failure threshold",
                    False,
                    f"{tokens} > {thresholds['WORKFLOW_TOKENS_FAIL']}",
                ).to_dict()
            )
        copy["checks"] = checks
        copy["threshold_warnings"] = _workflow_threshold_warnings(workflow, latency, tokens, thresholds)
        copy["overall_passed"] = bool(copy.get("overall_passed")) and all(check.get("passed") for check in checks)
        updated.append(copy)
    return updated


def evaluate_thresholds(records: list[dict[str, Any]], env: dict[str, str] | None = None) -> dict[str, list[str]]:
    thresholds = _threshold_values(env)
    warnings: list[str] = []
    failures: list[str] = []
    total_latency = sum(int(record.get("latency_ms") or 0) for record in records)
    total_tokens = sum(int(record.get("total_tokens") or 0) for record in records)
    if total_latency > thresholds["TOTAL_LATENCY_MS_WARN"]:
        warnings.append(f"total latency {total_latency}ms exceeds warning threshold {thresholds['TOTAL_LATENCY_MS_WARN']}ms")
    if total_tokens > thresholds["TOTAL_TOKENS_WARN"]:
        warnings.append(f"total tokens {total_tokens} exceeds warning threshold {thresholds['TOTAL_TOKENS_WARN']}")
    for record in records:
        workflow = str(record.get("workflow") or "")
        latency = int(record.get("latency_ms") or 0)
        tokens = int(record.get("total_tokens") or 0)
        warnings.extend(_workflow_threshold_warnings(workflow, latency, tokens, thresholds))
        if latency > thresholds["WORKFLOW_LATENCY_MS_FAIL"]:
            failures.append(f"{workflow} latency {latency}ms exceeds failure threshold {thresholds['WORKFLOW_LATENCY_MS_FAIL']}ms")
        if tokens > thresholds["WORKFLOW_TOKENS_FAIL"]:
            failures.append(f"{workflow} tokens {tokens} exceed failure threshold {thresholds['WORKFLOW_TOKENS_FAIL']}")
    return {"warnings": warnings, "failures": failures}


def estimate_cost(
    usage: dict[str, int] | None,
    *,
    model: str | None,
    input_cost_per_1m: float | None = None,
    output_cost_per_1m: float | None = None,
) -> CostEstimate:
    source = COST_SOURCE_UNAVAILABLE
    if input_cost_per_1m is not None and output_cost_per_1m is not None:
        source = COST_SOURCE_ENV_OVERRIDE
    elif input_cost_per_1m is None and output_cost_per_1m is None:
        default_rates = DEFAULT_MODEL_COST_RATES_PER_1M_TOKENS.get(str(model or ""))
        if default_rates:
            input_cost_per_1m = default_rates["input"]
            output_cost_per_1m = default_rates["output"]
            source = COST_SOURCE_DEFAULT_MODEL_RATE

    if not usage or input_cost_per_1m is None or output_cost_per_1m is None:
        return CostEstimate(None, COST_SOURCE_UNAVAILABLE)

    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cost = (input_tokens / 1_000_000 * input_cost_per_1m) + (output_tokens / 1_000_000 * output_cost_per_1m)
    return CostEstimate(
        estimated_cost_usd=round(cost, 8),
        cost_source=source,
        input_cost_per_1m_tokens=input_cost_per_1m,
        output_cost_per_1m_tokens=output_cost_per_1m,
    )


def estimate_cost_usd(
    usage: dict[str, int] | None,
    *,
    input_cost_per_1m: float | None,
    output_cost_per_1m: float | None,
    model: str | None = None,
) -> float | None:
    return estimate_cost(
        usage,
        model=model,
        input_cost_per_1m=input_cost_per_1m,
        output_cost_per_1m=output_cost_per_1m,
    ).estimated_cost_usd


def assert_no_secret_leaks(value: Any) -> None:
    import json

    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern in text:
            raise AssertionError(f"secret-like pattern leaked: {pattern}")


def assert_no_private_paths(value: Any) -> None:
    import json

    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    private_markers = ("C:\\Users\\", "/Users/", "\\.env", "/.env")
    for marker in private_markers:
        if marker in text:
            raise AssertionError(f"private local path marker leaked: {marker}")


def _check(name: str, passed: bool, detail: str | None = None) -> CheckResult:
    return CheckResult(name=name, passed=bool(passed), detail=detail or ("passed" if passed else "failed"))


def _mentioned_titles(answer: str, titles: tuple[str, ...]) -> set[str]:
    lowered = answer.lower()
    return {title for title in titles if title.lower() in lowered}


def _importer_ingredient_evidence(texts: list[str]) -> set[str]:
    haystack = " ".join(text.lower() for text in texts if text)
    evidence: set[str] = set()
    for canonical, aliases in IMPORTER_INGREDIENT_ALIASES.items():
        if any(_contains_term(haystack, alias) for alias in aliases):
            evidence.add(canonical)
    return evidence


def _mentioned_terms(texts: list[str], terms: tuple[str, ...]) -> set[str]:
    haystack = " ".join(text.lower() for text in texts if text)
    return {term for term in terms if _contains_term(haystack, term)}


def _contains_term(haystack: str, term: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, haystack) is not None


def _generic_field_values(values: list[str]) -> list[str]:
    generic = []
    for value in values:
        lowered = value.strip().lower()
        if lowered in GENERIC_FIELD_VALUES:
            generic.append(value)
    return generic


def _title(value: Any) -> str:
    return str(value.get("title") or "") if isinstance(value, dict) else ""


def _ingredient_names(ingredients: list[Any]) -> list[str]:
    names = []
    for ingredient in ingredients:
        if isinstance(ingredient, dict):
            names.append(str(ingredient.get("name") or "").strip())
        else:
            names.append(str(ingredient).strip())
    return [name for name in names if name]


def _ingredient_quantity_count(ingredients: list[Any]) -> int:
    return sum(1 for ingredient in ingredients if isinstance(ingredient, dict) and str(ingredient.get("quantity") or "").strip())


def _instruction_texts(instructions: list[Any]) -> list[str]:
    texts = []
    for instruction in instructions:
        if isinstance(instruction, dict):
            texts.append(str(instruction.get("text") or "").strip())
        else:
            texts.append(str(instruction).strip())
    return [text for text in texts if text]


def _starts_with_action_verb(text: str) -> bool:
    first_word = text.strip().split(" ", 1)[0].lower().strip(".,:;!")
    return first_word in ACTION_VERBS


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _threshold_values(env: dict[str, str] | None = None) -> dict[str, int]:
    source = env if env is not None else os.environ
    defaults = {
        "TOTAL_LATENCY_MS_WARN": TOTAL_LATENCY_MS_WARN,
        "IMPORTER_LATENCY_MS_WARN": IMPORTER_LATENCY_MS_WARN,
        "WORKFLOW_LATENCY_MS_FAIL": WORKFLOW_LATENCY_MS_FAIL,
        "TOTAL_TOKENS_WARN": TOTAL_TOKENS_WARN,
        "IMPORTER_TOKENS_WARN": IMPORTER_TOKENS_WARN,
        "WORKFLOW_TOKENS_FAIL": WORKFLOW_TOKENS_FAIL,
    }
    return {name: _int_setting(source, name, default) for name, default in defaults.items()}


def _int_setting(source: dict[str, str], name: str, default: int) -> int:
    try:
        return int(source.get(name, default))
    except (TypeError, ValueError):
        return default


def _workflow_threshold_warnings(workflow: str, latency: int, tokens: int, thresholds: dict[str, int]) -> list[str]:
    warnings: list[str] = []
    if workflow == "importer" and latency > thresholds["IMPORTER_LATENCY_MS_WARN"]:
        warnings.append(f"importer latency {latency}ms exceeds warning threshold {thresholds['IMPORTER_LATENCY_MS_WARN']}ms")
    if workflow == "importer" and tokens > thresholds["IMPORTER_TOKENS_WARN"]:
        warnings.append(f"importer tokens {tokens} exceed warning threshold {thresholds['IMPORTER_TOKENS_WARN']}")
    return warnings
