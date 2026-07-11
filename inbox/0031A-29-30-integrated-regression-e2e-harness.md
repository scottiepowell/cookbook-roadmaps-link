# 0031A 29/30 Integrated Regression And E2E Harness

## Goal

Add a deterministic integrated regression and E2E-style validation harness for the completed 0029 access/guardrail track and the completed 0030 recipe-session alpha track before introducing secondary-provider offload experiments such as GLM-4.7 Flash.

This task should lock the baseline behavior for:

```text
0029C session/metering schemas
0029D local operator gate
0029E provider budget guard
0029F invite-only demo sessions
0029G admin usage report
0029H public route exposure review assumptions
0029I monetization/entitlement boundary assumptions
0030 recipe-session alpha API/UI/evals/hardening
```

The result should make future work safer, especially any future `0031B GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness`, by proving current OpenAI/mock behavior, access controls, invite sessions, budgets, route boundaries, and recipe-session workflows are stable first.

## Context

The 0029 track is complete through `0029I`:

- `0029C` added session, access grant, provider meter, quality event, audit event, and budget snapshot schemas.
- `0029D` added the local/private operator gate.
- `0029E` added centralized provider-call budget enforcement.
- `0029F` added local/private invite-only demo sessions.
- `0029G` added the local/operator usage report.
- `0029H` added public route exposure review and route-boundary tests.
- `0029I` added the monetization and entitlement boundary ADR.

The 0030 track completed the Recipe Session Alpha:

- requirements architecture;
- deterministic scaffold;
- alpha API endpoints;
- demo UI;
- offline eval harness;
- alpha hardening and acceptance runbook.

The next technical risk is regression drift across the combined 29/30 stack.

## Primary Objective

Create an integrated regression harness that exercises the combined local AI demo system end-to-end in mock/offline mode and optionally in live-smoke mode when explicitly opted in.

The harness should answer:

```text
Can a local operator create an invite, redeem it, use a protected recipe-session/importer/RAG flow, respect budget controls, observe usage reporting, and preserve route/public/monetization boundaries without leaking secrets or adding live/public behavior by default?
```

## Non-Negotiable Boundaries

Do not add:

- GLM provider integration in this task;
- secondary-provider routing in this task;
- production auth;
- user accounts;
- login UI;
- OAuth/OIDC;
- paid access;
- payment integration;
- ad network runtime code;
- sponsor runtime code;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- database migrations;
- production storage;
- Redis;
- Postgres;
- SQLite persistence;
- persistent user memory;
- production admin dashboard;
- live OpenAI calls during normal validation;
- committed invite/session tokens, operator tokens, `.env` files, logs, screenshots, generated artifacts, raw prompts, raw provider responses, or local absolute paths.

Normal validation must remain offline/mock-only.

Live checks must remain explicit opt-in and skip cleanly without opt-in.

## Suggested Files

Likely new files:

- `scripts/e2e-ai-29-30-regression.py`
- `scripts/run-ai-29-30-regression.ps1`
- `ai-api/tests/test_ai_29_30_regression_harness.py`
- `docs/ai-29-30-regression-e2e-harness.md`
- `outbox/0031A-29-30-integrated-regression-e2e-harness-results.md`

Likely updated files:

- `scripts/demo-ai-mock.ps1`
- `scripts/demo-ai-live-smoke.ps1`
- `scripts/run-openai-demo-evals.ps1`
- `evals/ai_cookbook/run_evals.py` if a new optional eval group is useful
- `docs/ai-live-demo-runbook.md`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-public-route-exposure-review.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/ai-monetization-and-entitlement-boundary-adr.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

## Required Work

### 1. Add integrated regression script

Create:

```text
scripts/e2e-ai-29-30-regression.py
```

The script should run locally/offline by default using FastAPI `TestClient` or the existing app test patterns.

It should execute a deterministic integrated flow:

```text
health/config readiness
operator gate disabled default check
invite sessions disabled default check
usage report empty/default safety check
operator gate enabled test context
invite session enabled test context
create invite grant
redeem invite grant into demo session
call protected importer or recipe-session start with invite session token
send recipe-session follow-up that triggers material change/RAG refresh
finalize recipe-session draft
call dataset ask or saved-recipe ask in mock/offline mode
exercise provider budget allowed/skipped mock behavior
force a budget block in test context and prove provider is not invoked
fetch usage report and verify session/meter/budget counts
verify admin usage report remains never-public/hidden from OpenAPI
verify route exposure assumptions still hold
verify monetization boundary docs are not runtime payment/ad code
verify forbidden strings do not appear in responses
```

Keep the script deterministic and bounded.

Do not rely on real OpenAI, GLM, Cloudflare, DNS, browser automation, screenshots, or external network access.

### 2. Add PowerShell wrapper

Create:

```text
scripts/run-ai-29-30-regression.ps1
```

The wrapper should:

- set safe default env vars for mock/offline mode;
- clear live/provider env pollution where appropriate;
- run the integrated regression script;
- print a concise pass/fail summary;
- skip live-only checks unless explicitly opted in;
- never print raw tokens or secrets.

