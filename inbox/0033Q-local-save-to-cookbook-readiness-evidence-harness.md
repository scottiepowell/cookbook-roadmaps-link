# 0033Q Local Save-to-Cookbook Readiness Evidence Harness

## Goal

Implement the local-only, explicitly approved readiness evidence harness described by `0033P`, so the project can prove or precisely block Phase 3 disposable Save-to-Cookbook write/rollback testing.

This task is the separate approval required by `0033P` for a local disposable harness. It may implement and run a local-only harness against the ignored `cookbook-local` runtime to generate the missing readiness evidence, but it must not implement a product Save-to-Cookbook button, public route, production write-back, migration, or exposed deployment integration.

## Context

`0033P` completed successfully but intentionally left Phase 3 blocked until a future implementation task proves the missing evidence. This task is that future implementation task.

The missing evidence is:

- exact ingredient/direction serialization accepted by the normal local Cookbook path;
- synthetic ownership setup and teardown;
- backup/restore execution for ignored local DB/uploads;
- transaction/cleanup behavior;
- duplicate/idempotency behavior;
- failure injection;
- local read-after-write verification.

Use the narrow first-write scope from `docs/save-to-cookbook-schema-informed-write-plan.md`: one synthetic local user, one synthetic recipe, deterministic text ingredients/directions, string servings, safe source/provenance, no categories, no media/uploads, and no embeddings unless the upstream app unavoidably performs them and the harness handles cleanup safely.

## Required Work

### 1. Read current design and evidence plan

Read:

```text
docs/save-to-cookbook-schema-informed-write-plan.md
outbox/0033P-save-to-cookbook-schema-informed-write-plan-results.md
docs/local-vanilla-cookbook-schema-discovery.md
outbox/0033O-local-vanilla-cookbook-schema-discovery-results.md
docs/ai-importer-save-to-cookbook-adapter-design.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md
outbox/0033N-ai-importer-save-dry-run-candidate-operation-results.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/tests/test_cookbook_import_adapter.py
ai-api/tests/test_cookbook_import_dry_run.py
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
.gitignore
```

Use actual filenames if they differ.

### 2. Implement a local-only readiness harness

Add a script such as:

```text
scripts/test-save-to-cookbook-local-readiness.ps1
```

The harness must:

- require an explicit approval switch, for example `-ApproveLocalWrite`;
- require the `cookbook-local` Compose project;
- require a localhost-only target such as `http://127.0.0.1:3000/`;
- refuse `https://cookbook.roadmaps.link` and any non-loopback target;
- refuse AWS, GitHub Actions, Cloudflare, tunnel, or production/deployment inputs;
- verify ignored local DB/upload mounts are the only write scope;
- create and verify a backup before any write;
- use only synthetic local user and synthetic recipe data;
- write at most one synthetic recipe candidate in the normal success path;
- verify local read-after-write safely;
- exercise duplicate/idempotency behavior without unbounded duplicate writes;
- exercise at least one failure/restore path;
- restore or clean the disposable DB/uploads before exit, including failures;
- print only safe statuses and opaque generated local IDs;
- never print recipe private content, SQL dumps, stack traces, absolute local paths, secrets, tokens, prompts, provider output, or environment values.

The harness must not call a live AI provider and must not require `OPENAI_API_KEY`.

### 3. Keep production and product surfaces untouched

Do not add:

```text
Save-to-Cookbook product button
public route
production commit endpoint
production write-back
Cloudflare/AWS/GitHub Actions integration
database migration
production data inspection
```

If adding internal helper code, keep it local-only, deterministic, and tested offline. Normal unit tests must not require Docker or live OpenAI.

### 4. Prove or precisely block the missing evidence

The harness should attempt to prove:

```text
ingredient/direction serialization round-trip readability
synthetic ownership setup/teardown
backup/restore execution
transaction/cleanup behavior
duplicate/idempotency behavior
failure injection
local read-after-write verification
```

If an item cannot be proven safely, stop and report a precise blocker rather than weakening the guardrails.

### 5. Update docs

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

Docs should explain whether Phase 3 is now unblocked, partially unblocked, or still blocked.

### 6. Add outbox report

Create:

```text
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
```

The outbox must summarize:

- harness implemented;
- approval and local-only guards;
- write scope actually attempted;
- synthetic user behavior;
- serialization/read-after-write result;
- backup/restore result;
- duplicate/idempotency result;
- failure-injection result;
- cleanup/restoration result;
- whether Phase 3 is now ready, partially ready, or still blocked;
- docs/code changed;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A local-only readiness evidence harness exists.
- It refuses to run without explicit approval.
- It refuses production and exposed targets.
- It runs only against the disposable `cookbook-local` runtime.
- It creates a backup before any write and restores/cleans up afterward.
- It uses only synthetic local user/recipe data.
- It proves or precisely blocks ingredient/direction serialization, synthetic ownership, backup/restore, duplicate/idempotency, failure injection, and local read-after-write verification.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- No Save-to-Cookbook button, public route, production write-back, migration, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, row dumps, or browser artifacts are committed.

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

Run local readiness verification only after safe preflight:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-save-to-cookbook-local-readiness.ps1 -ApproveLocalWrite

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md

git commit -m "test: add local save to cookbook readiness harness"

git pull --rebase origin main

git push origin main
```
