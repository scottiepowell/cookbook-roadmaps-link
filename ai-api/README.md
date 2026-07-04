# AI API Sidecar

This is the minimal FastAPI scaffold for the AI cookbook sidecar.

Current endpoints:

- `GET /health`: returns service health.
- `GET /ai/config`: returns non-secret provider availability booleans.
- `GET /recipes/search?q=<query>&limit=<n>`: deterministic keyword search over read-only recipe documents.
- `POST /recipes/search`: deterministic keyword search with a JSON body.

Internal reader modules:

- `app.schema_inspector`: lists SQLite user tables and columns as structured objects.
- `app.recipe_reader`: opens SQLite with URI `mode=ro` and normalizes recipe-like rows into `RecipeDocument`.
- `app.search`: ranks `RecipeDocument` objects with deterministic keyword matching.
- `app.providers`: selects deterministic mock generation by default and contains the first OpenAI provider path.

This scaffold does not implement RAG, embeddings, recipe import, meal planning, live provider calls during validation, or write-back to Vanilla Cookbook.

## Recipe Search

Search is intentionally deterministic and offline. It lowercases and tokenizes simple words, searches recipe title, tags, ingredients, instructions, description, and source, and returns minimal result fields:

```json
{
  "query": "beans",
  "count": 1,
  "results": [
    {
      "id": "1",
      "title": "Lemon Beans",
      "score": 10,
      "matched_fields": ["title"],
      "snippet": "Lemon Beans"
    }
  ]
}
```

Title and tag matches rank above ingredient and instruction matches. Equal scores keep fixture/input ordering stable. Empty or no-match queries return an empty result list.

## AI Provider Harness

The provider harness is present for later importer, RAG, and meal-planning tasks. It is not called by the current search endpoints.

Default local configuration:

```text
AI_PROVIDER=mock
AI_MODEL=mock-basic
AI_MAX_OUTPUT_TOKENS=700
AI_TIMEOUT_SECONDS=20
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
OPENAI_ENABLE_LIVE_TESTS=false
```

`mock` is the default provider and returns deterministic text and structured JSON-shaped responses for offline tests. `openai` is the first real provider path and uses the official OpenAI Python SDK lazily, with `gpt-5.4-nano` as the default model and `gpt-5.4-mini` configured as a fallback for future explicit use.

Manual live smoke tests are opt-in only and were not added to automated validation:

```bash
AI_PROVIDER=openai OPENAI_ENABLE_LIVE_TESTS=true OPENAI_API_KEY=... pytest ai-api/tests/test_openai_live.py
```

There is no live test file yet. Future live smoke tests should stay skipped unless `OPENAI_ENABLE_LIVE_TESTS=true` and `OPENAI_API_KEY` are both present.

## Cookbook DB Path

The future production DB path is configured with `COOKBOOK_DB_PATH`. The current default is:

```text
/data/cookbook-db/dev.db
```

No Compose DB mount is enabled yet. When the production reader is wired into Compose, mount the cookbook DB read-only, for example `./db:/data/cookbook-db:ro`.

## Local Tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest tests
```

The root repository validator also runs these tests in a temporary virtual environment:

```bash
bash scripts/validate-repo.sh
```

Provider keys are optional. `/ai/config` only reports whether provider settings are present and never returns key values, token fragments, raw base URLs, or model strings.
