# 0033O Local Vanilla Cookbook Schema Discovery

## Goal

Perform read-only schema discovery against the verified local Vanilla Cookbook Docker runtime so future Save-to-Cookbook dry-run/write-back work can map AI importer candidates to the real upstream Cookbook storage model safely.

This is a discovery/reporting task only. Do not implement a Save-to-Cookbook button, commit endpoint, database write, migration, production integration, or public route in this task.

## Context

`0033J` defined the Save-to-Cookbook adapter design and required schema/compatibility discovery before any write implementation.

`0033L` verified the local disposable Vanilla Cookbook runtime with Docker Desktop running: `jt196/vanilla-cookbook:stable` started under the `cookbook-local` Compose project, bound to `127.0.0.1:3000`, returned HTTP 200, and did not start `cloudflared`.

`0033M` added a fixture-only in-memory adapter contract.

`0033N` added the disabled-by-default internal dry-run operation around the fixture adapter, but intentionally added no HTTP route because the core-app adapter/auth boundary is still not present.

The current blocker for a future disposable write/rollback test is the real upstream Vanilla Cookbook schema and/or supported create path.

## Required Work

### 1. Read current design and runtime docs

Read:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
outbox/0033L-local-vanilla-cookbook-runtime-verification-and-coder-asset-reuse-results.md
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

Use actual filenames if test/module names differ.

### 2. Start or verify local Vanilla Cookbook runtime

Use the repository local runtime scripts when possible:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
```

Confirm:

- Docker daemon is available;
- `cookbook-local` Compose project starts;
- only the local Vanilla Cookbook `app` service is running;
- no `cloudflared` container is running;
- `http://127.0.0.1:3000/` responds or has a precise recovery note;
- disposable DB/uploads remain under ignored `.local/vanilla-cookbook/` paths.

If Docker is unavailable, do not invent schema facts. Record the blocker and keep this task docs-only.

### 3. Read-only schema discovery

Inspect the local disposable Vanilla Cookbook runtime and mounted data read-only.

Allowed:

```text
inspect container metadata
inspect image/container filesystem read-only
inspect local disposable DB file metadata and schema
inspect SQLite tables, columns, indexes, foreign keys, triggers, and views
inspect Prisma/schema metadata if present inside the container/image
inspect package/app metadata that reveals model names or create/edit API shape
inspect localhost routes only enough to identify whether a native create/import API exists
record relative disposable paths such as .local/vanilla-cookbook/db when needed
```

Not allowed:

```text
no production database inspection
no production deployment inspection
no GitHub Actions/AWS/Cloudflare work
no production secrets
no copying or committing DB files
no modifying local DB rows
no writing synthetic recipes
no upload writes
no screenshots/traces/browser artifacts
no raw provider outputs/prompts
no local absolute paths in docs beyond safe relative repo paths
```

Prefer commands that are read-only, for example:

```bash
docker compose -f docker-compose.local.yml -p cookbook-local ps
docker compose -f docker-compose.local.yml -p cookbook-local exec app sh -lc 'find /app -maxdepth 4 -iname "schema.prisma" -o -iname "*.db" -o -iname "*.sqlite"'
docker compose -f docker-compose.local.yml -p cookbook-local exec app sh -lc 'find /app -maxdepth 5 -type f | grep -Ei "prisma|schema|route|api|recipe" | head -100'
```

Use SQLite read-only inspection if a disposable DB is present. Avoid write-capable opens when possible.

### 4. Create schema discovery report

Create:

```text
docs/local-vanilla-cookbook-schema-discovery.md
```

The report should cover:

```text
runtime inspected
image/container/app metadata found
DB file location and whether it exists
SQLite/Prisma schema facts discovered
recipe-related tables/models
ingredient/instruction/tag/source/upload relationships if discoverable
primary keys and generated IDs
required fields, defaults, nullability, unique constraints, foreign keys, indexes
whether recipes appear JSON/text/relational
whether ownership/user/account fields exist
whether draft/archive/delete/revision fields exist
whether media/upload references exist
whether a native create/edit API or route appears to exist
known unknowns
implications for the 0033M/0033N adapter contract
changes needed before disposable write/rollback testing
```

Be explicit about confidence:

```text
Observed fact
Inference
Unknown
Not inspected
```

Do not over-claim write behavior from schema alone.

### 5. Optional contract alignment notes

If clear schema facts are discovered, update docs and comments to note whether the existing candidate payload is likely sufficient or missing fields.

Do not change the adapter contract in a way that assumes write behavior unless the evidence is strong and tests remain fixture-only.

Possible safe updates:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/ai-schema-notes.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
README.md
```

### 6. Tests / validation

Add deterministic tests only if code changes are made. Normal validation must not require Docker or live OpenAI.

If a helper script is useful, it must be read-only and must not commit DB contents or local output artifacts.

Do not add a schema snapshot if it contains local paths, row data, private recipe contents, secrets, generated DB bytes, or uploads.

### 7. Outbox

Create:

```text
outbox/0033O-local-vanilla-cookbook-schema-discovery-results.md
```

The outbox should summarize:

```text
runtime availability
schema discovery method
schema facts discovered
known unknowns
impact on adapter contract
whether future disposable write/rollback testing is unblocked or still blocked
code/docs changed
validation results
explicit non-goals
```

## Acceptance Criteria

- Local Vanilla Cookbook schema discovery is attempted against the verified disposable runtime.
- Any discovered schema facts are documented with clear confidence labels.
- No production data or production deployment is inspected.
- No local DB rows are modified.
- No DB files/uploads/runtime artifacts are committed.
- No Save-to-Cookbook button, public route, commit endpoint, database write, migration, production integration, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
- Normal validation remains mock/offline and does not require Docker unless an explicitly optional local schema check is documented separately.
- The outbox clearly states whether Phase 3 disposable write/rollback testing is ready, partially ready, or blocked.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1

& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py

& .\.venv\Scripts\python.exe -m pytest ai-api\tests

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
git add docs README.md ai-api outbox/0033O-local-vanilla-cookbook-schema-discovery-results.md

git commit -m "docs: add local cookbook schema discovery"

git pull --rebase origin main

git push origin main
```
