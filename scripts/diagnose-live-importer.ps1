param(
    [string]$EnvFile = ".env",
    [switch]$ApproveLiveCall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")

function Write-SafeSummary {
    param([string]$Status, [string]$Category, [string]$Guidance)
    Write-Host "workflow=importer"
    Write-Host "requested_provider=openai"
    Write-Host "requested_model=gpt-5.4-nano"
    Write-Host ("api_key={0}" -f ($(if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) { "missing" } else { "redacted-present" })))
    Write-Host ("live_opt_in={0}" -f ($env:OPENAI_ENABLE_LIVE_TESTS -eq "true"))
    Write-Host ("budget_config={0}" -f $script:BudgetState)
    Write-Host ("token_config={0}" -f $script:TokenState)
    Write-Host ("timeout_config={0}" -f $script:TimeoutState)
    Write-Host "status=$Status"
    Write-Host "safe_unavailable_category=$Category"
    Write-Host "safe_guidance=$Guidance"
}

try {
    if (-not [string]::IsNullOrWhiteSpace($EnvFile) -and (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        Import-AiEnvFile -Path $EnvFile -OnlyIfMissing | Out-Null
    }
} catch {
    $script:BudgetState = "invalid"
    $script:TokenState = "invalid"
    $script:TimeoutState = "invalid"
    Write-SafeSummary -Status "blocked" -Category "unexpected_safe_internal_block" -Guidance "Local runtime configuration could not be loaded safely. No provider call was attempted."
    exit 0
}

$script:BudgetState = "valid"
$script:TokenState = "valid"
$script:TimeoutState = "valid"
$budget = 0
$tokens = 0
$timeout = 0.0
if (-not [int]::TryParse($env:OPENAI_LIVE_TEST_BUDGET_CENTS, [ref]$budget) -or $budget -lt 1 -or $budget -gt 25) { $script:BudgetState = "invalid" }
if (-not [int]::TryParse($env:AI_MAX_OUTPUT_TOKENS, [ref]$tokens) -or $tokens -lt 1 -or $tokens -gt 300) { $script:TokenState = "invalid" }
if (-not [double]::TryParse($env:AI_TIMEOUT_SECONDS, [ref]$timeout) -or $timeout -le 0) { $script:TimeoutState = "invalid" }

if (-not $ApproveLiveCall) {
    Write-SafeSummary -Status "blocked" -Category "operator_approval_required" -Guidance "Pass -ApproveLiveCall after reviewing the redacted preflight. No provider call was attempted."
    exit 0
}
if ($env:AI_PROVIDER -ne "openai" -or $env:OPENAI_ENABLE_LIVE_TESTS -ne "true") {
    Write-SafeSummary -Status "blocked" -Category "live_not_enabled" -Guidance "Set explicit local live opt-in and AI_PROVIDER=openai before approving this diagnostic. No provider call was attempted."
    exit 0
}
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    Write-SafeSummary -Status "blocked" -Category "missing_api_key" -Guidance "Add OPENAI_API_KEY to the ignored local environment, then rerun the bounded diagnostic. No provider call was attempted."
    exit 0
}
if ($env:OPENAI_MODEL -ne "gpt-5.4-nano" -or $env:AI_MODEL -and $env:AI_MODEL -ne "gpt-5.4-nano") {
    Write-SafeSummary -Status "blocked" -Category "model_not_allowed" -Guidance "Only gpt-5.4-nano is allowed for this diagnostic. No provider call was attempted."
    exit 0
}
if ($script:BudgetState -ne "valid") { Write-SafeSummary -Status "blocked" -Category "budget_not_configured" -Guidance "Configure a live-test budget from 1 to 25 cents. No provider call was attempted."; exit 0 }
if ($script:TokenState -ne "valid") { Write-SafeSummary -Status "blocked" -Category "budget_not_configured" -Guidance "Configure AI_MAX_OUTPUT_TOKENS from 1 to 300. No provider call was attempted."; exit 0 }
if ($script:TimeoutState -ne "valid") { Write-SafeSummary -Status "blocked" -Category "unexpected_safe_internal_block" -Guidance "Configure a positive AI timeout. No provider call was attempted."; exit 0 }
if ($env:AI_PROVIDER_CALLS_ENABLED -eq "false" -or $env:AI_PROVIDER_GLOBAL_DISABLE -eq "true") {
    Write-SafeSummary -Status "blocked" -Category "provider_calls_disabled" -Guidance "Provider calls are disabled by local safety settings. No provider call was attempted."
    exit 0
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) { $Python = "python" }
$captured = (& $Python "scripts\smoke-openai-importer-live.py" --max-output-tokens $tokens --ai-timeout-seconds $timeout 2>&1 | Out-String)
$exitCode = $LASTEXITCODE
if ($exitCode -eq 0) {
    Write-SafeSummary -Status "passed" -Category "none" -Guidance "One bounded importer call completed. No retry was attempted."
    exit 0
}

$category = "unexpected_safe_internal_block"
if ($captured -match "provider_error_category=([^\s]+)") {
    $rawCategory = $Matches[1]
    $category = switch ($rawCategory) {
        "timeout" { "provider_timeout"; break }
        "quota_or_rate_limit" { "provider_account_or_quota_unavailable"; break }
        "auth" { "provider_account_or_quota_unavailable"; break }
        "bad_model" { "model_not_allowed"; break }
        "network" { "provider_http_error_redacted"; break }
        default { "unexpected_safe_internal_block" }
    }
}
Write-SafeSummary -Status "failed" -Category $category -Guidance "The bounded importer call did not complete successfully. No retry was attempted."
exit 1
