# 0034J — Core Real Authenticated Session Plan

Do not create a new task.
Do not implement production Save-to-Cookbook.
Do not deploy.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or production data.
Do not call Google, Microsoft, OpenAI, storage providers, OAuth providers, or live external providers.
Do not create or commit real OAuth client secrets, access tokens, refresh tokens, ID tokens, cookies, sessions, OAuth codes, browser state, real credentials, real profile data, DB files, uploads, logs, screenshots, traces, row dumps, prompts, provider outputs, local env values, source archives, generated indexes, or container snapshots.
Do not request Google Drive/storage scopes.
Do not add direct sidecar database writes.
Do not use browser/session automation that exports or depends on credentials.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.

## Goal

After `0034I`, pause the synthetic/local-save expansion track and plan the next phase required for true end-to-end Save-to-Cookbook: **core-owned real authenticated sessions**.

This task is a security/design and implementation-readiness task, not a production OAuth rollout. It should define the smallest safe path from the existing `0034E` Google-first OIDC foundation to a real local authenticated session in the Vanilla Cookbook core.

The desired future product flow is:

```text
Google identity-only sign-in
  -> Vanilla Cookbook core validates OIDC callback
  -> core creates/validates session cookie
  -> core maps/links provider identity to AuthUser/AuthAccount
  -> authenticated user saves AI-reviewed recipe through core-owned adapter
  -> sidecar remains a candidate generator/client and never owns identity
```

## Context

`0034E` found that the core already owns Lucia `AuthUser` and sessions through `locals.user`, and already has a Prisma `AuthAccount` provider-link model/migration. It added an offline Google-first identity foundation but did not add real routes, clients, cookies, sessions, or durable provider links.

`0034G` proved persistent local saves with a core-created synthetic `AuthUser` and disposable DB/uploads restore.

`0034H` wired the local sidecar UI to the gated persistent transport but did not perform local runtime writes.

`0034I` is the final validation task for the current synthetic/local-save track. After it, do not keep extending synthetic auth unless the task finds a blocking safety gap.

## Read first

```text
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
docs/sidecar-real-save-local-wiring-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all external source inspection or change notes outside this sidecar repository.

Use official Google/Microsoft/OIDC/Lucia documentation only if current external facts are required. Cite official sources in docs. Do not create provider apps, secrets, OAuth codes, or tokens.

## Required analysis

In the external Vanilla Cookbook workspace, inspect and document the real auth/session path:

```text
Lucia auth/session helpers
current login/logout routes
locals.user population
requireAuth behavior
session cookie creation/validation/invalidation
CSRF/state/nonce/PKCE support or absence
existing OAuth/OIDC route implementation
AuthUser/AuthAccount schema and migration status
provider account linking and collision behavior
redirect URI handling
local dev configuration conventions
secret/config custody expectations
test harness patterns for auth without leaking cookies/tokens
```

## Deliverable

Create a concrete plan for the next implementation task, likely `0034K`, that gets to a real local authenticated session safely.

The plan must decide whether the next implementation should be:

```text
A. Core-owned local real Google OIDC session with developer-created local Google OAuth app and ignored secrets.
B. Core-owned local mock OIDC provider that exercises real session creation without Google.
C. Core-owned local email/password or magic-link session bootstrap as an interim auth path.
D. Blocked until upstream auth/session risks are resolved.
```

Expected recommendation: prefer **B first if it can exercise real session creation without external provider calls**, then A as a manual/local-only Google credential task. If B cannot meaningfully exercise Lucia/session cookies, document why and recommend A with strict manual operator steps and ignored secrets.

## Required boundaries for the future implementation plan

The future real-session task must preserve:

```text
core owns AuthUser/session/provider links/storage grants/recipe authorization;
sidecar never owns userId/session/cookie/provider token/storage grant;
Google login uses identity-only scopes: openid, email, profile;
Google Drive/storage scopes remain a separate later BYOS consent;
provider tokens/secrets are never committed or printed;
local dev secrets live only in ignored local env/config;
normal validation stays mock/offline;
production auth and production Save-to-Cookbook remain separate approval gates.
```

## Sidecar repository updates

Create:

```text
docs/core-real-authenticated-session-plan.md
outbox/0034J-core-real-authenticated-session-plan-results.md
```

Update as appropriate:

```text
README.md
docs/google-first-core-oidc-local-auth-spike.md
docs/google-first-oidc-storage-auth-architecture.md
docs/local-ui-real-save-wiring.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The outbox must summarize:

```text
0034I outcome considered;
existing core auth/session findings;
real session gaps;
OIDC callback/session/cookie/linking risks;
recommended next implementation path;
whether mock OIDC real-session testing is viable;
whether manual Google local credentials are required;
what must remain ignored/local-only;
remaining blockers before sidecar UI can observe real Cookbook saved recipes;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
A clear real-authenticated-session path is documented.
No production auth or production Save-to-Cookbook is implemented.
No Google/OAuth/provider/storage calls are made.
No secrets, cookies, tokens, sessions, OAuth codes, real credentials, real profile data, browser artifacts, DB files, uploads, local env values, traces, screenshots, prompts, provider output, or row dumps are committed.
Core-owned identity/session boundary is preserved.
Sidecar remains out of identity/session ownership.
The next task after 0034J is clearly specified.
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

Do not run live OpenAI, Google, Microsoft, OAuth, or storage calls.

Commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034J-core-real-authenticated-session-plan-results.md

git commit -m "docs: plan core real authenticated sessions"

git pull --rebase origin main

git push origin main
```
