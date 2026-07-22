Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js and npm are required. Run npm install, then npx playwright install chromium."
    exit 2
}

try {
    $Readiness = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/product" -TimeoutSec 5
} catch {
    Write-Error "Cookbook AI sidecar is not running at http://127.0.0.1:8000/product. Start scripts\start-ai-demo-local.ps1 in another terminal, then retry."
    exit 2
}

if ($Readiness.StatusCode -ne 200) {
    Write-Error "Cookbook AI product route returned HTTP $($Readiness.StatusCode). Start the local sidecar, then retry."
    exit 2
}

try {
    $ModeReadiness = Invoke-RestMethod -Uri "http://127.0.0.1:8000/demo/readiness" -TimeoutSec 5
} catch {
    Write-Error "Cookbook AI readiness metadata is unavailable. Start the local sidecar in mock mode, then retry."
    exit 2
}

if ($ModeReadiness.provider.mode -ne "mock" -or $ModeReadiness.provider.model -ne "mock-basic") {
    Write-Error "This local UI harness is mock-only. Start the sidecar with: scripts\start-ai-demo-local.ps1 -Provider mock. It will not run against a live-configured server."
    exit 2
}

if (-not (Test-Path "node_modules\@playwright\test")) {
    Write-Error "Playwright dependencies are missing. Run npm install and npx playwright install chromium."
    exit 2
}

Write-Host "Running local Chromium UI troubleshooting against http://127.0.0.1:8000 (verified mock/mock-basic server)."
npx playwright test
exit $LASTEXITCODE
