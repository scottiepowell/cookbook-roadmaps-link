# Save-to-Cookbook Core Adapter Path Decision

Status: architecture decision; no save implementation.

Date: 2026-07-25

## Decision

Choose a source-owned or separately forked Vanilla Cookbook core workspace and
custom local image as the next implementation path. The core app should own a
reviewed adapter/service boundary that accepts a bounded candidate, establishes
authenticated ownership, validates and serializes fields, commits within its
transaction boundary, and returns a canonical recipe identifier. The AI
sidecar remains the draft, dry-run, and candidate producer.

The next concrete task is **0033V: prepare a source-owned Vanilla Cookbook
adapter workspace/custom image plan**. It should establish source ownership,
license/provenance review, a reproducible local image, the core adapter
contract, synthetic local user setup, and a no-production test boundary. It
must not begin production write-back until those gates are separately approved.

Path C remains a preferred implementation variant if the upstream project
offers a reviewed API/plugin hook with equivalent ownership and transaction
semantics. The workspace task should verify that possibility before deciding
whether to fork or contribute upstream.

## Current state and evidence

The current repository runs `jt196/vanilla-cookbook:stable` as an external
image and does not contain the editable Vanilla Cookbook source tree. The local
runtime is useful for schema discovery and the 0033Q disposable harness, but
the image is not a source-owned adapter workspace.

0033T inspected the local route and found:

- `POST /api/recipe` requires `requireAuth(locals)`;
- `locals.user` comes from Lucia-validated session state in the core app;
- anonymous sidecar requests cannot create recipes;
- the route accepts multipart form data and writes the Recipe row before
  optional image/upload processing and background semantic embedding work;
- it has no adapter-specific dry-run or rollback envelope.

The source tree and image metadata inspected locally did not reveal a checked-in
canonical repository URL or license/provenance record that this repository can
safely adopt. No external source was fetched, copied, vendored, or committed.
This is an ownership/provenance unknown for 0033V, not evidence that no upstream
source exists.

The local image has the expected `jt196/vanilla-cookbook:stable` tag but no
useful OCI source/license labels. Repository documentation likewise treats it
as an external image rather than a source-controlled dependency.

## Path evaluation

| Path | Feasibility | Ownership/auth and rollback | Maintenance and future button | Decision |
| --- | --- | --- | --- | --- |
| A. Keep external image; sidecar simulation plus 0033Q | High for demos; no real save | Core ownership remains intact, but sidecar cannot authenticate or commit through the app; 0033Q proves only disposable harness behavior | Lowest maintenance and best current local UX; cannot become feature-complete without a core boundary | Accept as prototype baseline only |
| B. Source-owned/forked core app and custom image | Feasible after source/license review | Core owns auth, user, validation, transaction, rollback, and canonical recipe; sidecar calls a reviewed core adapter | Higher maintenance and source-sync burden; directly supports a real local button and later production path | Recommended next path |
| C. Reviewed upstream API/plugin hook | Potentially best if an official hook exists or is accepted upstream | Core/upstream retains ownership; adapter contract can define auth, validation, idempotency, and rollback | Lowest fork drift, but dependent on upstream availability, review, versioning, and support | Preferred alternative to B if verified |
| D. Browser/session automation | Technically possible but fragile | Requires cookies/session handling, browser state, CSRF/redirect assumptions, and cannot guarantee atomic rollback | High operational/test burden; poor production reliability and difficult error/idempotency semantics | Reject |
| E. Direct sidecar DB writes | Technically possible against local SQLite but unsafe | Bypasses Lucia ownership, core validation, route side effects, transaction policy, and future schema changes | Appears simple but creates split-brain ownership and migration risk; cannot be approved for production | Reject permanently |

### Path A: external image

This is the current `0033S` state: the demo reviews a draft, runs the
disabled-by-default sidecar dry-run, and exercises an in-memory local commit
simulation. The `0033Q` script separately proves a synthetic disposable DB
write/restore boundary. It preserves Vanilla Cookbook as canonical owner but
does not make a recipe appear through the normal app. It is suitable for demos
and contract tests, not a completed Save-to-Cookbook feature.

### Path B: source-owned/forked core adapter

The core app should receive a narrow service or internal endpoint, for example
`POST /api/adapter/recipes/import-candidate`, with a versioned candidate,
explicit user confirmation, idempotency key, dry-run mode, and commit mode. The
core app—not the sidecar—should derive ownership from its authenticated
context, perform schema mapping, exclude media in the first scope, and commit
Recipe plus any related records atomically. The sidecar should never receive or
manage the core session cookie.

This path requires a separate source/license review, source synchronization
policy, local custom image, synthetic user fixture, transaction/rollback tests,
duplicate behavior, and production approval gates. It moves only the
ownership-sensitive adapter into the core app; RAG, provider controls, draft
generation, and dry-run candidate production remain in the sidecar.

### Path C: upstream-supported API/plugin

An official API or plugin hook is preferable if it provides authenticated
ownership without sharing cookies, a stable schema/version contract, dry-run or
validation, idempotency, and a transaction/error boundary. The project must
verify those capabilities from primary upstream documentation or an accepted
upstream change. A generic existing create form is not enough: 0033T showed
that the current route has auth and post-create side effects but no reviewed
adapter boundary.

### Paths D and E

Browser automation would turn a core ownership problem into brittle session and
CSRF handling. It would also make read-after-write, retries, duplicate
protection, and rollback dependent on UI timing. Direct DB writes would bypass
the canonical app entirely. Neither path should be used to ship the feature.

## Required 0033V deliverables

Before implementation, the next task should produce:

1. source repository/fork location, license/provenance evidence, and a policy
   for syncing upstream changes;
2. a reproducible local custom image that is separate from production and does
   not require production secrets;
3. a core-owned adapter contract for draft, dry-run, confirmation, commit,
   canonical ID, duplicate/idempotency, and safe errors;
4. a synthetic local user/ownership fixture that does not expose cookies,
   tokens, or session values to the sidecar;
5. transaction and rollback behavior covering Recipe and any related records;
6. first-write exclusions for categories, media/uploads, remote image fetches,
   and embeddings unless explicitly proven safe;
7. local-only tests and a backup/restore harness that retains the 0033Q
   evidence boundary;
8. a go/no-go review before wiring the 0033S UI to a real core commit.

## Status and non-goals

Save-to-Cookbook is currently prototype-only: the sidecar UI/in-memory service
and disposable 0033Q harness exist, but a normal Vanilla Cookbook recipe is
not saved by the product flow. Vanilla Cookbook remains the canonical owner.
Direct sidecar DB writes, browser/session automation, production save,
production routes, migrations, auth bypasses, AWS/platform work, provider
changes, QMD, payment, analytics, ads, and live calls are not implemented or
approved by this decision.
