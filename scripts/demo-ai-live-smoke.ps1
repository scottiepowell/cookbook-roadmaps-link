param(
    [string]$EnvFile,
    [switch]$WriteMissingEnvDefaults
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")

$SmokeDefaults = [ordered]@{
    AI_PROVIDER = "openai"
    OPENAI_ENABLE_LIVE_TESTS = "false"
    OPENAI_MODEL = "gpt-5.4-nano"
    OPENAI_FALLBACK_MODEL = "gpt-5.4-mini"
    AI_MAX_OUTPUT_TOKENS = "300"
    AI_TIMEOUT_SECONDS = "60"
    OPENAI_LIVE_TEST_BUDGET_CENTS = "25"
    AI_PROVIDER_CALLS_ENABLED = "true"
    AI_PROVIDER_GLOBAL_DISABLE = "false"
    AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION = "2"
    AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL = "12000"
    AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL = "300"
    AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL = "14000"
    AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION = "0.25"
    AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL = "0.05"
    AI_PROVIDER_BUDGET_MODE = "enforce"
}

if (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
    if ($WriteMissingEnvDefaults) {
        $Appended = Write-AiEnvDefaults -Path $EnvFile -Defaults $SmokeDefaults -OnlyMissing
        if ($Appended.Count -gt 0) {
            Write-Host ("Updated env file with safe defaults: {0}" -f ($Appended -join ", "))
        } else {
            Write-Host "Safe env defaults already present."
        }
    }

    Import-AiEnvFile -Path $EnvFile -OnlyIfMissing | Out-Null
    Write-Host "Loaded env file summary:"
    Get-AiSafeEnvSummary | ForEach-Object { Write-Host $_ }
}

if ($env:OPENAI_ENABLE_LIVE_TESTS -ne "true") {
    Write-Host "Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in."
    exit 0
}

if ($env:AI_PROVIDER -ne "openai") {
    Write-Host "Live smoke skipped: set AI_PROVIDER=openai to opt in."
    exit 0
}

if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    Write-Host "Live smoke skipped: OPENAI_API_KEY is not present in the process environment."
    Write-Host "The Python smoke script can also read an ignored local .env file."
}

if ([string]::IsNullOrWhiteSpace($env:OPENAI_LIVE_TEST_BUDGET_CENTS)) {
    $env:OPENAI_LIVE_TEST_BUDGET_CENTS = "25"
}

if ([string]::IsNullOrWhiteSpace($env:AI_MAX_OUTPUT_TOKENS)) {
    $env:AI_MAX_OUTPUT_TOKENS = "200"
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python "scripts\smoke-openai-live.py"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($env:AI_29_30_REGRESSION_LIVE -eq "true") {
    Write-Host "Running optional 29/30 regression live boundary..."
    & $Python "scripts\e2e-ai-29-30-regression.py" --live-smoke
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
