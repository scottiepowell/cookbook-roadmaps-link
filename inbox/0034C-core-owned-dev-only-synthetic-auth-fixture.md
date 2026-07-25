# 0034C — Core-Owned Dev-Only Synthetic Auth Fixture

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not add a production Save-to-Cookbook route.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not bypass production auth.
Do not create, export, print, persist, or commit cookies, auth tokens, sessions, real user credentials, browser state, or real account data.
Do not use browser/session automation.
Do not add direct sidecar database writes.
Do not add SSO/BYOS, analytics, ads, payment, provider routing changes, QMD integration, or live calls.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, or session values.

## Goal

Implement the next safe bridge recommended by `0034B`: a **core-owned, local dev-only synthetic auth verification fixture** in the separate Vanilla Cookbook workspace.

The fixture should prove the end-to-end adapter sequence inside the core app process without exporting session credentials:

```text
synthetic in-process AuthUser
reviewed import candidate
core dry-run
explicit local approval
core commit
safe read-after-write
replay/conflict and duplicate behavior
rollback/failure path
backup/restore cleanup
safe UID/status envelope only
```

This task may add a dev-only local verification fixture or route in the external Vanilla Cookbook workspace, but only if it is disabled by default, loopback/custom-image guarded, explicit-approval gated, and impossible to use in production/exposed contexts.

This task must not wire the normal sidecar UI real-save button yet. The output should make that wiring possible in a later task by proving a safe local-only verification boundary first.

## Context

`0034B` recorded that the remaining bridge is that the sidecar has no reviewed way to establish the core authenticated user context without handling cookies, tokens, sessions, or real credentials. It rejected browser/session export and direct sidecar DB writes, deferred sidecar client wiring, and recommended this task: a core-owned local dev-only adapter verification fixture with synthetic in-process `AuthUser`, dry-run-before-commit, explicit local approval, loopback/custom-image guards, disposable DB/uploads backup/restore, safe read-after-write, and no credential export.

Current verified state:

```text
0033S: sidecar local UI/in-memory prototype exists
0033Q: disposable DB/write readiness harness exists
0033Y: authenticated core dry-run route exists
0033Z: authenticated core commit route/service exists
0034A: synthetic core AuthUser + real SQLite service-level commit verification passed
0034B: planned the safe bridge and recommended this fixture
```

Remaining blocked state:

```text
Sidecar UI real-save wiring is still blocked.
Production Save-to-Cookbook is not implemented.
Route-level/session-based real runtime verification remains off-limits if it requires cookies, tokens, sessions, or real credentials.
```

## Read first

From this sidecar repository:

