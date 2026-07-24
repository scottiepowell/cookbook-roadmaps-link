# 0033R Local Save-to-Cookbook Backend Integration

## Goal

Implement the first local-only backend integration for saving a reviewed AI importer candidate into the disposable `cookbook-local` Vanilla Cookbook runtime.

This task may add a disabled-by-default local backend commit service and, only if it can be safely gated, a local-only internal route for future UI use. It must not add a production save path, exposed route behavior, product button, migration, auth/SSO integration, AWS/Cloudflare/GitHub Actions work, or live provider call.

## Context

`0033Q` completed the local readiness evidence harness. It proved deterministic ingredient/direction serialization, invariant servings text, synthetic ownership, local read-after-write, duplicate/replay/conflict decisions, an invalid-owner rollback path, and DB/upload restore for the disposable local runtime.

`0033Q` still intentionally did not implement a Save-to-Cookbook button, public route, commit endpoint, native authenticated core-app adapter, production write-back, migration, or UI/API integration. Its outbox says the next implementation task must separately review native adapter ownership, API transaction behavior, and production approval boundaries before mutation.

## Required Work

### 1. Read current evidence and code

Read:

```text
docs/save-to-cookbook-schema-informed-write-plan.md
outbox/0033P-save-to-cookbook-schema-informed-write-plan-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/local-vanilla-cookbook-schema-discovery.md
outbox/0033O-local-vanilla-cookbook-schema-discovery-results.md
docs/ai-importer-save-to-cookbook-adapter-design.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md
outbox/0033N-ai-importer-save-dry-run-candidate-operation-results.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/local_save_readiness.py
ai-api/tests/test_cookbook_import_adapter.py
ai-api/tests/test_cookbook_import_dry_run.py
scripts/test-save-to-cookbook-local-readiness.ps1
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
```

Use actual filenames if they differ.

### 2. Review native adapter/API boundary locally

Before implementing any commit path, review the native local Vanilla Cookbook create/update ownership and transaction behavior using only the disposable `cookbook-local` runtime and source/schema facts already discovered.

Allowed:

- read local app source/routes/schema;
- inspect local container metadata;
- run local app on `127.0.0.1:3000`;
- use synthetic local data only;
- document whether native API usage is safe for a local MVP or whether the local service must use the already-proven disposable DB harness boundary.

Not allowed:

- production data inspection;
- production deployment inspection;
- exposed URL testing;
- real user data;
- real auth sessions;
- secrets/tokens;
- screenshots/traces/artifacts;
- live provider calls.

If native API auth/session behavior is unclear or unsafe, do not force it. Use the local-only DB-backed harness/service boundary and document why native API integration remains future work.

### 3. Implement local-only backend commit service

Add a backend service that consumes the same validated candidate/dry-run shape from `0033M`/`0033N` and performs a local-only commit into the disposable runtime when explicitly enabled.

Required service behavior:

- disabled by default;
- requires explicit local enablement/approval in code path;
- requires `cookbook-local` runtime and loopback target;
- refuses exposed/production URLs, Cloudflare/tunnel targets, AWS, GitHub Actions, and non-loopback targets before any write;
- uses synthetic/local owner policy only;
- uses schema-informed serialization from `0033P`/`0033Q`;
- excludes categories, photos/uploads/media, and embeddings from first local MVP unless unavoidable and safely handled;
- performs at most one successful write per request/idempotency key;
- returns safe status envelope with canonical local ID/deep-link if available;
- returns duplicate/idempotency/conflict information without unbounded duplicate writes;
- returns safe validation/guard errors;
- does not print or return prompts, provider output, recipe private content beyond user-submitted candidate fields already being reviewed, SQL dumps, absolute local paths, secrets, tokens, or environment values.

Implementation may use helper functions/classes from `local_save_readiness.py` if they are cleanly separable from the test harness. Keep test-only code and runtime service code clearly separated.

### 4. Route policy

Prefer service functions plus tests first.

If adding an HTTP route is necessary for the next UI task, it must be:

- disabled by default;
- local-only;
- unavailable for production/exposed targets;
- guarded by explicit non-secret local setting;
- safe to call only when `cookbook-local` and loopback target are verified;
- documented as not production auth or public save support.

Do not add a production/public commit endpoint.

### 5. Tests

Add focused offline tests for:

```text
commit service disabled by default
missing approval/local enablement refuses before write
production/exposed target refusal
non-loopback target refusal
mapping/serialization matches 0033Q evidence
synthetic owner policy is local-only
valid candidate produces a safe local commit plan/result using fake or temp local store
duplicate/idempotency replay/conflict behavior
unsafe payload/unknown fields return safe errors
safe envelope excludes secrets, prompts, provider bodies, SQL dumps, absolute local paths, tokens, and environment values
normal tests do not require Docker or live OpenAI
```

Add a separate optional local Docker verification path only if needed; normal repository tests must remain mock/offline.

### 6. Docs

Update as appropriate:

```text
README.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-schema-notes.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly distinguish:

- fixture dry-run contract;
- local readiness harness;
- local-only commit service;
- future UI button;
- future native authenticated core-app adapter;
- production/exposed save support, which remains not implemented.

### 7. Outbox

Create:

```text
outbox/0033R-local-save-to-cookbook-backend-integration-results.md
```

Summarize:

- native API/ownership review result;
- backend service/route shape;
- local-only guardrails;
- serialization and synthetic owner behavior;
- duplicate/idempotency behavior;
- write/restore or no-write test behavior;
- tests added;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A disabled-by-default local-only backend commit service exists, or the task precisely documents why it remains blocked after native boundary review.
- The service cannot target production/exposed URLs or non-loopback targets.
- The service requires explicit local approval/enablement before any write.
- The service uses only disposable local runtime/synthetic ownership semantics.
- The service preserves existing `0033M`/`0033N` dry-run behavior.
- The service uses serialization and safety evidence from `0033P`/`0033Q`.
- Focused tests cover disabled, guard refusal, valid local behavior, duplicate/idempotency, safe errors, and leakage boundaries.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- No Save-to-Cookbook product button, production commit endpoint, migration, production write-back, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, Cloudflare work, provider routing change, QMD integration, or live call is added.
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

Optional local verification, only after safe preflight and if a local commit path is implemented:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-save-to-cookbook-local-readiness.ps1 -ApproveLocalWrite

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0033R-local-save-to-cookbook-backend-integration-results.md

git commit -m "feat: add local save to cookbook backend integration"

git pull --rebase origin main

git push origin main
```
