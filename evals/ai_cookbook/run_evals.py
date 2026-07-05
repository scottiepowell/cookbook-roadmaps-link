from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any


SECRET_PATTERNS = ("OPENAI_API_KEY", "sk-", "Authorization:", ".env", "raw provider config")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "ai-api"))

    cases_path = Path(__file__).with_name("dataset_ask_cases.json")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))

    failures: list[str] = []
    for case in cases:
        try:
            _run_case(case)
            print(f"PASS: {case['name']}")
        except AssertionError as exc:
            failures.append(f"{case['name']}: {exc}")
            print(f"FAIL: {case['name']}: {exc}", file=sys.stderr)

    if failures:
        print("Offline evals failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(f"Offline evals passed: {len(cases)} cases.")
    return 0


def _run_case(case: dict[str, Any]) -> None:
    from app.dataset_rag import ask_dataset_recipes
    from app.schemas import DatasetAskRequest

    old_env = {key: os.environ.get(key) for key in ("AI_PROVIDER", "RECIPE_DATASET_DIR")}
    os.environ["AI_PROVIDER"] = "mock"

    temp_root = Path(__file__).resolve().parents[2] / ".tmp-pytest-evals"
    temp_root.mkdir(exist_ok=True)
    dataset_dir = temp_root
    csv_path = dataset_dir / "13k-recipes.csv"
    if csv_path.exists():
        csv_path.unlink()

    if case.get("missing_dataset"):
        os.environ["RECIPE_DATASET_DIR"] = str(dataset_dir / "missing")
    else:
        _write_csv(csv_path, case.get("rows", []))
        os.environ["RECIPE_DATASET_DIR"] = str(dataset_dir)

    response = ask_dataset_recipes(
        DatasetAskRequest(
            question=case["question"],
            limit=case.get("limit", 3),
            dataset_limit=case.get("dataset_limit", 10),
        )
    )

    _restore_env(old_env)
    payload = response.model_dump()
    serialized = json.dumps(payload, sort_keys=True)

    assert response.provider == case["expect_provider"], f"provider {response.provider!r}"
    assert [citation.source_id for citation in response.citations] == case["expected_source_ids"]

    for forbidden in case.get("forbidden_source_ids", []):
        assert forbidden not in serialized, f"non-retrieved source id leaked: {forbidden}"

    if case.get("must_include_citations"):
        assert response.citations, "missing citations"
        for citation in response.citations:
            assert citation.provenance.dataset == "Food Ingredients and Recipes Dataset with Images"
            assert citation.provenance.license == "CC BY-SA 3.0"
            assert citation.provenance.source_url.startswith("https://www.kaggle.com/")
            assert citation.source_id, "citation missing source ID"
            assert citation.title, "citation missing title"
    else:
        assert response.citations == [], "unexpected citations"

    expected_warning = case.get("expected_warning")
    if expected_warning:
        assert expected_warning in response.warnings, f"missing warning {expected_warning!r}"

    for pattern in SECRET_PATTERNS:
        assert pattern not in serialized, f"secret-like pattern leaked: {pattern}"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["recipe_id", "title", "ingredients", "instructions", "cuisine"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _restore_env(old_env: dict[str, str | None]) -> None:
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
