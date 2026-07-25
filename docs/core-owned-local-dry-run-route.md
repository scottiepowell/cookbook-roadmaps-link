# Core-Owned Local Dry-Run Route

Status: complete in the separate source-owned core workspace; dry-run only.

Date: 2026-07-25

## External implementation

0033Y adds the first authenticated route around the 0033X core-owned,
no-mutation service. The source remains outside this sidecar repository:

- Branch: `openclaw/0033Y-core-owned-local-dry-run-route`
- Commit: `a3d33924795d31e60ad587ac7960cae7ac7dc86d`
- Image: `local/vanilla-cookbook-adapter:0033y`
- Local target: `http://127.0.0.1:3000/`

No external source, source diff, image layer, or runtime data was copied into
this repository. The custom image is local-only and opt-in; the sidecar local
Compose default remains `jt196/vanilla-cookbook:stable`.

## Route and ownership boundary

The core workspace exposes `POST /api/adapter/recipes/import-candidate/dry-run`.
The route calls the normal core `requireAuth(locals)` helper before processing
the request. Anonymous access is rejected by the existing core authentication
boundary. Ownership comes from the authenticated core user context; request
fields such as `userId`, `owner`, `session`, `cookie`, `token`, and `auth` are
rejected rather than accepted as assertions. No credentials are created,
printed, or stored by this task.

The route delegates to the pure 0033X service and keeps the route free of
Prisma, filesystem, uploads, provider calls, categories, image fetching,
embeddings, and migrations. It is part of the opt-in local custom image and
does not change the deployed or exposed application.

## Candidate and response

The first-scope candidate accepts title/name, description, servings,
ingredients, instructions, safe source label/URL, bounded provenance notes,
idempotency key, and contract/schema versions. Mapping remains title/name to
`Recipe.name`, servings to invariant text, ingredients to deterministic
one-item-per-line text, instructions to numbered plain text directions,
validated HTTP(S) source URL to source metadata, and bounded notes to reviewed
provenance. Categories, media/uploads, remote image fetching, and embeddings
remain excluded.

The response is a safe JSON envelope containing status, contract/schema or
adapter versions, mapped recipe preview, field errors, warnings, duplicate
status, idempotency status, opaque fingerprint metadata, and next-action
guidance. It does not contain raw provider bodies, prompts, SQL, stack traces,
absolute paths, secrets, environment values, cookies, tokens, sessions, or
database rows.

## Duplicate and no-mutation behavior

The service computes a deterministic fingerprint from normalized candidate
content, owner scope, and contract version. Same-key same-payload requests are
replay-safe; same-key changed-payload requests return a safe conflict; matching
fixture fingerprints are reviewable duplicate signals. These checks remain
in-memory/dry-run checks and do not query or mutate recipe storage.

Focused external tests pass: 12 tests across the 0033X service and 0033Y
route. Prisma generation, service-worker generation, and the Vite production
build passed. The image built successfully and the sidecar guarded local
scripts started only the `cookbook-local` app service with that image,
observed HTTP 200 on loopback, and stopped it afterward.

## Remaining gap and non-goals

This route is not a commit endpoint. A future task must define and separately
approve a core-owned authenticated commit boundary with explicit confirmation,
transaction/rollback behavior, persisted idempotency, duplicate handling, and
local disposable verification before any recipe mutation is enabled.
Production/exposed Save-to-Cookbook remains unimplemented.

No recipe/database mutation, public production route, migration, auth bypass,
browser/session automation, direct sidecar DB write, provider call, UI
production button, source vendoring, AWS, Cloudflare, GitHub Actions, QMD,
analytics, ads, payment, or SSO/BYOS work was added.
