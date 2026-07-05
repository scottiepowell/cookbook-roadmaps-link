# Task 0024D: Add RAG Over Indexed Dataset With Citations

## Goal

Add retrieval-augmented question answering over the local Kaggle recipe dataset index.

This task should add an API endpoint that answers questions by first retrieving relevant recipes from the deterministic dataset index introduced in `0024B` and exposed in `0024C`, then using the existing provider harness to synthesize a grounded answer from only those retrieved dataset results.

This is the first RAG layer over the local 13K recipe dataset. It must keep mock as the default provider, must not run live OpenAI calls during validation, and must include clear citations/provenance for any dataset-specific claims.

## Build On

Completed work:

- `0024A`: local Kaggle dataset adapter/schema inspection
- `0024B`: deterministic in-memory recipe index/search helpers
- `0024C`: indexed dataset retrieval endpoint
- `0019`: provider harness with mock default and OpenAI nano optional path
- `0022`: RAG ask endpoint over saved Vanilla Cookbook recipes

Before implementing, confirm the repo has:

- `ai-api/app/dataset_adapter.py`
- `ai-api/app/dataset_index.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/tests/test_dataset_adapter.py`
- `ai-api/tests/test_dataset_index.py`
- `ai-api/tests/test_dataset_search_api.py`
- `outbox/0024A-add-local-recipe-dataset-adapter-results.md`
- `outbox/0024B-build-local-deterministic-recipe-index-results.md`
- `outbox/0024C-add-indexed-dataset-retrieval-endpoint-results.md`
- `.gitignore` rule for `recipe-dataset/`

If any prerequisite is missing or incomplete, stop and write a short report explaining what is missing. Do not invent a separate adapter/index/retrieval design.

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

Keep attribution docs intact. Dataset RAG responses must include citation/provenance metadata so users can see the source dataset and license.

Do not commit the raw dataset or generated index artifacts.

## Endpoint

Add a dataset RAG endpoint.

Preferred endpoint:

```text
POST /dataset/ask
```

Suggested request:

```json
{
  "question": "What pasta recipes use chicken and tomatoes?",
  "limit": 5,
  "dataset_limit": 1000
}
```

Suggested response shape:

```json
{
  "answer": "Based on the indexed dataset results, there are chicken pasta recipes that include tomato-based ingredients. The strongest retrieved matches are Chicken Pasta Bake and Tomato Chicken Spaghetti.",
  "citations": [
    {
      "id": "13k-recipes.csv:123",
      "source_id": "123",
      "title": "Chicken Pasta Bake",
      "snippet": "...chicken...pasta...tomato...",
      "source_file": "13k-recipes.csv",
      "source_table": null,
      "license": "CC BY-SA 3.0",
      "source_url": "https://www.kaggle.com/datasets/pes12017000148/food-ingredients-and-recipe-dataset-with-images"
    }
  ],
  "provider": "mock",
  "model": "mock-basic",
  "retrieval": {
    "query": "What pasta recipes use chicken and tomatoes?",
    "retrieved_count": 2,
    "limit": 5,
    "dataset_limit": 1000,
    "matched_ids": ["13k-recipes.csv:123", "13k-recipes.csv:456"]
  },
  "warnings": [],
  "usage": {"input_tokens": 100, "output_tokens": 20}
}
```

Exact field names may differ if they align better with existing schema models, but the response must include:

- answer
- citations/provenance
- provider/model metadata
- retrieval metadata
- warnings
- optional usage

## Required Behavior

1. Retrieve first.

   Use `0024C` dataset retrieval / `0024B` deterministic index search before any provider call.

2. Send only retrieved dataset results to the provider.

   Do not send the full 13K corpus. Do not send unbounded raw recipe contents.

3. Mock remains default.

   Automated tests and validation must use mock/offline behavior only.

4. OpenAI remains optional/manual only.

   OpenAI `gpt-5.4-nano` may remain available through the existing provider harness, but do not run live OpenAI calls during validation.

5. No-match behavior must be controlled.

   If retrieval finds no dataset matches, return a controlled no-match response with empty citations and warnings. Do not call the provider and do not invent recipes.

6. Citations are required.

   Any dataset-specific answer must include citations with dataset/source/license metadata.

7. Prompt must enforce grounding.

   The provider prompt/system instruction must say:

   - answer only from retrieved dataset recipe context;
   - cite source IDs/titles;
   - do not invent recipes, ingredients, instructions, or source records;
   - if retrieved context is insufficient, say the indexed dataset does not contain enough information;
   - do not provide medical/nutrition certainty claims;
   - do not claim exact calories/macros unless present in the retrieved record context.

