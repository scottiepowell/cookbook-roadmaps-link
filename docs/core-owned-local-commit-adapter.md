# Core-Owned Local Commit Adapter

Status: implemented in the separate source-owned core workspace; local-only
and explicitly gated.

Date: 2026-07-25

## External implementation

The source remains outside this sidecar repository.

- Branch: `openclaw/0033Z-core-owned-local-commit-adapter`
- Commit: `c8ee3ed8234135d5b889b84b2b14bd69397e4de3`
- Route: `POST /api/adapter/recipes/import-candidate/commit`
- Image: `local/vanilla-cookbook-adapter:0033z`

No external source, image layer, database, upload, session, or credential was
copied into this repository. The image is local-only and opt-in; the sidecar
Compose default remains `jt196/vanilla-cookbook:stable`.

## Auth and local gates

The route first requires the explicit local gate
`COOKBOOK_ADAPTER_LOCAL_COMMIT_ENABLED=true`, a loopback HTTP
`COOKBOOK_TARGET_URL` (defaulting conceptually to `http://127.0.0.1:3000/`),
and no AWS, GitHub Actions, or Cloudflare Tunnel environment indicators. It
then calls the normal core `requireAuth(locals)` helper. Anonymous requests
are rejected, and ownership always comes from the authenticated core user.

The candidate cannot supply `userId`, owner, cookie, token, session, auth, or
other identity assertions. Confirmation must be explicit with
`confirm_save: true`. The route is unavailable by default and is not enabled
in the production/exposed deployment.

## Mapping and commit behavior

The service validates the existing 0033X/0033Y contract and maps only the first
scope: name, description, invariant text servings, deterministic ingredient
lines, numbered directions, safe source/source URL, and bounded provenance
notes. Categories, media/uploads, remote image fetching, and embeddings are
excluded. The recipe is created with core-authenticated `userId`, private by
default, and a core-generated UUID.

Recipe creation runs inside the core Prisma `$transaction` callback. The
existing `Recipe.hash` field carries only an opaque adapter marker containing a
version, scoped key digest, and normalized candidate fingerprint. This avoids
a migration while making idempotency durable for adapter-created rows; it does
not store prompts, provider bodies, secrets, sessions, or raw candidate text.

The safe response contains status, adapter/contract/schema versions, canonical
local recipe UID, relative recipe URL, idempotency state, and next action. It
does not expose recipe rows, SQL, stack traces, absolute paths, cookies,
tokens, sessions, environment values, prompts, or provider output.

## Duplicate, replay, and rollback behavior

Within the transaction, the service checks the authenticated user's opaque
idempotency marker before any create. Same key and same normalized payload
returns the original UID with `replay`; same key with changed payload returns a
safe conflict. Matching user/name/ingredient/direction content returns a
review-required duplicate status without creating another row. No silent merge
or overwrite occurs.

An injected create failure is covered by a fixture transaction that restores
the pre-write state. The external tests use an in-memory Prisma-shaped fixture
store for deterministic offline coverage; they do not create sessions or
credentials. A future disposable runtime test must still back up and restore
`.local/vanilla-cookbook/db` and uploads around a single synthetic write.

## Evidence and remaining boundary

Focused external Vitest passes 20/20 tests across the dry-run service/routes
and commit service/route. Tests cover confirmation, auth and identity gates,
mapping, exclusions, validation, replay/conflict, duplicate blocking,
rollback, safe envelopes, and production/non-loopback refusal. Prisma
generation, service-worker generation, and the Vite production build passed.

The `local/vanilla-cookbook-adapter:0033z` image built successfully and was
started through the sidecar's guarded local scripts. Only the app service ran;
loopback returned HTTP 200 and the container was stopped afterward. A real
authenticated runtime commit was not attempted because creating or exporting a
session/cookie would violate the task boundary. The safe next step is a
separately approved local session/ownership test strategy or core-owned test
fixture, followed by disposable backup/restore verification. Production save
and sidecar UI wiring remain unimplemented.

## Explicit non-goals

No production Save-to-Cookbook, public production route, exposed target,
authentication bypass, cookie/session automation, direct sidecar DB write,
migration, category/media/upload/embedding side effect, provider call, UI
production button, source vendoring, AWS, Cloudflare, GitHub Actions, QMD,
analytics, ads, payment, or SSO/BYOS work was added.
