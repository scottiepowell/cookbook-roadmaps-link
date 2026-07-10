# 0029D Local Operator Access Gate

## Goal

Add a local/private operator access gate for controlled AI demo use before any invite-only, public, paid, or live provider-backed access is exposed.

This task should build on the 0029C access/metering schemas, but it must remain local/offline-friendly and must not add production auth, user accounts, paid access, public route exposure, invite emails, persistent storage, or live OpenAI calls during normal validation.

## Context

`0029C` completed the schema-only scaffold for future AI demo access and metering:

- `AiDemoSession`
- `AiAccessGrant`
- `AiProviderMeterEvent`
- `AiQualityEvent`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`
- safe serialization helpers
- docs for future operator gate, invite flow, budget enforcement, and admin reports

`0030F` completed the local Recipe Session Alpha hardening and acceptance baseline.

`0029D` should add the first runtime access-control guardrail, scoped only to local/private operator use.

## Primary Objective

Implement an opt-in local operator gate that can protect AI demo workflows when enabled:

```text
operator request
  -> local gate config check
  -> token/header verification using safe fingerprint comparison
  -> safe access decision
  -> route/workflow allowed or blocked
  -> no raw token leakage
```

The gate should be testable offline with FastAPI `TestClient` and should not require a real external auth provider.

## Non-Negotiable Boundaries

Do not add:

- production auth;
- user accounts;
- login UI;
- OAuth/OIDC;
- paid access;
- invite emails;
- payment provider integration;
- public route exposure;
- Cloudflare changes;
- database migrations;
- production storage;
- persistent user memory;
- Redis;
- Postgres;
- SQLite session persistence;
- budget enforcement runtime beyond simple gate allow/block decisions;
- admin dashboard UI;
- live OpenAI calls during normal validation;
- committed secrets, tokens, `.env` files, logs, screenshots, or generated artifacts.

The gate should default to a safe local/developer behavior that does not break existing offline validation.

## Suggested Files

Likely new files:

- `ai-api/app/ai_operator_gate.py`
- `ai-api/tests/test_ai_operator_gate.py`
- `docs/ai-local-operator-access-gate.md`
- `outbox/0029D-local-operator-access-gate-results.md`

Likely updated files:

- `ai-api/app/config.py`
- `ai-api/app/main.py` or relevant route module/dependency wiring
- `ai-api/app/ai_access_models.py` if small enum/helper additions are useful
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_demo_ui.py` if the demo displays gate status
- `scripts/demo-ai-mock.ps1`
- `docs/ai-session-metering-schema.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Add local operator gate configuration

Add configuration for a local/private operator gate.

Suggested environment variables:

```text
AI_OPERATOR_GATE_ENABLED=false
AI_OPERATOR_GATE_TOKEN_FINGERPRINT=
AI_OPERATOR_GATE_ALLOWED_WORKFLOWS=importer,dataset_ask,recipe_session,meal_plan
AI_OPERATOR_GATE_LOCAL_BYPASS=true
```

Use names that match existing config style if different.

Rules:

- default should not break existing offline tests or mock demo;
- when gate is disabled, current local behavior should remain unchanged;
- when gate is enabled, protected workflows require a valid operator token/header;
- raw tokens must never be logged or returned;
- token verification should compare fingerprints/hashes, not raw configured token values, if practical.

If a raw local token is accepted for developer convenience, immediately fingerprint it internally and never expose it in responses.

### 2. Add gate decision model

Use or extend 0029C models where appropriate.

Define a small gate decision object such as:

```text
AiOperatorGateDecision
```

Fields should include:

- `enabled`
- `allowed`
- `workflow`
- `reason`
- `status`, such as `allowed`, `blocked`, `disabled`, `misconfigured`
- `grant_type` or `session_type` when relevant
- `metadata_fingerprint` if relevant
- `safe_message`

Do not include raw token, raw header, API key, secret, local path, request body, or stack trace values.

### 3. Add gate helper/dependency

Create a reusable helper/dependency that can be called from route handlers or smoke tests.

Suggested behavior:

```text
check_operator_gate(workflow, request_headers, settings)
```

It should:

- return allowed when gate disabled;
- return blocked when gate enabled and no token/header is present;
- return blocked when token/header fingerprint does not match;
- return blocked when workflow is not allowed;
- return misconfigured when gate is enabled but no valid fingerprint/config exists;
- return allowed when gate enabled and token/header is valid;
- use constant-time comparison where practical.

Suggested header:

```text
X-AI-Operator-Token
```

A bearer-style `Authorization` header may be supported if already consistent with project conventions, but never echo it.

### 4. Add safe gate status endpoint if useful

Add a safe local status endpoint only if it helps the demo/runbook.

Suggested endpoint:

```text
GET /ai/operator-gate/status
```

It may return:

- enabled/disabled;
- configured/misconfigured;
- allowed workflows;
- safe instructions for local demo;
- no raw token/fingerprint unless fingerprint is intentionally short and safe.

Do not return raw token, full hash, env variable values, `.env` contents, or local paths.

If adding a status endpoint creates unnecessary surface area, skip the endpoint and document the helper/config instead.

### 5. Protect appropriate AI demo workflows when enabled

Wire the gate into the local AI sidecar routes in a minimal, testable way.

Candidate protected workflows:

- recipe importer;
- dataset ask/RAG;
- recipe session start/message/finalize;
- meal plan;
- live-provider smoke routes if any are exposed through API.

Do not break existing behavior when the gate is disabled.

When the gate blocks a request:

- return a safe 401/403 style response or consistent app error;
- include a helpful safe message;
- do not call provider logic;
- do not run RAG/importer generation;
- do not leak token/header/config details.

### 6. Demo UI behavior

If practical, add a small local/operator-only UI indication in `/demo`:

- gate disabled/enabled;
- whether current demo calls may require `X-AI-Operator-Token`;
- friendly blocked message if the API returns a gate block.

Do not add login UI.

Do not store tokens in browser local storage.

Do not commit example real tokens.

### 7. Mock smoke support

Update `scripts/demo-ai-mock.ps1` so normal validation still passes with the gate disabled.

Add optional coverage for the enabled gate if lightweight:

- gate enabled without token blocks protected route;
- gate enabled with wrong token blocks protected route;
- gate enabled with valid token allows protected route;
- gate disabled preserves existing mock workflow behavior.

Keep this offline/mock-only.

Do not require live provider calls.

### 8. Add deterministic tests

Add tests for:

- gate disabled allows existing local workflows;
- gate enabled with no token blocks protected workflow;
- gate enabled with wrong token blocks protected workflow;
- gate enabled with valid token allows protected workflow;
- misconfigured enabled gate blocks safely;
- disallowed workflow blocks safely;
- blocked requests do not call provider/importer/RAG generation if testable;
- gate decision safe serialization excludes raw token/header/env/path data;
- status endpoint, if added, does not leak raw token/full hash/env values;
- existing API/session/importer tests still pass with gate disabled by default.

Forbidden output strings should include:

```text
OPENAI_API_KEY
sk-
Authorization
X-AI-Operator-Token: real
.env
.tmp-ai-demo
raw_provider_prompt
raw_provider_response
C:\\Users\\
/home/
postgres://
redis://
```

### 9. Update documentation

Create:

```text
docs/ai-local-operator-access-gate.md
```

The doc should explain:

- purpose of the local operator gate;
- why it exists before invite/public/live access;
- default disabled behavior;
- how to enable it locally;
- how to provide a token safely;
- which workflows are protected when enabled;
- expected blocked/allowed behavior;
- safe status output;
- relationship to 0029C schemas;
- relationship to future 0029E budget enforcement and 0029F invite-only demo sessions;
- explicit non-goals.

Update as needed:

- `docs/ai-session-metering-schema.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

### 10. Create outbox report

Create:

```text
outbox/0029D-local-operator-access-gate-results.md
```

Include:

- gate config added;
- protected workflows;
- helper/dependency behavior;
- status endpoint if added;
- demo UI behavior if updated;
- tests added;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Local operator gate exists and is disabled by default.
- Existing offline/mock validation passes with gate disabled.
- When enabled, protected workflows require a valid local operator token/header.
- Missing, wrong, or misconfigured token states block safely.
- Valid token allows protected workflows.
- Blocked requests do not call provider generation when testable.
- No raw tokens, headers, env values, secrets, prompts, provider responses, or local paths are returned or logged.
- Docs explain how to enable and use the local gate safely.
- No production auth, user accounts, paid access, public route exposure, persistent storage, invite flow, budget enforcement runtime, or live OpenAI calls are added.

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
git add ai-api scripts docs README.md outbox/0029D-local-operator-access-gate-results.md

git commit -m "mailbox: complete task 0029D local operator access gate"

git pull --rebase origin main
git push origin main
```