```text
outbox/0034B-sidecar-real-save-local-wiring-plan-results.md
docs/sidecar-real-save-local-wiring-plan.md
outbox/0034A-core-owned-local-auth-commit-verification-results.md
docs/core-owned-local-auth-commit-verification.md
outbox/0033Z-core-owned-local-commit-adapter-results.md
docs/core-owned-local-commit-adapter.md
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
outbox/0033X-core-owned-local-dry-run-adapter-results.md
docs/core-owned-local-dry-run-adapter.md
outbox/0033W-bootstrap-source-owned-vanilla-cookbook-workspace-results.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
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

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all source changes outside this sidecar repository.

## External workspace work

In the external Vanilla Cookbook source workspace:

```text
Create branch: openclaw/0034C-core-owned-dev-only-synthetic-auth-fixture
Base it on the latest approved external adapter branch/commit from 0034A/0033Z, as appropriate.
```

Implement the smallest core-owned dev-only verification fixture that proves the dry-run/commit sequence without real sessions.

Acceptable shapes include one of the following, chosen based on the core app architecture:

```text
A dev-only internal API route that runs entirely inside the core app process with synthetic AuthUser.
A dev-only script/command inside the core workspace that invokes the same route/service boundary in-process.
A dev-only test harness exposed only to local verification scripts.
```

Preferred route shape, if safe:

```text
POST /api/adapter/dev-only/recipes/import-candidate/verify-local-commit
```

The fixture must:

```text
be disabled by default;
require explicit local enablement;
require explicit approval in the request or command;
require loopback/local runtime checks;
require the local custom adapter image/runtime, not the default external image;
reject production/exposed targets before any write;
create or use only a synthetic in-process AuthUser/core user context;
never accept sidecar-supplied userId, cookie, token, session, or ownership claims;
run dry-run before commit;
commit through the core-owned commit service only;
verify safe UID/owner read-after-write;
verify same-key replay and same-key changed-payload conflict;
verify duplicate blocking/review status;
verify rollback/failure path;
backup and restore disposable local SQLite/uploads around the run;
return only safe status/UID/idempotency/verification envelope fields;
clean up after itself;
fail closed when any guard is missing.
```

The fixture must not:

```text
create real users or real credentials;
export cookies/tokens/sessions;
print auth headers, session values, DB rows, SQL dumps, stack traces, secrets, absolute paths, or environment values;
write categories, media/uploads, remote images, embeddings, or provider output;
use browser automation;
use production/exposed targets;
run against https://cookbook.roadmaps.link;
call live OpenAI or any provider;
change production deployment behavior.
```

Candidate data must be synthetic and bounded.

First-scope commit fields remain:

```text
name/title
description
servings as invariant text
deterministic ingredient lines
deterministic numbered directions
safe source/source URL
bounded provenance note
no categories
no media/uploads
no embeddings
```

## Guard requirements

Add explicit guards that are tested and documented.

At minimum, the fixture must refuse unless all required local gates are satisfied, such as:

```text
NODE_ENV/deployment mode is not production;
local dev-only adapter fixture env flag is enabled;
request/command includes explicit approval;
target/runtime is loopback/local only;
no Cloudflare/AWS/GitHub Actions/CI/tunnel indicators are active;
custom adapter image/runtime marker is present, if practical;
synthetic AuthUser fixture mode is explicitly selected;
DB/uploads backup path is disposable/local and ignored.
```

Use the actual core app environment/config conventions. Do not introduce secrets as gates.

## External workspace tests

Add focused tests for:

```text
disabled-by-default refusal;
missing approval refusal;
production/exposed/tunnel/CI guard refusal;
sidecar-supplied identity/cookie/token/session fields rejected;
synthetic in-process AuthUser is used for ownership;
dry-run runs before commit;
valid fixture creates exactly one recipe in disposable test DB;
read-after-write returns safe UID/owner status only;
same-key same-payload replay returns original safe result;
same-key different-payload returns safe conflict and no second write;
duplicate fingerprint returns duplicate/review status and no unbounded duplicate;
injected failure rolls back;
backup/restore leaves zero recipes after restore;
categories/media/uploads/embeddings excluded;
safe envelope leakage checks.
```

Run focused external tests and the relevant core build steps. Record exact commands and results.

Build a new local-only image if focused tests/build pass:

```text
local/vanilla-cookbook-adapter:0034c
```

Do not push or deploy the image.

## Sidecar optional verification

From the sidecar repo, verify only local/loopback startup with the custom image:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034c

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

# Run only the approved dev-only synthetic auth verification fixture if it exists and all local gates are enabled.
# Do not export, print, or save cookies/tokens/sessions.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

If a sidecar helper script is added to run the fixture, it must:

```text
be local-only;
require explicit approval;
require a local/vanilla-cookbook-adapter:* image;
refuse production/exposed targets;
redact output;
never accept or print cookies/tokens/sessions;
not require live providers;
not commit local DBs/uploads/artifacts.
```

Do not wire the normal sidecar UI real-save button in this task.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/core-owned-dev-only-synthetic-auth-fixture.md
outbox/0034C-core-owned-dev-only-synthetic-auth-fixture-results.md
```

Update as appropriate:

```text
README.md
docs/sidecar-real-save-local-wiring-plan.md
docs/core-owned-local-auth-commit-verification.md
docs/core-owned-local-commit-adapter.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The docs must clearly state:

```text
source remains outside this sidecar repository;
the fixture is dev-only/local-only/disabled by default;
the fixture uses synthetic in-process AuthUser and no credential export;
production Save-to-Cookbook remains not implemented;
normal sidecar UI real-save wiring remains a later task;
direct sidecar DB writes and browser/session automation remain rejected;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external workspace branch/commit;
fixture shape: route/script/test harness;
custom image tag/build result;
focused external tests/build results;
sidecar startup/verification result;
backup/restore result;
read-after-write result;
replay/conflict/duplicate behavior;
rollback behavior;
auth/ownership guard behavior;
safe envelope/leakage behavior;
remaining blockers before sidecar UI real-save wiring;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
Core-owned dev-only synthetic auth verification fixture is implemented or precisely blocked.
No external source is committed into this sidecar repository.
No production route/save/deployment is added.
Fixture is disabled by default and requires explicit local approval.
Fixture uses synthetic in-process AuthUser, not cookies/tokens/sessions/real credentials.
Fixture runs dry-run before commit.
Fixture proves or precisely blocks real local commit, safe read-after-write, replay/conflict, duplicate blocking, rollback, and backup/restore.
Fixture returns only safe envelopes.
Custom local image local/vanilla-cookbook-adapter:0034c is built or blocker is documented.
Sidecar docs record external commit/status and next step.
Normal sidecar UI real-save wiring remains deferred.
No live OpenAI/provider calls are used.
No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, external source files, container source snapshots, cookies, auth tokens, or session values are committed.
```

## Validation

In the external Vanilla Cookbook workspace, run focused tests/builds available there and record exact commands/results in the outbox.

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

Do not run live OpenAI.

Commit external workspace changes if appropriate and record that external commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034C-core-owned-dev-only-synthetic-auth-fixture-results.md

git commit -m "docs: record core owned dev auth fixture"

git pull --rebase origin main

git push origin main
```
