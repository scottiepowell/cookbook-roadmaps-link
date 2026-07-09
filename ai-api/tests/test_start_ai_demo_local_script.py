import subprocess
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


def test_start_ai_demo_local_uses_live_manual_demo_defaults():
    text = read_script()

    assert '"gpt-5.4-nano"' in text
    assert "AI_MAX_OUTPUT_TOKENS" in text
    assert "OPENAI_LIVE_TEST_BUDGET_CENTS" in text
    assert "$DefaultMaxOutputTokens = 500" in text
    assert "$DefaultMaxOutputTokens = 900" in text
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


def test_start_ai_demo_local_keeps_mock_launch_safe_by_default():
    text = read_script()

    assert '[string]$Provider = "mock"' in text
    assert '"Provider=openai requires -EnableLiveTests' in text
    assert '$env:OPENAI_ENABLE_LIVE_TESTS = "true"' in text
    assert 'Get-ParameterOrEnv -Name "RecipeDatasetDir"' in text
    assert 'DefaultValue $DefaultRecipeDatasetDir' in text
    assert '$env:AI_PROVIDER_DEBUG = $EffectiveProviderDebug.ToString().ToLowerInvariant()' in text


def test_start_ai_demo_local_prints_safe_summary_without_key_value():
    text = read_script()

    assert 'Write-Host "Provider: $EffectiveProvider"' in text
    assert 'Write-Host "Model: $DisplayModel"' in text
    assert 'Write-Host "Live tests enabled:' in text
    assert 'Write-Host "Budget cents:' in text
    assert 'Write-Host "Max output tokens:' in text
    assert 'Write-Host "AI timeout seconds:' in text
    assert 'Write-Host "Provider debug:' in text
    assert 'Write-Host "Cookbook DB path:' in text
    assert 'Write-Host "Dataset path:' in text
    assert 'Write-Host "Dataset index limit:' in text
    assert 'Write-Host "OPENAI_API_KEY' not in text


def test_ai_live_demo_runbook_documents_full_dataset_rag_launch():
    text = (Path(__file__).resolve().parents[2] / "docs" / "ai-live-demo-runbook.md").read_text(encoding="utf-8")

    assert "-MaxOutputTokens 900" in text
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
