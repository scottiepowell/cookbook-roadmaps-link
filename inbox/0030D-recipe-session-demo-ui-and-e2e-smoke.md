# 0030D Recipe Session Demo UI And E2E Smoke

## Goal

Add a thin local demo UI workflow and offline smoke coverage for the 0030C recipe-session alpha endpoints.

This task should make the recipe-session flow visible in the existing AI sidecar demo page without turning it into a full chat app, production user feature, public endpoint rollout, or persistent-memory system.

## Context

`0030A` created the recipe-session requirements architecture.

`0030B` added deterministic requirements/session scaffolding:

- requirements state models;
- requirements extraction;
- confidence labels;
- clarification decision rules;
- follow-up delta classification;
- RAG refresh decision logic;
- bounded process-local session store.

`0030C` added local alpha API endpoints:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{interaction_id}/message`
- `GET /ai/recipe-session/{interaction_id}`
- `POST /ai/recipe-session/{interaction_id}/finalize`

`0030D` should add the smallest useful UI layer and smoke coverage for those endpoints.

## Primary Objective

Add a local/offline demo workflow to the existing AI sidecar demo that allows a developer/operator to exercise:

```text
start recipe session
  -> see interpreted requirements
  -> see clarification or generated draft
  -> send follow-up message
  -> see RAG refresh/no-refresh decision
  -> get current session state
  -> finalize for demo
```

The UI should be simple and transparent. It does not need to be a full chat interface.

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
- SQLite session persistence;
- vector DB;
- embeddings;
- Qdrant;
- pgvector;
- full chat UI;
- browser automation screenshots committed to the repo;
- live OpenAI calls during normal validation.

The session store must remain process-local and bounded.

## Suggested Files

Likely updated files:

- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/app/static/demo.css`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_recipe_session_api.py`
- `scripts/demo-ai-mock.ps1`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Optional new file if useful:

- `scripts/test-recipe-session-demo-smoke.ps1`

Required new outbox:

- `outbox/0030D-recipe-session-demo-ui-and-e2e-smoke-results.md`

## Required Work

### 1. Add a Recipe Session section to the existing demo UI

Add a new demo section to the AI sidecar demo page.

Suggested title:

```text
Recipe Session Alpha
```

The section should include:

- a textarea for initial rough recipe notes;
- a `Start session` button;
- a field or textarea for follow-up message;
- a `Send follow-up` button;
- a `Get session` button;
- a `Finalize for demo` button;
- a `Reset session` button.

Keep the UI simple and developer/operator oriented.

Do not add a full chat transcript UI unless it is minimal and clearly alpha-only.

### 2. Display session state clearly

After starting or updating a session, show safe state fields:

- `interaction_id`
- `response_state`
- `revision_count`
- `confidence_label`
- `dish_intent`
- `serving_count`
- `required_ingredients`
- `excluded_ingredients`
- `cooking_method`
- `equipment_constraints`
- `dietary_constraints`
- `open_questions`
- `resolved_questions`
- `rag_refreshed`
- `rag_refresh_reason`
- `changed_fields`
- `support_level`
- `last_citation_ids`
- `expires_at`
- warnings

If a draft is present, render a concise draft summary using the same safe rendering patterns as the importer UI.

If citations are present, render them using the same citation/provenance component already used elsewhere.

### 3. Clarification behavior

When `POST /ai/recipe-session/start` returns `clarification_needed`:

- show the one bounded clarification question;
- do not show a fake draft;
- enable the follow-up field;
- make it clear that the user should answer the question.

Example test case:

```text
make dessert
```

Expected UI behavior:

- response state: `clarification_needed`;
- one question visible;
- no draft shown.

### 4. RAG refresh behavior

When a follow-up materially changes requirements, show the refresh result.

Example flow:

```text
Start: classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight
Follow-up: actually make it no-bake
```

Expected UI behavior:

- response state is `rag_refreshed` or `draft_revised`;
- `rag_refreshed=true` if exposed by API;
- refresh reason visible;
- changed fields visible, such as `cooking_method`;
- revised draft or updated state visible;
- current citations/support information visible if returned.

### 5. No-refresh behavior

When a follow-up does not materially change requirements, show that no RAG refresh happened.

Examples:

```text
thanks
make it shorter
looks good
```

Expected UI behavior:

- response state: `no_material_change` or formatting/no-refresh equivalent;
- `rag_refreshed=false`;
- no new draft is required;
- no provider call should be implied.

### 6. Finalize behavior

When `Finalize for demo` is clicked:

- call `POST /ai/recipe-session/{interaction_id}/finalize`;
- show `ready_to_finalize` or whatever stable state was implemented in 0030C;
- clearly state that this is demo-only and does not write to production storage.

### 7. Loading and reset behavior

For each action:

- disable the relevant button while the request is in flight;
- show a useful loading label;
- restore controls after success or failure;
- show friendly recoverable error cards for failed requests;
- reset should clear local UI state but not require server restart.

### 8. Safety display rules

The UI must not display:

- raw provider prompts;
- raw provider responses;
- API keys;
- authorization headers;
- `.env` contents;
- local absolute dataset paths;
- stack traces;
- secret-like values;
- raw generated cache internals.

Use existing forbidden text checks from `test_demo_ui.py` if available and extend them for the new recipe-session section.

### 9. Update mock demo validation

Update `scripts/demo-ai-mock.ps1` or add a small targeted script so the recipe-session endpoints are exercised during mock demo validation.

Suggested mock flow:

1. Start a detailed cheesecake session.
2. Send follow-up `actually make it no-bake`.
3. Get the session.
4. Finalize for demo.
5. Start vague `make dessert` and confirm clarification.
6. Send `thanks` on a valid session and confirm no refresh.

Keep the script offline and mock-only.

Do not use live OpenAI.

### 10. Add/extend tests

Add or extend deterministic tests for:

- static demo UI contains the Recipe Session Alpha section;
- required controls exist;
- forbidden text is not present in static UI;
- JS rendering handles `draft_generated`;
- JS rendering handles `clarification_needed`;
- JS rendering handles `rag_refreshed` / `draft_revised`;
- JS rendering handles `no_material_change`;
- JS rendering handles `ready_to_finalize`;
- JS rendering handles friendly errors;
- mock demo script exercises the recipe-session endpoint flow;
- existing importer, RAG, and session API tests still pass.

Prefer lightweight tests that can run in `scripts/validate-repo.sh`.

Do not add browser automation unless existing tests already support it without extra runtime risk.

### 11. Update docs

Update:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md` if relevant
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

