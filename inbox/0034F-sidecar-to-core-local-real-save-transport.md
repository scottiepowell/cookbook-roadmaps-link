# 0034F — Sidecar-to-Core Local Real-Save Transport

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not implement production authentication.
Do not implement real Google login.
Do not call Google, Microsoft, OpenAI, storage providers, OAuth providers, or live external providers.
Do not request Google Drive or storage scopes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not bypass production auth.
Do not create, export, print, persist, or commit cookies, auth tokens, sessions, OAuth codes, refresh tokens, access tokens, ID tokens, client secrets, real user credentials, browser state, or real account data.
Do not use browser/session automation.
Do not add direct sidecar database writes.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, sessions, OAuth state, or real profile data.

## Goal

Implement the first safe **local-only sidecar-to-core Save-to-Cookbook transport** using the core-owned adapter boundaries already proven in `0034C` and the Google-first core auth foundation from `0034E`.

This task should make the sidecar local UI or local sidecar API capable of calling a reviewed core-owned local/dev adapter path and receiving only safe UID/status/idempotency/canonical-link information.

This is still **not** production Save-to-Cookbook and not real Google login. It may mutate only the disposable local `cookbook-local` runtime under explicit local approval and backup/restore verification.

## Context

`0034C` proved the local synthetic-auth bridge inside the core process:

```text
synthetic in-process AuthUser
core dry-run before commit
core commit
safe read-after-write
replay/conflict behavior
duplicate blocking
rollback/failure path
backup/restore cleanup
safe UID/status envelope only
```

`0034E` added a Google-first, core-owned identity foundation but did not add real OAuth routes, secrets, tokens, sessions, or production auth. Google OIDC implementation remains a later security/configuration task.

Current intended boundary:

```text
Vanilla Cookbook core
  owns AuthUser/session/provider links/storage grants/recipe authorization
  owns adapter dry-run and commit
  owns canonical recipe storage

AI sidecar
  owns reviewed recipe candidate UI/workflow
  calls reviewed core-owned adapter transport only
  never owns userId/session/cookie/provider token/storage grant
  never writes the Cookbook DB directly
```

## Read first

From this sidecar repository:

```text
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
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
ai-api/app/cookbook_import_adapter.py
ai-api/app/cookbook_import_dry_run.py
ai-api/app/cookbook_import_commit.py
ai-api/app/static/demo.js
ai-api/app/main.py
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
Create branch: openclaw/0034F-sidecar-to-core-local-real-save-transport
Base it on the latest approved external branch/commit from 0034E as appropriate.
```

Inspect whether `0034C` produced only a script/test harness or also a dev-only HTTP route. If there is no safe local HTTP transport for the sidecar to call, implement the smallest core-owned local/dev-only HTTP route that wraps the already-proven synthetic-auth fixture behavior.

Preferred local-only route shape, if safe:

```text
POST /api/adapter/dev-only/recipes/import-candidate/verify-local-commit
```

or another clearly named dev-only route under `/api/adapter/dev-only/...`.

The core route must:

```text
remain disabled by default;
require explicit local enablement;
require explicit approval in the request;
require loopback/local runtime checks;
require local custom adapter image/runtime markers where practical;
reject production/exposed/Cloudflare/AWS/GitHub Actions/CI/tunnel contexts before setup;
create/use only synthetic in-process AuthUser/core user context;
reject sidecar-supplied userId, cookie, token, session, OAuth code, provider token, or ownership claims;
run core dry-run before commit;
commit only through the core-owned commit service;
verify safe read-after-write;
verify replay/conflict and duplicate behavior when requested by verification mode;
return only safe UID/status/idempotency/canonical-link/verification envelope fields;
not return DB rows, SQL, stack traces, absolute paths, secrets, env values, cookies, tokens, sessions, prompts, provider output, or raw private content.
```

The route must not:

```text
implement real Google login;
create real users or credentials;
export cookies/tokens/sessions;
use browser automation;
request Drive/storage scopes;
write categories/media/uploads/remote images/embeddings;
call providers;
change production behavior.
```

If adding this route safely requires a migration, real session, cookie export, real account, or unsafe runtime state, do not implement it. Document the blocker and keep sidecar wiring disabled.

Run focused external tests for:

```text
disabled-by-default refusal;
missing approval refusal;
production/exposed/CI/tunnel guard refusal;
sidecar-supplied identity/session/token/cookie/provider claims rejected;
synthetic in-process AuthUser ownership;
dry-run before commit;
valid local request creates exactly one recipe in disposable DB;
safe read-after-write UID/owner status;
same-key same-payload replay behavior;
same-key changed-payload conflict behavior;
duplicate blocking/review behavior;
rollback/failure path;
categories/media/uploads/embeddings excluded;
safe envelope leakage checks.
```

