# 0030I-8 Bounded Live Importer 503 Diagnostics

## Goal

Diagnose the controlled HTTP 503 observed during `0030I-5` live importer acceptance without exposing secrets, widening scope, or claiming success prematurely.

`0030I-5` proved:

- explicit mock mode works across importer, Recipe Session, Ask My Cookbook, Dataset Ask, and Meal Planner;
- the Chromium Playwright mock suite passes and confirms normalized provider/model payloads;
- no-argument ignored `.env` startup can make the sidecar live-capable with safe readiness `openai` / `gpt-5.4-nano`;
- one authorized importer request was made with requested `openai` / `gpt-5.4-nano`;
- that request returned controlled HTTP 503 and was not retried;
- no raw provider body, prompt, key, env value, or stack trace was captured or reported.

This task is the bounded follow-up. It should determine whether the 503 is caused by local configuration, provider gating, budget/quota/model availability, route/provider wiring, request validation, timeout behavior, or another safe diagnostic category.

## Primary Objective

Add a safe, operator-approved live importer diagnostic path that can explain the controlled 503 using only redacted, non-secret evidence.

If valid live config and explicit approval are present, perform at most one bounded live importer diagnostic call unless the operator explicitly approves an additional retry. Do not broaden into multi-workflow live testing.

## Required Work

### 1. Inspect current live importer path

Inspect:

```text
scripts/start-ai-demo-local.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
ai-api/app/config.py
ai-api/app/ai_mode_routing.py
ai-api/app/routes/ai.py
ai-api/app/providers.py
ai-api/app/provider_policy.py
ai-api/app/provider_budget.py
ai-api/app/static/demo.js
outbox/0030I-5-local-live-mode-product-acceptance-and-mode-audit-results.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
```

Confirm where `POST /ai/import-recipe` can return controlled HTTP 503 when requested mode/model are `openai` / `gpt-5.4-nano`.

Classify each 503 source into a safe category such as:

```text
live_not_enabled
missing_api_key
provider_globally_disabled
provider_calls_disabled
budget_not_configured
budget_exceeded
model_not_allowed
provider_account_or_quota_unavailable
provider_timeout
provider_http_error_redacted
request_validation_error
unexpected_safe_internal_block
```

Use existing category names if they already exist. Do not invent incompatible response schemas unless a small additive field is needed.

### 2. Preserve safety and redaction

Diagnostics may expose only safe facts:

- requested provider/mode;
- requested model;
- effective provider;
- effective model;
- workflow name;
- HTTP status;
- safe error category;
- safe user guidance;
- whether key is present as `redacted-present` or `missing`;
- budget setting validity as present/invalid/exceeded, without sensitive details;
- timeout setting validity;
- whether live opt-in is enabled.

Diagnostics must not expose:

- API key;
- API key prefix/suffix;
- `.env` contents;
- raw prompt;
- raw provider request;
- raw provider response;
- provider account IDs;
- provider headers;
- raw provider error body;
- local filesystem paths;
- stack traces;
- raw dataset contents.

### 3. Add a bounded diagnostic script

Create if useful:

```text
scripts/diagnose-live-importer.ps1
```

The script should:

- require explicit operator approval to make a live call, for example `-ApproveLiveCall`;
- load ignored `.env` through the existing env helper if `-EnvFile` or default `.env` loading is supported;
- verify live config before any provider call;
- print a safe preflight summary;
- call only the importer workflow;
- use a tiny, deterministic input recipe fixture;
- enforce `gpt-5.4-nano` only;
- enforce budget/token/time limits;
- return a concise pass/fail/blocked summary;
- stop after one live call unless an explicit future retry switch is designed;
- never print secrets.

Suggested operator flow:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
# second terminal, only after verifying startup says openai / gpt-5.4-nano
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall
```

If the sidecar is not live-capable, the script should stop before any provider call and explain the safe missing category.

### 4. Improve safe 503 observability if needed

If the route currently collapses multiple causes into a generic 503, add a safe diagnostic field to the importer response/error envelope and/or logs.

Examples:

```json
{
  "provider_mode": "openai",
  "ai_model": "gpt-5.4-nano",
  "effective_provider": "openai",
  "effective_model": "gpt-5.4-nano",
  "status": "unavailable",
  "safe_unavailable_category": "provider_timeout",
  "safe_guidance": "Live OpenAI was enabled but the bounded provider call did not complete within the configured timeout. No retry was attempted."
}
```

Keep this additive and backwards-compatible where possible.

Do not expose raw provider internals.

### 5. Add deterministic tests

Add tests for:

- live importer diagnostics require explicit approval before a live call;
- preflight stops safely when live config is missing;
- preflight uses only `gpt-5.4-nano`;
- unsupported models are rejected safely;
- controlled 503 responses include a safe category/guidance when possible;
- no secrets, raw prompts, raw provider responses, env values, local paths, or stack traces are emitted;
- normal mock/offline validation still passes;
- Playwright UI QA remains mock-only and does not run against live sidecars.

Use fake env fixtures and mock provider stubs for automated tests. Do not make live OpenAI calls during tests or normal validation.

### 6. Optional manual live diagnostic

If the operator's ignored `.env` is valid and approval is explicitly supplied, run one live importer diagnostic call.

Record only safe evidence:

- preflight category;
- requested provider/model;
- effective provider/model;
- status;
- safe unavailable category or success status;
- whether budget/token/time limits were enforced;
- whether no retry occurred.

If live diagnostics cannot run safely, skip and document why.

### 7. Update docs

Update:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
docs/local-cookbook-ai-product-integration.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Document:

- why `0030I-5` did not claim successful live importer acceptance;
- how to run bounded live importer diagnostics;
- required `.env` keys;
- explicit approval requirement;
- one-call/no-retry default;
- safe diagnostic categories;
- what must never be printed;
- Playwright remains mock-only;
- normal validation remains offline/mock-only.

### 8. Add outbox report

Create:

```text
outbox/0030I-8-bounded-live-importer-503-diagnostics-results.md
```

The outbox must summarize:

- `0030I-5` live importer 503 baseline;
- diagnostic script or route/log improvements added;
- safe diagnostic categories;
- tests added;
- validation results;
- whether a manual live diagnostic was run;
- if run, safe result summary only;
- if skipped, safe skip reason;
- explicit non-goals;
- whether a follow-up live acceptance task is now ready.

## Acceptance Criteria

- The controlled live importer 503 has a bounded diagnostic path.
- Diagnostics require explicit live-call approval before contacting the provider.
- Diagnostics classify the failure into a safe category when possible.
- The only allowed live model remains `gpt-5.4-nano`.
- Diagnostics stop safely when live config is missing or invalid.
- Diagnostics perform at most one live importer call by default.
- No secrets, key fragments, raw provider data, raw prompts, env values, local paths, stack traces, screenshots, traces, videos, or raw dataset contents are committed or printed.
- Normal validation remains offline/mock-only.
- Playwright UI QA remains mock-only.
- No AWS/platform work, production auth, payment, public route exposure, Cloudflare/DNS change, secondary-provider runtime, vector DB, embeddings, upstream UI rewrite, browser automation expansion, raw dataset commit, persistent index, or disk cache is added.

## Validation

Run normal validation without live calls:

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
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

If explicitly approved and valid ignored live config is present, run the bounded diagnostic once:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall
```

The live diagnostic must not be required for normal validation.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-8-bounded-live-importer-503-diagnostics-results.md

git commit -m "mailbox: add task 0030I-8 bounded live importer diagnostics"

git pull --rebase origin main

git push origin main
```
