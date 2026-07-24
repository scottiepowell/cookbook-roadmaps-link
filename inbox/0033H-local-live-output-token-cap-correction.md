# 0033H Local Live Output Token Cap Correction

## Goal

Update the local live product launcher so manual live browser testing can use the proven larger output-token cap.

Manual testing showed that the current `scripts/start-ai-demo-local.ps1` local live guard still rejects values above 300:

```text
AI_MAX_OUTPUT_TOKENS must be between 1 and 300 for local live mode.
```

The local live product path should now default to 500 output tokens and allow an explicit value up to 1000. Values above 1000 must fail fast with a clear error before the sidecar starts.

This is a focused runtime/script correction. Do not broaden into provider routing, new model support, QMD integration, analytics, ads, auth, AWS/platform work, or public route exposure.

## Context

Relevant current script behavior:

- `scripts/start-ai-demo-local.ps1` safe live defaults still set `AI_MAX_OUTPUT_TOKENS = "300"`.
- The script initializes `$DefaultMaxOutputTokens = 500`, but then overrides it to 300 when `Provider=openai`.
- The script rejects local OpenAI live mode when `$EffectiveMaxOutputTokens -gt 300`.
- Operator-approved manual diagnostic evidence previously established that 500 succeeds for the strict importer path, 400 failed safely, and 1000 remains the troubleshooting ceiling.

The requested new local live launcher policy is:

```text
Provider=mock:
  keep existing offline/mock behavior; no live provider calls.

Provider=openai local live mode:
  default AI_MAX_OUTPUT_TOKENS = 500
  valid range = 500..1000 inclusive
  values below 500 fail fast with a clear error
  values above 1000 fail fast with a clear error
```

Keep the existing model gate: local OpenAI product mode still permits only `gpt-5.4-nano`.

Keep the existing live-call gate: `Provider=openai` still requires `-EnableLiveTests` or `OPENAI_ENABLE_LIVE_TESTS=true`, a valid local API key, and the live budget guard.

## Required Work

### 1. Update the launcher

Update:

```text
scripts/start-ai-demo-local.ps1
```

Required behavior:

- Change safe local live default `AI_MAX_OUTPUT_TOKENS` from `300` to `500`.
- Remove the openai-specific default override to `300`.
- For `Provider=openai`, validate `AI_MAX_OUTPUT_TOKENS` as `500..1000` inclusive.
- Error clearly when the OpenAI local live value is below 500.
- Error clearly when the OpenAI local live value is above 1000.
- Preserve mock/offline behavior and existing mock validation.
- Preserve the existing budget validation of `OPENAI_LIVE_TEST_BUDGET_CENTS=1..25`.
- Preserve the existing local model allowlist of `gpt-5.4-nano` only.
- Preserve secret redaction and startup summary behavior.

Suggested error text:

```text
AI_MAX_OUTPUT_TOKENS must be between 500 and 1000 for local live mode.
```

### 2. Update tests

Add or update deterministic tests to cover the launcher behavior without live provider calls.

Cover at minimum:

- `-Provider openai -MaxOutputTokens 500 -CheckRuntimeProfile` accepts the cap when other required live inputs are safely stubbed.
- `-Provider openai -MaxOutputTokens 1000 -CheckRuntimeProfile` accepts the cap when other required live inputs are safely stubbed.
- `-Provider openai -MaxOutputTokens 1001 -CheckRuntimeProfile` exits non-zero and prints the new clear error.
- `-Provider openai -MaxOutputTokens 499 -CheckRuntimeProfile` exits non-zero and prints the new clear error.
- `-WriteMissingLiveDefaults` writes/keeps `AI_MAX_OUTPUT_TOKENS=500` as the safe local live default, never writes `OPENAI_API_KEY`, and preserves existing comments/values where applicable.
- `-Provider mock` remains offline and does not require or inherit live behavior.

Do not make live OpenAI calls in tests.

### 3. Update docs/status

Update documentation that still says local live product mode defaults to or requires a 300-token cap.

Likely files:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/live-openai-demo-evals.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Be precise about scope:

- Local live product/browser testing now defaults to 500 and allows 500..1000.
- 1000 is allowed as an explicit ceiling, not the normal recommended default.
- The recommended default is 500.
- Mock/offline validation remains unchanged.
- Live smoke/eval wrappers may have separate workflow-specific caps; do not conflate them unless the code actually shares the same setting.
- The importer diagnostic cap history remains: 500 passed, 400/300 too low, 1000 troubleshooting ceiling.

### 4. Add outbox report

Create:

```text
outbox/0033H-local-live-output-token-cap-correction-results.md
```

Summarize:

- launcher default changed to 500;
- local live allowed range changed to 500..1000;
- >1000 and <500 fail fast;
- docs updated;
- tests/validation run;
- mock/offline and no-live-call boundaries preserved;
- explicit non-goals.

## Acceptance Criteria

- `scripts/start-ai-demo-local.ps1` defaults local live `AI_MAX_OUTPUT_TOKENS` to 500.
- `Provider=openai` local live mode accepts `-MaxOutputTokens 500`.
- `Provider=openai` local live mode accepts `-MaxOutputTokens 1000`.
- `Provider=openai` local live mode rejects `-MaxOutputTokens 1001` before startup.
- `Provider=openai` local live mode rejects `-MaxOutputTokens 499` before startup.
- Error text no longer says the local live maximum is 300.
- Safe default writer uses 500 and still never writes `OPENAI_API_KEY`.
- Mock/offline validation remains unchanged.
- No live OpenAI call is made during normal validation.
- No provider routing, model allowlist, QMD, analytics, ads, auth, payment, SSO/BYOS, AWS/platform, public route, or browser UI feature work is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, or local env values are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1

& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

git diff --check

docker compose config --quiet

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

Do not run live OpenAI during normal validation.

## Manual post-fix check

After implementation, this should no longer fail with the old 300-token message:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 800 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

Do not run the manual live browser call unless the operator explicitly approves it locally.

## Non-Goals

- no new provider integration;
- no provider routing change;
- no OpenAI model allowlist change;
- no QMD integration;
- no analytics, ads, monetization, auth, payment, SSO/BYOS, session-timer, AWS/platform, Cloudflare/DNS, or public route work;
- no browser UI feature work;
- no live calls during normal validation.

## Commit

```bash
git add scripts docs README.md outbox/0033H-local-live-output-token-cap-correction-results.md

git commit -m "scripts: update local live output token cap"

git pull --rebase origin main

git push origin main
```
