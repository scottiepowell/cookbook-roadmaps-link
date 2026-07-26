# 0034K — Core-Owned Mock OIDC Real Session Fixture

Do not create a new task.
Do not implement production authentication.
Do not implement production Save-to-Cookbook.
Do not implement real Google login.
Do not call Google, Microsoft, OpenAI, storage providers, OAuth providers, or live external providers.
Do not request Google Drive or storage scopes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or production data.
Do not create, export, print, persist, or commit real OAuth client secrets, access tokens, refresh tokens, ID tokens, cookies, sessions, OAuth codes, browser state, real credentials, real profile data, DB files, uploads, logs, screenshots, traces, row dumps, prompts, provider outputs, local env values, source archives, generated indexes, or container snapshots.
Do not add direct sidecar database writes.
Do not use browser/session automation that exports or depends on credentials.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.

## Goal

Implement the next real-session step recommended by `0034J`: a **core-owned, loopback-only, disabled-by-default mock OIDC session fixture** in the separate Vanilla Cookbook workspace.

This task must exercise the real Vanilla Cookbook/Lucia session lifecycle without any external provider call:

```text
mock OIDC synthetic claims
  -> core-owned OIDC callback/session path or equivalent guarded fixture
  -> AuthUser/AuthAccount link or replay/collision handling
  -> real core session cookie lifecycle in an in-memory/local test client
  -> protected locals.user / requireAuth verification
  -> core-owned Save-to-Cookbook adapter under authenticated user context
  -> logout/session invalidation verification
```

This is still not production auth, not real Google login, and not production Save-to-Cookbook.

## Context

`0034I` proved the disposable local save flow through the sidecar and `0034G` persistent core route, but browser observation remained unavailable because no real authenticated session exists.

`0034J` found that the core already owns Lucia, Prisma-backed `AuthUser`/`AuthSession`, `AuthAccount`, `locals.user`, `requireAuth`, session creation, validation, and logout invalidation. It also found that the existing OIDC callback uses issuer discovery, state and PKCE handoff cookies, `openid-client` validation, verified-email matching/provisioning, provider linking, `auth.createSession`, and `locals.auth.setSession`.

`0034J` recommended option B first: a core-owned mock OIDC fixture that exercises the real session cookie lifecycle without Google, then a later manual local Google task only after this passes.

## Read first

From this sidecar repository:

```text
outbox/0034J-core-real-authenticated-session-plan-results.md
docs/core-real-authenticated-session-plan.md
outbox/0034I-local-ui-persistent-save-e2e-verification-results.md
docs/local-ui-persistent-save-e2e-verification.md
outbox/0034H-local-ui-real-save-wiring-results.md
docs/local-ui-real-save-wiring.md
outbox/0034G-core-owned-local-persistent-user-auth-transport-results.md
docs/core-owned-local-persistent-user-auth-transport.md
outbox/0034E-google-first-core-oidc-local-auth-spike-results.md
docs/google-first-core-oidc-local-auth-spike.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all external source changes outside this sidecar repository.

Use official Lucia/OIDC/Google documentation only if current external facts are required. Cite official sources in sidecar docs. Do not create provider apps, secrets, OAuth codes, tokens, or real sessions outside the guarded local/mock fixture.

## External core workspace work

In the external Vanilla Cookbook source workspace:

```text
Create branch: openclaw/0034K-core-owned-mock-oidc-real-session-fixture
Base it on the latest approved external branch/commit from 0034G/0034E as appropriate.
```

Implement the smallest safe mock OIDC real-session fixture that exercises the existing core session machinery without external provider calls.

Acceptable shapes:

```text
A local/dev-only mock OIDC callback route guarded by explicit fixture flags.
A test-only in-process callback verifier that drives the real session helpers.
A local script/test harness using an in-memory cookie jar and disposable DB.
```

Prefer the shape that proves the real session cookie lifecycle with the least new surface area.

The fixture must:

```text
remain disabled by default;
require explicit local/mock-session enablement;
require loopback/local test context;
reject production, exposed, Cloudflare, AWS, GitHub Actions, CI, or tunnel contexts;
use synthetic OIDC identity claims only;
use identity-only concepts: issuer, subject, email, email_verified, display name/avatar if present;
reject Google Drive/storage scopes;
call no external discovery/token/userinfo/provider endpoint;
create or link AuthUser/AuthAccount only inside the core process;
exercise real auth.createSession / setSession or the current equivalent session helpers;
verify locals.user / requireAuth works after session creation;
verify logout/session invalidation;
verify account-link replay is idempotent;
verify verified-email/provider-subject collision or recovery behavior is safe;
verify Save-to-Cookbook adapter derives ownership from the authenticated core user context;
use only disposable local/test database and uploads, with backup/restore or isolated cleanup;
use only an in-memory test cookie jar or equivalent non-exported local client state;
return or record only safe status summaries.
```

The fixture must not:

```text
call Google, Microsoft, OpenAI, OAuth, storage, or live providers;
create or use real Google Cloud credentials;
request Drive/storage scopes;
print, persist, export, or commit cookies, sessions, tokens, OAuth codes, secrets, auth headers, browser state, DB rows, SQL, paths, env values, profile data, prompts, provider output, stack traces, screenshots, logs, or uploads;
accept sidecar-supplied userId/session/cookie/token/provider/storage claims;
write categories/media/uploads/remote images/embeddings unless already required by existing safe core behavior;
use browser automation that exports or depends on credentials;
change production auth or production deployment behavior.
```

If real session verification cannot be done safely without leaking cookies/session state, document the blocker precisely and do not add unsafe routes.

## Tests in external workspace

Add focused tests for:

```text
disabled-by-default refusal;
production/CI/exposed/tunnel guard refusal;
mock OIDC claims validation;
invalid issuer/audience/subject/profile rejection;
unverified email behavior is explicit and safe;
Drive/storage scope rejection;
no external provider calls;
AuthUser/AuthAccount link creation under core control;
existing account replay/idempotency;
provider-subject/email collision or review handling;
real session cookie created only inside in-memory/local test client;
locals.user populated after session validation;
requireAuth allows authenticated route after session creation;
logout/session invalidation clears access;
Save-to-Cookbook adapter derives ownership from authenticated core user;
sidecar identity/session/token claims rejected if present;
no safe envelope leaks cookies/tokens/sessions/secrets/paths/prompts/provider output/row dumps;
backup/restore or isolated cleanup leaves no committed runtime artifacts.
```

Run focused external tests and relevant Prisma/generation/build/typecheck steps. Record exact commands/results in the outbox.

Build a new local-only image if focused tests/build pass:

```text
local/vanilla-cookbook-adapter:0034k
```

Do not push or deploy the image.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/core-owned-mock-oidc-real-session-fixture.md
outbox/0034K-core-owned-mock-oidc-real-session-fixture-results.md
```

