# 0033L Local Vanilla Cookbook Runtime Verification And Coder Asset Reuse

## Goal

Verify the local Vanilla Cookbook Docker development runtime now that Docker Desktop is running, and inspect any existing local Coder/Vanilla Cookbook Docker assets for reusable non-secret patterns that can improve the repo's local development workflow.

This is a local-dev verification and hardening task. Do not implement Save to Cookbook in this task.

## Context

`0033K` added the local runtime scaffolding, including `docker-compose.local.yml` plus start/check/stop scripts for a `cookbook-local` Compose project. However, validation could not actually start the upstream container because Docker Desktop was not running. The operator has now started Docker Desktop.

The operator also reports prior local development work for Vanilla Cookbook under a Coder image/images directory. Codex may be able to see those local files from the development machine. Treat those assets as read-only reference material unless they are inside this repository and intentionally tracked.

## Required Work

### 1. Read current local runtime work

Read:

```text
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
docker-compose.yml
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
outbox/0033K-local-vanilla-cookbook-docker-dev-runtime-results.md
inbox/0033J-ai-importer-save-to-cookbook-adapter-design.md
.gitignore
```

### 2. Verify Docker Desktop path

With Docker Desktop running, run and record safe results from the local runtime path:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
```

Confirm whether:

- Docker daemon is available;
- the `cookbook-local` Compose project starts;
- only the local Vanilla Cookbook app is started;
- `cloudflared` is not started;
- `http://127.0.0.1:3000/` responds or provides a clear observable status;
- disposable DB/uploads remain under ignored `.local/vanilla-cookbook/` paths;
- no production `.env`, AWS, GitHub Actions, or Cloudflare Tunnel token is required.

If startup fails, diagnose and fix the local-dev scripts/config without using production infrastructure.

### 3. Verify AI product handoff against local Vanilla Cookbook

Start the AI sidecar in mock/offline mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

Then verify with safe local checks:

- `http://127.0.0.1:8000/product` loads;
- `/product/cookbook` targets `http://127.0.0.1:3000/` when `COOKBOOK_TARGET_URL` is unset or local;
- `/product/ai` still targets `/demo`;
- the product shell gives clear recovery guidance if Vanilla Cookbook is stopped;
- no live OpenAI call is made.

Use a browser manually if helpful, but do not commit screenshots, traces, videos, or browser artifacts.

### 4. Inspect prior Coder/Vanilla Cookbook Docker assets read-only

Search the local development machine read-only for prior Coder image or Vanilla Cookbook Docker work. Likely search terms/locations may include:

```text
coder
coder-images
images
vanilla-cookbook
cookbook
Dockerfile
docker-compose
```

Possible roots to inspect if accessible:

```text
C:\Users\scott
C:\Users\scott\coder
C:\Users\scott\images
C:\Users\scott\projects
/home/scott
/home/scott/projects
```

Rules:

- Do not copy or commit local `.env` files, secrets, tokens, database files, uploads, browser artifacts, private notes, or generated runtime data.
- Do not commit external local files wholesale.
- If reusable Docker/Compose/script patterns exist, review them and port only minimal non-secret, project-appropriate logic into this repo.
- If the prior Coder image work contains useful commands or environment assumptions, summarize those assumptions in docs without exposing private values.
- If nothing reusable is found or local paths are inaccessible, state that honestly in the outbox.

### 5. Harden local dev path if needed

Based on actual Docker Desktop verification and any reusable Coder patterns, make the smallest safe improvements to local dev scripts/docs.

Potential improvements, only if needed:

- clearer Docker Desktop not running detection;
- clearer Docker daemon readiness message;
- clearer image pull guidance for `jt196/vanilla-cookbook:stable`;
- port 3000 conflict detection and recovery command;
- Compose project naming clarity;
- explicit `cloudflared` non-start assertion;
- documented startup order for Vanilla Cookbook + AI sidecar;
- documented stop/reset commands for disposable data;
- local troubleshooting notes for Windows Docker Desktop.

Do not add production deployment behavior.

### 6. Update docs

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly say:

- Docker Desktop must be running for the local Vanilla Cookbook path;
- the local path starts only Vanilla Cookbook, not Cloudflare;
- production/exposed Cookbook is separate from local dev;
- `0033J` Save-to-Cookbook adapter design should use this local disposable runtime for schema discovery and later write/rollback tests;
- prior Coder image assets, if used, were treated as read-only references and no secrets/local data were committed.

### 7. Add outbox report

Create:

```text
outbox/0033L-local-vanilla-cookbook-runtime-verification-and-coder-asset-reuse-results.md
```

The outbox should summarize:

- Docker Desktop/runtime verification result;
- whether the Vanilla Cookbook container started;
- whether `http://127.0.0.1:3000/` responded;
- whether cloudflared stayed off;
- AI product handoff result;
- prior Coder/Vanilla Cookbook Docker asset search result;
- reusable patterns found or not found;
- code/docs changed;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Local Vanilla Cookbook runtime is actually tested with Docker Desktop running, or any remaining blocker is documented with concrete recovery steps.
- `cloudflared` is not required and is not started for the local dev path.
- `http://127.0.0.1:3000/` is verified or a precise failure/recovery is documented.
- AI product shell can target the local Vanilla Cookbook runtime for integration testing.
- Prior local Coder/Vanilla Cookbook Docker assets are inspected read-only if accessible.
- Any reused logic is minimal, non-secret, and committed only as repo-appropriate scripts/docs/config.
- Local DB/uploads/generated runtime data remain ignored and uncommitted.
- No Save-to-Cookbook write path is implemented.
- No live OpenAI call is made during normal validation.
- No secrets, prompts, provider outputs, screenshots, traces, local env values, raw datasets, generated indexes, local DBs, uploads, or browser artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1

& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

git diff --check

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

Stop local Vanilla Cookbook when finished:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI during normal validation.

## Commit

```bash
git add docker-compose*.yml scripts docs README.md .gitignore outbox/0033L-local-vanilla-cookbook-runtime-verification-and-coder-asset-reuse-results.md

git commit -m "dev: verify local vanilla cookbook runtime"

git pull --rebase origin main

git push origin main
```
