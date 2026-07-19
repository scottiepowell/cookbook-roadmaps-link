# 0030H Local Cookbook AI Product Integration

## Goal

Integrate the AI sidecar experience into the local Cookbook product experience before moving on to AWS/platform infrastructure work.

The current AI UI is intentionally served separately by the FastAPI sidecar at `/demo` because the repository runs Vanilla Cookbook from an external Docker image and does not contain the upstream Vanilla Cookbook frontend source tree. This task should close that local product gap as much as practical without vendoring or rewriting the upstream application.

## Priority

Run this before `0032A Portfolio Platform AWS Scaling Architecture ADR`.

Keep `0032A` queued, but do not proceed with AWS infrastructure planning until the local integrated product path is designed and validated.

## Background

The 0029/0030 AI work is now strong as a local sidecar/demo feature slice:

- RAG-informed importer/create flow;
- dataset search and Dataset Ask/RAG;
- Ask My Cookbook;
- meal planning;
- recipe-session alpha endpoints;
- recipe-session demo UI;
- requirement diffs and revision summaries;
- offline evals and regression harnesses;
- local operator gate, invite sessions, usage report, and budget guard scaffolding.

However, the AI experience is still mostly sidecar/demo-oriented rather than integrated into the main local Cookbook product flow.

Existing docs say the first AI UI integration is served by the sidecar at:

```text
GET /demo
GET /demo/ai
```

and that this was intentional because the upstream Vanilla Cookbook frontend source tree is not present in the repo.

## Primary Objective

Create a local integrated product experience that makes Cookbook AI feel like part of the local Cookbook application, while preserving the architecture boundary that Vanilla Cookbook remains an external/upstream app and the AI sidecar owns AI workflows.

The outcome should be a polished local product path an operator can demo before AWS deployment work begins.

## Required Work

### 1. Inspect the current local runtime shape

Inspect:

- `docker-compose.yml`;
- `scripts/start-ai-demo-local.ps1`;
- `scripts/demo-ai-mock.ps1`;
- `ai-api/app/static/demo.html`;
- `ai-api/app/static/demo.js`;
- `ai-api/app/static/demo.css`;
- `docs/ai-ui-integration-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `README.md`.

Confirm how the Vanilla Cookbook container and AI sidecar are currently started locally, what ports/routes are exposed, and how generated fixture data is seeded.

### 2. Decide the local integration pattern

Choose the least invasive local integration pattern that works with an external upstream Cookbook image.

Acceptable options include:

#### Option A: Local integrated product shell

Add a sidecar-served local product shell that frames or links the Cookbook app and AI workflows together in one cohesive product page.

Example routes:

```text
GET /product
GET /product/cookbook
GET /product/ai
```

The shell may include:

- top navigation;
- local Cookbook app link/open target;
- AI recipe creator/session panel;
- readiness and data status;
- clear local/demo-only boundary messaging.

#### Option B: Reverse-proxy style local gateway design

If existing local routing supports it, create a local gateway/proxy plan or lightweight local route layout that makes Cookbook and AI appear under one local origin.

Example local routes:

```text
http://127.0.0.1:8000/product      -> integrated product shell
http://127.0.0.1:8000/demo         -> existing AI demo
http://127.0.0.1:<cookbook-port>/  -> upstream Cookbook app
```

Do not add production proxy/Cloudflare changes in this task.

#### Option C: Upstream UI integration only if source exists

If the actual editable Vanilla Cookbook frontend source is present in this repo, integrate a navigation entry or AI panel directly.

If it is not present, do not vendor the upstream app or rewrite it. Document the limitation and implement Option A or B instead.

### 3. Build a polished local entry point

Add or update the local sidecar UI so the operator has a single obvious place to start the local product demo.

The integrated entry point should show:

- app title/branding for the local Cookbook AI product;
- link or embedded access to the Vanilla Cookbook app;
- AI Recipe Creator / Recipe Session Alpha workflow;
- Ask My Cookbook;
- Dataset Search / Dataset Ask if still useful for demos;
- Meal Planner if still useful for demos;
- readiness/data status;
- provider mode/model status;
- local-only/demo-only boundary message;
- reset/seed guidance if local fixture data is missing.

Prefer reusing existing `/demo` components rather than duplicating large UI logic.

### 4. Preserve local safety boundaries

The integrated local product must not:

- expose API keys;
- expose raw provider prompts or provider responses;
- expose local filesystem paths;
- expose `.env` values;
- commit raw dataset files;
- commit `.tmp-ai-demo/` artifacts;
- write to production Cookbook storage;
- require live OpenAI calls;
- require public route exposure.

### 5. Improve local start/run guidance

Update local run scripts or docs so an operator can start the integrated local product clearly.

Potential script/doc updates:

- `scripts/start-ai-demo-local.ps1` prints the integrated product URL;
- `scripts/demo-ai-mock.ps1` validates the integrated product route or shell;
- README has a clear `Run the local integrated product` section;
- runbook explains which URL to open first.

Do not break the existing `/demo` route.

### 6. Add tests

Add deterministic offline tests for:

- integrated product route/page exists;
- page includes Cookbook app access/link or local integration guidance;
- page includes AI workflow access;
- readiness/provider status remains safe;
- static assets do not contain forbidden secret-like strings;
- mock smoke validates the integrated local entry point;
- existing `/demo` tests still pass.

If a true upstream app integration is impossible because the frontend source is not present, tests should assert the chosen local shell/link integration behavior and docs should state the boundary clearly.

### 7. Update docs

Update:

- `docs/ai-ui-integration-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md`.

Create if useful:

```text
docs/local-cookbook-ai-product-integration.md
```

Create:

```text
outbox/0030H-local-cookbook-ai-product-integration-results.md
```

The outbox should summarize:

- current separation between Vanilla Cookbook and AI sidecar;
- chosen local integration pattern;
- routes/UI added or updated;
- script/docs changes;
- tests added;
- validation results;
- explicit non-goals;
- recommendation for what must be true before AWS deployment work resumes.

## Acceptance Criteria

- Local integrated Cookbook AI product entry point exists.
- The entry point makes the AI sidecar feel connected to the Cookbook app locally.
- The chosen integration pattern respects the fact that the upstream Vanilla Cookbook frontend may not be editable in this repo.
- Existing `/demo` route remains available.
- Local run guidance clearly tells the operator which URL to open first.
- Mock/offline validation covers the integrated product entry point.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No AWS resources, Terraform, CDK, CloudFormation, DNS, Cloudflare, production deployment, auth, payment, public route, provider-routing, vector DB, embeddings, raw dataset, screenshot, browser automation, generated persistent index, or disk cache work is added.

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

If direct Windows pytest is run and fails due to the known local `pytest-of-scott` temp ACL issue, document that separately and rely on Git Bash validation if it passes.

Do not run live OpenAI during normal validation.

## Non-Goals

- No AWS resource creation
- No Terraform
- No CDK
- No CloudFormation
- No DNS or Cloudflare changes
- No production deployment
- No production auth
- No payment implementation
- No public route exposure
- No provider-routing changes
- No secondary-provider runtime
- No live OpenAI calls
- No vector database
- No embeddings
- No upstream Vanilla Cookbook vendoring
- No full upstream UI rewrite
- No production database migrations
- No persistent production memory
- No screenshots
- No browser automation
- No raw dataset commits
- No generated persistent indexes
- No disk cache

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030H-local-cookbook-ai-product-integration-results.md

git commit -m "mailbox: complete task 0030H local cookbook ai product integration"

git pull --rebase origin main

git push origin main
```
