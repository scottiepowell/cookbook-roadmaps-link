# 0033Z Core-Owned Local Commit Adapter

## Goal

Implement the first **core-owned, authenticated, local-only commit adapter** in the separate source-owned Vanilla Cookbook workspace, then build and verify a new local-only custom image. This is the first task that may create a real recipe through the core app adapter, but only against the disposable local `cookbook-local` runtime with explicit local approval, synthetic data, backup/restore, transaction/rollback, duplicate handling, and persisted idempotency evidence.

This task must not implement production Save-to-Cookbook, public production routes, exposed deployment integration, AWS/GitHub Actions/Cloudflare work, provider integration, or live calls.

## Context

`0033Y` completed the authenticated core-owned dry-run route in the external Vanilla Cookbook workspace:

- External branch: `openclaw/0033Y-core-owned-local-dry-run-route`;
- External commit: `a3d33924795d31e60ad587ac7960cae7ac7dc86d`;
- Route: `POST /api/adapter/recipes/import-candidate/dry-run`;
- Local image: `local/vanilla-cookbook-adapter:0033y`.

The dry-run route uses core `requireAuth(locals)`, rejects anonymous requests, derives ownership from authenticated core context, rejects sidecar-supplied identity fields, delegates to the pure service, and performs no Prisma/SQLite/upload/category/media/embedding/filesystem/provider/recipe mutation.

The remaining gap is a core-owned authenticated commit boundary with explicit confirmation, transaction/rollback, persisted idempotency, duplicate handling, and local disposable verification. `0033Y` explicitly states no commit/save endpoint exists.

## Hard boundaries

Do not:

- create a new task;
- implement production Save-to-Cookbook;
- add public production routes;
- target `https://cookbook.roadmaps.link`;
- use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment;
- inspect or modify production data;
- bypass auth;
- create or export cookies, auth tokens, sessions, or real user credentials;
- use browser/session automation;
- add direct sidecar database writes;
- add SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls;
- vendor or copy external Vanilla Cookbook source into this sidecar repository;
- commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, or session values.

## Required reading in the sidecar repository

Read first:

```text
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
outbox/0033X-core-owned-local-dry-run-adapter-results.md
docs/core-owned-local-dry-run-adapter.md
outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
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

Use actual filenames if they differ.

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all source changes outside this sidecar repository.

## External workspace implementation

In the external Vanilla Cookbook source workspace:

1. Start from the `0033Y` external branch/commit or a clean successor branch.
2. Create a focused branch such as:

```text
openclaw/0033Z-core-owned-local-commit-adapter
```

3. Implement the smallest core-owned local commit boundary.

Preferred route shape:

```text
POST /api/adapter/recipes/import-candidate/commit
```

The commit route/service must:

- require normal core `requireAuth(locals)`;
- reject anonymous requests;
- derive ownership only from the authenticated core user context;
- reject sidecar-supplied `userId`, cookie, token, session, or ownership claims;
- require explicit confirmation in the request, for example `confirm_save: true`;
- require a valid dry-run-compatible candidate and contract version;
- require an idempotency key;
- use deterministic schema-informed mapping from prior tasks;
- commit only first-scope fields:
  - `Recipe.name` from title;
  - `Recipe.description`;
  - invariant text servings;
  - deterministic one-line-per-ingredient text;
  - deterministic numbered directions text;
  - safe source label/source URL only when validated;
  - bounded reviewed provenance note;
- exclude categories, media/uploads, remote image fetches, and embeddings in the first commit scope;
- avoid optional side effects where possible;
- use a transaction for recipe creation and adapter metadata/idempotency state;
- return safe canonical UID/URL/status only;
- never return prompts, raw provider output, SQL dumps, stack traces, absolute machine paths, cookies, tokens, session values, secrets, environment values, row dumps, or private DB content.

## Idempotency and duplicate handling

Implement persisted local idempotency/duplicate behavior inside the core app boundary.

Preferred behavior:

- same idempotency key + same candidate/user scope returns the original safe commit result without creating a second recipe;
- same idempotency key + different payload returns a safe conflict with no write;
- duplicate fingerprint for same user scope returns a reviewable duplicate status and does not silently merge, overwrite, or create unbounded duplicates;
- idempotency metadata must not store prompts, provider bodies, secrets, cookies, tokens, sessions, or raw private content.

If durable idempotency requires a schema change, do **not** add an unreviewed production migration. Use a local-only/dev-safe mechanism if already available, or stop and document the migration/metadata blocker. If a migration is unavoidable even locally, it must be clearly documented as a blocker for a separate migration-review task rather than implemented here.

## Tests in the external workspace

Add focused core-app tests for:

```text
anonymous commit route is rejected
missing confirmation refuses before write
sidecar-supplied identity fields are rejected
valid authenticated synthetic user commit creates one recipe in test DB/fixture
commit maps first-scope fields exactly
categories/media/uploads/embeddings are excluded
same-key same-payload replay returns same canonical result
same-key changed-payload returns safe conflict and no write
duplicate fingerprint returns reviewable duplicate/no unbounded duplicate
transaction rollback on injected create/related failure
safe envelope leakage checks
no prompt/provider/secret/cookie/token/session/absolute-path/SQL/stack leakage
```

Use synthetic local users/fixtures only. Do not read or depend on real local users, cookies, sessions, production data, or browser state.

Run the relevant external tests/builds. If the full upstream suite still has pre-existing environment failures, record them separately from the focused adapter results.

## Custom image

If focused tests/build pass, build a new local-only image:

```text
local/vanilla-cookbook-adapter:0033z
```

Do not retag or mutate `jt196/vanilla-cookbook:stable`.
Do not push the image.
Do not deploy it.

Optionally verify the custom image with sidecar guarded scripts:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033z

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Only use local Docker/loopback. Do not use live OpenAI or production.

## Local disposable verification

If the commit endpoint exists and the image starts safely, add or document a local-only verification path that:

- uses explicit local approval;
- starts/checks `cookbook-local` with `local/vanilla-cookbook-adapter:0033z`;
- creates only synthetic local authenticated test context/data;
- backs up disposable DB/uploads before any local write;
- submits exactly one reviewed synthetic candidate through the core-owned commit route/service;
- verifies safe read-after-write by UID/status only;
- exercises idempotent replay and conflict behavior;
- exercises a rollback/failure case if feasible;
- restores/cleans DB/uploads before exit;
- does not print secrets, cookies, sessions, row dumps, recipe bodies, absolute paths, prompts, or provider output.

If authenticated local verification cannot be performed without unsafe cookie/session handling, document the exact blocker and keep verification at focused service/route test level.

## Sidecar repository updates

Do not copy external source into this repo. In this sidecar repo, update docs only unless a tiny local-image selector/config fix is required.

Create:

```text
docs/core-owned-local-commit-adapter.md
```

The document must cover:

```text
external workspace branch/commit status
custom image tag/build result
commit route/service shape
auth/ownership boundary
confirmation requirement
transaction/rollback behavior
idempotency persistence or blocker
duplicate handling
canonical mapping rules
safe response envelope
local verification result or blocker
remaining gap before wiring sidecar UI to real core commit
production non-goals
```

Update as appropriate:

```text
README.md
docs/core-owned-local-dry-run-route.md
docs/core-owned-local-dry-run-adapter.md
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

