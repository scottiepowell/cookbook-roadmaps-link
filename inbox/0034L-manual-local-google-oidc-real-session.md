# 0034L — Manual Local Google OIDC Real-Session Verification

Do not create a new task.
Do not implement production authentication.
Do not implement production Save-to-Cookbook.
Do not deploy.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or production data.
Do not request Google Drive/storage scopes.
Do not add direct sidecar database writes.
Do not use browser/session automation that exports or depends on credentials.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit OAuth client secrets, access tokens, refresh tokens, ID tokens, cookies, sessions, OAuth codes, browser state, real credentials, real profile data, DB files, uploads, logs, screenshots, traces, row dumps, prompts, provider outputs, local env values, source archives, generated indexes, or container snapshots.

## Goal

Implement and verify the first **manual local Google OIDC real-session path** in the separate Vanilla Cookbook workspace, using ignored local developer credentials and identity-only scopes.

This task follows `0034K`. It is a local/manual verification gate, not a production OAuth rollout. It may perform a manually approved local Google sign-in only if all custody, redaction, loopback, and ignored-config requirements are satisfied.

Desired local proof:

```text
Google identity-only sign-in
  -> Vanilla Cookbook core validates OIDC callback
  -> core creates/validates Lucia session cookie
  -> core maps/links Google subject to AuthUser/AuthAccount
  -> locals.user / requireAuth work under the real session
  -> core-owned Save-to-Cookbook authorization is available for that user
  -> no identity/session value is owned by the sidecar
```

## Context

`0034K` proved a core-owned mock OIDC real-session fixture without any external provider. It exercised real Lucia session creation, cookie setting in an in-memory jar, second-request session validation, `locals.user`, `requireAuth`, Save-to-Cookbook ownership, logout, and invalidation. The next approved step is a separate manual local Google OIDC task with ignored credentials and identity-only scopes.

`0034J` selected this ordering: mock OIDC first, then manual local Google OIDC with strict local-only custody.

## Read first

```text
outbox/0034K-core-owned-mock-oidc-real-session-fixture-results.md
docs/core-owned-mock-oidc-real-session-fixture.md
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
outbox/0034D-google-first-oidc-storage-auth-architecture-results.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all external source changes outside this sidecar repository.

Use only official Google OIDC, OpenID Connect, and Lucia documentation for any current provider/session facts. Cite official sources in sidecar docs. Do not rely on blog/tutorial copies for provider behavior.

## External core workspace work

In the external Vanilla Cookbook source workspace:

```text
Create branch: openclaw/0034L-manual-local-google-oidc-real-session
Base it on the latest approved external branch/commit from 0034K as appropriate.
```

Inspect the existing real OIDC routes and configuration, especially:

```text
Google/OIDC provider config
issuer discovery
redirect URI handling
state, nonce, and PKCE handling
callback validation
verified email handling
AuthUser/AuthAccount linking
session cookie creation and validation
logout/invalidation
local environment conventions
redaction/logging behavior
test harnesses for auth flows
```

Implement the smallest safe local/manual Google OIDC verification path.

Acceptable implementation shapes:

```text
A. A local-only verification script/runbook plus small guarded code fixes if the existing routes are already safe.
B. A disabled-by-default local Google OIDC verification route/helper that wraps the existing auth implementation without bypassing callback validation.
C. A precise blocker report if the existing route cannot be safely exercised without leaking credentials/tokens/sessions or changing production behavior.
```

The implementation must:

```text
remain disabled by default;
require explicit local enablement;
require loopback redirect URI only;
require identity-only scopes: openid, email, profile;
reject Google Drive/storage scopes;
use ignored local configuration for client ID/client secret/redirect URI;
never commit, print, persist, or copy secrets/tokens/cookies/session values;
validate state, nonce, PKCE, issuer, audience/client, expiry, and email verification according to the core implementation and provider requirements;
derive or link AuthUser/AuthAccount only inside the Vanilla Cookbook core;
create and validate a real Lucia session cookie in a local client/browser context without exporting the cookie value;
verify locals.user and requireAuth under the real session;
verify logout invalidates the session;
keep sidecar out of userId/session/cookie/provider-token/storage-grant ownership;
keep normal repository validation mock/offline;
fail closed if any local gate, credential, redirect, state, PKCE, or scope requirement is unsafe.
```

The implementation must not:

```text
add production auth;
add production Save-to-Cookbook;
request Drive/storage scopes;
store refresh tokens for future Drive/BYOS;
use production domain redirects;
use Cloudflare/AWS/tunnels/GitHub Actions;
export cookies/tokens/sessions to the sidecar;
add direct sidecar DB writes;
commit local env values, screenshots, traces, browser storage, DB/upload artifacts, or provider outputs;
use browser automation that depends on or exports credentials.
```

## Manual operator steps

If a live local Google OIDC test is possible, document a manual operator runbook that clearly separates repo-safe steps from private local steps.

The runbook may instruct the operator to create a local Google OAuth client manually, but must not create it automatically. It must specify:

```text
local-only redirect URI, such as http://127.0.0.1:3000/auth/google/callback or the actual reviewed local callback path;
identity-only scopes: openid email profile;
ignored local env/config file location;
redaction expectations;
how to start cookbook-local with the custom image;
how to perform the manual sign-in;
how to verify safe status without printing secrets/tokens/cookies;
how to logout and cleanup;
how to remove local credentials after testing.
```

Do not include any real client ID, client secret, OAuth code, token, cookie, session value, profile data, or local env value in committed docs or outbox.

## Verification goals

Verify as much as safely possible:

```text
Google sign-in starts only under local gates;
callback rejects bad state/nonce/PKCE/audience/issuer where testable without live provider leakage;
real Google callback, if manually exercised, creates/links AuthUser/AuthAccount;
real Lucia session cookie is set and validated without printing the value;
second authenticated request populates locals.user;
requireAuth-protected core route works under the real session;
logout invalidates the session;
sidecar receives no identity/session/cookie/provider token;
Save-to-Cookbook remains core-owned and ready for later authenticated observation;
Drive/storage scopes remain absent;
all logs/output are redacted.
```

If a real Google login cannot be safely verified in the current environment, document the precise blocker and still land any offline-safe tests/docs/runbook improvements.

## Tests

Add or update focused external tests where possible for:

```text
local Google config disabled by default;
identity-only scopes only;
Drive/storage scope rejection;
loopback redirect requirement;
production/CI/tunnel refusal;
missing client config refusal without leaking config names/values;
state/nonce/PKCE validation behavior where locally testable;
provider-link replay/collision behavior remains safe;
no cookie/token/session/client secret appears in safe envelopes/log-like output;
mock OIDC real-session fixture from 0034K still passes;
Save-to-Cookbook ownership still derives from core session/AuthUser context.
```

Build a new local-only image if tests/build pass:

```text
local/vanilla-cookbook-adapter:0034l
```

Do not push or deploy the image.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/manual-local-google-oidc-real-session.md
outbox/0034L-manual-local-google-oidc-real-session-results.md
```