Docs should state:

- the recipe-session UI is alpha/local/demo-only;
- sessions are process-local and expire;
- finalize is demo-only and does not persist to production storage;
- normal validation is offline/mock-only;
- live OpenAI is not required.

### 12. Create outbox report

Create:

```text
outbox/0030D-recipe-session-demo-ui-and-e2e-smoke-results.md
```

Include:

- UI section added;
- controls added;
- response states displayed;
- clarification behavior;
- RAG refresh behavior;
- no-refresh behavior;
- finalize behavior;
- mock smoke coverage;
- tests added/updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Existing demo UI has a Recipe Session Alpha section.
- A user can start a recipe session from the demo UI.
- A vague request shows one clarification question and no fake draft.
- A detailed request can show a generated draft/state through the existing mock/offline path.
- A material follow-up can show RAG refresh/revised draft behavior.
- Chatter/formatting-only follow-ups show no-refresh behavior.
- Finalize is demo-only and does not write to production storage.
- Static UI/tests verify the new section and safety boundaries.
- Mock demo validation exercises the recipe-session flow.
- Existing `/ai/import-recipe`, RAG E2E, 0030B unit tests, and 0030C API tests still pass.
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
git add ai-api scripts docs README.md outbox/0030D-recipe-session-demo-ui-and-e2e-smoke-results.md

git commit -m "mailbox: complete task 0030D recipe session demo ui smoke"

git pull --rebase origin main
git push origin main
```
