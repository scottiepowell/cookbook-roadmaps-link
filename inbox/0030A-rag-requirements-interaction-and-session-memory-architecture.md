# 0030A RAG Requirements Interaction And Session Memory Architecture

## Goal

Design the next layer after 0029 retrieval tuning: a requirements/interaction layer that lets the AI recipe creator ask targeted follow-up questions when the user input is under-specified or low-confidence, then re-run or refine RAG after the user supplies meaningful new requirements.

This is an architecture/design task first. Do not implement runtime auth, paid access, production storage, database migrations, public route exposure, Cloudflare changes, vector databases, embeddings, or persistent production memory.

## Background

The current 0029 work focuses on making the recipe importer behave like a RAG-informed recipe creator:

- default servings of 4
- quantities when reasonable
- stronger instructions
- importer citations/provenance
- full-dataset RAG launch and citation rendering
- retrieval relevance tuning

The next product-level issue is interaction quality. When the model has low confidence, missing requirements, or ambiguous user intent, it should ask a bounded clarifying question before producing a final draft. If the user answers with relevant information, the system should update the requirements state and retrieve again from RAG using the improved requirement set.

Example:

- User: `cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill`
- Model can proceed because this is specific enough.
- User later says: `actually make it no-bake`
- System should recognize this as a material requirement change, update the requirements state, re-run RAG for no-bake cheesecake examples, and produce a revised draft.

## Core Concept

Introduce a requirements layer between input-quality checks and generation:

```text
user input
  -> input quality gate
  -> requirements extraction
  -> confidence assessment
  -> clarify if needed
  -> RAG retrieval
  -> recipe generation
  -> user revision
  -> requirements delta detection
  -> RAG refresh when relevant
  -> revised generation
```

## Design Requirements

### 1. Requirements state model

Define a lightweight requirements state for one recipe-creation interaction.

Suggested fields:

- session_id or interaction_id
- original_user_text
- latest_user_text
- dish_intent
- serving_count
- required_ingredients
- optional_ingredients
- excluded_ingredients
- cooking_method
- equipment_constraints
- time_constraints
- dietary_constraints
- texture/style goals
- source of each requirement: user, inferred, default, RAG-supported
- confidence score or confidence label
- open_questions
- resolved_questions
- revision_count
- retrieval_cache_key
- last_retrieval_summary

Do not store raw prompts or provider responses by default.

### 2. Clarification trigger rules

Design when the model should ask one bounded question instead of generating immediately.

Examples:

Ask a question when:

- dish intent is unclear
- required ingredient conflicts exist
- cooking method materially changes the recipe
- safety-critical food handling is ambiguous
- input is too vague for useful RAG
- retrieval results are weak and the missing information is likely user-specific

Do not ask a question when:

- the model can make a safe, clearly disclosed assumption
- the missing detail is minor and can be noted
- the user already provided enough requirements to create a useful draft
- the user adds irrelevant information that does not change recipe requirements

Keep the clarification bounded: at most one question per turn unless a later user answer creates a new material ambiguity.

### 3. RAG refresh rules

Design when new user input should trigger fresh retrieval.

Refresh RAG when the user changes or adds:

- dish type: cheesecake -> no-bake cheesecake
- cooking method: bake -> no-bake, stovetop -> slow cooker
- main ingredient: chicken -> turkey, cream cheese -> ricotta
- dietary constraint: gluten-free, vegetarian, low-sodium
- cuisine/style: Italian, Mexican, southern casserole
- equipment: Instant Pot, air fryer, no oven
- time constraint: under 30 minutes, make-ahead
- serving count changes enough to alter proportions

Do not refresh RAG when the user adds:

- thanks / social chatter
- cosmetic wording only
- formatting preference only
- irrelevant comments
- a minor preference that does not affect retrieval

### 4. Retrieval cache design

Design a short-lived retrieval cache for the interaction.

Purpose:

- avoid redoing identical retrieval
- preserve cited examples used in the current draft
- allow comparison between original and revised requirements
- support explanation like `RAG was refreshed because the user changed the method to no-bake`

Suggested cache contents:

