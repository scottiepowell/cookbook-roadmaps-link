# 0034E — Google-First Core OIDC Local Auth Spike

Do not create a new task.
Do not implement production authentication.
Do not implement production Save-to-Cookbook.
Do not wire the normal sidecar UI real-save button.
Do not add production routes.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not bypass production auth.
Do not create, export, print, persist, or commit cookies, auth tokens, sessions, OAuth codes, refresh tokens, access tokens, ID tokens, client secrets, real user credentials, browser state, or real account data.
Do not call Google, Microsoft, OpenAI, storage providers, or live external providers.
Do not request Google Drive or storage scopes in this task.
Do not add direct sidecar database writes.
Do not use browser/session automation.
Do not add analytics, ads, payment, provider routing changes, QMD integration, or live calls.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, sessions, OAuth state, or real profile data.

## Goal

Start the product authentication path recommended by `0034D`: a **Google-first, core-owned OIDC local auth spike** in the separate Vanilla Cookbook workspace.

This is not a production OAuth rollout. The goal is to create the smallest safe core-owned identity architecture/code path that prepares for Google sign-in later while preserving the current security boundary:

```text
Vanilla Cookbook core owns AuthUser, sessions, provider links, token grants, storage connections, and Save-to-Cookbook authorization.
AI sidecar remains a reviewed candidate generator/client and owns none of those values.
```

Use a local mock/OIDC-fixture provider or unit-test-only callback verification. Do not call Google or require real Google credentials.

## Context

`0034C` completed the dev-only synthetic auth fixture. It proved dry-run-before-commit, commit, read-after-write, replay/conflict, duplicate blocking, rollback, and backup/restore with synthetic in-process `AuthUser`, without exporting cookies, tokens, sessions, real credentials, or browser state.

`0034D` decided:

```text
Google is the first planned external OIDC candidate in the Vanilla Cookbook core.
Sign-in uses identity-only consent.
Google Drive is a later, separate BYOS consent step.
Provider-neutral identity/storage contracts are planned so Microsoft identity plus OneDrive/Graph can be evaluated next.
The core owns AuthUser, sessions, provider links, token grants, storage connections, and Save-to-Cookbook authorization.
The AI sidecar remains a reviewed candidate generator/client and owns none of those values.
```

The next implementation step should build a local/provider-neutral auth foundation in the core app, not sidecar-owned auth and not Drive/storage consent.

## Read first

From this sidecar repository:

