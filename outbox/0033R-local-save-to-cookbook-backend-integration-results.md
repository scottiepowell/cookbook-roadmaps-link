# 0033R Local Save-to-Cookbook Backend Integration Results

Status: complete, local-only and disabled by default.

## Native boundary review

The local upstream source exposes an authenticated `POST /api/recipe` path,
but its auth/session ownership and possible upload/embedding side effects are
not a safe sidecar contract. It was not called. No production or exposed data
was inspected. Native core-owned adapter integration remains future work.

## Implementation

Added `ai-api/app/cookbook_import_commit.py` and focused tests. The service is
not a route and requires explicit enablement, approval, runtime verification,
the exact `cookbook-local` Compose project, loopback HTTP, and synthetic local
ownership. It uses an injected in-memory store so normal tests cannot touch
SQLite, uploads, the upstream app, or a provider.

The schema-informed mapping uses the reviewed candidate's name, description,
string servings, deterministic newline ingredients, numbered directions, safe
source/source URL, and bounded notes. Categories, media/uploads, and
embeddings are excluded.

The service returns only safe status envelopes with versions, opaque local IDs,
warnings, and field/guard errors. It prevents same-key replay conflicts and
unbounded duplicates. Failure-injection tests verify the in-memory store rolls
back after a simulated transaction failure.

## Validation and boundaries

- Focused backend integration tests: 6 passed.
- Existing fixture and dry-run tests remain covered by the repository suite.
- Disabled-by-default behavior refuses before any store write.
- No Docker or live OpenAI call is required for normal tests.
- No product button, public route, production commit endpoint, native API
  write, migration, auth integration, or production write-back was added.

The 0033Q readiness harness remains the approved path for disposable DB/
uploads backup, local runtime verification, and restoration. This service does
not replace those guards and should not be connected to an upstream store
without a separately reviewed native ownership/API decision.
