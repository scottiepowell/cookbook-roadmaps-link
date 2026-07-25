# 0033V Source-Owned Vanilla Cookbook Adapter Workspace Plan Results

Status: complete; discovery and planning only.

## Summary

Created `docs/source-owned-vanilla-cookbook-adapter-workspace-plan.md` and
updated the Save-to-Cookbook status/backlog/product integration documentation.
The current feature remains prototype-only: 0033S provides the local
sidecar/in-memory simulation and 0033Q provides disposable write/restore
evidence. No normal product flow saves a recipe in Vanilla Cookbook.

## Provenance findings

- The repository uses external `jt196/vanilla-cookbook:stable` and contains no
  editable upstream source.
- Local image metadata had no useful OCI source/license labels.
- Public project documentation identifies the likely upstream GitHub source
  and Docker image workflow, but this task did not download, copy, vendor, or
  commit source.
- The applicable license and submodule licenses remain a gate for the next
  workspace task; no license type is asserted here.

## Decision

Evaluated a separate fork/source checkout, submodule/subtree, remaining
image-only, upstream plugin/API, and custom-image options. Recommended a
separate source-owned/forked workspace with a distinct local custom image,
while preferring a verified upstream plugin/API hook if it provides equivalent
core ownership, validation, idempotency, transaction, and rollback guarantees.

Browser/session automation and direct sidecar database writes remain rejected.

## Planned core adapter and image boundaries

The future core adapter must derive ownership from core authentication, accept a
reviewed candidate, support no-write dry-run and explicit commit, enforce
idempotency/duplicate behavior, transact canonical recipe persistence, return a
safe canonical UID/URL, and keep provider prompts/bodies out of recipe data.
The first scope excludes categories, media/uploads, remote image fetches, and
embeddings unless separately controlled.

The future custom image will be built from a pinned reviewed source checkout
outside this repository, run app-only under `cookbook-local`, bind only to
loopback, retain ignored `.local/vanilla-cookbook` runtime paths, and never
require Cloudflare, AWS, GitHub Actions, production secrets, or exposed URLs.

## Next task and validation

The next concrete implementation task is **0033W: bootstrap the source-owned
Vanilla Cookbook workspace and custom local image**. It must complete license/
provenance review and stop at the core-owned local adapter/test boundary until
separate production approval exists.

Validation for this docs-only task:

- `git diff --check` passed.
- Repository validation passed.
- Both default and local Compose configurations passed quiet config checks.
- No live OpenAI call was made.

## Explicit non-goals

No source was vendored; no custom image, adapter, route, migration, auth/session
work, UI production button, database mutation, production integration, public
route, deployment work, provider call, cookie, token, local artifact, DB, or
upload was added.
