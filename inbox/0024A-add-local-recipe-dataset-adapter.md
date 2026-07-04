# Task 0024A: Add Local Recipe Dataset Adapter And Schema Inspection

## Goal

Start the indexing layer phase by adding a local-only source adapter for the Kaggle 13K recipe dataset under `recipe-dataset/`.

This task must inspect and normalize dataset metadata/schema only. It must not build the full index yet, must not ingest the dataset into the app database, and must not commit raw dataset files.

The local dataset path may look like:

```text
recipe-dataset/
  13k-recipes.csv
  13k-recipes.db
  5k-recipes.db
  metadata.json
  README.md
  tutorial.md
```

The repository should contain code and docs that know how to inspect this local dataset path when present. The raw dataset remains local/private and ignored by Git.

## Dataset Source And License

Dataset source:

```text
Food Ingredients and Recipes Dataset with Images
Kaggle dataset by pes12017000148
https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
```

License noted by the developer:

```text
Creative Commons Attribution-ShareAlike 3.0 Unported
CC BY-SA 3.0
Canonical URL: https://creativecommons.org/licenses/by-sa/3.0/
```

Document attribution clearly. Do not include the raw dataset itself in the repository.

## Build On

Completed work:

- `0017`: read-only recipe reader
- `0018`: deterministic recipe search
- `0019`: provider harness with mock default and OpenAI nano optional path
- `0021`: structured recipe importer
- `0022`: RAG ask endpoint
- `0023A`: meal planner foundation
- `0023B`: meal plan endpoint

## Scope

Implement local dataset adapter and schema inspection only:

1. Add a config value for local dataset directory, defaulting to `recipe-dataset` or `RECIPE_DATASET_DIR`.
2. Add adapter code that detects the expected local files when present.
3. Add CSV schema inspection for `13k-recipes.csv` when present.
4. Add SQLite schema inspection for `13k-recipes.db` and/or `5k-recipes.db` when present.
5. Add metadata loading for `metadata.json` when present.
6. Add a small normalized dataset-record preview model, but do not build a full index.
7. Add CLI or script support for schema inspection if useful.
8. Add tests using generated temporary CSV/SQLite fixtures, not the real dataset.
9. Add docs for local setup, attribution, license, and non-commit rules.
10. Keep all tests offline and deterministic.

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/dataset_adapter.py
ai-api/app/config.py
ai-api/app/schemas.py
ai-api/tests/test_dataset_adapter.py
scripts/inspect-recipe-dataset.py
docs/dataset-attribution.md
docs/local-recipe-dataset.md
docs/indexing-roadmap.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/repo-map.md
ai-api/README.md
outbox/0024A-add-local-recipe-dataset-adapter-results.md
```

Keep changes narrow. If schema growth makes `ai-api/app/schemas.py` too large, add a note to the outbox recommending a future schema split instead of doing a broad refactor.

## .gitignore / Safety

The repo should ignore the raw local dataset directory:

```gitignore
recipe-dataset/
```

If it already exists, leave it intact.

Do not commit:

```text
recipe-dataset/13k-recipes.csv
recipe-dataset/13k-recipes.db
recipe-dataset/5k-recipes.db
recipe-dataset/metadata.json
recipe-dataset/README.md
recipe-dataset/tutorial.md
```

Do not commit generated indexes in this task.

## Adapter Behavior

Add a local adapter with behavior similar to:

```python
inspect_recipe_dataset(dataset_dir: Path) -> RecipeDatasetInspection
```

The inspection result should include:

- dataset directory path, represented safely;
- whether the directory exists;
- discovered expected files;
- missing expected files;
- CSV column names and sample row count if inspectable;
- SQLite table names and columns if inspectable;
- metadata keys if `metadata.json` is present;
- warnings for missing/unreadable files;
- no raw recipe content beyond tiny safe previews needed for tests/docs.

Add a small normalized preview record model if useful, for example:

```text
ExternalRecipePreview
```

It may include:

- source ID
- title/name field if available
- ingredients field summary if available
- instructions field summary if available
- source file
- warning list

Do not map all 13K rows in this task unless needed for a tiny preview/sample. This is schema inspection, not indexing.

## CLI / Script

If adding a script, keep it simple and local-only:

```powershell
python scripts/inspect-recipe-dataset.py --dataset-dir recipe-dataset
```

It should print a compact schema/metadata summary and must not print huge recipe contents.

The script must work with generated fixture data in tests or at least have importable logic covered by tests.

## License / Attribution Docs

Create or update docs to include:

- dataset title;
- Kaggle source URL;
- creator/owner as provided by Kaggle page/developer note;
- license name: CC BY-SA 3.0;
- canonical license URL;
- statement that raw dataset files are not committed;
- statement that derived/indexed artifacts may require ShareAlike handling if distributed;
- no warranty / upstream rights caveat;
- note that this project currently commits only loader/indexing code and docs.

## Non-Goals

Do not implement:

- full indexing
- embeddings
- vector database
- hybrid search endpoint
- RAG over the 13K dataset
- bulk import into Vanilla Cookbook
- recipe write-back
- image ingestion
- image download or storage
- OCR
- OpenAI calls
- provider calls
- meal planner changes
- UI changes
- Cloudflare/deployment changes
- committing raw dataset files
- committing generated indexes

## Tests

Add deterministic offline tests using temporary fixture files.

Tests should cover:

1. Missing dataset directory returns controlled warnings.
2. Expected files are discovered when present.
3. CSV columns are inspected from a tiny generated CSV fixture.
4. SQLite tables/columns are inspected from a tiny generated SQLite fixture.
5. Metadata JSON keys are loaded from a tiny generated metadata fixture.
6. Adapter does not require the real `recipe-dataset/` folder.
7. Adapter does not call providers or OpenAI.
8. Existing health, config, provider, reader, search, importer, RAG, and meal-plan tests still pass.

Tests must not require:

- the real Kaggle dataset
- network access
- OpenAI API key
- live provider calls
- Docker

## Validation

Run from Windows PowerShell in the repo:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
python -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If any command is unavailable, document it in the outbox report.

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no files under `recipe-dataset/` are staged.

## Outbox Report

Create:

```text
outbox/0024A-add-local-recipe-dataset-adapter-results.md
```

Include:

- Summary
- Files changed
- Dataset/license handling
- Adapter behavior
- Schema inspection behavior
- Validation results
- Confirmation that no provider/OpenAI calls were run
- Confirmation that no `.env`, secrets, raw dataset files, or generated indexes were committed
- Recommended next task: `0024B` build local deterministic index over the inspected dataset

## Commit

Commit and push:

```bash
git add .gitignore ai-api scripts docs README.md outbox/0024A-add-local-recipe-dataset-adapter-results.md
git commit -m "mailbox: complete task 0024A add local recipe dataset adapter"
git push origin main
```

## Done Criteria

- Local dataset adapter exists.
- Dataset directory is configurable.
- Missing dataset path is handled safely.
- CSV schema inspection works with fixture data.
- SQLite schema inspection works with fixture data.
- Metadata JSON inspection works with fixture data.
- Attribution/license docs exist.
- Raw `recipe-dataset/` files remain ignored and uncommitted.
- No index is built yet.
- No provider/OpenAI calls are made.
- Tests are deterministic and offline.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
