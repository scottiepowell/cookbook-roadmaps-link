Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

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
