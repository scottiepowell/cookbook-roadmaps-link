# 0033Z Core-Owned Local Commit Adapter Results

Date: 2026-07-25

## Implementation

Implemented the first core-owned authenticated commit adapter in the separate
source workspace:

- Branch: `openclaw/0033Z-core-owned-local-commit-adapter`
- Commit: `c8ee3ed8234135d5b889b84b2b14bd69397e4de3`
- Route: `POST /api/adapter/recipes/import-candidate/commit`
- Image: `local/vanilla-cookbook-adapter:0033z`

The route is disabled by default. It requires explicit local enablement,
loopback HTTP target, no AWS/GitHub/Cloudflare indicators, normal core
authentication, and `confirm_save: true`. Ownership is derived only from
authenticated core context; sidecar identity assertions are rejected.

## Commit, idempotency, and rollback

The adapter uses the validated 0033X/0033Y mapping: text servings,
deterministic ingredient lines, numbered directions, safe source metadata,
bounded provenance, and no categories, media/uploads, remote image fetches, or
embeddings. Recipe creation uses the core Prisma transaction boundary and the
existing `Recipe.hash` field for an opaque, versioned idempotency marker; no
migration was added.

Same-key same-payload replay returns the original safe UID/URL, changed-payload
reuse returns conflict, and matching user/name/ingredient/direction content is
a review-required duplicate with no second write. Injected create failure is
rolled back by the fixture transaction. Responses contain only safe status,
version, UID/relative URL, and idempotency metadata.

## Tests and build

Focused external Vitest passed 20/20 tests. Prisma generation, service-worker
generation, and Vite production build passed. The custom image built
successfully. No live provider call, credential, cookie, session, production
target, or production data was used.

The custom image was started with the sidecar guarded local scripts and
`cookbook-local`; only the app service ran and `http://127.0.0.1:3000/` returned
HTTP 200. It was stopped afterward. A real authenticated runtime commit was
not attempted because obtaining or exporting a session would violate the
explicit task boundary. Disposable runtime DB/upload contents were not
committed or inspected beyond existing safe startup checks.

## Sidecar and remaining work

Added [Core-Owned Local Commit Adapter](../docs/core-owned-local-commit-adapter.md).
Only documentation/outbox changes were made in the sidecar repository. A
future task may consider sidecar UI wiring after a safe local auth/ownership
fixture and disposable backup/restore verification are approved. Production
Save-to-Cookbook remains unimplemented.

## Explicit non-goals

No production or public route, production write-back, migration, auth bypass,
browser/session automation, direct sidecar DB write, categories, media,
uploads, embeddings, provider call, AWS, GitHub Actions, Cloudflare, QMD,
analytics, ads, payment, SSO/BYOS, or UI production button was added. No
secrets, prompts, provider output, screenshots, traces, raw data, generated
indexes, local env values, DBs, uploads, cookies, tokens, sessions, or external
source were committed.
