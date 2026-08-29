# 0034M Manual Local Google OIDC Login Verification

Status: complete. Manual loopback Google login succeeded on 2026-08-29.

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

## 2026-08-29 verification result

The external core workspace had an ignored local configuration with the
required client fields and exactly `openid email profile`. A temporary runtime
override set the approved `http://127.0.0.1:3000` origin without changing or
reporting private values. Docker Desktop and
`local/vanilla-cookbook-adapter:0034l` were available.

The core OIDC start route reached Google, the callback returned to loopback, and
the core accepted the authenticated session. The user reached an authenticated
core settings page, proving the Lucia session populated `locals.user` through
the core authorization boundary. The core created or linked its own account;
the sidecar received no identity or session data. Replay and logout/invalidation
were not exercised in this run and remain covered only by the 0034K fixture.

Only safe boolean/opaque outcomes were observed. No client secret, OAuth code,
token, cookie, session value, browser state, or profile data was recorded or
committed.

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

0034M is complete for manual loopback identity verification. A separate task may
now verify authenticated Save-to-Cookbook browser/UI observation. No such
observation is claimed here.

Official references: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect),
[Google OAuth scopes](https://developers.google.com/identity/protocols/oauth2/scopes),
[OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html), and
[Lucia sessions](https://v2.lucia-auth.com/basics/sessions/).

Explicit non-goals: production auth, provider calls during normal validation,
Drive/storage consent, token or cookie handling by the sidecar, browser
automation, saved-recipe UI observation, direct database writes, deployment, and
credential management in this repository.
