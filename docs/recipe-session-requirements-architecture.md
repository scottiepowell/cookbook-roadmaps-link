# Recipe Session Requirements Architecture

## Purpose

This document defines the proposed 0030A alpha architecture for a recipe requirements and interaction layer that sits between input quality checks and the existing RAG-informed importer/generator pipeline.

The goal is to let the recipe creator understand what the user is trying to make, decide whether the input is specific enough to generate, ask one bounded clarification question when needed, and track session-scoped requirement changes so RAG is refreshed only when it materially matters.

This is a design document. It does not implement runtime endpoints, production storage, auth, paid access, public route exposure, database migrations, embeddings, vector databases, Redis, long-term memory, or a full chat UI.

## Alpha Scaffold Status

`0030B` adds the first narrow implementation scaffold for this architecture:

- `ai-api/app/recipe_requirements.py` defines session-scoped requirements models, deterministic extraction, confidence labels, clarification decisions, follow-up delta classification, and RAG refresh decisions.
- `ai-api/app/recipe_session.py` defines a bounded process-local in-memory session store for tests and local demo scaffolding only.
- `ai-api/tests/test_recipe_requirements.py` and `ai-api/tests/test_recipe_session.py` cover extraction, confidence, clarification, delta classification, RAG refresh decisions, safe serialization, and store bounds/TTL behavior.

`0030C` adds local alpha API endpoints on top of that scaffold:

- `POST /ai/recipe-session/start`
- `POST /ai/recipe-session/{interaction_id}/message`
- `GET /ai/recipe-session/{interaction_id}`
- `POST /ai/recipe-session/{interaction_id}/finalize`

These endpoints are local/offline/mock-friendly and reuse the existing importer/RAG path for draft generation. They store only bounded process-local demo session state and safe draft/citation/retrieval summaries. They do not add production storage, auth, paid access, persistent user memory, Redis, embeddings, vector databases, public route exposure, or a full chat UI.

`0030D` adds the smallest useful local demo UI layer for the alpha endpoints:

- `GET /demo` and `GET /demo/ai` include a `Recipe Session Alpha` section.
- The section can start a session, send one follow-up, get current state, finalize for demo, and reset local UI state.
- It displays interpreted requirements, clarification questions, RAG refresh/no-refresh decisions, support level, citation IDs, draft summaries, citations, warnings, and expiration.
- `scripts/demo-ai-mock.ps1` exercises the session start/message/get/finalize, vague-clarification, and chatter/no-refresh paths offline with the mock provider.

This UI is still an operator/developer demo panel, not a production recipe editor or full chat app. Sessions remain process-local and expire. Finalize is demo-only and does not write to production storage.

`0030E` adds a dedicated offline/mock regression baseline for recipe-session behavior:

- `evals/ai_cookbook/session_cases.yaml` defines deterministic start/message/get/finalize cases.
- `evals/ai_cookbook/session_eval.py` runs those cases through FastAPI `TestClient` with generated dataset fixtures and the mock provider.
- `evals/ai_cookbook/run_evals.py` includes the `recipe_session` group, covering detailed draft generation, vague clarification, material RAG refresh, chatter/formatting no-refresh, clarification answer, demo finalize, missing-session safety, and prompt/secret/path leakage checks.

The session eval harness does not require live OpenAI, real `recipe-dataset/`, production storage, browser automation, screenshots, or persistent user memory.

`0030F` hardens the local alpha acceptance surface:

- session API safety tests cover empty/symbol input, unknown and expired get/message/finalize, follow-up before draft, finalize before draft, repeated finalize, repeated no-refresh messages, contradictory method updates, equipment changes, and excluded-ingredient updates;
- session evals add air-fryer refresh, excluded-ingredient refresh, and finalize-without-draft cases, raising the offline eval baseline to 39/39 cases;
- the demo UI labels process-local alpha behavior, session expiration, no-refresh reuse, friendly missing/expired-session errors, and demo-only finalize boundaries more clearly;
- [Recipe Session Alpha Acceptance Runbook](recipe-session-alpha-acceptance-runbook.md) defines the local acceptance checklist and validation commands.

