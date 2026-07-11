Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

. (Join-Path $PSScriptRoot "lib\ai-env-file.ps1")

$PythonEnv = @(
    "AI_PROVIDER",
    "OPENAI_ENABLE_LIVE_TESTS",
    "OPENAI_LIVE_TEST_BUDGET_CENTS",
    "AI_MAX_OUTPUT_TOKENS",
    "AI_PROVIDER_CALLS_ENABLED",
    "AI_PROVIDER_GLOBAL_DISABLE",
    "AI_PROVIDER_BUDGET_MODE",
    "OPENAI_API_KEY",
    "EXAMPLE_SECRET_TOKEN",
    "VISIBLE_VALUE",
    "LOAD_ME",
    "KEEP_ME"
)

$SavedEnv = @{}
foreach ($Name in $PythonEnv) {
    $SavedEnv[$Name] = [Environment]::GetEnvironmentVariable($Name, [EnvironmentVariableTarget]::Process)
}

$TempRoot = Join-Path $env:TEMP ("ai-env-loader-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

$PassCount = 0
$FailCount = 0

function Test-Case {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    try {
        & $Action
        Write-Host "PASS: $Name"
        $script:PassCount += 1
    }
    catch {
        Write-Host "FAIL: $Name"
        Write-Host $_
        $script:FailCount += 1
    }
}

try {
    $FixturePath = Join-Path $TempRoot "fixture.env"
    Set-Content -LiteralPath $FixturePath -Value @(
        "# comment that should stay",
        "AI_PROVIDER=mock",
        "VISIBLE_VALUE=from-file",
        "OPENAI_ENABLE_LIVE_TESTS=false",
        "LOAD_ME='loaded from file'"
    )

    Test-Case -Name "loads missing values without overwriting existing process env" -Action {
        $env:AI_PROVIDER = "process-value"
        $env:KEEP_ME = "keep-process-value"
        $env:VISIBLE_VALUE = ""
        $env:OPENAI_ENABLE_LIVE_TESTS = ""
        $Imported = Import-AiEnvFile -Path $FixturePath -OnlyIfMissing
        if ($env:AI_PROVIDER -ne "process-value") {
            throw "AI_PROVIDER was overwritten."
        }
        if ($env:VISIBLE_VALUE -ne "from-file") {
            throw "VISIBLE_VALUE was not imported."
        }
        if ($env:OPENAI_ENABLE_LIVE_TESTS -ne "false") {
            throw "OPENAI_ENABLE_LIVE_TESTS was not imported."
        }
        if ($env:LOAD_ME -ne "loaded from file") {
            throw "Quoted values were not parsed."
        }
        if (-not ($Imported -contains "VISIBLE_VALUE")) {
            throw "Import list did not include VISIBLE_VALUE."
        }
    }

    Test-Case -Name "writes missing defaults only" -Action {
        $Defaults = [ordered]@{
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
            OPENAI_API_KEY = "should-not-be-written"
        }

        $Appended = Write-AiEnvDefaults -Path $FixturePath -Defaults $Defaults -OnlyMissing
        $Content = Get-Content -LiteralPath $FixturePath -Raw
        if ($Content -notmatch "# comment that should stay") {
            throw "Comment was not preserved."
        }
        if ($Content -notmatch "AI_PROVIDER=mock") {
            throw "Existing AI_PROVIDER value was lost."
        }
        if ($Content -match "AI_PROVIDER=openai") {
            throw "Existing AI_PROVIDER value was overwritten."
        }
        if ($Content -notmatch "AI_MAX_OUTPUT_TOKENS=300") {
            throw "Missing defaults were not appended."
        }
        if ($Content -match "OPENAI_API_KEY") {
            throw "OPENAI_API_KEY was written unexpectedly."
        }
        if (-not ($Appended -contains "AI_MAX_OUTPUT_TOKENS")) {
            throw "Appended list did not include AI_MAX_OUTPUT_TOKENS."
        }
    }

    Test-Case -Name "safe summary redacts secrets and tokens" -Action {
        $env:OPENAI_API_KEY = "top-secret-value"
        $env:EXAMPLE_SECRET_TOKEN = "another-secret-value"
        $env:KEEP_ME = "visible-value"
        $Summary = (Get-AiSafeEnvSummary -Keys @("OPENAI_API_KEY", "EXAMPLE_SECRET_TOKEN", "KEEP_ME", "OPENAI_ENABLE_LIVE_TESTS")) -join "`n"
        if ($Summary -notmatch "OPENAI_API_KEY=redacted-present") {
            throw "OPENAI_API_KEY was not redacted."
        }
        if ($Summary -notmatch "EXAMPLE_SECRET_TOKEN=redacted-present") {
            throw "Token-like values were not redacted."
        }
        if ($Summary -notmatch "KEEP_ME=visible-value") {
            throw "Non-secret values were not shown."
        }
        if ($Summary -match "top-secret-value|another-secret-value") {
            throw "Secret values leaked in summary."
        }
    }

    Test-Case -Name "missing env file fails clearly" -Action {
        $MissingPath = Join-Path $TempRoot "missing.env"
        try {
            Import-AiEnvFile -Path $MissingPath -OnlyIfMissing | Out-Null
            throw "Missing env file did not fail."
        }
        catch {
            if ($_.Exception.Message -notmatch "Env file not found") {
                throw
            }
        }
    }

    Test-Case -Name "live smoke skips when OPENAI_ENABLE_LIVE_TESTS is false" -Action {
        $SmokeEnv = Join-Path $TempRoot "smoke.env"
        Set-Content -LiteralPath $SmokeEnv -Value @(
            "AI_PROVIDER=openai",
            "OPENAI_ENABLE_LIVE_TESTS=false"
        )

        $Output = & powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile $SmokeEnv 2>&1
        $Text = $Output -join "`n"
        if ($LASTEXITCODE -ne 0) {
            throw "Smoke wrapper returned exit code $LASTEXITCODE."
        }
        if ($Text -notmatch "Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in\.") {
            throw "Smoke wrapper did not skip cleanly."
        }
        if ($Text -match "top-secret-value|another-secret-value|should-not-be-written") {
            throw "Smoke wrapper leaked secret-like values."
        }
    }

    if ($FailCount -ne 0) {
        throw "$FailCount test case(s) failed."
    }

    Write-Host ("SUMMARY: {0} passed, {1} failed" -f $PassCount, $FailCount)
    exit 0
}
finally {
    foreach ($Name in $PythonEnv) {
        if ($null -eq $SavedEnv[$Name]) {
            Remove-Item Env:$Name -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($Name, $SavedEnv[$Name], [EnvironmentVariableTarget]::Process)
        }
    }

    Remove-Item -Recurse -Force $TempRoot -ErrorAction SilentlyContinue
}
