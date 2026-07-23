# ADR: Cookbook AI Plugin and Adapter Architecture

Status: proposed, docs-only, future integration

Date: 2026-07-23

## Decision summary

Integrate the RAG/AI sidecar into `cookbook.roadmaps.link` through two stable
boundaries: a Cookbook adapter contract owned by the core app and an AI plugin
API owned by the sidecar. The core app remains the source of truth for users,
sessions, recipes, authorization, and product UI. The AI sidecar remains the
source of truth for retrieval, AI sessions, provider calls, budgets, and
AI-specific diagnostics.

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

The boundary is deliberately modular, but modular internals cannot result in a
visibly bolted-on product. The production experience must feel like one
Cookbook product even when requests cross an adapter and a sidecar.

## Problem statement

The repository currently has a local product shell that presents the external
Vanilla Cookbook container and the AI sidecar from one entry point. The sidecar
already supports recipe import, Ask My Cookbook, dataset RAG, meal planning,
and Recipe Session Alpha workflows. The upstream Cookbook frontend source is
not in this repository, so the current local shell intentionally uses links and
redirects rather than rewriting or vendoring that UI.

A future production integration needs AI actions to appear in natural Cookbook
workflows while preserving ownership of canonical recipes, sessions, auth,
provider controls, and retrieval data. It must allow either side to evolve
without turning UI details, database tables, provider SDKs, or raw prompts into
an accidental shared interface.

## Why direct UI/backend coupling is risky

Directly embedding sidecar calls into arbitrary Cookbook screens or allowing
the sidecar to read core tables creates several risks:

- UI components become coupled to provider-specific payloads, error shapes, and
  timing behavior.
- Recipe persistence and AI draft generation can diverge on validation,
  ownership, authorization, or optimistic updates.
- The sidecar may accidentally receive more user data than a workflow needs.
- Provider keys, raw prompts, provider responses, and debug fields can leak
  across browser or public route boundaries.
- A schema or endpoint change in either application becomes a synchronized
  deployment rather than a versioned contract change.
- RAG indexing can silently become a second, stale recipe database.
- Mock/offline validation becomes harder if the UI depends on live sidecar
  availability.
- The current external Vanilla Cookbook image cannot be safely modified from
  this repository, and a forced UI rewrite would exceed the integration scope.

The adapter isolates these concerns and gives contract tests a stable seam.

## Responsibilities and ownership

### Core Cookbook application

The core app owns:

- canonical users, sessions, auth, authorization, and tenancy;
- canonical recipe records, revisions, ownership, and persistence;
- recipe import/save/edit/delete semantics;
- primary navigation, visual language, accessibility, and responsive layout;
- public/private route classification and origin policy;
- user-facing loading, empty, error, and confirmation states;
- approved write-back transactions and audit policy.

The core app must not need to know which provider generated an AI suggestion or
how RAG context was assembled.

### Cookbook AI plugin / RAG sidecar

The plugin owns:

- AI capability discovery and manifest metadata;
- bounded import, Ask, dataset RAG, meal-plan, and recipe-session workflows;
- retrieval query preparation and citation/provenance metadata;
- AI-specific schema validation and refusal of invalid or incomplete JSON;
- provider selection within the approved provider boundary;
- server-side live opt-in, model allowlists, budgets, timeouts, and safe errors;
- mock/offline execution and deterministic AI eval support;
- AI-specific readiness and operator diagnostics.

The plugin does not become the canonical recipe store, user directory, public
auth system, or browser secret holder.

### Cookbook AI Adapter

The adapter is the translation and policy layer between the core app and plugin.
It owns:

- translating authorized core-app context into minimal AI-safe context;
- validating contract versions, capability availability, and request shape;
- enforcing per-workflow read scopes and write scopes;
- normalizing recipe records into retrieval-safe documents or references;
- translating plugin results into core-app view models and user-facing errors;
- routing approved candidate write-back through core-app APIs;
- correlation IDs and safe metadata, without copying prompts or provider bodies;
- compatibility shims while contracts migrate between versions.

