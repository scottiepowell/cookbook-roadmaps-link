from __future__ import annotations

import csv
import json
import os
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MAX_BUDGET_CENTS = 25
MAX_LIVE_CALLS = 4
DEFAULT_MAX_OUTPUT_TOKENS = "200"
MAX_OUTPUT_TOKENS_LIMIT = 300
DEFAULT_BUDGET_SESSION_ID = "live-openai-smoke"
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


@dataclass(frozen=True)
class GuardResult:
    should_run: bool
    exit_code: int
    message: str
    budget_cents: int | None = None


@dataclass
class SmokeSummary:
    provider: str
    model: str
    live_calls: int = 0
    estimated_usage_tokens: int = 0
    workflows: list[str] = field(default_factory=list)

    def record(self, workflow: str, payload: Any) -> None:
        self.live_calls += 1
        self.workflows.append(workflow)
        usage = getattr(payload, "usage", None)
        if isinstance(usage, dict):
            self.estimated_usage_tokens += int(usage.get("total_tokens") or 0)
            if "total_tokens" not in usage:
                self.estimated_usage_tokens += int(usage.get("input_tokens") or 0)
                self.estimated_usage_tokens += int(usage.get("output_tokens") or 0)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "ai-api"))

    os.environ.setdefault("AI_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS)
    os.environ.setdefault("AI_PROVIDER_BUDGET_SESSION_ID", DEFAULT_BUDGET_SESSION_ID)
    guard = evaluate_live_guard(os.environ)
    if not guard.should_run:
        print(guard.message)
        return guard.exit_code

    from app.config import get_ai_settings, get_provider_config
    from app.providers import get_provider
    from app.providers.errors import ProviderConfigError, ProviderError

    try:
        settings = get_ai_settings()
        provider = get_provider(settings)
    except ProviderConfigError as exc:
        return _fail_safely(f"provider configuration failed before live calls: {_safe_error(exc)}")

    config_payload = {
        "provider": settings.provider,
        "configured": get_provider_config()["openai"].configured,
        "model": settings.openai_model,
        "fallback_model": settings.openai_fallback_model,
        "max_output_tokens": settings.max_output_tokens,
    }
    _assert_no_secret_leaks(config_payload)
    if settings.max_output_tokens > MAX_OUTPUT_TOKENS_LIMIT:
        return _fail_safely(
            f"AI_MAX_OUTPUT_TOKENS must be {MAX_OUTPUT_TOKENS_LIMIT} or lower for live smoke tests."
        )

    summary = SmokeSummary(provider=provider.name, model=provider.model)
    try:
        with _make_smoke_temp_dir() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            _run_importer_smoke(provider, summary)
            _assert_call_budget(summary)
            _run_saved_recipe_ask_smoke(provider, summary)
            _assert_call_budget(summary)
            _run_dataset_ask_smoke(provider, summary, temp_dir)
            _assert_call_budget(summary)
            _run_meal_plan_smoke(provider, summary, temp_dir)
            _assert_call_budget(summary)
    except ProviderError as exc:
        return _fail_safely(
            "live OpenAI provider call failed. Confirm the configured model is available, "
            f"the account has quota, and rate limits are clear. Detail: {_safe_error(exc)}"
        )
    except AssertionError as exc:
        return _fail_safely(f"live smoke assertion failed: {_safe_error(exc)}")

    result = {
        "provider": summary.provider,
        "model": summary.model,
        "live_calls": summary.live_calls,
        "estimated_usage_tokens": summary.estimated_usage_tokens,
        "workflows": summary.workflows,
        "budget_cents": guard.budget_cents,
        "status": "passed",
    }
    _assert_no_secret_leaks(result)
    print(_compact_summary(result))
    return 0


def evaluate_live_guard(env: dict[str, str]) -> GuardResult:
    if env.get("OPENAI_ENABLE_LIVE_TESTS") != "true":
        return GuardResult(False, 0, "SKIP: live OpenAI smoke tests are disabled.")
    if env.get("AI_PROVIDER") != "openai":
        return GuardResult(False, 0, "SKIP: AI_PROVIDER is not openai.")
    if not env.get("OPENAI_API_KEY", "").strip():
        return GuardResult(False, 0, "SKIP: OpenAI API key is not configured.")
    if env.get("AI_PROVIDER_CALLS_ENABLED") == "false" or env.get("AI_PROVIDER_GLOBAL_DISABLE") == "true":
        return GuardResult(False, 0, "SKIP: provider calls are disabled by budget settings.")

    raw_budget = env.get("OPENAI_LIVE_TEST_BUDGET_CENTS")
    try:
        budget = int(raw_budget or "")
    except ValueError:
        return GuardResult(False, 2, "FAIL: live budget cap is missing or invalid.")
    if budget < 1 or budget > MAX_BUDGET_CENTS:
        return GuardResult(False, 2, f"FAIL: live budget cap must be between 1 and {MAX_BUDGET_CENTS} cents.")

    raw_tokens = env.get("AI_MAX_OUTPUT_TOKENS", DEFAULT_MAX_OUTPUT_TOKENS)
    try:
        max_tokens = int(raw_tokens)
    except ValueError:
        return GuardResult(False, 2, "FAIL: AI_MAX_OUTPUT_TOKENS is invalid.")
    if max_tokens < 1 or max_tokens > MAX_OUTPUT_TOKENS_LIMIT:
        return GuardResult(False, 2, f"FAIL: AI_MAX_OUTPUT_TOKENS must be between 1 and {MAX_OUTPUT_TOKENS_LIMIT}.")

    return GuardResult(True, 0, "RUN: live OpenAI smoke tests enabled.", budget_cents=budget)


def _make_smoke_temp_dir() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix="cookbook-openai-smoke-", ignore_cleanup_errors=True)