```text
outbox/0034D-google-first-oidc-storage-auth-architecture-results.md
docs/google-first-oidc-storage-auth-architecture.md
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
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all external source changes outside this sidecar repository.

Use the official provider citations already recorded in `0034D`. If additional current provider facts are required, use only official Google/Microsoft docs and cite them in sidecar docs. Do not create or use real provider apps, client secrets, OAuth codes, or tokens.

## External workspace work

In the external Vanilla Cookbook source workspace:

```text
Create branch: openclaw/0034E-google-first-core-oidc-local-auth-spike
Base it on the latest approved external adapter/auth branch/commit from 0034C as appropriate.
```

Inspect the existing core auth implementation first:

```text
Lucia/auth helpers
AuthUser/User schema
session creation and validation path
login/logout routes
current locals.user / requireAuth behavior
Prisma schema around users/sessions
existing test harness patterns
```

Document whether the core already supports provider account linking, OAuth state/nonce/PKCE, callback verification, or only local credentials.

## Implementation scope

Implement the smallest safe Google-first/provider-neutral OIDC foundation that can be verified offline.

Preferred shape:

```text
core-owned provider account model or service contract
provider-neutral OIDC profile normalization service
Google provider descriptor/config validation
local mock OIDC callback verifier or unit-test-only OIDC fixture
core AuthUser mapping/linking service
safe login/start/callback route skeletons only if they do not call real providers
```

The implementation must:

```text
remain disabled by default;
require explicit local enablement for any route behavior;
not call Google or Microsoft;
not require real client ID/client secret;
not store or print tokens;
not request Drive/storage scopes;
use identity-only OIDC concepts only: subject, issuer, email, email_verified, display name/avatar if available;
derive or create core AuthUser only inside Vanilla Cookbook core;
store provider link metadata only if a reviewed local schema/migration strategy is safe;
separate identity linking from future storage grants;
keep Save-to-Cookbook authorization core-owned;
keep sidecar out of userId/session/provider-token ownership;
return only safe status/profile mapping envelopes in tests;
fail closed when provider config is missing, invalid, production, or enabled without explicit local gates.
```

If durable provider linking requires a schema migration, do not add an unreviewed production migration. Either:

```text
use an existing safe model if present;
implement a pure service/contract plus tests without persistent schema changes; or
document the required migration as a blocker for a separate migration-review task.
```

Do not implement Google Drive/BYOS storage in this task. The Google Drive/storage consent path remains separate and later.

## Route/scaffold guidance

Route scaffolding is allowed only if safe and disabled by default.

Possible local-only route shapes:

```text
GET /auth/google/start
GET /auth/google/callback
```

But these routes must not call Google or exchange codes in this task unless a fully mocked provider path is used under local/test-only gates. It is acceptable to implement only services/tests and document route wiring as the next step if route scaffolding would require unsafe OAuth configuration.

Any route or helper must reject:

```text
production mode;
missing local auth feature flag;
missing explicit local approval for mock flow;
non-loopback/exposed target;
Cloudflare/AWS/GitHub Actions/CI/tunnel indicators;
real provider token/code/client secret input;
sidecar-supplied userId/session/cookie/token/provider grant;
Drive/storage scopes.
```

## Tests in external workspace

Add focused tests for:

```text
Google provider descriptor uses identity-only scopes only;
Drive/storage scopes are rejected/deferred;
provider config disabled by default;
invalid issuer/audience/profile is rejected safely;
unverified email behavior is explicit and safe;
provider subject maps to a core provider-link identity, not sidecar identity;
AuthUser mapping/linking is core-owned;
existing AuthUser link replay is idempotent;
same provider subject with conflicting verified email returns safe conflict/review status;
sidecar-supplied userId/session/cookie/token/provider grant is rejected;
no tokens/client secrets/cookies/sessions are returned in envelopes;
production/CI/exposed/tunnel guard refusal works if route/scaffold exists;
Google Drive/storage scopes are not requested;
Save-to-Cookbook adapter still derives ownership from core AuthUser context.
```

Run focused external tests and relevant build/typecheck commands. Record exact commands/results in the outbox.

Build a new local-only image if focused tests/build pass:

```text
local/vanilla-cookbook-adapter:0034e
```

Do not push or deploy the image.

Optional sidecar local startup verification:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034e

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run a real OAuth browser login. Do not create Google Cloud credentials. Do not call Google.

## Sidecar repository updates

Do not copy external source into this sidecar repo.

Create:

```text
docs/google-first-core-oidc-local-auth-spike.md
outbox/0034E-google-first-core-oidc-local-auth-spike-results.md
```

Update as appropriate:

```text
README.md
docs/google-first-oidc-storage-auth-architecture.md
docs/core-owned-dev-only-synthetic-auth-fixture.md
docs/sidecar-real-save-local-wiring-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The docs must clearly state:

```text
source remains outside this sidecar repository;
Google is first planned OIDC provider;
OIDC sign-in is identity-only;
Google Drive/storage consent remains a later separate BYOS step;
core owns AuthUser/session/provider links/token grants/storage connections/Save-to-Cookbook authorization;
sidecar owns no userId/session/cookie/provider token/storage grant;
0034C synthetic-auth fixture remains valid and independent of real SSO;
production auth and production Save-to-Cookbook remain unimplemented;
normal sidecar UI real-save wiring remains later;
no external source is vendored into this repo.
```

The outbox must summarize:

```text
external workspace branch/commit;
existing core auth findings;
OIDC/provider-neutral implementation status or blocker;
Google descriptor/config behavior;
AuthUser/provider-link mapping behavior;
storage/Drive deferral behavior;
custom image tag/build result;
external focused tests/build results;
sidecar startup verification result if run;
remaining blockers before real Google login;
remaining blockers before sidecar UI real-save wiring;
validation results;
explicit non-goals.
```

## Acceptance criteria

```text
Google-first core OIDC local auth spike is implemented or precisely blocked.
No external source is committed into this sidecar repository.
Core-owned identity/session/provider-token/storage boundary is preserved.
No real Google/Microsoft/OAuth/provider calls are made.
No client secrets, OAuth codes, access tokens, refresh tokens, ID tokens, cookies, sessions, or real user data are created/exported/printed/committed.
Google Drive/storage scopes are not requested and remain deferred.
AuthUser mapping/linking is core-owned or a migration blocker is documented.
Provider-neutral structure can later support Microsoft/OneDrive.
0034C synthetic-auth fixture and Save-to-Cookbook adapter assumptions remain valid.
Custom local image local/vanilla-cookbook-adapter:0034e is built or blocker is documented.
Sidecar docs record external commit/status and next step.
Production auth, production Save-to-Cookbook, sidecar UI real-save wiring, browser automation, direct DB writes, AWS/GitHub Actions/Cloudflare, analytics, ads, payment, QMD, provider routing, and live calls are not implemented.
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
git add docs README.md outbox/0034E-google-first-core-oidc-local-auth-spike-results.md

git commit -m "docs: record google first core oidc auth spike"

git pull --rebase origin main

git push origin main
```
