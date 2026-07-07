# 0027E Live OpenAI Demo Evals And Metrics Results

## Summary

Completed `0027E` by adding a repeatable live OpenAI demo eval harness with strict opt-in guardrails, generated demo-safe data, deterministic expected checks, metrics capture, and ignored artifact output.

The requested local inbox file `inbox/0027E-live-openai-demo-evals-and-metrics.md` was not present at the start of the local run. It was added on `origin/main` during the final rebase, then read and checked against this implementation before push.

Normal validation did not run live OpenAI calls. The new wrapper skips cleanly unless all live eval opt-in settings are present.

## Files Changed

- Added `scripts/run-openai-demo-evals.ps1`.
- Added `scripts/live-openai-demo-evals.py`.
- Added `evals/ai_cookbook/live_cases.json`.
- Added `evals/ai_cookbook/expected_checks.py`.
- Added `ai-api/tests/test_live_openai_demo_evals.py`.
- Added `docs/live-openai-demo-evals.md`.
- Updated `docs/ai-live-demo-runbook.md`.
- Updated `docs/ai-feature-status.md`.
- Updated `docs/ai-implementation-backlog.md`.
- Updated `README.md`.
- Added `outbox/0027E-live-openai-demo-evals-and-metrics-results.md`.

## Harness Behavior

The live eval harness:

- seeds generated demo-safe saved recipes and dataset data;
- runs in OpenAI provider mode only after explicit opt-in;
- mirrors the UI workflow order: readiness, importer, Ask My Cookbook, dataset search, dataset Ask/RAG, and meal planner;
- defines expected checks in `evals/ai_cookbook/live_cases.json`;
- scores results through deterministic helpers in `evals/ai_cookbook/expected_checks.py`;
- records latency, provider/model, warnings, citations, retrieved counts, token usage when available, and estimated cost when local rate inputs are provided;
- writes ignored artifacts under `.tmp-ai-demo/live-evals/<timestamp>/`;
- avoids printing or persisting API keys, key fragments, auth headers, raw environment files, or provider secrets.

Expected generated files:

- `results.jsonl`
- `summary.json`
- `summary.md`
- `responses/*.json`

Generated live eval results are not committed by default.

## Guardrails

The wrapper requires all of these before live calls:

- `AI_PROVIDER=openai`
- `OPENAI_ENABLE_LIVE_TESTS=true`
- `OPENAI_API_KEY` present
- `OPENAI_LIVE_TEST_BUDGET_CENTS` present and within 1 to 25
- `OPENAI_MODEL` configured, expected default `gpt-5.4-nano`
- `AI_MAX_OUTPUT_TOKENS` present and between 1 and 300

If required opt-in settings are missing, the wrapper exits `0` with a skip message and no live calls. Invalid numeric caps fail before live calls.

## Manual Live Run Shape

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The script prints the generated report path and a compact pass/fail summary when live evals run.

## OpenAI Docs And Pricing References Used

Official OpenAI references checked during this task:

- Structured Outputs guide: `https://platform.openai.com/docs/guides/structured-outputs`
  - Used to confirm the existing provider path should keep strict JSON Schema structured outputs for schema-constrained workflows.
- Evals guide: `https://platform.openai.com/docs/guides/evals`
  - Used to align the harness shape around predefined test data, expected criteria, and deterministic graders/checks.
- API pricing page: `https://developers.openai.com/api/docs/pricing`
  - Used to confirm pricing should be treated as current external configuration. The harness records usage tokens and estimates cost only when local rate environment variables are provided, avoiding hardcoded pricing drift.

## Validation Results

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 99 tests; 61 passed before 38 `tmp_path` setup errors.
  - The new `test_live_openai_demo_evals.py` tests passed in this run.
- Passed targeted: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_live_openai_demo_evals.py`
  - 9 passed.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `99 passed` for `ai-api\tests`.
  - Includes offline evals, shell script syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`
  - Output begins: `SKIP: OPENAI_ENABLE_LIVE_TESTS=true is required.`

Normal validation stayed offline. Live OpenAI calls were not run.

## Future Production Hardening

Future production tasks may include:

- authenticated access;
- time-limited sessions;
- paid access or monetization gate;
- usage metering;
- user/session isolation;
- durable storage;
- multi-use-case routing;
- deployment exposure controls;
- provider cost controls;
- admin/operator dashboard.

These were not implemented in this task.

## Safety Confirmation

- Live OpenAI calls were not run during normal validation.
- No live eval generated artifacts are committed.
- No raw Kaggle dataset files are committed.
- No screenshots are committed.
- No private environment files, provider keys, auth headers, raw environment contents, or credentials are committed.
