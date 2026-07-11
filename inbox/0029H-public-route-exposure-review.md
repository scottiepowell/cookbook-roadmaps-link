# 0029H Public Route Exposure Review

## Goal

Perform a public route exposure review for the AI sidecar before any public live provider-backed AI access is exposed.

This task should produce a concrete route inventory, exposure decision matrix, Cloudflare/reverse-proxy/CORS review, safety checklist, and go/no-go recommendations. It should not expose new public routes, change Cloudflare, enable production auth, add paid access, or run live OpenAI during normal validation.

## Context

The 0029 guardrail track now includes:

- `0029C`: access/metering schemas and safe serialization models;
- `0029D`: local/private operator gate;
- `0029E`: centralized provider-call budget guard;
- `0029F`: local/private invite-only demo session flow;
- `0029G`: local/operator usage-report prototype.

The AI sidecar also has the completed 0030 recipe-session alpha:

- local alpha recipe-session API endpoints;
- Recipe Session Alpha demo UI;
- offline eval harness;
- alpha hardening and acceptance runbook.

`0029H` is a review and readiness task. It should answer:

```text
Which AI routes exist?
Which routes are local-only?
Which routes could ever be public?
What must be gated before public access?
What Cloudflare/reverse-proxy/CORS controls are required?
What should remain private forever?
```

## Primary Objective

Create a public exposure review that covers:

```text
route inventory
local-only/private route list
candidate public route list
required gate/budget/invite controls
Cloudflare Tunnel or reverse proxy boundary
CORS boundary
admin/status endpoint exposure
live provider safety
logging/secret exposure safety
manual go/no-go checklist
```

This is primarily a documentation, test, and safety-review task.

## Non-Negotiable Boundaries

Do not add:

- public route exposure;
- Cloudflare changes;
- DNS changes;
- production auth;
- user accounts;
- login UI;
- OAuth/OIDC;
- paid access;
- payment integration;
- invite emails;
- database migrations;
- production storage;
- Redis;
- Postgres;
- SQLite persistence;
- persistent user memory;
- production admin dashboard;
- live OpenAI calls during normal validation;
- committed tokens, `.env` files, screenshots, logs, or generated artifacts.

This task may add tests, docs, static route inventory helpers, and safety assertions.

## Suggested Files

Likely new files:

- `docs/ai-public-route-exposure-review.md`
- `ai-api/tests/test_ai_route_exposure_review.py`
- `outbox/0029H-public-route-exposure-review-results.md`

Likely updated files:

