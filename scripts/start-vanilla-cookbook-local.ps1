param(
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot
$ComposeFile = Join-Path $RepoRoot "docker-compose.local.yml"
$ComposeProject = "cookbook-local"
$LocalRuntimeRoot = Join-Path $RepoRoot ".local\vanilla-cookbook"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    [Console]::Error.WriteLine("Docker is required for the local Vanilla Cookbook runtime.")
    exit 2
}

if (-not (Test-Path -LiteralPath $ComposeFile -PathType Leaf)) {
    [Console]::Error.WriteLine("Local Compose file is missing: docker-compose.local.yml")
    exit 2
}

New-Item -ItemType Directory -Force -Path (Join-Path $LocalRuntimeRoot "db") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LocalRuntimeRoot "uploads") | Out-Null

if ($Check) {
    & (Get-Command docker).Source compose -p $ComposeProject -f $ComposeFile ps
    exit $LASTEXITCODE
}

Write-Host "Starting local Vanilla Cookbook only."
Write-Host "Compose project: $ComposeProject"
Write-Host "Cookbook URL: http://127.0.0.1:3000/"
Write-Host "Local runtime data: .local\vanilla-cookbook\ (ignored)"
Write-Host "Cloudflare Tunnel, AWS, GitHub Actions, and production .env are not required."
& (Get-Command docker).Source compose -p $ComposeProject -f $ComposeFile up -d app
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Local Vanilla Cookbook container started. Check it with:"
Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1"
