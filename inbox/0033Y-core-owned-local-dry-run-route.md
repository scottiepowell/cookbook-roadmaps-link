# 0033Y Core-Owned Local Dry-Run Route

## Goal

Implement the authenticated, core-owned, no-mutation dry-run route in the separate source-owned Vanilla Cookbook workspace, using the `0033X` dry-run service as the backend. Then update this sidecar repository only with documentation/outbox status and any strictly necessary local configuration notes.

This task must not implement recipe commit/save mutation. It must not implement production Save-to-Cookbook. It must not add production routes, migrations, auth bypasses, browser/session automation, sidecar database writes, deployment, provider calls, or a production UI button.

## Context

`0033X` completed the core-owned no-mutation dry-run service in the separate Vanilla Cookbook source workspace:

- external branch: `openclaw/0033X-core-owned-dry-run-adapter`;
- external commit: `90c70c0`;
- service: `src/lib/server/importAdapter.js`;
- local image: `local/vanilla-cookbook-adapter:0033x`;
- service requires core current-user context, rejects anonymous/missing ownership, validates reviewed candidates, maps first-scope fields, and returns a safe dry-run envelope;
- no route was added;
- no Prisma/filesystem/upload/provider mutation occurs.

`0033X` explicitly left the authenticated core route as the next reviewed follow-up before any commit/save implementation.

## Hard Boundaries

- Do not create a new task.
- Do not implement commit/save mutation.
- Do not implement production Save-to-Cookbook.
- Do not add production/public routes.
- Do not target `https://cookbook.roadmaps.link`.
- Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
- Do not inspect or modify production data.
- Do not add database migrations.
- Do not bypass auth.
- Do not create, export, print, or commit cookies, auth tokens, sessions, or real user credentials.
- Do not use browser/session automation.
- Do not add direct sidecar database writes.
- Do not add SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls.
- Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
- Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, or session values.

## Required Reading

Read from this sidecar repository first:

```text
outbox/0033X-core-owned-local-dry-run-adapter-results.md
docs/core-owned-local-dry-run-adapter.md
outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
outbox/0033T-local-native-save-to-cookbook-spike-results.md
outbox/0033S-local-save-to-cookbook-ui-mvp-results.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W` and updated by `0033X`. Keep that source outside this sidecar repository.

## External Workspace Work

In the separate Vanilla Cookbook source workspace:

1. Start from the `0033X` branch/commit or create a follow-up branch, for example:

```text
openclaw/0033Y-core-owned-dry-run-route
```

2. Add the smallest authenticated dry-run route around the `0033X` service.

Preferred route shape:

```text
POST /api/adapter/recipes/import-candidate/dry-run
```

Route requirements:

- requires the normal core app authenticated current user context;
- rejects anonymous requests;
- never accepts `userId`, cookies, auth tokens, sessions, or ownership assertions from the sidecar request body;
- delegates to the core dry-run service from `0033X`;
- performs no database write;
- performs no upload/file write;
- performs no category creation;
- performs no image URL fetch;
- performs no embedding generation;
- performs no migration;
- performs no provider call;
- returns safe status/error envelopes only;
- is local/custom-image work only, not production deployment.

Candidate contract should remain first-scope only:

```text
title/name
description
servings
ingredients[]
instructions[]
source label
source URL only after safe validation
notes/provenance label
idempotency key
contract/schema version
```

Response envelope should include only safe fields such as:

```text
status
contract_version
adapter_version
mapped_recipe_preview
field_errors
warnings
duplicate_status or duplicate_candidates
idempotency_status
safe next-action guidance
```

The response must not include prompts, raw provider output, SQL dumps, stack traces, absolute machine paths, cookies, auth tokens, session values, secrets, environment values, row dumps, private DB content, or local filesystem paths.

## Auth Testing

Add focused tests in the external workspace for:

```text
anonymous route request is rejected
route derives ownership from core locals/current user context
route rejects sidecar-supplied userId/ownership assertions
valid authenticated dry-run returns mapped preview
missing title/ingredients/instructions returns field errors
unsafe source URL returns safe error/warning
unknown/provider-like fields are rejected
same-key replay and same-key/different-payload conflict behavior
safe envelope leakage checks
no mutation during route execution
```

Use synthetic user context in tests without creating real sessions, real cookies, real tokens, or real user accounts. If route-level tests require framework helpers that are unavailable, test the route handler boundary as narrowly as possible and document the limitation honestly.

## Local Custom Image

If tests/build pass, build a new local-only image:

```text
local/vanilla-cookbook-adapter:0033y
```

Do not retag or mutate `jt196/vanilla-cookbook:stable`.
Do not push the image.
Do not deploy it.

Optionally verify this sidecar repo can start the custom image locally:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033y

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Only use loopback/local Docker. Do not use live OpenAI or production.

## Sidecar Repository Updates

Do not copy external source into this repository.

Create:

```text
docs/core-owned-local-dry-run-route.md
```

The document must cover:

```text
external workspace branch/commit
custom image tag/build result
route shape
auth/current-user boundary
candidate contract
safe envelope
no-mutation evidence
test results
local image verification result or blocker
remaining gap before commit/save implementation
explicit non-goals
```

Update as appropriate:

```text
README.md
docs/core-owned-local-dry-run-adapter.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
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
- authenticated core dry-run route does not commit recipes;
- production Save-to-Cookbook remains not implemented;
- commit/save endpoint remains a later task;
- direct sidecar DB writes and browser/session automation remain rejected;
- no external source is vendored into this repo.

Create:

```text
outbox/0033Y-core-owned-local-dry-run-route-results.md
```

The outbox must summarize:

```text
external workspace branch/commit
route implementation status
custom image tag/build result
local startup verification
core-app tests/build results
sidecar docs/config changes
remaining blockers before commit/save
validation results
explicit non-goals
```

If the external workspace changes are committed there, record the external commit SHA in the outbox. Do not copy the external diff or source files into this repo.

## Acceptance Criteria

- Authenticated core dry-run route is implemented in the separate source workspace, or a precise blocker is documented.
- No external source is committed into this sidecar repository.
- Route rejects anonymous access.
- Route derives ownership from core app context, not sidecar-supplied identity.
- Route performs no DB, upload, media, category, embedding, migration, filesystem, provider, or production mutation.
- Candidate mapping follows `0033X`/`0033P`/`0033Q` decisions.
- Safe envelope excludes secrets, prompts, provider output, stack traces, SQL dumps, cookies, tokens, sessions, absolute paths, and env values.
- Duplicate/idempotency route behavior is tested or precisely blocked.
- Local custom image is built as `local/vanilla-cookbook-adapter:0033y` or build blocker is documented.
- Sidecar docs record the external workspace commit/status and next step.
- No production Save-to-Cookbook, public production route, commit endpoint, migration, browser automation, direct DB write, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, or live call is implemented.

## Validation

In the external Vanilla Cookbook workspace, run the relevant focused route tests and build commands available there. Record exact commands/results in the outbox.

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

Optional custom-image local verification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033y

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

Commit external workspace changes in the external workspace if appropriate, and record that commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0033Y-core-owned-local-dry-run-route-results.md

git commit -m "docs: record core owned local dry-run route"

git pull --rebase origin main

git push origin main
```
