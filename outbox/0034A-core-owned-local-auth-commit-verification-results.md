# 0034A Core-Owned Local Auth Commit Verification Results

Date: 2026-07-25

## External branch and implementation

Created external branch:
`openclaw/0034A-core-owned-local-auth-commit-verification`

External verification commit:
`ffd71da4a8b2c83a8699bad4f2bc5fd77bd991d4`

The branch adds an opt-in real SQLite integration test for the existing core
commit service. It does not add a new production route, auth bypass, or
sidecar code.

## Synthetic auth/ownership and persistence evidence

With `RUN_LOCAL_AUTH_COMMIT_DB=1`, the test pushes the existing Prisma schema
to a temporary SQLite database, creates one synthetic `AuthUser`, derives an
in-process core `userId` context, and invokes `commitRecipeImport`. It does not
create or export cookies, tokens, sessions, real credentials, or browser
state.

The test passed 3/3 and proved one real persisted recipe, safe UID/owner
read-after-write, same-key replay, changed-payload conflict, duplicate review
without a second row, foreign-owner failure rollback, and exclusion of
categories/photos/embeddings. It snapshots the empty schema database before
fixture setup, restores that snapshot after verification, confirms zero recipes
after restore, disconnects Prisma, and removes the temporary database.

Normal focused external coverage passed 23/23. Prisma generation, service
worker generation, and Vite build passed. The new local image
`local/vanilla-cookbook-adapter:0034a` built successfully. Guarded sidecar
startup with that image ran only `cookbook-local`, returned HTTP 200 on
`http://127.0.0.1:3000/`, and stopped the container afterward.

## Remaining limitations

The evidence is a core service-level authenticated ownership fixture, not a
browser or HTTP-session test. Route-level verification remains intentionally
blocked because the task forbids creating/exporting session values, cookies,
tokens, or real credentials. The route's normal `requireAuth(locals)` gate is
already covered by focused handler tests. Sidecar UI real-save wiring remains
not ready until a future task approves a safe in-process route fixture and
disposable runtime backup/restore path.

Production Save-to-Cookbook remains unimplemented.

## Sidecar changes and non-goals

Added [Core-Owned Local Auth Commit Verification](../docs/core-owned-local-auth-commit-verification.md)
and updated status, backlog, integration, README, and roadmap references.
No external source was copied into the sidecar repository.

No production save, public route, migration, auth bypass, browser/session
automation, direct sidecar DB write, AWS, GitHub Actions, Cloudflare, QMD,
analytics, ads, payment, SSO/BYOS, provider routing, live call, secret,
prompt, provider output, screenshot, trace, raw dataset, generated index,
local env value, DB, upload, row dump, cookie, token, session, or browser
artifact was committed.
