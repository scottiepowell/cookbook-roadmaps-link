# 0033P Save-to-Cookbook Schema-Informed Write Plan

## Goal

Define the schema-informed mapping, synthetic ownership fixture, backup/restore, transaction cleanup, duplicate/idempotency, failure-injection, and local-only write-harness plan needed before any Save-to-Cookbook disposable write test.

This is a design/test-plan task. Do not implement a write harness, Save-to-Cookbook button, commit endpoint, database mutation, migration, production integration, or public route in this task.

## Context

`0033O` completed read-only schema discovery against the verified `cookbook-local` runtime. It found useful facts, including UUID recipe IDs, required `userId` and `created`, text `ingredients`, `directions`, and `servings`, category/photo relations, and authenticated create/update/delete paths.

Phase 3 disposable write/rollback testing remains partially informed but blocked until the project defines:

- core-owned mapping for name, servings, ingredient/direction serialization, categories, source fields, and provenance;
- a synthetic user/ownership fixture without reading or importing local user data;
- DB/upload backup/restore and transaction/cleanup plan;
- duplicate/idempotency and failure-injection behavior;
- a local-only approved write harness that cannot target production.

## Required Work

### 1. Read current design/discovery work

Read:

```text
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/local-vanilla-cookbook-schema-discovery.md
outbox/0033J-ai-importer-save-to-cookbook-adapter-design-results.md
outbox/0033M-ai-importer-save-adapter-fixture-contract-results.md
outbox/0033N-ai-importer-save-dry-run-candidate-operation-results.md
outbox/0033O-local-vanilla-cookbook-schema-discovery-results.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/tests/test_cookbook_import_adapter.py
ai-api/tests/test_cookbook_import_dry_run.py
```

Use actual filenames if they differ.

### 2. Create a write-readiness plan

Create:

```text
docs/save-to-cookbook-schema-informed-write-plan.md
```

The plan must cover:

- schema-informed field mapping decisions;
- ingredient serialization options for upstream `ingredients` text;
- direction/instruction serialization options for upstream `directions` text;
- serving normalization from integer to upstream `servings` text;
- source/source URL/provenance handling;
- categories/tags policy for first disposable test;
- media/photo/upload exclusion for first disposable test;
- synthetic ownership/user fixture plan that avoids local user data;
- required `created`/timestamp behavior;
- duplicate/idempotency strategy using title/name and candidate fingerprint;
- backup/restore plan for `.local/vanilla-cookbook/db` and uploads;
- transaction/cleanup expectations;
- failure-injection cases;
- local-only write harness guardrails;
- evidence required before a future implementation task can mutate disposable local data;
- explicit non-goals.

### 3. Define recommended first-write scope

Recommend the narrowest first disposable write scope.

Expected recommendation should be conservative, such as:

```text
Allowed in first disposable write test:
- synthetic local user only;
- one synthetic recipe candidate;
- name/title;
- description;
- servings serialized as simple text;
- ingredients serialized as deterministic plain text lines;
- directions serialized as deterministic numbered or newline text;
- source/source_url only if safe fixture values;
- notes with bounded reviewed provenance label;
- no categories initially unless the ownership fixture is proven;
- no photos/uploads/media;
- no embeddings/semantic regeneration unless unavoidable and safely handled by upstream app;
- backup before write and restore/delete after verification.
```

### 4. Define local-only write harness requirements

Design, but do not implement, a future script/harness such as:

```text
scripts/test-save-to-cookbook-local-write.ps1
```

The future harness must:

- refuse to run unless explicitly approved;
- require `cookbook-local` Compose project;
- require localhost-only target;
- refuse `COOKBOOK_TARGET_URL` values that are not local;
- refuse production/exposed URLs;
- create a backup/restore point before any write;
- create or use a synthetic local user without reading/importing user data;
- perform exactly one synthetic candidate write;
- verify the recipe can be read by the normal local Cookbook app/API/UI if safely possible;
- exercise duplicate/idempotency behavior;
- restore or clean up disposable DB/uploads before exit;
- print only safe IDs/statuses, never recipe private content, secrets, absolute local paths, prompts, or provider output.

### 5. Add fixture tests only if code changes are appropriate

This task may update fixture-only mapping code if the schema facts clearly require a small schema-informed normalization change, but it should prefer docs/planning unless a change is obviously safe.

If code changes are made, add tests. Normal tests must remain offline and must not require Docker or live OpenAI.

### 6. Update planning docs

Update as appropriate:

```text
README.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-schema-notes.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

### 7. Add outbox report

Create:

```text
outbox/0033P-save-to-cookbook-schema-informed-write-plan-results.md
```

Summarize:

- plan created;
- schema-informed mapping decisions;
- recommended first-write scope;
- synthetic ownership fixture plan;
- backup/restore and cleanup plan;
- duplicate/idempotency and failure-injection plan;
- local-only harness guardrails;
- whether Phase 3 implementation is ready, partially ready, or still blocked;
- docs/code changed;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A schema-informed write-readiness plan exists.
- The plan addresses all blockers identified by `0033O`.
- The plan recommends a conservative first disposable write-test scope.
- The plan defines a synthetic ownership/user fixture without reading or importing local user data.
- The plan defines DB/upload backup, restore, and cleanup expectations.
- The plan defines duplicate, idempotency, and failure-injection expectations.
- The plan defines local-only harness guardrails that cannot target production.
- No Save-to-Cookbook button, public route, commit endpoint, database write, migration, production integration, auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing change, QMD integration, or live call is added.
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
git add ai-api docs README.md outbox/0033P-save-to-cookbook-schema-informed-write-plan-results.md

git commit -m "docs: add save to cookbook write readiness plan"

git pull --rebase origin main

git push origin main
```
