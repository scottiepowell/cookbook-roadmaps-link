# 0030E Recipe Session Eval Harness And Regression Baseline

## Goal

Add an offline/mock evaluation harness and regression baseline for the 0030 recipe-session alpha workflow.

This task should turn the session behavior from 0030C/0030D into repeatable eval cases that run with the existing offline eval pipeline, without adding production storage, persistent memory, live OpenAI calls, full chat UI, or public access.

## Context

`0030A` designed the recipe-session requirements architecture.

`0030B` added deterministic requirements/session scaffolding.

`0030C` added local alpha API endpoints:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{interaction_id}/message`
- `GET /ai/recipe-session/{interaction_id}`
- `POST /ai/recipe-session/{interaction_id}/finalize`

`0030D` added a local `Recipe Session Alpha` demo UI panel and mock smoke coverage.

`0030E` should add a dedicated eval harness so session behavior is tracked as a regression surface alongside the existing 28 offline eval cases.

## Primary Objective

Create offline session eval cases that verify:

```text
start session
  -> requirements extraction
  -> clarification or draft generation
  -> follow-up classification
  -> RAG refresh decision
  -> revised draft when material requirements change
  -> no-refresh behavior for chatter/formatting
  -> safe get/finalize behavior
  -> no prompt/secret/path leakage
