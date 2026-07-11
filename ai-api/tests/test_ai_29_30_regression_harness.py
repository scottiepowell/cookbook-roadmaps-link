from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "e2e-ai-29-30-regression.py"
WRAPPER = REPO_ROOT / "scripts" / "run-ai-29-30-regression.ps1"

FORBIDDEN_STRINGS = (
    "OPENAI_API_KEY",
    "sk-",
    "Authorization",
    "X-AI-Operator-Token",
    "X-AI-Demo-Session-Token: real",
    ".env",
    ".tmp-ai-demo",
    "raw_provider_prompt",
    "raw_provider_response",
    "C:\\Users\\",
    "/home/",
    "postgres://",
    "redis://",
    "GLM-4.7 Flash Secondary Provider Offload",
    "Stripe",
    "PayPal",
    "checkout",
)


def _load_module():
    spec = importlib.util.spec_from_file_location("e2e_ai_29_30_regression", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_regression_harness_files_exist():
    assert SCRIPT.exists()
    assert WRAPPER.exists()


def test_regression_harness_runs_offline_with_deterministic_summary():
    module = _load_module()

    first = module.run_regression()
    second = module.run_regression()

    assert first.passed is True
    assert second.passed is True
    assert first.summary == second.summary
    assert first.summary.startswith("SUMMARY:")
    assert first.checks[-1].detail == "Skipped because live smoke was not requested."
    assert any(check.name == "usage report reflects session and meter counts" for check in first.checks)
    assert any(check.name == "provider budget block prevents provider invocation" for check in first.checks)


def test_regression_harness_main_prints_safe_summary_and_no_forbidden_strings():
    result = _run_script()

    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "SUMMARY:" in combined
    assert "PASS: health/config readiness" in combined
    assert "PASS: usage report reflects session and meter counts" in combined
    assert "Skipped because live smoke was not requested." in combined
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in combined


def test_live_checks_are_opt_in_only():
    module = _load_module()

    result = module.run_regression(live_smoke=True)

    assert result.passed is True
    assert any(check.name == "optional live smoke gate" for check in result.checks)
    assert result.checks[-1].detail.startswith("Skipped because")


def test_regression_harness_text_does_not_include_glm_secondary_provider_or_payment_runtime_code():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "GLM-4.7 Flash Secondary Provider Offload" not in text
    assert "secondary-provider routing" not in text.lower()
    assert "stripe" not in text.lower()
    assert "paypal" not in text.lower()
    assert "ad network runtime code" not in text.lower()
    assert "sponsor runtime code" not in text.lower()
    assert "affiliate link runtime code" not in text.lower()


def test_wrapper_uses_safe_mock_defaults_and_live_opt_in_flag():
    text = WRAPPER.read_text(encoding="utf-8")
    assert 'AI_29_30_REGRESSION_LIVE' in text
    assert '$env:AI_PROVIDER = "mock"' in text
    assert '$env:OPENAI_ENABLE_LIVE_TESTS = "false"' in text
    assert 'Write-Host "PASS: 29/30 regression harness"' in text
    assert 'Write-Host "FAIL: 29/30 regression harness"' in text
