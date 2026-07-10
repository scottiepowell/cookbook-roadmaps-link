# 0029F Invite-Only Demo Session Flow

## Goal

Add a local/private invite-only demo session flow on top of the completed access and budget guardrails without enabling public access, paid access, production auth, production storage, invite emails, or live OpenAI calls during normal validation.

This task should create a controlled demo-session runtime that can issue, validate, revoke, and expire short-lived invite grants for AI demo workflows while remaining safe, deterministic, and offline-testable.

## Context

`0029C` added schema-only access and metering models:

- `AiDemoSession`
- `AiAccessGrant`
- `AiProviderMeterEvent`
- `AiQualityEvent`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`
- safe serialization helpers

`0029D` added the local/private operator access gate:

- disabled by default;
- safe token fingerprint validation when enabled;
- protected importer, dataset ask, recipe-session, and meal-plan workflows;
- no production auth or public access.

`0029E` added centralized provider-call budget enforcement:

- mock/local provider calls remain zero-cost and allowed by default;
- live provider calls can be blocked before invocation by disable flags, token caps, call-count caps, and estimated-cost caps;
- safe meter events and budget snapshots are produced.

`0029F` should add the next layer: local/private invite-only demo sessions.

## Primary Objective

Implement an invite-only demo session flow:

```text
operator creates invite grant
  -> raw invite token/code is generated or accepted locally
  -> only safe fingerprint is stored
  -> invite can be redeemed into a short-lived demo session
  -> demo session can call protected AI workflows within allowed workflow/budget limits
  -> invite/session can expire or be revoked
  -> safe status/audit/meter views are available
```

This is still a local/private demo capability, not public production access.

## Non-Negotiable Boundaries

Do not add:

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
- SQLite persistence for invites/sessions;
- persistent user memory;
- admin dashboard UI;
- live OpenAI calls during normal validation;
- committed invite tokens, secrets, `.env` files, logs, screenshots, or generated artifacts.

Everything must remain local/private and process-local unless explicitly documented as future work.

## Suggested Files

Likely new files:

- `ai-api/app/ai_invite_sessions.py`
- `ai-api/tests/test_ai_invite_sessions.py`
- `docs/ai-invite-only-demo-session-flow.md`
- `outbox/0029F-invite-only-demo-session-flow-results.md`

Likely updated files:

- `ai-api/app/ai_access_models.py`
- `ai-api/app/ai_operator_gate.py`
- `ai-api/app/ai_budget_guard.py`
- `ai-api/app/config.py`
- `ai-api/app/main.py`
- `ai-api/app/recipe_session_routes.py`
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_ai_operator_gate.py`
- `ai-api/tests/test_ai_budget_guard.py`
- `ai-api/tests/test_demo_ui.py`
- `scripts/demo-ai-mock.ps1`
- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Add invite/session configuration

Add local invite-session settings.

Suggested environment variables:

```text
AI_INVITE_SESSIONS_ENABLED=false
AI_INVITE_SESSION_TTL_SECONDS=1800
AI_INVITE_GRANT_TTL_SECONDS=3600
AI_INVITE_MAX_SESSIONS_PER_GRANT=1
AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS=5
AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD=0.50
AI_INVITE_ALLOWED_WORKFLOWS=importer,dataset_ask,recipe_session,meal_plan
AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED=true
```

Use names consistent with existing config style if different.

Rules:

- defaults must not break existing offline/mock validation;
- invite-session flow must be disabled by default unless tests opt in;
- process-local state only;
- no invite tokens committed or logged;
- raw invite token/code may be returned only once at local operator creation time if implemented, and must not be stored raw;
- after creation, only fingerprints/hashes should be stored or displayed.

### 2. Add process-local invite/session store

Create a bounded process-local store, suggested class:

```text
AiInviteSessionStore
```

It should support:

- create invite grant;
- redeem invite token/code into a demo session;
- get safe grant/session status;
- revoke grant;
- revoke session;
- expire grants/sessions by time;
- clear/reset for tests.

Requirements:

- bounded max grants/sessions;
- TTL expiration;
- no disk persistence;
- no Redis/Postgres/SQLite;
- no long-term user memory;
- no raw token storage;
- safe serialization only.

### 3. Reuse 0029C models

Use or extend existing models where appropriate:

