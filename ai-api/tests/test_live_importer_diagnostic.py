from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "diagnose-live-importer.ps1"


def _powershell() -> str:
    for candidate in ("powershell", "pwsh"):
        value = shutil.which(candidate)
        if value:
            return value
    pytest.skip("PowerShell is required for the bounded diagnostic tests.")


def _run(env_file: Path, *, approve: bool = False, preflight: bool = False, max_output_tokens: int | None = None, env: dict[str, str] | None = None, helper: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-EnvFile", str(env_file)]
    if approve:
        command.append("-ApproveLiveCall")
    if preflight:
        command.append("-PreflightOnly")
    if max_output_tokens is not None:
        command.extend(["-MaxOutputTokens", str(max_output_tokens)])
    if helper is not None:
        command.extend(["-HelperPath", str(helper)])
    merged = os.environ.copy()
    for name in (
        "AI_PROVIDER",
        "AI_MODEL",
        "OPENAI_ENABLE_LIVE_TESTS",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_LIVE_TEST_BUDGET_CENTS",
        "AI_MAX_OUTPUT_TOKENS",
        "AI_TIMEOUT_SECONDS",
        "AI_PROVIDER_CALLS_ENABLED",
        "AI_PROVIDER_GLOBAL_DISABLE",
    ):
        merged.pop(name, None)
    if env:
        merged.update(env)
    return subprocess.run(command, cwd=REPO_ROOT, env=merged, capture_output=True, text=True, check=False)


def _write_env(tmp_path: Path, **values: str) -> Path:
    path = tmp_path / "fake.env"
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
    return path


def test_diagnostic_requires_explicit_approval_without_call(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_API_KEY="fake-offline-key",
        OPENAI_MODEL="gpt-5.4-nano",
        AI_MODEL="gpt-5.4-nano",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    result = _run(env_file)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "status=blocked" in output
    assert "safe_unavailable_category=operator_approval_required" in output
    assert "fake-offline-key" not in output
    assert "No provider call was attempted." in output
    assert "requested_max_output_tokens=300" in output


def test_explicit_1000_token_preflight_is_accepted_without_call(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_API_KEY="fake-offline-key",
        OPENAI_MODEL="gpt-5.4-nano",
        AI_MODEL="gpt-5.4-nano",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    result = _run(env_file, preflight=True, max_output_tokens=1000)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "requested_max_output_tokens=1000" in output
    assert "token_config=valid" in output
    assert "safe_unavailable_category=operator_approval_required" in output
    assert "No provider call was attempted." in output


def test_explicit_cap_above_1000_is_rejected_safely(tmp_path: Path) -> None:
    env_file = _write_env(tmp_path, AI_PROVIDER="openai", OPENAI_ENABLE_LIVE_TESTS="true", OPENAI_API_KEY="fake-offline-key", OPENAI_MODEL="gpt-5.4-nano", AI_MODEL="gpt-5.4-nano", OPENAI_LIVE_TEST_BUDGET_CENTS="25", AI_MAX_OUTPUT_TOKENS="300", AI_TIMEOUT_SECONDS="60")
    result = _run(env_file, approve=True, max_output_tokens=1001)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "requested_max_output_tokens=1001" in output
    assert "token_config=invalid" in output
    assert "No provider call was attempted." in output
    assert "fake-offline-key" not in output


def test_approved_explicit_cap_is_passed_to_helper(tmp_path: Path) -> None:
    env_file = _write_env(tmp_path, AI_PROVIDER="openai", OPENAI_ENABLE_LIVE_TESTS="true", OPENAI_API_KEY="fake-offline-key", OPENAI_MODEL="gpt-5.4-nano", AI_MODEL="gpt-5.4-nano", OPENAI_LIVE_TEST_BUDGET_CENTS="25", AI_MAX_OUTPUT_TOKENS="300", AI_TIMEOUT_SECONDS="60")
    helper = tmp_path / "fake-helper.ps1"
    marker = tmp_path / "helper-args.txt"
    helper.write_text(f'Set-Content -LiteralPath "{marker}" -Value ($args -join " ")\nWrite-Output ("provider_error_category=output_cap_or_incomplete_response")\nexit 1\n', encoding="utf-8")
    result = _run(env_file, approve=True, max_output_tokens=1000, helper=helper)
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "requested_max_output_tokens=1000" in output
    assert "safe_unavailable_category=output_cap_or_incomplete_response" in output
    assert "--max-output-tokens 1000" in marker.read_text(encoding="utf-8")
    assert "--ai-timeout-seconds 60" in marker.read_text(encoding="utf-8")


def test_diagnostic_missing_key_stops_before_call(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_MODEL="gpt-5.4-nano",
        AI_MODEL="gpt-5.4-nano",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    result = _run(env_file, approve=True)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "safe_unavailable_category=missing_api_key" in output
    assert "No provider call was attempted." in output


def test_diagnostic_rejects_unsupported_model_safely(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_API_KEY="fake-offline-key",
        OPENAI_MODEL="not-allowed",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    result = _run(env_file, approve=True)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "safe_unavailable_category=model_not_allowed" in output
    assert "fake-offline-key" not in output


@pytest.mark.parametrize(
    ("field", "expected_guidance"),
    (
        ("AI_MODEL", "AI_MODEL is set to a value outside"),
        ("OPENAI_MODEL", "OPENAI_MODEL is set to a value outside"),
    ),
)
def test_diagnostic_identifies_stale_model_field(tmp_path: Path, field: str, expected_guidance: str) -> None:
    values = {
        "AI_PROVIDER": "openai",
        "OPENAI_ENABLE_LIVE_TESTS": "true",
        "OPENAI_API_KEY": "fake-offline-key",
        "OPENAI_MODEL": "gpt-5.4-nano",
        "AI_MODEL": "gpt-5.4-nano",
        "OPENAI_LIVE_TEST_BUDGET_CENTS": "25",
        "AI_MAX_OUTPUT_TOKENS": "300",
        "AI_TIMEOUT_SECONDS": "60",
    }
    values[field] = "mock-basic"
    result = _run(_write_env(tmp_path, **values), approve=True)
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "safe_unavailable_category=model_not_allowed" in output
    assert expected_guidance in output
    assert "provider_error" not in output


def test_valid_model_preflight_reports_allowed_without_call(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_API_KEY="fake-offline-key",
        OPENAI_MODEL=" gpt-5.4-nano ",
        AI_MODEL=" gpt-5.4-nano ",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    result = _run(env_file, env={"AI_MODEL": "gpt-5.4-nano"})
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "openai_model_status=allowed" in output
    assert "ai_model_status=allowed" in output
    assert "model_config=valid" in output
    assert "safe_unavailable_category=operator_approval_required" in output
    assert "No provider call was attempted." in output


def test_failed_helper_output_cap_is_safe_envelope_without_native_command_error(tmp_path: Path) -> None:
    env_file = _write_env(
        tmp_path,
        AI_PROVIDER="openai",
        OPENAI_ENABLE_LIVE_TESTS="true",
        OPENAI_API_KEY="fake-offline-key",
        OPENAI_MODEL="gpt-5.4-nano",
        AI_MODEL="gpt-5.4-nano",
        OPENAI_LIVE_TEST_BUDGET_CENTS="25",
        AI_MAX_OUTPUT_TOKENS="300",
        AI_TIMEOUT_SECONDS="60",
    )
    helper = tmp_path / "fake-helper.ps1"
    helper.write_text(
        'Write-Output "provider_error_category=output_cap_or_incomplete_response"\n'
        'Write-Output "provider_error_type=JSONDecodeError"\n'
        "exit 1\n",
        encoding="utf-8",
    )
    result = _run(env_file, approve=True, helper=helper)
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "status=failed" in output
    assert "safe_unavailable_category=output_cap_or_incomplete_response" in output
    assert "safe_provider_error_type=JSONDecodeError" in output
    assert "The bounded importer call reached the live provider path" in output
    assert "NativeCommandError" not in output
    assert "fake-offline-key" not in output
    assert "provider_error_category=" not in output


def test_diagnostic_script_contains_bounded_safety_contract() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "ApproveLiveCall" in text
    assert "gpt-5.4-nano" in text
    assert "smoke-openai-importer-live.py" in text
    assert "No retry was attempted." in text
    assert "scrambled eggs: 2 eggs, 1 tbsp butter" in text
    assert "--max-output-tokens $tokens" in text
    assert "MaxOutputTokens" in text
    assert "-gt 1000" in text
    for forbidden in ("sk-proj-", "Authorization: Bearer", "raw_provider_prompt", "raw_provider_response"):
        assert forbidden not in text
