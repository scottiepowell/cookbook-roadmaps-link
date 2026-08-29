# 0034L Manual Local Google OIDC Real Session

Status: prepared and offline-validated; manual provider verification was not run.

0034L hardens the existing core-owned generic OIDC path for a separately approved
local Google sign-in. The Vanilla Cookbook source remains outside this repository
on branch `openclaw/0034L-manual-local-google-oidc-real-session`, at external
commit `cfc25e9`. The local image was built as
`local/vanilla-cookbook-adapter:0034l` and was not pushed or deployed.

## What was verified without a provider call

The external core already has the generic OIDC start and callback path:

- `/api/oauth?provider=oidc` performs issuer discovery, creates state and PKCE,
  and stores short-lived HttpOnly handoff cookies.
- `/api/oauth/callback` validates the callback, links or provisions the core
  account, creates the Lucia session, and clears the handoff cookies.
- `locals.user`, `requireAuth`, and Save-to-Cookbook ownership remain core-owned.

0034L adds a local configuration guard for the manual Google path. It requires
development mode, a loopback HTTP origin, the Google issuer, local client values,
and exactly `openid email profile`. It rejects production, CI, deployment/tunnel
indicators, exposed origins, storage scopes, and missing configuration. The OIDC
authorization request now includes a nonce; the nonce is held in the existing
short-lived HttpOnly handoff boundary and is required during callback validation.
Only safe reason codes are returned by the guard.

Focused external tests passed: 19 tests across the OIDC foundation, mock session,
local auth fixture, and manual configuration guard. Prisma generation, service
worker generation, and the Vite production build passed. No Google request,
OAuth exchange, browser login, credential read, or session/cookie export occurred.

## Manual operator gate

This section is instructions for a future operator who explicitly approves a
local Google test. It is not a request to run one during normal validation.

1. Create a Google OAuth web client manually, using only the loopback callback
   `http://127.0.0.1:3000/api/oauth/callback`. Do not add Drive or other storage
   scopes.
2. In the external core workspace only, create an ignored local `.env` with
   private values equivalent to:

   ```text
   ORIGIN=http://127.0.0.1:3000
   OIDC_ISSUER_URL=https://accounts.google.com
   OIDC_CLIENT_ID=<private local value>
   OIDC_CLIENT_SECRET=<private local value>
   OIDC_SCOPES=openid email profile
   ```

   Never print, commit, paste into sidecar requests, or record these values.
3. Start only the app using `local/vanilla-cookbook-adapter:0034l`, verify the
   loopback health check, and navigate manually to the existing OIDC start path.
   A normal local browser may hold its own session, but no browser automation,
   cookie export, screenshots, or traces are part of this task.
4. Verify only that the core returns to the local callback and authenticated
   application state. Use logout, remove the ignored local credentials, and
   stop the local runtime when finished.

The current run could not perform these steps because no external-workspace
`.env` or local Google credentials were present. This is an intentional blocker,
not a reason to weaken the gates.

## Boundaries and next step

Google sign-in is identity-only. Google Drive/BYOS authorization is a separate
future consent step and is not requested here. The sidecar owns no `userId`,
session, cookie, provider token, OAuth code, or storage grant. Production auth,
production Save-to-Cookbook, and normal sidecar UI real-save wiring remain
unimplemented. The 0034K synthetic real-session fixture remains valid and does
not depend on Google.

0034M completed the approved manual loopback login. Google returned through the
hardened callback, the core accepted its Lucia session, and an authenticated
settings page proved the core-owned user/authorization boundary. Replay and
logout were not exercised in this run. See [0034M Manual Local Google OIDC Login
Verification](manual-local-google-oidc-login-verification.md).

Authenticated Save-to-Cookbook browser/UI observation is now the next separate
task. Public Google authentication and Drive/storage consent remain separate.

Official references: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect),
[Google OAuth scopes](https://developers.google.com/identity/protocols/oauth2/scopes),
[OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html), and
[Lucia cookies and sessions](https://v2.lucia-auth.com/basics/using-cookies/).

Explicit non-goals: production OAuth, Google API calls, Drive/storage consent,
provider token persistence, sidecar auth, browser automation, migrations,
production deployment, and Save-to-Cookbook UI changes.