def _run_importer_smoke(provider: Any, summary: SmokeSummary) -> None:
    from app.importer import import_recipe_text
    from app.schemas import RecipeImportRequest

    response = import_recipe_text(
        RecipeImportRequest(
            text="Lemon beans: warm canned beans with lemon juice and olive oil. Serve.",
            source="manual live smoke fixture",
        ),
        provider=provider,
    )
    if getattr(response, "provider", "none") != "openai":
        warnings = " ".join(getattr(response, "warnings", []) or [])
        if _looks_like_budget_block(warnings):
            raise ProviderError("provider call blocked by budget settings.")
        raise ProviderError(f"provider did not return openai: {getattr(response, 'provider', 'none')}")
    assert response.draft.title.strip(), "importer returned an empty title"
    assert response.draft.ingredients, "importer returned no ingredients"
    assert response.draft.instructions, "importer returned no instructions"
    _assert_no_secret_leaks(response.model_dump())
    summary.record("importer", response)


def _run_saved_recipe_ask_smoke(provider: Any, summary: SmokeSummary) -> None:
    from app.rag import ask_cookbook
    from app.schemas import AskRequest, RecipeDocument

    response = ask_cookbook(
        AskRequest(question="What saved recipe uses lemon?", limit=1),
        provider=provider,
        recipes=[
            RecipeDocument(
                id="1",
                title="Lemon Beans",
                description="Tiny smoke fixture recipe.",
                ingredients=["beans", "lemon", "olive oil"],
                instructions=["Warm beans", "Add lemon"],
                tags=["dinner"],
            ),
            RecipeDocument(
                id="2",
                title="Plain Toast",
                ingredients=["bread"],
                instructions=["Toast bread"],
            ),
        ],
    )
    if getattr(response, "provider", "none") != "openai":
        warnings = " ".join(getattr(response, "warnings", []) or [])
        if _looks_like_budget_block(warnings):
            raise ProviderError("provider call blocked by budget settings.")
        raise ProviderError(f"provider did not return openai: {getattr(response, 'provider', 'none')}")
    assert response.citations and response.citations[0].recipe_id == "1", "saved-recipe citation missing"
    _assert_no_secret_leaks(response.model_dump())
    summary.record("ask_my_cookbook", response)


