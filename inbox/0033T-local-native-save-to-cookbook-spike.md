# 0033T Local Native Save-to-Cookbook Spike

## Goal

Close the remaining gap between the local UI MVP and a real local Cookbook save by attempting a strictly local-only native save spike against the disposable `cookbook-local` Vanilla Cookbook runtime.

This task may implement a disabled-by-default local native save adapter only if the native ownership/session/API path can be proven safe with synthetic local data, loopback-only guards, and backup/restore evidence. If the native path cannot be proven safely, stop and document the precise blocker.

## Context

`0033S` added a local-only importer review panel plus disabled-by-default dry-run and local-commit routes. Those routes are internal, gated, and safe, but the local commit path delegates to the in-memory `0033R` service. It does **not** write SQLite, uploads, files, or the upstream Vanilla Cookbook app.

`0033Q` remains the approved disposable DB/write proof path. It proved one synthetic local write, deterministic serialization, synthetic ownership, local read-after-write, duplicate/idempotency behavior, rollback, and restore under the ignored local runtime paths.

The next product gap is a real local save that makes the recipe appear in the local Vanilla Cookbook app while preserving all local-only/disposable guardrails.

## Hard boundaries

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not add public production routes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not add database migrations.
Do not add SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, row dumps, browser artifacts, cookies, auth tokens, or session values.

## Required reading

Read first:

```text
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
outbox/0033R-local-save-to-cookbook-backend-integration-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
outbox/0033P-save-to-cookbook-schema-informed-write-plan-results.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
ai-api/app/local_save_readiness.py
scripts/test-save-to-cookbook-local-readiness.ps1
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
```

Also inspect local upstream app source inside the disposable container/image only as needed for native auth/session/API behavior:

```text
POST /api/recipe
related auth/session helpers
Prisma recipe create path
media/upload/embedding behavior
CSRF/session requirements if present
```

## Phase 1: native ownership/API review

Start or verify the local runtime:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
```

Review whether a native local-only save path can safely use the upstream authenticated `POST /api/recipe` route or an equivalent core-owned local service boundary.

Allowed:

```text
read local container/source files
inspect local schema/route/auth code
use synthetic local data only
use loopback-only HTTP
use ignored disposable DB/uploads
create backup/restore points during approved local verification
```

Not allowed:

```text
production data or exposed deployment
real local user accounts or existing sessions
secret/token/cookie output
raw row dumps or recipe contents
media/upload/image fetching unless explicitly proven disabled
live AI provider calls
```

If auth/session behavior requires real user data, real browser sessions, secrets, or unsafe token handling, do not implement native save. Document the blocker.

## Phase 2: implement only if safe

If Phase 1 proves a safe local native path, implement the smallest local-only native save adapter.

Required behavior:

- disabled by default;
- requires explicit local enablement and approval;
- requires `cookbook-local` Compose project;
- requires loopback target only;
- refuses exposed, production, tunnel, AWS, GitHub Actions, Cloudflare, and non-loopback targets before any write;
- uses only synthetic local user/ownership setup;
- uses the deterministic serialization from `0033P`/`0033Q`;
- excludes categories, media/uploads, remote image fetches, and embeddings from the first native save path unless they are proven disabled or safely bypassed;
- writes at most one reviewed candidate per approved local commit request;
- verifies local read-after-write using safe IDs/status only;
- preserves duplicate/idempotency protections or reports precise limitations;
- returns safe envelopes only;
- never returns prompts, provider bodies, secrets, SQL dumps, stack traces, absolute local paths, cookies, auth tokens, session values, or environment values.

Prefer a separate service module, for example:

```text
ai-api/app/cookbook_native_local_save.py
```

Only wire it to the existing local UI/route if the same guards can be preserved end-to-end. If the route wiring is unsafe, keep the service and document the UI wiring blocker.

## Phase 3: local verification

If a native local save path is implemented, add a local verification script or extend an existing local script so it can:

- start/check `cookbook-local`;
- back up DB/uploads;
- enable only local native save mode;
- submit one synthetic reviewed candidate;
- verify it appears in the local Cookbook app/API through safe ID/status checks;
- verify duplicate/idempotency behavior;
- exercise at least one failure path;
- restore DB/uploads before exit;
- stop local runtime when requested.

Normal repository tests must remain offline and must not require Docker or live OpenAI.

## Tests

Add focused offline tests for any new code:

```text
disabled by default
missing approval refuses before write
production/exposed/non-loopback target refusal
unsafe native auth/session conditions block safely
serialization uses 0033P/0033Q rules
synthetic ownership is required
media/categories/embeddings excluded
safe envelope leakage checks
idempotency/duplicate handling or explicit limitation
normal tests do not require Docker or live OpenAI
```

Add optional Docker/local verification only as a separate script/manual validation path.

## Documentation

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly distinguish:

- in-memory local UI MVP from `0033S`;
- disposable DB/write proof from `0033Q`;
- any new local native save spike from this task;
- future production/exposed Save-to-Cookbook, which remains not implemented.

## Outbox

Create:

```text
outbox/0033T-local-native-save-to-cookbook-spike-results.md
```

Summarize:

```text
native ownership/API review result
whether native local save was implemented or blocked
service/route/script shape
local-only guards
serialization and synthetic ownership behavior
read-after-write result
backup/restore result
duplicate/idempotency behavior
failure handling
tests added
docs updated
validation results
explicit non-goals
```

## Acceptance criteria

- Native local save path is either implemented safely or precisely blocked with evidence.
- No production/exposed target can be used.
- No production data is inspected or modified.
- If implemented, the path is disabled by default and requires explicit local approval.
- If implemented, it uses only `cookbook-local`, loopback, synthetic data, and disposable backup/restore.
- If implemented, one reviewed synthetic candidate can be saved and verified locally, or the precise runtime blocker is documented.
- Existing dry-run, in-memory commit, importer, and mock workflows remain working.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- No Save-to-Cookbook production path, public production route, migration, SSO/BYOS, analytics, ads, payment, AWS/platform work, Cloudflare work, provider routing change, QMD integration, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, row dumps, cookies, auth tokens, session values, or browser artifacts are committed.

## Validation

Run normal validation:

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

Optional local verification, only if a native local save path is implemented:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
# run the approved local native save verification script added by this task
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0033T-local-native-save-to-cookbook-spike-results.md
git commit -m "feat: spike local native save to cookbook"
git pull --rebase origin main
git push origin main
```
