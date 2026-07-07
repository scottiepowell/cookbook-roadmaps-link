Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$env:AI_PROVIDER = "mock"

Write-Host "AI demo mock path: offline evals"
& $Python "evals\ai_cookbook\run_evals.py"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "AI demo mock path: direct endpoint smoke"
$DemoPython = @'
import os
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, "ai-api")

from app.demo_data import seed_demo_data
from fastapi.testclient import TestClient

from app.main import app


tmp_parent = Path(".tmp-ai-demo")
tmp_parent.mkdir(exist_ok=True)
tmp = tmp_parent / f"run-{uuid.uuid4().hex}"
tmp.mkdir()

try:
    root = tmp
    paths = seed_demo_data(root)
    os.environ["COOKBOOK_DB_PATH"] = str(paths["db_path"])
    os.environ["RECIPE_DATASET_DIR"] = str(paths["dataset_dir"])
    os.environ["AI_PROVIDER"] = "mock"

    client = TestClient(app)
    checks = [
        ("health", client.get("/health")),
        ("config", client.get("/ai/config")),
        ("importer", client.post("/ai/import-recipe", json={"text": "Lemon beans: warm beans with lemon.", "source": "demo"})),
        ("ask_my_cookbook", client.post("/ai/ask", json={"question": "What uses lemon?", "limit": 1})),
        ("dataset_search", client.get("/dataset/search", params={"q": "tomato pasta", "limit": 1, "dataset_limit": 3})),
        ("dataset_ask", client.post("/dataset/ask", json={"question": "What indexed recipe uses tomato pasta?", "limit": 1, "dataset_limit": 3})),
        ("meal_plan", client.post("/ai/meal-plan", json={"days": 1, "meals_per_day": 1, "preferences": "lemon", "candidate_limit": 2})),
    ]

    for name, response in checks:
        if response.status_code != 200:
            raise SystemExit(f"{name} failed with HTTP {response.status_code}: {response.text}")
        text = response.text
        for forbidden in ("OPENAI_API_KEY", "sk-", "Authorization:"):
            if forbidden in text:
                raise SystemExit(f"{name} leaked forbidden text: {forbidden}")
        print(f"PASS: {name}")
finally:
    shutil.rmtree(root, ignore_errors=True)
    try:
        tmp_parent.rmdir()
    except OSError:
        pass

print("Mock endpoint demo checks passed.")
'@

$DemoPython | & $Python -
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Mock AI demo checks passed."
