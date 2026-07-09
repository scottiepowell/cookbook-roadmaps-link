from __future__ import annotations

import csv
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.dataset_retrieval import search_dataset_recipes
from app.demo_data import DEMO_DATASET_MARKER
from app.rag_support_policy import assess_importer_rag_support


RETRIEVAL_CASES_PATH = Path(__file__).with_name("retrieval_cases.yaml")
CATEGORY_ORDER = {"none": -1, "weak": 0, "moderate": 1, "strong": 2}
MATERIAL_RELEVANCE_MIN = "moderate"


@dataclass(frozen=True)
class RetrievalEvalResult:
    case_id: str
    passed: bool
    summary: str
    top1_title: str
    top_k_titles: list[str]
    relevant_in_top_k: int
    top_k: int
    anchor_coverage: str
    negative_drift_count: int
    relevance_category: str
    warning_expected: bool
    warning_observed: bool
    support_level: str
    support_expected: str
    document_count: int
    dataset_limit: int


def load_retrieval_cases(path: Path | None = None) -> list[dict[str, Any]]:
    case_path = path or RETRIEVAL_CASES_PATH
    cases = json.loads(case_path.read_text(encoding="utf-8"))
    for case in cases:
        case.setdefault("name", case.get("id"))
        case.setdefault("top_k", 3)
        case.setdefault("dataset_limit", 5000)
        case.setdefault("expected_relevance_min", "strong")
        case.setdefault("expected_support_level", case.get("expected_relevance_min", "strong"))
        case.setdefault("min_relevant_in_top_k", 2)
        case.setdefault("expect_warning", False)
    return cases