- normalized retrieval query
- anchors used
- matched result IDs
- citation summaries
- retrieval quality score/label
- created_at
- expires_at
- revision_number

Cache should be local/session-scoped for now. Do not design production persistent user memory in this task.

### 5. Requirements delta detection

Design a simple deterministic or model-assisted classifier that can label a new user message as:

- relevant requirement update
- irrelevant/user chatter
- clarification answer
- correction to previous assumption
- request to regenerate without new requirements
- request to save/finalize

For relevant updates, determine whether RAG should be refreshed.

### 6. Multi-turn interaction flow

Document example flows:

#### Flow A: enough information, no clarification

User provides cheesecake notes. System extracts requirements, retrieves examples, generates draft.

#### Flow B: low confidence, asks one question

User says `make dessert`. System asks one bounded question such as `What dessert do you want to make, and do you want it baked or no-bake?`

#### Flow C: user changes method after draft

User starts with baked cheesecake. System generates draft. User says `make it no-bake`. System updates requirements, refreshes RAG, generates revised no-bake draft.

#### Flow D: user adds irrelevant information

User says `that reminds me of my grandma`. System does not refresh RAG and may respond conversationally or ask whether they want to add a requirement.

#### Flow E: safety-relevant ambiguity

User says `chicken rice casserole bake until hot`. System can generate, but should include safe handling assumptions or ask if chicken is raw vs cooked if the product path requires exact instructions.

### 7. UI implications

Design how the demo UI should show:

- current interpreted requirements
- assumptions made
- open question if clarification is needed
- why RAG was refreshed
- citations from current retrieval
- previous retrieval/citations if helpful
- revised draft after additional user input

Do not implement a full chat UI in this task unless explicitly scoped later.

### 8. API implications

Propose API shape for future implementation.

Potential endpoints:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{id}/message`
- `GET /ai/recipe-session/{id}`
- `POST /ai/recipe-session/{id}/finalize`

Or propose a simpler API if better.

Include request/response examples for:

- start interaction
- clarification needed
- user answers clarification
- RAG refreshed
- draft generated
- revised draft generated

### 9. Evaluation plan

Define offline and manual eval cases for 0030.

Include at least:

- `make dessert` -> clarification
- `cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill` -> generate without clarification
- `actually no bake` -> detect relevant requirement update and refresh RAG
- `make it for 8 people` -> serving count update and possibly no RAG refresh unless proportion/style changes
- `thanks` -> no RAG refresh
- `use gluten-free crust` -> requirement update and RAG refresh or ingredient constraint update
- `raw chicken or cooked chicken?` / chicken casserole safety case

### 10. Docs to create or update

Create:

- `docs/rag-requirements-interaction-architecture.md`
- `docs/recipe-creator-session-memory-model.md`
- `outbox/0030A-rag-requirements-interaction-and-session-memory-architecture-results.md`

Update as appropriate:

- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

## Acceptance Criteria

- Clearly distinguishes 0029 retrieval tuning from 0030 requirements interaction.
- Defines requirements state.
- Defines clarification trigger rules.
- Defines RAG refresh rules.
- Defines interaction-scoped retrieval cache.
- Defines requirements delta detection.
- Includes multi-turn example flows.
- Includes proposed API shape.
- Includes UI implications.
- Includes eval plan.
- Does not implement production persistent memory.
- Does not expose secrets, raw prompts, raw provider responses, private paths, or logs.

## Validation

Run normal documentation/code validation if files are changed:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live wrappers should skip unless explicit opt-in settings are present.

Do not run live OpenAI calls during normal validation.

## Non-Goals

- No production auth
- No paid access
- No public route exposure
- No Cloudflare changes
- No database migrations
- No persistent user memory
- No long-term production storage
- No vector database
- No embeddings
- No committed raw datasets
- No screenshots
- No browser automation
- No upstream Vanilla Cookbook rewrite

## Commit

```bash
git add docs README.md outbox/0030A-rag-requirements-interaction-and-session-memory-architecture-results.md

git commit -m "mailbox: complete task 0030A rag requirements interaction architecture"

git push origin main
```