- `ai-api/app/main.py` only if metadata/tags/internal flags need small non-functional cleanup;
- `ai-api/app/recipe_session_routes.py` only if metadata/tags/internal flags need small non-functional cleanup;
- `ai-api/tests/test_demo_ui.py` if UI exposure labels need coverage;
- `docs/ai-live-demo-runbook.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Inventory AI routes

Create a route inventory for the AI sidecar.

Include all relevant routes such as:

- health/config/status routes;
- demo UI routes;
- importer routes;
- dataset ask / saved recipe ask routes;
- meal-plan routes;
- recipe-session routes;
- operator gate/status routes;
- invite grant/session routes;
- admin usage report route;
- any live smoke/debug/status routes if present.

For each route, document:

- method;
- path;
- purpose;
- current default exposure;
- whether hidden from OpenAPI;
- whether it can trigger provider calls;
- whether it uses operator gate;
- whether it uses invite sessions;
- whether it uses provider budget guard;
- whether it returns admin/operator data;
- recommended exposure category.

Suggested exposure categories:

```text
public_candidate
invite_only_candidate
operator_only
local_only
internal_status
never_public
```

### 2. Add route exposure tests

Add deterministic tests that verify route exposure expectations.

Suggested file:

```text
ai-api/tests/test_ai_route_exposure_review.py
```

Tests should check where practical:

- admin usage-report endpoint is hidden from OpenAPI;
- invite/session operator endpoints are not accidentally public-ready by default;
- operator-gated workflows block safely when gate enabled;
- invite-only workflows remain disabled by default;
- live provider calls remain opt-in and budget-gated;
- route inventory helper, if added, classifies admin/operator routes as `operator_only` or `never_public`;
- no route docs or generated schema expose raw token examples;
- no route response examples include secrets, local paths, raw prompts, or raw provider responses.

Do not require browser automation.

Do not require live provider calls.

### 3. Review OpenAPI exposure

Review which AI routes appear in OpenAPI.

Document:

- routes safe to show in OpenAPI;
- routes intentionally hidden from OpenAPI;
- routes that should remain hidden forever;
- any recommended metadata cleanup.

If a route exposes admin/invite/operator internals in OpenAPI by mistake, fix that with minimal metadata changes and add tests.

Do not change public deployment behavior.

### 4. Review Cloudflare/reverse-proxy boundary

Document the expected reverse-proxy boundary before any public AI route exposure.

Cover:

- current Cloudflare Tunnel/reverse-proxy assumption;
- which URL paths should be routed publicly;
- which URL paths should be blocked at proxy layer;
- whether `/demo`, `/ai/*`, `/ai/admin/*`, `/ai/invite/*`, and recipe-session routes should be exposed;
- whether operator-only/admin endpoints should be allowlisted or never routed;
- how to stage exposure safely.

Do not modify Cloudflare config in this task.

### 5. Review CORS boundary

Document recommended CORS behavior.

Cover:

- local development origins;
- production public site origin;
- whether wildcard CORS is acceptable;
- credential/header implications for `X-AI-Operator-Token` and `X-AI-Demo-Session-Token`;
- whether admin/operator headers should be allowed from browsers;
- preflight implications.

Do not open CORS broadly in this task.

### 6. Review endpoint classes

Document recommended future exposure by class:

#### Public candidate

Examples might include:

- static demo page only if intentionally public;
- health route if safe;
- basic recipe import preview only after gate/budget/invite controls are enforced.

#### Invite-only candidate

Examples might include:

- importer;
- dataset ask;
- recipe-session start/message/finalize;
- meal plan.

Only after invite sessions, budget guard, rate limiting, and route exposure controls are validated.

#### Operator-only

Examples:

- invite grant creation/revocation;
- usage report;
- operator gate status;
- live provider diagnostics.

#### Never public

Examples:

- admin usage report raw/detail endpoints if any;
- internal debug endpoints;
- endpoints that expose config or operational internals.

### 7. Add go/no-go checklist

Create a manual readiness checklist for future public exposure.

Checklist should include:

- operator gate reviewed;
- invite session flow tested;
- provider budget enforcement tested;
- usage report reviewed;
- route inventory updated;
- admin/operator endpoints hidden and blocked at proxy layer;
- CORS restricted;
- live opt-in confirmed;
- secret scan passed;
- evals passed;
- mock smoke passed;
- abuse/rate-limit strategy documented;
- logging reviewed;
- rollback plan documented.

### 8. Add abuse/rate-limit placeholder guidance

Do not implement rate limiting unless already present and trivial.

Document what should be added before public exposure:

- reverse proxy request limits;
- per invite/session request limits;
- provider-call limits;
- payload size limits;
- abuse/error thresholds;
- temporary block/revoke behavior;
- incident/rollback process.

### 9. Update docs

Create:

```text
docs/ai-public-route-exposure-review.md
```

Update:

- `docs/ai-live-demo-runbook.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

### 10. Create outbox report

Create:

```text
outbox/0029H-public-route-exposure-review-results.md
```

Include:

- route inventory summary;
- OpenAPI exposure findings;
- Cloudflare/reverse-proxy recommendations;
- CORS recommendations;
- public/invite/operator/never-public classification;
- tests added;
- docs updated;
- go/no-go checklist summary;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Public route exposure review document exists.
- AI route inventory identifies route purpose, provider-call risk, gate/invite/budget controls, and exposure recommendation.
- Admin/operator/invite routes are classified clearly.
- OpenAPI exposure is reviewed and tested where practical.
- Cloudflare/reverse-proxy recommendations are documented without changing deployment config.
- CORS recommendations are documented without broadening exposure.
- Go/no-go checklist exists for any future public live AI exposure.
- Tests protect critical exposure assumptions.
- Existing offline/mock validation remains stable.
- No public route exposure, Cloudflare changes, auth, paid access, payment integration, production storage, persistent memory, Redis/Postgres/SQLite persistence, production admin dashboard, or live OpenAI calls during normal validation are added.

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
- no payment secrets;
- no Cloudflare config changes.

## Commit

```bash
git add ai-api docs README.md outbox/0029H-public-route-exposure-review-results.md

git commit -m "mailbox: complete task 0029H public route exposure review"

git pull --rebase origin main
git push origin main
```
