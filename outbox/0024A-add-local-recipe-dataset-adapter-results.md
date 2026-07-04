# 0024A Add Local Recipe Dataset Adapter Results

## Summary

Added a local-only Kaggle recipe dataset adapter for the AI sidecar. The adapter inspects expected files under `recipe-dataset/` or `RECIPE_DATASET_DIR`, returns structured inspection objects, and keeps indexing/importing/provider behavior out of scope.

## Files Created Or Modified

- Created `ai-api/app/dataset_adapter.py`
- Created `ai-api/tests/test_dataset_adapter.py`
- Created `docs/local-recipe-dataset-adapter.md`
- Created `inbox/0024A-add-local-recipe-dataset-adapter.md`
- Created `outbox/0024A-add-local-recipe-dataset-adapter-results.md`
- Modified `ai-api/app/config.py`
- Modified `ai-api/README.md`
- Modified `.env.example`
- Modified `README.md`
- Modified `docs/ai-sidecar-architecture.md`
- Modified `docs/ai-implementation-backlog.md`
- Modified `docs/repo-map.md`

## Adapter Implementation

- Added `RECIPE_DATASET_DIR`, defaulting to `recipe-dataset`.
- Detects the expected local files:
  - `13k-recipes.csv`
  - `13k-recipes.db`
  - `5k-recipes.db`
  - `metadata.json`
  - `README.md`
  - `tutorial.md`
- Returns structured file status objects with presence, readability, size, and warnings.
- Inspects `13k-recipes.csv` columns and up to three sample rows.
- Inspects SQLite schemas for `13k-recipes.db` and `5k-recipes.db` through the existing read-only schema inspector.
- Parses `metadata.json` into structured keys and values.
- Adds a small normalized preview for likely title, ingredients, and instructions fields when CSV rows are available.
- Emits controlled warnings for missing, unreadable, malformed CSV/JSON, or malformed SQLite files.

## Fixture Schema Used For Tests

Tests use generated temporary fixtures only:

- CSV fixture: `Title,Ingredients,Instructions,Image_Name`
- SQLite fixture: `recipes(id INTEGER PRIMARY KEY, title TEXT NOT NULL)`
- Metadata fixture: `{"title": "Food Ingredients and Recipes Dataset with Images", "license": "CC BY-SA 3.0"}`

No real `recipe-dataset/` files, provider keys, cookbook DB files, or network access are required.

## Dataset Attribution And License

Docs record the local dataset source:

- Food Ingredients and Recipes Dataset with Images
- Kaggle dataset by `pes12017000148`
- https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
- Creative Commons Attribution-ShareAlike 3.0 Unported, CC BY-SA 3.0
- https://creativecommons.org/licenses/by-sa/3.0/

`recipe-dataset/` remains ignored by Git. Raw dataset files, generated indexes, and images must not be committed.

## Validation

- `python -m pytest ai-api\tests`: failed in the system Python because `pytest` is not installed (`No module named pytest`).
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed.
  - 53 AI API tests passed, including 4 new dataset adapter tests.
  - Shell syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `git status --short`: confirmed no files under `recipe-dataset/` are staged.

## Assumptions And Unknowns

- The local Kaggle files are optional. Missing files produce warnings instead of failing inspection.
- The adapter intentionally reads only small previews and schemas; it does not count full CSV rows or load the dataset into memory.
- SQLite inspection is schema-only and read-only.
- The exact production indexing schema is still unknown.
- Image ingestion, embeddings, vector storage, hybrid search, and RAG over the Kaggle dataset remain future tasks.

## Recommended Next Task

Add the deterministic dataset indexing foundation after reviewing the inspected CSV and SQLite schemas locally. Keep it offline, generated-fixture tested, and separate from Vanilla Cookbook write-back.
