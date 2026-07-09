# Task 0029B-1: Start AI Demo Provider Override

## Goal

Fix the local AI demo startup script so manual end-user recipe-entry acceptance can intentionally run with either the safe mock provider or the live OpenAI provider.

The current `scripts/start-ai-demo-local.ps1` forces:

```powershell
$env:AI_PROVIDER = "mock"
```

This overrides operator-provided PowerShell environment variables such as:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="500"
$env:OPENAI_MODEL="gpt-5.4-nano"
```

Observed behavior during `0029B` manual testing:

```json
{"endpoint_name":"recipe.import","model":"mock-basic","provider":"mock","status":"ok"}
```

So the UI launched, but importer calls were still mock-backed.

## Relationship To 0029B

This is a blocker/fix task before continuing:

```text
0029B: Manual End-User Recipe Entry Acceptance
```

After this task, the operator should be able to launch the demo UI in mock mode by default or live OpenAI mode intentionally with command-line parameters.

## Required Behavior

Update `scripts/start-ai-demo-local.ps1` so that:

1. Safe default remains mock provider.
2. The script no longer blindly overwrites an explicit provider choice without operator intent.
3. The script supports command-line provider override.
4. The script provides useful defaults for the live manual-demo variables so the operator does not have to set every variable manually.
5. Live OpenAI mode requires `OPENAI_API_KEY` to already exist in the environment. Do not prompt for it. Do not print it.
6. The script prints a safe startup summary showing provider, model, budget, output-token cap, local URL, cookbook DB path, and dataset path.
7. The script never prints secrets or provider keys.
8. Existing mock demo behavior continues to work.

## Suggested Script Interface

Keep existing parameters:

```powershell
[int]$Port = 8000
[string]$DemoDataDir = ".tmp-ai-demo\local"
```

Add parameters such as:

```powershell
[ValidateSet("mock", "openai")]
[string]$Provider = $env:AI_PROVIDER

[string]$OpenAIModel = $env:OPENAI_MODEL

[int]$MaxOutputTokens = 500

[int]$LiveTestBudgetCents = 25

[switch]$EnableLiveTests
```

Implementation can choose equivalent names if cleaner, but the operator experience should support these patterns:

### Mock default

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Expected:

```text
AI_PROVIDER=mock
provider=mock
model=mock-basic or configured mock model
```

### Explicit OpenAI live mode

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Expected defaults when not otherwise provided:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_LIVE_TEST_BUDGET_CENTS=25
AI_MAX_OUTPUT_TOKENS=500
OPENAI_MODEL=gpt-5.4-nano
```

### Explicit OpenAI live mode with overrides

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 600 `
  -LiveTestBudgetCents 50 `
  -Port 8001
```

Expected:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_LIVE_TEST_BUDGET_CENTS=50
AI_MAX_OUTPUT_TOKENS=600
OPENAI_MODEL=gpt-5.4-nano
Port=8001
```

### Env override still works

If the operator sets env vars before running, the script should respect them unless an explicit script parameter overrides them:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_MODEL="gpt-5.4-nano"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Expected:

```text
AI_PROVIDER=openai
OPENAI_MODEL=gpt-5.4-nano
OPENAI_ENABLE_LIVE_TESTS=true
```

But if no env vars or parameters are set, default to mock.

## Recommended Defaults

Use safe defaults:

```text
Provider: mock
OpenAIModel: gpt-5.4-nano
MaxOutputTokens: 500
LiveTestBudgetCents: 25
EnableLiveTests: false unless Provider=openai and -EnableLiveTests is supplied or OPENAI_ENABLE_LIVE_TESTS=true already exists
```

Important safety behavior:

- If `Provider=openai` but live tests are not enabled, fail fast with a helpful message or explicitly set `OPENAI_ENABLE_LIVE_TESTS=true` only when `-EnableLiveTests` is supplied.
- If `Provider=openai` and `OPENAI_API_KEY` is missing, fail fast with a helpful message.
- If `Provider=mock`, do not require OpenAI variables or API key.

## Startup Summary

Print a safe summary similar to:

```text
AI demo data is ready.
Provider: openai
Model: gpt-5.4-nano
Live tests enabled: true
Budget cents: 25
Max output tokens: 500
Open: http://127.0.0.1:8000/demo
Logs will print in this terminal. Stop with Ctrl+C.
```

Do not print:

- `OPENAI_API_KEY`;
- any provider key value;
- `.env` contents;
- raw secret-like values.

## Documentation Updates

Update as needed:

```text
docs/ai-live-demo-runbook.md
docs/manual-recipe-entry-acceptance-2026-07.md if already created
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0029B-1-start-ai-demo-provider-override-results.md
```

At minimum, document the new startup commands for:

```powershell
# Mock default
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1

# Live OpenAI manual demo
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

## Tests

Add or update offline tests if practical for the PowerShell script behavior.

Suggested approaches:

- add a lightweight script syntax check;
- add docs examples validated by existing shell/Markdown checks;
- if there is a PowerShell test pattern, add tests for provider parameter handling;
- otherwise document manual command validation in the outbox.

Do not run live OpenAI during normal validation.

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

Also run at least a safe mock launch validation if possible:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

If this starts a long-running server, validate startup manually, then stop it with Ctrl+C and document the result.

Optional live validation, only if the operator intentionally enables it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Then verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/demo/readiness | ConvertTo-Json -Depth 10
```

Expected provider mode:

```text
openai
```

Do not require live validation for completion if no API key or operator approval is available.

## Outbox Report

Create:

```text
outbox/0029B-1-start-ai-demo-provider-override-results.md
```

Include:

- Summary
- Root cause
- Files changed
- New script parameters
- Default behavior
- OpenAI live launch behavior
- Env override behavior
- Safety behavior
- Validation results
- Whether live OpenAI was run or skipped
- Recommended next task
- Artifact safety confirmation

## Non-Goals

Do not implement:

- production auth;
- billing;
- invite sessions;
- paid access;
- database migrations;
- public route exposure;
- Cloudflare route changes;
- automatic browser testing;
- screenshot automation;
- committed `.tmp-ai-demo/` artifacts;
- committed raw response JSON;
- committed API keys, env files, raw datasets, screenshots, logs, or credentials.

## Commit

Commit and push:

```bash
git add scripts docs README.md outbox/0029B-1-start-ai-demo-provider-override-results.md

git commit -m "mailbox: complete task 0029B-1 start ai demo provider override"

git push origin main
```

## Done Criteria

- `start-ai-demo-local.ps1` defaults to mock safely.
- `start-ai-demo-local.ps1` can launch OpenAI mode intentionally with command-line parameters.
- Live manual demo defaults are available from the script: model, budget cents, max output tokens, and live-test enablement.
- Existing env vars are respected unless explicit parameters override them.
- Missing `OPENAI_API_KEY` fails fast only for OpenAI mode.
- Startup summary is useful and secret-safe.
- Normal validation remains offline.
- No generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.
