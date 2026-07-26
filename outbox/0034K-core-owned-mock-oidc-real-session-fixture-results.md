# 0034K Core-Owned Mock OIDC Real-Session Fixture Results

## Result

Implemented the core-owned, local/dev-only mock OIDC real-session fixture in
the separate Vanilla Cookbook workspace.

- branch: `openclaw/0034K-core-owned-mock-oidc-real-session-fixture`;
- external commit: `d7ef5e7`;
- fixture shape: service plus focused Vitest harness, with no public route;
- source remains outside the sidecar repository.

## Evidence

The fixture uses synthetic claims and the core-owned identity store, then
exercises actual Lucia session creation, in-memory cookie setting, a second
request's session validation, `locals.user`/`requireAuth`, Save-to-Cookbook
ownership, logout, and session invalidation. Provider-subject replay is safe;
verified-email collision returns review status. Sidecar-supplied identity,
cookie, session, token, OAuth, provider-grant, and storage-grant fields are
rejected.

The envelope exposes only safe status/link/ownership/save/logout fields and an
opaque UID from the injected test commit service. Cookie values, sessions,
tokens, rows, paths, secrets, prompts, and provider output are not returned or
printed. Google Drive/storage scopes and external discovery/token/userinfo
calls are not used.

## Gates and runtime

The fixture requires explicit mock-session enablement, explicit approval,
synthetic-auth mode, `local/vanilla-cookbook-adapter:0034k`, and an HTTP
loopback target. It refuses production, CI, AWS, Cloudflare, tunnel, real
provider credentials, and storage scopes.

The custom local image `local/vanilla-cookbook-adapter:0034k` built
successfully and was not pushed. The sidecar local start/stop scripts launched
and removed only the local `cookbook-local` app container. Port 3000 opened,
but the short readiness probe did not observe an HTTP page before shutdown;
this is recorded as a runtime timing limitation, not claimed as HTTP-ready
evidence.

## Tests and limitations

Passed in the external workspace:

```text
corepack pnpm exec vitest run src/tests/mockOidcSessionFixture.test.js src/tests/oidcIdentityFoundation.test.js src/tests/localAuthFixture.test.js
16 passed
corepack pnpm exec prisma generate
corepack pnpm run generate-sw
corepack pnpm exec vite build
passed
```

The full external Vitest suite was attempted. It retains unrelated baseline
failures: five AI unit tests require an OpenAI key, five conversion tests need
seeded ingredient data, and one parser test depends on a live page response.
No live OpenAI, Google, Microsoft, OAuth, storage, or browser session call was
made.

The fixture uses an isolated in-memory Lucia adapter and cookie jar for normal
tests, so it proves the core session lifecycle without mutating a local DB or
creating committed runtime artifacts. A separate disposable-runtime run is
still required before claiming browser-observable saved recipes.

## Next step and non-goals

Next recommended task: 0034L, manual local Google OIDC with ignored developer
credentials and identity-only scopes. It must remain a separate approval gate.

No Google login, production authentication, production Save-to-Cookbook, sidecar
UI real-save wiring, direct DB write, migration, public route, browser
automation, provider call, cookie/token/session export, storage grant, or
external source vendoring was added.
