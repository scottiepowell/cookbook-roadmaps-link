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

Write-Host "Stopping local Vanilla Cookbook container only."
& (Get-Command docker).Source compose -p $ComposeProject -f $ComposeFile down
exit $LASTEXITCODE
