import importlib.util
import json
import shutil
import sys
from pathlib import Path

from evals.ai_cookbook.expected_checks import (
    assert_no_secret_leaks,
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


def test_live_eval_guard_skips_when_not_enabled():
    live_evals = load_live_eval_module()
    result = live_evals.evaluate_live_eval_guard({})

    assert result.should_run is False
    assert result.exit_code == 0
    assert "OPENAI_ENABLE_LIVE_TESTS=true" in result.message


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
        "draft": {"title": "Lemon Beans", "ingredients": [{"name": "beans"}], "instructions": [{"step": 1, "text": "Warm beans"}]},
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "warnings": [],
    }
    assert all(check.passed for check in score_importer(passing, "gpt-5.4-nano"))

    failing = {**passing, "draft": {**passing["draft"], "title": ""}}
    results = score_importer(failing, "gpt-5.4-nano")
    assert any(check.name == "title is non-empty" and not check.passed for check in results)


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

    dataset_payload = {
        "answer": "Tomato Pasta Skillet is relevant. Cucumber Chickpea Salad is also here.",
        "citations": [{"source_id": "demo-dataset-1", "title": "Tomato Pasta Skillet", "snippet": "tomato"}],
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "retrieval": {"retrieved_count": 1},
    }
    dataset_results = score_dataset_ask(dataset_payload, "gpt-5.4-nano")
    assert any("unsupported dataset recipes" in check.name and not check.passed for check in dataset_results)


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


def test_metrics_summary_and_cost_estimation():
    assert estimate_cost_usd(
        {"input_tokens": 1000, "output_tokens": 500},
        input_cost_per_1m=0.10,
        output_cost_per_1m=0.40,
    ) == 0.0003

    summary = summarize_records(
        [
            {
                "overall_passed": True,
                "latency_ms": 10,
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150,
                "estimated_cost_usd": 0.01,
            },
            {
                "overall_passed": False,
                "latency_ms": 20,
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
                "estimated_cost_usd": None,
            },
        ]
    )
    assert summary["overall_passed"] is False
    assert summary["workflow_count"] == 2
    assert summary["passed_workflow_count"] == 1
    assert summary["total_tokens"] == 165


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
