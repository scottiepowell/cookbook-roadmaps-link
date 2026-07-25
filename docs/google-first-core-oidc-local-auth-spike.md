# 0034E Google-First Core OIDC Local Auth Spike

Status: complete as an offline/local foundation in the separate core
workspace. No real provider flow or production authentication is enabled.

Date: 2026-07-25

## External workspace and implementation

The source-owned Vanilla Cookbook workspace remains outside this repository:

- Branch: `openclaw/0034E-google-first-core-oidc-local-auth-spike`
- Commit: `f5b37e1` (`feat: add local oidc identity foundation`)
- Image: `local/vanilla-cookbook-adapter:0034e`
- Module: `src/lib/server/oidcIdentityFoundation.js`
- Tests: `src/tests/oidcIdentityFoundation.test.js`

No external source was copied or vendored into this sidecar repository.

## Existing core auth findings

The core already owns Lucia `AuthUser`/session handling through
`locals.user`, `requireAuth`, and Lucia request middleware. Its Prisma schema
already contains `AuthUser`, `AuthSession`, and `AuthAccount`; the existing
`AuthAccount` migration provides a unique provider/subject link.

The new foundation remains below the network/session boundary. It does not
create a Lucia session, set a cookie, exchange a code, call a provider, or
persist an account link. Persistence is represented by an injected core store
in unit tests, so any future durable linking remains a core-owned schema and
security review decision.

## Google-first identity contract

The provider-neutral descriptor is identity-only:

```text
provider: google
issuer: https://accounts.google.com
identity scopes: openid, email, profile
storage scopes: none
```

The normalizer accepts only a bounded identity claim set, validates the Google
issuer and stable subject, normalizes a verified email, and returns safe
profile metadata. Missing/invalid issuer or subject is rejected. An
unverified email returns `review_required`; it is not silently linked.
Unknown claims are rejected rather than echoed.

The linker receives a normalized profile and an injected core-owned store. It
replays an existing provider/subject link safely, requires review for a
verified-email collision, and otherwise asks the core store to create an
`AuthUser` and `AuthAccount` link. It never accepts a sidecar `userId`, session,
cookie, token, or storage-grant assertion.

## Local mock gates

The foundation is disabled unless all non-secret local conditions are present:

```text
NODE_ENV=development
LOCAL_OIDC_MOCK_ENABLED=1
LOCAL_OIDC_MOCK_APPROVED=1
OIDC_PROVIDER=google
COOKBOOK_TARGET_URL=http://127.0.0.1:3000/
```

Production, CI, AWS/Cloudflare indicators, exposed targets, client secrets,
and any storage-scope setting are rejected. These are unit-test configuration
guards only; no route reads them and no real credentials are needed.

## Validation evidence

External focused tests passed:

```text
corepack pnpm exec vitest run src/tests/oidcIdentityFoundation.test.js src/tests/localAuthFixture.test.js src/tests/importAdapter.test.js src/tests/importAdapter.route.test.js src/tests/importCommit.test.js src/tests/importCommit.route.test.js
6 test files, 32 tests passed
```

The normal package build wrapper failed in this Windows shell because its
nested script invokes a `pnpm` executable that is not on PATH. Equivalent
Corepack-resolved steps passed:

```text
corepack pnpm exec prisma generate
corepack pnpm run generate-sw
corepack pnpm exec vite build
```

The local image was built without push or deployment. The sidecar local script
started only the `cookbook-local` app with that opt-in image; after readiness,
`http://127.0.0.1:3000/` returned HTTP 200. The container was stopped after
verification.

## Boundaries and next steps

Google Drive/BYOS storage scopes remain deferred and are not requested. The
0034C synthetic-auth fixture remains valid and independent of real SSO. The
Save-to-Cookbook adapter continues to derive ownership from core `AuthUser`;
the sidecar owns none of the identity/session/token/storage values.

Before real Google login, a separate security task must review provider
registration, discovery/signature/audience validation, PKCE/state/nonce,
redirect allowlists, account linking and recovery, session cookies, secret
custody, revocation, and any persistent-link migration. Before sidecar UI
real-save wiring, a separate transport gate must define a core-owned session
boundary without exporting credentials.

## Explicit non-goals

No Google/Microsoft/provider call, OAuth route or callback, code exchange,
token/session/cookie handling, client secret, storage scope, Drive integration,
provider migration, login UI, production authentication, production
Save-to-Cookbook, sidecar real-save wiring, browser automation, direct DB write,
AWS, GitHub Actions, Cloudflare, analytics, ads, payment, QMD, or live call was
added.
