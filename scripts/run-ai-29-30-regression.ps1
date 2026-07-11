Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$LiveSmokeEnabled = $env:AI_29_30_REGRESSION_LIVE -eq "true"

if ($LiveSmokeEnabled) {
    $env:AI_PROVIDER = "openai"
    $env:OPENAI_ENABLE_LIVE_TESTS = "true"
    if ([string]::IsNullOrWhiteSpace($env:AI_MAX_OUTPUT_TOKENS)) {
        $env:AI_MAX_OUTPUT_TOKENS = "200"
    }
} else {
    $env:AI_PROVIDER = "mock"
    $env:OPENAI_ENABLE_LIVE_TESTS = "false"
    $env:AI_OPERATOR_GATE_ENABLED = "false"
    $env:AI_INVITE_SESSIONS_ENABLED = "false"
    $env:AI_PROVIDER_CALLS_ENABLED = "true"
    $env:AI_PROVIDER_GLOBAL_DISABLE = "false"
    Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:AI_OPERATOR_GATE_TOKEN_FINGERPRINT -ErrorAction SilentlyContinue
    Remove-Item Env:AI_OPERATOR_GATE_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:AI_OPERATOR_GATE_ALLOWED_WORKFLOWS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_OPERATOR_GATE_LOCAL_BYPASS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_SESSION_TTL_SECONDS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_GRANT_TTL_SECONDS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_MAX_SESSIONS_PER_GRANT -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_ALLOWED_WORKFLOWS -ErrorAction SilentlyContinue
    Remove-Item Env:AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_BUDGET_MODE -ErrorAction SilentlyContinue
    Remove-Item Env:AI_PROVIDER_BUDGET_SESSION_ID -ErrorAction SilentlyContinue
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
