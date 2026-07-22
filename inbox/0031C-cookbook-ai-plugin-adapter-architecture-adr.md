# 0031C Cookbook AI Plugin Adapter Architecture ADR

## Goal

Design a future architecture for integrating the RAG/AI sidecar into `cookbook.roadmaps.link` as a modular plugin connected through clear adapter interfaces.

The finished product should feel seamless to the end user even if the implementation remains modular behind the scenes.

This is design/ADR only. Do not implement production integration in this task.

## Background

The current local integration keeps Vanilla Cookbook and the AI sidecar separate while presenting them from one local product shell. That boundary has been useful for local validation, provider safety, mock/live routing, Playwright UI QA, and live diagnostics.

The future product direction is to integrate AI/RAG features into the core Cookbook experience without turning the AI layer into tightly coupled application code.

The intended architecture is:

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

## Required Work

### 1. Read current notes and integration docs

Read:

```text
docs/cookbook-ai-plugin-adapter-future-feature.md
docs/local-cookbook-ai-product-integration.md
docs/ai-ui-integration-plan.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
docs/playwright-ui-troubleshooting.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Use those docs as the source of truth for the current local shell, sidecar, mode routing, live/mock boundary, and Playwright QA posture.

### 2. Produce an ADR

Create:

```text
docs/cookbook-ai-plugin-adapter-architecture-adr.md
```

The ADR should cover:

- the problem statement;
- why direct UI/backend coupling is risky;
- why a plugin/adapter boundary is preferred;
- the proposed core app responsibilities;
- the proposed AI sidecar/plugin responsibilities;
- the proposed adapter responsibilities;
- a plugin manifest concept;
- a core Cookbook adapter contract;
- an AI plugin API contract;
- auth/session handoff concept;
- recipe read/write boundary;
- RAG/indexing boundary;
- provider/mock/live boundary;
- UI integration levels;
- seamless end-user UX requirements;
- migration phases;
- contract test strategy;
- security/data boundary requirements;
- explicit non-goals.

### 3. Preserve seamless user experience as a first-class requirement

The ADR must explicitly state that modular internals cannot result in a visibly bolted-on product.

The user-facing target should include:

- consistent navigation;
- consistent visual style, spacing, typography, loading states, and empty states;
- AI actions placed in natural Cookbook workflows;
- no confusing split between core app and AI sidecar in production UX;
- no raw diagnostics shown to normal users;
- operator/debug metadata available only in appropriate support/debug views;
- safe, readable user-facing error messages;
- accessibility and responsive layout considerations for integrated AI panels.

### 4. Define interface sketches

Include sketches for:

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

and adapter concepts such as:

```text
GET    /adapter/recipes
GET    /adapter/recipes/{id}
POST   /adapter/recipes/search
POST   /adapter/recipes/import-candidate
POST   /adapter/recipes/{id}/ai-notes
GET    /adapter/user/context
```

These are design sketches only unless the existing repo already has better names.

### 5. Update planning docs

Update as appropriate:

```text
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
```

Do not disturb active live-diagnostics tasks.

### 6. Add outbox report

Create:

```text
outbox/0031C-cookbook-ai-plugin-adapter-architecture-adr-results.md
```

The outbox should summarize:

- ADR created;
- plugin/adapter direction;
- seamless UX requirement;
- contracts sketched;
- migration phases;
- security/data boundaries;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Future plugin/adapter architecture ADR exists.
- ADR preserves modularity between core Cookbook app, adapter, and RAG/AI sidecar.
- ADR explicitly requires seamless UI integration for end users.
- ADR defines plugin manifest and adapter/API contract sketches.
- ADR defines read/write boundaries for recipes.
- ADR keeps provider keys server-side only.
- ADR preserves mock/offline validation and server-side live gating.
- ADR defines staged migration phases.
- ADR avoids implementation work.
- No secrets, provider outputs, raw prompts, local env values, screenshots, traces, generated artifacts, raw datasets, indexes, or local secret material are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If the full validator is too expensive for this design-only task, run the repository doc/static checks that are already available and record the limitation honestly in the outbox.

## Non-Goals

- no implementation of plugin endpoints;
- no production auth;
- no public route exposure;
- no AWS resources;
- no Cloudflare/DNS changes;
- no payment/subscription work;
- no new provider integration;
- no vector database or embeddings implementation;
- no upstream UI rewrite;
- no browser automation;
- no live OpenAI calls;
- no raw dataset commits.

## Commit

```bash
git add docs README.md outbox/0031C-cookbook-ai-plugin-adapter-architecture-adr-results.md

git commit -m "docs: add cookbook ai plugin adapter architecture adr"

git pull --rebase origin main

git push origin main
```
