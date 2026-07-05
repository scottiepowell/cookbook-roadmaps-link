# Task 0024C: Add Indexed Dataset Retrieval Endpoint

## Goal

Expose the local deterministic Kaggle recipe dataset index from `0024B` through an `ai-api` retrieval endpoint.

This task should let the API search the ignored local `recipe-dataset/` corpus using the deterministic index, returning ranked recipe results with provenance/citation metadata.

This is retrieval only. Do not add RAG, OpenAI/provider calls, embeddings, vector database, or generated/persisted index artifacts in this task.

## Build On

Completed work:

- `0024A`: local Kaggle dataset adapter and schema inspection
- `0024B`: local deterministic in-memory recipe index and search helpers

Before implementing, confirm the repo has:

- `ai-api/app/dataset_adapter.py`
- `ai-api/app/dataset_index.py`
- `ai-api/tests/test_dataset_adapter.py`
- `ai-api/tests/test_dataset_index.py`
- `scripts/inspect-recipe-index.py`
- `docs/local-recipe-dataset-adapter.md`
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md`
- `outbox/0024B-build-local-deterministic-recipe-index-results.md`
- `.gitignore` rule for `recipe-dataset/`

If `0024A` or `0024B` are missing or incomplete, stop and write a short report explaining what is missing. Do not invent a separate adapter/index design.

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

Keep attribution docs intact. Do not commit the raw dataset or generated index artifacts.

## Endpoint

Add an indexed dataset search endpoint.

Preferred endpoint names:

```text
GET  /dataset/search?q=<query>&limit=<n>
POST /dataset/search
```

If there is a better naming convention in the existing API, use it consistently, but do not replace existing endpoints.

Suggested POST request:

```json
{
  "query": "chicken pasta",
  "limit": 10,
  "dataset_limit": 1000
}
```

Suggested response:

```json
{
  "query": "chicken pasta",
  "count": 3,
  "results": [
    {
      "id": "13k-recipes.csv:123",
      "source_id": "123",
      "title": "Chicken Pasta Bake",
      "score": 42,
      "matched_fields": ["title", "ingredients"],
      "snippet": "Chicken Pasta Bake ... pasta ... chicken ...",
      "source_file": "13k-recipes.csv",
      "source_table": null,
      "citation": {
        "dataset": "Food Ingredients and Recipes Dataset with Images",
        "source_file": "13k-recipes.csv",
        "source_id": "123",
        "license": "CC BY-SA 3.0"
      }
    }
  ],
  "index": {
    "document_count": 1000,
    "fields_indexed": ["title", "tags", "ingredients", "instructions", "source"],
    "source_counts": {"13k-recipes.csv": 1000}
  },
  "warnings": []
}
```

Exact field names may differ if they align better with existing schema models, but the response must include results, ranking metadata, matched fields/snippets, safe provenance/citations, index summary metadata, and warnings.

## Config

Use existing dataset configuration from `0024A`/`0024B`.

If useful, add safe config defaults for:

```text
RECIPE_DATASET_DIR=recipe-dataset
RECIPE_DATASET_SEARCH_LIMIT=10
RECIPE_DATASET_INDEX_LIMIT=1000
```

Do not expose full local filesystem paths in API responses unless they are intentionally sanitized. Prefer source file names like `13k-recipes.csv` and source table names.

## Behavior

The endpoint should:

1. Use the `0024B` deterministic index/search logic.
2. Build an in-memory index from a bounded number of local records.
3. Return deterministic ranked results.
4. Return safe citation/provenance metadata.
5. Return controlled warnings if the local dataset folder is missing or empty.
6. Return an empty result set for empty/no-match queries.
7. Never call OpenAI, provider harness, embeddings, or network services.
8. Never write to the Vanilla Cookbook database.
9. Never commit or persist generated index artifacts.
10. Never return raw huge recipe content.

It is acceptable for the first endpoint to rebuild the in-memory index per request using a bounded `dataset_limit`. If adding simple process-local caching is straightforward and well tested, it may be added, but do not make caching complex in this task.

## Error / Missing Dataset Behavior

If `recipe-dataset/` is missing or has no inspectable records:

- return a controlled 200 response with `count: 0` and warnings, or a controlled 422/503 error if that fits existing API style better;
- do not crash with a traceback;
- do not require the real dataset for tests.

Prefer a user-friendly response because the dataset is intentionally local and ignored.

## Tests

Add deterministic offline tests using tiny generated fixture data.

Tests should cover:

1. GET endpoint rejects or handles blank query safely.
2. POST endpoint rejects or handles blank query safely.
3. Endpoint searches a tiny generated CSV/SQLite fixture through the adapter/index path.
4. Results include title, score, matched fields, snippet, and safe citation/provenance metadata.
5. Ranking order matches deterministic field weighting from `0024B`.
6. Missing dataset directory returns controlled warnings or controlled error.
7. Dataset search does not call provider/OpenAI.
8. Dataset search does not write to the Vanilla Cookbook database.
9. Dataset search does not require the real `recipe-dataset/` folder.
10. Existing health, config, provider, reader, recipe search, importer, RAG, meal-plan, dataset adapter, and dataset index tests still pass.

Tests must not require:

- the real Kaggle dataset
- network access
- OpenAI API key
- live provider calls
- Docker

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/dataset_search.py
ai-api/app/main.py
ai-api/app/schemas.py
ai-api/tests/test_dataset_search_api.py
scripts/inspect-recipe-index.py
docs/local-recipe-index.md
docs/indexed-dataset-retrieval.md
docs/indexing-roadmap.md
docs/dataset-attribution.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/repo-map.md
ai-api/README.md
outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md
```

