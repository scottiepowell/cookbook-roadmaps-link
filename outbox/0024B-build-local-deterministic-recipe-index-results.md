# 0024B Build Local Deterministic Recipe Index Results

## Summary

Built the first local deterministic indexing layer over the 0024A Kaggle recipe dataset adapter. The work adds bounded CSV/SQLite record reading, normalization into indexable recipe documents, an in-memory keyword/field index, deterministic search/ranking, offline fixture tests, and local documentation.

No API endpoint, RAG over the 13K dataset, embeddings, vector database, provider calls, image ingestion, Vanilla Cookbook import/write-back, deployment changes, generated index artifacts, `.env`, or raw dataset files were added.

## 0024A Prerequisite Check

Confirmed before implementation:

- `ai-api/app/dataset_adapter.py` exists.
- `ai-api/tests/test_dataset_adapter.py` exists.
- `docs/local-recipe-dataset-adapter.md` exists with attribution/license notes.
- `.gitignore` ignores `recipe-dataset/`.
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md` exists.

## Files Created Or Modified

- Modified `ai-api/app/dataset_adapter.py`
- Created `ai-api/app/dataset_index.py`
- Created `ai-api/tests/test_dataset_index.py`
- Created `scripts/inspect-recipe-index.py`
- Created `inbox/0024B-build-local-deterministic-recipe-index.md`
- Created `outbox/0024B-build-local-deterministic-recipe-index-results.md`
- Modified `ai-api/README.md`
- Modified `docs/local-recipe-dataset-adapter.md`
- Modified `docs/ai-sidecar-architecture.md`
- Modified `docs/ai-implementation-backlog.md`
- Modified `docs/repo-map.md`

## Index Behavior

- `iter_recipe_dataset_records()` reads at most a caller-provided limit from local CSV and SQLite files.
- CSV support handles the Kaggle-style blank first ID column plus common `id`, `recipe_id`, and `source_id` aliases.
- SQLite support uses schema inspection to find a recipe-like table and reads through the existing read-only SQLite helper.
- Records normalize source ID, title/name, ingredients, instructions/directions, tags/category/cuisine, source file, and source table.
- `build_recipe_index()` creates an in-memory deterministic index and summary with document counts, source counts, indexed fields, token count, warnings, and deterministic build metadata.
- `search_recipe_index()` lowercases/tokenizes consistently, ranks title/name above tags, tags above ingredients, ingredients above instructions, and instructions above source metadata.
- Results include ID, source ID, title, score, matched fields, snippet, source file, and optional source table.
- Stable input ordering breaks score ties.

## Local Script

Added `scripts/inspect-recipe-index.py` for local inspection:

```powershell
python scripts/inspect-recipe-index.py --dataset-dir recipe-dataset --limit 25 --query beans
```

The script prints compact in-memory summaries/results and does not write generated index artifacts.

## Fixture Schema Used For Tests

Tests use generated temporary fixtures only:

- CSV fixture with Kaggle-like columns: blank ID column, `Title`, `Ingredients`, `Instructions`, `Image_Name`, `Cleaned_Ingredients`
- CSV fixture with generic columns: `recipe_id`, `title`, `ingredients`, `instructions`, `cuisine`
- SQLite fixture: `recipes(id INTEGER PRIMARY KEY, name TEXT NOT NULL, ingredients TEXT, directions TEXT, category TEXT)`

Tests cover bounded record reading, read-only SQLite behavior, summary models, deterministic ranking, empty/no-match behavior, and no generated index artifacts.

## Dataset And License Handling

Attribution docs remain intact:

- Food Ingredients and Recipes Dataset with Images
- Kaggle dataset by `pes12017000148`
- https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
- License: CC BY-SA 3.0
- https://creativecommons.org/licenses/by-sa/3.0/

`recipe-dataset/` remains ignored. Raw dataset files and generated index artifacts were not staged or committed.

## Validation

- `python -m pytest ai-api\tests`: failed because the system Python does not have `pytest` installed (`No module named pytest`).
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed.
  - 58 AI API tests passed, including 5 new dataset index tests.
  - Shell syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `git status --short`: run before commit.

## Staging Safety

Before commit, confirm:

- no files under `recipe-dataset/` are staged;
- no generated index artifacts are staged;
- no `.env` or secrets are staged.

## Assumptions And Unknowns

- The first index is intentionally in-memory and bounded for local inspection/testing.
- The exact SQLite schema in the Kaggle DBs can vary; table detection is conservative and fixture tested.
- Distributed derived artifacts from the Kaggle data may require ShareAlike handling. This task commits only code, tests, and docs.
- No endpoint exposes the dataset index yet.

## Recommended Next Task

`0024C`: add an indexed retrieval endpoint over the local deterministic index after deciding how to handle dataset licensing, result provenance, and generated artifact storage.