## Problem

The completed 0029B RAG line makes a single importer request much stronger:

- input quality checks run before provider calls;
- local dataset examples are normalized, ranked, cached, and packed into bounded prompt context;
- citations, provenance, context-packing metadata, cache metadata, and RAG support honesty are returned;
- offline evals and E2E tests prove the importer route works with generated fixtures.

The remaining product issue is interaction quality across turns. A user may start vague, answer a clarification question, or revise a material requirement after a draft. The system needs a lightweight session state so it can tell the difference between:

- a meaningful recipe requirement change, such as `actually make it no-bake`;
- an answer to a clarification question;
- a formatting preference;
- irrelevant chatter;
- a request to regenerate with the same requirements;
- a finalization request.

Without this layer, the app either generates too early, reruns RAG unnecessarily, or fails to explain why citations changed.

## Relationship To 0029B

The requirements layer is upstream of the existing importer RAG pipeline. It does not replace retrieval, context packing, support policy, citations, or cache behavior.

```text
user input
  -> input quality gate
  -> requirements extraction
  -> confidence assessment
  -> clarify if needed
  -> RAG retrieval
  -> context packing
  -> RAG support policy
  -> recipe generation
  -> citations/provenance
  -> user revision
  -> requirements delta detection
  -> RAG refresh when relevant
  -> revised generation
```

The 0029B importer path remains the generation engine. The 0030A layer decides when to call it, what interpreted requirement state should shape retrieval, and why a later turn should reuse or refresh retrieval context.

## Alpha Scope

In scope for alpha design:

- session-scoped requirements state;
- deterministic or model-assisted requirements extraction;
- confidence labels for whether generation can proceed;
- one bounded clarification question per turn;
- delta classification for follow-up messages;
- RAG refresh policy and refresh explanations;
- references to existing process-local retrieval cache metadata;
- API and UI proposal for a future implementation;
- offline test strategy.

Out of scope:

- production auth or paid access;
- public live OpenAI exposure;
- production persistent storage;
- database migrations;
- persistent user memory or long-term personalization;
- Redis, vector databases, embeddings, pgvector, Qdrant, or generated persistent indexes;
- Cloudflare or route exposure changes;
- full chat UI;
- raw prompt or raw provider response storage.

## Request Flow

The alpha flow should use the existing input quality gate first. Empty, junk, symbol-only, or unsafe unusable input is rejected before requirements extraction, retrieval, or provider calls.

For usable input:

1. Extract requirements into a lightweight state model.
2. Assess confidence.
3. If the requirements are too vague or materially ambiguous, return one clarification question.
4. If the requirements are specific enough, build a retrieval query from the requirements.
5. Run deterministic dataset retrieval or reuse safe cache hits.
6. Pack bounded RAG context.
7. Apply RAG support policy.
8. Generate a draft with the mock or explicitly opted-in provider.
9. Persist only session-safe state and retrieval summaries.
10. On later messages, classify the delta and decide whether to refresh RAG.

The provider should not receive raw session history by default. It should receive the current user-visible requirement summary, current user text or revision instruction, and packed RAG context only when generation is needed.

## Requirements State Model

The alpha state is session-scoped and short-lived. It is suitable for local memory or a future ephemeral store, not production long-term memory.

