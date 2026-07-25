# 0034C Core-Owned Dev-Only Synthetic Auth Fixture Results

Date: 2026-07-25

## External workspace

Created branch
`openclaw/0034C-core-owned-dev-only-synthetic-auth-fixture` and committed
`e6172b350375d204aec22371d473e53bad23e24d`.

Added a fail-closed guard helper, focused guard tests, and the dev-only
`scripts/verify-local-auth-commit.mjs` command. The source remains outside the
sidecar repository.

## Fixture evidence

The command requires explicit development, approval, synthetic-fixture,
approved-image, and loopback settings. It rejects production, exposed,
Cloudflare, AWS, GitHub/CI, and default-image contexts before setup. It creates
only a synthetic in-process core `AuthUser`, runs dry-run before commit, and
never creates or exports cookies, tokens, sessions, real credentials, or
browser state.

The explicit run completed successfully and emitted safe phase/status output:
dry-run ready, commit with an opaque UID, replay, conflict, duplicate review,
rollback, and restore. It used a temporary schema-backed SQLite DB and empty
uploads directory, backed both up before fixture setup, restored both after
verification, confirmed zero recipes, and removed the temporary directory.

It proved safe read-after-write ownership, one recipe only, idempotent replay,
changed-key conflict, duplicate blocking, foreign-owner rollback, and no
categories/photos/embeddings. Guard tests passed 3/3; the combined external
adapter/route/commit focused suite passed 23/23.

The image `local/vanilla-cookbook-adapter:0034c` built successfully. Guarded
sidecar startup with that image ran only `cookbook-local`, returned HTTP 200 at
`http://127.0.0.1:3000/`, and stopped the container. No provider call was
made.

## Remaining boundary

The fixture is core-process verification, not sidecar UI wiring. The sidecar
UI remains the in-memory prototype until a later task approves a safe
sidecar-to-core transport that does not own identity or export session
credentials. Production Save-to-Cookbook remains unimplemented; direct sidecar
DB writes and browser/session automation remain rejected.

## Sidecar changes and non-goals

Added [Core-Owned Dev-Only Synthetic Auth Fixture](../docs/core-owned-dev-only-synthetic-auth-fixture.md)
and updated related status, backlog, integration, acceptance, README, and
roadmap docs. No sidecar code, route, UI wiring, external source, database,
upload, secret, prompt, provider output, screenshot, trace, raw dataset,
generated index, local env value, cookie, token, session, or browser artifact
was committed.
