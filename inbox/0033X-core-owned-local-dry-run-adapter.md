# 0033X Core-Owned Local Dry-Run Adapter

## Goal

Implement the first **core-owned, no-mutation dry-run adapter** in the separate source-owned Vanilla Cookbook workspace created by `0033W`, then build a new local-only custom image and document how the sidecar can use it for future Save-to-Cookbook integration.

This task must not implement commit/save mutation, production Save-to-Cookbook, deployment, migration, auth bypass, browser/session automation, direct sidecar database writes, or live provider behavior.

## Context

`0033W` completed the source-owned workspace bootstrap:

- upstream source and license provenance were reviewed;
- a recursive checkout exists outside this sidecar repository;
- local source pin is `7d94160e90368ed8ceb55b2dccfbbb5de1fb7b2c`;
- submodule pin is `6e8d1dff0c05f749b435c7e19b7f6627f60aa5d0`;
- a local image `local/vanilla-cookbook-adapter:0033w` was built successfully;
- `docker-compose.local.yml` can opt into `local/vanilla-cookbook-adapter:*` while defaulting to `jt196/vanilla-cookbook:stable`;
- no external source was committed into this sidecar repo.

`0033W` defined the next task as a core-owned authenticated, no-mutation dry-run adapter with reviewed candidate input, idempotency/duplicate checks, safe errors, canonical field mapping, and no categories/media/remote images/embeddings initially.

## Hard boundaries

Do not create a new task.
Do not implement commit/save mutation.
Do not implement production Save-to-Cookbook.
Do not add production routes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not add database migrations.
Do not bypass auth.
Do not create or export cookies, auth tokens, sessions, or real user credentials.
Do not use browser/session automation.
Do not add direct sidecar database writes.
Do not add SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, or session values.

## Required reading

Read from this sidecar repository first:

```text
outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
outbox/0033V-source-owned-vanilla-cookbook-adapter-workspace-plan-results.md
outbox/0033T-local-native-save-to-cookbook-spike-results.md
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`.

Use the actual external workspace path recorded by `0033W`. Keep the source outside this sidecar repository.

## External workspace work

In the separate Vanilla Cookbook source workspace only:

1. Create a focused branch for this task, for example:

```text
openclaw/0033X-core-owned-dry-run-adapter
```

2. Implement the smallest core-owned dry-run adapter boundary.

Preferred shape:

```text
core service/helper that accepts reviewed import candidate + core current user context
optional local/internal API route such as POST /api/adapter/recipes/import-candidate/dry-run
```

Requirements:

- dry-run only;
- no database writes;
- no uploads;
- no migration;
- no recipe commit;
- no category creation;
- no image URL fetch;
- no embedding generation;
- no background semantic work;
- ownership derived from core app user/session context, never from sidecar-supplied `userId`;
- route, if added, must require normal core auth and reject anonymous requests;
- service tests may inject a synthetic user object without creating sessions/cookies;
- no cookies, tokens, sessions, auth headers, or real accounts are printed or committed.

3. Candidate contract should accept the first-scope fields only:

```text
title/name
description
servings
ingredients[]
instructions[]
source label
source URL only if validated as a safe URL
notes/provenance label
idempotency key
contract/schema version
```

4. Canonical mapping should match the prior sidecar evidence:

```text
title -> Recipe.name
description -> Recipe.description
servings -> invariant text
ingredients[] -> deterministic one-ingredient-per-line text
directions/instructions[] -> deterministic numbered plain text
source label -> Recipe.source
source URL -> Recipe.source_url only after validation
notes -> bounded reviewed provenance only
no categories
no media/uploads
no embeddings
```

5. Dry-run response must include safe status envelope fields such as:

```text
status
contract_version
schema_version or adapter_version
mapped_recipe_preview
field_errors
warnings
duplicate_candidates or duplicate_status
idempotency_status
safe next-action guidance
```

The response must not include prompts, raw provider output, SQL dumps, stack traces, absolute machine paths, cookies, auth tokens, session values, secrets, environment values, row dumps, or private DB content.

6. Duplicate/idempotency behavior:

- compute a deterministic candidate fingerprint from normalized title/name, ingredients, owner scope, and adapter contract version;
- same idempotency key + same payload should be reported as replay-safe in dry-run state;
- same idempotency key + different payload should return a safe conflict;
- duplicate fingerprint should return a reviewable duplicate signal, not a save or merge.

