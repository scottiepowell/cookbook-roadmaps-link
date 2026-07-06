# 0025D Fix OpenAI Structured Output Schema Results

## Summary

Fixed the manual live OpenAI smoke-test structured-output schema issue by normalizing Pydantic JSON Schemas before sending them to OpenAI with `strict=True`.

The requested `inbox/0025D-fix-openai-structured-output-schema.md` file was not present in this checkout. All explicitly listed prerequisite files were present, so I proceeded from the task text in the prompt.

## Files Changed

- `ai-api/app/providers/openai_schema.py`
- `ai-api/app/providers/openai_provider.py`
- `ai-api/tests/test_openai_schema.py`

## Implementation

Added `normalize_strict_json_schema()` for OpenAI strict structured outputs.

Behavior:

- returns a deep-copied normalized schema and does not mutate the caller-provided schema;
- recursively walks dictionaries and lists;
- sets `additionalProperties: false` on every object schema with `properties`;
- sets `required` to all property names for every object schema with `properties`;
- normalizes nested object schemas and `$defs`;
- preserves nullable `anyOf` fields and existing Pydantic keywords.

`OpenAIProvider.generate_structured()` now sends the normalized schema in the OpenAI `text.format.schema` payload.

## Structured Workflows Covered

Offline tests cover strict-schema normalization for:

- `RecipeImportDraft`;
- nested `RecipeIngredientDraft`;
- nested `RecipeInstructionDraft`;
- `MealPlanDraft`;
- nested `MealPlanDay`;
- nested `MealPlanSlot`;
- `OpenAIProvider.generate_structured()` payload construction with a fake OpenAI client and no network calls.

## Validation Results

Focused tests passed:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_openai_schema.py ai-api\tests\test_providers.py
```

Result: 12 passed.

Offline evals passed:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

Result: 9 offline eval cases passed.

Direct Windows pytest command:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Result: failed because pytest could not access the local temp base directory:

```text
PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'
```

The new OpenAI schema tests passed in that direct run before the temp-directory fixture failures. This matches the known local Windows temp-directory issue.

Passed via Git Bash repository validator:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

Result:

```text
81 passed, 1 warning
Offline evals passed: 9 cases.
Repository validation passed: 7 checks.
```

Passed:

```powershell
git diff --check
docker compose config --quiet
```

## Safety Confirmation

No live OpenAI calls were run during validation. No CI live tests, production deployment changes, Cloudflare changes, Qdrant, Postgres, pgvector, embeddings, vector DB, `.env`, secrets, raw dataset files, or generated index artifacts were added.