Update as appropriate:

```text
README.md
docs/core-real-authenticated-session-plan.md
docs/core-owned-mock-oidc-real-session-fixture.md
docs/google-first-core-oidc-local-auth-spike.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Docs must clearly state:

```text
manual Google OIDC is local-only and disabled by default;
Google sign-in uses identity-only scopes;
Google Drive/storage consent remains a later BYOS task;
private local credentials are ignored and never committed;
core owns AuthUser/AuthAccount/AuthSession/session cookie/recipe authorization;
sidecar owns no userId/session/cookie/provider token/storage grant;
production auth and production Save-to-Cookbook remain unimplemented;
normal validation remains mock/offline;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external branch/commit;
existing route/config findings;
implementation status or blocker;
manual local Google OIDC runbook status;
whether a real local Google login was actually exercised;
real session cookie lifecycle evidence, without cookie values;
AuthUser/AuthAccount linking evidence, without profile data;
locals.user/requireAuth evidence;
logout/invalidation evidence;
Save-to-Cookbook readiness under real session;
Drive/storage scope deferral evidence;
redaction/leakage behavior;
custom image tag/build result;
external focused tests/build results;
sidecar validation results;
remaining blockers before browser-observed authenticated Save-to-Cookbook;
remaining blockers before production auth;
explicit non-goals.
```

## Acceptance criteria

```text
Manual local Google OIDC real-session path is implemented, verified, or precisely blocked.
No production auth or production Save-to-Cookbook is implemented.
No Drive/storage scopes are requested.
No secrets, OAuth codes, access tokens, refresh tokens, ID tokens, cookies, sessions, real credentials, real profile data, browser artifacts, DB files, uploads, local env values, traces, screenshots, prompts, provider output, or row dumps are committed.
Core-owned identity/session boundary is preserved.
Sidecar remains out of identity/session ownership.
Local private credential custody and cleanup are documented.
Custom local image local/vanilla-cookbook-adapter:0034l is built or blocker is documented.
Next task after 0034L is clearly specified.
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

Do not run live OpenAI, Microsoft, storage, or production calls. A manual local Google OIDC call is allowed only when explicitly approved by the operator and all local-only gates are satisfied; otherwise keep the task offline and document the blocker.

Commit external workspace changes if appropriate and record that external commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034L-manual-local-google-oidc-real-session-results.md

git commit -m "docs: record manual local google oidc session"

git pull --rebase origin main

git push origin main
```
