# 0030F Recipe Session Alpha Hardening And Acceptance

## Goal

Harden the completed 0030 recipe-session alpha workflow and produce a clear operator acceptance/runbook baseline before adding access gates, metering enforcement, invite flows, or public/live AI exposure.

This task should focus on quality, safety, edge cases, documentation, and acceptance readiness for the existing local/offline recipe-session alpha. It should not add major new product features.

## Context

The 0030 recipe-session alpha now includes:

- `0030A`: requirements/session architecture;
- `0030B`: deterministic requirements scaffold and process-local session store;
- `0030C`: local alpha recipe-session API endpoints;
- `0030D`: Recipe Session Alpha demo UI and offline smoke flow;
- `0030E`: recipe-session offline eval harness integrated into `run_evals.py`.

The offline eval baseline is now 36/36 cases and the Git Bash validator has passed with the recipe-session eval group included.

`0030F` should be a hardening and acceptance task that makes the alpha safe to demo locally and easy to evaluate before moving to the 0029C/0029D access and metering guardrail track.

## Primary Objective

Review and harden the recipe-session alpha across:

```text
API responses
session state safety
UI rendering
mock smoke flow
session evals
operator runbook
edge cases
logging/diagnostics
artifact safety
```

The final result should answer: "Can I confidently demo and validate the Recipe Session Alpha locally, and do I know its boundaries?"

## Non-Negotiable Boundaries

Do not add:

- production storage;
- database migrations;
- auth;
- paid access;
- public route exposure;
- Cloudflare changes;
- persistent user memory;
- Redis;
- Postgres;
- SQLite session persistence;
- vector DB;
- embeddings;
- Qdrant;
- pgvector;
- full chat UI;
- browser automation;
- screenshots committed to the repo;
- live OpenAI calls during normal validation;
- budget enforcement runtime;
- invite flow runtime.

Keep everything local/offline/mock-friendly.

## Suggested Files

Likely updated files:

- `ai-api/app/recipe_session_routes.py`
- `ai-api/app/recipe_session.py`
- `ai-api/app/recipe_requirements.py`
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/app/static/demo.css`
- `ai-api/tests/test_recipe_session_api.py`
- `ai-api/tests/test_recipe_session.py`
- `ai-api/tests/test_recipe_requirements.py`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_recipe_session_eval_harness.py`
- `evals/ai_cookbook/session_cases.yaml`
- `evals/ai_cookbook/session_eval.py`
- `scripts/demo-ai-mock.ps1`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Optional new file:

- `docs/recipe-session-alpha-acceptance-runbook.md`

Required new outbox:

- `outbox/0030F-recipe-session-alpha-hardening-and-acceptance-results.md`

## Required Work

### 1. Perform an alpha workflow review

Review the current recipe-session path end to end:

```text
start
message
get
finalize
reset UI
mock smoke
session evals
```

Confirm the behavior is consistent across:

- API tests;
- demo UI rendering;
- mock smoke script;
- eval harness;
- docs/runbook.

Fix inconsistencies or clearly document intentional differences.

### 2. Harden API response safety

Review session endpoint responses for safe serialization.

Confirm none of the recipe-session endpoints expose:

- raw provider prompts;
- raw provider responses;
- API keys;
- authorization headers;
- `.env` values;
- local absolute dataset paths;
- `.tmp-ai-demo` paths;
- stack traces;
- raw cache internals;
- production storage paths.

Add or strengthen tests if any response path is not covered.

### 3. Harden edge cases

Add focused tests or fixes for practical alpha edge cases.

Cover as many as are lightweight and appropriate:

- empty start text;
- symbols-only start text;
- very vague start text;
- detailed start text;
- expired session get/message/finalize;
- unknown session get/message/finalize;
- follow-up before draft exists;
- finalize before draft exists;
- repeated finalize;
- repeated no-refresh message;
- reset/local UI state behavior;
- contradictory follow-up such as `make it no-bake but bake it overnight`;
- food-safety ambiguity such as raw vs cooked chicken casserole;
- method-change follow-up such as `use air fryer instead`;
- excluded ingredient follow-up such as `no nuts` or `no heavy cream`.

