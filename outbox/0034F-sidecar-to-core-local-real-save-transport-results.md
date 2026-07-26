# 0034F Sidecar-to-Core Local Real-Save Transport Results

## Result

Implemented the first guarded sidecar transport to the core-owned local
synthetic verification boundary.

- External branch: `openclaw/0034F-sidecar-to-core-local-real-save-transport`
- External commit: `99641db`
- Core route: `POST /api/adapter/dev-only/recipes/import-candidate/verify-local-commit`
- Local image: `local/vanilla-cookbook-adapter:0034f`
- Sidecar client: `ai-api/app/cookbook_core_transport.py`

The sidecar client is disabled by default and service-only; the normal UI was
not wired to it.

## Core boundary

The external core route uses a dev-only synthetic in-process owner, temporary
schema-backed storage, dry-run-before-commit, core commit logic, safe
read-after-write, replay/conflict/duplicate checks, invalid-owner rollback,
and temporary DB/uploads restore/removal. It does not create a browser
session or export credentials. Its route rejects identity claims in the
candidate/body and returns safe status/UID/verification fields only.

The core focused suite passed 35 tests, including the new route wrapper tests.
The equivalent Prisma generation, service-worker generation, and Vite build
passed. Docker built the distinct `0034f` image locally; the shell command
reached Docker's final image export after the command timeout, and image
inspection confirmed the tag exists. The image was not pushed.

## Sidecar transport

`CoreTransportSettings` requires explicit enablement, approval, runtime
verification, `cookbook-local`, exact `0034f` image marker, and a loopback
HTTP target. The client additionally rejects production, CI, AWS, Cloudflare,
and tunnel indicators before any network call.

It maps only reviewed candidate fields to the core contract, serializing
ingredients as deterministic lines and instructions as deterministic text,
and sends only the candidate plus explicit local approval. It does not send
user IDs, cookies, sessions, tokens, OAuth values, provider grants, or storage
grants. Response handling is allowlisted to safe status/UID/idempotency,
duplicate, rollback, verification, and relative-link fields.

Sidecar tests cover disabled defaults, missing approval, non-loopback and
deployment refusal, safe payload shape, confirmation and identity rejection,
validation errors, network failure, and leakage boundaries.

## Verification limits and next step

No persistent Cookbook UI save was attempted. The core route intentionally
uses temporary fixture storage and synthetic ownership, so its safe UID proof
is not a real authenticated user session. The existing sidecar UI remains the
in-memory prototype. A future task must separately approve a core-owned local
persistent-user/auth transport before wiring a UI control; production save
remains out of scope.

## Validation

- External focused tests: passed, 35 tests.
- External build: passed with Prisma generation and Vite warnings only.
- Custom image: local `0034f` tag confirmed; not pushed.
- Sidecar pytest: 402 passed.
- Repository validation: shell syntax, Docker Compose, repository tests, and
  offline evals passed; `git diff --check` passed.
- Sidecar Compose configuration and `cookbook-local` Compose configuration
  both passed.
- Local image startup via `start-vanilla-cookbook-local.ps1 -CookbookImage
  local/vanilla-cookbook-adapter:0034f`: container/port checks passed and HTTP
  200 was confirmed after startup; the container was stopped afterward.
- No live OpenAI, Google, Microsoft, OAuth, storage, or other provider call.

## Explicit non-goals

No production Save-to-Cookbook, public route, normal UI real-save wiring,
native persistent write, migration, direct sidecar DB write, auth/session
export, browser automation, production deployment, Cloudflare/AWS/GitHub
Actions work, provider routing, QMD, analytics, ads, payment, or external
source vendoring was added.
