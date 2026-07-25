# Source-Owned Vanilla Cookbook Adapter Workspace Plan

Status: planning only; no upstream source, image, adapter, route, or save
implementation is added by this plan.

Date: 2026-07-25

## Current status

Save-to-Cookbook is prototype-only. The repository contains the 0033S
sidecar UI/in-memory simulation and the 0033Q disposable local database
readiness harness. Neither is a production save path, and the sidecar does
not own Vanilla Cookbook recipe persistence.

The 0033T native spike confirmed that the external image's native recipe route
requires core-app Lucia session ownership. The sidecar cannot safely create or
forward a user session, cookie, or token. Direct sidecar database writes and
browser/session automation therefore remain rejected. A real feature requires
either a source-owned core adapter or a reviewed upstream API/plugin hook.

## Provenance and license gates

Observed locally:

- `docker-compose.yml` and `docker-compose.local.yml` use the external
  `jt196/vanilla-cookbook:stable` image.
- This repository has no editable Vanilla Cookbook source tree, source
  checkout, fork metadata, or committed license record for that image.
- Local image inspection found no useful OCI source or license labels. No
  image source snapshot, database, upload, or external archive was copied.

Web-current provenance lead, not a local ownership fact:

- The public [Vanilla Cookbook GitHub repository](https://github.com/jt196/vanilla-cookbook)
  is the likely upstream source identified by the project's public
  [installation documentation](https://vanilla-cookbook.readthedocs.io/en/stable/manual/installation/).
  That documentation describes cloning with a recursive submodule and using
  the `jt196/vanilla-cookbook` Docker image.
- The applicable GPL-3.0 license must be reviewed directly from the upstream
  [LICENCE file](https://github.com/jt196/vanilla-cookbook/blob/main/LICENCE)
  before a fork, source checkout, or redistributed custom image is created.
  This task records the local review result but does not grant permission for
  redistribution of unreviewed dependencies.

Required gates before source ownership:

1. Record the exact upstream commit/tag and image build relationship.
2. Review the license, submodule licenses, redistribution terms, and any
   required notices.
3. Choose a source owner and repository boundary; do not put external app
   source into this sidecar repository without a separate approval.
4. Define upstream sync, security patch, and local patch ownership.
5. Record whether an upstream-supported adapter/plugin API is available before
   accepting fork maintenance.

## Workspace options

| Option | Assessment | Decision |
| --- | --- | --- |
| Separate fork/source checkout repository | Best ownership and isolation; supports custom image, core tests, auth/session ownership, and transaction work. Requires license and sync discipline. | Recommended default |
| Git submodule or subtree here | Keeps one top-level checkout but imports external source topology, license obligations, and update friction into the sidecar repo. | Do not choose without a separate monorepo decision |
| Remain external-image-only | Lowest maintenance and preserves current local workflow. Supports only the 0033S simulation and 0033Q evidence, not a real saved recipe. | Prototype fallback only |
| Upstream plugin/API contribution | Best long-term sync if upstream accepts a narrow authenticated adapter contract with stable versioning and rollback semantics. Availability is not yet verified. | Preferred alternative if confirmed |
| Custom local image from a reviewed external checkout | Good local isolation and reproducible testing, but still requires a source owner, license review, patch policy, and separate source workspace. | Use as the build output of the recommended option |

## Recommended workspace strategy

Use a separate source-owned or forked Vanilla Cookbook repository/workspace,
outside this sidecar repository, and build a separately tagged local custom
image from a reviewed commit. Keep this repository responsible for the AI
candidate contract, dry-run behavior, local product integration, and
documentation. Keep the core repository responsible for authenticated user
ownership, recipe validation, persistence, transaction boundaries, and
canonical recipe URLs.

The source-owned workspace is now bootstrapped outside this repo by 0033W.
The next task should maintain the workspace location, license record, exact
upstream pin, patch queue, and image build without adding the checkout here.

## Core-owned adapter contract

The future core app adapter should be an authenticated core-app service or
internal API. It must derive the current user from the core app session and
must never accept a sidecar-provided `userId`, cookie, token, or session claim.

Minimum contract:

- versioned reviewed candidate input;
- dry-run validation with no mutation;
- explicit user confirmation before commit;
- transactional recipe creation and related-record cleanup;
- idempotency key and candidate fingerprint handling;
- duplicate detection with a bounded, safe response;
- canonical recipe UID and URL on success;
- field-level validation and safe error codes;
- no raw prompts, provider bodies, secrets, or provider output stored as
  canonical recipe content;
- controlled rollback for future categories, photos/uploads, and embeddings.

First implementation scope:

- name/title, description, and invariant servings text;
- deterministic plain-text ingredients;
- deterministic numbered directions;
- safe fixture source and bounded provenance note;
- no categories, media/uploads, remote image fetches, or embeddings unless
  explicitly disabled or controlled by the core app;
- one synthetic local user and one reviewed synthetic candidate per test.

## Future custom image and local workflow

The bootstrapped source-owned workspace and future adapter work should:

1. Check out or fork the reviewed upstream source at a pinned commit outside
   this repository.
2. Add the smallest core-owned adapter and tests in that workspace, preserving
   the application's auth, validation, transaction, and rollback boundaries.
3. Build a local-only image with a distinct name/tag. Do not retag or mutate
   `jt196/vanilla-cookbook:stable`.
4. Add an explicitly documented, local-only compose override or parameter so
   `docker-compose.local.yml` can select the custom image while retaining
   `127.0.0.1:3000:3000`.
5. Start only the app service under the `cookbook-local` project. Never start
   `cloudflared`; no AWS, GitHub Actions, tunnel, or production secret is
   needed for local validation.
6. Run migrations only against a disposable local database after a separate
   migration review. No migration belongs in 0033V.
7. Keep `.local/vanilla-cookbook/db` and `.local/vanilla-cookbook/uploads`
   ignored. Back up and restore these paths around synthetic write tests.
8. Run core-app unit/adapter tests, then this repository's existing offline
   sidecar tests and mock demo. Docker-dependent checks remain optional and
   local-only.

The local two-terminal workflow remains:

```powershell
# Terminal 1: source-owned local core image (opt-in)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 `
  -CookbookImage local/vanilla-cookbook-adapter:0033w

# Terminal 2: sidecar, offline by default
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

The current external image path remains the default fallback. Production/exposed
Cookbook behavior is separate and is not changed by this plan.

## Testing, security, and rollback boundaries

Before a real local adapter is wired to the 0033S UI, the source-owned core
workspace must demonstrate:

- synthetic user creation without reading or importing existing users;
- authenticated ownership derived inside the core app;
- dry-run and commit separation;
- exact candidate serialization and required-field validation;
- duplicate/idempotency replay and conflict behavior;
- transaction rollback for recipe and any related records;
- backup/restore of disposable DB/uploads;
- safe read-after-write verification using opaque IDs/statuses only;
- no media, remote image fetch, or embedding side effects in the first scope;
- no cookies, tokens, prompts, provider bodies, private rows, or absolute
  machine paths in logs or responses.

The 0033Q harness remains the approved disposable evidence boundary. A future
core adapter test may use it, but it must not weaken its loopback, approval,
backup, synthetic-data, and cleanup guards.

## Next implementation task

Recommend **0033X: implement the core-owned local dry-run adapter in the
separate source workspace**. 0033W completed provenance/license review,
recursive checkout, pinning, and the app-only local image bootstrap. 0033X
should implement only authenticated dry-run mapping, validation, idempotency,
and core tests, stopping before production write-back or exposed deployment
integration.

If the upstream project confirms an equivalent supported plugin/API hook before
0033W begins, the task may choose that route instead of maintaining a fork,
subject to the same ownership, idempotency, transaction, and rollback gates.

## Explicit non-goals

This plan does not vendor or copy external source, create a fork, build an
image, change Compose, add a route, add a save adapter, mutate a database,
create a migration, handle auth/session values, add a UI production button,
write to production, inspect production data, or add AWS, Cloudflare,
GitHub Actions, payment, analytics, ads, QMD, provider, or public-infrastructure
work.
