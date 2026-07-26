# 0034J Core Real Authenticated Session Plan Results

## Result

Created a security/design plan for the next phase: core-owned real
authenticated sessions. No provider, OAuth, session, cookie, database, or
production operation was executed.

## 0034I considered

0034I proved mock importer → sidecar dry-run → explicit local confirmation →
0034G persistent core commit, safe UID/read-after-write/idempotency status,
and disposable cleanup. Browser observation remained unavailable because no
real authenticated session exists.

## Core findings

The external core owns Lucia, Prisma-backed `AuthUser`/`AuthSession`,
`AuthAccount`, request `locals.user`, `requireAuth`, session creation,
validation, and logout invalidation. The current OIDC callback uses issuer
discovery, state and PKCE handoff cookies, `openid-client` validation, verified
email matching/provisioning, provider linking, `auth.createSession`, and
`locals.auth.setSession`.

The 0034E mock foundation normalizes identity and links provider subjects but
does not exercise real Lucia session creation or `locals.user` propagation.
The current tests do not provide an approved no-leak session-cookie lifecycle
test. These are the remaining real-session gaps.

## Decision and next task

Recommend option B first: `0034K` should implement a core-owned, loopback-only,
disabled-by-default mock OIDC session fixture using synthetic claims and a
disposable DB. It should exercise the real core session cookie lifecycle,
protected `locals.user`, account-link replay/collision, logout/invalidation,
and the core-owned Save-to-Cookbook adapter without any external provider.

Option A (manual local Google OIDC credentials) follows only after B passes.
Option C is rejected as an unnecessary alternate auth surface; option D is
not required because the core boundaries are identifiable, though production
auth remains gated.

## Required future custody

Any later Google task must use only ignored local configuration, identity-only
scopes (`openid email profile`), loopback redirect URI, redacted logs, and an
in-memory cookie jar. No Drive/storage scopes, tokens, cookies, client
secrets, OAuth codes, real profile data, or browser artifacts may enter the
repository or outbox.

## Remaining observation blockers

The sidecar cannot safely observe a real saved recipe until a core session is
created and validated in a real local client context. The sidecar must remain
candidate-only and must not receive or forward core identity/session values.
After 0034K, a separate manual Google task is still required before claiming
real provider authentication. Production authentication and production
Save-to-Cookbook remain separate approvals.

## Validation

Docs-only validation completed:

- `git diff --check`;
- `scripts/validate-repo.sh`;
- `docker compose config --quiet`; and
- `docker compose -f docker-compose.local.yml -p cookbook-local config --quiet`.

No live OpenAI, Google, Microsoft, OAuth, storage, or browser session call was
made. No sidecar code/config change was made, so the sidecar test suite was not
required by the task.

## Explicit non-goals

No production auth, Google login, OAuth client, provider call, secret, token,
cookie, session, browser automation, migration, storage grant, direct sidecar
DB write, production Save-to-Cookbook, deployment, or external source was
added.
