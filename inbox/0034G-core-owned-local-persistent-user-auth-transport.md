# 0034G — Core-Owned Local Persistent-User Auth Transport

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not implement production authentication.
Do not implement real Google login.
Do not wire the normal sidecar UI real-save button.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not bypass production auth.
Do not call Google, Microsoft, OpenAI, storage providers, OAuth providers, or live external providers.
Do not request Google Drive or storage scopes.
Do not create, export, print, persist, or commit cookies, auth tokens, sessions, OAuth codes, refresh tokens, access tokens, ID tokens, client secrets, real user credentials, browser state, or real account data.
Do not use browser/session automation.
Do not add direct sidecar database writes.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, sessions, OAuth state, or real profile data.

## Goal

Close the remaining gap from `0034F`: prove a **core-owned local persistent-user/auth transport** against the disposable `cookbook-local` runtime before any normal UI real-save wiring.

`0034F` proved that the sidecar can call a guarded core-owned dev route safely, but that route used temporary fixture storage and synthetic ownership. This task should move one step closer to product behavior by proving that the core app can create/use a local dev-only synthetic persistent `AuthUser` in the disposable local runtime, commit a reviewed recipe candidate through the core-owned adapter, verify safe read-after-write from the runtime database/API, and restore local DB/uploads afterward.

This remains local/dev-only. It is not production auth, not real Google login, not normal sidecar UI save, and not production Save-to-Cookbook.

## Context

Current verified state:

```text
0034C: core-process synthetic AuthUser fixture proved dry-run -> commit -> read-after-write -> replay/conflict -> duplicate -> rollback -> restore
0034E: offline Google-first core-owned identity foundation exists; no real OAuth/login
0034F: sidecar-to-core local transport exists; core route uses temporary fixture storage and synthetic ownership; normal UI remains in-memory prototype
```

`0034F` remaining blocker:

```text
No persistent Cookbook UI save was attempted. The core route intentionally uses temporary fixture storage and synthetic ownership, so its safe UID proof is not a real authenticated user session. The existing sidecar UI remains the in-memory prototype. A future task must separately approve a core-owned local persistent-user/auth transport before wiring a UI control.
```

## Read first

From this sidecar repository:

```text
outbox/0034F-sidecar-to-core-local-real-save-transport-results.md
docs/sidecar-to-core-local-real-save-transport.md
outbox/0034E-google-first-core-oidc-local-auth-spike-results.md
docs/google-first-core-oidc-local-auth-spike.md
outbox/0034C-core-owned-dev-only-synthetic-auth-fixture-results.md
docs/core-owned-dev-only-synthetic-auth-fixture.md
outbox/0034B-sidecar-real-save-local-wiring-plan-results.md
docs/sidecar-real-save-local-wiring-plan.md
outbox/0034A-core-owned-local-auth-commit-verification-results.md
docs/core-owned-local-auth-commit-verification.md
outbox/0033Z-core-owned-local-commit-adapter-results.md
docs/core-owned-local-commit-adapter.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
ai-api/app/cookbook_core_transport.py
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all external source changes outside this sidecar repository.

## External core workspace work

In the external Vanilla Cookbook source workspace:

```text
Create branch: openclaw/0034G-core-owned-local-persistent-user-auth-transport
Base it on the latest approved external branch/commit from 0034F as appropriate.
```

Implement or precisely block the smallest core-owned local/dev-only persistent-user verification path.

Preferred shape, if safe:

```text
POST /api/adapter/dev-only/recipes/import-candidate/verify-local-persistent-commit
```

or a clearly named dev-only route/script under the core app that:

```text
uses the real disposable cookbook-local runtime database, not a temporary detached DB;
creates or reuses one synthetic local dev AuthUser owned by the core app;
does not create, export, print, or return cookies/tokens/sessions/real credentials;
runs dry-run before commit;
commits only through the core-owned commit service;
verifies safe read-after-write from core storage using safe UID/owner/status only;
verifies replay/conflict/duplicate behavior;
verifies rollback/failure behavior;
backs up disposable local DB/uploads before the run;
restores DB/uploads afterward;
confirms cleanup/restore state;
returns only safe status/UID/idempotency/canonical-link/verification envelope fields.
```

The route/script must fail closed unless all local gates are satisfied:

```text
not production;
explicit local persistent fixture flag enabled;
explicit approval in request or command;
loopback/local runtime only;
custom local adapter image/runtime marker present where practical;
no Cloudflare/AWS/GitHub Actions/CI/tunnel indicators;
disposable local DB/uploads paths only;
no sidecar-supplied userId/session/cookie/token/OAuth/provider/storage grant.
```

It must not:

```text
implement real Google login;
create real users or credentials;
export cookies/tokens/sessions;
use browser automation;
request Drive/storage scopes;
write categories/media/uploads/remote images/embeddings;
call providers;
change production behavior;
commit migrations unless a separate migration-review task approved them.
```

If durable persistent-user/provider-link support requires a migration or unsafe session handling, do not implement it. Document the blocker precisely.

Run focused external tests for:

```text
disabled-by-default refusal;
missing approval refusal;
production/exposed/CI/tunnel guard refusal;
sidecar-supplied identity/session/token/cookie/provider/storage claims rejected;
core-owned synthetic persistent AuthUser setup;
dry-run before commit;
valid local persistent request creates exactly one recipe in disposable runtime storage;
safe read-after-write UID/owner/status;
same-key same-payload replay behavior;
same-key changed-payload conflict behavior;
duplicate blocking/review behavior;
rollback/failure path;
backup/restore leaves runtime storage clean;
categories/media/uploads/embeddings excluded;
safe envelope leakage checks.
```

Build a new local-only image if focused tests/build pass:

```text
local/vanilla-cookbook-adapter:0034g
```

Do not push or deploy the image.

## Sidecar work

Do not wire the normal sidecar UI real-save button in this task.

Update the existing sidecar transport only if needed to support the new local persistent fixture safely. Keep it disabled by default and local-only.

If a sidecar helper script is added, it must:

```text
require explicit local approval;
require loopback target;
require local/vanilla-cookbook-adapter:0034g or approved local adapter image marker;
refuse production/exposed/tunnel/Cloudflare/AWS/GitHub Actions/CI contexts;
never accept or print cookies/tokens/sessions/OAuth codes/provider grants/storage grants;
redact output;
not require live providers;
not commit DBs/uploads/artifacts.
```

If the saved recipe cannot be observed in the Vanilla Cookbook browser UI without a real authenticated session, document that honestly. A safe core UID/read-after-write proof against persistent disposable runtime storage is acceptable for this task. Browser/session UI observation remains blocked if it requires cookies/tokens/sessions or real credentials.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/core-owned-local-persistent-user-auth-transport.md
outbox/0034G-core-owned-local-persistent-user-auth-transport-results.md
```