Do not overbuild. Prefer deterministic tests and simple safe behavior.

### 4. Harden UI presentation

Review the Recipe Session Alpha UI.

Improve only where useful:

- clearer alpha/demo-only labeling;
- clearer session expiration display;
- clearer finalize-for-demo warning;
- clearer no-refresh explanation;
- clearer RAG refresh reason;
- better empty-state text;
- better friendly errors for missing/expired sessions;
- consistent citation/support rendering with importer UI.

Do not build a full chat UI.

### 5. Harden eval coverage if needed

Review `evals/ai_cookbook/session_cases.yaml` and `session_eval.py`.

Add small regression cases only if they materially improve alpha confidence.

Good candidates:

- expired/missing finalize safety;
- finalize-before-draft behavior;
- contradictory method follow-up safe handling;
- air fryer equipment follow-up triggers refresh;
- excluded ingredient follow-up triggers refresh.

Keep `run_evals.py` fast and deterministic.

### 6. Add or update acceptance runbook

Create or update a clear operator acceptance runbook.

Preferred new file:

```text
docs/recipe-session-alpha-acceptance-runbook.md
```

The runbook should include:

- purpose of Recipe Session Alpha;
- local/offline boundary;
- how to start the mock demo;
- demo URL(s);
- required provider mode for normal validation;
- step-by-step happy path;
- clarification path;
- RAG refresh path;
- no-refresh path;
- finalize-for-demo path;
- expected response states;
- what good looks like;
- what is intentionally not supported yet;
- known Windows `pytest-of-scott` temp ACL issue note;
- validation commands.

### 7. Logging and diagnostics review

Confirm existing logs/diagnostics are useful and safe for the recipe-session flow.

If logging exists for these endpoints, confirm it includes safe operational metadata such as:

- endpoint/workflow;
- response state;
- status;
- duration if available;
- warning count if available;
- retrieved/citation counts if available.

Do not log raw prompts, raw provider responses, secrets, local paths, or `.env` values.

If recipe-session logging is absent or minimal, add small safe logs only if consistent with existing logging patterns.

### 8. Update mock smoke validation if needed

Ensure `scripts/demo-ai-mock.ps1` remains the canonical local smoke command and exercises:

- detailed session start;
- material follow-up with RAG refresh;
- get session;
- finalize;
- vague clarification;
- chatter/no-refresh;
- forbidden-text safety.

Keep it offline/mock-only.

### 9. Update docs and status

Update as needed:

- `docs/recipe-session-requirements-architecture.md`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Mark `0030F` complete in the backlog only after validation passes.

### 10. Create outbox report

Create:

```text
outbox/0030F-recipe-session-alpha-hardening-and-acceptance-results.md
```

Include:

- hardening summary;
- edge cases reviewed/fixed;
- UI changes;
- eval/test changes;
- mock smoke coverage;
- runbook/docs updates;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Recipe Session Alpha has a clear local acceptance/runbook baseline.
- API responses remain safe and do not leak prompts, secrets, local paths, provider raw responses, or stack traces.
- Important start/message/get/finalize edge cases are tested or documented.
- Demo UI clearly labels alpha/demo-only behavior and finalize-for-demo boundaries.
- Mock smoke validation still exercises the session flow offline.
- Offline evals still pass and remain fast.
- Git Bash validator passes.
- No live OpenAI calls are required.
- No production storage, persistent user memory, auth, paid access, public route exposure, vector DB, embeddings, Redis, Qdrant, pgvector, browser automation, screenshots, invite flow, budget enforcement, or full chat UI is added.

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
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage;
- no payment/invite secrets.

## Commit

```bash
git add ai-api evals scripts docs README.md outbox/0030F-recipe-session-alpha-hardening-and-acceptance-results.md

git commit -m "mailbox: complete task 0030F recipe session alpha hardening acceptance"

git pull --rebase origin main
git push origin main
```