```json
{
  "interaction_id": "recipe-session-short-id",
  "original_user_text": "classic baked cheesecake for 4 people...",
  "latest_user_text": "actually make it no-bake",
  "dish_intent": {
    "value": "no-bake cheesecake",
    "source": "clarified-by-user"
  },
  "serving_count": {
    "value": 4,
    "source": "user-provided"
  },
  "required_ingredients": [
    {"value": "cream cheese", "source": "user-provided"},
    {"value": "graham cracker crust", "source": "user-provided"}
  ],
  "optional_ingredients": [
    {"value": "vanilla", "source": "user-provided"}
  ],
  "excluded_ingredients": [
    {"value": "heavy cream", "source": "user-provided"}
  ],
  "cooking_method": {
    "value": "chill, no bake",
    "source": "clarified-by-user"
  },
  "equipment_constraints": [],
  "time_constraints": [
    {"value": "chill overnight", "source": "user-provided"}
  ],
  "dietary_constraints": [],
  "texture_or_style_goals": [
    {"value": "classic", "source": "user-provided"}
  ],
  "assumptions": [
    {"value": "default servings are 4 when not specified", "source": "defaulted"}
  ],
  "requirement_sources": {
    "user-provided": ["dish_intent", "serving_count", "required_ingredients"],
    "inferred": [],
    "defaulted": ["serving_count"],
    "RAG-supported": ["structure", "proportions"],
    "clarified-by-user": ["cooking_method"]
  },
  "confidence_label": "ready",
  "open_questions": [],
  "resolved_questions": [
    {
      "question": "Should this cheesecake be baked or no-bake?",
      "answer": "no-bake",
      "resolved_at": "timestamp"
    }
  ],
  "revision_count": 1,
  "last_retrieval_summary": {
    "query": "no-bake cheesecake cream cheese graham cracker crust chill",
    "retrieved_count": 3,
    "top_titles": ["No-Bake Cheesecake Bars", "Classic Cheesecake"],
    "relevance_category": "strong",
    "rag_refresh_reason": "cooking_method changed from baked to no-bake"
  },
  "last_retrieval_cache_key": "short-safe-fingerprint",
  "last_support_level": "strong",
  "last_citation_ids": ["dataset:no-bake-cheesecake-bars", "dataset:classic-cheesecake"],
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "expires_at": "timestamp"
}
```

### Requirement Sources

Each requirement should track provenance:

- `user-provided`: explicitly stated by the user.
- `inferred`: derived from phrasing but not explicitly stated.
- `defaulted`: system default, such as servings of 4.
- `RAG-supported`: reinforced by retrieved examples, without overriding the user.
- `clarified-by-user`: supplied as an answer to an open question or later correction.

Raw provider prompts, raw provider responses, API keys, environment values, local dataset paths, and private file paths should not be stored in state.

## Confidence Assessment

Use a small confidence taxonomy:

| Label | Meaning | Next Action |
| --- | --- | --- |
| `ready` | Dish intent and enough core requirements are present. | Run RAG and generate. |
| `needs_clarification` | One material missing or conflicting detail blocks a useful draft. | Ask one bounded question. |
| `usable_with_assumptions` | Minor details are missing but safe assumptions can be disclosed. | Run RAG and generate with assumptions. |
| `rejected` | Input quality is unusable or unsafe for the workflow. | Return controlled rejection before retrieval/provider calls. |

Confidence may be deterministic for obvious cases and model-assisted later for nuanced extraction. The alpha design should keep deterministic rules authoritative for provider-call avoidance and safety.

## Clarification Trigger Policy

Ask one bounded question when:

- dish intent is unclear, such as `make dessert`;
- recipe type is too vague for useful retrieval;
- required ingredient conflicts exist, such as `vegan carbonara with pancetta`;
- method choice materially changes the recipe, such as baked versus no-bake cheesecake;
- the user likely needs to decide an important thing, such as raw versus cooked chicken in a casserole path;
- retrieval support is weak and the missing detail is user-specific;
- safety-relevant food handling ambiguity affects instructions.

Do not ask when:

- the model can make a safe disclosed assumption;
- the missing detail is minor, such as garnish or optional seasoning;
- input is already specific enough for retrieval and generation;
- the user is social or off-topic;
- the user asks only for formatting or wording changes.

Clarification rules:

- ask at most one question per turn;
- use short, direct wording;
- prefer choices when the ambiguity has obvious options;
- do not ask for information already provided;
- do not call the provider while waiting for a required clarification.

Examples:

| Situation | Clarification |
| --- | --- |
| `make dessert` | `What dessert do you want to make: cake, cookies, cheesecake, or something else?` |
| `chicken rice casserole bake until hot` | `Is the chicken already cooked, or should the recipe start with raw chicken?` |
| `make pasta with cheese` | `What pasta dish are you aiming for, such as mac and cheese, carbonara, or baked pasta?` |

## RAG Refresh Policy

Refresh retrieval when a follow-up changes or adds:

