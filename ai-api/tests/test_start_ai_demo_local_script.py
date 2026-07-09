from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "start-ai-demo-local.ps1"


def read_script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_start_ai_demo_local_supports_provider_override_parameters():
    text = read_script()

    assert '[ValidateSet("mock", "openai")]' in text
    assert "[string]$Provider" in text
    assert "[string]$OpenAIModel" in text
    assert "[Nullable[int]]$MaxOutputTokens" in text
    assert "[Nullable[int]]$LiveTestBudgetCents" in text
    assert "[switch]$EnableLiveTests" in text


def test_start_ai_demo_local_uses_live_manual_demo_defaults():
    text = read_script()

    assert '"gpt-5.4-nano"' in text
    assert "AI_MAX_OUTPUT_TOKENS" in text
    assert "OPENAI_LIVE_TEST_BUDGET_CENTS" in text
    assert "DefaultValue 500" in text
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


def test_start_ai_demo_local_prints_safe_summary_without_key_value():
    text = read_script()

    assert 'Write-Host "Provider: $EffectiveProvider"' in text
    assert 'Write-Host "Model: $DisplayModel"' in text
    assert 'Write-Host "Live tests enabled:' in text
    assert 'Write-Host "Budget cents:' in text
    assert 'Write-Host "Max output tokens:' in text
    assert 'Write-Host "Cookbook DB path:' in text
    assert 'Write-Host "Dataset path:' in text
    assert 'Write-Host "OPENAI_API_KEY' not in text
