# 0034N — Public Homepage Login And Google OIDC Callback

## Goal

Align the public homepage/login work with the mailbox workflow, preserve the
administrator/user separation decision, and correct the first public Google
OIDC defect: a login started at `cookbook.roadmaps.link` must not send the
browser to a loopback callback.

## Context

0034M proved the hardened Google OIDC path manually on loopback with exactly
`openid email profile`. The public homepage was subsequently implemented and
deployed with returning-user login as its primary action and first-administrator
setup behind an explicit link.

The first public-login observation reached `127.0.0.1:3000` after Google. Treat
that observation as evidence of an origin/callback configuration defect, not as
permission to record browser state, credentials, identity data, or OAuth
artifacts.

## Required work

In the external Vanilla Cookbook core workspace:

- retain the public anonymous homepage and existing-user login action;
- retain `/setup` as an explicit first-administrator link rather than the
  default anonymous destination;
- keep administrator and ordinary-user authorization core-owned and enforced
  server-side;
- ensure ignored local environment files cannot be copied into Docker images;
- run the public container with the effective origin
  `https://cookbook.roadmaps.link`;
- generate the public callback
  `https://cookbook.roadmaps.link/api/oauth/callback`;
- request exactly `openid email profile` with state, PKCE, and nonce;
- authorize that exact HTTPS callback on the existing Google Web application
  OAuth client;
- retain Docker-managed database and upload volumes during replacement.

In this sidecar repository:

- keep the homepage goal and administrator/user ADR as the durable design
  records;
- add a safe 0034N outbox result;
- update feature, backlog, tunnel, deployment, and README status;
- run repository, Compose, link, whitespace, and secret validation.

## Safety boundaries

Do not print, commit, export, or record any client identifier, client secret,
OAuth code, access token, refresh token, ID token, state value, PKCE value,
nonce value, cookie, session value, real profile data, browser state, local
environment value, database file, or upload.

Do not request Google Drive, storage, Gmail, Calendar, or offline-access scopes.
Do not give the sidecar, Cloudflare connector, or AI API ownership of users,
roles, provider links, sessions, or cookies. Do not change AWS, GitHub Actions,
EC2, production Save-to-Cookbook, or storage-provider behavior.

## Acceptance criteria

- A matching `inbox/0034N...` and `outbox/0034N...results.md` pair exists.
- Anonymous `/` returns the public homepage with login and conditional setup or
  registration actions.
- The public OIDC start redirects to Google with the exact HTTPS callback,
  identity-only scopes, state, PKCE, and nonce.
- Google accepts the registered callback without `redirect_uri_mismatch`.
- No ignored `.env` file is present in the built image.
- The public container and Cloudflare connector remain healthy.
- Manual account selection and authenticated callback/session observation are
  recorded only if the operator performs them; they are never automated by
  exporting or inspecting private browser/authentication state.
- Safe validation results and any remaining manual verification are explicit.

## Validation

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
docker compose config --quiet
docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

Validate the external core production image, verify that ignored environment
files are absent from it, and inspect only safe callback/scope/gate booleans.

