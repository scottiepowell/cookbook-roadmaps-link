param(
    [string]$Python = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$tempRoot = Join-Path $repoRoot ".tmp-pytest"
$runTemp = Join-Path $tempRoot ([System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $runTemp | Out-Null

$env:TMP = $runTemp
$env:TEMP = $runTemp
$env:PYTHONPATH = Join-Path $repoRoot "ai-api"

try {
    & $Python -m pytest ai-api\tests --basetemp (Join-Path $runTemp "pytest")
    if ($LASTEXITCODE -ne 0) {
        throw "Direct Windows pytest failed with exit code $LASTEXITCODE."
    }
    & $Python evals\ai_cookbook\run_evals.py
    if ($LASTEXITCODE -ne 0) {
        throw "Offline evals failed with exit code $LASTEXITCODE."
    }
}
catch {
    Write-Warning "$_"
    Write-Warning "Falling back to Git Bash repository validator."
    & "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
    if ($LASTEXITCODE -ne 0) {
        throw "Git Bash repository validator failed with exit code $LASTEXITCODE."
    }
}
finally {
    Remove-Item -Recurse -Force $runTemp -ErrorAction SilentlyContinue
}
