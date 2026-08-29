# 0034M Manual Local Google OIDC Login Verification Results

## Outcome

Manual local Google OIDC login succeeded. The external core used ignored local
configuration, the approved 0034L image, exactly `openid email profile`, and the
loopback callback. The core callback returned and accepted a real core-owned
authenticated session.

## Safe evidence

- The approved setup shape is core-local and loopback-only, using the core
  callback and exactly `openid email profile`.
- 0034L already added Google issuer, loopback, development, storage-scope, and
  state/PKCE/nonce guards in the core workspace.
- Google issuer, callback, state, PKCE, nonce, and identity-only scope checks
  completed through the hardened core path.
- The callback returned, the core accepted the Lucia session, and an
  authenticated settings page proved the core `locals.user` authorization
  boundary succeeded.
- The core created or linked its own AuthUser/AuthAccount. Provider-link replay
  was not exercised in this run.
- Logout/invalidation was not exercised in this run; 0034K remains the evidence
  for replay and invalidation behavior.
- No secret, OAuth code, token, cookie, session value, profile data, screenshot,
  trace, or browser artifact was recorded or committed.

The next product verification is authenticated Save-to-Cookbook UI observation
as a separate task. Public Google authentication, Drive/BYOS consent, and
production Save-to-Cookbook remain separate approvals.

## Validation and non-goals

Required static/repository and Compose validation follows after the documentation
update. No live OpenAI, Microsoft, storage, or unrelated provider call was made.

Explicit non-goals: production authentication, production Save-to-Cookbook,
Drive/BYOS consent, sidecar identity/session ownership, browser automation,
credential/token/cookie export, direct sidecar DB writes, deployment, and saved
recipe browser observation.
