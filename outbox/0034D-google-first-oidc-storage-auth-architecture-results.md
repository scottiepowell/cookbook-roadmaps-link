# 0034D Google-First OIDC + Future Storage Auth Architecture Results

## Completed

- Created [Google-First OIDC and Future Storage Authorization](../docs/google-first-oidc-storage-auth-architecture.md).
- Updated the project status/backlog/roadmap and local integration guidance to
  record the core-owned identity boundary and separate storage consent.

## Research

Reviewed current official documentation for Google OIDC, Google sign-in
scopes, Google Drive least-privilege scopes and verification, Microsoft OIDC,
Microsoft identity scopes, and Microsoft Graph file permissions. Exact primary
links are cited in the ADR. No OAuth flow, account, token, cookie, or provider
client was used.

## Decision

Google is the first planned external OIDC candidate in the Vanilla Cookbook
core. Sign-in uses identity-only consent; Google Drive is a later, separate
BYOS consent step. Provider-neutral identity/storage contracts are planned so
Microsoft identity plus OneDrive/Graph can be evaluated next.

The core owns `AuthUser`, sessions, provider links, token grants, storage
connections, and Save-to-Cookbook authorization. The AI sidecar remains a
reviewed candidate generator/client and owns none of those values.

## Save-to-Cookbook impact

0034C synthetic-auth verification remains independent of real SSO. Production
Save-to-Cookbook is not implemented. Future sidecar wiring must call a reviewed
core adapter and receive safe UID/status/idempotency results only; it must not
forward a user ID, cookie, session, provider token, or storage grant.

## Validation

- `git diff --check` passed.
- Repository validation passed with `scripts/validate-repo.sh`.
- Both production-shaped and local Compose configurations passed `config --quiet`.
- No live OpenAI, OAuth, Google, Microsoft, storage, or production calls were
  made.

## Explicit non-goals

No auth/SSO/OIDC code, storage integration, provider clients, callbacks,
migrations, routes, login UI, token handling, secrets, cookies, sessions,
production deployment, direct sidecar writes, or production Save-to-Cookbook
was added.