```

The eval harness must be deterministic, fast, offline, and mock-only.

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
- browser automation;
- screenshots;
- live OpenAI calls during normal validation.

Use generated fixture data only.

Do not require the real `recipe-dataset/` folder.

## Suggested Files

Likely new files:

- `evals/ai_cookbook/session_cases.yaml`
- `evals/ai_cookbook/session_eval.py`
- `ai-api/tests/test_recipe_session_eval_harness.py`
- `outbox/0030E-recipe-session-eval-harness-and-regression-baseline-results.md`

Likely updated files:

- `evals/ai_cookbook/run_evals.py`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `docs/recipe-session-requirements-architecture.md`
- `README.md` if relevant

## Required Work

### 1. Add session eval cases

Create a small deterministic eval case file, suggested path:

```text
evals/ai_cookbook/session_cases.yaml
```

Include cases for these flows at minimum:

#### Case A: detailed start generates draft

Input:

```text
classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight
```

Expected:

- `response_state=draft_generated`
- `confidence_label=high` or acceptable high/specific label
- draft exists
- citations exist when fixture dataset is configured
- support level is not `none`
- no clarification question

#### Case B: vague start asks clarification

Input:

```text
make dessert
```

Expected:

- `response_state=clarification_needed`
- one bounded clarification question exists
- no draft exists
- no provider call should be implied

#### Case C: material method change refreshes RAG

Flow:

```text
start: classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight
message: actually make it no-bake
```

Expected:

- response state is `rag_refreshed` or `draft_revised`
- `rag_refreshed=true` when exposed
- changed fields include `cooking_method` or method-equivalent field
- revised draft exists
- current requirements include no-bake method

#### Case D: chatter does not refresh

Flow:

```text
start: carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream
message: thanks
```

Expected:

- `response_state=no_material_change`
- `rag_refreshed=false`
- no changed retrieval-affecting fields
- no new draft required

#### Case E: formatting-only does not refresh

Flow:

```text
start: omelette for 4 with eggs cheddar onions butter folded in a skillet
message: make it shorter
```

Expected:

- formatting/no-refresh classification
- `rag_refreshed=false`
- response state is `no_material_change` or documented equivalent

#### Case F: clarification answer generates draft

Flow:

```text
start: make dessert
message: cheesecake, no-bake, for 4 people
```

Expected:

- start returns `clarification_needed`
- follow-up is classified as clarification answer or relevant requirement update
- final response generates a draft or reaches a ready state with no-bake cheesecake requirements
- no fake draft is emitted before clarification answer

#### Case G: finalize is demo-only

Flow:

```text
start: chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly
finalize
```

Expected:

- finalize state is `ready_to_finalize` or documented stable finalize state
- no production write-back fields are exposed
- no storage path is exposed

#### Case H: safe missing session behavior

Input:

```text
GET or message unknown interaction_id
```

Expected:

- safe `not_found` or 404 response
- no stack trace
- no local path
- no secret leakage

### 2. Add session eval runner

Create:

```text
evals/ai_cookbook/session_eval.py
```

The runner should:

- use FastAPI `TestClient` or an existing offline test pattern;
- force mock provider settings;
- use generated fixture dataset only;
- clear/reset the process-local recipe session store between cases;
- clear/reset retrieval cache where appropriate;
- execute start/message/get/finalize flows;
- collect pass/fail results with readable case IDs;
- include elapsed time per case;
- fail clearly when expected state, refresh behavior, citations, or safety boundaries regress.

Do not use browser automation.

Do not start a live server if TestClient is enough.

### 3. Integrate with existing eval runner

Update:

```text
evals/ai_cookbook/run_evals.py
```

Add a new eval group, suggested name:

```text
recipe_session
```

The normal eval output should include lines such as:

```text
EVAL: starting recipe_session: vague_dessert_clarifies
PASS: vague_dessert_clarifies
EVAL: starting recipe_session: no_bake_refreshes_rag
PASS: no_bake_refreshes_rag
```

The final summary should include the new cases in the total pass/fail count.

Keep evals fast. The new session evals should not make `run_evals.py` slow or flaky.

### 4. Add safety checks

Each eval response should be checked for forbidden content, including:

- `OPENAI_API_KEY`
- `sk-`
- `Authorization`
- `.env`
- `.tmp-ai-demo`
- raw provider prompt text
- raw provider response text
- stack trace text
- local absolute Windows paths
- local absolute Unix paths
- generated dataset directory path
- production storage write indicators

### 5. Add tests for the eval harness

Add:

```text
ai-api/tests/test_recipe_session_eval_harness.py
```

Test that:

- session case fixture loads;
- all required case IDs exist;
- eval runner returns all pass on the generated fixture data;
- failure messages include the case ID and expected state when a synthetic failure is introduced or mocked if practical;
- no live provider settings are required.

Keep this test deterministic and offline.

### 6. Update docs

Update:

- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `docs/recipe-session-requirements-architecture.md`
- `README.md` if relevant

Docs should state:

- recipe-session behavior now has an offline eval baseline;
- session evals cover clarification, RAG refresh, no-refresh, finalize, and safety boundaries;
- evals use generated fixture data and mock provider;
- no live OpenAI is required.

### 7. Create outbox report

Create:

```text
outbox/0030E-recipe-session-eval-harness-and-regression-baseline-results.md
```

Include:

- eval case file added;
- eval runner added;
- run_evals integration;
- cases covered;
- safety checks;
- tests added;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- Dedicated recipe-session eval cases exist.
- Session eval runner executes start/message/get/finalize flows offline.
- `run_evals.py` includes the new recipe-session eval group.
- Evals cover draft generation, clarification, material RAG refresh, chatter no-refresh, formatting no-refresh, clarification answer, finalize, and missing session safety.
- Evals check for prompt/secret/path leakage.
- Generated fixture data only; no real dataset required.
- Mock provider only; no live OpenAI required.
- New eval harness tests pass.
- Existing importer, RAG, session API, demo UI, and 0030B/0030C/0030D tests still pass.
- Normal validation remains offline/mock-only.
- No production storage, persistent user memory, auth, paid access, public route exposure, vector DB, embeddings, Redis, Qdrant, pgvector, browser automation, screenshots, or full chat UI is added.

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
git add ai-api evals docs README.md outbox/0030E-recipe-session-eval-harness-and-regression-baseline-results.md

git commit -m "mailbox: complete task 0030E recipe session eval harness"

git pull --rebase origin main
git push origin main
```
