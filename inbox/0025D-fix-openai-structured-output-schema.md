# Task 0025D: Fix OpenAI Structured Output Schema Compatibility

## Goal

Fix the manual live OpenAI smoke-test failure caused by strict structured-output JSON Schema incompatibility.

The live smoke script reached OpenAI successfully, but the first structured workflow failed before model output because the schema sent for `RecipeImportDraft` was not compatible with OpenAI strict structured outputs.

Observed error:

```text
Invalid schema for response_format 'RecipeImportDraft': In context=(), 'additionalProperties' is required to be supplied and to be false.
```

This task should make the OpenAI provider convert Pydantic-generated schemas into the strict JSON Schema subset expected by OpenAI Structured Outputs, while keeping mock/offline validation deterministic and avoiding live calls in normal validation.

## Build On

Completed work:

- `0019`: provider harness with mock default and OpenAI optional/manual path
- `0021`: structured recipe importer
- `0023B`: meal-plan endpoint using structured provider output
- `0025C`: manual live OpenAI smoke-test script

Before implementing, confirm the repo has:

- `ai-api/app/providers/openai_provider.py`
- `ai-api/app/providers/base.py`
- `ai-api/app/importer.py`
- `ai-api/app/meal_plan_endpoint.py`
- `ai-api/app/schemas.py`
- `scripts/smoke-openai-live.py`
- `docs/live-openai-smoke-tests.md`
- `outbox/0025C-add-manual-live-openai-smoke-tests-results.md`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Root Cause

`OpenAIProvider.generate_structured()` currently sends:

```python
"schema": request.schema,
"strict": True,
```

The schema comes from Pydantic `model_json_schema()`. The raw schema does not consistently include OpenAI-required strict fields such as:

```json
"additionalProperties": false
```

on every object schema.

OpenAI strict structured outputs also require every object property to be listed in `required`; optional values should be represented as nullable types / `anyOf` with `null`, not by omitting fields from `required`.

## Scope

Implement schema normalization for OpenAI structured outputs.

Add a small, well-tested utility that takes the Pydantic JSON schema and returns an OpenAI-compatible strict schema.

Suggested location:

```text
ai-api/app/providers/openai_schema.py
```

or keep it inside `openai_provider.py` if the project is still small.

The normalizer should:

1. Recursively walk dictionaries/lists.
2. For every schema object with `type: "object"` and `properties`, set:

   ```json
   "additionalProperties": false
   ```

3. For every schema object with `type: "object"` and `properties`, set:

   ```json
   "required": [all property names]
   ```

   Preserve deterministic key ordering.

4. Apply the same logic inside `$defs` / definitions and nested objects.
5. Preserve valid nullable/`anyOf` schemas for optional fields.
6. Avoid mutating the caller-provided schema in place.
7. Strip or handle unsupported/default Pydantic keywords only if tests or OpenAI errors require it.
8. Keep generated schema compact and deterministic.

Use the normalized schema only for the OpenAI provider. Do not change mock provider behavior unless needed for tests.

## Structured Workflows To Cover

The fix should cover all current structured OpenAI workflows:

- `RecipeImportDraft`
- `MealPlanDraft`

If other structured schemas are added later, the same normalizer should apply automatically.

## Tests

Add offline tests for schema normalization and provider request construction.

Tests should cover:

1. Root `RecipeImportDraft` schema includes `additionalProperties: false`.
2. Nested ingredient/instruction object schemas include `additionalProperties: false`.
3. Root `required` contains all root properties, including nullable/defaulted fields.
4. Nested `required` contains all nested properties, including nullable/defaulted fields.
5. `$defs` schemas are normalized.
6. The original Pydantic schema object is not mutated.
7. `OpenAIProvider.generate_structured()` sends the normalized schema to the OpenAI client.
8. Normal offline tests/evals still pass without live OpenAI credentials.

Use a fake OpenAI client or monkeypatch `_client_instance()` so tests do not make network calls.

## Manual Live Smoke Behavior

After this fix, `scripts/smoke-openai-live.py` should be able to progress past the importer structured-output schema failure when run manually with:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
& .\.venv\Scripts\python.exe .\scripts\smoke-openai-live.py
```

Do not run live OpenAI calls during normal validation or from Codex unless explicitly requested and credentials are available locally.

If the manual live smoke later fails on a new OpenAI schema restriction, document the exact next error in the outbox and keep the fix narrow.

## Documentation

Update docs as needed:

```text
docs/live-openai-smoke-tests.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
ai-api/README.md
outbox/0025D-fix-openai-structured-output-schema-results.md
```

Docs should explain:

- Pydantic schemas are normalized before being sent to OpenAI strict structured outputs;
- normal validation remains mock/offline;
- live smoke tests remain manual-only;
- if live smoke fails, the error may identify the next compatibility issue to fix.

## Non-Goals

Do not implement:

- production deployment changes
- Cloudflare changes
- GitHub Actions live tests
- CI live OpenAI tests
- controller/demo workflows
- Qdrant
- Postgres
- pgvector
- embeddings
- vector DB
- persistent generated indexes
- raw dataset commits
- `.env` or secret commits
- live calls as part of normal validation

## Validation

Run from Windows PowerShell:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct Windows pytest still fails with the known temp-directory permission issue, document the exact error and confirm Git Bash validator passes.

Manual live smoke can be run separately by the developer after commit. If it is not run in this task, say so clearly.

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no raw dataset files, generated index artifacts, `.env`, or secrets are staged.

## Outbox Report

Create:

```text
outbox/0025D-fix-openai-structured-output-schema-results.md
```

Include:

- Summary
- Files changed
- Root cause
- Schema normalization behavior
- Tests added
- Validation results
- Whether manual live OpenAI smoke was run or skipped
- If skipped, why
- Confirmation that no live OpenAI calls were run during normal validation
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next step for the developer to rerun live smoke manually

## Commit

Commit and push:

```bash
git add ai-api scripts docs README.md outbox/0025D-fix-openai-structured-output-schema-results.md

git commit -m "mailbox: complete task 0025D fix openai structured schema"

git push origin main
```

## Done Criteria

- OpenAI structured schema normalizer exists.
- `OpenAIProvider.generate_structured()` uses the normalized schema.
- Root and nested object schemas include `additionalProperties: false`.
- Root and nested object schemas list all properties as required.
- Original schema is not mutated.
- Offline tests cover the normalizer and provider request construction.
- Normal validation remains offline/mock-only.
- Manual live smoke remains opt-in only.
- Documentation/outbox updated.
- No secrets or raw datasets are committed.
- Changes are committed and pushed.