- external source remains outside this sidecar repository;
- custom image is local-only and opt-in;
- commit adapter is local/core-owned only;
- production Save-to-Cookbook remains not implemented;
- sidecar UI is not yet wired to the real core commit route unless explicitly done by a later task;
- direct sidecar DB writes and browser/session automation remain rejected;
- no external source is vendored into this repo.

Create:

```text
outbox/0033Z-core-owned-local-commit-adapter-results.md
```

The outbox must summarize:

```text
external workspace branch/commit
commit route/service implementation status
custom image tag/build result
external tests/build results
local startup verification
local disposable commit verification or blocker
auth/ownership/confirmation behavior
idempotency/duplicate behavior
transaction/rollback behavior
sidecar docs/config changes
remaining blockers before sidecar UI real-save wiring
validation results
explicit non-goals
```

If the external workspace changes are committed there, record the external commit SHA in the outbox. Do not copy the external diff or source files into this repo.

## Acceptance criteria

- Core-owned local commit route/service is implemented in the separate source workspace, or a precise blocker is documented.
- No external source is committed into this sidecar repository.
- Commit requires core authentication and explicit confirmation.
- Ownership is derived from core context, not sidecar-supplied identity.
- Candidate mapping follows the schema-informed decisions from prior tasks.
- Categories/media/uploads/remote image fetches/embeddings remain excluded from first scope.
- Idempotency and duplicate behavior are persisted/tested or precisely blocked.
- Transaction/rollback behavior is tested or precisely blocked.
- Safe response envelope excludes secrets, prompts, provider output, stack traces, SQL dumps, cookies, tokens, sessions, absolute paths, and env values.
- Local custom image is built as `local/vanilla-cookbook-adapter:0033z` or build blocker is documented.
- Sidecar docs record the external workspace commit/status and next step.
- No production Save-to-Cookbook, public production route, migration, browser automation, direct sidecar DB write, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, or live call is implemented.

## Validation

In the external Vanilla Cookbook workspace, run the relevant focused tests/builds and record exact commands/results in the outbox.

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
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0033z

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

Commit external workspace changes in the external workspace if appropriate, and record that commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0033Z-core-owned-local-commit-adapter-results.md

git commit -m "docs: record core owned local commit adapter"

git pull --rebase origin main

git push origin main
```