Update as appropriate:

```text
README.md
docs/sidecar-to-core-local-real-save-transport.md
docs/google-first-core-oidc-local-auth-spike.md
docs/core-owned-dev-only-synthetic-auth-fixture.md
docs/sidecar-real-save-local-wiring-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly state:

```text
source remains outside this sidecar repository;
transport is local-only/dev-only/disabled by default;
core owns AuthUser/session/provider links/storage grants/recipe authorization;
sidecar never owns identity, storage, cookies, sessions, or provider grants;
Google OIDC real login remains later;
normal sidecar UI real-save wiring remains later;
production Save-to-Cookbook remains not implemented;
any local persistent behavior targets only cookbook-local loopback/custom image and restores disposable storage;
direct sidecar DB writes and browser/session automation remain rejected;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external workspace branch/commit;
core persistent-user route/script implementation status or blocker;
local image tag/build result;
sidecar transport/helper status;
local verification result;
whether saved recipe can be observed in Vanilla Cookbook UI or why not;
auth/ownership/session boundary behavior;
idempotency/replay/conflict/duplicate behavior;
rollback/backup/restore behavior;
external focused tests/build results;
sidecar tests/validation results;
remaining blockers before normal sidecar UI real-save wiring;
remaining blockers before production Save-to-Cookbook;
remaining blockers before real Google login;
explicit non-goals.
```

## Acceptance criteria

```text
A core-owned local persistent-user/auth transport is implemented or precisely blocked.
No external source is committed into this sidecar repository.
No production auth or production Save-to-Cookbook is implemented.
No real Google/OAuth/provider/storage call is made.
No cookie/token/session/OAuth code/real credential/browser state is created/exported/printed/committed.
Sidecar sends no userId/session/cookie/token/provider/storage grant.
Core owns the synthetic persistent AuthUser and commit authorization.
Local custom image local/vanilla-cookbook-adapter:0034g is built or blocker is documented.
Normal sidecar validation remains mock/offline.
Direct sidecar DB writes and browser/session automation remain rejected.
Docs/outbox record whether local saved recipe UI observation is possible without credentials.
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

Do not run live OpenAI, Google, Microsoft, OAuth, or storage calls.

Commit external workspace changes if appropriate and record that external commit SHA in the sidecar outbox.

Then commit sidecar changes:

```bash
git add ai-api scripts docs README.md outbox/0034G-core-owned-local-persistent-user-auth-transport-results.md

git commit -m "feat: add local persistent core save transport"

git pull --rebase origin main

git push origin main
```