Build a new local-only image if focused tests/build pass:

```text
local/vanilla-cookbook-adapter:0034f
```

Do not push or deploy the image.

## Sidecar transport work

In this sidecar repository, implement the smallest local-only sidecar client/transport to call the core-owned dev-only route.

Acceptable shape:

```text
ai-api/app/cookbook_core_transport.py
local-only sidecar route used by the existing importer review panel
or a local-only sidecar service plus tests, with UI wiring only if gates are safe
```

The sidecar transport must:

```text
be disabled by default;
require explicit local enablement;
require explicit user/operator confirmation for save;
require the target to be loopback only, such as http://127.0.0.1:3000;
require a local/vanilla-cookbook-adapter:0034f or explicitly allowed local/vanilla-cookbook-adapter:* image marker/config;
refuse production/exposed/tunnel/Cloudflare/AWS/GitHub Actions/CI contexts;
only send reviewed recipe candidate data, idempotency key, contract version, and explicit approval;
never send userId, cookie, session, token, provider grant, OAuth code, or storage grant;
return only safe status/UID/idempotency/canonical-link fields to the UI/API;
fall back to safe unavailable state when disabled or blocked.
```

If UI wiring is added, the existing importer review panel must clearly label the action as local/dev-only real save and must not imply production support. It should show:

```text
unsaved AI draft;
dry-run/review status;
explicit confirm/save action;
safe saved UID/status or safe unavailable/error;
local canonical link only if safe;
no raw prompts/provider output/stack traces/paths/tokens.
```

If UI wiring is not safe yet, implement the sidecar client/service and document the UI blocker precisely.

## Sidecar tests

Add focused tests for:

```text
transport disabled by default;
missing approval refuses before core call;
production/exposed/non-loopback target refusal;
Cloudflare/AWS/GitHub Actions/CI/tunnel guard refusal;
sidecar never sends userId/session/cookie/token/provider/storage fields;
safe candidate payload shape;
safe success envelope rendering;
safe unavailable/error envelope rendering;
idempotency/replay/conflict/duplicate statuses pass through safely;
leakage checks for prompts/provider output/secrets/stack traces/paths/tokens/sessions;
existing in-memory prototype remains available when real-save transport is disabled;
normal validation remains mock/offline and does not require Docker or live providers.
```

Optional local verification, only if both core route and sidecar transport are implemented safely:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034f

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

# Run the approved local sidecar-to-core save verification path with explicit local approval.
# Do not export, print, or save cookies/tokens/sessions.
# Do not call Google/OAuth/OpenAI/storage providers.

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

If the saved recipe cannot be observed in the Vanilla Cookbook UI without real session credentials, document that honestly. A safe core UID/read-after-write proof is acceptable for this task; browser/session UI observation remains blocked if it requires cookies/tokens/sessions or real credentials.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/sidecar-to-core-local-real-save-transport.md
outbox/0034F-sidecar-to-core-local-real-save-transport-results.md
```

Update as appropriate:

```text
README.md
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
sidecar never owns identity or storage;
core owns AuthUser/session/provider links/storage grants/recipe authorization;
Google OIDC real login remains later;
production Save-to-Cookbook remains not implemented;
any local real-save behavior targets only cookbook-local loopback/custom image;
direct sidecar DB writes and browser/session automation remain rejected;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external workspace branch/commit;
core dev-only route/transport implementation status or blocker;
local image tag/build result;
sidecar transport implementation status;
UI wiring status or blocker;
local verification result;
whether saved recipe can be observed in Vanilla Cookbook UI or why not;
auth/ownership/session boundary behavior;
idempotency/replay/conflict/duplicate behavior;
rollback/backup/restore behavior if exercised;
external focused tests/build results;
sidecar tests/validation results;
remaining blockers before production Save-to-Cookbook;
remaining blockers before real Google login;
explicit non-goals.
```

## Acceptance criteria

```text
A local-only sidecar-to-core transport is implemented or precisely blocked.
No external source is committed into this sidecar repository.
No production auth or production Save-to-Cookbook is implemented.
No real Google/OAuth/provider/storage call is made.
No cookie/token/session/OAuth code/real credential/browser state is created/exported/printed/committed.
Sidecar sends no userId/session/cookie/token/provider/storage grant.
Core owns the synthetic AuthUser and commit authorization.
Local custom image local/vanilla-cookbook-adapter:0034f is built or blocker is documented.
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
git add ai-api scripts docs README.md outbox/0034F-sidecar-to-core-local-real-save-transport-results.md

git commit -m "feat: add local sidecar core save transport"

git pull --rebase origin main

git push origin main
```
