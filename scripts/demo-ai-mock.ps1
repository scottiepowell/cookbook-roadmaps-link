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
import csv
import json
import os
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path

sys.path.insert(0, "ai-api")

from fastapi.testclient import TestClient

from app.main import app


def write_recipe_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT,
            tags TEXT,
            source_url TEXT
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO recipes
          (id, title, description, ingredients, instructions, tags, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "Lemon Beans", "Bright pantry dinner", json.dumps(["beans", "lemon", "olive oil"]), "Warm beans\nAdd lemon\nServe", "dinner\nvegetarian", None),
            (2, "Pasta Bake", "Comfort dinner", json.dumps(["pasta", "tomato", "cheese"]), "Boil pasta\nBake with cheese", "dinner", None),
        ],
    )
    connection.commit()
    connection.close()


def write_dataset(path: Path) -> None:
    with (path / "13k-recipes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["recipe_id", "title", "ingredients", "instructions", "cuisine"])
        writer.writeheader()
        writer.writerow({"recipe_id": "demo-1", "title": "Lemon Beans", "ingredients": "beans; lemon", "instructions": "Warm beans", "cuisine": "dinner"})
        writer.writerow({"recipe_id": "demo-2", "title": "Plain Toast", "ingredients": "bread", "instructions": "Toast bread", "cuisine": "breakfast"})


tmp_parent = Path(".tmp-ai-demo")
tmp_parent.mkdir(exist_ok=True)
tmp = tmp_parent / f"run-{uuid.uuid4().hex}"
tmp.mkdir()

try:
    root = tmp
    db_path = root / "recipes.sqlite"
    dataset_dir = root / "dataset"
    dataset_dir.mkdir()
    write_recipe_db(db_path)
    write_dataset(dataset_dir)
    os.environ["COOKBOOK_DB_PATH"] = str(db_path)
    os.environ["RECIPE_DATASET_DIR"] = str(dataset_dir)
    os.environ["AI_PROVIDER"] = "mock"

    client = TestClient(app)
    checks = [
        ("health", client.get("/health")),
        ("config", client.get("/ai/config")),
        ("importer", client.post("/ai/import-recipe", json={"text": "Lemon beans: warm beans with lemon.", "source": "demo"})),
        ("ask_my_cookbook", client.post("/ai/ask", json={"question": "What uses lemon?", "limit": 1})),
        ("dataset_search", client.get("/dataset/search", params={"q": "lemon", "limit": 1, "dataset_limit": 2})),
        ("dataset_ask", client.post("/dataset/ask", json={"question": "What indexed recipe uses lemon?", "limit": 1, "dataset_limit": 2})),
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