def write_retrieval_fixture_dataset(root: Path) -> dict[str, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    rows = _retrieval_fixture_rows()
    csv_path = root / "13k-recipes.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["recipe_id", "title", "ingredients", "instructions", "cuisine"])
        writer.writeheader()
        writer.writerows(rows)
    (root / DEMO_DATASET_MARKER).write_text(
        json.dumps({"kind": "cookbook-ai-demo-fixture", "purpose": "retrieval-eval-fixture"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {row["recipe_id"]: row for row in rows}


def evaluate_retrieval_case(case: dict[str, Any], dataset_dir: Path | None = None) -> RetrievalEvalResult:
    case_id = str(case.get("id") or case.get("name") or "retrieval_case")
    top_k = int(case.get("top_k", 3))
    dataset_limit = int(case.get("dataset_limit", 5000))
    expected_category = str(case.get("expected_relevance_min", "strong"))
    expected_support_level = str(case.get("expected_support_level", expected_category))
    min_relevant_in_top_k = int(case.get("min_relevant_in_top_k", 2))
    expected_warning = bool(case.get("expect_warning", False))

    with _dataset_workspace(dataset_dir) as root:
        record_map = write_retrieval_fixture_dataset(root)
        previous_dataset_dir = os.environ.get("RECIPE_DATASET_DIR")
        os.environ["RECIPE_DATASET_DIR"] = str(root)
        try:
            response = search_dataset_recipes(str(case["query"]), limit=top_k, dataset_limit=dataset_limit)
        finally:
            if previous_dataset_dir is None:
                os.environ.pop("RECIPE_DATASET_DIR", None)
            else:
                os.environ["RECIPE_DATASET_DIR"] = previous_dataset_dir

    results = response.results[:top_k]
    top_titles = [result.title for result in results]
    scored = [_score_result(result, record_map.get(result.source_id, {}), case) for result in results]
    top1_score = scored[0] if scored else None
    top1_record = record_map.get(results[0].source_id, {}) if results else {}
    anchor_coverage = _anchor_coverage(top1_record, case.get("required_anchors", []))
    negative_drift_count = sum(
        1
        for item in scored
        if item["generic_drift"] or item["negative_title_hits"] > 0 or item["negative_generic_hits"] > 0
    )
    relevant_in_top_k = sum(1 for item in scored if CATEGORY_ORDER[item["category"]] >= CATEGORY_ORDER[MATERIAL_RELEVANCE_MIN])
    top1_category = top1_score["category"] if top1_score is not None else "weak"
    support = assess_importer_rag_support(
        relevance_category=top1_category if top_titles else "unavailable",
        retrieved_count=len(results),
        citation_count=len(results),
        packed_count=min(len(results), top_k),
        weak_examples_included=top1_category == "weak",
        matched_result_scores=[result.score for result in results],
        warning="Retrieved examples were weak matches; recipe draft was primarily shaped by user-provided notes and general recipe structure." if top1_category == "weak" else None,
        top_k_relevant_count=relevant_in_top_k,
    )
    warning_observed = (
        top1_category == "weak"
        or CATEGORY_ORDER[top1_category] < CATEGORY_ORDER[expected_category]
        or relevant_in_top_k < min_relevant_in_top_k
    )

    passed, reason = _evaluate_case(
        case=case,
        top1_title=top_titles[0] if top_titles else "none",
        top1_category=top1_category,
        relevant_in_top_k=relevant_in_top_k,
        anchor_coverage=anchor_coverage,
        negative_drift_count=negative_drift_count,
        support_level=support.support_level,
        warning_observed=warning_observed,
    )
    summary = _format_summary(
        case_id=case_id,
        top1_title=top_titles[0] if top_titles else "none",
        relevant_in_top_k=relevant_in_top_k,
        top_k=top_k,
        category=top1_category,
        anchor_coverage=anchor_coverage,
        negative_drift_count=negative_drift_count,
        support_level=support.support_level,
        warning_observed=warning_observed,
    )
    if not passed:
        summary = f"{summary}; {reason}"

    return RetrievalEvalResult(
        case_id=case_id,
        passed=passed,
        summary=summary,
        top1_title=top_titles[0] if top_titles else "none",
        top_k_titles=top_titles,
        relevant_in_top_k=relevant_in_top_k,
        top_k=top_k,
        anchor_coverage=anchor_coverage,
        negative_drift_count=negative_drift_count,
        relevance_category=top1_category,
        warning_expected=expected_warning,
        warning_observed=warning_observed,
        support_level=support.support_level,
        support_expected=expected_support_level,
        document_count=response.index.document_count,
        dataset_limit=dataset_limit,
    )


def classify_relevance_category(score: int) -> str:
    if score >= 8:
        return "strong"
    if score >= 4:
        return "moderate"
    return "weak"


def _evaluate_case(
    *,
    case: dict[str, Any],
    top1_title: str,
    top1_category: str,
    relevant_in_top_k: int,
    anchor_coverage: str,
    negative_drift_count: int,
    support_level: str,
    warning_observed: bool,
) -> tuple[bool, str]:
    errors: list[str] = []
    expected_title_terms = [str(term).lower() for term in case.get("preferred_title_terms", [])]
    expected_category = str(case.get("expected_relevance_min", "strong"))
    expected_support_level = str(case.get("expected_support_level", expected_category))
    min_relevant_in_top_k = int(case.get("min_relevant_in_top_k", 2))
    required_anchor_count = len(case.get("required_anchors", []))
    expect_warning = bool(case.get("expect_warning", False))
    negative_title_terms = [str(term).lower() for term in case.get("negative_title_terms", [])]

    if not top1_title or top1_title == "none":
        errors.append("no retrieval results returned")
        return False, "; ".join(errors)

    if expected_title_terms and not any(term in top1_title.lower() for term in expected_title_terms):
        errors.append(f"top1={top1_title!r} expected title term {'/'.join(expected_title_terms)}")

    if CATEGORY_ORDER[top1_category] < CATEGORY_ORDER[expected_category]:
        errors.append(f"relevance={top1_category} expected>={expected_category}")

    if relevant_in_top_k < min_relevant_in_top_k:
        errors.append(f"top{case.get('top_k', 3)}_relevant={relevant_in_top_k}/{case.get('top_k', 3)}")

    if required_anchor_count and anchor_coverage.startswith("0/"):
        errors.append(f"anchors={anchor_coverage}")

    if expect_warning != warning_observed:
        errors.append(f"warning expected={expect_warning} observed={warning_observed}")

    if negative_title_terms and any(term in top1_title.lower() for term in negative_title_terms):
        errors.append(f"top1 matched negative title term {'/'.join(negative_title_terms)}")

    if case.get("max_generic_drift") is not None and negative_drift_count > int(case["max_generic_drift"]):
        errors.append(f"generic_drift={negative_drift_count} > {case['max_generic_drift']}")

    if CATEGORY_ORDER[support_level] < CATEGORY_ORDER[expected_support_level]:
        errors.append(f"support={support_level} expected>={expected_support_level}")

    return not errors, "; ".join(errors)


def _format_summary(
    *,
    case_id: str,
    top1_title: str,
    relevant_in_top_k: int,
    top_k: int,
    category: str,
    anchor_coverage: str,
    negative_drift_count: int,
    support_level: str,
    warning_observed: bool,
) -> str:
    warning_state = "warning" if warning_observed else "no-warning"
    return (
        f"{case_id} top1={top1_title} top{top_k}_relevant={relevant_in_top_k}/{top_k} "
        f"relevance={category} support={support_level} anchors={anchor_coverage} drift={negative_drift_count} {warning_state}"
    )


def _score_result(result: Any, record: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    title = _normalized_text(str(record.get("title") or result.title or ""))
    ingredients = _normalized_text(str(record.get("ingredients") or ""))
    instructions = _normalized_text(str(record.get("instructions") or ""))
    tags = _normalized_text(" ".join(record.get("tags") or []))
    combined = " ".join(part for part in (title, ingredients, instructions, tags) if part)

    required_anchors = [str(anchor).lower() for anchor in case.get("required_anchors", [])]
    preferred_title_terms = [str(term).lower() for term in case.get("preferred_title_terms", [])]
    preferred_ingredient_terms = [str(term).lower() for term in case.get("preferred_ingredient_terms", [])]
    preferred_instruction_terms = [str(term).lower() for term in case.get("preferred_instruction_terms", [])]
    negative_title_terms = [str(term).lower() for term in case.get("negative_title_terms", [])]
    negative_generic_terms = [str(term).lower() for term in case.get("negative_generic_terms", [])]

    anchor_hits = sum(1 for term in required_anchors if _contains_term(combined, term))
    title_hits = sum(1 for term in preferred_title_terms if _contains_term(title, term))
    ingredient_hits = sum(1 for term in preferred_ingredient_terms if _contains_term(ingredients, term))
    instruction_hits = sum(1 for term in preferred_instruction_terms if _contains_term(instructions, term))
    negative_title_hits = sum(1 for term in negative_title_terms if _contains_term(title, term))
    negative_generic_hits = sum(1 for term in negative_generic_terms if _contains_term(combined, term))

    score = (anchor_hits * 3) + (title_hits * 4) + (ingredient_hits * 2) + instruction_hits
    score -= negative_title_hits * 4
    score -= negative_generic_hits
    category = classify_relevance_category(score)
    generic_drift = bool(negative_generic_hits and not (anchor_hits or title_hits or ingredient_hits or instruction_hits))
    return {
        "score": score,
        "category": category,
        "anchor_hits": anchor_hits,
        "title_hits": title_hits,
        "ingredient_hits": ingredient_hits,
        "instruction_hits": instruction_hits,
        "negative_title_hits": negative_title_hits,
        "negative_generic_hits": negative_generic_hits,
        "generic_drift": generic_drift,
    }


def _anchor_coverage(record: dict[str, Any], required_anchors: list[Any]) -> str:
    if not required_anchors:
        return "0/0"
    combined = _normalized_text(
        " ".join(
            str(part)
            for part in (
                record.get("title") or "",
                record.get("ingredients") or "",
                record.get("instructions") or "",
                " ".join(record.get("tags") or []),
            )
        )
    )
    matched = sum(1 for anchor in required_anchors if _contains_term(combined, str(anchor).lower()))
    return f"{matched}/{len(required_anchors)}"


def _dataset_workspace(dataset_dir: Path | None = None):
    if dataset_dir is not None:
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return _TempWorkspace(dataset_dir)
    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    path = base / f"retrieval-eval-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return _TempWorkspace(path)


@dataclass
class _TempWorkspace:
    path: Path

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None


def _retrieval_fixture_rows() -> list[dict[str, str]]:
    return [
        {
            "recipe_id": "cheesecake-baked-1",
            "title": "Classic Baked Cheesecake",
            "ingredients": "cream cheese; sugar; eggs; vanilla; graham crackers",
            "instructions": "Preheat oven; Press crust into pan; Beat filling; Bake until set; Cool and chill",
            "cuisine": "dessert",
        },
        {
            "recipe_id": "cheesecake-nobake-1",
            "title": "No-Bake Cheesecake Bars",
            "ingredients": "cream cheese; sugar; whipped cream; graham crackers; vanilla",
            "instructions": "Press crust into pan; Mix filling; Chill until set; Slice and serve",
            "cuisine": "dessert",
        },
        {
            "recipe_id": "cheesecake-frosting-1",
            "title": "Cream Cheese Frosting",
            "ingredients": "cream cheese; butter; sugar; vanilla",
            "instructions": "Beat cream cheese and butter; Add sugar; Mix until fluffy",
            "cuisine": "dessert",
        },
        {
            "recipe_id": "cheesecake-crumble-1",
            "title": "Apple Crumble with Vanilla Ice Cream",
            "ingredients": "apples; sugar; butter; oats; cream",
            "instructions": "Prep apples; Mix topping; Bake until bubbly; Serve with ice cream",
            "cuisine": "dessert",
        },
        {
            "recipe_id": "cheesecake-pear-1",
            "title": "Pear Tart with Creme Fraiche",
            "ingredients": "pears; sugar; butter; flour; creme fraiche",
            "instructions": "Prepare crust; Arrange pears; Bake; Cool before serving",
            "cuisine": "dessert",
        },
        {
            "recipe_id": "carbonara-1",
            "title": "Spaghetti Carbonara",
            "ingredients": "spaghetti; eggs; parmesan; pancetta; black pepper",
            "instructions": "Boil pasta; Whisk eggs and parmesan; Toss off heat with pancetta and pasta water",
            "cuisine": "dinner",
        },
        {
            "recipe_id": "carbonara-cream-1",
            "title": "Creamy Garlic Pasta",
            "ingredients": "pasta; cream; parmesan; garlic; butter",
            "instructions": "Boil pasta; Simmer cream sauce; Toss together and serve",
            "cuisine": "dinner",
        },
        {
            "recipe_id": "carbonara-aglio-1",
            "title": "Aglio e Olio Pasta",
            "ingredients": "spaghetti; garlic; olive oil; parsley",
            "instructions": "Boil spaghetti; Toss with garlic and oil; Finish with parsley",
            "cuisine": "dinner",
        },
        {
            "recipe_id": "omelet-1",
            "title": "Cheese Omelet",
            "ingredients": "eggs; cheese; butter; onion",
            "instructions": "Beat the eggs; Cook in butter; Add cheese and onions; Fold and serve",
            "cuisine": "breakfast",
        },
        {
            "recipe_id": "omelet-sandwich-1",
            "title": "Breakfast Sandwich",
            "ingredients": "egg; cheese; bread; bacon",
            "instructions": "Cook the egg; Assemble on toast; Serve hot",
            "cuisine": "breakfast",
        },
        {
            "recipe_id": "omelet-skilletpie-1",
            "title": "Skillet Pie",
            "ingredients": "eggs; cheese; pie crust; milk",
            "instructions": "Mix filling; Bake in skillet; Cool before slicing",
            "cuisine": "breakfast",
        },
        {
            "recipe_id": "casserole-1",
            "title": "Chicken and Rice Casserole",
            "ingredients": "chicken; rice; cream of chicken soup; cheese; onion",
            "instructions": "Preheat oven; Combine chicken, rice, cream of chicken soup, and cheese; Bake until hot and chicken reaches 165 F",
            "cuisine": "dinner",
        },
        {
            "recipe_id": "casserole-chicken-1",
            "title": "Lemon Chicken Skillet",
            "ingredients": "chicken; lemon; butter; garlic",
            "instructions": "Cook chicken in a skillet; Add lemon and butter; Serve",
            "cuisine": "dinner",
        },
        {
            "recipe_id": "casserole-rice-1",
            "title": "Rice Pilaf",
            "ingredients": "rice; onion; stock; butter",
            "instructions": "Toast rice; Simmer in stock; Fluff and serve",
            "cuisine": "side",
        },
    ]


def _normalized_text(value: str) -> str:
    return " ".join(value.lower().split())


def _contains_term(haystack: str, term: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])"
    return re.search(pattern, haystack) is not None
