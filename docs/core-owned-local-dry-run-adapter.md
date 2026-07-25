# Core-Owned Local Dry-Run Adapter

Status: complete in the separate core workspace; dry-run only.

Date: 2026-07-25

## External workspace and image

The implementation lives outside this sidecar repository in the source-owned
Vanilla Cookbook checkout created by 0033W.

- Branch: `openclaw/0033X-core-owned-dry-run-adapter`
- Commit: `90c70c0 feat: add core-owned import dry-run adapter`
- Source pin: `7d94160e90368ed8ceb55b2dccfbbb5de1fb7b2c`
- Parser submodule pin: `6e8d1dff0c05f749b435c7e19b7f6627f60aa5d0`
- Image: `local/vanilla-cookbook-adapter:0033x`

No external source or source diff was copied into this repository. The custom
image is local-only and opt-in; `docker-compose.local.yml` still defaults to
`jt196/vanilla-cookbook:stable`.

## Adapter shape

The core workspace adds a pure service module at
`src/lib/server/importAdapter.js` and focused Vitest coverage. It intentionally
does not add an HTTP route in this task. A future route must use the normal
core authentication boundary and must be separately reviewed before exposure.

The service accepts a reviewed candidate plus the core app's current user
context. It does not import Prisma, filesystem, uploads, network clients, or
provider code. It cannot create a recipe, category, photo, embedding, or
background task.

## Ownership and candidate contract

The service requires a core user object with `userId`. The candidate cannot
provide or override ownership, cookies, sessions, tokens, or auth assertions.
Service tests inject a synthetic user object directly; they do not create a
session or credential.

Accepted first-scope fields are title/name, description, servings,
ingredients, instructions/directions, source, safe source URL, bounded notes/
provenance, idempotency key, and contract/schema versions. Unknown fields are
reported as safe validation errors.

## Mapping and response

The dry-run preview follows the schema-informed mapping:

- title/name -> `Recipe.name`;
- description -> `Recipe.description`;
- servings -> invariant text;
- ingredients -> trimmed one-item-per-line text;
- instructions -> numbered plain text in `Recipe.directions`;
- source and validated HTTP(S) source URL -> source fields;
- notes -> bounded reviewed provenance label;
- categories, media/uploads, remote image fetches, and embeddings -> excluded.

The safe envelope contains `status`, adapter/contract/schema versions, a mapped
recipe preview, field errors, warnings, duplicate status, idempotency status,
an opaque candidate fingerprint, and next-action guidance. It does not return
prompts, provider bodies, SQL, stack traces, absolute paths, secrets,
environment values, cookies, tokens, sessions, or database rows.

## Duplicate and idempotency behavior

The candidate fingerprint is deterministic over normalized title, ingredients,
owner scope, and contract version. Optional duplicate fingerprints are fixture
inputs only and produce a review-required warning. An injected in-memory
registry reports:

- same idempotency key and same normalized payload: `replay`;
- same key and different normalized payload: safe `conflict` error;
- matching candidate fingerprint: duplicate review signal, never a save or
  merge.

No real recipe lookup is performed. A future core route may add a safe,
authenticated duplicate lookup only after its read boundary is reviewed.

## Evidence and remaining gap

The external focused suite passes 7/7 tests, covering mapping, required fields,
unsafe URLs, unknown/provider-like fields, version mismatch, exclusions,
duplicate signals, replay/conflict, and no-persistence/leakage behavior. The
core build path also passed Prisma generation, service-worker generation, and
Vite production build.

The full upstream suite was attempted and is not a clean environmental gate:
607 tests passed, while six existing tests failed because five require an
OpenAI key and one live/fixture parser expectation changed; one suite also
needs generated Prisma setup (fixed for the build by running Prisma generate).
No live provider call was made.

The custom image was verified through this repository's local scripts. After
normalizing shell line endings in the external Windows checkout, it started
under `cookbook-local` and returned HTTP 200 at `http://127.0.0.1:3000/`; it
was stopped afterward. Standard disposable runtime initialization was the
only local runtime activity. The adapter performed no DB, upload, or recipe
mutation.

The remaining gap before commit/save is a separately approved authenticated
core route/service commit boundary with transaction, rollback, duplicate
storage, and explicit confirmation semantics. Production Save-to-Cookbook is
not implemented.

## Explicit non-goals

No commit/save mutation, production route, public route, migration, auth
bypass, cookie/session handling, browser automation, direct sidecar DB write,
production deployment, provider call, UI production button, source vendoring,
AWS, Cloudflare, GitHub Actions, QMD, analytics, ads, or payment work was
added.
