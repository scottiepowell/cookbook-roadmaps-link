import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from app.dataset_retrieval import search_dataset_recipes
from app.demo_data import seed_demo_data
from app.importer import RecipeImportProviderError
from app.providers.errors import ProviderCallError
from evals.ai_cookbook.expected_checks import (
    COST_SOURCE_DEFAULT_MODEL_RATE,
    COST_SOURCE_ENV_OVERRIDE,
    COST_SOURCE_UNAVAILABLE,
    CheckResult,
    assert_no_secret_leaks,
    assert_no_private_paths,
    apply_threshold_checks,
    estimate_cost,
    evaluate_thresholds,
    estimate_cost_usd,
    score_ask_my_cookbook,
    score_dataset_ask,
    score_importer,
    score_meal_plan,
    summarize_records,
)


def load_live_eval_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "live-openai-demo-evals.py"
    spec = importlib.util.spec_from_file_location("live_openai_demo_evals", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_live_eval_wrapper(*, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    merged_env = os.environ.copy()
    if env is not None:
        merged_env.update(env)
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo_root / "scripts" / "run-openai-demo-evals.ps1")],
        cwd=repo_root,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_eval_guard_skips_when_not_enabled():
    live_evals = load_live_eval_module()
    result = live_evals.evaluate_live_eval_guard({})

    assert result.should_run is False
    assert result.exit_code == 0
    assert "OPENAI_ENABLE_LIVE_TESTS=true" in result.message


def test_live_eval_wrapper_skips_without_opt_in():
    env = os.environ.copy()
    for name in (
        "AI_PROVIDER",
        "OPENAI_ENABLE_LIVE_TESTS",
        "OPENAI_API_KEY",
        "OPENAI_LIVE_TEST_BUDGET_CENTS",
        "OPENAI_MODEL",
        "AI_MAX_OUTPUT_TOKENS",
    ):
        env.pop(name, None)

    result = run_live_eval_wrapper(env=env)

    assert result.returncode == 0
    assert "SKIP:" in result.stdout
    assert "OPENAI_ENABLE_LIVE_TESTS=true is required." in result.stdout


def test_live_eval_guard_requires_explicit_model_and_token_cap():
    live_evals = load_live_eval_module()
    base_env = {
        "AI_PROVIDER": "openai",
        "OPENAI_ENABLE_LIVE_TESTS": "true",
        "OPENAI_API_KEY": "fake-offline-key",
        "OPENAI_LIVE_TEST_BUDGET_CENTS": "25",
    }

    missing_model = live_evals.evaluate_live_eval_guard(base_env)
    assert missing_model.should_run is False
    assert missing_model.exit_code == 0
    assert "OPENAI_MODEL" in missing_model.message

    enabled = live_evals.evaluate_live_eval_guard(
        {
            **base_env,
            "OPENAI_MODEL": "gpt-5.4-nano",
            "AI_MAX_OUTPUT_TOKENS": "300",
        }
    )
    assert enabled.should_run is True
    assert enabled.model == "gpt-5.4-nano"


def test_live_eval_guard_rejects_invalid_budget_and_large_token_cap():
    live_evals = load_live_eval_module()
    env = {
        "AI_PROVIDER": "openai",
        "OPENAI_ENABLE_LIVE_TESTS": "true",
        "OPENAI_API_KEY": "fake-offline-key",
        "OPENAI_LIVE_TEST_BUDGET_CENTS": "26",
        "OPENAI_MODEL": "gpt-5.4-nano",
        "AI_MAX_OUTPUT_TOKENS": "300",
    }

    too_expensive = live_evals.evaluate_live_eval_guard(env)
    assert too_expensive.should_run is False
    assert too_expensive.exit_code == 2

    too_many_tokens = live_evals.evaluate_live_eval_guard(
        {**env, "OPENAI_LIVE_TEST_BUDGET_CENTS": "25", "AI_MAX_OUTPUT_TOKENS": "301"}
    )
    assert too_many_tokens.should_run is False
    assert too_many_tokens.exit_code == 2