- dish type;
- cooking method;
- main ingredient;
- excluded ingredient;
- dietary constraint;
- cuisine or style;
- equipment constraint;
- time constraint;
- serving count large enough to alter proportions or recipe family;
- any requirement that changes which examples should be retrieved.

Examples that should refresh RAG:

| Follow-Up | Refresh Reason |
| --- | --- |
| `actually make it no-bake` | Cooking method changed. |
| `use ricotta instead of cream cheese` | Main ingredient changed. |
| `make it gluten-free` | Dietary constraint changed. |
| `I only have an air fryer` | Equipment constraint changed. |
| `turn the omelet into a casserole` | Dish type changed. |

Do not refresh RAG for:

- `thanks`;
- `looks good`;
- unrelated personal comments;
- cosmetic wording only;
- formatting preference only;
- regenerate requests with no new requirements;
- small copy edits that do not change retrieval intent.

When RAG refreshes, the response should include a concise explanation:

```text
RAG refreshed because the cooking method changed from baked to no-bake.
```

## Delta Classifier

The follow-up classifier should use these labels.

| Label | Meaning | Refresh RAG | Provider Call | Follow-Up Question |
| --- | --- | --- | --- | --- |
| `relevant_requirement_update` | User adds or changes a material recipe requirement. | Yes when retrieval intent changes. | Yes after refresh unless clarification is required. | Only if the update creates a material ambiguity. |
| `clarification_answer` | User answers the currently open question. | Yes if the answer changes retrieval intent. | Yes if state becomes ready. | No, unless a new material conflict appears. |
| `correction_to_assumption` | User corrects an inferred/defaulted assumption. | Yes when the correction affects retrieval. | Yes after refresh or state update. | Rarely. |
| `irrelevant_chatter` | Social or unrelated text. | No. | No, unless product chooses a brief conversational response. | No. |
| `formatting_only` | User asks for bullets, shorter wording, metric units, or copy style only. | No. | Yes only if draft text must be reformatted. | No. |
| `regenerate_without_new_requirements` | User asks to try again with the same requirements. | No. | Yes, reuse current retrieval context. | No. |
| `save_or_finalize_request` | User accepts or asks to save/export/finalize. | No. | No unless final formatting is needed. | No. |
| `unknown` | The system cannot confidently classify the message. | No by default. | No by default. | Ask one bounded clarification if needed. |

Examples:

- `Use ricotta instead` -> `relevant_requirement_update`, refresh.
- `Yes, no-bake` -> `clarification_answer`, refresh if previous state was baked or unknown.
- `I meant cooked chicken` -> `correction_to_assumption`, refresh if chicken handling changes retrieved examples.
- `thanks, this is nice` -> `irrelevant_chatter`, no refresh.
- `make it a table` -> `formatting_only`, no refresh.
- `try again` -> `regenerate_without_new_requirements`, no refresh.
- `save this` -> `save_or_finalize_request`, no refresh.

## Retrieval And Session Cache Design

The session layer should not duplicate the 0029B process-local retrieval cache. Instead:

- session state stores safe summaries and fingerprints;
- the process-local cache stores built dataset indexes and retrieval results;
- citations are referenced by stable safe IDs and titles;
- old and new requirements are compared in the session layer before retrieval;
- RAG refresh explanations are stored with the revision.

Session state should store:

- normalized retrieval query summary;
- anchors used;
- matched result IDs;
- citation IDs and titles;
- retrieval support level;
- retrieval cache key fingerprint;
- context-packing summary;
- refresh reason;
- revision number;
- timestamps and expiry.

Process-local cache should store:

- dataset index cache entries;
- retrieval result cache entries;
- safe hit/miss metadata;
- bounded LRU or TTL behavior.

TTL recommendations:

- local alpha session state: 30 to 120 minutes;
- process-local retrieval cache: keep existing 0029B-10 defaults unless future performance evidence changes them;
- finalization should clear or mark the session complete in alpha.

Privacy and safety boundaries:

- no raw provider prompts or raw provider responses in session state;
- no local absolute dataset paths in public metadata;
- no `.env` values, API keys, Authorization headers, or secret-like strings;
- no long-term personal memory;
- no cross-demo data sharing beyond shared infrastructure.

