# 0030C Recipe Session Alpha API Endpoints Results

## Summary

Implemented local/offline alpha recipe-session API endpoints on top of the 0030B deterministic requirements scaffold.

These endpoints are local alpha workflow endpoints only. They do not add production storage, auth, paid access, public route exposure, persistent user memory, Redis, Postgres, SQLite session persistence, vector databases, embeddings, Qdrant, pgvector, a full chat UI, or live OpenAI calls.

## Endpoints Added

Added `ai-api/app/recipe_session_routes.py` and wired it into `ai-api/app/main.py`.

Endpoints:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{interaction_id}/message`
- `GET /ai/recipe-session/{interaction_id}`
- `POST /ai/recipe-session/{interaction_id}/finalize`

## In-Memory Store Use

The endpoints use the bounded process-local `default_recipe_session_store` from `ai-api/app/recipe_session.py`.

The store holds only alpha demo/test state:

- requirements state;
- response state;
- current generated draft;
- safe citations and retrieval metadata;
- warnings;
- revision count;
- expiration timestamp.

It does not write sessions to disk, SQLite, Postgres, Redis, or the Vanilla Cookbook database.

## Importer/RAG Reuse

Draft generation goes through the existing `import_recipe_text` path. The session endpoint does not duplicate importer, provider, retrieval, context-packing, support-policy, citation, or schema-validation logic.

Clarification and rejected paths avoid provider generation. Specific enough start requests and material follow-up changes can generate drafts through the existing mock/offline importer path.

## Response States Implemented

The alpha API uses the 0030A/0030B taxonomy:

- `draft_generated`
- `clarification_needed`
- `rag_refreshed`
- `draft_revised`
- `no_material_change`
- `ready_to_finalize`
- `rejected`
- `not_found`
- `expired`

Missing or expired sessions return a safe 404 with `response_state=not_found`.

## Tests Added

Added `ai-api/tests/test_recipe_session_api.py`.

Tests cover:

- detailed cheesecake start -> `draft_generated`;
- vague `make dessert` start -> `clarification_needed`, one question, no draft;
- unusable input -> `rejected`;
- get existing session;
- baked cheesecake follow-up `actually make it no-bake` -> RAG refresh and revised draft;
- `thanks` -> no material change and no RAG refresh;
- `make it shorter` -> formatting-only no-refresh behavior;
- clarification answer -> updated requirements and generated draft;
- finalize with draft -> `ready_to_finalize` with no production write;
- missing and expired sessions -> safe 404;
- offline start-message-get-finalize flow;
- response serialization safety.

Fixtures use generated local CSV data only and the mock provider.

## Documentation Updates

Updated:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`

## Validation Results

- Direct focused Windows pytest initially hit the known local `pytest-of-scott` temp ACL issue before the new API tests could execute. A direct TestClient smoke script was used to confirm the start -> message -> get -> finalize flow while debugging.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 28 offline cases.
- Git Bash `scripts/validate-repo.sh`: passed, including 210 AI API tests, 28 offline eval cases, Docker Compose config, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed with line-ending warnings only.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed, including offline evals and direct endpoint smoke checks.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live opt-in settings were not present.

No live OpenAI calls were run during normal validation.

## Explicit Non-Goals

This task did not add:

- production storage;
- database migrations;
- authentication;
- paid access;
- public route exposure;
- Cloudflare changes;
- persistent user memory;
- Redis;
- Postgres;
- SQLite session persistence;
- vector databases;
- embeddings;
- Qdrant;
- pgvector;
- full chat UI;
- live OpenAI calls.

## Artifact Safety Confirmation

Before commit, confirm:

- no raw dataset files are staged;
- no `.tmp-ai-demo` artifacts are staged;
- no generated persistent index files or disk cache files are staged;
- no `.env` files are staged;
- no screenshots or logs are staged;
- no credentials are staged;
- no raw provider prompts are included;
- no local absolute paths appear in public docs examples;
- no production session storage is added.

Confirmed during pre-commit status, staged-file, and docs checks.
