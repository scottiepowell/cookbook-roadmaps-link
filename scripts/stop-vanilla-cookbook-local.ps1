Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
$ComposeFile = Join-Path $RepoRoot "docker-compose.local.yml"
$ComposeProject = "cookbook-local"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    [Console]::Error.WriteLine("Docker is required to stop the local Vanilla Cookbook runtime.")
    exit 2
}

$Docker = (Get-Command docker).Source
& $Docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("Docker Desktop daemon is unavailable. Start Docker Desktop and retry; verify with: docker info")
    exit 3
}

Write-Host "Stopping local Vanilla Cookbook container only."
& $Docker compose -p $ComposeProject -f $ComposeFile down
exit $LASTEXITCODE