## API Proposal

The alpha API can be session-oriented while still using the existing importer generation internals.

### `POST /ai/recipe-session/start`

Purpose: start a recipe creation interaction from user notes.

Alpha implementation: available locally as of 0030C. It extracts requirements, creates an in-memory session, returns `clarification_needed` or `rejected` without provider calls when appropriate, and otherwise calls the existing importer/RAG pipeline for a mock/offline draft.

Request:

```json
{
  "text": "classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust",
  "options": {
    "provider": "mock",
    "dataset_limit": 5000
  }
}
```

Response state `draft_generated`:

```json
{
  "interaction_id": "rs_123",
  "state": "draft_generated",
  "requirements": {
    "dish_intent": "baked cheesecake",
    "serving_count": 4,
    "required_ingredients": ["cream cheese", "sugar", "eggs", "vanilla", "graham cracker crust"],
    "confidence_label": "ready",
    "assumptions": []
  },
  "rag": {
    "ran": true,
    "refreshed": false,
    "support_level": "strong",
    "citation_ids": ["dataset:classic-cheesecake"],
    "retrieval_cache_key": "short-safe-fingerprint"
  },
  "draft": {
    "title": "Classic Baked Cheesecake",
    "servings": 4
  },
  "citations": [
    {
      "id": "dataset:classic-cheesecake",
      "title": "Classic Baked Cheesecake",
      "source_id": "classic-cheesecake"
    }
  ]
}
```

Response state `clarification_needed`:

```json
{
  "interaction_id": "rs_124",
  "state": "clarification_needed",
  "requirements": {
    "dish_intent": null,
    "confidence_label": "needs_clarification",
    "open_questions": [
      {
        "id": "q1",
        "question": "What dessert do you want to make: cake, cookies, cheesecake, or something else?"
      }
    ]
  },
  "rag": {
    "ran": false,
    "refreshed": false
  }
}
```

### `POST /ai/recipe-session/{id}/message`

Purpose: process a follow-up message, classify the delta, refresh RAG when needed, and optionally revise the draft.

Alpha implementation: available locally as of 0030C. It classifies follow-up messages, returns `no_material_change` for chatter or formatting-only updates, refreshes RAG for material requirement changes, and reuses importer/RAG generation for revised drafts.

Request:

```json
{
  "text": "actually make it no-bake"
}
```

Response state `rag_refreshed` or `draft_revised`:

```json
{
  "interaction_id": "rs_123",
  "state": "draft_revised",
  "delta": {
    "label": "relevant_requirement_update",
    "rag_refresh_required": true,
    "reason": "cooking_method changed from baked to no-bake"
  },
  "requirements": {
    "dish_intent": "no-bake cheesecake",
    "cooking_method": "no bake, chill",
    "revision_count": 1
  },
  "rag": {
    "ran": true,
    "refreshed": true,
    "refresh_reason": "cooking_method changed from baked to no-bake",
    "support_level": "strong",
    "previous_citation_ids": ["dataset:classic-cheesecake"],
    "citation_ids": ["dataset:no-bake-cheesecake-bars"]
  },
  "draft": {
    "title": "No-Bake Cheesecake",
    "servings": 4
  }
}
```

Response state `no_material_change`:

```json
{
  "interaction_id": "rs_123",
  "state": "no_material_change",
  "delta": {
    "label": "irrelevant_chatter",
    "rag_refresh_required": false,
    "reason": "message did not change recipe requirements"
  },
  "rag": {
    "ran": false,
    "refreshed": false,
    "citation_ids": ["dataset:classic-cheesecake"]
  }
}
```

### `GET /ai/recipe-session/{id}`

Purpose: return current safe session state for UI recovery.

Alpha implementation: available locally as of 0030C. Missing or expired sessions return a safe 404 response.

Response:

```json
{
  "interaction_id": "rs_123",
  "state": "draft_generated",
  "requirements": {
    "dish_intent": "baked cheesecake",
    "serving_count": 4,
    "confidence_label": "ready"
  },
  "last_retrieval_summary": {
    "support_level": "strong",
    "citation_ids": ["dataset:classic-cheesecake"]
  },
  "expires_at": "timestamp"
}
```

