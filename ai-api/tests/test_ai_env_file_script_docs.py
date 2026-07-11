from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_STRINGS = (
    "sk-proj-",
    "sk_live_",
    "sk_test_",
    "STRIPE_SECRET_KEY",
    "PAYPAL_CLIENT_SECRET",
    "raw_provider_prompt",
    "raw_provider_response",
    "Authorization: Bearer real",
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _powershell_executable() -> str:
    for candidate in ("powershell", "pwsh"):
        found = shutil.which(candidate)
        if found:
            return found
    pytest.skip("PowerShell is required for env-file wrapper validation.")


def _assert_no_forbidden(text: str) -> None:
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in text


def test_env_file_loader_script_exists_and_wrappers_expose_envfile() -> None:
    helper = _read("scripts/lib/ai-env-file.ps1")
    smoke = _read("scripts/demo-ai-live-smoke.ps1")
    evals = _read("scripts/run-openai-demo-evals.ps1")
    regression = _read("scripts/run-ai-29-30-regression.ps1")

    assert "Get-AiSafeEnvSummary" in helper
    assert "Import-AiEnvFile" in helper
    assert "Write-AiEnvDefaults" in helper
    assert "EnvFile" in smoke
    assert "WriteMissingEnvDefaults" in smoke
    assert "EnvFile" in evals
    assert "EnvFile" in regression

    _assert_no_forbidden("".join((helper, smoke, evals, regression)))


def test_docs_explain_envfile_loading_and_live_opt_in() -> None:
    docs = "\n".join(
        _read(path)
        for path in (
            "docs/ai-live-demo-runbook.md",
            "docs/live-openai-smoke-tests.md",
            "docs/live-openai-demo-evals.md",
            "docs/ai-29-30-regression-e2e-harness.md",
            "README.md",
            "docs/ai-feature-status.md",
            "docs/ai-evals-plan.md",
            "docs/ai-implementation-backlog.md",
        )
    )

    assert "-EnvFile .\\.env" in docs
    assert "-WriteMissingEnvDefaults" in docs
    assert "OPENAI_ENABLE_LIVE_TESTS=false" in docs
    assert "AI_PROVIDER=mock" in docs
    assert "never commit or paste" in docs
    assert ".env" in docs

    _assert_no_forbidden(docs)


def test_env_file_loader_script_runs_and_remains_safe() -> None:
    powershell = _powershell_executable()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts/test-ai-env-file-loader.ps1"),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    assert result.returncode == 0, output
    assert "SUMMARY: 5 passed, 0 failed" in output
    assert "PASS: live smoke skips when OPENAI_ENABLE_LIVE_TESTS is false" in output
    _assert_no_forbidden(output)


def test_env_file_docs_do_not_expose_secret_examples() -> None:
    docs = "\n".join(
        _read(path)
        for path in (
            "docs/live-openai-smoke-tests.md",
            "docs/live-openai-demo-evals.md",
            "docs/ai-live-demo-runbook.md",
        )
    )
    _assert_no_forbidden(docs)