Keep changes narrow. Do not do broad schema refactors unless absolutely necessary.

## .gitignore / Safety

Ensure these remain ignored:

```gitignore
recipe-dataset/
```

If generated local index artifact folders exist from earlier work, keep them ignored too.

Before committing, run:

```powershell
git status --short
```

Confirm no files under `recipe-dataset/` and no generated index artifacts are staged.

## Non-Goals

Do not implement:

- RAG over indexed dataset
- provider/OpenAI synthesis
- embeddings
- vector database
- persistent/generated index artifacts
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

## Documentation

Update docs to explain:

- `0024A` added local dataset adapter/schema inspection.
- `0024B` added deterministic local index/search helpers.
- `0024C` exposes deterministic indexed retrieval through API endpoints.
- Raw Kaggle data remains local and ignored.
- Generated indexes remain local/ignored or are not generated.
- Attribution/license docs remain in place.
- Endpoint returns source/citation metadata for dataset results.
- RAG over the indexed dataset is deferred to `0024D`.
- Embeddings/vector search remain deferred.

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
outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md
```

Include:

- Summary
- Files changed
- Confirmation that `0024A` and `0024B` prerequisites were present
- Endpoint(s) added
- Retrieval/index behavior
- Citation/provenance behavior
- Missing dataset behavior
- Validation results
- Confirmation that no provider/OpenAI calls were run
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next task: `0024D` RAG over indexed dataset with citations

## Commit

Commit and push:

```bash
git add .gitignore ai-api scripts docs README.md outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md
git commit -m "mailbox: complete task 0024C add indexed dataset retrieval endpoint"
git push origin main
```

## Done Criteria

- Indexed dataset retrieval endpoint exists.
- It uses `0024B` deterministic index/search logic.
- It builds from a bounded local dataset read.
- It returns ranked results with snippets/matched fields.
- It returns safe citation/provenance metadata.
- Missing dataset behavior is controlled.
- Tests are deterministic and offline.
- Real Kaggle dataset is not required for tests.
- No RAG/provider/OpenAI calls are added.
- No embeddings/vector DB are added.
- Raw `recipe-dataset/` files remain ignored and uncommitted.
- Generated index artifacts remain ignored/uncommitted or are not created.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
