# 0029G Admin Usage Report Prototype

## Goal

Prototype a local/operator-only AI usage report that summarizes invite sessions, provider-call budget decisions, meter events, quality/eval events, and safety warnings without adding a production admin dashboard, production storage, public access, paid access, or live OpenAI calls during normal validation.

This task should build on the completed 0029C/0029D/0029E/0029F guardrail stack and produce a safe reporting surface for local demo operations.

## Context

`0029C` added access and metering models:

- `AiDemoSession`
- `AiAccessGrant`
- `AiProviderMeterEvent`
- `AiQualityEvent`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`
- safe serialization helpers

`0029D` added the local/private operator access gate:

- disabled by default;
- safe fingerprint token/header verification when enabled;
- protected importer, dataset ask, recipe-session, and meal-plan workflows.

`0029E` added centralized provider-call budget enforcement:

- process-local budget tracker;
- safe budget decisions;
- safe meter events and budget snapshots;
- live calls can be blocked before invocation by disable flags, token caps, call-count caps, and estimated-cost caps.

`0029F` added local/private invite-only demo sessions:

- disabled by default;
- bounded process-local invite grant/session store;
- safe invite/session token fingerprinting;
- single-use invite redemption;
- revocation and expiry;
- integration with the operator gate and budget guard.

`0029G` should add a local reporting prototype so an operator can understand active sessions, budget state, provider-call decisions, and quality/safety status before any public route exposure review.

## Primary Objective

Create a local/operator usage report that can answer:

```text
What demo sessions/grants are active?
Which sessions are expired, revoked, used, or completed?
How many provider calls were allowed, blocked, skipped, or failed?
What is the estimated spend and remaining budget?
Which workflows are being used?
Are there quality/eval failures or safety warnings?
Are any thresholds close to exhaustion?
```

The report should be generated from safe process-local state and model snapshots only.

## Non-Negotiable Boundaries

Do not add:

- production admin dashboard;
- production auth;
- user accounts;
- login UI;
- OAuth/OIDC;
- paid access;
- payment provider integration;
- public checkout;
- public route exposure;
- Cloudflare changes;
- invite emails;
- database migrations;
- production storage;
- Redis;
- Postgres;
- SQLite persistence;
- persistent user memory;
- live OpenAI calls during normal validation;
- committed invite/session tokens, secrets, `.env` files, logs, screenshots, or generated artifacts.

Everything must remain local/private, process-local, and offline-testable.

## Suggested Files

Likely new files:

- `ai-api/app/ai_usage_report.py`
- `ai-api/tests/test_ai_usage_report.py`
- `docs/ai-admin-usage-report-prototype.md`
- `outbox/0029G-admin-usage-report-prototype-results.md`

Likely updated files:

- `ai-api/app/ai_access_models.py`
- `ai-api/app/ai_budget_guard.py`
- `ai-api/app/ai_invite_sessions.py`
- `ai-api/app/ai_operator_gate.py` if needed for operator-only protection
- `ai-api/app/config.py`
- `ai-api/app/main.py`
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_ai_budget_guard.py`
- `ai-api/tests/test_ai_invite_sessions.py`
- `ai-api/tests/test_demo_ui.py`
- `scripts/demo-ai-mock.ps1`
- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Add usage report models/helpers

Create:

```text
ai-api/app/ai_usage_report.py
```

Define a report builder that can assemble safe operator report data from existing process-local stores/trackers.

Suggested report model:

```text
AiUsageReport
```

Suggested sections:

- `summary`
- `sessions`
- `grants`
- `provider_meter_events`
- `budget_snapshots`
- `quality_events`
- `audit_events`
- `warnings`
- `thresholds`
- `generated_at`

If the project prefers plain dicts over Pydantic models for this layer, keep the structure deterministic and safe.

### 2. Define usage summary

Add a usage summary object or dict with fields such as:

- `active_session_count`
- `expired_session_count`
- `revoked_session_count`
- `completed_session_count`
- `active_grant_count`
- `used_grant_count`
- `revoked_grant_count`
- `expired_grant_count`
- `provider_calls_allowed`
- `provider_calls_blocked`
- `provider_calls_skipped`
- `provider_calls_failed`
- `estimated_cost_usd_total`
- `remaining_estimated_cost_usd_total`
- `quality_pass_count`
- `quality_warning_count`
- `quality_failure_count`
- `threshold_warning_count`

Keep defaults stable when no sessions/events exist.

### 3. Report provider budget and meter state

Use 0029E budget tracker data where available.

Report should summarize:

- total allowed calls;
- total blocked calls;
- total skipped mock/local calls;
- total failed decisions;
- estimated cost total;
- remaining budget by session/grant where known;
- sessions near call-count exhaustion;
- sessions near estimated-cost exhaustion;
- safe meter event rows.

Do not expose raw prompts, raw provider responses, request bodies, provider API keys, or env values.

### 4. Report invite grants and sessions

Use 0029F invite store safe views.

Report should summarize:

- active grants;
- used grants;
- revoked grants;
- expired grants;
- active sessions;
- expired sessions;
- revoked sessions;
- completed sessions if supported;
- allowed workflows;
- expiry timestamps;
- safe metadata fingerprints.

