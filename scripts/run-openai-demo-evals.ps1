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

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python "scripts\live-openai-demo-evals.py"
exit $LASTEXITCODE
