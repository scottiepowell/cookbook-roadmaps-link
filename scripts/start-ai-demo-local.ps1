param(
    [int]$Port = 8000,
    [string]$DemoDataDir = ".tmp-ai-demo\local",
    [string]$EnvFile = ".env",
    [ValidateSet("mock", "openai")]
    [string]$Provider = "mock",
    [string]$OpenAIModel = "",
    [string]$RecipeDatasetDir = "",
    [Nullable[int]]$RecipeDatasetIndexLimit = $null,
    [Nullable[int]]$MaxOutputTokens = $null,
    [Nullable[int]]$LiveTestBudgetCents = $null,
    [Nullable[double]]$AiTimeoutSeconds = $null,
    [switch]$ProviderDebug,
    [switch]$EnableLiveTests,
    [switch]$WriteMissingLiveDefaults,
    [switch]$CheckRuntimeProfile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptParameters = $PSBoundParameters

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")

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

$LocalLiveDefaults = [ordered]@{
    AI_PROVIDER = "openai"
    OPENAI_ENABLE_LIVE_TESTS = "true"
    OPENAI_MODEL = "gpt-5.4-nano"
    AI_MAX_OUTPUT_TOKENS = "300"
    AI_TIMEOUT_SECONDS = "60"
    OPENAI_LIVE_TEST_BUDGET_CENTS = "25"
    AI_PROVIDER_CALLS_ENABLED = "true"
    AI_PROVIDER_GLOBAL_DISABLE = "false"
    AI_PROVIDER_BUDGET_MODE = "enforce"
}

if (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
    $ResolvedEnvFile = Resolve-AbsolutePathString -PathValue $EnvFile
    if ($WriteMissingLiveDefaults) {
        $Appended = Write-AiEnvDefaults -Path $ResolvedEnvFile -Defaults $LocalLiveDefaults -OnlyMissing
        if ($Appended.Count -gt 0) {
            Write-Host ("Added safe local live defaults: {0}" -f ($Appended -join ", "))
        } else {
            Write-Host "Safe local live defaults already present."
        }
        Write-Host "Add OPENAI_API_KEY to your local ignored .env or process environment. Never commit or paste it."
    }
    if (Test-Path -LiteralPath $ResolvedEnvFile -PathType Leaf) {
        Import-AiEnvFile -Path $ResolvedEnvFile -OnlyIfMissing | Out-Null
        $LoadedLocalEnv = $true
    } else {
        $LoadedLocalEnv = $false
    }
} else {
    $LoadedLocalEnv = $false
}

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

$EffectiveProvider = (Get-ParameterOrEnv -Name "Provider" -Value $Provider -EnvName "AI_PROVIDER" -DefaultValue "mock").ToString().ToLowerInvariant()
if ($EffectiveProvider -notin @("mock", "openai")) {
    [Console]::Error.WriteLine("Invalid provider '$EffectiveProvider'. Use -Provider mock or -Provider openai.")
    exit 2
}

$EffectiveOpenAIModel = (Get-ParameterOrEnv -Name "OpenAIModel" -Value $OpenAIModel -EnvName "OPENAI_MODEL" -DefaultValue "gpt-5.4-nano").ToString()
$EffectiveRecipeDatasetIndexLimit = [int](Get-ParameterOrEnv -Name "RecipeDatasetIndexLimit" -Value $RecipeDatasetIndexLimit -EnvName "RECIPE_DATASET_INDEX_LIMIT" -DefaultValue 25)
$DefaultMaxOutputTokens = 500
if ($EffectiveProvider -eq "openai") {
    $DefaultMaxOutputTokens = 300
}
$EffectiveMaxOutputTokens = [int](Get-ParameterOrEnv -Name "MaxOutputTokens" -Value $MaxOutputTokens -EnvName "AI_MAX_OUTPUT_TOKENS" -DefaultValue $DefaultMaxOutputTokens)
$EffectiveLiveTestBudgetCents = [int](Get-ParameterOrEnv -Name "LiveTestBudgetCents" -Value $LiveTestBudgetCents -EnvName "OPENAI_LIVE_TEST_BUDGET_CENTS" -DefaultValue 25)
$EffectiveAiTimeoutSeconds = [double](Get-ParameterOrEnv -Name "AiTimeoutSeconds" -Value $AiTimeoutSeconds -EnvName "AI_TIMEOUT_SECONDS" -DefaultValue 20)
$EffectiveProviderDebug = Get-ParameterOrEnvBool -Name "ProviderDebug" -Value ([bool]$ProviderDebug) -EnvName "AI_PROVIDER_DEBUG" -DefaultValue $false
$EffectiveLiveTestsEnabled = Get-ParameterOrEnvBool -Name "EnableLiveTests" -Value ([bool]$EnableLiveTests) -EnvName "OPENAI_ENABLE_LIVE_TESTS" -DefaultValue $false

if ($EffectiveMaxOutputTokens -lt 1) {
    [Console]::Error.WriteLine("AI_MAX_OUTPUT_TOKENS must be greater than 0.")
    exit 2
}

if ($EffectiveLiveTestBudgetCents -lt 1 -or $EffectiveLiveTestBudgetCents -gt 25) {
    [Console]::Error.WriteLine("OPENAI_LIVE_TEST_BUDGET_CENTS must be between 1 and 25.")
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
    if ($EffectiveOpenAIModel -ne "gpt-5.4-nano") {
        [Console]::Error.WriteLine("Provider=openai only supports OPENAI_MODEL=gpt-5.4-nano for the local product.")
        exit 2
    }

    if ($EffectiveMaxOutputTokens -gt 300) {
        [Console]::Error.WriteLine("AI_MAX_OUTPUT_TOKENS must be between 1 and 300 for local live mode.")
        exit 2
    }

    if (-not $EffectiveLiveTestsEnabled) {
        [Console]::Error.WriteLine("Provider=openai requires -EnableLiveTests or existing OPENAI_ENABLE_LIVE_TESTS=true. This prevents accidental live provider calls.")
        exit 2
    }

    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("OPENAI_API_KEY"))) {
        [Console]::Error.WriteLine("Provider=openai requires OPENAI_API_KEY to be set in the environment. The script will not prompt for or print the key.")
        exit 2
    }
}

