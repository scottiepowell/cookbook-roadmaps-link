# 0033M AI Importer Save Adapter Fixture Contract

## Goal

Implement the first safe technical step after the `0033J` Save-to-Cookbook design: a local fixture adapter contract and schema-discovery note for the future **Save to Cookbook** path.

This task must not write to the Vanilla Cookbook database. It should create a fake/in-memory adapter contract that maps validated AI importer drafts into a candidate Cookbook payload, returns validation errors and duplicate/idempotency signals, and can be tested without a running production target.

## Context

`0033J` defined the future flow:

```text
AI draft -> review/edit -> dry-run validation -> explicit confirmation -> Cookbook save -> canonical recipe view
```

It also defined phases:

- Phase 1: local fixture adapter contract with no Vanilla DB writes;
- Phase 2: dry-run candidate operation that never writes;
- Phase 3: disposable local write/rollback test;
- Phase 4: local-only review UI;
- Phase 5: reviewed production path.

`0033K` and `0033L` verified the disposable local Vanilla Cookbook runtime at `http://127.0.0.1:3000/`, with ignored `.local/vanilla-cookbook/` DB/uploads and no `cloudflared`.

## Required Work

### 1. Read current design/runtime docs

Read:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
docs/cookbook-ai-plugin-adapter-architecture-adr.md
docs/local-cookbook-ai-product-integration.md
outbox/0033L-local-vanilla-cookbook-runtime-verification-and-coder-asset-reuse-results.md
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
ai-api/app/**import*
ai-api/app/**recipe*
ai-api/tests/**import*
ai-api/tests/**recipe*
docs/ai-schema-notes.md
```

Use actual filenames if globbing differs.

### 2. Inspect local Vanilla Cookbook schema read-only if available

If Docker Desktop and the local `cookbook-local` runtime are available, inspect only safe schema facts needed for adapter planning.

Allowed:

- container status and bind mount layout;
- disposable local DB file location under `.local/vanilla-cookbook/db`;
- table names, column names, nullability, indexes, foreign keys, and Prisma/SQLite metadata if available;
- whether recipe/ingredient/instruction data appears to be JSON, text, or related rows;
- whether a native API/plugin hook is visible from the local app or container metadata.

Not allowed:

- production database inspection;
- production deployment inspection;
- production secrets;
- copying or committing DB files;
- modifying local DB rows;
- writing synthetic recipes;
- storing local paths in code or docs beyond safe relative paths;
- committing screenshots, traces, uploads, provider output, prompts, raw datasets, or generated indexes.

If the schema cannot be inspected safely, document the limitation and keep the adapter contract fixture-only.

### 3. Implement a fixture-only adapter contract

Add a small internal module under the AI sidecar or another repo-appropriate path that models a fake Cookbook core adapter.

Preferred behavior:

- accepts a validated importer draft/candidate object;
- normalizes fields into a candidate Cookbook payload;
- returns a dry-run style response with:
  - mapped payload;
  - field-level validation errors;
  - warnings;
  - duplicate candidates;
  - idempotency key/result metadata;
  - schema/contract version;
  - safe status envelope.
- never writes to the Vanilla Cookbook DB;
- never contacts production;
- never requires auth, SSO, BYOS, provider keys, or live OpenAI;
- remains disabled from public routes unless a test-only/internal path already exists and is explicitly safe.

This task should prefer pure functions/classes and tests over runtime routes.

Potential internal API shape:

```text
CookbookImportCandidate
CookbookImportDryRunResult
FakeCookbookAdapter
map_import_draft_to_candidate(...)
dry_run_import_candidate(...)
```

Keep naming consistent with existing project style.

### 4. Validation/error cases to support

Cover at minimum:

```text
valid importer draft maps to candidate payload
missing title returns field error
blank ingredient name returns field error
missing instructions returns field error
non-contiguous or empty steps return field error
very long title/notes return bounded validation errors or warnings
unknown fields are rejected or ignored explicitly according to the contract
unsafe source URL returns field error or warning
duplicate title/ingredient fingerprint returns duplicate candidate warning
same candidate/idempotency key returns same dry-run result rather than creating a new object
result envelope contains no prompt, provider body, key, local path, token, or raw provider output
schema/contract version mismatch returns safe error
```

### 5. Add tests

Add focused unit tests for the fixture adapter contract. They must be deterministic, offline, and not require Docker unless placed behind an explicit optional local-runtime check.

If schema discovery is performed, keep those checks documented and/or optional; normal repository tests must not require a running container.

### 6. Update docs

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

- this is Phase 1 fixture-only adapter contract work;
- no Vanilla Cookbook DB writes occur;
- the contract is the prerequisite for a future dry-run endpoint;
- any schema facts discovered from the local runtime;
- remaining unknowns before disposable write/rollback testing.

### 7. Add outbox report

Create:

```text
outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md
```

The outbox should summarize:

- adapter contract implementation;
- schema discovery result or limitation;
- mapping behavior;
- validation and duplicate/idempotency behavior;
- tests added;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A fixture-only Save-to-Cookbook adapter contract exists.
- The contract maps AI importer drafts to a candidate Cookbook payload without writing to Vanilla Cookbook storage.
- The contract returns dry-run-style validation results, duplicate signals, idempotency metadata, and safe errors.
- Focused tests cover valid, invalid, duplicate, idempotent, and unsafe-field cases.
- Normal validation remains mock/offline and does not require Docker or live OpenAI.
- Any local schema discovery is read-only and documented.
- No public route, runtime save button, DB mutation, production write-back, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
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

If an optional local schema discovery command requires Docker Desktop, run it only when Docker is available and record any limitation honestly.

## Commit

```bash
git add ai-api docs README.md outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md

git commit -m "feat: add save adapter fixture contract"

git pull --rebase origin main

git push origin main
```
