# Task 0021 Results: Add Structured Recipe Importer

## Summary

Added a structured recipe importer draft endpoint to the `ai-api` sidecar. The endpoint accepts pasted recipe text, calls the existing provider harness with `generate_structured(...)`, validates the provider output with Pydantic, and returns a draft JSON object.

This is draft-only. It does not write to the Vanilla Cookbook database, modify recipes, add RAG, add embeddings, add meal planning, or generate shopping lists. No live OpenAI calls were run.

## Files Created

- `inbox/0021-add-structured-recipe-importer.md`
- `ai-api/app/importer.py`
- `ai-api/tests/test_importer.py`
- `outbox/0021-add-structured-recipe-importer-results.md`

The inbox file was missing in this checkout, so it was created from the task text provided in the prompt.

## Files Modified

- `ai-api/README.md`
- `ai-api/app/main.py`
- `ai-api/app/providers/mock.py`
- `ai-api/app/schemas.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-evals-plan.md`
- `docs/repo-map.md`

## Importer Behavior

- New endpoint: `POST /ai/import-recipe`.
- Request body: pasted recipe text plus optional source text.
- Response body: validated `RecipeImportDraft`, provider name, model name, warnings, and optional usage.
- Empty or whitespace-only recipe text returns request validation errors.
- Invalid provider output is converted into a controlled API error.
- Provider configuration failures are converted into a controlled API error.

## Schemas

Added Pydantic schemas for:

- `RecipeImportRequest`
- `RecipeIngredientDraft`
- `RecipeInstructionDraft`
- `RecipeImportDraft`
- `RecipeImportResponse`

The draft requires title, at least one ingredient, and at least one instruction.

## Provider Use

The importer uses the existing provider harness:

```python
provider.generate_structured(...)
```

`mock` remains the default provider and is used for all automated tests. The mock provider now resolves local JSON-schema `$defs` references so nested Pydantic draft schemas can produce deterministic structured fixtures.

OpenAI `gpt-5.4-nano` remains an optional manual provider path through the existing provider harness. Automated validation did not run live provider calls.

## Database Write-Back

No database write-back was added. Tests create a temporary SQLite database, call the importer endpoint, and verify the existing row remains unchanged. The importer service does not call the recipe reader or any database write path.

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
  - AI API tests: PASS, `31 passed`
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings for text files.
- `docker compose config --quiet`: passed after temporarily copying `.env.example` to `.env`; the temporary `.env` was removed and no containers were started.

## Recommended Next Task

Proceed with the next AI task: add the RAG ask endpoint over saved recipes using deterministic retrieval first and the mock provider for automated tests.
