# 0033N AI Importer Save Dry-Run Candidate Operation

## Goal

Implement a local/internal **dry-run candidate operation** for the future Save-to-Cookbook flow, using the fixture-only adapter contract from `0033M`, without writing to Vanilla Cookbook storage.

This is Phase 2 of the Save-to-Cookbook path. It may expose an internal/local-only dry-run surface if safely gated, but it must not implement a commit operation, runtime save button, public production route, or database mutation.

## Context

`0033J` defined the future flow:

```text
AI draft -> review/edit -> dry-run validation -> explicit confirmation -> Cookbook save -> canonical recipe view
```

`0033M` added a pure in-memory adapter contract in `ai-api/app/cookbook_import_adapter.py` with focused tests in `ai-api/tests/test_cookbook_import_adapter.py`. The contract maps validated importer drafts into candidate payloads and returns safe field errors, warnings, duplicate signals, contract/schema versions, and idempotency metadata, without HTTP, SQLite, filesystem, provider, or authentication dependencies.

The next safe step is a no-write dry-run operation that lets the importer UI/backend exercise mapping and validation as an operation, while keeping commit/write behavior disabled.

## Required Work

### 1. Read current design and contract work

Read:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md
ai-api/app/cookbook_import_adapter.py
ai-api/tests/test_cookbook_import_adapter.py
ai-api/app/**import*
ai-api/app/**recipe*
ai-api/tests/**import*
ai-api/tests/**recipe*
docs/ai-schema-notes.md
docs/local-cookbook-ai-product-integration.md
```

Use actual filenames if globbing differs.

### 2. Add no-write dry-run operation

Implement the smallest safe operation layer around the fixture adapter.

Preferred behavior:

- accepts a validated AI importer draft/candidate payload;
- invokes the fixture adapter dry-run mapping;
- returns the adapter's dry-run result in a stable response envelope;
- returns field-level validation errors and warnings;
- returns duplicate and idempotency metadata;
- includes contract/schema version fields;
- never writes to SQLite, uploads, filesystem, or Vanilla Cookbook storage;
- never contacts production;
- never requires live OpenAI;
- never stores prompts, provider bodies, secrets, local paths, tokens, or raw provider output.

If adding an HTTP route, it must be local/internal-only and clearly unavailable for production/exposed targets. Prefer a route name consistent with the design such as:

```text
POST /adapter/recipes/import-candidate/dry-run
```

If the current app architecture makes a route too risky, implement a service function and tests only, and document the reason.

Do not add:

```text
POST /adapter/recipes/import-candidate/{id}/commit
Save button
production write endpoint
DB write path
public route exposure
```

### 3. Gate the operation safely

The dry-run operation must be safe by default. Choose the smallest repo-consistent gate.

Acceptable gate patterns:

- local/dev-only setting;
- existing operator/local gate;
- disabled unless explicit non-secret config enables adapter dry-run;
- route marked unavailable when target is production/exposed.

The gate must not require or expose secrets. It must produce safe errors when disabled.

### 4. Add tests

Add focused deterministic tests for:

```text
valid importer draft dry-runs to mapped candidate payload
invalid candidate returns safe field errors
unsafe source URL returns safe field error/warning
unknown fields are rejected or explicitly ignored by contract
schema/contract version mismatch returns safe error
duplicate fixture returns duplicate signal
idempotent replay returns same dry-run result
idempotency key reuse conflict returns safe conflict metadata
operation disabled/gated state returns safe unavailable response if a route/gate is added
operation response contains no prompt, provider body, key, local path, token, raw provider output, or secret-like value
no database, upload, or filesystem write occurs
normal mock/offline validation remains deterministic
```

Normal tests must not require Docker Desktop, a running Vanilla Cookbook container, or live OpenAI.

### 5. Update docs

Update as appropriate:

```text
README.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/ai-schema-notes.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs should explain:

- this is Phase 2 dry-run candidate operation;
- the operation does not write to Vanilla Cookbook;
- commit/save remains unavailable;
- the dry-run result is the prerequisite for a future local-only review UI;
- Docker/local Vanilla Cookbook is not required for normal dry-run tests;
- future Phase 3 disposable write/rollback tests must still use `cookbook-local`.

### 6. Add outbox report

Create:

```text
outbox/0033N-ai-importer-save-dry-run-candidate-operation-results.md
```

The outbox should summarize:

- dry-run operation added;
- route/service shape;
- gate behavior;
- mapping/validation/duplicate/idempotency behavior;
- no-write guarantees;
- tests added;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A no-write dry-run candidate operation exists around the `0033M` fixture adapter contract.
- The operation returns mapped payloads, field errors, warnings, duplicate signals, idempotency metadata, and contract/schema versions.
- The operation is gated safely if exposed through HTTP.
- The operation does not write to Vanilla Cookbook DB, uploads, filesystem, or production targets.
- No Save-to-Cookbook button or commit operation is implemented.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- Focused tests cover valid, invalid, duplicate, idempotent, disabled/gated if applicable, and safe-envelope cases.
- No public production route, database mutation, production write-back, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, local DBs, uploads, or browser artifacts are committed.

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

Do not run live OpenAI during normal validation.

## Commit

```bash
git add ai-api docs README.md outbox/0033N-ai-importer-save-dry-run-candidate-operation-results.md

git commit -m "feat: add save adapter dry-run operation"

git pull --rebase origin main

git push origin main
```