The adapter is not a general-purpose proxy and must not forward arbitrary
browser requests to the sidecar.

## Plugin manifest concept

The core app discovers a versioned manifest rather than hardcoding every AI
feature. This is a design sketch, not a production endpoint or schema commit:

```json
{
  "plugin_name": "cookbook-ai",
  "manifest_version": "1",
  "plugin_version": "0.1",
  "capabilities": [
    "recipe_import",
    "ask_my_cookbook",
    "dataset_rag",
    "meal_planning",
    "recipe_session"
  ],
  "api_contract": "cookbook-ai.v1",
  "supports_mock_mode": true,
  "requires_server_side_provider_key": true,
  "read_scopes": ["recipes:read", "user:context"],
  "write_scopes": ["recipes:import-candidate", "recipes:ai-notes"]
}
```

The manifest may describe capabilities, contract version, readiness classes,
required scopes, and safe feature flags. It must not include provider keys,
prompts, provider response bodies, local paths, or hidden environment values.

## Core Cookbook adapter contract

These are stable contract sketches only unless the existing application later
adopts better names:

```text
GET    /adapter/recipes
GET    /adapter/recipes/{id}
POST   /adapter/recipes/search
POST   /adapter/recipes/import-candidate
POST   /adapter/recipes/{id}/ai-notes
GET    /adapter/user/context
```

Suggested semantics:

| Contract | Purpose | Boundary |
| --- | --- | --- |
| `GET /adapter/recipes` | Return an authorized, bounded recipe list or page | No unrestricted database export; fields are scoped and normalized. |
| `GET /adapter/recipes/{id}` | Return one authorized recipe view | The adapter checks ownership/authorization and omits unrelated private fields. |
| `POST /adapter/recipes/search` | Search canonical recipes for an AI workflow | Search terms and result limits are bounded; raw indexes are not exposed. |
| `POST /adapter/recipes/import-candidate` | Submit a validated AI candidate for user review/save | Candidate is not canonical until core-app validation and user-authorized write-back complete. |
| `POST /adapter/recipes/{id}/ai-notes` | Add an explicitly supported AI note or annotation | Notes are scoped, attributable, reviewable, and cannot silently overwrite recipe content. |
| `GET /adapter/user/context` | Return minimal context needed for personalization | No credentials, raw tokens, payment data, or unrelated private profile data. |

The adapter should use stable IDs, explicit pagination/limits, schema versions,
safe timestamps, and structured status values. It should return safe errors,
not stack traces or downstream provider details.

## AI plugin API contract

These are AI capability sketches only:

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

Contract expectations:

- request and response schemas are versioned and strict where structured JSON
  is required;
- invalid, incomplete, or schema-nonconforming provider output is failure,
  never a successful draft;
- responses expose only safe user-facing data, citations, warnings, counts,
  and bounded statuses;
- provider name/model and usage summaries are operator metadata, not a license
  to expose raw provider bodies or prompts;
- readiness reports capability/configuration state without revealing secrets;
- every workflow has bounded input, output, timeout, and budget behavior;
- mock mode is a first-class contract mode for local validation;
- live mode remains server-side, explicitly opted in, model-allowlisted, and
  budget-enforced.

The existing sidecar route names are the starting point for these sketches;
this ADR does not add plugin endpoints or change current routes.

## Auth and session handoff concept

The core app remains the authority for authentication and authorization. A
future adapter call should carry a short-lived, audience-bound internal
assertion or server-to-server session context containing only:

- a non-secret user/session subject identifier;
- tenant or cookbook scope, if applicable;
- allowed workflow and read/write scopes;
- contract version and expiration;
- a correlation identifier for safe support diagnostics.

The sidecar validates audience, expiry, scope, and contract version before
processing. It does not mint public user sessions or become the system of
record for auth. Browser clients do not receive provider keys or internal
assertions. The exact mechanism—signed assertion, mTLS-backed internal call,
or an equivalent server-side handoff—requires a separate security design and
implementation task.

## Recipe read/write boundary

