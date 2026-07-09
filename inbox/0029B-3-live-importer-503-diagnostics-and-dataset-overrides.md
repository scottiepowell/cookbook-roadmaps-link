# Task 0029B-3: Live Importer 503 Diagnostics And Dataset Overrides

## Goal

Fix the live manual recipe-entry blocker where the demo UI returns `503 Service Unavailable` for `POST /ai/import-recipe` after the provider call fails.

Also add explicit dataset-path and dataset-limit overrides to the local demo startup script so RAG-informed importer testing can use the operator's full local recipe dataset instead of only the generated `.tmp-ai-demo` fixture dataset.

## Observed Failure

During manual live OpenAI testing after the provider startup override work, the server started successfully:

```text
Open: http://127.0.0.1:8000/demo
Cookbook DB path: C:\Users\scott\cookbook-roadmaps-link\.tmp-ai-demo\local\recipes.sqlite
Dataset path: C:\Users\scott\cookbook-roadmaps-link\.tmp-ai-demo\local\dataset
```

Readiness passed:

```text
GET /demo/readiness HTTP/1.1 200 OK
```

But recipe import failed:

```json
{"endpoint_name":"recipe.import","event":"ai.workflow","safe_error_type":"RecipeImportProviderError","status":"error"}
```

Request result:

```text
POST /ai/import-recipe HTTP/1.1 503 Service Unavailable
```

Durations were around 5-7 seconds:

```text
duration_ms=6842.21 status=503
duration_ms=5651.81 status=503
```

This looked like a timeout to the user, but the app returned a 503 from the provider-error path.

## Current Code Findings

### 1. Provider errors are too opaque for local operator debugging

`ai-api/app/providers/openai_provider.py` wraps all OpenAI structured-output exceptions as:

```python
raise ProviderCallError("OpenAI structured generation failed.") from exc
```

`ai-api/app/importer.py` catches provider errors and raises:

```python
raise RecipeImportProviderError("Recipe importer provider failed.") from exc
```

`ai-api/app/main.py` then returns:

```python
HTTPException(status_code=503, detail="Recipe importer provider is not available.")
```

This is safe for UI users, but not enough for local operator troubleshooting.

### 2. Strict structured-output schema may include unsupported/default metadata

`RecipeImportDraft` currently includes:

```python
servings: int | None = Field(default=4, ge=1, le=24)
```

The strict schema normalizer currently only recursively sets:

```python
additionalProperties = False
required = list(properties.keys())
```

It does not strip schema metadata like `default`, which may cause live structured-output provider errors depending on the provider's supported JSON-schema subset.

The default serving value should be applied in application logic/post-processing, not necessarily embedded as a provider schema default.

### 3. Demo startup still uses generated fixture dataset by default

`scripts/start-ai-demo-local.ps1` sets:

```powershell
$env:RECIPE_DATASET_DIR = Join-Path $ResolvedDataDir "dataset"
$env:RECIPE_DATASET_INDEX_LIMIT = "25"
```

This is good for safe mock/demo validation, but it prevents the operator from easily using the full local recipe dataset for RAG-informed manual testing.

The user expects importer RAG to be informed by the larger local dataset, described informally as around 14K recipes.

## Required Fixes

### 1. Add local operator-safe provider diagnostics

Keep public UI errors safe. Do not expose secrets or raw provider responses.

Add an opt-in local debug mechanism such as:

```text
AI_PROVIDER_DEBUG=true
```

When enabled, server logs may include sanitized provider exception class/type and short sanitized message.

Requirements:

- never print API keys;
- never print Authorization headers;
- never print raw prompt text by default;
- never print raw response JSON by default;
- never expose provider exception details to public UI responses;
- include enough detail in local logs to distinguish timeout, schema rejection, invalid model, quota/rate limit, authentication, and network failure.

Suggested safe log fields:

```json
{
  "provider_error_type": "BadRequestError",
  "provider_error_summary": "schema validation failed...",
  "workflow": "recipe.import"
}
```

Sanitize secret-like values before logging.

### 2. Fix strict structured-output schema compatibility

Update `ai-api/app/providers/openai_schema.py` to remove unsupported schema metadata before sending strict schemas to OpenAI.

At minimum consider stripping recursively:

```text
default
examples
title
description
```

Only strip fields that are not needed for validation and are unsafe/problematic for strict provider schemas.

Add tests showing:

- defaults are stripped from nested schema nodes;
- `additionalProperties=false` is still set;
- all properties are still required for strict structured output;
- the `RecipeImportDraft` schema sent to the provider does not include `default: 4` for `servings`.

Keep application behavior:

- `servings` still defaults to 4 in post-processing/application logic when the user does not specify servings;
- provider output should still validate as `RecipeImportDraft`.

If a non-null integer is easier for strict structured output, consider changing:

```python
servings: int | None = Field(default=4, ge=1, le=24)
```

to:

```python
servings: int = Field(default=4, ge=1, le=24)
```

