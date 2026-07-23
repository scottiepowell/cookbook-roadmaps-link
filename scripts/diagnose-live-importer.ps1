param(
    [string]$EnvFile = ".env",
    [switch]$ApproveLiveCall,
    [switch]$PreflightOnly,
    [string]$HelperPath = "",
    [Nullable[int]]$MaxOutputTokens = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")
$script:RequestedMaxOutputTokens = if ($PSBoundParameters.ContainsKey("MaxOutputTokens")) { $MaxOutputTokens } else { "default" }

function Write-SafeSummary {
    param([string]$Status, [string]$Category, [string]$Guidance, [string]$ProviderErrorType = "")
    Write-Host "workflow=importer"
    Write-Host "requested_provider=openai"
    Write-Host "requested_model=gpt-5.4-nano"
    Write-Host "requested_max_output_tokens=$script:RequestedMaxOutputTokens"
    Write-Host "openai_model_status=$script:OpenAiModelState"
    Write-Host "ai_model_status=$script:AiModelState"
    Write-Host "model_config=$script:ModelState"
    Write-Host ("api_key={0}" -f ($(if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) { "missing" } else { "redacted-present" })))
    Write-Host ("live_opt_in={0}" -f ($env:OPENAI_ENABLE_LIVE_TESTS -eq "true"))
    Write-Host ("budget_config={0}" -f $script:BudgetState)
    Write-Host ("token_config={0}" -f $script:TokenState)
    Write-Host ("timeout_config={0}" -f $script:TimeoutState)
    Write-Host "status=$Status"
    Write-Host "safe_unavailable_category=$Category"
    if (-not [string]::IsNullOrWhiteSpace($ProviderErrorType)) {
        Write-Host "safe_provider_error_type=$ProviderErrorType"
    }
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
    $script:OpenAiModelState = "unknown"
    $script:AiModelState = "unknown"
    $script:ModelState = "invalid"
    Write-SafeSummary -Status "blocked" -Category "unexpected_safe_internal_block" -Guidance "Local runtime configuration could not be loaded safely. No provider call was attempted."
    exit 0
}

$script:BudgetState = "valid"
$script:TokenState = "valid"
$script:TimeoutState = "valid"
$script:OpenAiModelState = "missing"
$script:AiModelState = "missing"
$script:ModelState = "invalid"
$script:RequestedMaxOutputTokens = if ($PSBoundParameters.ContainsKey("MaxOutputTokens")) { $MaxOutputTokens } else { $null }
$allowedModel = "gpt-5.4-nano"
$openAiModel = if ($null -eq $env:OPENAI_MODEL) { "" } else { $env:OPENAI_MODEL.Trim() }
$aiModel = if ($null -eq $env:AI_MODEL) { "" } else { $env:AI_MODEL.Trim() }
if ($openAiModel -eq $allowedModel) { $script:OpenAiModelState = "allowed" } elseif (-not [string]::IsNullOrWhiteSpace($openAiModel)) { $script:OpenAiModelState = "not_allowed" }
if ($aiModel -eq $allowedModel) { $script:AiModelState = "allowed" } elseif (-not [string]::IsNullOrWhiteSpace($aiModel)) { $script:AiModelState = "not_allowed" }
if ($script:OpenAiModelState -eq "allowed" -and ($script:AiModelState -in @("allowed", "missing"))) { $script:ModelState = "valid" }
$budget = 0
$tokens = 0
$timeout = 0.0
if (-not [int]::TryParse($env:OPENAI_LIVE_TEST_BUDGET_CENTS, [ref]$budget) -or $budget -lt 1 -or $budget -gt 25) { $script:BudgetState = "invalid" }
if ($PSBoundParameters.ContainsKey("MaxOutputTokens")) {
    $tokens = $MaxOutputTokens
    if ($tokens -lt 1 -or $tokens -gt 1000) { $script:TokenState = "invalid" }
} elseif (-not [int]::TryParse($env:AI_MAX_OUTPUT_TOKENS, [ref]$tokens) -or $tokens -lt 1 -or $tokens -gt 300) {
    $script:TokenState = "invalid"
}
$script:RequestedMaxOutputTokens = $tokens
if (-not [double]::TryParse($env:AI_TIMEOUT_SECONDS, [ref]$timeout) -or $timeout -le 0) { $script:TimeoutState = "invalid" }