Recipe reads flow from the canonical core app through the adapter. The sidecar
receives only the bounded fields needed for the requested workflow, such as
title, ingredients, instructions, tags, and safe provenance IDs. It does not
query core tables directly or receive an unrestricted database path/export.

AI-generated content is initially a candidate or suggestion. The sidecar may
return a validated draft, citations, warnings, and a safe summary. The core app
owns review, merge, conflict handling, authorization, persistence, revision
history, and deletion. Any write-back must use an explicit adapter operation
and an approved core-app transaction. AI notes must not silently replace a
canonical recipe.

## RAG and indexing boundary

The core app owns canonical recipe truth and authorization. The sidecar owns
retrieval preparation, bounded query construction, ranking policy, citation
assembly, and any derived retrieval representation approved for the workflow.

An index is a derived, rebuildable view—not a second source of truth. The
adapter controls which records may enter retrieval, applies scope and deletion
rules, and supplies stable source IDs/version metadata. No vector database,
embeddings, persistent index, or production indexing implementation is chosen
by this ADR. The current local deterministic dataset/index path remains a
mock/offline development mechanism.

## Provider, mock, and live boundary

Provider access remains entirely behind the sidecar. Provider keys stay in
server-side secret/configuration handling and never appear in browser storage,
URLs, request bodies, manifests, logs, docs, or adapter payloads.

Mock/offline mode remains the normal validation path. It must work without a
provider key, network access, or production Cookbook integration. Live OpenAI
remains an explicit server-side opt-in with the existing model allowlist,
budget enforcement, timeouts, strict schema validation, and safe diagnostics.
No new provider or fallback integration is implied by this ADR.

## UI integration levels

Migration may proceed through these levels:

1. Link integration: retain the current local product shell and redirects for
   local validation. This is useful now but is not the final production UX.
2. Embedded plugin surface: place a bounded panel or routed module within the
   core app while the sidecar owns workflow execution. The panel uses adapter
   view models and safe status/error states.
3. Native core-app UI: the core app owns the final screens and interaction
   patterns, calls adapter methods behind the scenes, and renders AI results as
   native recipe/search/planning/session states.

The final production target is level 3. A panel may be an intermediate
implementation, but it must not expose an obvious product split.

## Seamless end-user UX requirements

Regardless of deployment topology, the integrated experience must provide:

- consistent navigation and information hierarchy;
- consistent visual style, spacing, typography, loading states, and empty
  states;
- AI actions placed in natural Cookbook workflows, including recipe import,
  recipe detail, cookbook search, and meal planning;
- no confusing split between the core app and AI sidecar in production UX;
- no raw diagnostics shown to normal users;
- operator/debug metadata only in appropriate support or debug views;
- safe, readable user-facing error messages that explain the next action;
- accessible labels, keyboard operation, focus behavior, contrast, and screen
  reader semantics for integrated AI panels and controls;
- responsive behavior for narrow, desktop, and touch layouts without hidden
  overflow or unusable side panels;
- clear draft/review/save states so AI suggestions cannot be mistaken for
  persisted canonical recipes.

Modularity is an implementation property, not a user-facing excuse. A user
should experience one Cookbook product with coherent navigation and feedback.

## Migration phases

### Phase 0: Preserve and document the current local boundary

Keep the current sidecar-served `/product` shell, `/demo` workspace, mock
smoke path, offline evals, server-side live gates, and optional mock-only
Playwright troubleshooting. No production integration is performed.

### Phase 1: Freeze contracts in design and fixtures

Define manifest, adapter, and plugin schemas; establish versioning, scopes,
safe error envelopes, capability readiness, and generated contract fixtures.
Add contract tests against fakes only. Do not connect the production Cookbook
or add new routes yet.

### Phase 2: Introduce a server-side adapter behind a feature flag

Implement the adapter in a separately approved task using the core app's
existing authorization and recipe APIs. Route only a bounded internal test
workflow to a mock AI plugin. Verify read scopes, candidate write-back, and
failure behavior before any live provider use.

