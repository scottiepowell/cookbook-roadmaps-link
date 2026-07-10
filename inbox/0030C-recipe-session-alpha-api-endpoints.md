# 0030C Recipe Session Alpha API Endpoints

## Goal

Add the first local/offline alpha API endpoints for the recipe-session requirements workflow using the 0030B requirements/session scaffold.

This task should wire the deterministic requirements state, clarification decisions, follow-up classification, RAG refresh decisions, and bounded in-memory session store into API routes that can be tested end-to-end without production storage or live OpenAI.

## Context

`0030A` produced the architecture for recipe-session requirements interaction.

`0030B` implemented the first pure scaffold:

- `ai-api/app/recipe_requirements.py`
- `ai-api/app/recipe_session.py`
- deterministic requirements extraction;
- confidence labels;
- one-question clarification decisions;
- follow-up delta classification;
- RAG refresh decisions;
- bounded in-memory test/demo session store;
- unit tests.

`0030C` should add a thin runtime API layer on top of that scaffold.

## Primary Objective

Add local alpha endpoints for this flow:

```text
POST /ai/recipe-session/start
  -> input quality / requirements extraction
  -> clarify if needed OR generate initial draft through existing importer path
  -> store session state

POST /ai/recipe-session/{interaction_id}/message
  -> classify follow-up
  -> update requirements when meaningful
  -> decide whether RAG should refresh
  -> generate revised draft when appropriate
  -> store revised state

GET /ai/recipe-session/{interaction_id}
  -> return safe current session state

POST /ai/recipe-session/{interaction_id}/finalize
  -> mark ready-to-finalize / finalized-for-demo only
  -> no production write-back
```

Keep this alpha local/offline/mock-friendly.

## Non-Negotiable Boundaries

Do not add:

- production storage;
- database migrations;
- auth;
- paid access;
- public route exposure;
- Cloudflare changes;
- persistent user memory;
- Redis;
- Postgres;
- SQLite persistence for sessions;
- vector database;
- embeddings;
- Qdrant;
- pgvector;
- full chat UI;
- live OpenAI calls during normal validation.

The session store must remain process-local and bounded.

## Suggested Files

Likely new files:

- `ai-api/app/recipe_session_routes.py` or route additions in the existing AI route module
- `ai-api/tests/test_recipe_session_api.py`
- `outbox/0030C-recipe-session-alpha-api-endpoints-results.md`

Likely updated files:

- `ai-api/app/main.py` or route registration module if needed
- `ai-api/app/schemas.py` if shared response schemas belong there
- `ai-api/app/recipe_session.py`
- `ai-api/app/recipe_requirements.py`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md` if relevant
- `README.md` if relevant

## Required Work

### 1. Add alpha API schemas

Add request/response models for the recipe-session API.

Suggested request models:

```text
RecipeSessionStartRequest
RecipeSessionMessageRequest
RecipeSessionFinalizeRequest
```

Suggested response models:

```text
RecipeSessionApiResponse
RecipeSessionStateResponse
RecipeSessionDraftSummary
RecipeSessionRetrievalSummary
RecipeSessionClarificationResponse
```

Responses should expose safe fields only:

- `interaction_id`
- `response_state`
- `requirements`
- `decision`
- `clarification_question`
- `rag_refreshed`
- `rag_refresh_reason`
- `changed_fields`
- `draft` if generated
- `citations` if generated
- `retrieval` if generated
- `support_level` if available
- `revision_count`
- `expires_at`
- `warnings`

Do not expose raw provider prompts, raw provider responses, local absolute dataset paths, `.env` values, API keys, or secret-like values.

### 2. Add `POST /ai/recipe-session/start`

Implement a local alpha start endpoint.

Expected behavior:

1. Accept rough recipe text.
2. Run existing input quality logic if reusable.
3. Extract deterministic requirements through the 0030B scaffold.
4. Decide whether clarification is needed.
5. Create a session in the bounded in-memory session store.
6. If clarification is needed, return `response_state=clarification_needed` with one bounded question and no provider call.
7. If input is rejected, return `response_state=rejected` safely.
8. If input is specific enough, generate an initial draft using the existing importer/RAG pipeline when practical.

Use the existing importer path rather than duplicating provider/RAG logic.

If directly calling the importer helper is not clean, add a small internal service wrapper that both `/ai/import-recipe` and the new session endpoint can use. Do not copy/paste the whole importer implementation.

Tests should use the mock provider only.

### 3. Add `POST /ai/recipe-session/{interaction_id}/message`

Implement a local alpha message endpoint.

Expected behavior:

1. Load the session from the in-memory store.
2. Return safe 404 if not found or expired.
3. Classify the follow-up message using the 0030B classifier.
4. Update requirements when the follow-up contains meaningful requirements.
5. Decide whether RAG should refresh.
6. If RAG refresh is needed, generate a revised draft through the existing importer/RAG path using the updated requirements text.
7. If no material change is needed, return `response_state=no_material_change` without provider call.
8. If the user asks to regenerate without new requirements, return an appropriate state and reuse current requirements/retrieval context where possible.
9. If the user asks to save/finalize, return `response_state=ready_to_finalize` or direct them to finalize.

Required example behaviors:

- Existing baked cheesecake session + `actually make it no-bake` -> update method, refresh RAG, generate revised draft, `response_state=rag_refreshed` or `draft_revised`.
- Existing session + `thanks` -> no RAG refresh, no provider call, `response_state=no_material_change`.
- Existing session + `make it shorter` -> formatting-only, no RAG refresh.
- Existing vague session that asked a clarification + user answer -> treat as clarification answer, update requirements, and generate if specific enough.

### 4. Add `GET /ai/recipe-session/{interaction_id}`

Return the safe current session state.

It should include:

- current requirements;
- confidence label;
- open/resolved questions;
- revision count;
- last retrieval summary;
- last support level;
- last citation IDs;
- expiration;
- current response state if tracked.

It must not include raw provider prompts/responses, local paths, secrets, logs, or env values.

### 5. Add `POST /ai/recipe-session/{interaction_id}/finalize`

Add a demo-safe finalize endpoint.

This should not write to production storage.

Expected behavior:

- if a draft exists, mark the session as `ready_to_finalize` or `finalized_for_demo` depending on existing enum names;
- if no draft exists, return a safe warning or `clarification_needed` / `rejected` style state;
- preserve current requirements and citation summary;
- do not save to the upstream Vanilla Cookbook database unless a future task explicitly scopes that.

### 6. Session response states

Use or extend the 0030B `RecipeSessionResponseState` taxonomy.

Required states:

```text
draft_generated
clarification_needed
rag_refreshed
draft_revised
no_material_change
ready_to_finalize
rejected
not_found
expired
```

Keep state naming stable and documented.

### 7. Integrate with existing importer safely

Where a draft is generated, reuse existing `/ai/import-recipe` behavior as much as possible.

Generated session responses should include the same safe draft/retrieval/citation structures already proven by the 0029B E2E test.

Do not weaken the existing importer endpoint or tests.

Do not run live OpenAI in normal validation.

### 8. Add API tests

Add deterministic FastAPI `TestClient` tests for the new endpoints.

Required tests:

- start with detailed cheesecake notes -> `draft_generated`, session stored, mock provider, retrieval/citations present when fixture dataset is configured;
- start with vague `make dessert` -> `clarification_needed`, one question, no provider call;
- start with unusable input -> `rejected`;
- get existing session -> safe state returned;
- message `actually make it no-bake` after baked cheesecake -> RAG refresh decision true and revised draft or refresh state;
- message `thanks` -> no material change and no RAG refresh;
- message `make it shorter` -> formatting-only/no refresh behavior;
- finalize session with draft -> ready/finalize state with no production write;
- missing/expired session -> safe 404 or response state;
- response serialization does not leak raw prompts, provider responses, env names/values, API keys, local paths, `.tmp-ai-demo`, or stack traces.

Use generated fixture data only. Do not require the real `recipe-dataset/` folder.

### 9. Update E2E or eval coverage if lightweight

If practical, add a small offline/mock E2E test for the session flow:

```text
start baked cheesecake
message actually make it no-bake
get session
finalize
```

Keep it fast enough for `scripts/validate-repo.sh`.

Do not add browser automation or screenshots.

### 10. Update docs and outbox

Update:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md` if relevant
- `docs/ai-live-demo-runbook.md` if relevant
- `README.md` if relevant

Create:

```text
outbox/0030C-recipe-session-alpha-api-endpoints-results.md
```

The outbox should summarize:

- endpoints added;
- how the in-memory store is used;
- how importer/RAG generation is reused;
- response states implemented;
- tests added;
- validation results;
- explicit non-goals;
- confirmation that no production persistence or live calls were added.

## Acceptance Criteria

- Local alpha recipe-session API endpoints exist.
- Start endpoint can create a session and either clarify, reject, or generate a mock/offline draft.
- Message endpoint can classify follow-up input and refresh RAG when requirements materially change.
- Get endpoint returns safe session state.
- Finalize endpoint is demo-safe and does not write to production storage.
- New tests cover start, message, get, finalize, clarification, no-refresh chatter, formatting-only, missing/expired session, and safety serialization.
- Existing `/ai/import-recipe` behavior and tests still pass.
- 0029B RAG E2E tests still pass.
- 0030B unit tests still pass.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No production storage, persistent user memory, auth, paid access, public route exposure, vector DB, embeddings, Redis, Qdrant, pgvector, or full chat UI is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest is run and fails because of the known local `pytest-of-scott` temp ACL issue or because live OpenAI environment variables are set, document that separately and rely on Git Bash validation if it passes.

Before committing, confirm:

- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no raw provider prompts;
- no local absolute paths in public docs examples;
- no production session storage.

## Commit

```bash
git add ai-api docs README.md outbox/0030C-recipe-session-alpha-api-endpoints-results.md

git commit -m "mailbox: complete task 0030C recipe session alpha api endpoints"

git pull --rebase origin main
git push origin main
```