### `POST /ai/recipe-session/{id}/finalize`

Purpose: mark the current draft as accepted for export or later cookbook write-back. Alpha should not write to the production cookbook database.

Alpha implementation: available locally as of 0030C. It marks the session as ready to finalize for demo purposes only and does not write to Vanilla Cookbook storage.

Request:

```json
{
  "format": "draft_json"
}
```

Response state `ready_to_finalize`:

```json
{
  "interaction_id": "rs_123",
  "state": "ready_to_finalize",
  "draft": {
    "title": "Classic Baked Cheesecake",
    "servings": 4
  },
  "warnings": [
    "No cookbook database write-back is implemented in alpha."
  ]
}
```

### Response States

Allowed alpha response states:

- `draft_generated`
- `clarification_needed`
- `rag_refreshed`
- `draft_revised`
- `no_material_change`
- `ready_to_finalize`
- `rejected`

Errors should be safe and should not include raw prompts, raw provider responses, local paths, stack traces, API keys, or environment values.

## UI Proposal

The alpha UI does not need a full chat surface. It should show a recipe creation panel with:

- interpreted requirements;
- requirement sources, grouped as user-provided, inferred, defaulted, RAG-supported, or clarified-by-user;
- assumptions;
- one open clarification question;
- answer field for the open question;
- current draft;
- current citations and provenance;
- RAG support level and support message;
- context-packing and cache metadata from 0029B;
- refresh reason when RAG reruns;
- previous versus current retrieval summary when useful;
- finalization action that does not write to production storage.

UI language should avoid overstating support. Weak examples should be labeled as broad or structure-only examples, not authoritative sources.

### Operator Revision Summaries

The local alpha should show the current revision number and a compact, safe
requirement diff after every follow-up. The diff records changed fields, added,
removed, or updated requirement values, whether the change is retrieval
relevant, and the refresh/no-refresh reason. The companion revision sentence is
derived only from that structured state, such as `Revision 2: Changed
cooking_method; RAG refreshed because the change affects retrieval.` For
chatter and formatting-only updates it instead explains that no material
requirements changed, the existing draft and citations were reused, and no new
provider generation occurred. It must never display raw prompts, provider
responses, paths, environment values, or hidden retrieval context.

Alpha implementation status: `0030D` implements this as the `Recipe Session Alpha` panel in the existing sidecar demo UI. It is intentionally compact and operator-focused: textareas for initial notes and follow-up messages, buttons for start/message/get/finalize/reset, safe requirement and state metadata, draft summary/citations when present, and recoverable error cards. It does not implement a persistent conversation transcript, browser automation, production save, auth, paid access, or public route exposure.

## Example Flows

### Flow A: Enough Information, No Clarification

User message:

```text
cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill
```

Interpreted requirements:

- dish intent: cheesecake;
- cooking method: bake and chill;
- required ingredients: cream cheese, sugar, eggs, vanilla, graham cracker crust;
- serving count: defaulted to 4 if not stated.

Decision:

- confidence: `ready`;
- RAG runs;
- response state: `draft_generated`.

### Flow B: Low-Confidence Vague Request

User message:

```text
make dessert
```

Interpreted requirements:

- dish intent: unclear;
- category: dessert;
- missing user-specific detail: dessert type.

Decision:

- confidence: `needs_clarification`;
- RAG does not run;
- ask one question: `What dessert do you want to make: cake, cookies, cheesecake, or something else?`;
- response state: `clarification_needed`.

### Flow C: Method Change Triggers RAG Refresh

Initial user message:

```text
classic baked cheesecake for 4 with cream cheese graham cracker crust
```

Follow-up:

```text
actually make it no-bake
```

Interpreted delta:

- label: `relevant_requirement_update`;
- cooking method changed from baked to no-bake.

Decision:

- update requirements;
- refresh RAG for no-bake cheesecake examples;
- preserve previous citation IDs for comparison;
- response state: `draft_revised`;
- refresh explanation: `RAG refreshed because the cooking method changed from baked to no-bake.`

