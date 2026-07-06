# Task 0026A: Add AI Demo Walkthrough And Scripts

## Goal

Make the completed AI cookbook features demo-ready for a portfolio, interview, or freelance/customer walkthrough.

The app now has offline tests/evals and a successful manual live OpenAI validation. This task should package those capabilities into clear demo scripts, documentation, and repeatable commands that show the AI layer without requiring production infrastructure work.

## Build On

Completed work:

- `0021`: structured recipe importer
- `0022`: Ask My Cookbook RAG over saved recipes
- `0023B`: saved-recipe meal-plan endpoint
- `0024C`: indexed local dataset search endpoint
- `0024D`: dataset ask/RAG endpoint
- `0025A`: offline eval harness and validation hygiene
- `0025B`: expanded offline AI evals
- `0025C`: manual live OpenAI smoke tests
- `0025D`: OpenAI strict structured-output schema compatibility
- `0025E`: Windows-safe live smoke cleanup and recorded live validation

Before implementing, confirm the repo has:

- `scripts/smoke-openai-live.py`
- `evals/ai_cookbook/run_evals.py`
- `docs/live-openai-smoke-tests.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `docs/shared-infrastructure-data-boundaries.md`
- `outbox/0025E-fix-live-smoke-windows-cleanup-results.md`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

Create demo-focused scripts and docs only.

The demo should cover:

1. AI sidecar health/config.
2. Structured recipe importer.
3. Ask My Cookbook over saved recipes.
4. Local dataset search.
5. Dataset ask/RAG with citations.
6. Saved-recipe meal planning.
7. Offline evals.
8. Optional manual live OpenAI smoke validation.

Keep the demo local and safe. Do not change production deployment.

## Suggested Files

Create or modify as appropriate:

```text
scripts/demo-ai-mock.ps1
scripts/demo-ai-live-smoke.ps1
scripts/demo-ai-requests.http
docs/ai-demo-walkthrough.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/repo-map.md
README.md
outbox/0026A-add-ai-demo-walkthrough-and-scripts-results.md
```

If PowerShell scripts are too much for this task, create docs plus `.http` examples first and document deferred script work in the outbox.

## Demo Modes

### Mock Demo

Create a safe mock/offline demo path that does not require OpenAI credentials.

It should explain or automate:

- starting the app/sidecar locally if applicable;
- calling health/config;
- calling importer with sample recipe text;
- calling saved-recipe ask with generated or documented fixture assumptions;
- calling dataset search/ask with a tiny generated fixture if practical;
- running offline evals.

The mock demo should be the default recommended demo because it is free and deterministic.

### Live Smoke Demo

Create a separate script or doc section for the manual live OpenAI smoke path.

It should reuse `scripts/smoke-openai-live.py` and keep the existing opt-in controls:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
& .\.venv\Scripts\python.exe .\scripts\smoke-openai-live.py
```

Do not copy private keys into docs or scripts. The docs should say the provider key must come from the user's local ignored environment.

## Demo Walkthrough Content

`docs/ai-demo-walkthrough.md` should be written as a reusable guide.

Include:

- purpose of the AI sidecar;
- architecture summary: existing Vanilla Cookbook app plus FastAPI sidecar;
- what each AI endpoint demonstrates;
- what retrieval/citation grounding means;
- how offline evals prove basic quality gates;
- how the manual live smoke test proves the real provider path;
- known constraints and non-goals;
- a suggested 5-minute interview/demo talk track.

## Feature Status Matrix

Create or update `docs/ai-feature-status.md` with a matrix like:

```text
Feature | Endpoint/Script | Offline Tests | Offline Evals | Live Smoke | Docs | Notes
Importer | POST /ai/import-recipe | yes | yes | yes | yes | structured output
Ask My Cookbook | POST /ai/ask | yes | yes | yes | yes | saved-recipe RAG
Dataset Search | GET/POST /dataset/search | yes | yes | n/a | yes | deterministic retrieval
Dataset Ask | POST /dataset/ask | yes | yes | yes | yes | dataset RAG with citations
Meal Planner | POST /ai/meal-plan | yes | yes | yes | yes | saved recipe candidates only
Provider Harness | scripts/smoke-openai-live.py | yes | yes | yes | yes | mock default, live optional
```

Keep claims accurate based on actual tests/evals and outbox reports.

## Request Examples

Add request examples that can be copied into a REST client or VS Code REST Client.

Prefer a file like:

```text
scripts/demo-ai-requests.http
```

Include examples for:

- `GET /health`
- `GET /ai/config`
- `POST /ai/import-recipe`
- `POST /recipes/search`
- `POST /ai/ask`
- `GET /dataset/search`
- `POST /dataset/search`
- `POST /dataset/ask`
- `POST /ai/meal-plan`

Use safe sample data only.

Do not include API keys or private local paths.

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct Windows pytest still fails with the known temp-directory issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI calls as part of normal validation.

## Non-Goals

Do not implement:

- production storage architecture
- deployment changes
- Cloudflare changes
- controller/demo launch workflows
- GitHub Actions live provider tests
- Qdrant
- Postgres
- pgvector
- embeddings
- vector database
- persistent generated indexes
- UI rewrites
- raw dataset commits
- generated artifact commits
- private environment file commits

## Outbox Report

Create:

```text
outbox/0026A-add-ai-demo-walkthrough-and-scripts-results.md
```

Include:

- Summary
- Files changed
- Demo scripts/docs added
- Feature status matrix summary
- Request examples added
- Validation results
- Any deferred demo work and why
- Confirmation that normal validation stayed offline
- Confirmation that no private environment files, raw datasets, generated artifacts, or provider keys were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add scripts docs README.md outbox/0026A-add-ai-demo-walkthrough-and-scripts-results.md

git commit -m "mailbox: complete task 0026A add ai demo walkthrough and scripts"

git push origin main
```

## Done Criteria

- AI demo walkthrough exists.
- Feature status matrix exists.
- Request examples exist.
- Mock/offline demo path is documented.
- Manual live smoke path is documented without exposing private values.
- README points to the demo docs.
- Normal validation passes or the known Windows direct-pytest issue is documented with Git Bash validator passing.
- No production infrastructure changes are made.
- No private environment files, raw datasets, generated artifacts, or provider keys are committed.
