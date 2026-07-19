# 0030I Local Product Acceptance And Demo Hardening

## Goal

Perform a local product acceptance and hardening pass for the integrated Cookbook AI product experience before resuming AWS/platform architecture work.

`0030H` added the local integrated product shell:

- `GET /product` — local Cookbook AI shell;
- `GET /product/cookbook` — redirect to local Vanilla Cookbook on port 3000;
- `GET /product/ai` — redirect to the existing `/demo` AI workspace.

This task should turn that integration into a reviewed local baseline that is good enough to demo as a finalized local product slice.

## Background

Vanilla Cookbook remains an external Docker image on local port 3000, and AI workflows remain in the FastAPI sidecar on port 8000. The selected integration pattern is a sidecar-served product shell that connects the local Cookbook app and AI workflows without vendoring or rewriting the upstream frontend.

The `0030H` outbox says AWS/platform planning should resume only after the local product entry point, startup guidance, and mock smoke coverage remain the reviewed baseline.

## Primary Objective

Harden and validate the local integrated product experience so an operator can run one command, open one starting URL, and confidently demo the local product without needing to know the sidecar internals.

The local product should clearly support:

```text
start local product
  -> open /product
  -> verify readiness
  -> open Cookbook app
  -> open AI workspace
  -> run Recipe Creator / Recipe Session Alpha
  -> confirm mock/offline safety
  -> confirm no production write-back
  -> confirm clear next-step guidance
```

## Required Work

### 1. Review current local product flow

Inspect and exercise the current local flow:

```text
scripts/start-ai-demo-local.ps1
scripts/demo-ai-mock.ps1
docker-compose.yml
ai-api/app/static/product.html
ai-api/app/static/product.css
ai-api/app/static/product.js
ai-api/app/static/demo.html
ai-api/app/static/demo.js
ai-api/app/static/demo.css
docs/local-cookbook-ai-product-integration.md
docs/ai-ui-integration-plan.md
docs/ai-live-demo-runbook.md
README.md
```

If product files use different names, inspect the actual product-shell files added by `0030H`.

### 2. Improve `/product` as the canonical local entry point

Make sure `/product` clearly communicates:

- this is the local Cookbook AI product shell;
- Cookbook is the upstream local app;
- AI workflows are served by the sidecar;
- which URL to open first;
- provider mode/model status;
- saved-recipe fixture status;
- local dataset fixture status;
- safe mock/offline defaults;
- how to seed/reset fixtures if data is missing;
- that finalize/demo actions do not write production storage.

Keep the UI compact and practical. Do not build a full upstream UI rewrite.

### 3. Add a local product acceptance checklist

Create a concise operator checklist.

Suggested file:

```text
docs/local-product-acceptance-checklist.md
```

The checklist should include:

- prerequisites;
- start command;
- first URL to open;
- expected `/product` readiness state;
- expected Cookbook link/redirect behavior;
- expected AI workspace behavior;
- Recipe Session Alpha happy path;
- vague clarification path;
- RAG refresh path;
- no-refresh chatter path;
- finalize-for-demo behavior;
- mock/offline boundaries;
- known Windows pytest temp ACL note;
- go/no-go criteria for moving back to AWS/platform work.

### 4. Strengthen mock smoke coverage

Update `scripts/demo-ai-mock.ps1` or add a small focused helper so local mock smoke covers the integrated product baseline.

At minimum, assert:

- `/product` returns 200;
- `/product` contains product-shell text and AI/Cookbook navigation;
- `/product/cookbook` redirects or points to local port 3000 as intended;
- `/product/ai` redirects to `/demo` as intended;
- `/demo/readiness` remains safe;
- Recipe Session Alpha smoke still passes;
- forbidden-text checks cover product shell content.

Keep this offline and mock-only.

### 5. Add or update tests

Add deterministic tests for:

- product shell route exists;
- product shell has clear local product title;
- product shell includes Cookbook and AI workspace navigation;
- redirect routes behave as documented;
- readiness/provider metadata remains safe;
- missing fixture guidance is present or recoverable;
- product shell/static files avoid secret-like strings, raw local paths, raw prompts, and provider responses;
- existing `/demo` route remains available;
- mock smoke expectations match the documented acceptance checklist.

### 6. Review local product docs for consistency

Update:

- `docs/local-cookbook-ai-product-integration.md`;
- `docs/ai-ui-integration-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/recipe-session-alpha-acceptance-runbook.md` if relevant;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md`.

Ensure all docs agree that `/product` is the first local product URL to open.

### 7. Add a final local-product outbox report

Create:

```text
outbox/0030I-local-product-acceptance-and-demo-hardening-results.md
```

The outbox should summarize:

- product shell hardening;
- acceptance checklist created;
- smoke/test updates;
- local demo flow;
- known limitations;
- validation results;
- explicit non-goals;
- recommendation on whether AWS/platform planning can resume after this task.

## Acceptance Criteria

- `/product` is the canonical local product entry point.
- `/product` clearly links the upstream Cookbook app and AI workspace.
- Local startup guidance tells the operator exactly which command to run and which URL to open first.
- A local product acceptance checklist exists.
- Mock smoke validates the product shell and route behavior offline.
- Tests cover product shell, redirects/navigation, safe content, and preserved `/demo` behavior.
- Recipe Session Alpha local demo behavior remains intact.
- Normal validation remains offline and mock-only.
- No live OpenAI calls are required.
- No AWS/platform work is implemented in this task.
- No upstream Vanilla Cookbook vendoring or UI rewrite is added.
- No production write-back, production storage, public route exposure, auth, payment, provider-routing, secondary provider runtime, vector DB, embeddings, raw dataset, screenshot, browser automation, generated persistent index, or disk cache work is added.

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

- no AWS resource creation;
- no Terraform;
- no CDK;
- no CloudFormation;
- no DNS or Cloudflare changes;
- no production deployment;
- no production auth;
- no payment implementation;
- no public route exposure;
- no provider-routing changes;
- no secondary-provider runtime;
- no live OpenAI calls;
- no vector database;
- no embeddings;
- no upstream Vanilla Cookbook vendoring;
- no full upstream UI rewrite;
- no production database migrations;
- no persistent production memory;
- no screenshots;
- no browser automation;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-local-product-acceptance-and-demo-hardening-results.md

git commit -m "mailbox: complete task 0030I local product acceptance demo hardening"

git pull --rebase origin main

git push origin main
```