8. Secrets must not leak.

   Do not return, log, print, or document provider keys, token fragments, raw `.env` values, Authorization headers, or raw provider config.

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/dataset_rag.py
ai-api/app/main.py
ai-api/app/schemas.py
ai-api/tests/test_dataset_rag.py
ai-api/tests/test_dataset_ask_api.py
docs/dataset-rag.md
docs/indexing-roadmap.md
docs/dataset-attribution.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/repo-map.md
ai-api/README.md
outbox/0024D-add-rag-over-indexed-dataset-results.md
```

Keep changes narrow. Do not do broad schema/package refactors unless absolutely necessary.

## Provider Strategy

Use the existing provider harness.

Required behavior:

- default provider is `mock`;
- tests must not require `OPENAI_API_KEY`;
- no network calls;
- no live OpenAI calls;
- no provider call for no-match retrieval cases;
- no provider call should receive the full dataset.

If adding a live smoke-test note, document it as manual-only and skipped unless explicitly enabled. Do not add live tests to normal validation.

## Retrieval / Prompt Construction

Use the dataset retrieval results from `0024C`.

The prompt should include a compact context for each retrieved result, such as:

```text
[1]
ID: 13k-recipes.csv:123
Source ID: 123
Title: Chicken Pasta Bake
Matched fields: title, ingredients
Snippet: ...
Source file: 13k-recipes.csv
License: CC BY-SA 3.0
```

Do not include:

- full dataset;
- full raw CSV rows unless tiny and necessary;
- local filesystem paths;
- secrets;
- raw provider config;
- images.

## Missing Dataset Behavior

If the local `recipe-dataset/` folder is missing, return a controlled response with warnings and no provider call.

The response should not expose full local filesystem paths. It can say the configured local dataset directory is missing.

## Tests

Add deterministic offline tests using tiny generated fixture data.

Tests should cover:

1. Blank question is rejected or handled safely.
2. Matching dataset results are retrieved before provider generation.
3. Provider prompt contains only retrieved dataset results.
4. Provider prompt does not contain non-retrieved dataset rows.
5. Response includes citations/provenance with dataset name, source ID/file, license, and source URL.
6. No-match response does not call provider and does not invent recipes.
7. Missing dataset response is controlled and does not call provider.
8. Response does not leak `OPENAI_API_KEY`, `sk-`, Authorization headers, raw `.env`, or raw provider config.
9. No database write-back occurs.
10. Existing health, config, provider, reader, recipe search, importer, RAG over saved recipes, meal plan, dataset adapter, dataset index, and dataset search endpoint tests still pass.

Tests must not require:

- the real Kaggle dataset
- network access
- OpenAI API key
- live provider calls
- Docker

## Validation

Run from Windows PowerShell in the repo.

Prefer the repo venv for direct pytest:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If `.\.venv\Scripts\python.exe` is unavailable, document that direct pytest was unavailable and rely on `scripts/validate-repo.sh` only if it passes.

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no raw dataset files, generated index artifacts, `.env`, or secrets are staged.

## .gitignore / Safety

Ensure these remain ignored:

```gitignore
recipe-dataset/
```

If generated index artifact folders are introduced by mistake, remove them from the commit and add ignore rules if needed.

Do not commit:

- `recipe-dataset/`
- generated index artifacts
- `.env`
- provider keys
- API output containing private keys or full local paths

## Non-Goals

Do not implement:

- embeddings
- vector database
- persistent/generated index artifacts
- image ingestion
- image download/storage
- OCR
- importing records into Vanilla Cookbook
- recipe write-back
- meal planner changes
- shopping-list generation
- nutrition analysis
- UI changes
- Cloudflare/deployment changes
- live OpenAI validation
- Anthropic/Gemini/Ollama real providers
- committing raw dataset files
- committing generated indexes

## Documentation

Update docs to explain:

- `0024A` added dataset adapter/schema inspection.
- `0024B` added deterministic local index/search helpers.
- `0024C` added indexed dataset retrieval endpoints.
- `0024D` adds RAG synthesis over retrieved indexed dataset results.
- Raw Kaggle data remains local and ignored.
- Generated indexes remain uncommitted.
- Responses include source/provenance/license citations.
- Mock is default; OpenAI nano is manual/optional only.
- The provider receives only top-k retrieved context, not the full corpus.
- Embeddings/vector search remain deferred.

## Outbox Report

Create:

```text
outbox/0024D-add-rag-over-indexed-dataset-results.md
```

Include:

- Summary
- Files changed
- Confirmation that `0024A`, `0024B`, and `0024C` prerequisites were present
- Endpoint added
- Retrieval behavior
- Provider behavior
- Citation/provenance behavior
- No-match/missing-dataset behavior
- Validation results
- Confirmation that no live OpenAI calls were run
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add .gitignore ai-api docs README.md outbox/0024D-add-rag-over-indexed-dataset-results.md
git commit -m "mailbox: complete task 0024D add rag over indexed dataset"
git push origin main
```

## Done Criteria

- `POST /dataset/ask` exists.
- It retrieves through the local deterministic dataset index before provider generation.
- It sends only retrieved dataset results to the provider.
- Mock provider works by default.
- No live OpenAI calls are required.
- No-match/missing-dataset behavior is controlled and avoids provider calls.
- Dataset-specific answers include citations/provenance/license metadata.
- Tests are deterministic and offline.
- Real Kaggle dataset is not required for tests.
- No embeddings/vector DB are added.
- No raw dataset files or generated indexes are committed.
- No secrets are exposed.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
