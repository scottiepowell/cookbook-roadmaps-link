# 0024D Add RAG Over Indexed Dataset Results

## Summary

Added `POST /dataset/ask` to answer questions over the local indexed Kaggle recipe dataset. The endpoint retrieves through the deterministic 0024B/0024C dataset index first, sends only retrieved result context to the provider, and returns grounded answer metadata with dataset citations.

No embeddings, vector database, generated index artifacts, image ingestion, Vanilla Cookbook imports/write-back, meal planner changes, shopping-list generation, deployment changes, raw dataset files, `.env`, or secrets were added.

## Prerequisite Check

Confirmed before implementation:

- `ai-api/app/dataset_adapter.py` exists.
- `ai-api/app/dataset_index.py` exists.
- `ai-api/app/dataset_retrieval.py` exists.
- `ai-api/tests/test_dataset_adapter.py` exists.
- `ai-api/tests/test_dataset_index.py` exists.
- `ai-api/tests/test_dataset_search_api.py` exists.
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md` exists.
- `outbox/0024B-build-local-deterministic-recipe-index-results.md` exists.
- `outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md` exists.
- `.gitignore` ignores `recipe-dataset/`.

## Files Created Or Modified

- Created `ai-api/app/dataset_rag.py`
- Created `ai-api/tests/test_dataset_ask.py`
- Created `inbox/0024D-add-rag-over-indexed-dataset.md`
- Created `outbox/0024D-add-rag-over-indexed-dataset-results.md`
- Modified `ai-api/app/main.py`
- Modified `ai-api/app/schemas.py`
- Modified `ai-api/README.md`
- Modified `docs/local-recipe-dataset-adapter.md`
- Modified `docs/ai-sidecar-architecture.md`
- Modified `docs/ai-implementation-backlog.md`
- Modified `docs/repo-map.md`

## Endpoint Added

- `POST /dataset/ask`

Request fields:

- `question`
- `limit`
- `dataset_limit`

Response fields:

- `answer`
- `citations`
- `provider`
- `model`
- `retrieval`
- `warnings`
- `usage`

## Retrieval And Prompt Behavior

- Runs deterministic dataset retrieval before provider generation.
- Uses the 0024C bounded in-memory dataset search path.
- Sends only retrieved result context to the provider, not the full 13K corpus.
- Filters common question filler terms before retrieval to avoid source-file false positives.
- Prompt instructions require answers only from retrieved dataset context.
- Prompt instructions prohibit invented recipes, ingredients, instructions, source records, medical/nutrition certainty claims, and exact calorie/macro claims unless present in retrieved context.

## Citation And Provenance Behavior

Citations include:

- index result ID;
- source ID;
- title;
- snippet;
- matched fields;
- dataset title;
- Kaggle creator;
- source URL;
- source file/table;
- CC BY-SA 3.0 license and license URL.

The endpoint does not expose full local filesystem paths.

## Missing Dataset And No-Match Behavior

- Missing local dataset directory returns a controlled response with warnings, empty citations, `provider: none`, and no provider call.
- No-match questions return a controlled no-match answer, empty citations, `provider: none`, and no provider call.

## Dataset And License Handling

Attribution remains intact:

- Food Ingredients and Recipes Dataset with Images
- Kaggle dataset by `pes12017000148`
- https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images
- License: CC BY-SA 3.0
- https://creativecommons.org/licenses/by-sa/3.0/

Raw `recipe-dataset/` files and generated index artifacts remain uncommitted.

## Tests

Added deterministic offline tests with generated CSV fixtures covering:

- retrieval context sent to provider;
- endpoint use of mock provider and dataset citations;
- no-match no-provider-call behavior;
- missing-dataset no-provider-call behavior;
- blank question validation;
- no generated index artifacts.

Tests require no real Kaggle dataset, network access, OpenAI API key, live provider call, Docker runtime, or Vanilla Cookbook DB.

## Validation

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: failed with Windows `PermissionError` creating/scanning pytest temp directories. A retry with `--basetemp=.tmp-pytest-run` failed with the same temp-directory permission issue.
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed during implementation.
  - 69 AI API tests passed, including 6 new dataset ask tests.
  - Shell syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.

## Safety Confirmation

Before commit, confirm:

- no files under `recipe-dataset/` are staged;
- no generated index artifacts are staged;
- no `.env` or secrets are staged.
- local `.tmp-pytest*/` validation temp directories are ignored and not staged.

No live OpenAI calls were run.

## Recommended Next Task

Add offline eval cases for dataset ask grounding, citation completeness, no-match behavior, and secret leakage before considering UI exposure or live provider smoke tests.
