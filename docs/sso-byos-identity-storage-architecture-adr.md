# ADR: SSO, Email Identity, and Bring-Your-Own-Storage

Status: proposed, docs/research-only

Date: 2026-07-23

## Decision summary

Treat identity and user-owned storage as two separately authorized capabilities.
The Cookbook core app may eventually use email or an external identity
provider for sign-in, while a user may independently connect Google Drive,
Dropbox, OneDrive, or another supported storage provider for recipe data. A
sign-in provider must not automatically receive storage access, and a storage
connection must not become the user's identity authority.

The preferred direction is portable, user-readable export in a provider-
controlled app folder or equivalent least-privilege location. The core app may
retain minimal identity, consent, session, timer, metering, abuse, and
audit-safe metadata, but must not silently become the permanent owner of the
user's recipe corpus.

This is architecture/research only. It adds no auth flow, provider SDK,
storage client, endpoint, migration, secret, or production route.

## Research note and provider facts

Public documentation was reviewed on 2026-07-23. These are high-level
constraints, not implementation approval and may change:

- Google documents OAuth 2.0 authorization-code web-server flows, scoped API
  access, offline access/refresh tokens, and server-side ID-token validation.
  It also recommends using the stable OpenID Connect `sub` identifier rather
  than email as the account key, and marks many Drive scopes as sensitive.
  See [Google OAuth web-server guidance](https://developers.google.com/identity/protocols/oauth2/web-server),
  [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect),
  and [Google OAuth scopes](https://developers.google.com/identity/protocols/oauth2/scopes).
- Google documents that refresh tokens can be invalidated by user revocation,
  protective processes, or expiration. Connections need a reconnect path.
  See [Google OAuth policies](https://developers.google.com/identity/protocols/oauth2/policies).
- Meta/Facebook Login is an identity option, but permission review, product
  availability, data-use policy, and deletion obligations must be verified at
  implementation time. Meta's public Login material includes app-removal/data
  deletion handling; this ADR does not assume a Meta storage product. See
  [Meta Login notes](https://developers.facebook.com/docs/facebook-login/changelog/).
- Dropbox documents OAuth 2.0 user authorization and distinguishes App Folder
  from Full Dropbox access. App Folder limits an app to its application area.
  See [Dropbox OAuth guide](https://developers.dropbox.com/oauth-guide),
  [Dropbox authentication types](https://www.dropbox.com/developers/reference/auth-types),
  and [Dropbox getting started](https://www.dropbox.com/developers/reference/getting-started).
- Microsoft Graph documents an application folder (`approot`) and the
  dedicated `Files.ReadWrite.AppFolder` permission for OneDrive/SharePoint.
  It also notes quota, user edits/deletions, and app-folder availability as
  concerns. See [Microsoft app-folder guidance](https://learn.microsoft.com/en-us/graph/onedrive-sharepoint-appfolder)
  and [Graph permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference).

Provider facts require implementation-time review of account populations,
consent wording, redirect/PKCE requirements, token lifetimes, revocation,
quotas, conflict semantics, regional processing, and current terms.

## Problem statement

The product needs a credible path to user accounts and durable, portable recipe
data without making the Cookbook application the only long-term data owner.
The current local sidecar is mock/offline and has no production identity or
storage integration. Adding identity and storage together creates a large
trust boundary involving account linking, consent, token custody, sync, data
deletion, provider outages, and ownership ambiguity.

## Identity options

Email/password provides control but creates password storage, reset,
verification, recovery, delivery, abuse, and breach responsibilities. Magic
links avoid stored passwords but still require one-time links, replay
protection, expiry, delivery, recovery, and enumeration-resistant messaging.

Google is a strong OIDC sign-in candidate and also a possible Drive provider;
the two grants must remain separate. Facebook/Meta Login is optional and adds
provider policy, review, data-deletion, and account-availability risks. Microsoft
identity/OneDrive is a useful comparison, especially with its app-folder
permission. Other OIDC providers should use a stable identity adapter only
after provider and recovery review. Provider count should stay small.

## Identity and storage boundary

Identity answers “which app account is this?” Storage authorization answers
“where may this app read or write this user's files?” They are separate records
and consent actions:

```text
Core Cookbook account
  | identity links: provider, stable subject, status
  | optional 30-minute session/timer policy
  v
Cookbook AI Adapter
  | minimal authorized user context
  | separate storage connection reference
  v
Storage adapter -> user-selected provider app folder
```

A user may sign in with Google and connect Dropbox, sign in with email and
connect OneDrive, or use no cloud storage. Neither connection changes the
other's authority.

## Consent, scopes, and data placement

Consent must say what data is accessed, why, where it is stored, how long the
connection is used, and how to disconnect it. Request identity scopes only at
sign-in and storage scopes only during an explicit connect action. Prefer
app-folder/app-specific scopes over full-drive access. Never request broad
read/write access merely for convenience.

### BYOS candidate data

- user recipe exports;
- imported recipe drafts;
- AI notes;
- meal plans;
- user-owned application backups;
- portable JSON/Markdown bundles.

Bundles should be versioned, documented, human-readable where practical, and
contain stable IDs and provenance without secrets, prompts, or diagnostics.

### App-local candidate data

- minimal account identity link;
- consent and non-secret provider connection status;
- session/timer state;
- usage and budget counters;
- abuse-prevention state;
- audit-safe events and short-lived workflow caches.

The app may retain disclosed operational metadata, but canonical recipe content
should prefer the user's selected storage once BYOS is active. A future sync
design must define whether app-local drafts are temporary, cached, or canonical.

## Local/offline fallback

The current local product must continue working with generated fixtures and the
mock provider without an account, cloud connection, provider key, or network.
Phase 1 should define local export/import bundles before cloud integration. If
storage disconnects, offer export, safe local read-only recovery, and clear
messaging about what cannot sync. Offline mode must not claim cloud persistence.

## Tokens, revocation, and deletion

Authorization-code exchange, token validation, refresh, and provider calls
belong on a server-side adapter. A future design should use state/nonce/PKCE as
appropriate, exact redirect allowlists, issuer/audience/expiry checks, and
encrypted secret storage. Store refresh tokens only when background sync has a
documented need; otherwise prefer user-present operations.

Refresh tokens are high-value bearer credentials: encrypt, restrict, rotate,
revoke, and redact them. Associate them with a provider connection, not an
email. Treat expired, revoked, malformed, or scope-reduced tokens as a
disconnected state, not a retry loop. Never send them to browser code, logs,
support views, or AI prompts.

Disconnect stops future provider calls and removes stored tokens, while leaving
user-owned cloud files unless the user explicitly requests supported deletion.
Account deletion must separately address app-local identity/session/timer/
metering metadata, user-owned BYOS files, temporary app copies, and provider
authorization. Do not silently delete user-owned files. Record only safe
completion metadata.

Import/export must be explicit and reviewable. Export produces bounded
JSON/Markdown; import validates schema/version, preserves IDs when safe, detects
conflicts, and never silently overwrites canonical content.

User-friendly failures include disconnected provider, expired consent, quota
exceeded, outage, revoked permission, missing file, file conflict, and sync
conflict. Show recovery without raw provider bodies or tokens.

## Privacy, security, UX, and timer consistency

Publish a data map for identity attributes, recipe content, AI notes, provider
metadata, tokens, logs, and caches. Minimize profile data and review applicable
privacy, deletion, retention, transfer, age, accessibility, and processing
obligations before launch; this ADR is not legal advice.

Threats include account takeover, confused-deputy access, token theft,
malicious imports, sync overwrite, consent phishing, stale connections, and
abusive session creation. The adapter must verify connection ownership and
scope on every operation. The sidecar receives only minimal recipe context and
never identity or storage refresh tokens.

Sign-in and storage connection are separate, understandable actions. Show the
identity provider and storage provider independently; allow either to be
disconnected; and label data local, synced, pending, conflicted, or exported.

The 30-minute timer applies to application access, not cloud authorization.
Expiry may pause protected AI/sync actions, but must not revoke cloud grants or
delete drafts. Exceptions still cannot bypass storage ownership, consent,
revocation, budgets, or kill switches.

## Staged implementation options

1. **Phase 0:** docs-only architecture and provider fact review.
2. **Phase 1:** local export/import bundle format without cloud integration.
3. **Phase 2:** identity-only login prototype behind a local/dev gate, proving
   linking, logout, recovery, revocation, safe session handoff, and redaction.
4. **Phase 3:** one BYOS provider proof of concept using least-privilege
   app-folder storage and explicit connect/import/export/disconnect flows.
5. **Phase 4:** provider-neutral identity/storage adapters, adding providers
   only when portability and support cost justify them.
6. **Phase 5:** production deletion, revocation, backup/restore, support,
   retention, and outage operations.

Recommend Phase 1 before any provider integration. Choose the first identity
and storage providers only after separate security/privacy review.

## Contract and testing strategy

Future interfaces should be provider-neutral and server-side:

```text
IdentityProvider
  begin_sign_in(return_to, state) -> AuthorizationRedirect
  exchange_callback(code, state) -> IdentityAssertion
  revoke(identity_connection) -> RevocationResult

StorageProvider
  connect(user_context, consent) -> StorageConnection
  export(connection, bundle) -> StorageWriteResult
  import(connection, bundle_reference) -> StorageReadResult
  disconnect(connection) -> DisconnectResult
```

These are sketches, not endpoints. Mock-only contract tests should cover
token redaction, expired/revoked consent, import/export round trips,
version mismatch, file/sync conflicts, quota/outage recovery, disconnect and
deletion semantics, offline fallback, timer interactions, and no live provider
calls during normal validation.

## Explicit non-goals

No SSO, OAuth/OIDC, email registration, auth endpoint, cloud-storage client,
provider SDK, migration, secret/configuration, token exchange, production
route, payment, analytics, ads, monetization, timer enforcement, AWS/platform
work, live provider call, vector storage, embedding, or UI rewrite is added.