$DisplayModel = "mock-basic"
if ($EffectiveProvider -eq "openai") {
    $DisplayModel = $EffectiveOpenAIModel
} elseif (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("AI_MODEL"))) {
    $DisplayModel = [Environment]::GetEnvironmentVariable("AI_MODEL")
}

function Write-SafeStartupSummary {
    Write-Host ""
    Write-Host ("Local ignored config loaded: {0}" -f $LoadedLocalEnv.ToString().ToLowerInvariant())
    Write-Host "Provider: $EffectiveProvider"
    Write-Host "Model: $DisplayModel"
    Write-Host "Live tests enabled: $($EffectiveLiveTestsEnabled.ToString().ToLowerInvariant())"
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable("OPENAI_API_KEY"))) {
        Write-Host "OpenAI API key: missing"
    } else {
        Write-Host "OpenAI API key: redacted-present"
    }
    Write-Host "Budget cents: $EffectiveLiveTestBudgetCents"
    Write-Host "Max output tokens: $EffectiveMaxOutputTokens"
    Write-Host "AI timeout seconds: $EffectiveAiTimeoutSeconds"
    Write-Host "Provider debug: $($EffectiveProviderDebug.ToString().ToLowerInvariant())"
}

if ($CheckRuntimeProfile) {
    Write-SafeStartupSummary
    exit 0
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

Write-SafeStartupSummary
Write-Host "AI demo data is ready."
Write-Host "Open local product: http://127.0.0.1:$Port/product"
Write-Host "AI workspace remains available: http://127.0.0.1:$Port/demo"
Write-Host "Cookbook container target: http://127.0.0.1:3000/ (start Docker Compose separately)"
Write-Host "Fixture data: generated local demo database and dataset."
Write-Host "Dataset index limit: $env:RECIPE_DATASET_INDEX_LIMIT"
Write-Host "Logs will print in this terminal. Stop with Ctrl+C."
Write-Host ""

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
