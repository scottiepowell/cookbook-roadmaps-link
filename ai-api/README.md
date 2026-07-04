# AI API Sidecar

This is the minimal FastAPI scaffold for the AI cookbook sidecar.

Current endpoints:

- `GET /health`: returns service health.
- `GET /ai/config`: returns non-secret provider availability booleans.
- `GET /recipes/search?q=<query>&limit=<n>`: deterministic keyword search over read-only recipe documents.
- `POST /recipes/search`: deterministic keyword search with a JSON body.
- `POST /ai/import-recipe`: converts pasted recipe text into a validated draft JSON object.
- `POST /ai/ask`: answers questions over saved recipes using deterministic retrieval plus grounded provider synthesis.
- `POST /ai/meal-plan`: creates a validated meal plan from selected saved recipe candidates.

Internal reader modules:

- `app.schema_inspector`: lists SQLite user tables and columns as structured objects.
- `app.recipe_reader`: opens SQLite with URI `mode=ro` and normalizes recipe-like rows into `RecipeDocument`.
- `app.search`: ranks `RecipeDocument` objects with deterministic keyword matching.
- `app.providers`: selects deterministic mock generation by default and contains the first OpenAI provider path.
- `app.importer`: calls the provider harness for structured recipe draft extraction and validates the result.
- `app.rag`: retrieves matching recipe documents and asks the provider to answer only from that retrieved context.
- `app.meal_planner`: selects deterministic saved-recipe candidates for meal-plan generation.
- `app.meal_plan_endpoint`: validates provider meal-plan output against saved recipe candidates.

This scaffold does not implement embeddings, shopping-list generation, nutrition analysis, live provider calls during validation, or write-back to Vanilla Cookbook.

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

## Structured Recipe Import

`POST /ai/import-recipe` accepts messy pasted recipe text and returns a draft only. It does not write to the Vanilla Cookbook database, modify recipes, search, plan meals, generate shopping lists, or create embeddings.

Example request:

```json
{
  "text": "Lemon beans: simmer beans with lemon and olive oil. Serve warm.",
  "source": "family notes"
}
```

The response contains validated draft fields:

```json
{
  "draft": {
    "title": "mock-value",
    "description": null,
    "ingredients": [{"name": "mock-value", "quantity": null, "unit": null, "note": null}],
    "instructions": [{"step": 1, "text": "mock-value"}],
    "tags": [],
    "source": null,
    "notes": null
  },
  "provider": "mock",
  "model": "mock-basic",
  "warnings": [],
  "usage": {"input_tokens": 10, "output_tokens": 4}
}
```

The mock provider is the default for local validation and CI. Optional OpenAI manual testing can use `AI_PROVIDER=openai`, `OPENAI_ENABLE_LIVE_TESTS=true`, `OPENAI_MODEL=gpt-5.4-nano`, and a locally configured provider key, but no live OpenAI calls are part of automated validation.

## Ask My Cookbook

`POST /ai/ask` answers questions over saved recipes. It first runs deterministic keyword retrieval over `RecipeDocument` objects, then sends only the retrieved recipe context to the configured provider. It never sends the full cookbook corpus to the provider.

Example request:

```json
{
  "question": "What can I make with lemon?",
  "limit": 3
}
```

The response includes an answer, citations, provider/model metadata, retrieval metadata, warnings, and optional usage:

```json
{
  "answer": "Mock response from mock-basic: Question: What can I make with lemon?...",
  "citations": [
    {"recipe_id": "1", "title": "Lemon Beans", "snippet": "Lemon Beans"}
  ],
  "provider": "mock",
  "model": "mock-basic",
  "retrieval": {
    "query": "What can I make with lemon?",
    "retrieved_count": 1,
    "limit": 3,
    "matched_recipe_ids": ["1"]
  },
  "warnings": [],
  "usage": {"input_tokens": 30, "output_tokens": 6}
}
```

If retrieval finds no saved recipe match, the endpoint returns a controlled no-match answer, empty citations, a warning, and no provider call. The endpoint does not write to the Vanilla Cookbook database and does not add embeddings, meal planning, shopping lists, or bulk ingestion.

## Meal Planner Foundation

The meal-planner foundation selects deterministic saved-recipe candidates from existing `RecipeDocument` objects. It can use the existing keyword search when a query or include tags are provided, returns saved recipe references with snippets, filters excluded ingredients deterministically, and emits warnings when fewer saved candidates are available than requested.

`POST /ai/meal-plan` builds on that foundation. The endpoint sends only selected saved recipe candidate context to the provider, validates structured output, coerces meals back to saved recipe IDs/titles, and returns citations. No-match requests return an empty plan with warnings and no provider call.

It does not create shopping lists, analyze nutrition, make medical or dietary certainty claims, invent recipes, ingest the local recipe dataset, index recipes, or write to the Vanilla Cookbook database.

## AI Provider Harness

The provider harness is used by the structured importer and Ask My Cookbook. It is not called by the search endpoints.

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
AI_PROVIDER=openai OPENAI_ENABLE_LIVE_TESTS=true pytest ai-api/tests/test_openai_live.py
```

There is no live test file yet. Future live smoke tests should stay skipped unless `OPENAI_ENABLE_LIVE_TESTS=true` and a local provider key are both present.

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
