# 0033S Local Save-to-Cookbook UI MVP

## Goal

Implement a local-only Save-to-Cookbook UI MVP that lets a user review an AI importer draft, run the existing dry-run candidate operation, and exercise the disabled-by-default local commit service behind explicit local gates.

This task may add local/internal sidecar routes only if they are disabled by default and cannot target production. It may add a local-only UI control in the AI demo/product shell only when the local backend gates are satisfied. It must not implement exposed/production Save-to-Cookbook, native upstream API writes, migrations, auth/SSO, AWS, Cloudflare, GitHub Actions, QMD, analytics, ads, payment, provider routing changes, or live OpenAI calls.

## Context

`0033J` designed the Save-to-Cookbook adapter flow: AI draft -> review/edit -> dry-run -> confirm -> Cookbook save.

`0033M` added the fixture adapter contract.

`0033N` added the disabled-by-default internal dry-run service.

`0033Q` proved the local disposable write readiness harness against `cookbook-local`, including backup/restore, deterministic serialization, synthetic ownership, read-after-write, duplicate/idempotency, failure rollback, and restoration.

`0033R` added `ai-api/app/cookbook_import_commit.py`, a disabled-by-default local commit service with explicit enablement, approval, runtime verification, loopback target, and synthetic ownership guards. It is not a route and uses an injected in-memory store for normal tests. Native upstream API integration remains future work.

## Hard boundaries

- Do not create a new task.
- Do not implement production Save-to-Cookbook.
- Do not add public production routes.
- Do not call the native upstream `POST /api/recipe` route unless a separate future task explicitly approves native core-app ownership/API integration.
- Do not mutate the Vanilla Cookbook database from UI/API code in this task.
- Do not replace the `0033Q` readiness harness as the approved path for disposable DB/write proof.
- Do not add database migrations.
- Do not inspect production data.
- Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
- Do not add auth, SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls.
- Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, row dumps, or browser artifacts.

## Required work

### 1. Read current implementation and docs

Read:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
outbox/0033R-local-save-to-cookbook-backend-integration-results.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
ai-api/app/local_save_readiness.py
ai-api/tests/test_cookbook_import_adapter.py
ai-api/tests/test_cookbook_import_dry_run.py
scripts/test-save-to-cookbook-local-readiness.ps1
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
```

Use actual filenames if they differ.

### 2. Add local-only API surface only if safely gated

If needed for the UI, add local/internal sidecar routes for:

```text
POST /adapter/recipes/import-candidate/dry-run
POST /adapter/recipes/import-candidate/local-commit
```

Route requirements:

- disabled by default;
- unavailable unless explicit non-secret local config enables them;
- local-only and loopback-only;
- must reject production/exposed/tunnel/non-loopback targets before any service call;
- must return safe status envelopes;
- must not call live OpenAI;
- must not call the upstream native `POST /api/recipe` route;
- must not write SQLite/uploads/filesystem directly;
- must use the existing dry-run and local commit service behavior;
- normal tests must remain offline and not require Docker.

If a route is too risky or inconsistent with the app architecture, keep the service-only boundary and document why the UI remains blocked.

### 3. Add local-only review/dry-run/save UI MVP

Update the AI demo/product shell so an AI importer result can show a local-only Save-to-Cookbook panel.

Expected flow:

```text
Run AI importer
View structured unsaved draft
Edit reviewable fields if existing UI architecture supports it
Run Save dry-run
Show mapped payload summary, field errors, warnings, duplicate/idempotency status
Require explicit confirmation for local save
Call local commit only when local gates are enabled
Show safe local result or safe unavailable message
Keep production/exposed save unavailable
```

UI requirements:

- label the recipe as an unsaved AI draft until committed;
- make the local-only nature obvious;
- show when Save-to-Cookbook is unavailable because local gates are disabled;
- never claim production save support;
- never show prompts, provider raw body, secrets, local paths, SQL dumps, stack traces, or provider debug output;
- do not store provider output as canonical recipe data;
- preserve existing importer, mock, and live-safe behavior;
- keep `/product/cookbook` and `/product/ai` behavior unchanged unless a clear local UI link is needed.

### 4. Tests

Add focused tests for:

```text
routes disabled by default, if routes are added
routes reject production/exposed/non-loopback targets
routes return safe envelopes
valid dry-run response is rendered by UI or service tests
invalid draft shows field errors
duplicate/idempotency status is surfaced safely
local commit requires explicit approval/local enablement
production/exposed mode keeps save unavailable
safe leakage checks exclude prompts, provider bodies, secrets, SQL dumps, stack traces, absolute local paths, tokens, env values
existing importer flow still works
normal tests do not require Docker or live OpenAI
```

If Playwright/UI tests are added, they must use mock/offline mode and must not require live OpenAI. Do not commit Playwright artifacts.

### 5. Docs

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly distinguish:

- dry-run fixture contract;
- local readiness harness;
- local backend commit service;
- local-only UI MVP;
- future native core-app adapter/API integration;
- future production/exposed Save-to-Cookbook support, which remains not implemented.

### 6. Outbox

Create:

```text
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
```

Summarize:

- routes added or why routes remained blocked;
- UI flow added or why UI remained blocked;
- local-only gate behavior;
- dry-run rendering behavior;
- local commit behavior;
- tests added;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance criteria

- Local-only UI MVP exists, or the task precisely documents why it remains blocked.
- If routes are added, they are disabled by default and reject production/exposed/non-loopback targets.
- UI never claims production save support.
- Dry-run result can be exercised from the UI path or a documented local-only path.
- Local commit service remains gated by explicit local enablement/approval.
- No upstream/native app DB write is performed by the UI/API code in this task.
- Existing importer/mock workflows remain working.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- No Save-to-Cookbook production path, public production route, migration, native upstream API write, auth/SSO/BYOS, analytics, ads, payment, AWS/platform work, Cloudflare work, provider routing change, QMD integration, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, row dumps, or browser artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1

& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py

& .\.venv\Scripts\python.exe -m pytest ai-api\tests

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

git diff --check

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

Optional UI validation, only if the local UI path is implemented and mock/offline:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

Optional local disposable write evidence remains the `0033Q` harness only:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-save-to-cookbook-local-readiness.ps1 -ApproveLocalWrite

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0033S-local-save-to-cookbook-ui-mvp-results.md

git commit -m "feat: add local save to cookbook ui mvp"

git pull --rebase origin main

git push origin main
```
