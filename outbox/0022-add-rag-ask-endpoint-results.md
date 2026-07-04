# Task 0022 Results: Add RAG Ask Endpoint

## Summary

Added `POST /ai/ask` to the `ai-api` sidecar. The endpoint answers questions over saved recipe documents by running deterministic retrieval first and then asking the configured provider to synthesize from only the retrieved recipe context.

Mock remains the default provider for tests and validation. No live OpenAI calls were run.

## Files Created

- `inbox/0022-add-rag-ask-endpoint.md`
- `ai-api/app/rag.py`
- `ai-api/tests/test_rag.py`
- `outbox/0022-add-rag-ask-endpoint-results.md`

The inbox file was missing in this checkout, so it was created from the task text provided in the prompt.

## Files Modified

- `ai-api/README.md`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md`
- `docs/repo-map.md`

## Endpoint

```text
POST /ai/ask
```

Request:

```json
{
  "question": "What can I make with lemon?",
  "limit": 3
}
```

Response includes:

- `answer`
- `citations` with recipe IDs, titles, and snippets
- `provider` and `model`
- `retrieval` metadata
- `warnings`
- optional `usage`

## Retrieval And Grounding

- Retrieval uses deterministic keyword search over `RecipeDocument` objects.
- Conversational stop words are removed before retrieval to avoid broad matches.
- Only retrieved recipe context is sent to the provider.
- The full cookbook corpus is not sent to the provider.
- No embeddings or vector database were added.
- Recipe-specific answers include citations.
- No-match questions return a controlled no-match answer, empty citations, and a warning without calling the provider.

## Constraints Preserved

- No meal planning.
- No shopping-list generation.
- No bulk ebook ingestion.
- No Vanilla Cookbook database writes.
- No deployment or Cloudflare routing changes.
- No `.env` or secrets committed.
- Existing search behavior was not changed.
- Windows line-ending rules from task 0020 were not changed.

## Validation Results

```powershell
python -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `python -m pytest ai-api\tests`: unavailable in the active Windows Python because `pytest` is not installed.
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed.
  - Shell script syntax: PASS
  - Docker Compose configuration: PASS
  - AI API tests: PASS, `37 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings for text files.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Recommended Next Task

Proceed with the meal-planner task only after keeping the same guardrails: deterministic retrieval first, mock-only automated tests, citations to saved recipes, and no database write-back.
