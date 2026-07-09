import csv
import json
import uuid
from pathlib import Path

from evals.ai_cookbook import retrieval_eval


def test_retrieval_eval_cases_load_and_are_named():
    cases = retrieval_eval.load_retrieval_cases()

    assert [case["id"] for case in cases] == [
        "cheesecake_baked",
        "cheesecake_no_bake",
        "carbonara_classic",
        "omelet_basic",
        "chicken_rice_casserole",
        "omelette_alias",
        "no_bake_cheesecake_space",
        "no_bake_cheesecake_hyphen",
        "graham_crackers_cheesecake",
        "parmigiano_reggiano_carbonara",
        "cream_of_chicken_soup_casserole",
    ]
    assert all(case["name"] == case["id"] for case in cases)
    assert all(case["top_k"] == 3 for case in cases)


def test_retrieval_eval_harness_scores_fixture_cases():
    cases = retrieval_eval.load_retrieval_cases()

    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    dataset_root = base / f"retrieval-harness-{uuid.uuid4().hex}"
    dataset_root.mkdir(parents=True, exist_ok=True)
    results = [retrieval_eval.evaluate_retrieval_case(case, dataset_dir=dataset_root / case["id"]) for case in cases]

    assert all(result.passed for result in results)
    assert all(result.document_count == 14 for result in results)
    assert all(result.dataset_limit == 5000 for result in results)
    assert all(result.warning_expected is False for result in results)
    assert all(result.warning_observed is False for result in results)
    assert all(result.support_level == "strong" for result in results)
    assert all(result.support_expected == "strong" for result in results)
    assert results[0].top1_title == "Classic Baked Cheesecake"
    assert results[1].top1_title == "No-Bake Cheesecake Bars"
    assert results[2].top1_title == "Spaghetti Carbonara"
    assert results[3].top1_title == "Cheese Omelet"
    assert results[4].top1_title == "Chicken and Rice Casserole"
    assert results[5].top1_title == "Cheese Omelet"
    assert results[6].top1_title == "No-Bake Cheesecake Bars"
    assert results[7].top1_title == "No-Bake Cheesecake Bars"
    assert results[8].top1_title == "No-Bake Cheesecake Bars"
    assert results[9].top1_title == "Spaghetti Carbonara"
    assert results[10].top1_title == "Chicken and Rice Casserole"
    assert all(result.relevant_in_top_k >= int(case["min_relevant_in_top_k"]) for result, case in zip(results, cases, strict=True))
    assert all("top3_relevant=" in result.summary for result in results)
    assert all("relevance=" in result.summary for result in results)


def test_retrieval_eval_harness_reports_weak_warning_for_distractors_only(monkeypatch):
    def write_distractor_dataset(root: Path) -> dict[str, dict[str, str]]:
        root.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                "recipe_id": "crumble-1",
                "title": "Apple Crumble with Vanilla Ice Cream",
                "ingredients": "apples; sugar; butter; oats; cream",
                "instructions": "Prep apples; Mix topping; Bake until bubbly; Serve with ice cream",
                "cuisine": "dessert",
            },
            {
                "recipe_id": "pear-1",
                "title": "Pear Tart with Creme Fraiche",
                "ingredients": "pears; sugar; butter; flour; creme fraiche",
                "instructions": "Prepare crust; Arrange pears; Bake; Cool before serving",
                "cuisine": "dessert",
            },
        ]
        with (root / "13k-recipes.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["recipe_id", "title", "ingredients", "instructions", "cuisine"])
            writer.writeheader()
            writer.writerows(rows)
        (root / retrieval_eval.DEMO_DATASET_MARKER).write_text(
            json.dumps({"kind": "cookbook-ai-demo-fixture", "purpose": "distractor-only-test"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {row["recipe_id"]: row for row in rows}

    monkeypatch.setattr(retrieval_eval, "write_retrieval_fixture_dataset", write_distractor_dataset)
    case = {
        "id": "cheesecake_warning",
        "name": "cheesecake_warning",
        "query": "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill",
        "required_anchors": ["cheesecake", "cream cheese", "graham cracker crust", "bake", "chill"],
        "preferred_title_terms": ["cheesecake"],
        "preferred_ingredient_terms": ["cream cheese", "graham crackers", "eggs"],
        "preferred_instruction_terms": ["beat", "bake", "chill"],
        "negative_title_terms": ["crumble", "pear"],
        "negative_generic_terms": ["dessert", "cream", "sugar"],
        "expected_relevance_min": "strong",
        "expected_support_level": "weak",
        "min_relevant_in_top_k": 2,
        "top_k": 2,
        "expect_warning": True,
    }

    base = Path(".tmp-pytest-evals")
    base.mkdir(exist_ok=True)
    dataset_root = base / f"retrieval-harness-{uuid.uuid4().hex}"
    dataset_root.mkdir(parents=True, exist_ok=True)
    result = retrieval_eval.evaluate_retrieval_case(case, dataset_dir=dataset_root)

    assert result.warning_observed is True
    assert result.passed is False
    assert "warning expected=True observed=True" not in result.summary
    assert "warning" in result.summary
    assert result.relevance_category == "weak"
    assert result.support_level == "weak"


def test_relevance_category_classifier_is_deterministic():
    assert retrieval_eval.classify_relevance_category(0) == "weak"
    assert retrieval_eval.classify_relevance_category(4) == "moderate"
    assert retrieval_eval.classify_relevance_category(8) == "strong"