Update as appropriate:

```text
README.md
docs/core-real-authenticated-session-plan.md
docs/google-first-core-oidc-local-auth-spike.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-ui-persistent-save-e2e-verification.md
docs/local-ui-real-save-wiring.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly state:

```text
source remains outside this sidecar repository;
mock OIDC fixture is local/dev-only and disabled by default;
real Google login is still not implemented;
Google Drive/storage consent remains a separate later BYOS task;
core owns AuthUser/session/provider links/storage grants/recipe authorization;
sidecar owns no userId/session/cookie/provider token/storage grant;
session cookies are exercised only inside safe local/test client state and are never printed or committed;
production authentication and production Save-to-Cookbook remain unimplemented;
normal sidecar real-user UI observation remains a later task unless this fixture safely proves it;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external workspace branch/commit;
fixture shape and route/script/test harness used;
real session lifecycle behavior proven or blocker;
AuthUser/AuthAccount mapping behavior;
locals.user / requireAuth behavior;
logout/session invalidation behavior;
Save-to-Cookbook ownership behavior under authenticated core context;
collision/replay behavior;
local image tag/build result;
external focused tests/build results;
whether sidecar UI/browser observation remains blocked;
remaining blockers before manual local Google OIDC;
remaining blockers before production Save-to-Cookbook;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
Core-owned mock OIDC real-session fixture is implemented or precisely blocked.
No external source is committed into this sidecar repository.
No production auth or production Save-to-Cookbook is implemented.
No Google/Microsoft/OAuth/provider/storage call is made.
No cookies, sessions, tokens, OAuth codes, client secrets, real credentials, real profile data, browser artifacts, DB files, uploads, local env values, traces, screenshots, prompts, provider output, row dumps, or source snapshots are committed.
Session lifecycle is exercised only through safe local/test client state without export.
AuthUser/AuthAccount mapping is core-owned.
locals.user / requireAuth are verified or blocker is documented.
Logout/session invalidation is verified or blocker is documented.
Save-to-Cookbook ownership derives from authenticated core user context or blocker is documented.
Google Drive/storage scopes are not requested and remain deferred.
Provider-neutral shape still allows later manual Google and Microsoft/OneDrive evaluation.
Custom local image local/vanilla-cookbook-adapter:0034k is built or blocker is documented.
Next task after 0034K is clearly recommended.
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

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034K-core-owned-mock-oidc-real-session-fixture-results.md

git commit -m "docs: record mock oidc real session fixture"

git pull --rebase origin main

git push origin main
```
