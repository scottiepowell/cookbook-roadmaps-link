# 0034D — Google-First OIDC + Future Storage Auth Architecture

Do not create a new task.
Do not implement authentication, SSO, OAuth, OIDC, storage integration, account linking, token refresh, provider callbacks, migrations, routes, UI login buttons, production deployment, or live provider calls.
Do not create Google, Microsoft, Dropbox, Apple, Meta, or other provider clients.
Do not create, export, print, persist, or commit cookies, auth tokens, refresh tokens, ID tokens, access tokens, sessions, real user credentials, browser state, OAuth client secrets, local env values, or real account data.
Do not target `https://cookbook.roadmaps.link`.
Do not use AWS, GitHub Actions, Cloudflare, tunnels, or the production deployment.
Do not inspect or modify production data.
Do not bypass core auth.
Do not place Vanilla Cookbook identity ownership in the AI sidecar.
Do not add direct sidecar database writes.
Do not vendor or copy external Vanilla Cookbook source into this sidecar repository.
Do not commit secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, or session values.

## Goal

Create the architecture decision for **Google-first external OIDC authentication with future bring-your-own-storage support**, while preserving the project boundary chosen after `0034B`:

```text
External SSO/OIDC provider
        ↓
Vanilla Cookbook core auth adapter/plugin
        ↓
Core AuthUser / session / account linkage
        ↓
Core-owned Save-to-Cookbook adapter
        ↓
Canonical recipe storage
```

The AI sidecar must remain a candidate generator/client, not the owner of identity, sessions, user IDs, storage tokens, or canonical recipe persistence.

This is an ADR/planning task. It should prepare the later auth/SSO implementation path, but it must not implement auth or storage yet.

## Context

The user selected the architecture direction previously discussed as Option C:

```text
External OIDC/SSO provider with core-owned session mapping.
```

They want to start with Google because a future feature is bring-your-own-storage and Google has a major public identity provider plus Google Drive/Workspace storage APIs. Microsoft should be evaluated as the next likely provider because Microsoft identity and OneDrive/Graph are also major public identity/storage ecosystems. Other providers can be sequenced later.

Current verified project state:

```text
0033S: sidecar local UI/in-memory prototype exists
0033Q: disposable DB/write readiness harness exists
0033Y: authenticated core dry-run route exists in external core workspace
0033Z: authenticated core commit route/service exists in external core workspace
0034A: synthetic core AuthUser + real SQLite service-level commit verification passed
0034B: planned sidecar real-save wiring and recommended 0034C synthetic-auth fixture
0034C: queued to prove a core-owned dev-only synthetic auth fixture before UI real-save wiring
```

`0034C` should stay narrow and should not depend on real Google/Microsoft SSO. This `0034D` task should define the future production auth/storage architecture after the local synthetic-auth bridge is proven.

## Read first

From this sidecar repository:

```text
inbox/0034C-core-owned-dev-only-synthetic-auth-fixture.md
outbox/0034B-sidecar-real-save-local-wiring-plan-results.md
docs/sidecar-real-save-local-wiring-plan.md
outbox/0034A-core-owned-local-auth-commit-verification-results.md
docs/core-owned-local-auth-commit-verification.md
outbox/0033Z-core-owned-local-commit-adapter-results.md
docs/core-owned-local-commit-adapter.md
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
README.md
```

Also read any earlier SSO/BYOS docs if present, especially files matching:

```text
docs/*sso*
docs/*byos*
docs/*identity*
docs/*storage*
outbox/*0033C*
```

Do not assume filenames; search the repository if needed.

## Research requirements

Use current official provider documentation where internet access is available. Provider auth/storage facts can change, so verify against official sources and cite exact URLs in the ADR.

At minimum, research and cite:

```text
Google Identity Services / OpenID Connect support
Google OAuth/OIDC recommended scopes for sign-in: openid, email, profile
Google Drive API OAuth scope posture, especially least-privilege drive.file style scopes
Google OAuth app verification / sensitive or restricted scope implications
Microsoft identity platform OIDC support
Microsoft Graph / OneDrive file permission and storage API scope posture
```

Optional future-provider notes may include Dropbox, Apple, GitHub, or Meta, but only as high-level sequencing notes. Do not over-design them.

Clearly separate:

```text
observed repository facts
current official provider facts
architecture decisions
open questions / future verification gates
```

## Architecture questions to answer

Evaluate these options:

```text
A. Google-first OIDC in Vanilla Cookbook core, with storage authorization added later as separate Google Drive consent.
B. Google-first OIDC and Google Drive storage consent bundled at first login.
C. Sidecar-owned auth and storage tokens.
D. Reverse-proxy/BFF-owned auth with core session projection.
E. Provider-agnostic auth abstraction first, with Google as the first adapter.
F. Email/password or local-only auth first, SSO later.
```

Expected posture:

```text
Prefer A plus enough of E to avoid a Google-only dead end.
Reject C because the sidecar must not own Cookbook identity, sessions, storage tokens, or user IDs.
Be cautious with B because storage consent should usually be progressive and separate from sign-in.
Treat D as possible later platform architecture, not necessary for the local core-owned path.
Keep F only as a local/dev fallback if already supported by Vanilla Cookbook, not as the strategic production path.
```

## Required design decisions

The ADR must decide or explicitly defer each item:

