# 0030B Recipe Session Requirements Alpha Scaffold

## Goal

Implement the first narrow runtime scaffold for the 0030 recipe-session requirements layer described in `docs/recipe-session-requirements-architecture.md`.

This task should add deterministic, offline, mock-friendly building blocks for session-scoped recipe requirements without adding production storage, auth, paid access, public route exposure, persistent user memory, vector search, embeddings, or a full chat UI.

## Background

`0030A` completed the architecture/design layer for recipe-session requirements interaction.

The completed 0029B pipeline already provides:

- input quality checks;
- deterministic dataset retrieval;
- dataset normalization;
- bounded RAG context packing;
- RAG support classification;
- citations/provenance;
- process-local retrieval cache;
- offline/mock E2E validation through `/ai/import-recipe`.

`0030B` should begin implementation by adding pure, well-tested state/policy/service code that can support future endpoints in `0030C` or later.

## Scope

Implement alpha scaffolding for:

1. recipe requirements state models;
2. deterministic requirements extraction from a single user message;
3. clarification decision rules;
4. follow-up/delta classification rules;
5. RAG refresh decision rules;
6. session-scoped in-memory state store for tests/demo only;
7. unit tests and documentation.

This task may add a lightweight internal service module, but should not expose public runtime routes unless a very small private/test-only route already exists and is clearly appropriate. Prefer pure functions and unit tests for this slice.

## Suggested Files

Likely new files:

- `ai-api/app/recipe_requirements.py`
- `ai-api/app/recipe_session.py`
- `ai-api/tests/test_recipe_requirements.py`
- `ai-api/tests/test_recipe_session.py`
- `outbox/0030B-recipe-session-requirements-alpha-scaffold-results.md`

Likely updated files:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `README.md` if relevant

## Required Work

### 1. Add requirements state models

Add Pydantic models or dataclasses for session-scoped recipe requirements.

Suggested model names:

- `RecipeRequirementSource`
- `RecipeRequirementField`
- `RecipeRequirementsState`
- `RecipeSessionState`
- `RecipeSessionDecision`
- `RecipeSessionResponseState`

The state should support fields from the 0030A architecture:

- `interaction_id`
- `original_user_text`
- `latest_user_text`
- `dish_intent`
- `serving_count`
- `required_ingredients`
- `optional_ingredients`
- `excluded_ingredients`
- `cooking_method`
- `equipment_constraints`
- `time_constraints`
- `dietary_constraints`
- `texture_or_style_goals`
- `assumptions`
- `requirement_sources`
- `confidence_label`
- `open_questions`
- `resolved_questions`
- `revision_count`
- `last_retrieval_summary`
- `last_retrieval_cache_key`
- `last_support_level`
- `last_citation_ids`
- `created_at`
- `updated_at`
- `expires_at`

Keep defaults safe and deterministic.

Do not include raw provider prompts, raw provider responses, API keys, env values, local absolute paths, or long-term memory fields.

### 2. Add deterministic requirements extraction

Implement a conservative extractor that can parse obvious information from rough recipe notes.

It should identify, when present:

- dish intent, such as cheesecake, carbonara, omelet, chicken and rice casserole;
- serving count, such as `for 4`, `serves 6`, `4 servings`;
- required ingredients from known recipe-like tokens;
- excluded ingredients from phrases like `no heavy cream`, `without nuts`, `omit onions`;
- cooking method from terms like baked, no-bake, stovetop, skillet, slow cooker, air fryer;
- equipment constraints from terms like oven, skillet, instant pot, air fryer;
- dietary constraints from terms like gluten-free, vegetarian, dairy-free, low-sodium;
- time constraints from terms like under 30 minutes, overnight, make-ahead.

This does not need to be perfect. It should be deterministic, explainable, and tested.

Use existing normalization helpers where useful, but avoid adding a large ontology.

### 3. Add confidence labels

Add a small confidence taxonomy:

```text
high
medium
low
rejected
```

Suggested behavior:

- `high`: dish intent plus enough core ingredients/method details exist;
- `medium`: dish intent exists but some useful details are missing;
- `low`: broad/vague request such as `make dessert`;
- `rejected`: empty, symbols-only, or unusable text.

### 4. Add clarification decision rules

Implement a deterministic decision function that returns whether one bounded clarification question should be asked.

Ask one question when:

- dish intent is unclear;
- input is too broad for useful RAG;
- required ingredient conflict exists;
- cooking method is ambiguous and materially changes retrieval;
- retrieval support is weak and missing detail is user-specific;
- safety-relevant handling ambiguity affects instructions.

Do not ask when:

- the input is specific enough;
- a safe assumption can be disclosed;
- the missing detail is minor;
- the user message is social chatter;
- the user is only asking for formatting.

The decision should include:

- `should_clarify`
- `question`
- `reason`
- `confidence_label`

### 5. Add follow-up delta classification

Implement a deterministic classifier for follow-up messages.

Supported labels:

```text
relevant_requirement_update
clarification_answer
correction_to_assumption
irrelevant_chatter
formatting_only
regenerate_without_new_requirements
save_or_finalize_request
unknown
```

For each classification, return:

- label;
- reason;
- whether RAG should refresh;
- whether provider generation is likely needed;
- whether clarification may be needed.

Examples to cover:

- `actually make it no-bake` -> relevant requirement update, refresh RAG;
- `use ricotta instead of cream cheese` -> relevant requirement update, refresh RAG;
- `make it gluten-free` -> relevant requirement update, refresh RAG;
- `I only have an air fryer` -> relevant requirement update, refresh RAG;
- `thanks` -> irrelevant chatter, no refresh;
- `make it shorter` -> formatting only, no refresh;
- `regenerate it` -> regenerate without new requirements, no refresh;
- `save this` -> save/finalize request, no refresh.

### 6. Add RAG refresh decision rules

Implement a function that compares previous requirements state with updated requirements state or follow-up classification and returns:

- `should_refresh_rag`
- `reason`
- `changed_fields`
- `previous_summary`
- `current_summary`

Refresh when meaningful retrieval-affecting requirements changed:

- dish type;
- cooking method;
- main ingredient;
- excluded ingredient;
- dietary constraint;
- cuisine/style;
- equipment constraint;
- time constraint;
- serving count change large enough to alter proportions.

Do not refresh for chatter, cosmetic wording, formatting-only requests, `looks good`, or save/finalize.

### 7. Add test/demo session store

Add a lightweight in-memory session store suitable for tests/local demo only.

Requirements:

- process-local only;
- bounded max sessions;
- TTL/expiration;
- deterministic cleanup;
- no disk persistence;
- no Redis/SQLite/Postgres;
- no production user memory;
- no raw provider prompt/response storage.

Expose methods such as:

- `create_session(requirements_state)`
- `get_session(interaction_id)`
- `update_session(interaction_id, updated_state)`
- `expire_sessions(now)`
- `clear()`

This store is scaffolding for future API tasks. It does not need to be wired to public endpoints in this task.

### 8. Add tests

Add deterministic unit tests for:

- requirements extraction for cheesecake, carbonara, omelet, and chicken/rice casserole;
- serving count extraction;
- excluded ingredient extraction, such as `no heavy cream`;
- method extraction, such as baked vs no-bake;
- equipment and dietary constraints;
- confidence labels;
- clarification needed for vague `make dessert`;
- no clarification for detailed cheesecake notes;
- follow-up delta classification examples;
- RAG refresh true for `actually make it no-bake`;
- RAG refresh false for `thanks`, `looks good`, and formatting-only edits;
- session store create/get/update/expire/clear;
- safe serialization with no prompts, secrets, env values, local paths, raw provider responses, or long-term memory leakage.

### 9. Update docs

Update:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md` if relevant
- `README.md` if relevant

Create:

```text
outbox/0030B-recipe-session-requirements-alpha-scaffold-results.md
```

The outbox should summarize:

- models added;
- extraction rules added;
- clarification policy implemented;
- delta classifier implemented;
- RAG refresh decision logic;
- session store behavior;
- tests added;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Requirements/session scaffold exists and is deterministic.
- Basic requirements extraction works for common recipe notes.
- Confidence labels are present and tested.
- Clarification decisions are bounded to one question.
- Follow-up delta classifier supports the 0030A taxonomy.
- RAG refresh decision logic is implemented and tested.
- A bounded in-memory test/demo session store exists.
- No runtime public endpoints are required in this task.
- No production storage, persistent memory, auth, paid access, public route exposure, vector DB, embeddings, Redis, Qdrant, pgvector, or full chat UI is added.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required.
- No raw dataset files, `.tmp-ai-demo` artifacts, screenshots, logs, credentials, `.env` files, disk cache, or generated persistent indexes are committed.

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

If direct Windows pytest is run and fails due to the known local `pytest-of-scott` temp ACL issue or because live OpenAI env vars are set, document that separately and rely on Git Bash validation if it passes.

## Non-Goals

- no production storage;
- no auth;
- no paid access;
- no public route exposure;
- no Cloudflare changes;
- no database migrations;
- no persistent user memory;
- no vector database;
- no embeddings;
- no Qdrant;
- no pgvector;
- no Redis;
- no live OpenAI calls;
- no full chat UI;
- no browser automation;
- no screenshots;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api docs README.md outbox/0030B-recipe-session-requirements-alpha-scaffold-results.md

git commit -m "mailbox: complete task 0030B recipe session requirements scaffold"

git pull --rebase origin main
git push origin main
```
