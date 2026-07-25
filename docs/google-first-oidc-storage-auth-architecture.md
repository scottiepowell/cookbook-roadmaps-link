# ADR: Google-First OIDC and Future Storage Authorization

Status: proposed, documentation/research only
Date: 2026-07-25

## Decision

Use Google as the first production external identity-provider candidate, with
OIDC sign-in owned by the Vanilla Cookbook core. Treat cloud-storage access as
a separate, later user-consented capability. Define provider-neutral identity
and storage adapter contracts early enough that Microsoft/OneDrive can be
added without making the AI sidecar an identity or storage owner.

The boundary is:

```text
External OIDC provider
        |
Vanilla Cookbook core identity adapter
        |
Core AuthUser, provider link, and session
        |
Core-owned Save-to-Cookbook adapter
        |
Canonical Cookbook recipe storage
```

The AI sidecar remains a reviewed recipe-candidate generator and client of a
reviewed core adapter. It never owns `userId`, sessions, cookies, provider
tokens, storage grants, or canonical recipe persistence.

This ADR adds no authentication, OAuth/OIDC, storage client, provider SDK,
route, migration, login control, token handling, or live provider call.

## Current repository facts

Observed in this repository:

- 0033S provides a local sidecar review/in-memory Save-to-Cookbook prototype.
- 0033Q provides disposable local database/write-readiness evidence.
- 0033Y/0033Z provide core-owned dry-run and commit boundaries in the separate
  source-owned Vanilla Cookbook workspace.
- 0034A verifies the core service with a synthetic `AuthUser` and temporary
  SQLite data.
- 0034C verifies a fail-closed, core-process synthetic-auth fixture with
  dry-run-before-commit, rollback, duplicate handling, and restore. It does not
  require or represent real Google/Microsoft SSO.
- The sidecar has no approved production identity, storage, provider-token, or
  session boundary. Production Save-to-Cookbook remains unimplemented.

These are repository facts, not evidence that an external provider has been
configured or that a real account has been used.

## Current official provider facts

The following public primary documentation was reviewed on 2026-07-25. These
facts can change and must be rechecked before implementation:

