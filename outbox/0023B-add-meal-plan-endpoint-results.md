# Task 0023B Results: Add Meal Plan Endpoint

## Summary

Added `POST /ai/meal-plan` on top of the deterministic saved-recipe candidate foundation from 0023A. The endpoint selects saved recipe candidates first, sends only those candidates to the provider, validates structured meal-plan output, and returns saved recipe citations.

Mock remains the default provider. No live OpenAI calls were run.

## Files Changed

- `.gitignore`
- `ai-api/README.md`
- `ai-api/app/main.py`
- `ai-api/app/meal_plan_endpoint.py`
- `ai-api/app/meal_planner.py`
- `ai-api/app/schemas.py`
- `ai-api/tests/test_meal_plan_endpoint.py`
- `ai-api/tests/test_meal_planner.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md`
- `docs/meal-planner-foundation.md`
- `docs/repo-map.md`
- `outbox/0023B-add-meal-plan-endpoint-results.md`

## Endpoint Added

```text
POST /ai/meal-plan
```

The endpoint accepts meal-plan request fields from the 0023A foundation plus `preferences` and `tags` aliases for the public endpoint shape.

## How 0023A Was Used

The endpoint calls `select_meal_plan_candidates(...)` before any provider call. It uses saved `RecipeDocument` objects loaded through the read-only recipe reader and never sends the whole cookbook corpus to the provider.

If no candidates are selected, the endpoint returns a controlled empty plan and does not call the provider.

## Provider Behavior

- Uses the existing provider harness.
- Mock is the default provider for automated tests.
- Provider receives only selected saved recipe candidate context.
- Provider output is validated as `MealPlanDraft`.
- Meals are coerced back to selected saved recipe IDs and titles before returning.
- OpenAI `gpt-5.4-nano` remains optional/manual only.

## Citation Behavior

The response includes citations for selected saved recipe candidates:

- recipe ID
- title
- snippet
- matched fields

Plans are constrained to saved recipe IDs from the selected candidates. Tests verify that unselected recipe context is not sent to the provider.

## No-Match And Not-Enough-Candidates Behavior

- No-match requests return an empty plan, empty citations, `provider: none`, `model: none`, and warnings.
- No-match requests do not call the provider.
- Not-enough-candidates requests return a partial plan using saved recipes only and warnings.
- No external recipes are invented.

## Dataset Handling

Added `.gitignore` rule:

```gitignore
recipe-dataset/
```

The local `recipe-dataset/` folder was not ingested and no raw dataset files were committed. Dataset/indexing work is deferred to a later task.

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
  - AI API tests: PASS, `49 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings for text files.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Confirmations

- No live OpenAI calls were run.
- No `.env`, secrets, or raw dataset files were committed.
- No database write-back was added.
- No deployment or Cloudflare routing changes were made.
- No embeddings, vector database, indexing layer, nutrition analysis, or shopping-list generation were added.

## Recommended Next Task

Add the dataset/indexing foundation using the local `recipe-dataset/` directory without committing raw dataset files.