Do not expose raw invite tokens or session tokens.

### 5. Add quality/eval event hooks or placeholder support

If current runtime does not yet persist `AiQualityEvent` values, add a minimal process-local collector or report section that can accept safe quality events in tests.

Requirements:

- bounded;
- process-local only;
- no disk persistence;
- clear/reset helper for tests;
- safe serialization only;
- no raw prompts/responses.

This can be simple and future-facing.

### 6. Add threshold warnings

Add deterministic warning logic for near-limit conditions.

Suggested thresholds:

- session call budget >= 80% used;
- session estimated-cost budget >= 80% used;
- any blocked provider decision occurred;
- any quality failure occurred;
- any active invite/session expires soon;
- operator gate disabled while invite sessions enabled;
- invite sessions enabled while budget guard disabled or globally misconfigured.

Warnings should be safe strings or structured warning objects with:

- `severity`, such as `info`, `warning`, `critical`;
- `code`;
- `message`;
- `session_id` or `grant_id` when safe;
- no secrets or raw tokens.

### 7. Add local operator report endpoint

Add a local/operator-only endpoint, suggested:

```text
GET /ai/admin/usage-report
```

Requirements:

- protected by local operator gate when gate is enabled;
- local/private only;
- safe response only;
- no raw tokens, env values, prompts, provider responses, local paths, or stack traces;
- feature can be disabled or hidden by default if that matches project style.

If adding an endpoint is too much for this slice, expose only a helper and docs. Prefer adding the endpoint if it can be protected and tested safely.

### 8. Add optional demo UI status card

If lightweight, add a small operator-only card in `/demo` that shows:

- report feature status;
- active session count;
- provider calls allowed/blocked/skipped;
- estimated cost total;
- threshold warning count;
- link or button to fetch local usage report.

Do not build a full admin dashboard.

Do not show raw tokens or raw event payloads.

Do not store tokens in browser local storage.

If UI would be too much, document the endpoint/runbook instead.

### 9. Add deterministic tests

Add tests for:

- empty report returns stable zero/default summary;
- active/expired/revoked invite grants and sessions are counted correctly;
- provider meter events are counted by status;
- estimated cost totals are calculated correctly;
- remaining budget values are summarized correctly;
- threshold warnings fire at or above 80% call/cost use;
- blocked provider decisions create warnings;
- quality failures create warnings;
- safe report serialization excludes forbidden strings;
- usage report endpoint is protected by the operator gate when enabled;
- usage report endpoint does not expose raw invite/session tokens;
- optional demo UI status card, if added, does not contain forbidden text.

Forbidden output strings should include:

```text
OPENAI_API_KEY
sk-
Authorization
X-AI-Operator-Token
X-AI-Demo-Session-Token: real
.env
.tmp-ai-demo
raw_provider_prompt
raw_provider_response
C:\\Users\\
/home/
postgres://
redis://
```

### 10. Update mock smoke if useful

Update `scripts/demo-ai-mock.ps1` if useful to verify the usage-report endpoint or helper in the default offline path.

Default behavior should remain stable:

- invite sessions disabled unless optional path is explicitly enabled;
- operator gate disabled or pinned as needed;
- provider calls mock/offline;
- report endpoint/helper returns safe empty or mock-populated summary;
- no live provider calls.

### 11. Documentation

Create:

```text
docs/ai-admin-usage-report-prototype.md
```

Document:

- purpose of the usage report;
- relationship to 0029C schemas;
- relationship to 0029D operator gate;
- relationship to 0029E budget guard;
- relationship to 0029F invite sessions;
- report sections;
- endpoint/helper behavior;
- threshold warning logic;
- safe serialization rules;
- local demo/runbook examples;
- explicit non-goals.

Update:

- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

### 12. Create outbox report

Create:

```text
outbox/0029G-admin-usage-report-prototype-results.md
```

Include:

- report helper/model behavior;
- endpoint behavior if added;
- usage summary fields;
- budget/meter summaries;
- invite/session summaries;
- quality event support;
- threshold warnings;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Local/operator usage report prototype exists.
- Report summarizes invite grants, invite sessions, provider meter events, budget snapshots, quality events, and threshold warnings where data exists.
- Empty/default report is stable and safe.
- Threshold warnings identify near-exhaustion and blocked/failed conditions.
- Usage report endpoint/helper is protected by operator gate when enabled.
- Report does not expose raw invite/session tokens, operator tokens, API keys, env values, raw prompts, raw provider responses, local paths, request bodies, or stack traces.
- Default mock/offline validation remains stable.
- No production admin dashboard, production auth, user accounts, paid access, payment integration, public route exposure, invite emails, production storage, persistent memory, Redis/Postgres/SQLite persistence, or live OpenAI calls during normal validation are added.

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

- no raw invite/session tokens;
- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage;
- no payment secrets.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0029G-admin-usage-report-prototype-results.md

git commit -m "mailbox: complete task 0029G admin usage report prototype"

git pull --rebase origin main
git push origin main
```
