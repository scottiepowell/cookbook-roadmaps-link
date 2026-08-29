# 0034M Manual Local Google OIDC Login Verification

Status: precisely blocked pending core-local configuration and an available
local custom-image runtime. No Google login was attempted.

## Verification scope

The intended verification is a manual, loopback-only login against the external
Vanilla Cookbook core. It must use an ignored local configuration and exactly
these identity scopes:

```text
openid email profile
```

The only permitted redirect shape is a local callback such as
`http://127.0.0.1:3000/api/oauth/callback`, matching the core route reviewed in
0034L. Google Drive, storage, Gmail, calendar, broad API, and offline-storage
scopes are forbidden. This task does not observe or save a recipe.

## 2026-08-29 availability result

Configuration was checked only for safe presence and shape; no values were
read or recorded. The external core workspace has neither `.env` nor
`.env.local`. An ignored sidecar `.env` exists, but it is not core-local, and
its safe shape does not use the required `http://127.0.0.1:3000` origin. It
therefore cannot be used for the approved core-owned loopback verification.

The required `local/vanilla-cookbook-adapter:0034l` runtime also could not be
started because the local Docker engine is unavailable. No request was sent to
Google, and no browser, cookie, OAuth code, token, profile, database, upload,
or session artifact was created.

This is a real blocker. The core needs its own ignored configuration with the
approved loopback shape, and Docker Desktop must be running before the manual
flow can begin. Do not weaken the 0034L guard or substitute a mock result;
0034K already covers the mock/session lifecycle.

## Safe operator procedure for a future approved run

1. Create a Google OAuth web client outside this repository, limited to the
   loopback callback used by the external core.
2. Put the private values only in the external workspace’s ignored local
   configuration. The safe shape is:

   ```text
   ORIGIN=http://127.0.0.1:3000
   OIDC_ISSUER_URL=https://accounts.google.com
   OIDC_SCOPES=openid email profile
   OIDC_CLIENT_ID=<private local value>
   OIDC_CLIENT_SECRET=<private local value>
   ```

   Never print, commit, paste, or report the values.
3. Start only the approved local custom core image and manually open its OIDC
   start path. The core must enforce issuer, audience, state, nonce, PKCE,
   callback, and loopback checks.
4. Record only booleans or opaque safe statuses: callback returned, session was
   accepted by core, `locals.user`/`requireAuth` succeeded, account linking was
   idempotent, and logout invalidated the session if exercised.
5. Remove the ignored credentials and stop the local runtime. Do not export or
   inspect cookie/session values. Do not wire Save-to-Cookbook browser
   observation in this verification.

## Ownership and next step

Vanilla Cookbook core owns AuthUser, AuthAccount, sessions, provider links, and
recipe authorization. The sidecar receives none of the identity, cookie, session,
OAuth, token, or storage-grant values. Google Drive/BYOS remains a separate later
consent flow. Production authentication and production Save-to-Cookbook remain
unimplemented.

0034M remains blocked until the manual local login is completed under the stated
guards. After safe authenticated-state evidence exists, a separate task may
verify authenticated Save-to-Cookbook browser/UI observation. No such observation
is claimed here.

Official references: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect),
[Google OAuth scopes](https://developers.google.com/identity/protocols/oauth2/scopes),
[OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html), and
[Lucia sessions](https://v2.lucia-auth.com/basics/sessions/).

Explicit non-goals: production auth, provider calls during normal validation,
Drive/storage consent, token or cookie handling by the sidecar, browser
automation, saved-recipe UI observation, direct database writes, deployment, and
credential management in this repository.
