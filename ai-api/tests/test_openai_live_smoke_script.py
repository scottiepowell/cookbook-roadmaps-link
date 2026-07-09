import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def load_smoke_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "smoke-openai-live.py"
    spec = importlib.util.spec_from_file_location("smoke_openai_live", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_wrapper(script_name: str, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    merged_env = os.environ.copy()
    if env is not None:
        merged_env.update(env)
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo_root / "scripts" / script_name)],
        cwd=repo_root,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_live_guard_skips_when_not_enabled():
    smoke = load_smoke_module()
    result = smoke.evaluate_live_guard({})

    assert result.should_run is False
    assert result.exit_code == 0
    assert "disabled" in result.message


def test_live_guard_skips_without_api_key():
    smoke = load_smoke_module()
    result = smoke.evaluate_live_guard(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_ENABLE_LIVE_TESTS": "true",
            "OPENAI_LIVE_TEST_BUDGET_CENTS": "25",
            "AI_MAX_OUTPUT_TOKENS": "200",
        }
    )

    assert result.should_run is False
    assert result.exit_code == 0
    assert "not configured" in result.message


def test_live_guard_fails_invalid_budget_before_live_calls():
    smoke = load_smoke_module()
    result = smoke.evaluate_live_guard(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_ENABLE_LIVE_TESTS": "true",
            "OPENAI_API_KEY": "fake-offline-key",
            "OPENAI_LIVE_TEST_BUDGET_CENTS": "invalid",
            "AI_MAX_OUTPUT_TOKENS": "200",
        }
    )

    assert result.should_run is False
    assert result.exit_code == 2
    assert "budget" in result.message


def test_live_guard_fails_too_high_budget_before_live_calls():
    smoke = load_smoke_module()
    result = smoke.evaluate_live_guard(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_ENABLE_LIVE_TESTS": "true",
            "OPENAI_API_KEY": "fake-offline-key",
            "OPENAI_LIVE_TEST_BUDGET_CENTS": "26",
            "AI_MAX_OUTPUT_TOKENS": "200",
        }
    )

    assert result.should_run is False
    assert result.exit_code == 2
    assert "25 cents" in result.message


def test_live_guard_allows_explicit_bounded_opt_in():
    smoke = load_smoke_module()
    result = smoke.evaluate_live_guard(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_ENABLE_LIVE_TESTS": "true",
            "OPENAI_API_KEY": "fake-offline-key",
            "OPENAI_LIVE_TEST_BUDGET_CENTS": "25",
            "AI_MAX_OUTPUT_TOKENS": "200",
        }
    )

    assert result.should_run is True
    assert result.exit_code == 0
    assert result.budget_cents == 25


def test_secret_checker_catches_obvious_patterns():
    smoke = load_smoke_module()

    try:
        smoke._assert_no_secret_leaks({"text": "sk-offline-test-pattern"})
    except AssertionError as exc:
        assert "secret-like pattern" in str(exc)
    else:
        raise AssertionError("Expected secret-like pattern to fail.")


def test_smoke_temp_dir_uses_best_effort_cleanup(monkeypatch):
    smoke = load_smoke_module()
    captured = {}

    class FakeTemporaryDirectory:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(smoke.tempfile, "TemporaryDirectory", FakeTemporaryDirectory)

    smoke._make_smoke_temp_dir()

    assert captured == {
        "prefix": "cookbook-openai-smoke-",
        "ignore_cleanup_errors": True,
    }


def test_demo_ai_live_smoke_wrapper_skips_without_opt_in():
    env = os.environ.copy()
    for name in ("AI_PROVIDER", "OPENAI_ENABLE_LIVE_TESTS", "OPENAI_API_KEY", "OPENAI_LIVE_TEST_BUDGET_CENTS"):
        env.pop(name, None)

    result = run_wrapper("demo-ai-live-smoke.ps1", env=env)

    assert result.returncode == 0
    assert "Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in." in result.stdout
