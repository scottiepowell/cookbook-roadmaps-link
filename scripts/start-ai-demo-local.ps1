param(
    [int]$Port = 8000,
    [string]$DemoDataDir = ".tmp-ai-demo\local",
    [ValidateSet("mock", "openai")]
    [string]$Provider = "mock",
    [string]$OpenAIModel = "",
    [Nullable[int]]$MaxOutputTokens = $null,
    [Nullable[int]]$LiveTestBudgetCents = $null,
    [switch]$EnableLiveTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptParameters = $PSBoundParameters

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

function Get-ParameterOrEnv {
    param(
        [string]$Name,
        [object]$Value,
        [string]$EnvName,
        [object]$DefaultValue
    )

    if ($ScriptParameters.ContainsKey($Name)) {
        return $Value
    }

    $EnvValue = [Environment]::GetEnvironmentVariable($EnvName)
    if (-not [string]::IsNullOrWhiteSpace($EnvValue)) {
        return $EnvValue
    }

    return $DefaultValue
}

$EffectiveProvider = (Get-ParameterOrEnv -Name "Provider" -Value $Provider -EnvName "AI_PROVIDER" -DefaultValue "mock").ToString().ToLowerInvariant()
if ($EffectiveProvider -notin @("mock", "openai")) {
    [Console]::Error.WriteLine("Invalid provider '$EffectiveProvider'. Use -Provider mock or -Provider openai.")
    exit 2
}

$EffectiveOpenAIModel = (Get-ParameterOrEnv -Name "OpenAIModel" -Value $OpenAIModel -EnvName "OPENAI_MODEL" -DefaultValue "gpt-5.4-nano").ToString()
$EffectiveMaxOutputTokens = [int](Get-ParameterOrEnv -Name "MaxOutputTokens" -Value $MaxOutputTokens -EnvName "AI_MAX_OUTPUT_TOKENS" -DefaultValue 500)
$EffectiveLiveTestBudgetCents = [int](Get-ParameterOrEnv -Name "LiveTestBudgetCents" -Value $LiveTestBudgetCents -EnvName "OPENAI_LIVE_TEST_BUDGET_CENTS" -DefaultValue 25)
$ExistingLiveOptIn = [Environment]::GetEnvironmentVariable("OPENAI_ENABLE_LIVE_TESTS")
$EffectiveLiveTestsEnabled = $EnableLiveTests.IsPresent -or ($ExistingLiveOptIn -ieq "true")

if ($EffectiveMaxOutputTokens -lt 1) {
    [Console]::Error.WriteLine("AI_MAX_OUTPUT_TOKENS must be greater than 0.")
    exit 2
}

if ($EffectiveLiveTestBudgetCents -lt 1) {
    [Console]::Error.WriteLine("OPENAI_LIVE_TEST_BUDGET_CENTS must be greater than 0.")
    exit 2
}

if ($EffectiveProvider -eq "openai") {
    if (-not $EffectiveLiveTestsEnabled) {
        [Console]::Error.WriteLine("Provider=openai requires -EnableLiveTests or existing OPENAI_ENABLE_LIVE_TESTS=true. This prevents accidental live provider calls.")
        exit 2
    }

    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("OPENAI_API_KEY"))) {
        [Console]::Error.WriteLine("Provider=openai requires OPENAI_API_KEY to be set in the environment. The script will not prompt for or print the key.")
        exit 2
    }
}

$env:PYTHONPATH = "ai-api"
& $Python -m app.demo_data --output-dir $DemoDataDir
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ResolvedDataDir = Resolve-Path $DemoDataDir
$env:AI_PROVIDER = $EffectiveProvider
if ($EffectiveProvider -eq "openai") {
    $env:OPENAI_MODEL = $EffectiveOpenAIModel
    $env:OPENAI_ENABLE_LIVE_TESTS = "true"
    $env:OPENAI_LIVE_TEST_BUDGET_CENTS = $EffectiveLiveTestBudgetCents.ToString()
    $env:AI_MAX_OUTPUT_TOKENS = $EffectiveMaxOutputTokens.ToString()
}
$env:COOKBOOK_DB_PATH = Join-Path $ResolvedDataDir "recipes.sqlite"
$env:RECIPE_DATASET_DIR = Join-Path $ResolvedDataDir "dataset"
$env:RECIPE_DATASET_INDEX_LIMIT = "25"

$DisplayModel = "mock-basic"
if ($EffectiveProvider -eq "openai") {
    $DisplayModel = $EffectiveOpenAIModel
} elseif (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("AI_MODEL"))) {
    $DisplayModel = [Environment]::GetEnvironmentVariable("AI_MODEL")
}

Write-Host ""
Write-Host "AI demo data is ready."
Write-Host "Provider: $EffectiveProvider"
Write-Host "Model: $DisplayModel"
Write-Host "Live tests enabled: $($EffectiveLiveTestsEnabled.ToString().ToLowerInvariant())"
Write-Host "Budget cents: $EffectiveLiveTestBudgetCents"
Write-Host "Max output tokens: $EffectiveMaxOutputTokens"
Write-Host "Open: http://127.0.0.1:$Port/demo"
Write-Host "Cookbook DB path: $env:COOKBOOK_DB_PATH"
Write-Host "Dataset path: $env:RECIPE_DATASET_DIR"
Write-Host "Logs will print in this terminal. Stop with Ctrl+C."
Write-Host ""

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
