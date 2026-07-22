# Cookbook AI Plugin Adapter Future Feature

## Purpose

Capture the future integration direction for bringing the RAG/AI sidecar into the `cookbook.roadmaps.link` product while preserving modularity, clear ownership boundaries, and a seamless end-user experience.

This is a future feature note only. It does not implement the integration, change public routing, add production auth, add provider runtime changes, or move the current local sidecar into the core app.

## Product intent

The current local product keeps the Cookbook app and AI sidecar separate while presenting them from one local entry point. The future direction should preserve that modularity, but the finished product should not feel bolted on.

The end-user goal is:

```text
The AI/RAG features should feel like a native part of cookbook.roadmaps.link, even if the implementation remains a plugin or sidecar behind clear adapter interfaces.
```

That means the integration should aim for a seamless UI/UX:

- consistent navigation, spacing, typography, loading states, and empty states;
- no obvious jump between "core app" and "AI sidecar" styling;
- no confusing separate product shell once production integration exists;
- AI actions placed where users naturally need them, such as recipe import, recipe detail, meal planning, and cookbook search;
- clear status and errors that read like product messages, not backend diagnostics;
- no exposure of provider keys, raw prompts, raw provider responses, stack traces, local paths, or implementation internals;
- mock/live/provider metadata available where useful for operators, but not disruptive to normal users.

## Architectural direction

Treat the RAG/AI sidecar as a **Cookbook AI Plugin** connected to the core application through a stable adapter contract.

```text
cookbook.roadmaps.link core app
        |
        | stable app/plugin contract
        v
Cookbook AI Adapter
        |
        | stable AI sidecar API
        v
RAG/AI sidecar
```

The core app should own:

- users and sessions;
- auth and authorization;
- recipe persistence;
- canonical recipe UI;
- public/private routing decisions;
- approved write-back behavior.

The AI plugin/sidecar should own:

- retrieval and RAG context preparation;
- prompt/session workflows;
- AI provider routing and budget controls;
- citations, provenance, and safe unavailable responses;
- offline/mock evals and provider diagnostics;
- AI-specific validation and troubleshooting.

The adapter should own:

- translating core recipe/user/session data into AI-safe request context;
- enforcing what the AI layer may read or mutate;
- normalizing recipe records for retrieval;
- writing back AI-created candidates only through approved core app APIs;
- keeping provider secrets server-side only.

## Interface concepts

### Core Cookbook Adapter Contract

The AI sidecar should not depend directly on arbitrary core app tables or UI details. Long term, it should depend on a stable adapter interface such as:

```text
GET    /adapter/recipes
GET    /adapter/recipes/{id}
POST   /adapter/recipes/search
POST   /adapter/recipes/import-candidate
POST   /adapter/recipes/{id}/ai-notes
GET    /adapter/user/context
```

A local SQLite adapter can remain useful for development, but production integration should prefer a stable app API or adapter layer.

### AI Plugin Contract

The core app should call AI capabilities through a stable plugin API such as:

```text
GET    /ai/plugin/manifest
GET    /ai/plugin/readiness
POST   /ai/import-recipe
POST   /ai/ask
POST   /dataset/ask
POST   /ai/meal-plan
POST   /ai/recipe-session/start
POST   /ai/recipe-session/{id}/message
```

A plugin manifest can describe available capabilities without hardcoding every feature into the core app:

```json
{
  "plugin_name": "cookbook-ai",
  "version": "0.1",
  "capabilities": [
    "recipe_import",
    "ask_my_cookbook",
    "dataset_rag",
    "meal_planning",
    "recipe_session"
  ],
  "allowed_models": ["gpt-5.4-nano"],
  "requires_server_side_key": true,
  "supports_mock_mode": true
}
```

## UI integration levels

A staged approach keeps risk low:

### Level 1: Link integration

The current local approach links the product shell to the Cookbook container and AI workspace. This is useful for local validation and early demos, but it should not be the final user experience.

### Level 2: Embedded plugin panel

The core app can embed AI features through a panel, iframe, web component, or routed module while the sidecar still owns AI workflow logic. This gives users a more unified experience while preserving implementation boundaries.

### Level 3: Native UI using plugin APIs

The final target should make AI actions feel native to the Cookbook app. The core app owns the UI and calls the AI plugin APIs behind the scenes. The sidecar continues to own RAG/provider/session logic.

The user experience should be seamless at Level 3:

- recipe import AI actions appear inside the normal recipe import flow;
- Ask My Cookbook appears near cookbook search or recipe browsing;
- meal planning appears as a native meal-planning workflow;
- recipe-session drafts and revisions use the same visual language as saved recipes;
- provider/live/mock details remain behind operator/debug views unless needed for safe user guidance.

## Security and data boundaries

Keep these boundaries:

- Provider API keys stay server-side only.
- Browser requests carry only safe mode/model preferences, never keys.
- The AI plugin receives only authorized user/session context.
- AI write-back goes through explicit approved core app APIs.
- No raw provider prompts, provider responses, stack traces, environment values, or local file paths are exposed to users.
- Mock/offline validation remains available.
- Live calls remain gated by server-side config, model allowlists, budget caps, and provider diagnostics.

## Future ADR scope

A future ADR should define:

- plugin manifest schema;
- core adapter contract;
- AI plugin API contract;
- auth/session handoff;
- read/write boundaries for recipes;
- RAG indexing boundary;
- mock/live provider boundary;
- UI integration target and seamless UX requirements;
- contract tests;
- migration phases from local sidecar shell to production integration;
- explicit non-goals for the first production integration phase.

## Non-goals for this note

- no implementation;
- no production auth;
- no public route exposure;
- no AWS/platform changes;
- no Cloudflare/DNS changes;
- no payment or subscription work;
- no provider routing overhaul;
- no new model integration;
- no vector database or embeddings decision;
- no upstream UI rewrite until the core app source and integration boundary are explicit.
