# 0025E Fix Live Smoke Windows Cleanup Results

## Summary

Created and completed task 0025E. The manual live smoke script now has explicit, tested best-effort temporary directory cleanup for Windows, so a transient SQLite cleanup handle cannot mask successful live workflow validation.

## Files Changed

- `inbox/0025E-fix-live-smoke-windows-cleanup.md`
- `scripts/smoke-openai-live.py`
- `ai-api/tests/test_openai_live_smoke_script.py`
- `docs/live-openai-smoke-tests.md`
- `docs/ai-implementation-backlog.md`
- `outbox/0025E-fix-live-smoke-windows-cleanup-results.md`

## Implementation

- Factored smoke temp directory creation into `_make_smoke_temp_dir()`.
- The helper uses `tempfile.TemporaryDirectory(prefix="cookbook-openai-smoke-", ignore_cleanup_errors=True)`.
- `main()` uses the helper for live smoke fixture cleanup.
- Added an offline unit test that verifies best-effort cleanup is requested without making live calls.

Provider errors, workflow assertion failures, guardrail failures, and budget/config failures still return non-zero. Cleanup problems after successful live workflows no longer turn success into a false failure.

## Manual Live OpenAI Validation Recorded

The manual live OpenAI smoke test was run outside normal validation and passed:

```text
provider=openai
model=gpt-5.4-nano
live_calls=4
estimated_usage_tokens=1200
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

This result is now recorded in `docs/live-openai-smoke-tests.md`.

## Validation Results

Focused cleanup/guardrail tests passed:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_openai_live_smoke_script.py
```

Result: 7 passed.

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

The new smoke cleanup test passed in that direct run before the temp-directory fixture failures. This matches the known local Windows temp-directory issue.

Passed via Git Bash repository validator:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

Result:

```text
82 passed, 1 warning
Offline evals passed: 9 cases.
Repository validation passed: 7 checks.
```

Passed:

```powershell
git diff --check
docker compose config --quiet
```

## Safety Confirmation

No `.env`, API keys, raw datasets, generated indexes, or temp smoke files were staged or committed. No live OpenAI calls were added to normal validation or CI. No deployment, Cloudflare, Qdrant, Postgres, pgvector, embeddings, or vector DB changes were added.
