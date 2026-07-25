# Core-Owned Dev-Only Synthetic Auth Fixture

Status: complete in the separate core workspace; local verification only.

Date: 2026-07-25

## External fixture

0034C adds a core-process verification command and pure guard tests outside
this sidecar repository:

- Branch: `openclaw/0034C-core-owned-dev-only-synthetic-auth-fixture`
- Commit: `e6172b350375d204aec22371d473e53bad23e24d`
- Script: `scripts/verify-local-auth-commit.mjs`
- Guard helper: `src/lib/server/localAuthFixture.js`
- Image: `local/vanilla-cookbook-adapter:0034c`

No external source, runtime database, upload, cookie, token, session, or
credential was copied into this repository. The image is local-only and was
not pushed or deployed.

## Fail-closed gates

The script exits before database setup unless all of these non-secret values
are present:

```text
NODE_ENV=development
RUN_LOCAL_DEV_AUTH_FIXTURE=1
LOCAL_DEV_AUTH_FIXTURE_APPROVED=1
SYNTHETIC_AUTH_FIXTURE=1
VANILLA_COOKBOOK_IMAGE=local/vanilla-cookbook-adapter:0034c
COOKBOOK_TARGET_URL=http://127.0.0.1:3000/
```

Production mode, exposed targets, AWS, GitHub Actions/CI, Cloudflare Tunnel,
the default external image, and missing approval are rejected. The helper
tests cover disabled-by-default, valid explicit configuration, production,
exposed, CI, and wrong-image refusal. No secret is used as a gate.

## Core-owned sequence

The command creates a temporary schema-backed SQLite database and empty uploads
directory, snapshots both before fixture setup, and creates one synthetic
`AuthUser`. It derives an in-process core user context from that generated
owner ID; it does not create or export a Lucia session, cookie, auth header,
token, browser state, real account, or credential.

It then runs the existing core dry-run mapper before calling the core commit
service with explicit confirmation. The first-scope candidate contains only
bounded synthetic title, description, text servings, deterministic ingredient
lines, numbered directions, safe source metadata, provenance, contract/schema
versions, and an idempotency key. Categories, photos/uploads, remote images,
embeddings, and provider output are excluded.

The command verifies safe UID/owner read-after-write, same-key replay,
same-key changed-payload conflict, duplicate review without another recipe,
foreign-owner rollback, and absence of categories/photos/embeddings. It emits
only phase/status and the opaque generated recipe UID.

Finally it disconnects Prisma, restores the pre-write DB and uploads snapshot,
verifies zero recipes after restoration, reports restore status, and removes
the temporary runtime directory. No repository-local `.local` runtime data is
used by the fixture.

## Verification result

The explicit fixture command completed successfully with dry-run ready,
commit, replay, conflict, duplicate review, rollback, and restore statuses.
Guard tests passed 3/3; the combined adapter/route/commit focused suite passed
23/23. The `0034c` custom image built successfully. Sidecar guarded startup
used the image with only the `cookbook-local` app service; loopback returned
HTTP 200 and the container was stopped.

## Boundary after 0034C

This proves a safe core-process dev fixture, not a sidecar HTTP client or
browser session. The normal sidecar UI remains the 0033S in-memory prototype.
It must not forward identity, call Prisma, capture browser state, or call the
core commit route until a later task separately approves the transport and
sidecar-to-core ownership boundary. Production Save-to-Cookbook remains
unimplemented.

Direct sidecar DB writes, browser/session automation, cookie/token/session
export, auth bypass, and real credentials remain rejected.

## Explicit non-goals

No sidecar UI real-save wiring, production/public route, migration, production
deployment, provider call, AWS, GitHub Actions, Cloudflare, QMD, analytics,
ads, payment, SSO/BYOS, source vendoring, screenshots, traces, raw datasets,
generated indexes, local env values, DBs, uploads, cookies, tokens, sessions,
or browser artifacts were added.
