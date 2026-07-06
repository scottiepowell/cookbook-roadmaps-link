# Task 0027B: Production-Quality AI Demo Usability

## Goal

Harden the AI demo UI from `0027A` so it feels production-quality for a 15 to 30 minute hands-on live demo.

The application does not need production storage, control-plane automation, or long-term persistence in this task. However, a person using the demo for 15 to 30 minutes should experience clear flows, predictable state, useful demo data, good errors, and enough polish to understand and trust the AI features from the UI.

## Build On

This task should start only after `0027A` is complete.

Expected `0027A` outputs:

- sidecar-served AI demo UI route;
- static HTML/CSS/JS assets or equivalent;
- structured logging foundation;
- docs for UI integration and logging;
- outbox report for `0027A`.

Before implementing, confirm the repo has:

- `outbox/0027A-add-ai-demo-ui-and-logging-results.md`
- AI demo UI route and assets from `0027A`
- logging docs from `0027A`
- `docs/ai-feature-completion-review.md`

If prerequisites are missing, stop and report what is missing.

## Scope

Improve the user-facing demo experience. Keep this product-focused, not infrastructure-focused.

Add or improve:

1. Guided demo flow.
2. Production-style UI states.
3. Demo data readiness checks.
4. Clear error recovery.
5. Better logging visibility for an operator.
6. Screenshot-ready UI polish.
7. Documentation for running a 15 to 30 minute live demo.

## Usability Requirements

The UI should feel good enough for a live user session.

Minimum requirements:

- clear landing section explaining the demo;
- visible system/provider status;
- guided workflow order for importer, saved-recipe ask, dataset search, dataset ask, and meal planning;
- sample inputs for every feature;
- reset buttons for every feature;
- loading states and disabled buttons while requests run;
- readable answer cards, not only raw JSON;
- citations and provenance displayed in a dedicated area;
- warnings displayed as user-friendly messages;
- errors displayed with next-step guidance;
- raw JSON available behind a details/expand section;
- responsive layout for laptop screens;
- clean styling suitable for screenshots;
- no stack traces shown in the browser;
- no sensitive runtime values or local private paths displayed.

## Demo Data Readiness

Add a demo readiness panel or endpoint if helpful.

The UI should make it clear whether:

- the AI sidecar is healthy;
- provider mode is mock or OpenAI;
- saved-recipe data is available for saved-recipe flows;
- local dataset data is available for dataset flows;
- offline/demo fixture mode is being used, if applicable.

If saved-recipe data or dataset data is missing, the UI should show a friendly message and still allow the rest of the demo to work.

Do not import raw datasets or write to production cookbook data in this task.

## Optional Demo Fixture Support

If needed, add a small sidecar-only demo fixture mode for UI demos.

Acceptable options:

- UI sample inputs only;
- generated temporary fixtures used by existing endpoints/tests;
- a read-only demo-data endpoint that returns sample payloads;
- documentation that explains what local data is required.

Do not add persistent generated indexes, production writes, or raw dataset commits.

## Logging Usability

Build on the logging foundation from `0027A`.

Improve logs so an operator can answer during a demo:

- which UI workflow was run;
- which endpoint was called;
- whether the request succeeded or failed;
- provider and model if available;
- duration;
- retrieved count;
- citation count;
- warning count;
- request ID.

Update docs with commands such as:

```powershell
docker compose logs ai-api --tail 100
```

and local uvicorn log guidance if applicable.

Do not add external logging infrastructure.

## Docs

Create or update:

```text
docs/ai-live-demo-runbook.md
docs/ai-ui-integration-plan.md
docs/ai-sidecar-logging.md
docs/ai-screenshot-capture-guide.md
docs/ai-feature-status.md
docs/ai-demo-walkthrough.md
docs/ai-implementation-backlog.md
README.md
outbox/0027B-production-quality-ai-demo-usability-results.md
```

The live demo runbook should include:

- pre-demo checklist;
- mock/demo mode path;
- optional live OpenAI smoke path;
- how to open the UI;
- suggested 15 minute flow;
- suggested 30 minute flow;
- troubleshooting steps;
- log viewing commands;
- screenshot capture guidance;
- boundaries and non-goals.

## Tests

Use FastAPI TestClient and lightweight static checks only.

Add tests for:

- UI route includes major workflow sections;
- UI/static assets do not expose sensitive placeholders;
- readiness/status endpoint if added;
- error response handling helpers if implemented server-side;
- logging helper/event shape if changed;
- existing AI endpoints still pass.

Do not add browser automation in this task.

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
```

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

The live smoke wrapper should skip cleanly unless explicitly opted in. Do not run live provider calls during normal validation.

## Non-Goals

Do not implement production storage, deployment changes, Cloudflare changes, control-plane workflows, live provider tests in CI, Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, upstream Vanilla Cookbook frontend rewrite, browser automation, committed screenshots, raw dataset commits, generated artifact commits, private environment file commits, or credential commits.

## Outbox Report

Create:

```text
outbox/0027B-production-quality-ai-demo-usability-results.md
```

Include:

- Summary
- Files changed
- UI usability improvements
- Demo readiness behavior
- Logging usability improvements
- Runbook updates
- Tests added
- Validation results
- Known limitations
- Confirmation that normal validation stayed offline
- Confirmation that no private environment files, raw datasets, generated artifacts, screenshots, or credentials were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add ai-api docs README.md outbox/0027B-production-quality-ai-demo-usability-results.md

git commit -m "mailbox: complete task 0027B production quality ai demo usability"

git push origin main
```

## Done Criteria

- AI demo UI is usable for a 15 to 30 minute hands-on demo.
- UI has clear workflow sections, sample inputs, loading states, reset behavior, readable outputs, citations, warnings, and errors.
- Demo readiness/data availability is clear to the user.
- Operator can inspect useful sidecar logs during a demo.
- Live demo runbook exists.
- Tests cover the UI/readiness/logging behavior where practical.
- Normal validation passes or the known Windows direct-pytest issue is documented with Git Bash validator passing.
- No production infrastructure changes are made.