but ensure the provider schema remains compatible after normalization.

### 3. Add demo startup overrides for timeout and dataset

Update `scripts/start-ai-demo-local.ps1` to support parameters such as:

```powershell
[string]$RecipeDatasetDir = ""
[Nullable[int]]$RecipeDatasetIndexLimit = $null
[Nullable[int]]$AiTimeoutSeconds = $null
[switch]$ProviderDebug
```

Expected behavior:

- default remains generated safe fixture dataset;
- operator can override dataset path for full local RAG testing;
- operator can override dataset index limit;
- operator can increase provider timeout for live RAG-informed importer testing;
- operator can enable sanitized provider debug logs locally.

Example full local RAG launch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

Do not require full dataset for normal tests/CI.

### 4. Add a lightweight local diagnostic command or script

Add or document a quick diagnostic command for the importer only, so the operator does not have to use the browser to isolate provider errors.

Option A: document PowerShell `Invoke-RestMethod` command against `/ai/import-recipe`.

Option B: add a small script such as:

```text
scripts/smoke-openai-importer-live.ps1
```

Requirements:

- opt-in only;
- does not print secrets;
- reports provider/model/status/error type safely;
- can run with a small fixture input like omelet or lemon beans;
- does not commit generated artifacts.

### 5. Preserve manual observations

Document that previous manual testing found weak steps for omelet, cheesecake, and chicken/rice casserole, and that 0029B-2 added RAG-informed recipe creation to improve this.

Manual observations to preserve:

```text
Results from omelet with cheese: steps are pretty weak; step 1 should be to scramble the eggs.
Results from carbonara recipe were acceptable.
Results from cheesecake: the steps were just one, very weak.
Results from chicken and rice casserole: weak steps.
```

## Documentation Updates

Update as needed:

```text
docs/ai-live-demo-runbook.md
docs/manual-recipe-entry-acceptance-2026-07.md if present
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0029B-3-live-importer-503-diagnostics-and-dataset-overrides-results.md
```

Docs should include:

- safe mock launch;
- live OpenAI launch;
- live OpenAI launch with timeout and full dataset override;
- how to verify readiness;
- how to run a quick importer-only diagnostic;
- what a 503 provider error means;
- how to enable sanitized provider debug logs locally.

## Tests

Add offline tests only. Do not run live OpenAI during normal validation.

Tests should cover:

- strict OpenAI schema normalizer strips `default` recursively;
- normalized schema still has `additionalProperties=false` and required properties;
- `RecipeImportDraft` schema normalization strips default metadata from `servings`;
- provider debug sanitizer removes secret-like strings;
- startup script syntax remains valid;
- startup script docs/examples are consistent;
- mock launch behavior remains safe by default;
- existing live smoke/eval wrappers still skip without opt-in.

If PowerShell script behavior is hard to test automatically, document manual validation in the outbox.

## Validation

Run normal validation:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke and live eval wrappers should skip cleanly unless live opt-in settings are present.

Optional operator live validation after implementation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

Then test one importer input:

```text
omelet with eggs cheese maybe onions cooked in butter fold it over
```

Expected:

- no 503;
- provider is `openai`;
- model is `gpt-5.4-nano`;
- servings is 4;
- quantities are populated where reasonable;
- steps are stronger;
- citations appear if the full dataset path is available and retrieval returns matches;
- no secrets are logged.

Do not require live OpenAI validation for completion unless the operator intentionally runs it.

## Non-Goals

Do not implement:

- production auth;
- paid access;
- invite sessions;
- database migrations;
- public route exposure;
- Cloudflare route changes;
- raw dataset commits;
- vector DB/Qdrant/Postgres;
- long-term recipe write-back;
- screenshot automation;
- committed `.tmp-ai-demo/` artifacts;
- committed raw provider response JSON;
- committed API keys, env files, raw datasets, screenshots, logs, or credentials.

## Outbox Report

Create:

```text
outbox/0029B-3-live-importer-503-diagnostics-and-dataset-overrides-results.md
```

Include:

- Summary
- Observed failure
- Root cause or most likely cause
- Provider diagnostics added
- Schema compatibility changes
- Startup script overrides added
- Dataset override behavior
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Recommended next task
- Artifact safety confirmation

## Commit

Commit and push:

```bash
git add ai-api scripts docs README.md outbox/0029B-3-live-importer-503-diagnostics-and-dataset-overrides-results.md

git commit -m "mailbox: complete task 0029B-3 live importer diagnostics and dataset overrides"

git push origin main
```

## Done Criteria

- Live importer 503 failures can be diagnosed safely with local opt-in debug logs.
- Strict OpenAI structured-output schemas are normalized to avoid problematic default metadata.
- `servings` still defaults to 4 in application behavior.
- Startup script supports provider timeout, dataset path, dataset limit, and provider-debug overrides.
- Full local dataset RAG testing is possible without editing env vars manually.
- Mock demo remains safe default.
- Normal validation remains offline.
- No generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.