### Flow D: Irrelevant Social Chatter

Follow-up:

```text
that reminds me of my grandma
```

Interpreted delta:

- label: `irrelevant_chatter`;
- no requirement changed.

Decision:

- do not refresh RAG;
- do not call provider unless the product chooses a short conversational response;
- response state: `no_material_change`.

### Flow E: Safety-Relevant Ambiguity

User message:

```text
chicken rice casserole bake until hot
```

Interpreted requirements:

- dish intent: chicken and rice casserole;
- chicken state: unknown;
- cooking method: bake.

Decision:

- if exact instructions depend on raw versus cooked chicken, ask one question: `Is the chicken already cooked, or should the recipe start with raw chicken?`;
- RAG waits if the product requires exact safety instructions;
- response state: `clarification_needed`.

Alternative:

- generate with a disclosed assumption that chicken is cooked and include safe handling guidance;
- response state: `draft_generated`;
- assumption source: `defaulted`.

### Flow F: Regenerate Without New Requirements

Follow-up:

```text
try again
```

Interpreted delta:

- label: `regenerate_without_new_requirements`;
- requirements unchanged.

Decision:

- do not refresh RAG;
- reuse current retrieval context and citations;
- provider may be called to regenerate;
- response state: `draft_revised`.

### Flow G: Save Or Finalize

Follow-up:

```text
save this
```

Interpreted delta:

- label: `save_or_finalize_request`;
- requirements unchanged.

Decision:

- do not refresh RAG;
- no production cookbook write-back in alpha;
- return current draft and finalization warning;
- response state: `ready_to_finalize`.

## Test Strategy

Implementation should add offline tests only.

Unit tests:

- requirements extraction for named dishes, ingredients, methods, exclusions, servings, and constraints;
- requirement source tracking;
- confidence labels;
- clarification trigger rules;
- one-question limit;
- delta classifier labels;
- RAG refresh decisions;
- no-refresh chatter and formatting behavior;
- safety ambiguity handling;
- safe state serialization with no prompts, provider responses, local paths, or secrets.

Integration tests:

- `POST /ai/recipe-session/start` generates immediately for specific cheesecake notes;
- vague dessert request returns `clarification_needed` without provider or RAG calls;
- clarification answer updates state and runs RAG;
- no-bake method change refreshes RAG and updates citations;
- `thanks` returns `no_material_change`;
- regenerate reuses current retrieval context;
- finalize does not write to production storage.

Offline eval baseline:

- `evals/ai_cookbook/run_evals.py` includes the `recipe_session` group;
- cases use generated dataset fixtures and mock provider settings only;
- cases reset the process-local session store and retrieval cache between runs;
- response text is checked for raw prompts, raw provider responses, provider keys, stack traces, generated dataset paths, and local absolute paths.

E2E tests:

- generated fixture dataset only;
- mock provider only;
- start -> clarify -> answer -> generate;
- generate -> material change -> RAG refresh -> revise;
- generate -> chatter -> no refresh;
- support-policy and citation labels remain honest after revision;
- session state references process-local cache fingerprints safely.

Eval cases:

| Case | Expected |
| --- | --- |
| `make dessert` | `clarification_needed`, no RAG. |
| `cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill` | `draft_generated`, RAG runs. |
| `actually no bake` | `relevant_requirement_update`, RAG refresh. |
| `make it for 8 people` | serving update; refresh only if retrieval intent changes materially. |
| `thanks` | `no_material_change`, no RAG. |
| `use gluten-free crust` | dietary/ingredient constraint update; refresh or update retrieval query. |
| chicken casserole with unknown chicken state | clarification or safe disclosed assumption. |
| unknown session ID | safe `not_found` or `404` without stack trace or path leakage. |

## Implementation Phasing

Recommended follow-on tasks:

1. `0030G`: Operator UX polish for requirement diff display, still without production persistence.
2. `0030H`: Optional richer alpha session E2E eval cases if new product flows appear.
3. `0031A`: Production-readiness design for any future protected recipe-session exposure.

Each phase should keep normal validation offline and mock-only.