if ($env:AI_PROVIDER -ne "openai" -or $env:OPENAI_ENABLE_LIVE_TESTS -ne "true") {
    Write-SafeSummary -Status "blocked" -Category "live_not_enabled" -Guidance "Set explicit local live opt-in and AI_PROVIDER=openai before approving this diagnostic. No provider call was attempted."
    exit 0
}
if ($script:OpenAiModelState -ne "allowed") {
    Write-SafeSummary -Status "blocked" -Category "model_not_allowed" -Guidance "OPENAI_MODEL is set to a value outside the allowed live diagnostic model. Set OPENAI_MODEL to gpt-5.4-nano or clear the stale process value. No provider call was attempted."
    exit 0
}
if ($script:AiModelState -eq "not_allowed") {
    Write-SafeSummary -Status "blocked" -Category "model_not_allowed" -Guidance "AI_MODEL is set to a value outside the allowed live diagnostic model. Set both AI_MODEL and OPENAI_MODEL to gpt-5.4-nano or clear the stale process value. No provider call was attempted."
    exit 0
}
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    Write-SafeSummary -Status "blocked" -Category "missing_api_key" -Guidance "Add OPENAI_API_KEY to the ignored local environment, then rerun the bounded diagnostic. No provider call was attempted."
    exit 0
}
if ($script:BudgetState -ne "valid") { Write-SafeSummary -Status "blocked" -Category "budget_not_configured" -Guidance "Configure a live-test budget from 1 to 25 cents. No provider call was attempted."; exit 0 }
if ($script:TokenState -ne "valid") {
    $tokenGuidance = if ($PSBoundParameters.ContainsKey("MaxOutputTokens")) {
        "Pass -MaxOutputTokens from 1 to 1000 for this explicit diagnostic. No provider call was attempted."
    } else {
        "Configure AI_MAX_OUTPUT_TOKENS from 1 to 300, or pass -MaxOutputTokens for the explicit diagnostic profile. No provider call was attempted."
    }
    Write-SafeSummary -Status "blocked" -Category "budget_not_configured" -Guidance $tokenGuidance
    exit 0
}
if ($script:TimeoutState -ne "valid") { Write-SafeSummary -Status "blocked" -Category "unexpected_safe_internal_block" -Guidance "Configure a positive AI timeout. No provider call was attempted."; exit 0 }
if ($env:AI_PROVIDER_CALLS_ENABLED -eq "false" -or $env:AI_PROVIDER_GLOBAL_DISABLE -eq "true") {
    Write-SafeSummary -Status "blocked" -Category "provider_calls_disabled" -Guidance "Provider calls are disabled by local safety settings. No provider call was attempted."
    exit 0
}
if ($PreflightOnly -or -not $ApproveLiveCall) {
    Write-SafeSummary -Status "blocked" -Category "operator_approval_required" -Guidance "Preflight passed. Pass -ApproveLiveCall after reviewing the redacted summary to permit one bounded importer call. No provider call was attempted."
    exit 0
}

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$SmokeText = "scrambled eggs: 2 eggs, 1 tbsp butter, pinch salt. Whisk eggs, cook in butter over medium-low heat, stir until softly set. Serves 1."
if (-not [string]::IsNullOrWhiteSpace($HelperPath)) {
    $Python = $HelperPath
} elseif (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
if ([System.IO.Path]::GetExtension($Python) -eq ".ps1") {
    $captured = (& powershell -NoProfile -ExecutionPolicy Bypass -File $Python --text $SmokeText --max-output-tokens $tokens --ai-timeout-seconds $timeout 2>&1 | ForEach-Object { $_.ToString() } | Out-String)
} else {
    $captured = (& $Python "scripts\smoke-openai-importer-live.py" --text $SmokeText --max-output-tokens $tokens --ai-timeout-seconds $timeout 2>&1 | ForEach-Object { $_.ToString() } | Out-String)
}
$exitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($exitCode -eq 0) {
    Write-SafeSummary -Status "passed" -Category "none" -Guidance "One bounded importer call completed. No retry was attempted."
    exit 0
}

$category = "unexpected_safe_internal_block"
$providerErrorType = ""
if ($captured -match "provider_error_category=([^\s]+)") {
    $rawCategory = $Matches[1]
    $category = switch ($rawCategory) {
        "output_cap_or_incomplete_response" { "output_cap_or_incomplete_response"; break }
        "timeout" { "provider_timeout"; break }
        "quota_or_rate_limit" { "provider_account_or_quota_unavailable"; break }
        "auth" { "provider_account_or_quota_unavailable"; break }
        "bad_model" { "model_not_allowed"; break }
        "network" { "provider_http_error_redacted"; break }
        default { "unexpected_safe_internal_block" }
    }
}
$typeMatch = [regex]::Match($captured, "provider_error_type=([^\s]+)")
if ($typeMatch.Success -and $typeMatch.Groups[1].Value -match "^[A-Za-z][A-Za-z0-9_.-]{0,80}$") {
    $providerErrorType = $typeMatch.Groups[1].Value
}
$guidance = switch ($category) {
    "output_cap_or_incomplete_response" { "The bounded importer call reached the live provider path but the response could not be parsed as complete schema JSON within the configured output cap. No retry was attempted."; break }
    "provider_timeout" { "Live OpenAI was enabled but the bounded importer call timed out. No retry was attempted."; break }
    "provider_account_or_quota_unavailable" { "The bounded live importer call was unavailable due to provider account, quota, or rate limits. No retry was attempted."; break }
    "model_not_allowed" { "The bounded importer call used a model that the provider did not allow. Only gpt-5.4-nano is supported."; break }
    "provider_http_error_redacted" { "The bounded importer call could not reach the provider. No retry was attempted."; break }
    default { "The bounded importer call did not complete successfully. No retry was attempted." }
}
Write-SafeSummary -Status "failed" -Category $category -ProviderErrorType $providerErrorType -Guidance $guidance
exit 1
