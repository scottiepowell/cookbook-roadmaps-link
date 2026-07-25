# 0034E Google-First Core OIDC Local Auth Spike Results

## External workspace

- Branch: `openclaw/0034E-google-first-core-oidc-local-auth-spike`
- Commit: `f5b37e1`
- Source remains outside this sidecar repository.

## Findings and implementation

The core already owns Lucia `AuthUser` and sessions through `locals.user` and
has an existing Prisma `AuthAccount` provider-link model/migration. Existing
real OAuth/OIDC routes were inspected but not called or modified.

Added a pure, offline-safe Google-first identity foundation in the external
core workspace. It provides an identity-only Google descriptor, local mock
configuration guard, bounded issuer/subject/profile normalization, core-store
provider-link mapping, replay handling, verified-email collision review, and
sidecar identity-claim rejection. No route, migration, provider client, token,
cookie, session, or durable link was added.

Google uses only `openid`, `email`, and `profile` in the descriptor. Storage
scopes are an empty set and Google Drive/BYOS remains a later separate task.
Microsoft/OneDrive can use the same provider-neutral shape later.

## Verification

- Focused external suite: 6 files, 32 tests passed.
- Equivalent build steps passed: Prisma generate, service-worker generation,
  and Vite build. The package `build` wrapper itself is blocked by its nested
  direct `pnpm` invocation not being on this Windows PATH.
- Built local image: `local/vanilla-cookbook-adapter:0034e`; not pushed or
  deployed.
- Sidecar startup with the opt-in image ran only `cookbook-local`; after the
  initial readiness delay, localhost returned HTTP 200. The container was
  stopped afterward.
- No Google, Microsoft, OpenAI, OAuth, storage, or production call occurred.

## Remaining blockers

Real Google login still requires a separate core security implementation and
configuration review for discovery, PKCE/state/nonce, callback validation,
redirects, account-link collision/recovery, session cookies, secret custody,
revocation, and any durable link migration. Sidecar UI real-save wiring still
requires a reviewed core-owned transport and must not export identity or
session credentials. Production auth and production Save-to-Cookbook remain
unimplemented.

## Explicit non-goals

No production auth, OAuth callback, provider client, token/cookie/session,
Google credentials, Drive/storage scope, real account, migration, route,
login UI, sidecar real-save wiring, direct sidecar DB write, browser
automation, deployment work, or live provider call was added.
