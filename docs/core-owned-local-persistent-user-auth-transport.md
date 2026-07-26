# Core-Owned Local Persistent-User Auth Transport

Status: verified local/dev-only persistent fixture; normal UI wiring and
production Save-to-Cookbook remain unimplemented.

Date: 2026-07-26

## Core implementation

The separate Vanilla Cookbook workspace contains the core-owned route:

`POST /api/adapter/dev-only/recipes/import-candidate/verify-local-persistent-commit`

External branch:
`openclaw/0034G-core-owned-local-persistent-user-auth-transport`

The route is included in local image
`local/vanilla-cookbook-adapter:0034g` only. It is disabled unless the
explicit persistent fixture flags, synthetic fixture mode, loopback target,
and exact local image marker are present. Production, CI, AWS, Cloudflare,
tunnel, and non-loopback contexts fail closed.

The core process creates or reuses exactly one synthetic `AuthUser` with a
fixed dev-only identity. It does not create a Lucia session, cookie, token,
OAuth value, provider grant, or real account. Ownership is derived from this
core-owned user object; the candidate cannot provide a user ID or ownership
claim.

## Verification sequence

Before any write, the route backs up the disposable database and uploads
mounts. It then runs core dry-run validation, commits through
`commitRecipeImport`, reads the recipe back from the runtime database using
safe UID/owner/status checks, and verifies:

- one successful first-scope recipe commit;
- same-key replay without a second recipe;
- changed-payload idempotency conflict;
- duplicate fingerprint review without unbounded creation;
- invalid empty-owner rejection before a write;
- no categories, photos, uploads, or embeddings.

Finally it restores the database/uploads backup and removes the temporary
backup. The returned envelope contains only status, opaque recipe UID,
relative recipe URL, idempotency states, verification states, synthetic-user
status, and content-scope status. No rows, recipe bodies, SQL, paths, stack
traces, secrets, or credentials are returned.

The local Compose file passes only non-secret fixture settings into the app;
all fixture flags default to disabled. The sidecar transport has a separate
`0034g` persistent function and remains disabled by default. It sends only
the reviewed candidate and explicit approval; it never sends identity,
cookies, sessions, tokens, OAuth codes, provider grants, or storage grants.

## Local evidence and limits

With the `0034g` image, loopback target, `cookbook-local` project, and explicit
flags enabled, the route returned safe HTTP 200 evidence for commit,
read-after-write, replay, conflict, duplicate review, and rollback. The
runtime was stopped after the run. The saved recipe is not observed in the
browser UI: the verification uses a synthetic core owner and restores the
disposable storage, so no real authenticated browser session exists.

This is persistent disposable-runtime evidence, not production authentication.
Real Google OIDC, real sessions, storage consent, normal sidecar UI save
wiring, and production Save-to-Cookbook remain separate work.

## Explicit non-goals

No production auth, Google login, OAuth/provider call, Drive scope, session or
cookie export, normal UI button, public production route, migration, direct
sidecar DB write, browser automation, deployment work, analytics, ads,
payment, QMD, or external source vendoring was added.
