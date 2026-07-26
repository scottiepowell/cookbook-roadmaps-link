# 0034I — Local UI Persistent Save E2E Verification

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
Do not use browser/session automation that exports or depends on credentials.
Do not add direct sidecar database writes.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, sessions, OAuth state, or real profile data.

## Goal

Verify the `0034H` local/dev-only UI real-save wiring end-to-end against the already-proven `0034G` persistent core route and `cookbook-local` disposable runtime.

This is a validation task, not a new product feature. It may perform one approved disposable local persistent save through the sidecar UI/API path, but only against `cookbook-local` with backup/restore and safe evidence.

The supported observation is the sidecar UI/API safe UID/read-after-write/status envelope. Do not require browser observation inside Vanilla Cookbook if that would require a real authenticated session, cookie, token, or browser state.

## Read first

```text
outbox/0034H-local-ui-real-save-wiring-results.md
docs/local-ui-real-save-wiring.md
outbox/0034G-core-owned-local-persistent-user-auth-transport-results.md
docs/core-owned-local-persistent-user-auth-transport.md
outbox/0034F-sidecar-to-core-local-real-save-transport-results.md
docs/sidecar-to-core-local-real-save-transport.md
outbox/0034E-google-first-core-oidc-local-auth-spike-results.md
docs/google-first-core-oidc-local-auth-spike.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
ai-api/app/cookbook_core_transport.py
ai-api/app/static/demo.js
ai-api/app/main.py
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

## Verification scope

Use the existing external core image:

```text
local/vanilla-cookbook-adapter:0034g
```

Do not create a new external core branch unless a precise blocker or tiny guarded verification fix is required. If any external change is required, keep it outside this sidecar repository and record the external branch/commit.

Implement the smallest safe local E2E verification path, such as a PowerShell script, Python script, pytest, or Playwright-style UI test, that proves:

```text
start cookbook-local with 0034g image and local fixture gates;
start or exercise the sidecar in mock/offline mode with 0034H gates enabled;
create or use a synthetic reviewed importer candidate;
perform dry-run/review state;
require explicit local confirmation;
call the sidecar local persistent save route;
sidecar calls the 0034G core persistent route;
core performs disposable persistent commit and read-after-write;
sidecar UI/API receives and renders/returns safe status/UID/link/idempotency fields;
restore/cleanup leaves ignored local DB/uploads safe;
stop local runtime.
```

If UI automation is brittle or unavailable, API-level verification through the sidecar route is acceptable, but document the UI limitation precisely. Prefer UI-level assertion when safe and deterministic.

## Required guards

The verification must refuse unless:

```text
explicit local approval is supplied;
normal validation is not running in production/CI;
target is loopback only, such as http://127.0.0.1:3000;
Compose project is cookbook-local;
image marker is local/vanilla-cookbook-adapter:0034g;
local persistent save gates are explicitly enabled;
no Cloudflare/AWS/GitHub Actions/tunnel indicators are active;
no cookie/token/session/OAuth/provider/storage values are supplied.
```

The verification must not:

```text
call live OpenAI or other providers;
run real Google/OAuth login;
export or print cookies/tokens/sessions;
write direct sidecar DB data;
commit DB/upload/browser/runtime artifacts;
print recipe bodies, row dumps, SQL, absolute paths, env values, prompts, provider output, or stack traces.
```

## Tests and evidence

Add focused tests or verification assertions for:

```text
disabled-by-default refusal;
missing approval refusal;
non-loopback/production/CI/tunnel refusal;
exact 0034g image marker requirement;
sidecar sends no userId/session/cookie/token/provider/storage grants;
safe candidate payload only;
safe success envelope displayed or returned;
read-after-write status present;
idempotency/replay/conflict/duplicate statuses handled safely when exercised;
network/core unavailable returns safe unavailable state;
leakage checks for prompts/provider output/secrets/stack traces/paths/tokens/sessions;
cleanup/restore behavior documented.
```

## Sidecar repository updates

Create:

```text
docs/local-ui-persistent-save-e2e-verification.md
outbox/0034I-local-ui-persistent-save-e2e-verification-results.md
```

Update as appropriate:

```text
README.md
docs/local-ui-real-save-wiring.md
docs/core-owned-local-persistent-user-auth-transport.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The outbox must summarize:

```text
whether UI-level or API-level local E2E verification was used;
exact local commands run;
local image and Compose project used;
sidecar route/UI path exercised;
safe UID/read-after-write/status evidence;
cleanup/restore result;
whether Vanilla Cookbook browser observation remains blocked by real session requirements;
sidecar/core identity boundary behavior;
validation results;
remaining blockers before production Save-to-Cookbook;
remaining blockers before real Google login;
explicit non-goals.
```

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet

& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Run any focused local E2E command added by this task with explicit approval and record the result.

Do not run live OpenAI, Google, Microsoft, OAuth, or storage calls.

Commit sidecar changes:

```bash
git add ai-api scripts docs README.md outbox/0034I-local-ui-persistent-save-e2e-verification-results.md

git commit -m "test: verify local ui persistent save e2e"

git pull --rebase origin main

git push origin main
```