def test_importer_expected_checks_pass_and_fail():
    passing = {
        "draft": {
            "title": "Lemon Herb White Beans",
            "description": "White beans with lemon, olive oil, garlic, and parsley.",
            "servings": 4,
            "ingredients": [
                {"name": "white beans", "quantity": "2", "unit": "cups"},
                {"name": "lemon juice", "quantity": "1", "unit": "medium"},
                {"name": "olive oil", "quantity": "2", "unit": "tablespoons"},
            ],
            "instructions": [
                {"step": 1, "text": "Warm beans with olive oil."},
                {"step": 2, "text": "Stir in lemon juice."},
                {"step": 3, "text": "Finish with parsley."},
            ],
            "notes": "Quantities are estimated for 4 servings.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
        "citations": [{"source_id": "demo-dataset-2", "title": "Lemon White Bean Toasts"}],
        "warnings": [],
    }
    assert all(check.passed for check in score_importer(passing, "gpt-5.4-nano"))

    failing = {**passing, "draft": {**passing["draft"], "title": ""}}
    results = score_importer(failing, "gpt-5.4-nano")
    assert any(check.name == "title is non-empty" and not check.passed for check in results)

    unrelated = {**passing, "draft": {**passing["draft"], "ingredients": [{"name": "white beans"}, {"name": "chicken"}]}}
    unrelated_results = score_importer(unrelated, "gpt-5.4-nano")
    assert any(check.name == "draft should not include unrelated foods" and not check.passed for check in unrelated_results)


def test_importer_expected_checks_accept_structured_evidence_without_description():
    payload = {
        "draft": {
            "title": "Lemon Herb White Beans",
            "description": None,
            "servings": 4,
            "ingredients": [
                {"name": "white beans (warm)", "quantity": "2", "unit": "cups"},
                {"name": "olive oil", "quantity": "2", "unit": "tablespoons"},
                {"name": "garlic", "quantity": "2", "unit": "cloves"},
                {"name": "lemon juice", "quantity": "1", "unit": "medium"},
                {"name": "parsley", "quantity": "0.25", "unit": "cup"},
                {"name": "toast", "quantity": "4", "unit": "slices"},
            ],
            "instructions": [
                {"step": 1, "text": "Warm the white beans."},
                {"step": 2, "text": "Stir in olive oil, garlic, lemon juice, and parsley."},
                {"step": 3, "text": "Serve the beans with toast."},
            ],
            "notes": "Quantities are estimated for 4 servings.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
        "citations": [{"source_id": "demo-dataset-2", "title": "Lemon White Bean Toasts"}],
        "warnings": [],
    }

    results = score_importer(payload, "gpt-5.4-nano")
    assert all(check.passed for check in results)


def test_importer_expected_checks_accept_alias_evidence():
    payload = {
        "draft": {
            "title": "Citrus Bean Toasts",
            "description": "A citrus bean topping served on bread.",
            "servings": 4,
            "ingredients": [
                {"name": "beans", "quantity": "2", "unit": "cups"},
                {"name": "oil", "quantity": "2", "unit": "tablespoons"},
                {"name": "herbs", "quantity": "0.25", "unit": "cup"},
                {"name": "bread", "quantity": "4", "unit": "slices"},
            ],
            "instructions": [
                {"step": 1, "text": "Warm beans with oil."},
                {"step": 2, "text": "Stir herbs into beans."},
                {"step": 3, "text": "Serve on bread."},
            ],
            "notes": "Quantities are estimated for 4 servings.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
        "citations": [{"source_id": "demo-dataset-2", "title": "Lemon White Bean Toasts"}],
        "warnings": [],
    }

    results = score_importer(payload, "gpt-5.4-nano")
    assert all(check.passed for check in results)


def test_importer_expected_checks_reject_generic_and_ungrounded_outputs():
    generic = {
        "draft": {
            "title": "Recipe",
            "description": "A nice meal.",
            "ingredients": [{"name": "mock-value"}],
            "instructions": [{"step": 1, "text": "Cook until done."}],
            "notes": "Quantities are unspecified.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "warnings": [],
    }
    generic_results = score_importer(generic, "gpt-5.4-nano")
    assert any(check.name == "title should not be a generic placeholder" and not check.passed for check in generic_results)
    assert any(check.name == "structured fields should not be generic placeholders" and not check.passed for check in generic_results)

    ungrounded = {
        "draft": {
            "title": "Pantry Supper",
            "description": "A simple supper.",
            "ingredients": [{"name": "salt"}, {"name": "water"}],
            "instructions": [{"step": 1, "text": "Cook until warm."}],
            "notes": "Quantities are unspecified.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "warnings": [],
    }
    ungrounded_results = score_importer(ungrounded, "gpt-5.4-nano")
    assert any(
        check.name == "draft should preserve at least two input ingredients across structured fields" and not check.passed
        for check in ungrounded_results
    )


def test_importer_expected_checks_reject_weak_recipe_creator_outputs():
    weak_cheesecake = {
        "draft": {
            "title": "Cheesecake",
            "description": "Cheesecake with cream cheese and graham cracker crust.",
            "servings": 4,
            "ingredients": [
                {"name": "cream cheese", "quantity": "16", "unit": "ounces"},
                {"name": "sugar", "quantity": "0.75", "unit": "cup"},
                {"name": "eggs", "quantity": "4", "unit": "large"},
            ],
            "instructions": [{"step": 1, "text": "Bake and chill the cheesecake."}],
            "notes": "Quantities are estimated for 4 servings.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
        "citations": [{"source_id": "dataset-cheesecake", "title": "Classic Cheesecake"}],
        "warnings": [],
    }

    cheesecake_results = score_importer(weak_cheesecake, "gpt-5.4-nano")
    assert any(check.name == "instructions should have enough step depth" and not check.passed for check in cheesecake_results)
    assert any(check.name == "cheesecake instructions should cover bake and chill" and not check.passed for check in cheesecake_results)

    carbonara_with_cream = {
        "draft": {
            "title": "Carbonara Pasta",
            "description": "Carbonara pasta with eggs and parmesan.",
            "servings": 4,
            "ingredients": [
                {"name": "spaghetti", "quantity": "12", "unit": "ounces"},
                {"name": "eggs", "quantity": "4", "unit": "large"},
                {"name": "parmesan", "quantity": "1", "unit": "cup"},
                {"name": "heavy cream", "quantity": "0.5", "unit": "cup"},
            ],
            "instructions": [
                {"step": 1, "text": "Boil spaghetti until tender."},
                {"step": 2, "text": "Whisk eggs and parmesan."},
                {"step": 3, "text": "Toss pasta off heat."},
            ],
            "notes": "Quantities are estimated for 4 servings.",
        },
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
        "citations": [{"source_id": "dataset-carbonara", "title": "Carbonara"}],
        "warnings": [],
    }

    carbonara_results = score_importer(carbonara_with_cream, "gpt-5.4-nano")
    assert any(check.name == "carbonara should not require heavy cream unless supplied" and not check.passed for check in carbonara_results)


def test_ask_and_dataset_expected_checks_detect_unsupported_titles():
    ask_payload = {
        "answer": "Use Lemon Herb White Beans. Do not use Weeknight Tomato Pasta.",
        "citations": [{"recipe_id": "1", "title": "Lemon Herb White Beans", "snippet": "lemon"}],
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
    }
    ask_results = score_ask_my_cookbook(ask_payload, "gpt-5.4-nano")
    assert any("hallucinated" in check.name and not check.passed for check in ask_results)
    assert any("unsupported saved recipe titles" in check.name and not check.passed for check in ask_results)

    dataset_payload = {
        "answer": "Tomato Pasta Skillet is relevant. Cucumber Chickpea Salad is also here.",
        "citations": [{"source_id": "demo-dataset-1", "title": "Tomato Pasta Skillet", "snippet": "tomato"}],
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
    }
    dataset_results = score_dataset_ask(dataset_payload, "gpt-5.4-nano")
    assert any("unsupported dataset recipes" in check.name and not check.passed for check in dataset_results)
    assert any("unsupported dataset titles" in check.name and not check.passed for check in dataset_results)


def test_meal_plan_expected_checks_reject_invented_ids():
    payload = {
        "plan": {"days": [{"day": 1, "meals": [{"slot": "dinner", "recipe_id": "99", "title": "Made Up", "reason": "x"}]}]},
        "citations": [{"recipe_id": "1", "title": "Lemon Herb White Beans", "snippet": "lemon", "matched_fields": []}],
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "selection": {"candidate_count": 1, "matched_recipe_ids": ["1"], "requested_slots": 1},
        "warnings": [],
    }

    results = score_meal_plan(payload, "gpt-5.4-nano")
    assert any(check.name == "no invented recipe ids" and not check.passed for check in results)
    assert any(check.name == "selected meal title should match cited recipe title" and not check.passed for check in results)


def test_metrics_summary_and_cost_estimation():
    env_override = estimate_cost(
        {"input_tokens": 1000, "output_tokens": 500},
        model="custom-model",
        input_cost_per_1m=0.10,
        output_cost_per_1m=0.40,
    )
    assert env_override.estimated_cost_usd == 0.0003
    assert env_override.cost_source == COST_SOURCE_ENV_OVERRIDE
    assert estimate_cost_usd(
        {"input_tokens": 1000, "output_tokens": 500},
        input_cost_per_1m=0.10,
        output_cost_per_1m=0.40,
    ) == 0.0003

    default_nano = estimate_cost(
        {"input_tokens": 1000, "output_tokens": 500},
        model="gpt-5.4-nano",
    )
    assert default_nano.estimated_cost_usd == 0.000825
    assert default_nano.cost_source == COST_SOURCE_DEFAULT_MODEL_RATE

    unknown_model = estimate_cost(
        {"input_tokens": 1000, "output_tokens": 500},
        model="unknown-model",
    )
    assert unknown_model.estimated_cost_usd is None
    assert unknown_model.cost_source == COST_SOURCE_UNAVAILABLE

    sub_cent = estimate_cost(
        {"input_tokens": 1, "output_tokens": 1},
        model="gpt-5.4-nano",
    )
    assert sub_cent.estimated_cost_usd == 0.00000145
    assert sub_cent.estimated_cost_usd > 0

    summary = summarize_records(
        [
            {
                "overall_passed": True,
                "latency_ms": 10,
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "estimated_cost_usd": 0.01,
                "cost_source": COST_SOURCE_DEFAULT_MODEL_RATE,
            },
            {
                "overall_passed": False,
                "latency_ms": 20,
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
                "estimated_cost_usd": None,
                "cost_source": COST_SOURCE_UNAVAILABLE,
            },
        ]
    )
    assert summary["overall_passed"] is False
    assert summary["workflow_count"] == 2
    assert summary["passed_workflow_count"] == 1
    assert summary["total_tokens"] == 165
    assert summary["cost_sources"] == [COST_SOURCE_DEFAULT_MODEL_RATE, COST_SOURCE_UNAVAILABLE]


def test_run_case_records_default_cost_source_metadata(monkeypatch):
    live_evals = load_live_eval_module()
    monkeypatch.delenv("OPENAI_INPUT_COST_PER_1M_TOKENS", raising=False)
    monkeypatch.delenv("OPENAI_OUTPUT_COST_PER_1M_TOKENS", raising=False)
    responses_dir = Path(".tmp-ai-demo") / "live-evals" / "cost-source-offline-test" / "responses"
    shutil.rmtree(responses_dir.parent, ignore_errors=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    def runner(_case):
        return {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "usage": {"input_tokens": 1000, "output_tokens": 500, "total_tokens": 1500},
        }

    def scorer(_workflow, _payload, _expected_model):
        return [CheckResult("offline pass", True, "passed")]

    try:
        record = live_evals.run_case(
            {"workflow": "importer", "endpoint": "POST /ai/import-recipe", "input_summary": "offline", "expected_checks": []},
            runner,
            responses_dir,
            "gpt-5.4-nano",
            scorer,
        )

        assert record["estimated_cost_usd"] == 0.000825
        assert record["cost_source"] == COST_SOURCE_DEFAULT_MODEL_RATE
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


def test_importer_case_uses_workflow_specific_output_cap_and_restores_env(monkeypatch):
    live_evals = load_live_eval_module()
    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "300")
    monkeypatch.setenv("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL", "300")
    seen: dict[str, str | None] = {}

    def fake_import_recipe_text(request, provider=None):
        seen["AI_MAX_OUTPUT_TOKENS"] = os.environ.get("AI_MAX_OUTPUT_TOKENS")
        seen["AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL"] = os.environ.get("AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL")
        return {
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "draft": {"title": "Cap Test", "ingredients": [], "instructions": []},
            "retrieval": {"retrieved_count": 1},
            "citations": [],
            "warnings": [],
            "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            "input_quality": {"status": "ready"},
        }

    import app.importer as importer_module

    monkeypatch.setattr(importer_module, "import_recipe_text", fake_import_recipe_text)

    result = live_evals._run_importer_case(
        {"request": {"text": "rice and beans", "source": "manual"}},
        provider=object(),
        max_output_tokens=900,
    )

    assert seen["AI_MAX_OUTPUT_TOKENS"] == "900"
    assert seen["AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL"] == "900"
    assert os.environ["AI_MAX_OUTPUT_TOKENS"] == "300"
    assert os.environ["AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL"] == "300"
    assert result["draft"]["title"] == "Cap Test"


def test_run_case_records_safe_provider_diagnostics_for_importer_failures(monkeypatch):
    live_evals = load_live_eval_module()
    responses_dir = Path(".tmp-ai-demo") / "live-evals" / "provider-failure-test" / "responses"
    shutil.rmtree(responses_dir.parent, ignore_errors=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    provider_error = ProviderCallError(
        "provider response could not be decoded",
        failure_category="output_cap_or_incomplete_response",
        exception_type="JSONDecodeError",
        safe_summary="provider response was truncated before JSON parsing completed",
    )

    def runner(_case):
        raise RecipeImportProviderError("Recipe importer provider failed.") from provider_error

    def scorer(_workflow, _payload, _expected_model):
        return [CheckResult("offline pass", True, "passed")]

    try:
        record = live_evals.run_case(
            {"workflow": "importer", "endpoint": "POST /ai/import-recipe", "input_summary": "offline", "expected_checks": []},
            runner,
            responses_dir,
            "gpt-5.4-nano",
            scorer,
        )

        assert record["failure_category"] == "provider_call_failure"
        assert record["provider_error_category"] == "output_cap_or_incomplete_response"
        assert record["provider_error_type"] == "JSONDecodeError"
        assert "provider response was truncated" in record["safe_error_summary"]
        assert record["error_type"] == "RecipeImportProviderError"
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


def test_run_case_records_budget_block_before_invocation_failure(monkeypatch):
    live_evals = load_live_eval_module()
    responses_dir = Path(".tmp-ai-demo") / "live-evals" / "budget-block-test" / "responses"
    shutil.rmtree(responses_dir.parent, ignore_errors=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    def runner(_case):
        return {
            "provider": "none",
            "model": "none",
            "warnings": ["Provider calls are disabled for this local demo."],
            "usage": None,
        }

    def scorer(_workflow, _payload, _expected_model):
        return [CheckResult("offline pass", True, "passed")]

    try:
        record = live_evals.run_case(
            {"workflow": "importer", "endpoint": "POST /ai/import-recipe", "input_summary": "offline", "expected_checks": []},
            runner,
            responses_dir,
            "gpt-5.4-nano",
            scorer,
        )

        assert record["failure_category"] == "budget_block_before_invocation"
        assert record["provider_error_category"] == "budget_block_before_invocation"
        assert record["provider_error_type"] == "BudgetBlocked"
        assert record["provider_called"] is False
        assert record["error_type"] == "BudgetBlocked"
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


def test_threshold_warnings_and_failures_are_generated():
    records = [
        {
            "workflow": "importer",
            "overall_passed": True,
            "checks": [],
            "latency_ms": 8000,
            "total_tokens": 950,
        },
        {
            "workflow": "dataset_ask",
            "overall_passed": True,
            "checks": [],
            "latency_ms": 11000,
            "total_tokens": 1300,
        },
    ]

    thresholds = evaluate_thresholds(records)
    assert any("importer latency" in warning for warning in thresholds["warnings"])
    assert any("importer tokens" in warning for warning in thresholds["warnings"])
    assert any("dataset_ask latency" in failure for failure in thresholds["failures"])
    assert any("dataset_ask tokens" in failure for failure in thresholds["failures"])

    updated = apply_threshold_checks(records)
    assert updated[0]["overall_passed"] is True
    assert updated[0]["threshold_warnings"]
    assert updated[1]["overall_passed"] is False
    assert any(not check["passed"] for check in updated[1]["checks"])


def test_generated_demo_dataset_suppresses_optional_file_warnings(monkeypatch):
    run_dir = Path(".tmp-ai-demo") / "warning-filter-test"
    shutil.rmtree(run_dir, ignore_errors=True)
    try:
        paths = seed_demo_data(run_dir)
        monkeypatch.setenv("RECIPE_DATASET_DIR", str(paths["dataset_dir"]))

        response = search_dataset_recipes("tomato pasta", limit=3, dataset_limit=25)

        assert response.count >= 1
        assert not any("13k-recipes.db is missing" in warning for warning in response.warnings)
        assert not any("metadata.json is missing" in warning for warning in response.warnings)
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


def test_result_files_are_written_under_ignored_generated_path():
    live_evals = load_live_eval_module()
    run_dir = Path(".tmp-ai-demo") / "live-evals" / "offline-test"
    shutil.rmtree(run_dir, ignore_errors=True)
    records = [
        {
            "workflow": "readiness",
            "endpoint": "GET /demo/readiness",
            "provider": "none",
            "model": "none",
            "input_summary": "offline",
            "expected_checks": [],
            "actual_answer_summary": "ok",
            "checks": [],
            "overall_passed": True,
            "warning_count": 0,
            "citation_count": 0,
            "retrieved_count": 3,
            "latency_ms": 1,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": None,
            "cost_source": COST_SOURCE_UNAVAILABLE,
            "raw_response_path": str(run_dir / "responses" / "readiness.json"),
            "error_type": None,
        }
    ]

    try:
        summary = live_evals.write_run_outputs(
            run_dir=run_dir,
            records=records,
            cases=[{"workflow": "readiness"}],
            expected_model="gpt-5.4-nano",
        )

        assert ".tmp-ai-demo" in str(run_dir)
        assert (run_dir / "results.jsonl").exists()
        assert (run_dir / "summary.json").exists()
        assert (run_dir / "summary.md").exists()
        assert summary["overall_passed"] is True
        loaded = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        assert loaded["expected_model"] == "gpt-5.4-nano"
    finally:
        shutil.rmtree(Path(".tmp-ai-demo"), ignore_errors=True)


def test_secret_checker_blocks_artifacts():
    try:
        assert_no_secret_leaks({"message": "sk-offline-test-pattern"})
    except AssertionError as exc:
        assert "secret-like pattern" in str(exc)
    else:
        raise AssertionError("Expected secret-like pattern to fail.")


def test_private_path_checker_blocks_baseline_docs():
    try:
        assert_no_private_paths("Generated at C:\\Users\\private\\repo\\.tmp-ai-demo")
    except AssertionError as exc:
        assert "private local path marker" in str(exc)
    else:
        raise AssertionError("Expected private path marker to fail.")