- `AiAccessGrant`
- `AiDemoSession`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`

Add only small enums/helpers if needed.

Grant/session statuses should cover:

```text
active
expired
revoked
used
completed
```

### 4. Add invite token fingerprinting

Implement safe invite token handling.

Requirements:

- generate random local invite token/code when creating a grant, or accept a local operator-provided token only in tests/dev;
- store only a fingerprint/hash;
- compare with constant-time comparison where practical;
- support token redemption exactly once by default;
- never return token after the initial creation response;
- never include raw token in logs, status endpoints, safe views, audit events, docs examples, or test snapshots.

### 5. Add local invite/session API endpoints

Add local/private endpoints only.

Suggested endpoints:

```text
POST /ai/invite/grants
POST /ai/invite/redeem
GET /ai/invite/grants/{grant_id}
GET /ai/invite/sessions/{session_id}
POST /ai/invite/grants/{grant_id}/revoke
POST /ai/invite/sessions/{session_id}/revoke
GET /ai/invite/status
```

These endpoints should be disabled unless `AI_INVITE_SESSIONS_ENABLED=true` or equivalent.

Creation/revocation endpoints should require the local operator gate when gate is enabled, or should be documented as local-only if gate is disabled by default.

Do not add public auth or login UI.

### 6. Integrate invite sessions with operator gate and budget guard

Protected AI workflows should be able to accept an invite session token/header in addition to the local operator token when invite sessions are enabled.

Suggested header:

```text
X-AI-Demo-Session-Token
```

Expected behavior:

- valid local operator token still works when operator gate is enabled;
- valid invite session token can allow workflows listed in the grant/session allowed workflows;
- missing/wrong/expired/revoked session token blocks safely;
- disallowed workflow blocks safely;
- budget guard uses the demo session ID and grant limits where practical;
- provider-call counts and estimated cost can be associated with the invite session in process-local budget tracker.

Keep integration minimal and testable.

### 7. Add safe responses and audit events

Endpoint responses should include safe views only:

- grant/session IDs;
- statuses;
- timestamps;
- TTL/expiry;
- allowed workflows;
- max sessions/calls/cost;
- request/provider counts if available;
- safe metadata fingerprints;
- safe audit event summaries if useful.

Responses must not include:

- raw invite token after creation;
- raw operator token;
- raw session token after redemption if avoidable;
- API keys;
- Authorization header values;
- `.env` values;
- local absolute paths;
- raw prompts;
- raw provider responses;
- stack traces.

If an endpoint returns a raw token once, clearly mark it one-time and test that subsequent status calls do not expose it.

### 8. Demo UI indication if lightweight

If practical, add a small local/operator-only UI section or status card for invite demo sessions.

Minimal useful UI:

- show invite feature enabled/disabled;
- show safe explanation of session token header;
- optionally allow local operator to create/redeem invite in mock demo mode.

Do not add login UI.

Do not store invite/session tokens in local storage.

Do not build an admin dashboard.

If UI would be too much for this slice, document the endpoints/runbook instead.

### 9. Add deterministic tests

Add tests for:

- invite feature disabled returns safe disabled response or 404/403;
- create invite grant with local operator context;
- creation returns raw invite token only once if implemented;
- grant safe status does not expose raw token;
- redeem valid invite creates short-lived demo session;
- redeem wrong token blocks safely;
- redeem expired grant blocks safely;
- redeem revoked grant blocks safely;
- single-use grant cannot be redeemed twice by default;
- session safe status does not expose raw token;
- revoked session blocks protected workflow;
- expired session blocks protected workflow;
- disallowed workflow blocks protected workflow;
- valid invite session token allows an allowed protected workflow in mock mode;
- budget tracker associates calls with the invite session where practical;
- safe serialization excludes forbidden strings.

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

### 10. Update scripts

Update `scripts/demo-ai-mock.ps1` if useful so normal validation still pins invite sessions disabled by default.

Optionally add a local offline invite smoke subsection when explicitly enabled by script-local env vars:

- create invite grant;
- redeem invite;
- call one protected mock route with session token;
- revoke session;
- confirm revoked session blocks.

Keep default mock smoke stable and offline.

### 11. Documentation

Create:

```text
docs/ai-invite-only-demo-session-flow.md
```

Document:

- purpose of invite-only demo sessions;
- relationship to 0029C schemas;
- relationship to 0029D local operator gate;
- relationship to 0029E provider budget guard;
- configuration;
- endpoint flow;
- token/fingerprint safety;
- TTL/revocation behavior;
- allowed workflows;
- budget/session interaction;
- local testing/runbook examples;
- explicit non-goals.

Update:

- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

### 12. Create outbox report

Create:

```text
outbox/0029F-invite-only-demo-session-flow-results.md
```

Include:

- invite/session store behavior;
- endpoints added;
- token/fingerprint safety;
- operator gate integration;
- budget guard integration;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Local/private invite-session flow exists and is disabled by default.
- Invite grants can be created, redeemed, expired, revoked, and inspected safely when enabled.
- Raw invite/session tokens are never stored raw and are only exposed once if needed.
- Safe status responses do not expose tokens, secrets, prompts, provider responses, env values, or local paths.
- Protected workflows can be allowed by a valid invite session token for allowed workflows when invite sessions are enabled.
- Missing, wrong, expired, revoked, or workflow-disallowed session tokens block safely.
- Budget tracker can associate provider-call decisions with invite/demo session IDs where practical.
- Default mock/offline validation remains stable.
- No production auth, user accounts, paid access, payment integration, public route exposure, invite emails, production storage, persistent memory, Redis/Postgres/SQLite persistence, admin dashboard, or live OpenAI calls during normal validation are added.

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
git add ai-api scripts docs README.md outbox/0029F-invite-only-demo-session-flow-results.md

git commit -m "mailbox: complete task 0029F invite-only demo session flow"

git pull --rebase origin main
git push origin main
```
