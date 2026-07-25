# 0033Y Core-Owned Local Dry-Run Route Results

Date: 2026-07-25

0033Y completed the first authenticated, core-owned no-mutation dry-run route
in the separate Vanilla Cookbook workspace. External source was not copied or
committed into this sidecar repository.

- External branch: `openclaw/0033Y-core-owned-local-dry-run-route`
- External commit: `a3d33924795d31e60ad587ac7960cae7ac7dc86d`
- Route: `POST /api/adapter/recipes/import-candidate/dry-run`
- Local image: `local/vanilla-cookbook-adapter:0033y`

The route uses the normal core `requireAuth(locals)` boundary and rejects
anonymous requests. Ownership is derived from authenticated core context;
sidecar-supplied identity fields are rejected. It delegates to the 0033X pure
service and performs no Prisma, SQLite, upload, category, media, embedding,
filesystem, provider, or recipe mutation.

The existing safe envelope and schema-informed mapping are preserved: field
errors, warnings, duplicate status, idempotency state, contract/schema
metadata, text servings, deterministic ingredient/direction text, validated
safe source URL, bounded provenance, and no categories/media/embeddings. Same
key replay is safe, changed-payload key reuse is a conflict, and duplicate
signals remain review-only.

External focused Vitest passed 12/12 tests across service and route. Prisma
generation, service-worker generation, and the Vite production build passed.
The new image built successfully. Guarded sidecar scripts started
`cookbook-local` with that image; only the app service ran,
`http://127.0.0.1:3000/` returned HTTP 200, and the container was stopped.
No production or exposed target was contacted and no live provider call was
made.

The dry-run route is complete, but Save-to-Cookbook remains prototype-only
outside the core workspace. A future task must separately approve a core-owned
authenticated commit boundary with confirmation, transaction/rollback,
persisted idempotency, duplicate handling, and local disposable verification.
No commit/save endpoint exists.

Sidecar changes: added [Core-Owned Local Dry-Run Route](../docs/core-owned-local-dry-run-route.md)
and updated the related core adapter, integration, status, backlog, roadmap,
and README documentation. No sidecar code or route was added.

Explicit non-goals: no production save, public production route, commit
endpoint, database/upload mutation, migration, auth bypass, cookie/session
handling, browser automation, direct sidecar DB write, deployment work, AWS,
Cloudflare, GitHub Actions, QMD, analytics, ads, payment, SSO/BYOS, provider
routing, or live call. No prompts, provider outputs, secrets, screenshots,
traces, datasets, generated indexes, local env values, DBs, uploads, cookies,
tokens, sessions, or external source were committed.
