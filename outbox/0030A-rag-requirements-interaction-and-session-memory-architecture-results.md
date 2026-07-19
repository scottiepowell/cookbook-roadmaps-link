# 0030A RAG Requirements Interaction And Session Memory Architecture Results

## Summary

Completed the 0030A alpha architecture/design task for a session-scoped requirements layer that sits between input quality and the completed 0029B RAG importer pipeline.

No runtime endpoints, production storage, auth, paid access, database migrations, public route exposure, Cloudflare changes, embeddings, vector databases, Redis, persistent memory, full chat UI, live OpenAI calls, raw datasets, generated indexes, screenshots, or provider artifacts were added.

## Architecture Docs Created

- `docs/recipe-session-requirements-architecture.md`
- `docs/rag-requirements-interaction-architecture.md` (requirements-interaction entry document)
- `docs/recipe-creator-session-memory-model.md` (session-memory model companion)

The document defines the purpose, scope, request flow, relationship to 0029B, requirements state, clarification policy, RAG refresh policy, delta classifier, session/cache interaction, alpha API proposal, UI implications, example flows, and future test strategy.

## Proposed State Model

The proposed session-scoped state includes:

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

Requirement sources distinguish `user-provided`, `inferred`, `defaulted`, `RAG-supported`, and `clarified-by-user`.

The state intentionally excludes raw provider prompts, raw provider responses, secret values, `.env` contents, local absolute dataset paths, and long-term user memory.

## Clarification Policy

The architecture asks one bounded question when:

- dish intent is unclear;
- recipe type is too vague for useful retrieval;
- required ingredient conflicts exist;
- method choice materially affects the recipe;
- a user decision is likely required;
- retrieval support is weak and the missing detail is user-specific;
- safety-relevant food handling ambiguity affects instructions.

It avoids clarification when safe disclosed assumptions are enough, the missing detail is minor, input is already specific enough, the user is chatting, or the user only requests formatting.

## RAG Refresh Policy

The design refreshes retrieval when follow-up messages change requirements that affect examples:

- dish type;
- cooking method;
- main ingredient;
- excluded ingredient;
- dietary constraint;
- cuisine/style;
- equipment constraint;
- time constraint;
- serving count changes large enough to affect proportions;
- any requirement that changes retrieval intent.

It does not refresh for thanks, unrelated comments, cosmetic wording, formatting-only changes, `looks good`, or regenerate requests without new requirements.

Refresh explanations are part of the proposed response, for example:

```text
RAG refreshed because the cooking method changed from baked to no-bake.
```

## Delta Classifier

The proposed classifier taxonomy is:

- `relevant_requirement_update`
- `clarification_answer`
- `correction_to_assumption`
- `irrelevant_chatter`
- `formatting_only`
- `regenerate_without_new_requirements`
- `save_or_finalize_request`
- `unknown`

For each label, the architecture defines meaning, examples, whether to refresh RAG, whether to call the provider, and whether to ask a follow-up question.

## Proposed API

The alpha API proposal includes:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{id}/message`
- `GET /ai/recipe-session/{id}`
- `POST /ai/recipe-session/{id}/finalize`

Response states:

- `draft_generated`
- `clarification_needed`
- `rag_refreshed`
- `draft_revised`
- `no_material_change`
- `ready_to_finalize`
- `rejected`

The API proposal includes safe request/response JSON examples and keeps errors free of raw prompts, raw provider responses, local paths, stack traces, API keys, and environment values.

## Proposed UI Behavior

The UI proposal covers:

- interpreted requirements;
- requirement sources;
- assumptions;
- one open clarification question;
- the user's answer;
- why RAG refreshed;
- current citations and provenance;
- RAG support level and message;
- context-packing and cache metadata;
- previous versus current retrieval summary when useful;
- revised draft;
- finalize action without production write-back.

## Example Flows

Documented flows:

- enough information, no clarification;
- low-confidence vague request asks one bounded question;
- method change after draft, such as baked cheesecake to no-bake, triggers RAG refresh;
- irrelevant social chatter does not refresh RAG;
- safety-relevant ambiguity for chicken casserole;
- regenerate without new requirements reuses current retrieval context;
- save/finalize request does not refresh RAG or write to production storage.

## Test Strategy

The future implementation test strategy covers:

- requirements extraction;
- requirement source tracking;
- confidence labels;
- clarification trigger rules;
- one-question limit;
- delta classification;
- RAG refresh decisions;
- no-refresh chatter and formatting behavior;
- support-policy interaction;
- cache/session interaction;
- safety boundaries;
- safe state serialization;
- alpha API response states;
- offline/mock E2E flows.

## Documentation Updates

Updated:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`

## Explicit Non-Goals

This task did not implement:

- runtime recipe-session endpoints;
- production storage;
- authentication;
- paid access;
- database migrations;
- persistent user memory;
- public route exposure;
- Cloudflare changes;
- vector databases;
- embeddings;
- pgvector;
- Qdrant;
- Redis;
- full chat UI;
- screenshots or browser automation.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 28 offline cases.
- Git Bash `scripts/validate-repo.sh`: passed, including 179 AI API tests, 28 offline eval cases, Docker Compose config, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed with line-ending warnings only.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed, including offline evals and direct endpoint smoke checks.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live opt-in settings were not present.

No live OpenAI calls were run during normal validation.

## Artifact Safety Confirmation

Before commit, confirm:

- no raw dataset files are staged;
- no `.tmp-ai-demo` artifacts are staged;
- no generated persistent index files or disk cache files are staged;
- no `.env` files are staged;
- no screenshots are staged;
- no raw provider prompts, raw provider responses, API keys, credentials, or local absolute paths are included in public docs examples.

Confirmed during pre-commit status and staged-file review.
