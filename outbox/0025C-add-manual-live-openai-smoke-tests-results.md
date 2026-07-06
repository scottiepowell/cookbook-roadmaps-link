# 0025C Add Manual Live OpenAI Smoke Tests Results

## Summary

Added a manual-only live OpenAI smoke-test path for the AI cookbook sidecar. Normal tests, offline evals, CI, and repository validation remain deterministic, mock-only, and free.

## Files Changed

- `scripts/smoke-openai-live.py`
- `ai-api/tests/test_openai_live_smoke_script.py`
- `.env.example`
- `docs/live-openai-smoke-tests.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `docs/repo-validation.md`
- `ai-api/README.md`
- `README.md`

## Smoke Workflows Covered

The manual script covers all five requested areas:

- provider/config sanity without printing secrets;
- structured recipe importer live call;
- Ask My Cookbook live call over tiny generated saved-recipe fixtures;
- Dataset Ask live call over a tiny generated local `13k-recipes.csv` fixture;
- meal-plan live call over a tiny generated saved-recipe SQLite fixture.

## Manual Command Added

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
# OPENAI_API_KEY should already be in local .env or process env, never committed
& .\.venv\Scripts\python.exe scripts\smoke-openai-live.py
```

Default command behavior without opt-in:

```text
SKIP: live OpenAI smoke tests are disabled.
```

## Guardrails Added

- Requires `OPENAI_ENABLE_LIVE_TESTS=true` exactly.
- Requires `AI_PROVIDER=openai`.
- Requires a local OpenAI API key in process environment or ignored local `.env`.
- Requires `OPENAI_LIVE_TEST_BUDGET_CENTS` between 1 and 25.
- Requires `AI_MAX_OUTPUT_TOKENS` at or below 300; defaults to 200 in the script if unset.
- Caps the smoke path at four live workflow calls.
- Uses tiny generated fixtures only.
- Does not read the real `recipe-dataset/` folder.
- Does not use a production Vanilla Cookbook DB.
- Does not print API keys, key prefixes, authorization headers, raw `.env`, raw provider config, or cloud secret names.

## Validation Results

Passed:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

Result: 9 offline eval cases passed.

Focused offline guardrail tests passed:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_openai_live_smoke_script.py
```

Result: 6 passed.

Direct Windows pytest command:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Result: failed because pytest could not access the local temp base directory:

```text
PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'
```

The new `test_openai_live_smoke_script.py` guardrail tests passed in that direct run before the temp-directory fixture failures. This matches the known local Windows temp-directory issue.

Passed via Git Bash repository validator:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

Result:

```text
75 passed, 1 warning
Offline evals passed: 9 cases.
Repository validation passed: 7 checks.
```

Passed:

```powershell
git diff --check
docker compose config --quiet
```

## Live Smoke Status

The live OpenAI smoke test was not run with real API calls because this task does not require using a real key during commit validation. The script was run without opt-in and skipped cleanly before any provider call.

## Safety Confirmation

Normal validation remains offline and mock-only. The live smoke script is not wired into CI, `scripts/validate-repo.sh`, offline evals, deployment, Cloudflare, or controller/demo workflows.

No `.env`, raw dataset files, generated index artifacts, OpenAI keys, or other secrets were staged or committed.

No Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, image/audio/file calls, batch jobs, production deployment changes, or Cloudflare changes were added.

## Recommended Next Task

Finalize the AI feature documentation and demo-readiness pass: capture a short operator runbook for mock demos, manual live smoke interpretation, and screenshots only if approved without exposing private recipes or secrets.
