# Task 0018 Results: Add Deterministic Recipe Search API

## Summary

Added deterministic keyword search over `RecipeDocument` objects in the `ai-api` sidecar. The search layer reads normalized documents from the existing read-only SQLite recipe reader and exposes both browser-friendly and JSON-body search endpoints.

This task did not add RAG, embeddings, recipe importing, meal planning, cookbook DB write-back, or live AI provider calls.

## Files Created

- `ai-api/app/search.py`
- `ai-api/tests/test_search.py`
- `ai-api/tests/test_search_api.py`
- `outbox/0018-add-deterministic-recipe-search-api-results.md`

## Files Modified

- `ai-api/README.md`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-schema-notes.md`
- `docs/repo-map.md`

## Search Ranking Behavior

- Query text is lowercased and tokenized into simple alphanumeric words.
- Search checks title, tags, ingredients, instructions, description, and source.
- Title matches score highest, followed by tags, ingredients, instructions, description, and source.
- Equal scores keep the original `RecipeDocument` input ordering.
- Results include ID, title, integer score, matched fields, and a short snippet.
- Empty and no-match queries return an empty result list.

## Endpoints Added

```text
GET  /recipes/search?q=<query>&limit=<n>
POST /recipes/search
```

The endpoints use `COOKBOOK_DB_PATH` through the existing read-only recipe reader. If the configured SQLite DB has no conservative recipe-like table, the API returns a controlled `422` response. Search responses do not include the raw recipe row.

## Validation Commands And Results

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `pytest ai-api/tests`: could not run directly because `pytest` is not installed on the shell PATH.
- `bash -n scripts/validate-repo.sh`: passed using Git Bash.
- `bash scripts/validate-repo.sh`: passed.
  - Docker Compose configuration: PASS
  - AI API tests: PASS, `20 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Assumptions And Limitations

- Search is deterministic keyword search only; it is not semantic retrieval.
- The production Vanilla Cookbook SQLite schema remains unknown in this repo.
- Fixture tests generate temporary SQLite databases and do not require a real `db/` directory.
- Provider keys are not required and no live AI providers are called.
- Snippets are intentionally minimal and do not expose raw recipe rows.
- This session used the available Windows clone at `C:\Users\scott\cookbook-roadmaps-link`; Git Bash could not reliably access `/home/coder/repo`.

## Recommended Next Task

Proceed with task 0019: add an AI provider abstraction and deterministic mock provider, keeping all tests offline and avoiding live provider calls.