Because this is dry-run only, duplicate checks may use synthetic/in-memory fixtures or existing core read helpers only if safe. Do not inspect real row contents or production data. If real duplicate lookup would require unsafe access, leave it as a clearly documented future hook and test the decision logic with fixtures.

7. Tests in the external workspace should cover:

```text
valid candidate dry-run maps to Recipe-compatible preview
anonymous/unauthenticated route is rejected, if route is added
synthetic core user context works in service tests
missing title/ingredients/instructions returns field errors
unsafe source URL returns safe error/warning
unknown fields are rejected or explicitly ignored by contract
servings serializes to invariant text
ingredients serialize deterministically
directions serialize deterministically
categories/media/embeddings are excluded
same-key replay behavior
same-key/different-payload conflict
safe envelope leakage checks
no mutation during dry-run
```

Run the relevant core-app tests if available. If the upstream test harness is missing or hard to run, add the narrowest local tests possible and document any limitation honestly.

8. Build a new local-only custom image from the external source workspace if tests/build gates pass.

Use a distinct local tag such as:

```text
local/vanilla-cookbook-adapter:0033x
```

Do not retag or mutate `jt196/vanilla-cookbook:stable`.
Do not push the image.
Do not deploy it.

9. Optionally verify this sidecar repo can start the custom image locally:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033x
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Only use loopback/local Docker. Do not use live OpenAI or production.

## Sidecar repository updates

In this sidecar repository, update docs only unless a tiny local-image selector test/doc fix is required.

Create:

```text
docs/core-owned-local-dry-run-adapter.md
```

The document must cover:

```text
external workspace branch/commit status
custom image tag/build result
adapter/service/route shape
core auth/ownership boundary
candidate contract
canonical mapping rules
dry-run response envelope
duplicate/idempotency behavior
no-mutation evidence
local test results
local image verification result or blocker
remaining gap before commit/save implementation
explicit non-goals
```

Update as appropriate:

```text
README.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly state:

- source remains outside this sidecar repository;
- custom image is local-only and opt-in;
- dry-run adapter does not commit recipes;
- production Save-to-Cookbook remains not implemented;
- commit/save endpoint remains a later task;
- direct sidecar DB writes and browser/session automation remain rejected;
- no external source is vendored into this repo.

Create:

```text
outbox/0033X-core-owned-local-dry-run-adapter-results.md
```

The outbox must summarize:

```text
external workspace branch/commit
core dry-run adapter implementation status
route/service shape
custom image tag/build result
local startup verification
core-app tests/build results
sidecar docs/config changes
remaining blockers before commit/save
validation results
explicit non-goals
```

If the external workspace changes are committed there, record the external commit SHA in the outbox. Do not copy the external diff or source files into this repo.

## Acceptance criteria

- Core-owned dry-run adapter is implemented in the separate source workspace, or a precise blocker is documented.
- No external source is committed into this sidecar repository.
- Dry-run does not mutate the database, uploads, categories, media, embeddings, or production data.
- Ownership is derived from core app context, not sidecar-supplied identity.
- Anonymous route access is rejected if a route is added.
- Candidate mapping follows the schema-informed decisions from `0033P`/`0033Q`.
- Safe response envelope excludes secrets, prompts, provider output, stack traces, SQL dumps, cookies, tokens, sessions, absolute paths, and env values.
- Duplicate/idempotency dry-run behavior is tested or precisely blocked.
- Local custom image is built as `local/vanilla-cookbook-adapter:0033x` or build blocker is documented.
- Sidecar docs record the external workspace commit/status and next step.
- No production Save-to-Cookbook, public route, commit endpoint, migration, browser automation, direct DB write, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, or live call is implemented.

## Validation

In the external Vanilla Cookbook workspace, run the relevant tests/builds available there and record the exact commands/results in the outbox.

In this sidecar repository, run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

If sidecar code/config changes beyond docs are made, also run:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Optional custom-image local verification, only after safe preflight:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033x
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

Commit external workspace changes in the external workspace if appropriate, and record that commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0033X-core-owned-local-dry-run-adapter-results.md

git commit -m "docs: record core owned local dry-run adapter"

git pull --rebase origin main

git push origin main
```
