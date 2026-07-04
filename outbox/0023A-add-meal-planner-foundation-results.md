# Task 0023A Results: Add Meal Planner Foundation

## Summary

Added the A-side meal-planner foundation for the `ai-api` sidecar. This task adds Pydantic schemas and deterministic saved-recipe candidate selection that a later 0023B task can use for `POST /ai/meal-plan`.

No meal-plan endpoint was added.

## Files Created

- `ai-api/app/meal_planner.py`
- `ai-api/tests/test_meal_planner.py`
- `docs/meal-planner-foundation.md`
- `outbox/0023A-add-meal-planner-foundation-results.md`

## Files Modified

- `README.md`
- `ai-api/README.md`
- `ai-api/app/schemas.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md`
- `docs/repo-map.md`

The tracked inbox task file was restored unchanged after inspection.

## Schemas Added

- `MealPlanFoundationRequest`
- `MealPlanRecipeReference`
- `MealPlanCandidateSelectionMetadata`
- `MealPlanFoundationResponse`

The request validates bounded days, meals per day, and candidate limit. Blank query text is normalized to `None`, and tags/excluded ingredients are stripped, lowercased, deduplicated, and kept deterministic.

## Deterministic Selection Behavior

`select_meal_plan_candidates(...)`:

- accepts saved `RecipeDocument` objects only;
- uses deterministic keyword search when query or tags are provided;
- falls back to stable saved-recipe order when no query is provided;
- returns saved recipe references with recipe ID, title, snippet, and matched fields;
- filters recipes that match excluded ingredients;
- returns warnings when filters remove recipes or too few saved candidates are available;
- never invents recipes.

## Explicit Non-Goals Preserved

- No `POST /ai/meal-plan` route was added.
- No provider harness call was added.
- No live OpenAI call was run.
- No shopping-list generation was added.
- No nutrition analysis was added.
- No medical or dietary certainty claims were added.
- No embeddings or vector database were added.
- No bulk ebook ingestion was added.
- No Vanilla Cookbook database write-back was added.
- No deployment or Cloudflare routing changes were made.
- No `.env` or secrets were committed.

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
  - AI API tests: PASS, `44 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings for text files.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Recommended Next Task

Proceed with `0023B`: add the provider-backed `POST /ai/meal-plan` endpoint on top of this deterministic saved-recipe candidate foundation, while preserving mock-only automated tests and no database write-back.