### Phase 3: Integrate one native workflow

Choose one user-visible workflow, preferably recipe import or Ask My Cookbook.
Render it with core-app UI components and adapter view models. Keep a safe
fallback when the plugin is unavailable. Validate accessibility, responsive
behavior, no-leakage guarantees, and mock/offline regression coverage.

### Phase 4: Expand native workflows and operational controls

Add recipe detail notes, dataset-backed search, meal planning, and recipe
session capabilities only after each contract is stable. Add production auth,
rate limits, metering, and deployment changes only through separately approved
architecture and implementation tasks.

### Phase 5: Retire transitional links only after parity

Remove or demote link/redirect surfaces only when native workflows meet the
same product, accessibility, safety, and recovery expectations. Keep a safe
operator/debug path and a mock/offline test mode.

## Contract test strategy

Contract tests should run without live providers, production credentials,
browser automation, or raw recipe datasets. They should cover:

- manifest version, capability discovery, readiness statuses, and unknown
  capability handling;
- adapter request/response schemas, stable IDs, pagination, scope enforcement,
  bounded limits, and safe errors;
- plugin request/response schemas, strict structured output rejection, safe
  unavailable categories, and no raw diagnostics in user envelopes;
- auth/session handoff expiry, audience, scope, and correlation metadata using
  synthetic fixtures;
- recipe candidate review/write-back, conflict, duplicate, and no-write paths;
- RAG source scoping, deletion/version behavior, citation IDs, and derived
  index boundaries using generated in-memory records only;
- mock provider behavior and explicit refusal to call live providers during
  normal validation;
- compatibility between manifest/API contract versions;
- UI view-model mapping for loading, empty, unavailable, success, and error
  states using component-level/static checks where available.

The existing repository validator and offline eval harness remain the baseline.
Browser automation is optional local QA for the current task family and is not
part of this ADR implementation.

## Security and data boundary requirements

- Core-app auth and authorization are checked before adapter reads or writes.
- Provider keys remain server-side only; never place them in plugin manifests,
  browser payloads, logs, docs, or screenshots.
- Send least-privilege, bounded, purpose-specific context to the sidecar.
- Do not send payment data, raw auth tokens, unrelated profile data, local
  filesystem paths, private environment values, or unrestricted database dumps.
- Treat RAG indexes and derived records as scoped, rebuildable data with source
  IDs and deletion/version handling.
- Keep canonical recipe persistence in the core app and require explicit
  approved write-back for AI candidates.
- Keep raw prompts, raw provider outputs, headers, stack traces, and secret
  material out of normal user responses and operator summaries.
- Preserve strict schema validation and reject invalid or incomplete JSON.
- Enforce server-side provider model allowlists, budgets, timeouts, global
  disable controls, and safe error mapping before provider invocation.
- Keep public route exposure, CORS, proxy policy, auth, and deployment changes
  behind separate reviewed tasks.

## Explicit non-goals

This ADR does not:

- implement production integration or a plugin runtime;
- add plugin endpoints, adapter endpoints, production auth, or public routes;
- add AWS resources, Cloudflare/DNS changes, deployment work, or platform work;
- add payment, subscriptions, billing, or entitlement enforcement;
- add a new provider integration, fallback provider, or model routing change;
- add vector databases, embeddings, persistent production indexes, or a new
  indexing service;
- rewrite, vendor, or modify the upstream Vanilla Cookbook UI;
- change current local mock/offline validation or live diagnostic behavior;
- make live OpenAI calls or run browser automation;
- commit raw datasets, indexes, generated artifacts, screenshots, traces,
  secrets, prompts, provider outputs, or local environment values.

## Consequences

The adapter adds an explicit contract and some translation work, but it keeps
canonical data ownership and provider concerns separate. It makes staged native
UI integration possible without forcing a sidecar rewrite into the core app.
The cost is that future implementation tasks must maintain versioned contracts,
scope checks, safe view models, and compatibility tests. That cost is accepted
because seamless UX, data safety, and independent evolution are more important
than a short-term direct connection.
