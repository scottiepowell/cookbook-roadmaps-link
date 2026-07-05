# Task 0024B: Build Local Deterministic Recipe Index

## Goal

Build the first local deterministic indexing layer over the Kaggle recipe dataset adapter from `0024A`.

This task should create a local, reproducible index from the dataset records, but it must not add embeddings, a vector database, OpenAI calls, or RAG over the dataset yet.

The purpose is to turn the local 13K recipe dataset into a compact searchable/indexable artifact that later tasks can query efficiently.

## Hard Prerequisite

This task depends on `0024A` being complete.

Before implementing, confirm the repo has:

- local dataset adapter code from `0024A`;
- dataset schema inspection tests from `0024A`;
- attribution/license docs from `0024A`;
- `.gitignore` rule for `recipe-dataset/`;
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md`.

If `0024A` is missing or incomplete, stop and write a short report explaining what is missing. Do not invent a separate adapter design in this task.

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

Keep attribution docs intact. Do not commit the raw dataset or generated index artifacts unless explicitly approved in a later task.

## Local Dataset Path

The developer may have this local ignored folder:

```text
recipe-dataset/
  13k-recipes.csv
  13k-recipes.db
  5k-recipes.db
  metadata.json
  README.md
  tutorial.md
```

This folder is ignored and must remain uncommitted.

## Scope

Implement deterministic local indexing code only:

1. Use the `0024A` dataset adapter to read a bounded/sampleable stream of recipe records from CSV or SQLite.
2. Normalize records into an indexable recipe document shape.
3. Build a deterministic keyword/field index in memory or as an optional local generated artifact.
4. Add an index summary model that reports counts, source files, fields indexed, warnings, and build time metadata.
5. Add a local script to build/inspect the index from `recipe-dataset/`.
6. Add tests using tiny generated fixture CSV/SQLite data.
7. Keep all validation offline and deterministic.

Do not add an API endpoint yet. The indexed retrieval endpoint is for `0024C`.

## Index Design Requirements

The first index should be simple and explainable.

Suggested indexed fields:

- recipe ID/source ID
- title/name
- ingredients
- instructions/directions
- tags/category/cuisine if present
- source file/table

The index should support deterministic lookup primitives for later tasks, such as:

```python
build_recipe_index(records: Iterable[ExternalRecipeRecord]) -> RecipeIndex
search_recipe_index(index: RecipeIndex, query: str, limit: int = 10) -> list[RecipeIndexResult]
```

The exact function names may differ if they fit the existing codebase better.

Search behavior should:

- lowercase and tokenize consistently;
- rank title/name matches above ingredients;
- rank ingredients above instructions/body text;
- produce stable ordering for ties;
- return snippets or matched fields;
- avoid loading unbounded huge prompt text;
- avoid provider/LLM calls.

## Generated Artifacts

Generated indexes should stay local and ignored.

If an index artifact path is added, use a local ignored location such as:

```text
.local-index/
```

or:

```text
recipe-index/
```

If adding one, update `.gitignore` accordingly.

Do not commit generated index files.

For this task, it is acceptable to keep the index in memory and only add a script that prints summary/search results. The important part is deterministic indexing logic and tests.

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/dataset_index.py
ai-api/app/dataset_adapter.py
ai-api/app/config.py
ai-api/app/schemas.py
ai-api/tests/test_dataset_index.py
scripts/build-recipe-index.py
docs/local-recipe-index.md
docs/indexing-roadmap.md
docs/dataset-attribution.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/repo-map.md
ai-api/README.md
outbox/0024B-build-local-deterministic-recipe-index-results.md
```

Keep changes narrow. Do not do a broad schema/package refactor in this task unless absolutely necessary.

## Script Behavior

Add a script if useful:

```powershell
python scripts/build-recipe-index.py --dataset-dir recipe-dataset --limit 1000 --query "chicken pasta"
```

Expected behavior:

- uses local dataset directory;
- inspects/loads records through the `0024A` adapter;
- builds deterministic index over a bounded number of records by default if needed;
- prints compact summary;
- optionally prints top search results for a query;
- does not print huge recipe contents;
- does not call OpenAI/provider;
- does not write generated index artifacts unless explicitly requested by an option.

If a write option is added, it must default to off and write only to an ignored local path.

## .gitignore / Safety

Ensure these remain ignored:

```gitignore
recipe-dataset/
```

If generated local index artifacts are introduced, also ignore them, for example:

```gitignore
.local-index/
recipe-index/
```

Before committing, run:

```powershell
git status --short
```

Confirm no files under `recipe-dataset/` and no generated index artifacts are staged.

## Non-Goals

Do not implement:

- API endpoint for indexed search
- RAG over the 13K dataset
- embeddings
- vector database
- OpenAI calls
- provider calls
- meal planner changes
- shopping-list generation
- nutrition analysis
- recipe write-back
- importing records into Vanilla Cookbook
- image ingestion
- image download/storage
- OCR
- UI changes
- Cloudflare/deployment changes
- committing raw dataset files
- committing generated indexes

## Tests

Add deterministic offline tests using tiny generated fixture data.

Tests should cover:

1. Index builds from fixture records produced by the adapter.
2. Title/name matches rank above ingredient matches.
3. Ingredient matches rank above instruction/body matches.
4. Search returns stable ordering for ties.
5. Search returns snippets or matched field metadata.
6. Empty/no-match queries return controlled empty results.
7. Index does not require real `recipe-dataset/`.
8. Index does not call providers/OpenAI.
9. No generated index artifact is committed or required.
10. Existing health, config, provider, reader, search, importer, RAG, meal-plan, and dataset-adapter tests still pass.

Tests must not require:

- the real Kaggle dataset
- network access
- OpenAI API key
- live provider calls
- Docker

## Documentation

Update docs to explain:

- 0024A added local source adapter/schema inspection.
- 0024B adds deterministic local indexing logic.
- Raw Kaggle data remains local and ignored.
- Generated indexes remain local and ignored.
- Attribution/license docs remain in place.
- The index uses field-weighted keyword retrieval first.
- Embeddings/vector search are deferred.
- Indexed retrieval API is deferred to `0024C`.
- RAG over indexed dataset is deferred to `0024D`.

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

Confirm no raw dataset files or generated index artifacts are staged.

## Outbox Report

Create:

```text
outbox/0024B-build-local-deterministic-recipe-index-results.md
```

Include:

- Summary
- Files changed
- Confirmation that `0024A` prerequisite was present
- Index design
- Fields indexed
- Search/ranking behavior
- Script behavior, if added
- Validation results
- Confirmation that no provider/OpenAI calls were run
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next task: `0024C` indexed retrieval endpoint over local deterministic index

## Commit

Commit and push:

```bash
git add .gitignore ai-api scripts docs README.md outbox/0024B-build-local-deterministic-recipe-index-results.md
git commit -m "mailbox: complete task 0024B build local deterministic recipe index"
git push origin main
```

## Done Criteria

- `0024A` prerequisite is present or a clear stop report is written.
- Deterministic recipe index builder exists.
- Index search function exists.
- Field-weighted ranking exists.
- Tests are deterministic and offline.
- Real Kaggle dataset is not required for tests.
- No API endpoint is added yet.
- No embeddings/vector DB are added.
- No provider/OpenAI calls are made.
- Raw `recipe-dataset/` files remain ignored and uncommitted.
- Generated indexes remain ignored and uncommitted.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