def _run_dataset_ask_smoke(provider: Any, summary: SmokeSummary, temp_dir: Path) -> None:
    from app.dataset_rag import ask_dataset_recipes
    from app.schemas import DatasetAskRequest

    dataset_dir = temp_dir / "dataset"
    dataset_dir.mkdir()
    with (dataset_dir / "13k-recipes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["recipe_id", "title", "ingredients", "instructions", "cuisine"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "recipe_id": "live-1",
                "title": "Lemon Beans",
                "ingredients": "beans; lemon; olive oil",
                "instructions": "Warm beans and add lemon.",
                "cuisine": "dinner",
            }
        )
        writer.writerow(
            {
                "recipe_id": "live-2",
                "title": "Plain Toast",
                "ingredients": "bread",
                "instructions": "Toast bread.",
                "cuisine": "breakfast",
            }
        )

    old_dataset_dir = os.environ.get("RECIPE_DATASET_DIR")
    os.environ["RECIPE_DATASET_DIR"] = str(dataset_dir)
    try:
        response = ask_dataset_recipes(
            DatasetAskRequest(question="What indexed recipe uses lemon?", limit=1, dataset_limit=2),
            provider=provider,
        )
    finally:
        if old_dataset_dir is None:
            os.environ.pop("RECIPE_DATASET_DIR", None)
        else:
            os.environ["RECIPE_DATASET_DIR"] = old_dataset_dir

    if getattr(response, "provider", "none") != "openai":
        warnings = " ".join(getattr(response, "warnings", []) or [])
        if _looks_like_budget_block(warnings):
            raise ProviderError("provider call blocked by budget settings.")
        raise ProviderError(f"provider did not return openai: {getattr(response, 'provider', 'none')}")
    assert response.citations and response.citations[0].source_id == "live-1", "dataset citation missing"
    _assert_no_secret_leaks(response.model_dump())
    summary.record("dataset_ask", response)


def _run_meal_plan_smoke(provider: Any, summary: SmokeSummary, temp_dir: Path) -> None:
    from app.meal_plan_endpoint import create_meal_plan
    from app.schemas import MealPlanRequest

    db_path = temp_dir / "cookbook.sqlite"
    _write_recipe_db(db_path)
    old_db_path = os.environ.get("COOKBOOK_DB_PATH")
    os.environ["COOKBOOK_DB_PATH"] = str(db_path)
    try:
        response = create_meal_plan(
            MealPlanRequest(days=1, meals_per_day=1, preferences="lemon", candidate_limit=2),
            provider=provider,
        )
    finally:
        if old_db_path is None:
            os.environ.pop("COOKBOOK_DB_PATH", None)
        else:
            os.environ["COOKBOOK_DB_PATH"] = old_db_path

    if getattr(response, "provider", "none") != "openai":
        warnings = " ".join(getattr(response, "warnings", []) or [])
        if _looks_like_budget_block(warnings):
            raise ProviderError("provider call blocked by budget settings.")
        raise ProviderError(f"provider did not return openai: {getattr(response, 'provider', 'none')}")
    assert response.citations and response.selection.matched_recipe_ids == ["1"], "meal-plan citation missing"
    planned_ids = [meal.recipe_id for day in response.plan.days for meal in day.meals]
    assert set(planned_ids).issubset({"1"}), "meal plan used a non-selected recipe"
    _assert_no_secret_leaks(response.model_dump())
    summary.record("meal_plan", response)


def _write_recipe_db(path: Path) -> None:
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
                1,
                "Lemon Beans",
                "Tiny smoke fixture recipe.",
                json.dumps(["beans", "lemon", "olive oil"]),
                "Warm beans\nAdd lemon",
                "dinner",
                None,
            ),
            (
                2,
                "Plain Toast",
                "Tiny smoke fixture recipe.",
                json.dumps(["bread"]),
                "Toast bread",
                "breakfast",
                None,
            ),
        ],
    )
    connection.commit()
    connection.close()


def _assert_call_budget(summary: SmokeSummary) -> None:
    assert summary.live_calls <= MAX_LIVE_CALLS, f"live call cap exceeded: {summary.live_calls}"


def _assert_no_secret_leaks(payload: Any) -> None:
    serialized = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    for pattern in SECRET_PATTERNS:
        assert pattern not in serialized, f"secret-like pattern leaked: {pattern}"

def _safe_error(exc: BaseException) -> str:
    text = str(exc)
    for pattern in SECRET_PATTERNS:
        text = text.replace(pattern, "[redacted]")
    return text


def _looks_like_budget_block(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("budget", "disabled", "exhausted", "cap", "misconfigured"))


def _fail_safely(message: str) -> int:
    _assert_no_secret_leaks(message)
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def _compact_summary(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"provider={result['provider']}",
            f"model={result['model']}",
            f"live_calls={result['live_calls']}",
            f"estimated_usage_tokens={result['estimated_usage_tokens']}",
            f"workflows={','.join(result['workflows'])}",
            f"budget_cents={result['budget_cents']}",
            f"status={result['status']}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
