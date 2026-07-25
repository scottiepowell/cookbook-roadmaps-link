# 0034B Sidecar Real-Save Local Wiring Plan Results

Date: 2026-07-25

## Result

Created the planning/gate document
[Sidecar Real-Save Local Wiring Plan](../docs/sidecar-real-save-local-wiring-plan.md).

It records the completed 0033S, 0033Q, 0033Y, 0033Z, and 0034A evidence and
the remaining bridge: the sidecar has no reviewed way to establish the core
authenticated user context without handling cookies, tokens, sessions, or
real credentials.

## Options and recommendation

Evaluated in-memory prototype, core-owned local fixture, sidecar-to-core
client, browser/session export, and direct sidecar DB writes. Browser/session
export and direct DB writes are rejected. The in-memory UI remains a valid
prototype but is not feature-complete. Sidecar client wiring is deferred.

Recommended next task: **0034C**, a core-owned local dev-only adapter
verification fixture with synthetic in-process `AuthUser`, dry-run-before-
commit, explicit local approval, loopback/custom-image guards, disposable
DB/uploads backup/restore, safe read-after-write, and no credential export.

## Required future bridge behavior

Any later sidecar client must call only a reviewed core-owned adapter, never
own identity or write storage, and receive only safe UID/status/idempotency
envelopes. The sequence remains review -> dry-run -> explicit confirmation ->
core commit -> local canonical link -> restore/cleanup. The target must be
`cookbook-local` on loopback with opt-in image
`local/vanilla-cookbook-adapter:0034a`; production/exposed targets remain
disabled.

## Status and non-goals

Sidecar UI real-save wiring is still blocked. Production Save-to-Cookbook is
not implemented. No code routes, UI controls, auth/session handling, database
writes, migrations, provider calls, cloud/platform work, or external source
were added.

Validation: `git diff --check`, repository validation, default Compose config,
and local Compose config are required after documentation edits. No live
OpenAI or external provider call is used.
