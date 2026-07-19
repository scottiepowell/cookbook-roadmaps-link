import subprocess
import os
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "start-ai-demo-local.ps1"
REPO_ROOT = SCRIPT.parents[1]


def read_script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_start_ai_demo_local_supports_provider_override_parameters():
    text = read_script()

    assert '[ValidateSet("mock", "openai")]' in text
    assert "[string]$Provider" in text
    assert "[string]$OpenAIModel" in text
    assert "[string]$RecipeDatasetDir" in text
    assert "[Nullable[int]]$RecipeDatasetIndexLimit" in text
    assert "[Nullable[int]]$MaxOutputTokens" in text
    assert "[Nullable[int]]$LiveTestBudgetCents" in text
    assert "[Nullable[double]]$AiTimeoutSeconds" in text
    assert "[switch]$ProviderDebug" in text
    assert "[switch]$EnableLiveTests" in text
    assert '[string]$EnvFile = ".env"' in text
    assert "[switch]$WriteMissingLiveDefaults" in text
    assert "[switch]$CheckRuntimeProfile" in text


def test_start_ai_demo_local_uses_safe_live_profile_defaults():
    text = read_script()

    assert '"gpt-5.4-nano"' in text
    assert "AI_MAX_OUTPUT_TOKENS" in text
    assert "OPENAI_LIVE_TEST_BUDGET_CENTS" in text
    assert "$DefaultMaxOutputTokens = 500" in text
    assert "$DefaultMaxOutputTokens = 300" in text
    assert "DefaultValue 25" in text


def test_start_ai_demo_local_requires_api_key_only_for_openai():
    text = read_script()

    assert 'if ($EffectiveProvider -eq "openai")' in text
    assert "OPENAI_API_KEY" in text
    assert "requires OPENAI_API_KEY" in text


def test_start_ai_demo_local_does_not_force_mock_provider():
    text = read_script()

    assert '$env:AI_PROVIDER = "mock"' not in text
    assert "$env:AI_PROVIDER = $EffectiveProvider" in text


def test_start_ai_demo_local_loads_ignored_env_before_falling_back_to_mock():
    text = read_script()

    assert "Import-AiEnvFile -Path $ResolvedEnvFile -OnlyIfMissing" in text
    assert '$LocalLiveDefaults = [ordered]@{' in text
    assert 'AI_PROVIDER = "openai"' in text
    assert '"Provider=openai requires -EnableLiveTests' in text
    assert '$env:OPENAI_ENABLE_LIVE_TESTS = "true"' in text
    assert 'Get-ParameterOrEnv -Name "RecipeDatasetDir"' in text
    assert 'DefaultValue $DefaultRecipeDatasetDir' in text
    assert '$env:AI_PROVIDER_DEBUG = $EffectiveProviderDebug.ToString().ToLowerInvariant()' in text


def test_start_ai_demo_local_prints_safe_summary_without_key_value():
    text = read_script()

    assert 'Write-Host "OpenAI API key: redacted-present"' in text
    assert 'Write-Host "OpenAI API key: missing"' in text
    assert 'Write-Host "Model: $DisplayModel"' in text
    assert 'Write-Host "Live tests enabled:' in text
    assert 'Write-Host "Budget cents:' in text
    assert 'Write-Host "Max output tokens:' in text
    assert 'Write-Host "AI timeout seconds:' in text
    assert 'Write-Host "Provider debug:' in text
    assert 'Write-Host "Fixture data: generated local demo database and dataset."' in text
    assert 'Write-Host "Dataset index limit:' in text
    assert 'Write-Host "OPENAI_API_KEY' not in text


def test_ai_live_demo_runbook_documents_full_dataset_rag_launch():
    text = (Path(__file__).resolve().parents[2] / "docs" / "ai-live-demo-runbook.md").read_text(encoding="utf-8")

    assert "-MaxOutputTokens 300" in text
    assert "-RecipeDatasetDir recipe-dataset" in text
    assert "-RecipeDatasetIndexLimit 5000" in text
    assert "-ProviderDebug" in text
    assert "generated `.tmp-ai-demo` fixture dataset" in text
    assert "only three records" in text


def test_start_ai_demo_local_has_valid_powershell_syntax():
    command = (
        "$tokens = $null; "
        "$errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{SCRIPT}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { "
        '$errors | ForEach-Object { Write-Error $_.Message }; '
        "exit 1 }"
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def _check_runtime_profile(env_file: Path, *, provider: str | None = None):
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-EnvFile",
        str(env_file),
        "-CheckRuntimeProfile",
    ]
    if provider:
        command.extend(["-Provider", provider])
    env = os.environ.copy()
    for name in ("AI_PROVIDER", "OPENAI_ENABLE_LIVE_TESTS", "OPENAI_API_KEY", "OPENAI_MODEL", "AI_MAX_OUTPUT_TOKENS"):
        env.pop(name, None)
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, env=env)


def test_start_script_resolves_fake_local_live_env_without_exposing_key(tmp_path):
    env_file = tmp_path / "fake.env"
    env_file.write_text(
        "\n".join(
            (
                "AI_PROVIDER=openai",
                "OPENAI_ENABLE_LIVE_TESTS=true",
                "OPENAI_API_KEY=fake-local-test-key",
                "OPENAI_MODEL=gpt-5.4-nano",
                "AI_MAX_OUTPUT_TOKENS=300",
                "OPENAI_LIVE_TEST_BUDGET_CENTS=25",
                "AI_TIMEOUT_SECONDS=60",
            )
        ),
        encoding="utf-8",
    )

    result = _check_runtime_profile(env_file)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Provider: openai" in result.stdout
    assert "Model: gpt-5.4-nano" in result.stdout
    assert "OpenAI API key: redacted-present" in result.stdout
    assert "fake-local-test-key" not in result.stdout


def test_start_script_reports_missing_live_key_safely(tmp_path):
    env_file = tmp_path / "missing-key.env"
    env_file.write_text(
        "AI_PROVIDER=openai\nOPENAI_ENABLE_LIVE_TESTS=true\nOPENAI_MODEL=gpt-5.4-nano\n",
        encoding="utf-8",
    )

    result = _check_runtime_profile(env_file)

    assert result.returncode == 2
    assert "requires OPENAI_API_KEY" in result.stderr
    assert "OPENAI_API_KEY=" not in result.stderr


def test_start_script_explicit_mock_override_and_safe_default_initialization(tmp_path):
    env_file = tmp_path / "new-local.env"
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-EnvFile",
        str(env_file),
        "-Provider",
        "mock",
        "-WriteMissingLiveDefaults",
        "-CheckRuntimeProfile",
    ]
    env = os.environ.copy()
    for name in ("AI_PROVIDER", "OPENAI_ENABLE_LIVE_TESTS", "OPENAI_API_KEY", "OPENAI_MODEL", "AI_MAX_OUTPUT_TOKENS"):
        env.pop(name, None)
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False, env=env)

    assert result.returncode == 0, result.stderr or result.stdout
    assert "Provider: mock" in result.stdout
    contents = env_file.read_text(encoding="utf-8")
    assert "AI_PROVIDER=openai" in contents
    assert "OPENAI_API_KEY" not in contents


def test_local_env_example_and_ignore_rules_keep_secrets_out_of_git():
    example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    ignore_rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in ignore_rules
    assert "!.env.example" in ignore_rules
    assert "OPENAI_API_KEY=" in example
    assert "OPENAI_API_KEY=fake" not in example
    assert "OPENAI_API_KEY=sk-" not in example
    assert "OPENAI_MODEL=gpt-5.4-nano" in example