```text
1. Core owns AuthUser/session mapping.
2. External provider identity maps to a core account/provider link record.
3. Sidecar never supplies userId, session, cookie, or provider token claims.
4. Storage authorization is separate from login authorization.
5. Google is the first production provider candidate.
6. Microsoft is the next provider to evaluate because of Microsoft identity + OneDrive/Graph.
7. OAuth/OIDC client secrets and refresh tokens are never stored in repo or sidecar local artifacts.
8. Token storage, encryption, rotation, revocation, and deletion require a future security task.
9. BYOS storage must use least-privilege, app-specific or user-selected file/folder scopes where provider-supported.
10. Save-to-Cookbook remains core-owned; provider storage is an optional import/export/sync layer, not canonical recipe ownership unless a later ADR changes that.
```

## Google-first conceptual model

Define the first Google auth/storage model as two consent steps:

```text
Step 1: Sign in with Google using OIDC identity scopes only.
Step 2: Later, connect Google Drive storage with a least-privilege Drive scope for BYOS features.
```

The ADR should explain why the steps are separated:

```text
login should not require storage permission;
users may want local/core storage only;
storage consent can be requested when the user enables BYOS;
Google Drive scopes may require extra verification and security review;
progressive consent keeps the first login simpler and safer.
```

## Provider abstraction sketch

Define a small future provider abstraction without implementing it:

```text
IdentityProviderAdapter
- provider_id
- oidc_discovery_url or issuer
- auth_url/token_url/userinfo strategy
- normalized subject mapping
- email_verified handling
- display name/avatar handling
- account-linking rules
- logout/revocation capabilities

StorageProviderAdapter
- provider_id
- connect authorization URL
- granted scopes
- root/app folder strategy
- file picker / selected file strategy
- recipe export/import/sync capabilities
- token refresh/revocation requirements
- user-visible disconnect/delete behavior
```

Do not add code for these adapters in this task.

## Data model planning

Draft future data model requirements without adding migrations:

```text
CoreUser/AuthUser
ProviderAccountLink
ProviderTokenGrant or StorageConnection
StorageProviderFileReference
Audit/SecurityEvent for connect/disconnect/revocation
Idempotency linkage for import/export/sync operations
```

Each planned table/object must include:

```text
purpose
minimum fields
sensitive fields
retention/deletion behavior
whether it belongs in Vanilla Cookbook core, sidecar, or future platform service
```

Expected decision: identity and token grants belong to the core/platform auth boundary, not the AI sidecar.

## Security/privacy requirements

Document requirements for future tasks:

```text
PKCE and state/nonce validation where applicable
redirect URI allowlist
issuer/audience validation
email_verified handling
account linking collision rules
CSRF protection
secure same-site cookies managed by the core app
no token exposure to sidecar UI or logs
refresh token encryption at rest
token revocation/disconnect path
user data export/delete path
provider app verification requirements
least-privilege Drive/Graph scopes
safe local dev fixtures that do not use real credentials
```

## Save-to-Cookbook implications

Explain how this affects Save-to-Cookbook:

```text
0034C remains local synthetic auth proof and should not wait for Google SSO.
Sidecar real-save wiring can use the core-owned local fixture first.
Production real-save wiring should wait for real core auth/SSO account mapping.
The sidecar should call reviewed core-owned adapters and receive safe UID/status/idempotency envelopes only.
BYOS storage later can import/export/sync recipe files, but it must not bypass core Save-to-Cookbook ownership or validation.
```

## Documents to create/update

Create:

```text
docs/google-first-oidc-storage-auth-architecture.md
outbox/0034D-google-first-oidc-storage-auth-architecture-results.md
```

Update as appropriate:

```text
README.md
docs/sidecar-real-save-local-wiring-plan.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The docs must clearly state:

```text
Google is the first planned external OIDC provider candidate.
Storage authorization is separate from login authorization.
Core owns auth/session/user mapping.
The AI sidecar does not own identity, sessions, cookies, provider tokens, or storage grants.
Production Save-to-Cookbook remains not implemented.
0034C synthetic-auth fixture remains the next local bridge and does not require real SSO.
No provider secrets, tokens, sessions, or real OAuth flows were used.
```

## Outbox summary requirements

The outbox must summarize:

```text
docs created/updated
provider docs researched and cited
recommended Google-first architecture
Microsoft/later-provider sequencing
login vs storage consent decision
data model planning
security/privacy requirements
Save-to-Cookbook implications
next recommended implementation task
validation results
explicit non-goals
```

## Acceptance criteria

```text
Google-first OIDC + future storage ADR exists.
Official current provider documentation is cited.
Google sign-in and Google Drive storage consent are separated in the architecture.
Microsoft is identified as the next provider to evaluate.
Core-owned auth/session mapping is preserved.
Sidecar-owned auth/tokens/storage grants are rejected.
Future data model and security requirements are documented.
Save-to-Cookbook implications are documented.
0034C remains unblocked and independent from real SSO.
No auth/SSO/storage code, routes, migrations, UI login buttons, provider clients, live OAuth flows, production deployment, or provider calls are implemented.
No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container source snapshots, cookies, auth tokens, session values, OAuth client secrets, access tokens, refresh tokens, or ID tokens are committed.
```

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

If docs-only, full static/repo validation is enough. Do not run live OpenAI. Do not run real OAuth flows.

Commit:

```bash
git add docs README.md outbox/0034D-google-first-oidc-storage-auth-architecture-results.md

git commit -m "docs: plan google first oidc storage auth"

git pull --rebase origin main

git push origin main
```
