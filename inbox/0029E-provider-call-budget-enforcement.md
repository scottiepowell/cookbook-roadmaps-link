# 0029E Provider Call Budget Enforcement

## Goal

Centralize provider-call budget enforcement for AI demo workflows before any invite-only, public, paid, or broader live provider access is exposed.

This task should build on the 0029C access/metering schemas and the 0029D local operator gate. It should add deterministic budget-decision logic and wire it around provider-backed workflows so live/provider calls can be blocked safely when limits are exhausted or provider access is disabled.

Normal validation must remain offline/mock-only and should not require live OpenAI calls.

## Context

`0029C` added schema-only models for future access and metering:

- `AiDemoSession`
- `AiAccessGrant`
- `AiProviderMeterEvent`
- `AiQualityEvent`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`
- safe serialization helpers

`0029D` added the first local/private operator access gate:

- disabled by default;
- safe fingerprint token/header verification when enabled;
- protected importer, dataset ask, recipe-session, and meal-plan workflows;
- no production auth, persistent storage, public exposure, budget enforcement runtime, or live calls during normal validation.

`0029E` should add the next guardrail: centralized provider-call budget enforcement.

## Primary Objective

Implement a provider budget guard that can decide whether a provider-backed call should proceed:

```text
workflow request
  -> operator gate decision, if enabled
  -> provider budget config check
  -> provider enabled/disabled check
  -> call count/token/cost budget decision
  -> allow provider call OR block safely before provider invocation
  -> produce safe meter event / budget snapshot