- Google describes its OAuth implementation as OpenID Certified, publishes an
  OIDC discovery document, and directs web sign-in implementations to Google
  Identity Services: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
  and [Google OIDC API reference](https://developers.google.com/identity/openid-connect/reference).
- Google identifies `openid`, `email`, and `profile` as the sign-in identity
  scopes used for basic identity/profile claims in its OIDC guidance. The
  implementation must still validate the actual returned claims and issuer,
  audience, nonce, and signature according to a reviewed core security design.
- Google recommends the narrowest Drive scope. `drive.file` is described as
  access to files created/opened by the app or explicitly shared through a
  picker, while broad `drive` and `drive.readonly` scopes are restricted:
  [Choose Google Drive API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth).
- Google states that sensitive/restricted scopes can require OAuth app
  verification, and restricted-scope server storage can require a security
  assessment. Scope justification must match shipped functionality:
  [OAuth App Verification](https://support.google.com/cloud/answer/13463073?hl=en),
  [verification requirements](https://support.google.com/cloud/answer/13464321),
  and [requesting minimum scopes](https://support.google.com/cloud/answer/13807380).
- Microsoft documents OIDC discovery, authorization, token, UserInfo, JWKS,
  logout, nonce, and ID-token validation requirements:
  [Microsoft OIDC](https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc).
  Microsoft identity OIDC scopes include `openid`, `email`, `profile`, and
  `offline_access`: [Microsoft scopes and permissions](https://learn.microsoft.com/en-us/entra/identity-platform/scopes-oidc).
- Microsoft Graph offers OneDrive-oriented permissions such as
  `Files.ReadWrite.AppFolder`, `Files.ReadWrite`, and selected-file options,
  with materially different breadth and consent implications:
  [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference).

The provider documents establish design constraints, not permission to create
an app, request scopes, store grants, or run a provider flow in this task.

## Options evaluated

### A. Google-first OIDC in core; Drive later as separate consent — selected

Google sign-in creates or links a core account. A later, explicit “connect
storage” action requests only the reviewed Drive permission needed for a
specific BYOS feature. This keeps local/core storage available, avoids asking
for unrelated storage permission during login, and permits scope review before
any file access. It preserves core ownership and supports a later real
Save-to-Cookbook flow.

### B. Bundle Google sign-in and Drive consent at first login — rejected

This makes a recipe-login action look like a request for broad file access,
creates unnecessary consent friction, and couples identity recovery to storage
availability. It also increases verification and data-minimization scope before
the storage feature exists.

### C. Sidecar-owned auth and storage tokens — rejected

The sidecar would become a second identity authority, would need to handle
sessions and high-value grants, and could confuse ownership between candidate
generation and canonical Cookbook persistence. It violates the established
core-owned boundary.

### D. Reverse-proxy/BFF auth with core session projection — deferred

A platform-level BFF may eventually be useful, but it adds cookie/session
projection and deployment complexity. It is not necessary to prove the
core-owned local fixture or to choose Google first. Reconsider only through a
separate platform/security ADR.

### E. Provider-neutral abstraction first, Google first adapter — selected as a
design constraint

Do not build every provider up front. Define narrow provider-neutral contracts,
then implement Google first after a separate security task. This avoids a
Google-only data model while keeping the initial implementation small.

### F. Email/password or local-only auth first — fallback only

Existing local/dev behavior may remain available for offline fixtures, but it
does not resolve the selected external-identity direction. It is not a reason
to move identity into the sidecar or to delay the core ownership model.

## Consent model

Use two conceptual consent steps:

1. **Sign in with Google:** identity-only OIDC scopes: `openid`, `email`, and
   `profile` as appropriate. No Drive permission is requested.
2. **Connect Google Drive:** only when the user enables a defined BYOS feature;
   request the narrowest reviewed scope, initially considering `drive.file` or
   an app-specific/user-selected equivalent.

Login must work without cloud storage. A user may keep recipes in the core,
use local/offline export, or connect a different storage provider later.
Storage consent must explain what is accessed, why, where files live, what is
retained, how disconnect works, and whether import/export/sync is one-way or
bidirectional. A Drive scope review and any required verification/security
assessment precede public use.

## Provider-neutral contracts (future design only)

### `IdentityProviderAdapter`

Conceptual responsibilities:

- provider identifier and issuer/discovery metadata;
- authorization-code/OIDC exchange strategy owned by the core;
- normalized stable subject, verified-email handling, display metadata;
- account-linking and collision rules;
- logout, revocation, failure, and disconnect capabilities.

The stable provider subject, not an email address alone, should anchor an
external account link. The core creates the application session after the
claims are validated. No sidecar field may assert the owner.

### `StorageProviderAdapter`

Conceptual responsibilities:

- explicit connect authorization and granted-scope record;
- app-folder/root or user-selected-file strategy;
- import/export/sync operations with ownership and conflict checks;
- refresh/revocation/disconnect behavior;
- user-visible deletion/export semantics.

Storage adapters are optional services around core-owned recipes. BYOS does
not replace the Cookbook as canonical owner and does not allow a storage grant
to bypass core Save-to-Cookbook validation.

## Planned core-owned data model

No migration is added here. Future schema review should define the minimum
fields, encryption, retention, and deletion behavior for:

| Object | Purpose and minimum data | Sensitive data and owner |
|---|---|---|
| `CoreUser/AuthUser` | Core user ID, lifecycle/status, timestamps | Account identity; Vanilla Cookbook core |
| `ProviderAccountLink` | Core user ID, provider ID, stable subject, verified-at/status, link timestamps | Subject/email claims; core auth boundary, never sidecar |
| `ProviderTokenGrant` / `StorageConnection` | Core user ID, provider, granted scopes, encrypted refresh/access-grant reference, status and last-use metadata | Tokens/grants; encrypted core/platform secret store, never sidecar |
| `StorageProviderFileReference` | Core user ID, provider, opaque file ID, selected/root role, schema/version, sync status | Provider file metadata; core storage adapter, minimized and deletable |
| `Audit/SecurityEvent` | Connect, disconnect, revoke, link, conflict, deletion outcome | No token/body/content; core security/audit boundary |
| Import/export idempotency linkage | Operation key, core user scope, candidate/file fingerprint, outcome, timestamps | No prompt/provider body/secret/raw file; core operation boundary |

Refresh tokens, provider access tokens, cookies, and session identifiers must
not be mirrored into the AI sidecar. Encryption, rotation, revocation, backup,
retention, and deletion require a separate security implementation task.

## Security and privacy gates

Future implementation must include, at minimum:

- authorization-code flow with PKCE where applicable, state and nonce
  validation, exact redirect URI allowlists, issuer/audience/signature/expiry
  validation, and `email_verified` handling;
- collision-resistant account linking that never silently joins accounts by
  email; explicit confirmation/recovery for an existing core account;
- CSRF protection and secure, same-site, core-managed session cookies;
- no provider tokens or raw identity assertions in sidecar requests, browser
  storage, logs, prompts, traces, support views, or recipe content;
- encrypted refresh-grant storage, rotation/revocation, disconnect, deletion,
  and reconnect behavior;
- least-privilege Google Drive and Microsoft Graph scopes, provider review,
  clear consent, export/delete behavior, and outage/conflict recovery;
- local synthetic fixtures only for tests; no real OAuth accounts or provider
  credentials in normal validation.

## Save-to-Cookbook implications

0034C remains valid and independent of real SSO. Its synthetic core user is a
test ownership fixture, not a provider account and not a workaround for
authentication. Sidecar real-save wiring may eventually call a reviewed
core-owned adapter while receiving only safe UID/status/idempotency results.

Production real-save wiring must wait for the core's real account/session
mapping and its adapter authorization review. The sidecar must never supply
`userId`, session, cookie, provider token, or storage grant. Google Drive or
OneDrive support later may export/import/sync user-authorized files, but the
core remains the canonical recipe owner and validation boundary.

## Sequencing and next gate

1. Keep 0034C synthetic-auth verification as the local bridge; no real SSO is
   needed for it.
2. Create a separate core-auth security design covering provider registration,
   account linking, session lifecycle, secret custody, deletion, and recovery.
3. Implement Google identity-only sign-in in the core behind a reviewed local
   or staging gate, with mock contract tests and no sidecar token access.
4. Verify core-owned Save-to-Cookbook authorization with the resulting core
   session, still returning a safe adapter envelope to the sidecar.
5. Design and review Google Drive storage consent separately; only then
   evaluate a narrow BYOS proof.
6. Evaluate Microsoft identity plus OneDrive/Graph as the next provider using
   the same contracts and least-privilege review.

The next recommended task is **0034E: core-owned Google OIDC identity-only
implementation/security gate**. It must remain in the core workspace, define
no sidecar identity claims, and begin with mock/provider-contract and local
configuration review rather than a live account flow.

## Explicit non-goals

No Google/Microsoft client, OAuth/OIDC route, callback, token exchange,
provider account link, session, storage client, Drive/Graph API call, migration,
login button, public route, production deployment, Save-to-Cookbook production
path, direct sidecar DB write, browser/session automation, or secret is added.
