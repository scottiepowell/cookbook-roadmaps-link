param(
    [switch]$RequireHttp
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
$ComposeFile = Join-Path $RepoRoot "docker-compose.local.yml"
$ComposeProject = "cookbook-local"
$CookbookUrl = "http://127.0.0.1:3000/"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    [Console]::Error.WriteLine("Docker is unavailable; local Vanilla Cookbook cannot be checked.")
    exit 2
}

$Docker = (Get-Command docker).Source
& $Docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("Docker Desktop daemon is unavailable. Start Docker Desktop and retry; verify with: docker info")
    exit 3
}

$ContainerId = (& $Docker compose -p $ComposeProject -f $ComposeFile ps -q app).Trim()
if ([string]::IsNullOrWhiteSpace($ContainerId)) {
    [Console]::Error.WriteLine("Local Vanilla Cookbook container is not created. Start it first.")
    exit 3
}

$Running = (& $Docker inspect -f "{{.State.Running}}" $ContainerId).Trim()
if ($Running -ne "true") {
    [Console]::Error.WriteLine("Local Vanilla Cookbook container is not running.")
    exit 3
}

$PortOpen = Test-NetConnection -ComputerName "127.0.0.1" -Port 3000 -InformationLevel Quiet
if (-not $PortOpen) {
    [Console]::Error.WriteLine("Container is running, but 127.0.0.1:3000 is not accepting connections yet.")
    exit 4
}

try {
    $Response = Invoke-WebRequest -UseBasicParsing -Uri $CookbookUrl -TimeoutSec 5
    Write-Host ("PASS: Vanilla Cookbook responded at {0} with HTTP {1}." -f $CookbookUrl, [int]$Response.StatusCode)
} catch {
    Write-Host "WARN: container is running and port 3000 is open, but the HTTP page did not respond yet."
    if ($RequireHttp) {
        exit 5
    }
}

Write-Host "PASS: local Vanilla Cookbook runtime is running on localhost only."
Write-Host "AI product shell: http://127.0.0.1:8000/product"
Write-Host "AI workspace: http://127.0.0.1:8000/demo"
