# Meal Planner Foundation

Task 0023A adds only the deterministic foundation for a future meal-planner endpoint. It does not add `POST /ai/meal-plan`.

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

## What Does Not Exist Yet

Task 0023A intentionally does not add:

- `POST /ai/meal-plan`;
- provider-backed plan synthesis;
- OpenAI calls;
- shopping-list generation;
- nutrition analysis;
- medical or dietary certainty claims;
- embeddings or a vector database;
- bulk ebook ingestion;
- recipe database write-back.

## 0023B Direction

Task 0023B can build a provider-backed meal-plan endpoint on top of these saved-recipe candidates. It should keep prompts small by sending only selected saved recipe references and should require citations to saved recipes. Any generated plan should avoid external recipe invention and avoid medical or nutrition certainty claims.
