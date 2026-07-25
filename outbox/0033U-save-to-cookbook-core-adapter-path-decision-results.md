# 0033U Save-to-Cookbook Core Adapter Path Decision Results

Status: complete, docs-only; Save-to-Cookbook remains prototype-only and
implementation-blocked.

## Decision

Recommended next task: **0033V: prepare a source-owned Vanilla Cookbook
adapter workspace/custom image plan**. The plan should verify source/license
provenance, determine whether a reviewed upstream plugin/API hook is available,
and define a core-owned adapter contract before any real save implementation.

The recommended implementation path is a source-owned or separately forked
Vanilla Cookbook core workspace/custom image. The core app should own
authentication, user ownership, validation, transactions, rollback,
idempotency, and canonical recipe persistence. A verified upstream hook with
the same guarantees remains preferable if available.

## Paths evaluated

- Path A, current external image: retained as the local UI/in-memory prototype
  plus 0033Q disposable write evidence, but not feature-complete Save-to-Cookbook.
- Path B, source-owned/forked core adapter: recommended because it can keep
  ownership and transaction behavior inside the canonical app.
- Path C, upstream plugin/API hook: preferred alternative if primary evidence or
  an accepted upstream change provides stable ownership, dry-run, idempotency,
  and rollback semantics.
- Path D, browser/session automation: rejected as fragile and unsafe due to
  cookies, session state, CSRF, timing, and rollback limitations.
- Path E, direct sidecar DB writes: rejected because they bypass core ownership,
  validation, auth, side effects, and future schema changes.

## Source ownership findings

The repository treats `jt196/vanilla-cookbook:stable` as an external image and
does not contain the editable upstream source tree. Local image inspection
found no useful OCI source/license labels or canonical repository URL. No
external source was fetched, copied, vendored, or committed. Source ownership,
license, and synchronization remain 0033V discovery gates.

## Current status and validation

The 0033T blocker is unchanged: native `POST /api/recipe` requires Lucia
session ownership and has post-create side effects without a safe sidecar
transaction boundary. The route was not called. The 0033S local UI/in-memory
simulation and 0033Q disposable DB/write harness remain intact.

`git diff --check`, repository validation, 396 tests, and Compose configuration
checks passed. No live OpenAI call, production target, auth/session value,
database row, upload, or external artifact was used.

This task does not implement a production save path, native route, migration,
auth bypass, public route, UI production button, direct DB write, browser
automation, AWS, GitHub Actions, Cloudflare, analytics, ads, payment, provider
routing, QMD, or live provider integration.
