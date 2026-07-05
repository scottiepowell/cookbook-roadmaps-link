# 0024C Add Indexed Dataset Retrieval Endpoint Results

## Summary

Added deterministic indexed dataset retrieval over the local Kaggle recipe index from 0024B. The AI sidecar now supports:

- `GET /dataset/search?q=<query>&limit=<n>`
- `POST /dataset/search`

The endpoint builds a bounded in-memory index from local dataset records, returns ranked results, and includes safe provenance and index summary metadata. It does not add RAG over the indexed dataset, embeddings, vector storage, provider calls, generated index artifacts, Vanilla Cookbook imports, or write-back.

## Prerequisite Check

Confirmed before implementation:

- `ai-api/app/dataset_adapter.py` exists.
- `ai-api/app/dataset_index.py` exists.
- `ai-api/tests/test_dataset_adapter.py` exists.
- `ai-api/tests/test_dataset_index.py` exists.
- `scripts/inspect-recipe-index.py` exists.
- `docs/local-recipe-dataset-adapter.md` exists.
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md` exists.
- `outbox/0024B-build-local-deterministic-recipe-index-results.md` exists.
- `.gitignore` ignores `recipe-dataset/`.

## Files Created Or Modified

- Created `ai-api/app/dataset_retrieval.py`
- Created `ai-api/tests/test_dataset_search_api.py`
- Created `inbox/0024C-add-indexed-dataset-retrieval-endpoint.md`
- Created `outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md`
- Modified `.env.example`
- Modified `ai-api/app/config.py`
- Modified `ai-api/app/main.py`
- Modified `ai-api/app/schemas.py`
- Modified `ai-api/README.md`
- Modified `docs/local-recipe-dataset-adapter.md`
- Modified `docs/ai-sidecar-architecture.md`
- Modified `docs/ai-implementation-backlog.md`
- Modified `docs/repo-map.md`

## Endpoint Behavior

- Uses the 0024B deterministic index/search helpers.
- Reads a bounded number of records from `RECIPE_DATASET_DIR` or `recipe-dataset`.
- Uses `RECIPE_DATASET_INDEX_LIMIT`, default `100`, or request `dataset_limit` to bound indexed records.
- Builds an in-memory index per request.
- Returns ranked dataset recipe results with:
  - `id`
  - `source_id`
  - `title`
  - `score`
  - `matched_fields`
  - `snippet`
  - `source_file`
  - `source_table`
  - safe provenance metadata
- Includes index summary metadata:
  - document count
  - source counts
  - indexed fields
  - token count
  - deterministic build metadata
  - warnings
- Missing dataset directories return controlled warnings and empty results without exposing full local filesystem paths.

## Dataset And License Handling

Attribution remains intact:

- Food Ingredients and Recipes Dataset with Images
- Kaggle dataset by `pes12017000148`
- https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
- License: CC BY-SA 3.0
- https://creativecommons.org/licenses/by-sa/3.0/

The response provenance includes dataset name, creator, source URL, license, source file/table, and source ID. Raw `recipe-dataset/` files and generated index artifacts remain uncommitted.

## Tests

Added deterministic offline tests with tiny generated fixtures covering:

- `GET /dataset/search` ranked results;
- `POST /dataset/search`;
- empty query with index summary;
- missing dataset directory controlled warnings;
- no generated index artifacts.

Tests require no real Kaggle dataset, network access, provider key, live provider call, Docker runtime, or Vanilla Cookbook DB.

## Validation

- `python -m pytest ai-api\tests`: failed because the system Python does not have `pytest` installed (`No module named pytest`).
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed.
  - 63 AI API tests passed, including 5 new dataset search endpoint tests.
  - Shell syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.

## Safety Confirmation

Before commit, confirm:

- no files under `recipe-dataset/` are staged;
- no generated index artifacts are staged;
- no `.env` or secrets are staged.

No OpenAI/provider calls were added or run.

## Recommended Next Task

`0024D`: decide whether and how to add RAG over indexed dataset retrieval, with explicit grounding, citation, licensing, and provider cost controls.