Suggested default behavior:

```text
AI_PROVIDER=mock
OPENAI_ENABLE_LIVE_TESTS=false
AI_OPERATOR_GATE_ENABLED=false unless test context overrides internally
AI_INVITE_SESSIONS_ENABLED=false unless test context overrides internally
AI_PROVIDER_GLOBAL_DISABLE=false unless block test overrides internally
```

### 3. Add pytest coverage for the harness

Create:

```text
ai-api/tests/test_ai_29_30_regression_harness.py
```

Tests should verify:

- the regression script exists;
- the PowerShell wrapper exists;
- the script can run in mock/offline mode or key helper functions can be imported/tested;
- pass/fail summary is deterministic;
- forbidden strings are not printed;
- live checks are opt-in only;
- GLM/secondary-provider behavior is not added in this task;
- payment/ad/sponsor runtime code is not added by this task.

### 4. Add optional live-smoke regression boundary

If practical, extend existing live smoke wrappers with a clearly optional integrated check.

Expected behavior:

- without `OPENAI_ENABLE_LIVE_TESTS=true`, skip cleanly;
- with live opt-in, use existing OpenAI budget guard limits;
- run the smallest possible live route check;
- verify budget guard/usage report records safe meter data;
- do not exceed configured budget;
- do not require live checks in normal validation.

Do not add GLM live calls here.

### 5. Verify combined 0029 controls

The integrated harness should cover these 0029 controls:

- `0029C`: safe model serialization and meter/budget snapshot assumptions;
- `0029D`: operator gate blocks missing/wrong token when enabled;
- `0029E`: budget guard blocks live-provider call before invocation when over budget or disabled;
- `0029F`: invite grant/session creation, redemption, expiry/revocation or safe blocking;
- `0029G`: usage report reflects safe state;
- `0029H`: admin/report/invite routes are not public-ready and exposure assumptions hold;
- `0029I`: no payment/ad/sponsor runtime behavior exists.

### 6. Verify combined 0030 controls

The integrated harness should cover these 0030 recipe-session behaviors:

- detailed user request creates a draft;
- vague request asks clarification and does not fake a draft;
- follow-up can trigger material RAG refresh;
- chatter/format-only follow-up does not wastefully refresh;
- finalize is demo-only/local-safe;
- missing/expired session blocks safely;
- response serialization does not leak raw prompts/provider responses/secrets/local paths;
- existing offline recipe-session eval cases still pass.

### 7. Add regression documentation

Create:

```text
docs/ai-29-30-regression-e2e-harness.md
```

Document:

- why this harness exists;
- what 0029 controls it validates;
- what 0030 controls it validates;
- default mock/offline mode;
- optional live-smoke mode;
- how it prepares the project for `0031B GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness`;
- known Windows pytest temp ACL note;
- explicit non-goals.

### 8. Update docs/backlog/status

Update:

- `docs/ai-live-demo-runbook.md`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-public-route-exposure-review.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/ai-monetization-and-entitlement-boundary-adr.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

Backlog should introduce the next planned follow-on after this task:

```text
0031B: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness
```

Make clear that GLM work comes after this baseline and must be disabled by default.

### 9. Add outbox report

Create:

```text
outbox/0031A-29-30-integrated-regression-e2e-harness-results.md
```

Include:

- integrated flow implemented;
- scripts added;
- tests added;
- 0029 controls covered;
- 0030 controls covered;
- optional live-smoke behavior;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation;
- recommendation for `0031B` GLM ADR/eval harness.

## Acceptance Criteria

- Integrated 29/30 regression harness exists.
- Harness runs offline/mock by default.
- Harness exercises operator gate, invite sessions, provider budget guard, usage report, public exposure assumptions, monetization boundary assumptions, and recipe-session alpha behavior.
- Harness proves blocked budget/provider paths do not invoke provider when testable.
- Optional live-smoke path remains opt-in and skips cleanly without opt-in.
- Existing offline evals still pass.
- Existing mock demo still passes.
- No GLM provider integration, secondary-provider routing, payment runtime, ad/sponsor runtime, public route exposure, production auth, storage, Redis/Postgres/SQLite persistence, Cloudflare changes, DNS changes, browser automation, screenshots, generated artifacts, or live provider calls during normal validation are added.
- Docs explain that `0031B GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` should use this baseline for comparison.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ai-29-30-regression.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_29_30_regression_harness.py -q
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest hits the known local `pytest-of-scott` temp ACL issue for unrelated fixture tests, document it and rely on Git Bash validation if it passes.

Before committing, confirm:

- no GLM provider code yet;
- no secondary-provider routing yet;
- no raw invite/session tokens;
- no raw operator tokens;
- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no payment secrets;
- no ad network IDs;
- no sponsor secrets/contracts;
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0031A-29-30-integrated-regression-e2e-harness-results.md

git commit -m "mailbox: complete task 0031A 29 30 integrated regression e2e harness"

git pull --rebase origin main
git push origin main
```