```

The budget guard should be deterministic, testable offline, and safe to serialize.

## Non-Negotiable Boundaries

Do not add:

- production storage;
- database migrations;
- user accounts;
- production auth;
- paid access;
- payment provider integration;
- invite emails;
- public route exposure;
- Cloudflare changes;
- Redis;
- Postgres;
- SQLite persistence for budgets;
- persistent user memory;
- admin dashboard UI;
- live OpenAI calls during normal validation;
- committed secrets, tokens, `.env` files, logs, screenshots, or generated artifacts.

Do not require a real OpenAI API key for tests.

Mock/offline workflows should continue to work by default.

## Suggested Files

Likely new files:

- `ai-api/app/ai_budget_guard.py`
- `ai-api/tests/test_ai_budget_guard.py`
- `docs/ai-provider-budget-enforcement.md`
- `outbox/0029E-provider-call-budget-enforcement-results.md`

Likely updated files:

- `ai-api/app/config.py`
- `ai-api/app/ai_access_models.py`
- `ai-api/app/openai_provider.py` or existing provider-call wrapper module
- `ai-api/app/importer.py` or provider invocation service if applicable
- `ai-api/app/main.py`
- `ai-api/app/recipe_session_routes.py` if session generation needs budget metadata
- `scripts/demo-ai-mock.ps1`
- `scripts/demo-ai-live-smoke.ps1`
- `scripts/run-openai-demo-evals.ps1`
- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Add provider budget configuration

Add centralized budget-related settings.

Suggested environment variables:

```text
AI_PROVIDER_CALLS_ENABLED=true
AI_PROVIDER_GLOBAL_DISABLE=false
AI_PROVIDER_MAX_CALLS_PER_DEMO_SESSION=10
AI_PROVIDER_MAX_INPUT_TOKENS_PER_CALL=12000
AI_PROVIDER_MAX_OUTPUT_TOKENS_PER_CALL=1200
AI_PROVIDER_MAX_TOTAL_TOKENS_PER_CALL=14000
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_SESSION=1.00
AI_PROVIDER_MAX_ESTIMATED_COST_USD_PER_CALL=0.25
AI_PROVIDER_BUDGET_MODE=enforce
```

Use names that match existing config style if different.

Rules:

- defaults must not break existing mock/offline validation;
- mock provider calls should be treated as zero-cost and normally allowed;
- live provider calls should be blockable by global disable, call count, token caps, or estimated-cost caps;
- invalid budget config should fail closed for live provider calls and return a safe message;
- do not expose raw env values or secrets in responses.

### 2. Add budget decision model

Use or extend 0029C models where appropriate.

Define a small decision model such as:

```text
AiProviderBudgetDecision
```

Fields should include:

- `allowed`
- `status`, such as `allowed`, `blocked`, `disabled`, `exhausted`, `misconfigured`, `skipped`
- `workflow`
- `provider`
- `model`
- `reason`
- `safe_message`
- `provider_call_count`
- `max_provider_calls`
- `estimated_cost_usd`
- `max_estimated_cost_usd`
- `estimated_input_tokens`
- `estimated_output_tokens`
- `max_input_tokens`
- `max_output_tokens`
- `budget_snapshot`
- `meter_event`

Do not include raw prompts, raw provider responses, API keys, authorization headers, env values, local absolute paths, request bodies, or stack traces.

### 3. Add budget guard helper

Create a reusable helper/service such as:

```text
check_provider_budget(workflow, provider, model, estimated_input_tokens, requested_output_tokens, session_state, settings)
```

It should:

- allow mock/offline provider calls by default;
- block when provider calls are globally disabled;
- block live provider calls when `AI_PROVIDER_CALLS_ENABLED=false` or equivalent;
- block when estimated input tokens exceed cap;
- block when requested output tokens exceed cap;
- block when total estimated tokens exceed cap;
- block when session provider-call count is exhausted;
- block when estimated session cost is exhausted;
- block when estimated per-call cost exceeds cap;
- produce a safe `AiBudgetSnapshot`;
- produce a safe `AiProviderMeterEvent` with status `allowed`, `blocked`, `skipped`, or `failed`;
- never call the provider when blocked.

If no session object exists yet, support a safe anonymous/local budget context for current demo scripts.

### 4. Add lightweight process-local budget tracker if needed

If current workflows do not have a durable session concept for all provider calls, add a small process-local tracker for demo validation only.

Requirements:

- bounded;
- process-local only;
- clear/reset helper for tests;
- no disk persistence;
- no Redis/Postgres/SQLite;
- no long-term user memory;
- safe serialization only.

Suggested class:

```text
AiProviderBudgetTracker
```

Methods may include:

- `record_allowed_call(session_id, meter_event)`
- `record_blocked_call(session_id, meter_event)`
- `snapshot(session_id, grant_id=None)`
- `reset()`

Keep this minimal. Do not build an admin report UI.

### 5. Wire budget enforcement around provider calls

Wrap the actual live provider invocation path so blocked calls stop before network/provider invocation.

Likely targets:

- OpenAI importer provider call;
- dataset ask provider-backed path if applicable;
- recipe-session generation when it uses provider-backed importer logic;
- meal-plan provider-backed path if applicable;
- live smoke/eval wrappers if they call provider routes.

Do not duplicate provider logic.

Do not weaken existing mock provider behavior.

If a route is fully mock/offline and does not call a live provider, budget decision can be `skipped` or zero-cost `allowed`, but document the behavior.

### 6. Return safe blocked responses

When a request is blocked by budget enforcement:

- return a consistent safe response or HTTP error;
- include `response_state` / `status` where applicable;
- include safe budget reason;
- include safe budget snapshot if useful;
- do not include prompt, provider raw response, API key, env value, local path, or stack trace;
- do not imply the provider was called.

Suggested safe messages:

```text
Provider calls are disabled for this local demo.
Provider call budget exhausted for this demo session.
Requested output token limit exceeds the configured demo cap.
Estimated provider cost exceeds the configured demo budget.
```

### 7. Meter event behavior

Use `AiProviderMeterEvent` from 0029C to represent allowed/blocked/skipped provider call decisions.

For blocked calls:

- status should be `blocked`;
- reason should be safe and deterministic;
- token/cost estimates may be included when safe;
- no raw prompt/response should be stored.

For mock calls:

- status may be `skipped` or `allowed` with zero cost;
- provider should be `mock`;
- cost should be zero or omitted consistently.

For live allowed calls:

- record pre-call estimate where possible;
- if post-call usage data is available, include safe usage summary;
- do not require live calls in normal validation.

### 8. Add deterministic tests

Add tests for:

- mock provider allowed with zero cost;
- global provider disable blocks live provider call;
- provider calls disabled setting blocks live provider call;
- input token cap blocks safely;
- output token cap blocks safely;
- total token cap blocks safely;
- per-call cost cap blocks safely;
- per-session call count cap blocks safely;
- per-session estimated cost cap blocks safely;
- invalid/misconfigured budget config blocks live provider calls safely;
- allowed live-call decision creates safe meter event without making a real network call;
- blocked decision does not invoke provider when testable;
- budget tracker reset works;
- safe serialization excludes forbidden strings.

Forbidden output strings should include:

```text
OPENAI_API_KEY
sk-
Authorization
X-AI-Operator-Token
.env
.tmp-ai-demo
raw_provider_prompt
raw_provider_response
C:\\Users\\
/home/
postgres://
redis://
```

### 9. Add route/provider integration tests

Add route-level tests where practical:

- importer route blocked before provider when live provider is selected and global disable is true;
- recipe-session route blocked before provider when live provider is selected and budget exhausted;
- gate disabled + budget default still allows mock importer/session workflows;
- budget block response is safe;
- existing 0030 session API tests still pass with defaults.

Do not require a real OpenAI key.

### 10. Update scripts

Update live smoke/eval scripts if needed so they respect the centralized budget settings.

Expected behavior:

- without live opt-in, wrappers skip as before;
- with live opt-in but provider calls disabled, wrappers fail/skip safely with a clear budget message;
- with live opt-in and tight budget, wrappers stop before exceeding budget;
- mock smoke remains stable and offline.

Do not run live calls during normal validation.

### 11. Add documentation

Create:

```text
docs/ai-provider-budget-enforcement.md
```

The doc should explain:

- purpose of provider budget enforcement;
- relationship to 0029C schemas;
- relationship to 0029D local operator gate;
- default mock/offline behavior;
- configuration knobs;
- budget decision flow;
- blocked response behavior;
- meter event behavior;
- how live smoke scripts should use budgets;
- explicit non-goals.

Update:

- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

### 12. Create outbox report

Create:

```text
outbox/0029E-provider-call-budget-enforcement-results.md
```

Include:

- budget config added;
- decision model/helper behavior;
- tracker behavior if added;
- protected provider-call paths;
- blocked response behavior;
- meter event behavior;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Provider budget guard exists and is centralized.
- Mock/offline validation passes unchanged by default.
- Live provider calls can be blocked before invocation by global disable, provider-call disable, token caps, call-count caps, and estimated-cost caps.
- Budget decisions produce safe snapshots and meter events.
- Blocked responses are safe and do not leak prompts, provider responses, tokens, env values, or local paths.
- Tests prove blocked decisions do not invoke provider where practical.
- Live smoke/eval wrappers respect centralized budget settings while still skipping without opt-in.
- Existing importer, RAG, recipe-session, operator-gate, and eval tests still pass.
- No production storage, database migrations, auth, paid access, public route exposure, payment integration, invite flow, admin dashboard, persistent memory, Redis/Postgres/SQLite persistence, or live OpenAI calls during normal validation are added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest is run and fails because of the known local `pytest-of-scott` temp ACL issue or because live OpenAI environment variables are set, document that separately and rely on Git Bash validation if it passes.

Before committing, confirm:

- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no raw tokens;
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage;
- no payment or invite secrets.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0029E-provider-call-budget-enforcement-results.md

git commit -m "mailbox: complete task 0029E provider call budget enforcement"

git pull --rebase origin main
git push origin main
```
