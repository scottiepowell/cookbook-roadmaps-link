# 0034M — Manual Local Google OIDC Login Verification

Do not create a new task.
Do not implement production authentication.
Do not implement production Save-to-Cookbook.
Do not deploy.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or production data.
Do not request Google Drive/storage scopes.
Do not call Microsoft, OpenAI, storage providers, or unrelated live external providers.
Do not commit, print, export, persist, or save OAuth client secrets, access tokens, refresh tokens, ID tokens, cookies, sessions, OAuth codes, browser state, real credentials, real profile data, `.env` values, DB files, uploads, logs, screenshots, traces, row dumps, prompts, provider outputs, source archives, generated indexes, or container snapshots.
Do not add direct sidecar database writes.
Do not use browser/session automation that exports or depends on credentials.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.

## Goal

Perform the explicitly approved **manual local Google OIDC login verification** that remained blocked after `0034L` because no local Google credentials were available.

This task is a manual/local-only verification gate. It should prove that the hardened `0034L` Google OIDC path can create a real core-owned authenticated session from a developer-created local Google OAuth client, using only identity scopes:

```text
openid email profile
```

This task must not wire saved-recipe browser observation yet. It should only prove safe login/session state first. A later task may use this evidence to verify authenticated Save-to-Cookbook browser/UI observation.

## Context

`0034K` proved real Lucia session lifecycle with mock OIDC and no external provider.

`0034L` hardened the manual local Google OIDC path with loopback, Google issuer, identity-only scope, nonce, state, PKCE, callback validation, and fail-closed configuration guards. No Google call occurred because no ignored local credentials were supplied.

The remaining blocker recorded by `0034L` is an explicitly approved developer-created local Google OAuth client and a manual loopback login. Values must remain only in ignored local configuration, and the report must include only safe authenticated-state outcomes.

## Read first

```text
outbox/0034L-manual-local-google-oidc-real-session-results.md
docs/manual-local-google-oidc-real-session.md
outbox/0034K-core-owned-mock-oidc-real-session-fixture-results.md
docs/core-owned-mock-oidc-real-session-fixture.md
outbox/0034J-core-real-authenticated-session-plan-results.md
docs/core-real-authenticated-session-plan.md
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

Use only official Google/OIDC/Lucia documentation if current external facts are needed. Cite official sources in sidecar docs. Do not include raw URLs in committed secrets/config examples if they expose local private values.

## Manual setup guidance

The operator may create or supply a local Google OAuth client outside the repository, using only ignored local configuration. The OAuth client must be limited to loopback/local development redirect URIs. Record only safe setup shape, not actual values.

Allowed verification target examples:

```text
http://127.0.0.1:3000
http://localhost:3000
```

Allowed identity-only scopes:

```text
openid email profile
```

Forbidden scopes include any Google Drive, storage, Gmail, calendar, broad Google API, offline storage, or unrelated provider scopes.

## External workspace work

In the external Vanilla Cookbook source workspace, create a branch only if code/runbook hardening is needed:

```text
openclaw/0034M-manual-local-google-oidc-login-verification
```

Prefer no code change if `0034L` is sufficient.

Run only the approved manual local Google OIDC verification path. It must:

```text
use ignored local credentials only;
use loopback redirect URI only;
request only openid email profile;
exercise real Google OIDC start/callback manually;
validate issuer/audience/state/nonce/PKCE/callback behavior through the core path;
create or validate a real Lucia session inside the core app;
populate locals.user / requireAuth;
link or replay AuthAccount/AuthUser safely;
validate logout/session invalidation if practical;
report only safe authenticated-state outcomes.
```

The verification must not:

```text
print or commit client ID/secret;
print or commit OAuth code, access token, refresh token, ID token, cookie, or session value;
print real profile data beyond a safe boolean/opaque status;
request Google Drive or storage scopes;
call sidecar provider workflows;
wire Save-to-Cookbook browser observation;
modify production behavior;
create DB/upload/browser artifacts in the sidecar repository.
```

If manual login cannot be run because credentials are unavailable, document the exact blocker and leave the task precisely blocked without faking provider success.

## Sidecar repository updates

Create:

```text
docs/manual-local-google-oidc-login-verification.md
outbox/0034M-manual-local-google-oidc-login-verification-results.md
```

Update as appropriate:

```text
README.md
docs/manual-local-google-oidc-real-session.md
docs/core-owned-mock-oidc-real-session-fixture.md
docs/core-real-authenticated-session-plan.md
docs/google-first-core-oidc-local-auth-spike.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The outbox must summarize:

```text
whether manual local Google credentials were available;
local-only OAuth client setup shape without secret values;
identity-only scope verification;
loopback redirect verification;
Google issuer/callback/session validation status;
Lucia session creation/locals.user/requireAuth status;
AuthUser/AuthAccount link or replay behavior;
logout/invalidation status if exercised;
safe evidence only, with no secrets/tokens/cookies/sessions/profile data;
whether authenticated saved-recipe browser observation remains a later task;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
Manual local Google OIDC login is verified or precisely blocked.
No production authentication or production Save-to-Cookbook is implemented.
Only identity scopes openid email profile are allowed.
No Google Drive/storage scopes are requested.
No OAuth client secret, token, cookie, session, OAuth code, real credential, browser state, profile data, DB file, upload, local env value, screenshot, trace, row dump, prompt, provider output, or source archive is committed.
Core owns AuthUser/session/provider links and authorization.
Sidecar receives no identity/session/cookie/provider/storage values.
Next task after 0034M is clearly specified.
```

## Validation

Run:

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

Do not run live OpenAI, Microsoft, storage, or unrelated provider calls.

Commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034M-manual-local-google-oidc-login-verification-results.md

git commit -m "docs: verify manual local google oidc login"

git pull --rebase origin main

git push origin main
```
