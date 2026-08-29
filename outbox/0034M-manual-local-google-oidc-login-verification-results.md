# 0034M Manual Local Google OIDC Login Verification Results

## Outcome

Manual local Google OIDC login is precisely blocked. The external core workspace
is clean on the approved 0034L branch but has no `.env` or `.env.local` file.
An ignored sidecar `.env` was found, but safe shape checks show it is not suitable
as the core-local loopback configuration. The required local Docker engine is
also unavailable, so `local/vanilla-cookbook-adapter:0034l` cannot be started.
No Google request or manual login was attempted.

## Safe evidence

- The approved setup shape is core-local and loopback-only, using the core
  callback and exactly `openid email profile`.
- 0034L already added Google issuer, loopback, development, storage-scope, and
  state/PKCE/nonce guards in the core workspace.
- Core-owned AuthUser/AuthAccount/session and `locals.user`/`requireAuth`
  behavior remains covered by prior offline/mock evidence.
- No real callback, Lucia session from Google, provider-account link, logout, or
  invalidation result can honestly be reported for 0034M.
- No secret, OAuth code, token, cookie, session value, profile data, browser
  state, DB, upload, screenshot, trace, or log artifact was created or committed.

The exact blockers are missing ignored local Google OAuth configuration in the
external core workspace, a non-loopback-safe sidecar configuration location, and
an unavailable local Docker engine. After the core-local loopback configuration
and Docker runtime are available, the approved manual login can record only safe
boolean/opaque status evidence. The next product verification remains
authenticated Save-to-Cookbook UI observation, but it must wait for that
evidence.

## Validation and non-goals

This task is docs-only in the sidecar. Required static/repository and Compose
validation follows after the documentation update. No live OpenAI, Google,
Microsoft, OAuth, storage, or unrelated provider call was made.

Explicit non-goals: production authentication, production Save-to-Cookbook,
Drive/BYOS consent, sidecar identity/session ownership, browser automation,
credential/token/cookie export, direct sidecar DB writes, deployment, and saved
recipe browser observation.
