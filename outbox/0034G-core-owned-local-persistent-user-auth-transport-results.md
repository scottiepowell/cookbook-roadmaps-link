# 0034G Core-Owned Local Persistent-User Auth Transport Results

## Implementation

Implemented in the external Vanilla Cookbook workspace:

- Branch: `openclaw/0034G-core-owned-local-persistent-user-auth-transport`
- Commit: `453983d`
- Route: `POST /api/adapter/dev-only/recipes/import-candidate/verify-local-persistent-commit`
- Image: `local/vanilla-cookbook-adapter:0034g`

The route is a disabled-by-default core-owned local fixture. It creates or
reuses one synthetic persistent `AuthUser` in the disposable runtime database,
derives ownership inside the core process, and never creates or exports a
session, cookie, token, OAuth value, provider grant, or real credential.

## Local verification

The sidecar Compose file now passes the non-secret local fixture flags and
target/image markers into the app container, with disabled defaults. With
explicit persistent fixture approval, the route was exercised against
`cookbook-local` and returned safe HTTP 200 evidence:

- status: verified;
- commit: committed;
- read-after-write: verified;
- replay: replay;
- changed-key conflict: conflict;
- duplicate: duplicate review required;
- failure/rollback: verified;
- synthetic user: created by the core;
- content scope: first scope without categories/media/embeddings.

The runtime was stopped afterward. The route backed up and restored the
ignored disposable DB/uploads mounts. No recipe body, row dump, SQL, path,
cookie, token, session, or provider output was printed or committed. The
recipe was not browser-observed because that would require a real authenticated
session; safe core UID/read-after-write evidence was used instead.

## Sidecar transport

`ai-api/app/cookbook_core_transport.py` now has a separate, disabled-by-default
`send_core_local_persistent_commit` function. It requires the exact `0034g`
image marker, loopback target, `cookbook-local`, explicit enablement/approval,
and runtime verification. It sends only reviewed candidate data plus local
approval and allowlists safe response fields. The normal UI remains unwired.

## Validation

- External focused tests: 38 passed across the persistent route, prior core
  fixture, OIDC foundation, adapter, and commit suites.
- External Prisma generation, service-worker generation, and Vite build:
  passed with existing dependency/CSS warnings only.
- Custom image `local/vanilla-cookbook-adapter:0034g`: built locally and not
  pushed.
- Local persistent route: HTTP 200 safe verification as listed above.
- Sidecar pytest: 403 passed.
- Sidecar repository validation, `git diff --check`, and both Compose config
  checks passed.
- No live OpenAI, Google, Microsoft, OAuth, storage, or other provider call.

## Remaining blockers

The normal sidecar UI still uses the 0033S in-memory prototype and does not
call this transport. A future UI task must decide how a reviewed user action
can invoke a core-owned authenticated/persistent boundary without making the
sidecar an identity owner. Production Save-to-Cookbook and real Google login
remain unimplemented.

## Explicit non-goals

No production authentication, Google login, OAuth/session handling, Drive
scope, normal UI real-save button, public production route, migration, direct
sidecar DB write, browser/session automation, provider call, deployment work,
analytics, ads, payment, QMD, or external source vendoring was added.
