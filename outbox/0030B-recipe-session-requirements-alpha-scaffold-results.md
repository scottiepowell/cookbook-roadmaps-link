# 0030B Recipe Session Requirements Alpha Scaffold Results

## Summary

Implemented the first narrow alpha scaffold for session-scoped recipe requirements handling. This adds deterministic, offline, mock-friendly building blocks only. No public recipe-session API endpoints or full chat runtime were added.

## Models Added

Added `ai-api/app/recipe_requirements.py` with:

- `RecipeRequirementSource`
- `RecipeRequirementField`
- `RecipeRequirementsState`
- `RecipeSessionDecision`
- `RecipeSessionResponseState`
- `RecipeFollowUpClassification`
- `RecipeRagRefreshDecision`
- clarification question and retrieval summary models

The state supports dish intent, serving count, ingredients, exclusions, cooking method, equipment, time, dietary constraints, assumptions, requirement sources, confidence, questions, revision count, retrieval summaries, cache key fingerprint, support level, citation IDs, and TTL timestamps.

Requirement sources distinguish:

- `user-provided`
- `inferred`
- `defaulted`
- `RAG-supported`
- `clarified-by-user`

## Extraction Rules Added

The deterministic extractor handles obvious rough notes for:

- cheesecake;
- carbonara;
- omelet/omelette;
- chicken and rice casserole;
- serving counts such as `for 4`, `serves 6`, and `4 servings`;
- excluded ingredients such as `no heavy cream`;
- baked versus no-bake methods;
- skillet, oven, air fryer, Instant Pot, and slow cooker signals;
- gluten-free, vegetarian, dairy-free, and low-sodium constraints;
- under-30-minute, overnight, and make-ahead time constraints.

The implementation reuses existing normalization helpers and intentionally keeps the food term list small.

## Confidence Labels

Implemented:

- `high`
- `medium`
- `low`
- `rejected`

Detailed named-dish inputs with ingredients or method details classify as `high`; named dishes with sparse detail classify as `medium`; broad requests such as `make dessert` classify as `low`; empty, symbols-only, or unusable text classifies as `rejected`.

## Clarification Policy Implemented

`decide_clarification` returns:

- `should_clarify`
- `question`
- `reason`
- `confidence_label`

It asks one bounded question for vague dish intent, conflicting ingredient requirements, weak retrieval support with missing user-specific detail, or safety-relevant chicken casserole ambiguity.

It avoids clarification for specific inputs, safe assumptions, social chatter, and formatting-only messages.

## Delta Classifier Implemented

`classify_follow_up` supports the 0030A taxonomy:

- `relevant_requirement_update`
- `clarification_answer`
- `correction_to_assumption`
- `irrelevant_chatter`
- `formatting_only`
- `regenerate_without_new_requirements`
- `save_or_finalize_request`
- `unknown`

Examples covered by tests include no-bake changes, ricotta replacement, gluten-free constraints, air fryer equipment, thanks/chatter, shorter formatting, regenerate, and save/finalize.

## RAG Refresh Decision Logic

`decide_rag_refresh` compares retrieval-affecting requirement summaries and returns:

- `should_refresh_rag`
- `reason`
- `changed_fields`
- `previous_summary`
- `current_summary`

Refresh triggers include dish intent, method, ingredients, exclusions, dietary constraints, equipment constraints, time constraints, and large serving changes. Chatter, formatting-only edits, regenerate-without-new-requirements, and finalize requests do not refresh RAG.

## Session Store Behavior

Added `ai-api/app/recipe_session.py` with a bounded process-local `RecipeSessionStore` for tests/local demo scaffolding only.

The store supports:

- `create_session`
- `get_session`
- `update_session`
- `expire_sessions`
- `clear`

It enforces a max-session bound, TTL expiration, deterministic cleanup, and no disk persistence. It does not use Redis, SQLite, Postgres, production storage, or long-term user memory.

## Tests Added

Added:

- `ai-api/tests/test_recipe_requirements.py`
- `ai-api/tests/test_recipe_session.py`

The tests cover:

- requirements extraction for cheesecake, carbonara, omelet/omelette, and chicken/rice casserole;
- serving count extraction;
- excluded ingredient extraction;
- baked versus no-bake method extraction;
- equipment constraints;
- dietary constraints;
- confidence labels;
- clarification for vague `make dessert`;
- no clarification for detailed cheesecake notes;
- chicken casserole safety ambiguity;
- follow-up delta classification;
- RAG refresh true for no-bake method changes;
- RAG refresh false for chatter, `looks good`, formatting-only edits, and finalize;
- session store create/get/update/expire/clear;
- safe serialization checks for prompt/secret/path leakage.

## Documentation Updates

Updated:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `README.md`

## Validation Results

- Focused tests: `ai-api/tests/test_recipe_requirements.py` and `ai-api/tests/test_recipe_session.py` passed, 21 tests. Direct Windows pytest emitted the known local `.pytest_cache` warning only.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 28 offline cases.
- Git Bash `scripts/validate-repo.sh`: passed, including 200 AI API tests, 28 offline eval cases, Docker Compose config, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed with line-ending warnings only.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed, including offline evals and direct endpoint smoke checks.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live opt-in settings were not present.

No live OpenAI calls were run during normal validation.

## Explicit Non-Goals

This task did not add:

- public recipe-session endpoints;
- production storage;
- authentication;
- paid access;
- public route exposure;
- Cloudflare changes;
- database migrations;
- persistent user memory;
- vector databases;
- embeddings;
- Redis;
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
- no local absolute paths appear in public docs examples.

Confirmed during pre-commit status, staged-file, and docs checks.
