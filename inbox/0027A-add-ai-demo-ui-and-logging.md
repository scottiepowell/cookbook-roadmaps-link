# Task 0027A: Add AI Demo UI And Logging

## Goal

Start the product-facing phase by adding a lightweight AI demo UI and a safe logging foundation for the FastAPI AI sidecar.

Control plane, production storage, deployment architecture, Qdrant, Postgres, pgvector, embeddings, vector DB, and broader platform work remain deferred.

The goal is to let a user manually open a UI and exercise the completed AI features so future screenshots and live demos show the actual application behavior, not only docs or REST examples.

## Context

The current repo runs Vanilla Cookbook from an external Docker image in `docker-compose.yml`. The repo contains the FastAPI `ai-api` sidecar, but not the upstream Vanilla Cookbook frontend source tree. Therefore, do not attempt a deep upstream UI rewrite in this task.

The first UI integration should be a sidecar-served AI demo page, for example:

```text
GET /demo
GET /demo/ai
```

## Build On

Completed work:

- `0026C`: final AI feature completion review
- `0026B`: AI portfolio README polish
- `0026A`: AI demo scripts and request examples
- `0025C` through `0025E`: manual live OpenAI smoke path and fixes
- `0021` through `0024D`: completed AI endpoints

Before implementing, confirm the repo has:

- `ai-api/app/main.py`
- `ai-api/app/importer.py`
- `ai-api/app/rag.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/dataset_rag.py`
- `ai-api/app/meal_plan_endpoint.py`
- `docs/ai-feature-completion-review.md`
- `scripts/demo-ai-requests.http`
- `outbox/0026C-final-ai-feature-completion-review-results.md`

If prerequisites are missing, stop and report what is missing.

## Scope

Add two foundations:

1. A lightweight AI demo UI served by the FastAPI sidecar.
2. Structured logging for AI sidecar requests and AI workflow events.

Keep the implementation small and dependency-light.

## AI Demo UI Requirements

Add a simple HTML/CSS/JavaScript UI served by `ai-api`.

Suggested files:

```text
ai-api/app/static/demo.html
ai-api/app/static/demo.js
ai-api/app/static/demo.css
```

The UI should include sections for:

- health/config check;
- structured recipe importer;
- Ask My Cookbook;
- dataset search;
- dataset ask/RAG;
- meal planner;
- provider/status display;
- safety and data-boundary note.

Use browser `fetch()` calls to existing AI endpoints.

Show:

- readable answer text;
- JSON response preview;
- citations/provenance;
- warnings;
- provider/model;
- retrieval metadata;
- clear error messages.

The UI should not display sensitive runtime values or local private paths.

Saved-recipe flows may require local cookbook data. If required data is missing, the UI should show a friendly message instead of failing unclearly.

## Logging Requirements

Add a structured logging foundation for the AI sidecar.

A good first implementation can log to stdout because Docker Compose already collects service logs per service. Do not add external log infrastructure in this task.

Log safe metadata such as:

- endpoint name;
- request ID;
- provider;
- model;
- status;
- duration in milliseconds;
- retrieved count;
- citation count;
- warning count;
- safe error type;
- timestamp.

Do not log raw secrets, full environment contents, full prompts, full pasted recipes, full provider response bodies, or private local filesystem paths by default.

Add middleware if appropriate to assign a request ID and timing.

## Docs

Create or update:

```text
docs/ai-ui-integration-plan.md
docs/ai-sidecar-logging.md
docs/ai-feature-status.md
docs/ai-demo-walkthrough.md
docs/ai-implementation-backlog.md
docs/repo-map.md
README.md
outbox/0027A-add-ai-demo-ui-and-logging-results.md
```

Docs should explain:

- why the first UI integration is sidecar-served;
- how to open the AI demo UI locally;
- which endpoints the UI exercises;
- how to view logs locally or with Docker Compose;
- what is intentionally not logged;
- how this supports future screenshots and live demos.

## Tests

Add tests for:

- demo UI route returns HTML;
- static assets load if separate files are used;
- UI route does not include obvious sensitive-value placeholders;
- logging middleware or helper emits safe fields where practical;
- existing AI endpoints still pass.

Use FastAPI `TestClient` tests only. Do not add browser automation.

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

Do not implement production storage, deployment changes, Cloudflare changes, controller workflows, live provider tests in CI, Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, upstream Vanilla Cookbook frontend rewrite, browser automation, committed screenshots, raw dataset commits, generated artifact commits, private environment file commits, or credential commits.

## Outbox Report

Create:

```text
outbox/0027A-add-ai-demo-ui-and-logging-results.md
```

Include:

- Summary
- Files changed
- UI routes added
- UI features included
- Logging behavior added
- What is not logged
- Tests added
- Validation results
- Known limitations
- Confirmation that normal validation stayed offline
- Confirmation that no private environment files, raw datasets, generated artifacts, screenshots, or credentials were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add ai-api docs README.md outbox/0027A-add-ai-demo-ui-and-logging-results.md

git commit -m "mailbox: complete task 0027A add ai demo ui and logging"

git push origin main
```

## Done Criteria

- AI demo UI route exists and returns usable HTML.
- UI can manually exercise the major AI endpoints or clearly explains missing local data requirements.
- UI displays responses, citations/provenance, warnings, provider/model, and errors safely.
- Structured logging foundation exists for AI sidecar requests/events.
- Logs avoid sensitive values and large raw payloads by default.
- Tests cover UI route and basic logging safety.
- Docs explain the sidecar-served UI approach and logging behavior.
- Normal validation passes or the known Windows direct-pytest issue is documented with Git Bash validator passing.
- No production infrastructure changes are made.
