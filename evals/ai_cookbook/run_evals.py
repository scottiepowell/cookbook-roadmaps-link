from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization:",
    ".env",
    "raw provider config",
    "CLOUDFLARE_TUNNEL_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
)

PROVIDER_ENV_KEYS = (
    "AI_PROVIDER",
    "AI_MODEL",
    "AI_MAX_OUTPUT_TOKENS",
    "AI_TIMEOUT_SECONDS",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OPENAI_FALLBACK_MODEL",
    "OPENAI_ENABLE_LIVE_TESTS",
    "RECIPE_DATASET_DIR",
    "RECIPE_DATASET_INDEX_LIMIT",
    "COOKBOOK_DB_PATH",
    "CLOUDFLARE_TUNNEL_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "ai-api"))
    debug_log = _init_debug_log(repo_root)

    evals: list[tuple[str, dict[str, Any]]] = []
    for case in _load_retrieval_relevance_cases():
        evals.append(("retrieval_relevance", case))
    for case in _load_json("dataset_ask_cases.json"):
        evals.append(("dataset_ask", case))
    for case in _load_json("workflow_cases.json"):
        evals.append((case["type"], case))
    for case in _input_quality_cases():
        evals.append(("input_quality", case))
    evals.append(("provider_config", {"name": "provider_config_does_not_leak_fake_secrets"}))

    failures: list[str] = []
    for case_type, case in evals:
        case_name = str(case.get("name") or case.get("id") or case_type)
        started = time.monotonic()
        _log_progress(debug_log, f"starting {case_type}: {case_name}")
        try:
            summary = _run_case(case_type, case)
            elapsed = time.monotonic() - started
            _log_progress(debug_log, f"finished {case_type}: {case_name} elapsed={elapsed:.2f}s")
            if summary:
                print(f"PASS: {summary}")
            else:
                print(f"PASS: {case_name}")
        except AssertionError as exc:
            elapsed = time.monotonic() - started
            _log_progress(debug_log, f"failed {case_type}: {case_name} elapsed={elapsed:.2f}s error={exc}")
            failures.append(f"{case_name}: {exc}")
            print(f"FAIL: {case_name}: {exc}", file=sys.stderr)

    if failures:
        print("Offline evals failed:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    _log_progress(debug_log, f"summary passed={len(evals)} failed=0")
    print(f"Offline evals passed: {len(evals)} cases.")
    return 0


def _init_debug_log(repo_root: Path) -> Path:
    path = repo_root / ".tmp-ai-demo" / "eval-debug" / "run-evals-debug.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("run_evals debug log\n", encoding="utf-8")
    return path


def _log_progress(path: Path, message: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {message}"
    print(f"EVAL: {message}", flush=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _load_json(name: str) -> list[dict[str, Any]]:
    path = Path(__file__).with_name(name)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_retrieval_relevance_cases() -> list[dict[str, Any]]:
    from evals.ai_cookbook.retrieval_eval import load_retrieval_cases

    return load_retrieval_cases()


def _run_case(case_type: str, case: dict[str, Any]) -> str | None:
    if case_type == "dataset_ask":
        _run_dataset_ask_case(case)
    elif case_type == "saved_recipe_ask":
        _run_saved_recipe_ask_case(case)
    elif case_type == "import_recipe":
        _run_import_recipe_case(case)
    elif case_type == "meal_plan":
        _run_meal_plan_case(case)
    elif case_type == "input_quality":
        _run_input_quality_case(case)
    elif case_type == "provider_config":
        _run_provider_config_case()
    elif case_type == "retrieval_relevance":
        return _run_retrieval_relevance_case(case)
    else:
        raise AssertionError(f"unknown eval type {case_type!r}")
    return None


def _run_dataset_ask_case(case: dict[str, Any]) -> None:
    from app.dataset_rag import ask_dataset_recipes
    from app.schemas import DatasetAskRequest

    with _env_guard() as temp_root:
        os.environ["AI_PROVIDER"] = "mock"
        dataset_dir = temp_root / "dataset"
        dataset_dir.mkdir(exist_ok=True)
        csv_path = dataset_dir / "13k-recipes.csv"

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

    payload = response.model_dump()
    serialized = json.dumps(payload, sort_keys=True)

    assert response.provider == case["expect_provider"], f"provider {response.provider!r}"
    assert [citation.source_id for citation in response.citations] == case["expected_source_ids"]
    assert response.retrieval.retrieved_count == len(response.citations), "retrieval count does not match citations"
    assert response.retrieval.matched_result_ids == [citation.id for citation in response.citations]

    for forbidden in case.get("forbidden_source_ids", []):
        assert forbidden not in serialized, f"non-retrieved source id leaked: {forbidden}"

    if case.get("must_include_citations"):
        _assert_dataset_citations(response.citations)
    else:
        assert response.citations == [], "unexpected citations"

    expected_warning = case.get("expected_warning")
    if expected_warning:
        assert expected_warning in response.warnings, f"missing warning {expected_warning!r}"

    _assert_no_secret_leaks(case["name"], payload)


def _run_saved_recipe_ask_case(case: dict[str, Any]) -> None:
    from app.rag import ask_cookbook
    from app.schemas import AskRequest, RecipeDocument

    provider = TextFixtureProvider(case["answer"])
    recipes = [RecipeDocument(**recipe) for recipe in case["recipes"]]
    response = ask_cookbook(
        AskRequest(question=case["question"], limit=case.get("limit", 3)),
        provider=provider,
        recipes=recipes,
    )
    payload = response.model_dump()

    assert response.provider == "fixture"
    assert response.model == "fixture-model"
    assert [citation.recipe_id for citation in response.citations] == case["expected_recipe_ids"]
    assert response.retrieval.retrieved_count == len(response.citations)
    assert response.retrieval.matched_recipe_ids == case["expected_recipe_ids"]
    for citation in response.citations:
        assert citation.recipe_id, "citation missing recipe ID"
        assert citation.title, "citation missing title"
        assert citation.snippet, "citation missing snippet"
    for forbidden_title in case.get("forbidden_prompt_titles", []):
        assert forbidden_title not in provider.last_prompt, f"non-retrieved recipe was sent to provider: {forbidden_title}"
    _assert_no_secret_leaks(case["name"], payload)
    _assert_no_secret_leaks(f"{case['name']} provider prompt", provider.last_prompt)


def _run_import_recipe_case(case: dict[str, Any]) -> None:
    from app.importer import import_recipe_text
    from app.schemas import RecipeImportRequest

    provider = StructuredFixtureProvider(case["provider_data"])
    response = import_recipe_text(
        RecipeImportRequest(text=case["text"], source=case.get("source")),
        provider=provider,
    )
    payload = response.model_dump()

    assert response.provider == "fixture"
    assert response.model == "fixture-model"
    assert response.draft.title == case["expected_title"]
    assert [ingredient.name for ingredient in response.draft.ingredients] == case["expected_ingredients"]
    assert [instruction.step for instruction in response.draft.instructions] == case["expected_steps"]
    assert case["source"] in provider.last_prompt
    _assert_no_secret_leaks(case["name"], payload)
    _assert_no_secret_leaks(f"{case['name']} provider prompt", provider.last_prompt)


def _run_meal_plan_case(case: dict[str, Any]) -> None:
    from app.meal_plan_endpoint import create_meal_plan
    from app.schemas import MealPlanRequest

    with _env_guard() as temp_root:
        db_path = temp_root / "cookbook.sqlite"
        _write_recipe_db(db_path, case["recipes"])
        os.environ["COOKBOOK_DB_PATH"] = str(db_path)
        provider = StructuredFixtureProvider(case["provider_data"])
        response = create_meal_plan(MealPlanRequest(**case["request"]), provider=provider)

    payload = response.model_dump()
    planned_ids = [
        meal.recipe_id
        for day in response.plan.days
        for meal in day.meals
    ]

    assert response.provider == "fixture"
    assert response.model == "fixture-model"
    assert response.selection.matched_recipe_ids == case["expected_recipe_ids"]
    assert [citation.recipe_id for citation in response.citations] == case["expected_recipe_ids"]
    assert planned_ids == case["expected_planned_recipe_ids"]
    assert set(planned_ids).issubset(set(response.selection.matched_recipe_ids))
    for citation in response.citations:
        assert citation.recipe_id, "meal-plan citation missing recipe ID"
        assert citation.title, "meal-plan citation missing title"
        assert citation.snippet, "meal-plan citation missing snippet"
    for forbidden_title in case.get("forbidden_prompt_titles", []):
        assert forbidden_title not in provider.last_prompt, f"non-selected recipe was sent to provider: {forbidden_title}"
    _assert_no_secret_leaks(case["name"], payload)
    _assert_no_secret_leaks(f"{case['name']} provider prompt", provider.last_prompt)


def _run_provider_config_case() -> None:
    from app.config import get_provider_config

    with _env_guard():
        os.environ["OPENAI_API_KEY"] = "sk-fake-offline-eval-secret"
        os.environ["CLOUDFLARE_TUNNEL_TOKEN"] = "fake-cloudflare-token"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "fake-aws-secret"
        os.environ["AWS_ACCESS_KEY_ID"] = "fake-aws-key-id"
        config = get_provider_config()

    payload = {
        name: {"configured": availability.configured}
        for name, availability in config.items()
    }
    assert payload["mock"]["configured"] is True
    assert payload["openai"]["configured"] is True
    _assert_no_secret_leaks("provider config", payload)


def _run_retrieval_relevance_case(case: dict[str, Any]) -> str:
    from evals.ai_cookbook.retrieval_eval import evaluate_retrieval_case

    result = evaluate_retrieval_case(case)
    assert result.passed, result.summary
    return result.summary


def _input_quality_cases() -> list[dict[str, Any]]:
    return [
        {"name": "input_quality_empty_importer_rejected", "workflow": "importer", "input": "", "expected_status": "rejected"},
        {"name": "input_quality_symbol_importer_rejected", "workflow": "importer", "input": "!!!!!", "expected_status": "rejected"},
        {"name": "input_quality_vague_importer_clarifies", "workflow": "importer", "input": "make food", "expected_status": "needs_clarification"},
        {"name": "input_quality_weak_importer_warns", "workflow": "importer", "input": "Lemon beans toast", "expected_status": "weak_but_usable"},
        {"name": "input_quality_empty_saved_question_rejected", "workflow": "ask", "input": "", "expected_status": "rejected"},
        {"name": "input_quality_vague_meal_plan_clarifies", "workflow": "meal_plan", "input": "plan dinner", "expected_status": "needs_clarification"},
        {"name": "input_quality_nonsense_dataset_search_rejected", "workflow": "dataset_search", "input": "??????", "expected_status": "rejected"},
        {"name": "input_quality_valid_classifier_ready", "workflow": "classifier", "input": "What saved recipe uses lemon?", "expected_status": "ready"},
    ]


def _run_input_quality_case(case: dict[str, Any]) -> None:
    workflow = case["workflow"]
    expected_status = case["expected_status"]
    if workflow == "importer":
        from app.importer import import_recipe_text
        from app.schemas import RecipeImportRequest

        provider = (
            StructuredFixtureProvider(
                {
                    "title": "Lemon Beans Toast",
                    "description": "Lemon beans on toast.",
                    "ingredients": [{"name": "lemon"}, {"name": "beans"}, {"name": "toast"}],
                    "instructions": [{"step": 1, "text": "Warm beans."}],
                    "notes": "Quantities are unspecified.",
                }
            )
            if expected_status == "weak_but_usable"
            else FailingProvider()
        )
        response = import_recipe_text(RecipeImportRequest(text=case["input"]), provider=provider)
        assert response.input_quality is not None
        assert response.input_quality.status == expected_status
        if expected_status in {"rejected", "needs_clarification"}:
            assert response.provider == "none", "provider was called for deterministic importer input-quality case"
        if expected_status == "weak_but_usable":
            assert response.warnings, "weak importer input should include warnings"
    elif workflow == "ask":
        from app.rag import ask_cookbook
        from app.schemas import AskRequest

        response = ask_cookbook(AskRequest(question=case["input"]), provider=FailingProvider(), recipes=[])
        assert response.input_quality is not None
        assert response.input_quality.status == expected_status
        assert response.provider == "none", "provider was called for deterministic saved-recipe input-quality case"
    elif workflow == "meal_plan":
        from app.meal_plan_endpoint import create_meal_plan
        from app.schemas import MealPlanRequest

        response = create_meal_plan(MealPlanRequest(preferences=case["input"]), provider=FailingProvider())
        assert response.input_quality is not None
        assert response.input_quality.status == expected_status
        assert response.provider == "none", "provider was called for deterministic meal-plan input-quality case"
    elif workflow == "dataset_search":
        from app.dataset_retrieval import search_dataset_recipes

        with _env_guard():
            os.environ["RECIPE_DATASET_DIR"] = "missing-dataset-for-input-quality"
            response = search_dataset_recipes(case["input"], dataset_limit=10)
        assert response.input_quality is not None
        assert response.input_quality.status == expected_status
        assert response.index.build_metadata["mode"] == "input_quality"
    elif workflow == "classifier":
        from app.input_quality import classify_question_input

        response = classify_question_input(case["input"])
        assert response.status == expected_status
    else:
        raise AssertionError(f"unknown input-quality workflow {workflow!r}")

    payload = response.model_dump() if hasattr(response, "model_dump") else response.to_dict()
    _assert_no_secret_leaks(case["name"], payload)


def _assert_dataset_citations(citations: list[Any]) -> None:
    assert citations, "missing citations"
    for citation in citations:
        assert citation.id, "citation missing result ID"
        assert citation.source_id, "citation missing source ID"
        assert citation.title, "citation missing title"
        assert citation.snippet, "citation missing snippet"
        assert citation.provenance.dataset == "Food Ingredients and Recipes Dataset with Images"
        assert citation.provenance.license == "CC BY-SA 3.0"
        assert citation.provenance.source_url.startswith("https://www.kaggle.com/")
        assert citation.provenance.source_file, "citation missing source file"
        assert citation.provenance.source_id == citation.source_id


def _assert_no_secret_leaks(label: str, payload: Any) -> None:
    serialized = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        assert pattern not in serialized, f"{label} leaked secret-like pattern: {pattern}"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["recipe_id", "title", "ingredients", "instructions", "cuisine"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_recipe_db(path: Path, rows: list[dict[str, Any]]) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT,
            tags TEXT,
            source_url TEXT
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["id"],
                row["title"],
                row.get("description"),
                json.dumps(row.get("ingredients", [])),
                "\n".join(row.get("instructions", [])),
                "\n".join(row.get("tags", [])),
                row.get("source_url"),
            )
            for row in rows
        ],
    )
    connection.commit()
    connection.close()


class _env_guard:
    def __init__(self) -> None:
        self._old_env: dict[str, str | None] = {}
        self._base_temp_root = Path(__file__).resolve().parents[2] / ".tmp-pytest-evals"
        self._temp_root = self._base_temp_root / f"run-{uuid.uuid4().hex}"

    def __enter__(self) -> Path:
        self._old_env = {key: os.environ.get(key) for key in PROVIDER_ENV_KEYS}
        self._temp_root.mkdir(parents=True, exist_ok=True)
        return self._temp_root

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TextFixtureProvider:
    name = "fixture"
    model = "fixture-model"

    def __init__(self, text: str) -> None:
        self.text = text
        self.last_prompt = ""

    def generate_text(self, request: Any) -> Any:
        from app.providers.base import LLMResponse

        self.last_prompt = request.prompt
        return LLMResponse(
            text=self.text,
            provider=self.name,
            model=self.model,
            usage={"input_tokens": len(request.prompt.split()), "output_tokens": len(self.text.split())},
        )

    def generate_structured(self, request: Any) -> Any:
        raise AssertionError("Text fixture provider does not support structured generation.")


class StructuredFixtureProvider:
    name = "fixture"
    model = "fixture-model"

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.last_prompt = ""

    def generate_text(self, request: Any) -> Any:
        raise AssertionError("Structured fixture provider does not support text generation.")

    def generate_structured(self, request: Any) -> Any:
        from app.providers.base import StructuredLLMResponse

        self.last_prompt = request.prompt
        return StructuredLLMResponse(
            data=self.data,
            provider=self.name,
            model=self.model,
            usage={"input_tokens": len(request.prompt.split()), "output_tokens": len(self.data)},
        )


class FailingProvider:
    name = "failing"
    model = "none"

    def generate_text(self, request: Any) -> Any:
        raise AssertionError("provider should not be called")

    def generate_structured(self, request: Any) -> Any:
        raise AssertionError("provider should not be called")


if __name__ == "__main__":
    raise SystemExit(main())
