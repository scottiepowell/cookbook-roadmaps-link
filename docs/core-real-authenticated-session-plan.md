# Core Real Authenticated Session Plan

Status: design/readiness only. No real provider, session, cookie, or OAuth
flow was executed by this task.

Date: 2026-07-26

## Decision

Proceed with option B first: implement a core-owned, loopback-only mock OIDC
session fixture in the separate Vanilla Cookbook workspace. The fixture must
exercise the real Lucia session lifecycle and core-owned Save-to-Cookbook
authorization without contacting Google or any other provider. It must be
disabled by default and unavailable outside an explicitly approved local/test
runtime.

After B passes, create a separate manual local task for option A: a developer-
created Google OAuth app with identity-only scopes and ignored local secrets.
The mock fixture is a session-lifecycle test, not evidence that Google tokens
or claims are valid.

## 0034I outcome

0034I verified the full synthetic local path: mock importer draft, sidecar
dry-run, explicit confirmation, 0034G core persistent route, safe UID,
read-after-write, idempotency status, and disposable cleanup. It did not create
a real session, so the UI could not open the saved recipe in the Vanilla
Cookbook browser. That is the remaining gap this plan addresses.

## Observed core auth/session path

These are observations from the separate workspace at the approved 0034G
commit, branch `openclaw/0034G-core-owned-local-persistent-user-auth-transport`.

| Area | Evidence and confidence |
| --- | --- |
| Lucia ownership | `src/lib/server/lucia.js` creates Lucia with the Prisma adapter and maps `authUser`, `authKey`, and `authSession`. Observed fact. |
| Request locals | `src/hooks.server.js` calls `auth.handleRequest(event)`, validates the request, and assigns `event.locals.session` and `event.locals.user`. Observed fact. |
| Authorization | `src/lib/server/authHelpers.js` exposes `requireAuth(locals)` and rejects missing `locals.user` with 401. Observed fact. |
| Session creation | Login and OAuth callback paths call `auth.createSession({ userId, attributes: {} })` and `locals.auth.setSession(session)`. Observed fact. |
| Session invalidation | `/logout` validates the current session, calls `auth.invalidateSession`, and clears the request session. Observed fact. |
| Cookie handling | Lucia config uses SameSite=Lax, path `/`, and derives `secure` from dev/HTTP origin. The hook removes Secure for local HTTP responses. Observed fact; local HTTP behavior still needs a focused future test. |
| CSRF/origin | Lucia's request helper is the existing boundary; the app also has SameSite/CORS handling. The exact cross-origin test matrix is not present in the inspected auth tests. Gap requiring explicit 0034K tests. |
| OIDC start | `/api/oauth?provider=oidc` performs issuer discovery, creates state and PKCE verifier/challenge, stores handoff values in HttpOnly cookies, and redirects to the configured issuer. Observed fact. |
| OIDC callback | `/api/oauth/callback` requires provider/state/code, reads the state and verifier cookies, validates the callback through `openid-client`, links or provisions the core user, creates a Lucia session, and clears handoff cookies. Observed fact. |
| Provider linking | `AuthAccount` has a unique `(provider_id, provider_user_id)` constraint. The callback links an existing subject, verified-email matches, or provisions a user depending on site settings. Observed fact; concurrent collision/error behavior needs tests. |
| Durable schema | `AuthUser`, `AuthSession`, `AuthKey`, and `AuthAccount` are in `prisma/schema.prisma`; migrations include OAuth support and OIDC auto-provision settings. Observed fact. |
| Redirect URI | Generic OIDC uses `${ORIGIN}/api/oauth/callback`; Google OAuth uses the same callback path. `ORIGIN` is required for auth/CORS configuration. Observed fact. |
| Local config | `.env.template` documents `ORIGIN`, provider IDs/secrets, OIDC issuer/client values, and default `OIDC_SCOPES=openid email profile`. Secrets are expected in ignored local env, not source. Observed fact. |
| Test coverage | The inspected core tests contain adapter and fixture coverage but no approved real-session browser/cookie test that prints no cookie values. Unknown/remaining gap. |

The existing 0034E `oidcIdentityFoundation.js` is provider-neutral profile and
linking logic behind mock gates, but it intentionally does not create Lucia
sessions or set `locals.auth`. Therefore it is not sufficient by itself for
real-session proof.

## Candidate paths

### A. Manual local Google OIDC

