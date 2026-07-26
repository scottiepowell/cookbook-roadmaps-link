# Core-Owned Mock OIDC Real-Session Fixture

Status: complete in the separate core workspace; local/dev-only and disabled by
default. Production authentication, Google login, and production
Save-to-Cookbook remain unimplemented.

## Result

0034K added a core-owned service/test fixture at
`src/lib/server/mockOidcSessionFixture.js` in the external Vanilla Cookbook
workspace. It does not add a public route. The fixture accepts only synthetic
OIDC-shaped claims, links the provider subject through an injected core-owned
identity store, creates a real Lucia session, validates a new request through
the core session cookie boundary, calls the Save-to-Cookbook service with the
authenticated core user, and invalidates the session.

External workspace evidence:

- branch: `openclaw/0034K-core-owned-mock-oidc-real-session-fixture`;
- commit: `d7ef5e7` (`feat: add mock oidc real session fixture`);
- local image: `local/vanilla-cookbook-adapter:0034k` built successfully;
- source remains outside this repository and no source was vendored here.

## Gates and data boundaries

The fixture fails closed unless development/test mode, explicit mock-session
enablement and approval, synthetic-auth mode, the approved `0034k` image marker,
and an HTTP loopback Cookbook target are present. It rejects CI, tunnels,
AWS, Cloudflare, real provider credentials, and storage scopes.

Claims are limited to a synthetic issuer, subject, email, verification flag,
and bounded display fields. Sidecar identity, cookie, session, token, OAuth,
provider-grant, and storage-grant assertions are rejected. The fixture never
calls an external provider and never returns or prints the cookie value.

## Session and ownership evidence

The focused test creates a Lucia instance with an in-memory adapter and a
non-exported cookie jar. It proves core creates the synthetic `AuthUser` and
provider link, creates and validates a real Lucia session, exposes
`locals.user`, accepts `requireAuth`, passes the core-derived user to the
Save-to-Cookbook service, safely replays account linking, and invalidates the
session on logout.

This is session-lifecycle evidence, not Google claim-signature, discovery,
redirect-registration, token-exchange, or real-provider evidence. The normal
sidecar UI remains unchanged and does not receive a session or cookie.

## Validation and local image

External focused validation passed:

```text
corepack pnpm exec vitest run src/tests/mockOidcSessionFixture.test.js src/tests/oidcIdentityFoundation.test.js src/tests/localAuthFixture.test.js
16 tests passed
corepack pnpm exec prisma generate
corepack pnpm run generate-sw
corepack pnpm exec vite build
build passed
```

The full external Vitest run was attempted but is not a clean baseline in this
checkout: five existing AI unit tests require an OpenAI key, five ingredient
conversion tests require seeded data, and one parser fixture depends on a live
page response. No provider call was enabled or made for 0034K.

The sidecar started and stopped the custom image with the local scripts. The
container reached the localhost port, but the readiness check's HTTP page
probe was still pending during its short check window. Repeat the check after
startup if an HTTP-ready runtime is needed.

## Next steps and non-goals

The next task is 0034L: a separately approved manual local Google OIDC task
using ignored developer credentials, identity-only scopes (`openid email
profile`), a loopback callback, redacted logs, and no repository credential
material. Only after that should a later task consider real authenticated UI
observation.

Google Drive/storage consent remains a separate future BYOS task. No production
auth, production Save-to-Cookbook, sidecar identity ownership, direct sidecar
DB writes, browser automation, migration, public route, provider call, token,
cookie export, or deployment change was added.

Official references: [Lucia cookies](https://v2.lucia-auth.com/basics/using-cookies/),
[Lucia sessions](https://v2.lucia-auth.com/basics/sessions/), and
[OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html).
