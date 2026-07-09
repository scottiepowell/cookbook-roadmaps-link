import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


def load_importer_smoke_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "smoke-openai-importer-live.py"
    spec = importlib.util.spec_from_file_location("smoke_openai_importer_live", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_wrapper(*, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[2]
    merged_env = os.environ.copy()
    if env is not None:
        merged_env.update(env)
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo_root / "scripts" / "smoke-openai-importer-live.ps1")],
        cwd=repo_root,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importer_live_guard_skips_when_not_enabled():
    module = load_importer_smoke_module()
    result = module.evaluate_live_guard({})

    assert result.should_run is False
    assert result.exit_code == 0
    assert "live OpenAI importer smoke tests are disabled" in result.message


def test_importer_live_guard_uses_safe_default_budget_and_tokens():
    module = load_importer_smoke_module()
    result = module.evaluate_live_guard(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_ENABLE_LIVE_TESTS": "true",
            "OPENAI_API_KEY": "fake-offline-key",
        }
    )

    assert result.should_run is True
    assert result.budget_cents == 25


def test_importer_live_wrapper_exposes_tuning_parameters():
    text = (Path(__file__).resolve().parents[2] / "scripts" / "smoke-openai-importer-live.ps1").read_text(encoding="utf-8")

    assert "[string]$Text" in text
    assert "[Nullable[int]]$MaxOutputTokens" in text
    assert "[Nullable[double]]$AiTimeoutSeconds" in text
    assert "[switch]$ProviderDebug" in text


def test_importer_live_success_summary_includes_counts():
    module = load_importer_smoke_module()
    response = SimpleNamespace(
        provider="openai",
        model="gpt-5.4-nano",
        draft=SimpleNamespace(
            title="Classic Cheesecake (Graham Cracker Crust)",
            servings=4,
            ingredients=[1, 2, 3],
            instructions=[1, 2, 3, 4],
        ),
        retrieval=SimpleNamespace(retrieved_count=3),
        citations=[1, 2],
        usage={"input_tokens": 100, "output_tokens": 508, "total_tokens": 1246},
    )

    summary = module.format_success_summary(response)

    assert "provider=openai" in summary
    assert "model=gpt-5.4-nano" in summary
    assert "title=Classic Cheesecake (Graham Cracker Crust)" in summary
    assert "servings=4" in summary
    assert "ingredient_count=3" in summary
    assert "instruction_count=4" in summary
    assert "retrieval_count=3" in summary
    assert "citation_count=2" in summary
    assert "usage_output_tokens=508" in summary
    assert "status=passed" in summary


def test_importer_live_wrapper_skips_without_opt_in():
    env = os.environ.copy()
    for name in ("AI_PROVIDER", "OPENAI_ENABLE_LIVE_TESTS", "OPENAI_API_KEY", "OPENAI_LIVE_TEST_BUDGET_CENTS"):
        env.pop(name, None)

    result = run_wrapper(env=env)

    assert result.returncode == 0
    assert "SKIP:" in result.stdout
    assert "live OpenAI importer smoke tests are disabled" in result.stdout


def test_importer_live_wrapper_has_valid_powershell_syntax():
    wrapper = Path(__file__).resolve().parents[2] / "scripts" / "smoke-openai-importer-live.ps1"
    command = (
        "$tokens = $null; "
        "$errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{wrapper}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { "
        '$errors | ForEach-Object { Write-Error $_.Message }; '
        "exit 1 }"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
