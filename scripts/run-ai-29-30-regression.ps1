param(
    [string]$EnvFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")

if (-not [string]::IsNullOrWhiteSpace($EnvFile)) {
    Import-AiEnvFile -Path $EnvFile -OnlyIfMissing | Out-Null
    Write-Host "Loaded env file summary:"
    Get-AiSafeEnvSummary | ForEach-Object { Write-Host $_ }
}

if ([string]::IsNullOrWhiteSpace($env:AI_PROVIDER)) {
    $env:AI_PROVIDER = "mock"
}

if ([string]::IsNullOrWhiteSpace($env:OPENAI_ENABLE_LIVE_TESTS)) {
    $env:OPENAI_ENABLE_LIVE_TESTS = "false"
}

if ([string]::IsNullOrWhiteSpace($env:AI_PROVIDER_CALLS_ENABLED)) {
    $env:AI_PROVIDER_CALLS_ENABLED = "true"
}

if ([string]::IsNullOrWhiteSpace($env:AI_PROVIDER_GLOBAL_DISABLE)) {
    $env:AI_PROVIDER_GLOBAL_DISABLE = "false"
}

if ([string]::IsNullOrWhiteSpace($env:AI_OPERATOR_GATE_ENABLED)) {
    $env:AI_OPERATOR_GATE_ENABLED = "false"
}

if ([string]::IsNullOrWhiteSpace($env:AI_INVITE_SESSIONS_ENABLED)) {
    $env:AI_INVITE_SESSIONS_ENABLED = "false"
}

if ([string]::IsNullOrWhiteSpace($env:AI_PROVIDER_BUDGET_MODE)) {
    $env:AI_PROVIDER_BUDGET_MODE = "enforce"
}

$LiveSmokeEnabled = $env:AI_29_30_REGRESSION_LIVE -eq "true"

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Running 29/30 regression harness..."
$Args = @("scripts\e2e-ai-29-30-regression.py")
if ($LiveSmokeEnabled) {
    $Args += "--live-smoke"
}

& $Python @Args
$ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
    Write-Host "PASS: 29/30 regression harness"
} else {
    Write-Host "FAIL: 29/30 regression harness"
}
exit $ExitCode
