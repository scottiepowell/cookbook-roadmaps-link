# Meal Planner Foundation

Task 0023A added the deterministic foundation for the meal-planner endpoint. Task 0023B added `POST /ai/meal-plan` on top of that foundation.

## What Exists

The `ai-api/app/meal_planner.py` helper selects saved recipe candidates from existing `RecipeDocument` objects. It can:

- use deterministic keyword search when a query or tags are provided;
- fall back to stable saved-recipe ordering when no query is provided;
- return saved recipe references with recipe IDs, titles, snippets, and matched fields;
- filter recipes whose ingredient text matches excluded ingredients;
- return warnings when filters remove recipes or too few saved candidates are available.

The schemas live in `ai-api/app/schemas.py`:

- `MealPlanFoundationRequest`
- `MealPlanRecipeReference`
- `MealPlanCandidateSelectionMetadata`
- `MealPlanFoundationResponse`

## Endpoint

`POST /ai/meal-plan` now:

- runs deterministic saved-recipe candidate selection first;
- sends only selected candidate context to the provider;
- validates structured provider output;
- returns saved recipe citations;
- returns controlled no-match and partial-plan warnings;
- uses mock by default in automated tests.

## Non-Goals

The meal-planner feature intentionally does not add:

- live OpenAI calls during validation;
- shopping-list generation;
- nutrition analysis;
- medical or dietary certainty claims;
- embeddings or a vector database;
- bulk ebook ingestion;
- recipe database write-back.

## Dataset And Indexing

The local `recipe-dataset/` directory is intentionally ignored and not ingested. Dataset and indexing work is deferred to a later task.
