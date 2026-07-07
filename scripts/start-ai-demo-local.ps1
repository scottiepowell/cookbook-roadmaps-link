param(
    [int]$Port = 8000,
    [string]$DemoDataDir = ".tmp-ai-demo\local"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$env:PYTHONPATH = "ai-api"
& $Python -m app.demo_data --output-dir $DemoDataDir
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$ResolvedDataDir = Resolve-Path $DemoDataDir
$env:AI_PROVIDER = "mock"
$env:COOKBOOK_DB_PATH = Join-Path $ResolvedDataDir "recipes.sqlite"
$env:RECIPE_DATASET_DIR = Join-Path $ResolvedDataDir "dataset"
$env:RECIPE_DATASET_INDEX_LIMIT = "25"

Write-Host ""
Write-Host "AI demo data is ready."
Write-Host "Open: http://127.0.0.1:$Port/demo"
Write-Host "Logs will print in this terminal. Stop with Ctrl+C."
Write-Host ""

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port $Port
