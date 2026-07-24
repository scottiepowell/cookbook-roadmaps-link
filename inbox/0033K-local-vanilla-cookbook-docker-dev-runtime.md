# 0033K Local Vanilla Cookbook Docker Development Runtime

## Goal

Add a local development path for running the Vanilla Cookbook container without AWS, Cloudflare Tunnel, or GitHub Actions so Cookbook/AI integration work can be tested and verified entirely on the developer machine.

This task should make local Vanilla Cookbook availability explicit, repeatable, documented, and safe for future adapter work such as Save to Cookbook.

## Context

Manual testing after `0033I` clarified that Vanilla Cookbook is currently available through the production AWS/Cloudflare Tunnel deployment, not through a local running container. The product-shell link correction now supports a configurable `COOKBOOK_TARGET_URL`, but the integration work still needs a local Docker development runtime for the upstream Vanilla Cookbook surface.

Current repo state to account for:

- `docker-compose.yml` already defines an `app` service using `jt196/vanilla-cookbook:stable` and binding `127.0.0.1:3000:3000`.
- The same compose file also defines `cloudflared`, which should not be required for local development.
- The AI sidecar local launcher runs separately with `scripts/start-ai-demo-local.ps1` and points `/product/cookbook` at `COOKBOOK_TARGET_URL` or the local default.
- `0033I` intentionally did not proxy or rewrite the upstream Vanilla Cookbook app.
- `0033J` Save-to-Cookbook adapter design should wait until a disposable local Vanilla Cookbook runtime is available for schema/discovery work.

## Required Work

### 1. Inspect current local runtime/configuration

Read:

```text
docker-compose.yml
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
outbox/0033I-product-cookbook-link-target-correction-results.md
inbox/0033J-ai-importer-save-to-cookbook-adapter-design.md
```

Also inspect `.gitignore` and any existing `db/`, `uploads/`, compose, or local-start scripts.

### 2. Add a local-only Vanilla Cookbook Docker path

Provide a local development command path that starts only the Vanilla Cookbook container and does not require Cloudflare Tunnel, AWS, GitHub Actions, or production secrets.

Preferred shape, if it fits the existing repo:

```text
scripts/start-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
```

or a clearly documented compose profile/override such as:

```text
docker-compose.local.yml
```

The solution should make it obvious how to run:

```text
Vanilla Cookbook: http://127.0.0.1:3000/
AI product shell: http://127.0.0.1:8000/product
AI workspace: http://127.0.0.1:8000/demo
```

Requirements:

- Do not require `CLOUDFLARE_TUNNEL_TOKEN` for local development.
- Do not start `cloudflared` for local development.
- Do not require AWS, GitHub Actions, or external deployment to test the product shell.
- Keep Vanilla Cookbook bound to localhost only.
- Keep local database/uploads under ignored local paths.
- Do not commit local DBs, uploads, generated artifacts, screenshots, traces, secrets, or environment values.
- Preserve the current production/exposed deployment compose behavior unless a safer profile split is required and documented.

### 3. Make local sidecar integration easy

Document the intended two-terminal local workflow:

```powershell
# Terminal 1: start local Vanilla Cookbook only
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

# Terminal 2: start AI sidecar in mock mode
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

Also document the optional manual live sidecar workflow, but do not make live calls during validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 500 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

### 4. Add local readiness/check guidance

Add a deterministic local check script or documented command sequence that verifies:

- Docker is available;
- Vanilla Cookbook container starts;
- `http://127.0.0.1:3000/` responds;
- `/product/cookbook` targets the local Cookbook URL when `COOKBOOK_TARGET_URL` is unset or set to local;
- `/product/ai` still targets `/demo`;
- `cloudflared` is not required for the local path.

If a full HTTP readiness check for Vanilla Cookbook is not reliable, document the limitation honestly and use the best safe observable check available, such as container status plus port binding.

### 5. Update docs

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

Docs must clearly distinguish:

- local Vanilla Cookbook Docker runtime;
- production/exposed Cookbook URL;
- Cloudflare Tunnel production/exposed path;
- local AI sidecar path;
- when to use `COOKBOOK_TARGET_URL`;
- how to stop local containers;
- why `0033J` Save-to-Cookbook adapter work should use disposable local data first.

### 6. Add or update tests

Add deterministic tests for any new scripts/configuration where practical.

Cover at minimum:

- local script/compose command does not require `CLOUDFLARE_TUNNEL_TOKEN`;
- local script/compose path does not start `cloudflared`;
- configured local Cookbook URL remains localhost-only by default;
- production/exposed target remains configurable through `COOKBOOK_TARGET_URL`;
- no secrets/local env values are printed or committed;
- existing mock/offline validation remains unchanged.

### 7. Add outbox report

Create:

```text
outbox/0033K-local-vanilla-cookbook-docker-dev-runtime-results.md
```

The outbox should summarize:

- local Docker runtime path added;
- how to start/stop Vanilla Cookbook locally;
- how to run the AI sidecar against it;
- Cloudflare/AWS/GitHub Actions not required;
- validation results;
- any limitations;
- explicit non-goals.

## Acceptance Criteria

- There is a documented local development path for running Vanilla Cookbook on `127.0.0.1:3000`.
- Local development does not require Cloudflare Tunnel, AWS, GitHub Actions, or production secrets.
- Local development does not start `cloudflared` by default.
- The AI product shell can be pointed at local Vanilla Cookbook for integration testing.
- Local DB/uploads/generated runtime data are ignored and not committed.
- Docs explain how this unblocks `0033J` Save-to-Cookbook adapter design and future disposable write tests.
- No Save-to-Cookbook write path is implemented in this task.
- No live OpenAI call is made during normal validation.
- No secrets, prompts, provider outputs, screenshots, traces, local env values, raw datasets, generated indexes, local DBs, or uploads are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

Also run the new local Vanilla Cookbook start/check path if Docker is available. If Docker is unavailable, record that limitation honestly in the outbox.

Do not run live OpenAI during normal validation.

## Commit

```bash
git add docker-compose*.yml scripts docs README.md .gitignore outbox/0033K-local-vanilla-cookbook-docker-dev-runtime-results.md
git commit -m "dev: add local vanilla cookbook runtime"
git pull --rebase origin main
git push origin main
```