This is the eventual provider validation path. A developer creates a local
Google OAuth web client, registers only the loopback callback, stores the
client ID/secret in ignored local configuration, and manually verifies the
core callback, linking, session, logout, and Save-to-Cookbook flow. It proves
Google integration but requires real credentials and a real provider call, so
it is not suitable for normal validation or this task.

### B. Core-local mock OIDC session fixture — recommended first

Add a core-only dev/test route or service that accepts a fixed synthetic OIDC
claim fixture, never a token or user identity supplied by the sidecar, and
then uses the same core mapping, `auth.createSession`, `locals.auth.setSession`,
`locals.user`, and logout/invalidation boundaries as the normal callback.

The fixture should test session creation and validation with an in-memory test
cookie jar only. Assertions may check cookie attributes and authenticated
status, but must never print, persist, export, or commit the cookie value.
It should use a disposable database, synthetic subject/email, and explicit
local gates. It must not claim to validate Google signatures, discovery,
redirect registration, or provider token exchange.

This is the smallest way to close the session gap without Google calls.

### C. Local password or magic-link bootstrap

The core already has username/password login, but adding or choosing another
bootstrap would test Lucia sessions while bypassing the Google provider-link
path that the product architecture selected. It adds an alternate auth
surface, credential handling, and account-policy questions. Keep it as a
fallback only if the core mock cannot exercise the actual provider-link path.

### D. Blocked

The feature is not blocked from planning: the core has a usable Lucia boundary
and a durable account-link model. Real Google login is blocked from execution
until a separate local credential task approves secrets and external calls.

## Next task: 0034K

Implement the core-local mock OIDC session fixture in the external workspace.
The future task should:

1. require a dev/test build, loopback target, explicit mock enablement, and an
   explicit approval flag;
2. reject production, CI, tunnel, AWS, Cloudflare, exposed targets, sidecar
   identity/session/token fields, and real provider configuration;
3. use synthetic claims containing issuer, subject, verified email, and bounded
   display data only;
4. map/link the subject through the existing core AuthAccount/AuthUser
   service, with deterministic replay and verified-email collision behavior;
5. create a real Lucia session inside the core and verify `locals.user` on a
   protected test endpoint or core-owned adapter call;
6. test logout/session invalidation and expired/invalid session behavior;
7. test local HTTP cookie metadata without exposing cookie values;
8. run the existing Save-to-Cookbook adapter with core-derived ownership,
   using a disposable DB and backup/restore; and
9. return only safe status, owner-state, link-state, and opaque recipe UID
   fields.

The task must leave the normal sidecar UI unchanged. After 0034K succeeds,
0034L can be a separately approved manual Google local-credentials task. Only
after that evidence should normal sidecar UI real-save observation be
considered.

## Security and data boundaries

- Vanilla Cookbook core owns `AuthUser`, `AuthSession`, `AuthAccount`, provider
  grants, storage connections, and recipe authorization.
- The sidecar sends reviewed recipe candidates only. It never owns or receives
  `userId`, session cookies, session IDs, provider tokens, OAuth codes, client
  secrets, or storage grants.
- Google sign-in is identity-only: `openid email profile`. Google Drive and
  other storage scopes are a separate future BYOS consent.
- Local credentials, if later approved, belong only in ignored local env/config
  and must be redacted from logs, tests, reports, and outboxes.
- All mock-session tests use disposable local data and in-memory cookie jars;
  no browser automation or credential export is allowed.

## Official references

The core implementation was compared with the official protocol/library
references:

- [Lucia cookies and request validation](https://v2.lucia-auth.com/basics/using-cookies/)
  documents session-cookie validation and built-in origin/CSRF protection.
- [Lucia sessions](https://v2.lucia-auth.com/basics/sessions/) documents
  session creation and cookie-based transport.
- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
  defines the Google identity flow; Drive scopes are separate from the
  identity-only request.
- [Google OpenID Connect reference](https://developers.google.com/identity/openid-connect/reference)
  documents OIDC claims and cautions against using email as the stable
  identifier.
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
  is the protocol reference for issuer, subject, state, nonce, and callback
  validation requirements.

## Explicit non-goals

This task adds no auth code, provider route, OAuth client, secret, token,
cookie, session, database migration, sidecar identity flow, Google call,
storage scope, production authentication, production Save-to-Cookbook,
deployment change, browser automation, direct DB write, or external source.
