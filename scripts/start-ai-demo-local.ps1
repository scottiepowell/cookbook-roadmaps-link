param(
    [int]$Port = 8000,
    [string]$DemoDataDir = ".tmp-ai-demo\local",
    [ValidateSet("mock", "openai")]
    [string]$Provider = "mock",
    [string]$OpenAIModel = "",
    [string]$RecipeDatasetDir = "",
    [Nullable[int]]$RecipeDatasetIndexLimit = $null,
    [Nullable[int]]$MaxOutputTokens = $null,
    [Nullable[int]]$LiveTestBudgetCents = $null,
    [Nullable[double]]$AiTimeoutSeconds = $null,
    [switch]$ProviderDebug,
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

function Get-ParameterOrEnvBool {
    param(
        [string]$Name,
        [bool]$Value,
        [string]$EnvName,
        [bool]$DefaultValue
    )

    if ($ScriptParameters.ContainsKey($Name)) {
        return $Value
    }

    $EnvValue = [Environment]::GetEnvironmentVariable($EnvName)
    if ([string]::IsNullOrWhiteSpace($EnvValue)) {
        return $DefaultValue
    }

    return $EnvValue.Trim().ToLowerInvariant() -in @("1", "true", "yes", "on")
}

function Resolve-AbsolutePathString {
    param(
        [string]$PathValue
    )

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return $PathValue
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return [System.IO.Path]::GetFullPath($PathValue)
    }

    return [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $PathValue))
}

$EffectiveProvider = (Get-ParameterOrEnv -Name "Provider" -Value $Provider -EnvName "AI_PROVIDER" -DefaultValue "mock").ToString().ToLowerInvariant()
if ($EffectiveProvider -notin @("mock", "openai")) {
    [Console]::Error.WriteLine("Invalid provider '$EffectiveProvider'. Use -Provider mock or -Provider openai.")
    exit 2
}

$EffectiveOpenAIModel = (Get-ParameterOrEnv -Name "OpenAIModel" -Value $OpenAIModel -EnvName "OPENAI_MODEL" -DefaultValue "gpt-5.4-nano").ToString()
$EffectiveRecipeDatasetIndexLimit = [int](Get-ParameterOrEnv -Name "RecipeDatasetIndexLimit" -Value $RecipeDatasetIndexLimit -EnvName "RECIPE_DATASET_INDEX_LIMIT" -DefaultValue 25)
$EffectiveMaxOutputTokens = [int](Get-ParameterOrEnv -Name "MaxOutputTokens" -Value $MaxOutputTokens -EnvName "AI_MAX_OUTPUT_TOKENS" -DefaultValue 500)
$EffectiveLiveTestBudgetCents = [int](Get-ParameterOrEnv -Name "LiveTestBudgetCents" -Value $LiveTestBudgetCents -EnvName "OPENAI_LIVE_TEST_BUDGET_CENTS" -DefaultValue 25)
$EffectiveAiTimeoutSeconds = [double](Get-ParameterOrEnv -Name "AiTimeoutSeconds" -Value $AiTimeoutSeconds -EnvName "AI_TIMEOUT_SECONDS" -DefaultValue 20)
$EffectiveProviderDebug = Get-ParameterOrEnvBool -Name "ProviderDebug" -Value ([bool]$ProviderDebug) -EnvName "AI_PROVIDER_DEBUG" -DefaultValue $false
$EffectiveLiveTestsEnabled = Get-ParameterOrEnvBool -Name "EnableLiveTests" -Value ([bool]$EnableLiveTests) -EnvName "OPENAI_ENABLE_LIVE_TESTS" -DefaultValue $false

if ($EffectiveMaxOutputTokens -lt 1) {
    [Console]::Error.WriteLine("AI_MAX_OUTPUT_TOKENS must be greater than 0.")
    exit 2
}

if ($EffectiveLiveTestBudgetCents -lt 1) {
    [Console]::Error.WriteLine("OPENAI_LIVE_TEST_BUDGET_CENTS must be greater than 0.")
    exit 2
}

if ($EffectiveRecipeDatasetIndexLimit -lt 1 -or $EffectiveRecipeDatasetIndexLimit -gt 5000) {
    [Console]::Error.WriteLine("RECIPE_DATASET_INDEX_LIMIT must be between 1 and 5000.")
    exit 2
}

if ($EffectiveAiTimeoutSeconds -le 0) {
    [Console]::Error.WriteLine("AI_TIMEOUT_SECONDS must be greater than 0.")
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
$DefaultRecipeDatasetDir = Join-Path $ResolvedDataDir "dataset"
$EffectiveRecipeDatasetDir = Resolve-AbsolutePathString (
    Get-ParameterOrEnv -Name "RecipeDatasetDir" -Value $RecipeDatasetDir -EnvName "RECIPE_DATASET_DIR" -DefaultValue $DefaultRecipeDatasetDir
)
$env:AI_PROVIDER = $EffectiveProvider
$env:AI_TIMEOUT_SECONDS = $EffectiveAiTimeoutSeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)
$env:AI_PROVIDER_DEBUG = $EffectiveProviderDebug.ToString().ToLowerInvariant()
$env:RECIPE_DATASET_INDEX_LIMIT = $EffectiveRecipeDatasetIndexLimit.ToString()
if (-not [string]::IsNullOrWhiteSpace($EffectiveRecipeDatasetDir)) {
    $env:RECIPE_DATASET_DIR = $EffectiveRecipeDatasetDir
}
if ($EffectiveProvider -eq "openai") {
    $env:OPENAI_MODEL = $EffectiveOpenAIModel
    $env:OPENAI_ENABLE_LIVE_TESTS = "true"
    $env:OPENAI_LIVE_TEST_BUDGET_CENTS = $EffectiveLiveTestBudgetCents.ToString()
    $env:AI_MAX_OUTPUT_TOKENS = $EffectiveMaxOutputTokens.ToString()
}
$env:COOKBOOK_DB_PATH = Join-Path $ResolvedDataDir "recipes.sqlite"

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
Write-Host "AI timeout seconds: $EffectiveAiTimeoutSeconds"
Write-Host "Provider debug: $($EffectiveProviderDebug.ToString().ToLowerInvariant())"
Write-Host "Open: http://127.0.0.1:$Port/demo"
Write-Host "Cookbook DB path: $env:COOKBOOK_DB_PATH"
Write-Host "Dataset path: $env:RECIPE_DATASET_DIR"
Write-Host "Dataset index limit: $env:RECIPE_DATASET_INDEX_LIMIT"
Write-Host "Logs will print in this terminal. Stop with Ctrl+C."
Write-Host ""

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
