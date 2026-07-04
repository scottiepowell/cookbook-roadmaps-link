# Task 0023A: Add Meal Planner Foundation

## Goal

Add the foundation for the future meal-planner feature without adding provider calls or a public meal-plan endpoint yet.

This task should introduce typed schemas and deterministic saved-recipe selection helpers that later task `0023B` can use to build `POST /ai/meal-plan`.

This is intentionally a smaller A/B split to reduce long Codex task execution time.

## Build On

Existing completed work:

- `0017`: read-only recipe reader
- `0018`: deterministic recipe search
- `0019`: provider harness with mock default and OpenAI nano optional path
- `0021`: structured recipe importer
- `0022`: RAG ask endpoint with deterministic retrieval and citations

## Scope

Implement meal-planner foundation only:

1. Add Pydantic schemas for future meal planning.
2. Add deterministic saved-recipe selection logic.
3. Add unit tests for schemas and selection behavior.
4. Add documentation describing the planned 0023A/0023B split.
5. Do not add the final `POST /ai/meal-plan` endpoint in this task.
6. Do not call OpenAI or any provider in this task.

## Suggested Files

Create or modify as appropriate:

```text
ai-api/app/meal_planner.py
ai-api/app/schemas.py
ai-api/tests/test_meal_planner.py
docs/meal-planner-foundation.md
docs/ai-implementation-backlog.md
docs/ai-sidecar-architecture.md
docs/ai-evals-plan.md
docs/repo-map.md
ai-api/README.md
outbox/0023A-add-meal-planner-foundation-results.md
```

Keep changes narrow. If schema growth makes `ai-api/app/schemas.py` too large, do not perform a broad schema refactor in this task. Add a note to the outbox recommending a future schema split instead.

## Schema Requirements

Add typed models for the future meal planner. Suggested names:

```text
MealPlanRequest
MealPlanRecipeRef
MealPlanDay
MealPlanSlot
MealPlanSelection
MealPlanFoundationResponse
```

The exact names may differ if a simpler design fits the existing code better.

At minimum, represent:

- number of days
- meals per day or requested meal slots
- optional query/preferences text
- optional excluded ingredients
- optional tags
- selected saved recipe references
- recipe citations with recipe ID/title/snippet
- warnings

Validation should include:

- days is bounded, for example 1-14
- meals per day or slots are bounded, for example 1-6
- blank preferences are handled safely
- excluded ingredients and tags are normalized consistently

Do not include medical/nutrition certainty fields such as guaranteed calories, disease claims, or medical suitability.

## Deterministic Selection Logic

Add a helper that selects candidate recipes from saved `RecipeDocument` objects without using an LLM.

Suggested function:

```python
select_meal_plan_candidates(
    recipes: list[RecipeDocument],
    request: MealPlanRequest,
) -> MealPlanSelection
```

Selection behavior should:

- use existing deterministic search when query/preferences/tags are provided;
- fall back to stable recipe ordering when no query is provided;
- respect the requested number of candidate recipes needed for days/slots;
- filter or warn on excluded ingredients where simple deterministic matching is possible;
- return citations/references to saved recipes only;
- not invent external recipes;
- not write to the database;
- not call provider harness.

It is acceptable for the first version to be simple. This task is about creating a safe foundation for 0023B.

## Non-Goals

Do not implement:

- `POST /ai/meal-plan`
- provider-based plan synthesis
- shopping-list generation
- nutrition analysis
- calorie/macro calculation
- medical/dietary claims
- embeddings
- vector database
- bulk ebook ingestion
- recipe write-back
- UI changes
- Cloudflare route changes
- deployment changes
- live OpenAI validation
- Anthropic/Gemini/Ollama real providers

## Tests

Add deterministic offline tests for:

1. Meal planner request validation.
2. Candidate selection from recipe fixtures.
3. Query or tag-based selection uses saved recipes.
4. Excluded ingredient behavior works or produces clear warnings.
5. Selection never invents recipes.
6. No provider calls are made.
7. No database write-back occurs.
8. Existing health, config, provider, reader, search, importer, and RAG tests still pass.

Tests must not require:

- `OPENAI_API_KEY`
- network access
- live OpenAI calls
- Docker
- the real cookbook database

## Documentation

Update docs to explain:

- 0023A is the deterministic foundation only.
- 0023B will add the actual provider-backed `POST /ai/meal-plan` endpoint.
- Meal planning must cite saved recipes.
- No external recipe invention is allowed.
- No medical/nutrition certainty claims are made.
- The feature uses saved recipe candidates first to control cost and keep prompts small.

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
outbox/0023A-add-meal-planner-foundation-results.md
```

Include:

- Summary
- Files changed
- Schemas added
- Deterministic selection behavior
- Validation results
- Confirmation that no provider calls or live OpenAI calls were run
- Confirmation that no `.env` or secrets were committed
- Confirmation that no database write-back was added
- Recommended next task: `0023B` provider-backed meal-plan endpoint

## Commit

Commit and push:

```bash
git add ai-api docs README.md outbox/0023A-add-meal-planner-foundation-results.md
git commit -m "mailbox: complete task 0023A add meal planner foundation"
git push origin main
```

## Done Criteria

- Meal-planner foundation schemas exist.
- Deterministic saved-recipe candidate selection exists.
- Tests are deterministic and offline.
- No meal-plan endpoint is added yet.
- No provider calls are made.
- No live OpenAI calls are required.
- No recipes are invented.
- No recipe write-back occurs.
- No secrets are exposed.
- Documentation is updated.
- Outbox report exists.
- Validation passes.
- Changes are committed and pushed.
