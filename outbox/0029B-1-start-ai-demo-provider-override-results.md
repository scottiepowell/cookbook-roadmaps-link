# 0029B-1: Start AI Demo Provider Override Results

Status: complete.

## Summary

Updated `scripts/start-ai-demo-local.ps1` so the local browser demo still defaults to safe mock mode but can intentionally launch in live OpenAI mode for manual acceptance with `-Provider openai -EnableLiveTests`.

## Root Cause

The launcher hardcoded `AI_PROVIDER=mock`, which overwrote operator-provided environment variables and caused manual live UI acceptance to keep using `provider=mock` and `model=mock-basic`.

## Files Changed

- `scripts/start-ai-demo-local.ps1`
- `ai-api/tests/test_start_ai_demo_local_script.py`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-manual-ui-acceptance-test.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-1-start-ai-demo-provider-override-results.md`

## New Script Parameters

- `-Provider mock|openai`
- `-OpenAIModel <model>`
- `-MaxOutputTokens <int>`
- `-LiveTestBudgetCents <int>`
- `-EnableLiveTests`

Existing `-Port` and `-DemoDataDir` parameters remain supported.

## Default Behavior

Running without parameters still starts mock mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

The script seeds generated demo data, sets generated fixture paths, starts `/demo`, and prints a safe startup summary.

## OpenAI Live Launch Behavior

Intentional live launch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

OpenAI defaults:

- `OPENAI_MODEL=gpt-5.4-nano`
- `OPENAI_LIVE_TEST_BUDGET_CENTS=25`
- `AI_MAX_OUTPUT_TOKENS=500`

Explicit bounded override example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests -OpenAIModel gpt-5.4-nano -MaxOutputTokens 600 -LiveTestBudgetCents 50 -Port 8001
```

## Env Override Behavior

The script resolves settings in this order:

1. explicit script parameter;
2. existing environment variable;
3. safe default.

This lets operators configure `AI_PROVIDER`, `OPENAI_MODEL`, `OPENAI_ENABLE_LIVE_TESTS`, `OPENAI_LIVE_TEST_BUDGET_CENTS`, or `AI_MAX_OUTPUT_TOKENS` before startup while still allowing command-line parameters to override them.

## Safety Behavior

- `Provider=mock` does not require OpenAI variables or an API key.
- `Provider=openai` requires `-EnableLiveTests` or existing `OPENAI_ENABLE_LIVE_TESTS=true`.
- `Provider=openai` fails fast if `OPENAI_API_KEY` is missing.
- The startup summary prints provider, model, live-test enabled state, budget, max output tokens, URL, cookbook DB path, and dataset path.
- The script does not print API keys, `.env` contents, auth headers, or secret-like values.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 17 cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: known Windows temp ACL issue; 117 tests collected, 79 passed, 38 setup errors rooted in `PermissionError: [WinError 5] Access is denied` on the per-user pytest temp directory. The new `test_start_ai_demo_local_script.py` tests passed in this run.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed; includes 117 API tests passed and 17 offline eval cases passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed; offline evals and endpoint smoke checks passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live eval opt-in settings were not present.
- PowerShell parser check for `scripts\start-ai-demo-local.ps1`: passed.
- Safe mock launch validation: started `scripts\start-ai-demo-local.ps1 -Provider mock -Port 8010`, confirmed `/demo/readiness` returned `provider.mode=mock`, `model=mock-basic`, 3 saved recipes, and dataset available, then confirmed no listener remained on port 8010.
- OpenAI missing-key fail-fast validation: with `OPENAI_API_KEY` removed from the subprocess environment, `scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests` exited with code 2 and printed a helpful missing-key message without printing a key.

## Live OpenAI

No live OpenAI calls were run for this task.

## Recommended Next Task

Resume `0029B`: Manual End-User Recipe Entry Acceptance.

## Artifact Safety

No generated artifacts, raw response JSON, `.tmp-ai-demo/`, API keys, private env files, raw datasets, screenshots, logs, or credentials were committed.
