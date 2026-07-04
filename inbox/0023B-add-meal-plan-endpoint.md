# Task 0023B: Add Meal Plan Endpoint

## Goal

Finish task 0023 by adding the provider-backed meal-plan endpoint on top of the deterministic foundation from `0023A`.

This task should implement the actual `POST /ai/meal-plan` endpoint, but keep automated validation offline and mock-only. It must cite saved recipes, avoid invented recipes, and avoid medical/nutrition certainty claims.

## Build On

Completed or expected prior work:

- `0017`: read-only recipe reader
- `0018`: deterministic recipe search
- `0019`: provider harness with mock default and OpenAI nano optional path
- `0021`: structured recipe importer
- `0022`: RAG ask endpoint
- `0023A`: meal-planner schemas and deterministic saved-recipe candidate selection

If `0023A` is not present or incomplete, stop and report what is missing instead of inventing a different design.

## Important Local Dataset Note

The developer may have a local dataset directory in the working clone:

```text
recipe-dataset/
  13k-recipes.csv
  13k-recipes.db
  5k-recipes.db
  metadata.json
  README.md
  tutorial.md
```

Do not ingest this dataset in task `0023B`.

Do not commit the raw dataset files.

If `.gitignore` does not already ignore local dataset folders, add a narrow ignore rule such as:

```gitignore
recipe-dataset/
```

The dataset/indexing layer will be handled in a later task after task 0023 is complete.

## Endpoint

Add:

```text
POST /ai/meal-plan
```

The endpoint should use the deterministic candidate selection from `0023A`, then use the provider harness to produce a structured meal-plan response from the selected saved recipe candidates only.

Suggested request:

```json
{
  "days": 3,
  "meals_per_day": 2,
  "preferences": "easy dinners with chicken or pasta",
  "excluded_ingredients": ["peanuts"],
  "tags": ["dinner"]
}
```

Suggested response shape:

```json
{
  "plan": {
    "days": [
      {
        "day": 1,
        "meals": [
          {
            "slot": "dinner",
            "recipe_id": "12",
            "title": "Chicken Pasta Bake",
            "reason": "Selected from saved recipes matching dinner and pasta."
          }
        ]
      }
    ]
  },
  "citations": [
    {
      "recipe_id": "12",
      "title": "Chicken Pasta Bake",
      "snippet": "..."
    }
  ],
  "provider": "mock",
  "model": "mock-basic",
  "selection": {
    "candidate_count": 3,
    "matched_recipe_ids": ["12", "18", "22"]
  },
  "warnings": []
}
```

Exact field names can differ if they align better with `0023A` schemas, but the endpoint must return validated structured JSON with saved recipe citations.

## Provider Strategy

Use the existing provider harness.

Required behavior:

- `mock` remains default.
- Automated tests use mock/offline behavior only.
- Do not run live OpenAI calls.
- OpenAI `gpt-5.4-nano` remains optional/manual only through the existing provider harness.
- Do not expose, print, log, or document provider keys.

The provider should receive only selected saved recipe candidate context, not the whole cookbook corpus.

## Structured Output

Use `provider.generate_structured(...)` if the 0023A schema supports it. Validate provider output before returning it.

The prompt/system instruction should enforce:

- use only selected saved recipes;
- cite recipe IDs/titles;
- do not invent external recipes;
- do not create medical or nutrition certainty claims;
- do not claim exact calories/macros unless present in saved recipe data;
- if there are not enough candidates, return warnings rather than inventing recipes.

## No-Match / Not-Enough-Candidates Behavior

If deterministic selection finds no candidates:

- return a controlled response with empty plan/citations and warnings;
- do not call the provider.

If there are fewer candidates than requested meals:

- reuse saved candidates only if the schema/design supports reuse; or
- return a partial plan plus warnings; but
- do not invent external recipes.

## Tests

Add deterministic offline tests for:

1. `POST /ai/meal-plan` rejects invalid request values.
2. Endpoint uses deterministic candidate selection before provider generation.
3. Provider prompt receives only selected candidate recipe context.
4. Response includes saved recipe citations.
5. No-match response does not call provider and does not invent recipes.
6. Not-enough-candidates behavior returns warnings and saved recipes only.
7. Response does not leak `OPENAI_API_KEY`, `sk-`, Authorization headers, or raw provider config.
8. No database write-back occurs.
9. Existing health, config, provider, reader, search, importer, RAG, and 0023A foundation tests still pass.

Tests must not require:

- real OpenAI API key
- network access
- live OpenAI calls
- Docker
- the real cookbook database
- the local `recipe-dataset/` folder

## Documentation

Update docs to explain:

- `0023A` added deterministic selection foundation.
- `0023B` adds `POST /ai/meal-plan`.
- Meal plans are grounded in saved recipes only.
- Citations are required.
- No external recipe invention is allowed.
- No medical/nutrition certainty claims are made.
- OpenAI nano is manual/optional only; validation remains mock-only.
- The larger 13K recipe dataset/indexing layer is intentionally deferred to the next phase.

Suggested docs to update:

```text
ai-api/README.md
docs/ai-sidecar-architecture.md
docs/ai-implementation-backlog.md
docs/ai-evals-plan.md
docs/repo-map.md
```

## Non-Goals

Do not implement:

- bulk dataset ingestion
- indexing layer
- embeddings
- vector database
- shopping-list generation beyond minimal placeholders if already present in 0023A schemas
- nutrition analysis
- calorie/macro calculation
- medical/dietary claims
- recipe write-back
- UI changes
- Cloudflare route changes
- deployment changes
- live OpenAI validation
- Anthropic/Gemini/Ollama real providers

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

## Outbox Report

Create:

```text
outbox/0023B-add-meal-plan-endpoint-results.md
```

Include:

- Summary
- Files changed
- Endpoint added
- How `0023A` foundation was used
- Provider behavior
- Citation behavior
- No-match/not-enough-candidates behavior
- Validation results
- Confirmation that no live OpenAI calls were run
- Confirmation that no `.env`, secrets, or raw dataset files were committed
- Confirmation that no database write-back was added
- Recommended next task: dataset/indexing foundation using local `recipe-dataset/`

## Commit

Commit and push:

```bash
git add .gitignore ai-api docs README.md outbox/0023B-add-meal-plan-endpoint-results.md
git commit -m "mailbox: complete task 0023B add meal plan endpoint"
git push origin main
```

## Done Criteria

- `POST /ai/meal-plan` exists.
- It uses `0023A` deterministic saved-recipe candidate selection.
- Provider receives only selected saved recipe context.
- Mock provider works by default.
- No live OpenAI calls are required.
- Meal plan response is validated structured JSON.
- Saved recipe citations are included.
- No-match/not-enough-candidates behavior is controlled.
- No recipes are invented.
- No recipe write-back occurs.
- No raw local dataset files are committed.
- No secrets are exposed.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
