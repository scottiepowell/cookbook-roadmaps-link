# 0030I-4 Shared AI Mode Provider Routing

## Goal

Extend the local AI mode selector from importer-only provider preference into a shared, safe provider-routing layer for all local provider-backed AI workflows.

`0030I-3` proved the selector can drive `POST /ai/import-recipe` through a narrow request-scoped provider preference and added `/demo` navigation back to `/product`. It also documented an important limitation: other provider-backed routes still use the existing process-scoped provider configuration.

This task should close that gap without introducing unsafe global provider mutation, public exposure, production auth, payment, AWS/platform work, or live calls during normal validation.

## Context

Current local product routes:

```text
GET /product
GET /product/cookbook
GET /product/ai
GET /demo
```

Current expected AI mode behavior:

```text
Live OpenAI selected -> request openai with gpt-5.4-nano when live config and budget allow it
Mock offline selected -> request mock with mock-basic
Live selected but unavailable -> safe unavailable response/message, not silent mock fallback
```

The only allowed live model remains:

```text
gpt-5.4-nano
```

## Primary Objective

Create a shared request-scoped AI mode/provider routing helper and wire it through all local provider-backed workflows used by the product UI:

```text
POST /ai/import-recipe
POST /ai/recipe-session/start
POST /ai/recipe-session/{interaction_id}/message when generation is needed
POST /ai/ask
POST /dataset/ask
POST /ai/meal-plan
```

The selector should no longer be importer-only.

## Required Work

### 1. Inspect current 0030I-3 implementation

Inspect:

```text
ai-api/app/config.py
ai-api/app/providers/
ai-api/app/routes/ai.py
ai-api/app/recipe_session_routes.py
ai-api/app/importer.py
ai-api/app/rag.py
ai-api/app/dataset_rag.py
ai-api/app/meal_plan.py
ai-api/app/static/demo.html
ai-api/app/static/demo.js
ai-api/app/static/product.html
ai-api/app/static/product.js
ai-api/tests
scripts/demo-ai-mock.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
.env.example
outbox/0030I-3-ai-mode-selector-provider-wiring-and-demo-navigation-results.md
```

Find:

- the importer-specific provider preference added in `0030I-3`;
- where route schemas accept provider/mode/model preferences;
- which routes still read process-wide `AI_PROVIDER` only;
- where budget guards and live enablement checks happen;
- where response provider/model metadata is produced.

### 2. Add a shared request-scoped provider routing helper

Create or refactor into a small shared helper, for example:

```text
ai-api/app/ai_mode_routing.py
```

Use existing naming if a suitable helper already exists.

The helper should resolve:

- requested mode/provider;
- requested model;
- effective provider;
- effective model;
- live availability;
- safe unavailable reason;
- warnings;
- whether the workflow may call the provider.

Allowed modes/providers:

```text
mock
offline
live
openai
```

Allowed live model:

```text
gpt-5.4-nano
```

Allowed mock model:

```text
mock-basic
```

Reject or safely warn for:

- arbitrary provider names;
- arbitrary model names;
- missing live key/config;
- live selected without explicit live enablement;
- live selected when budget guard blocks the call.

Do not expose:

- API keys;
- raw env values;
- local filesystem paths;
- raw provider exceptions;
- raw prompts;
- raw provider responses;
- stack traces.

### 3. Preserve explicit live gating and budget boundaries

Do not make browser selection alone sufficient to call OpenAI.

Live mode must still require existing safe live configuration, including the current explicit live opt-in settings and budget/token caps.

If live is selected but unavailable, return a safe controlled response or warning. Do not silently fall back to mock while claiming live mode was used.

### 4. Wire all provider-backed local workflows

Wire the shared routing helper into:

```text
POST /ai/import-recipe
POST /ai/recipe-session/start
POST /ai/recipe-session/{interaction_id}/message when generation is needed
POST /ai/ask
POST /dataset/ask
POST /ai/meal-plan
```

Requirements:

- mock selection results in `provider=mock`, `model=mock-basic`;
- live selection requests `provider=openai`, `model=gpt-5.4-nano` when allowed;
- live unavailable produces safe metadata/warnings;
- response metadata shows the actual effective provider/model;
- selected mode is not ignored for any supported route;
- routes that cannot yet support per-request routing must be explicitly documented with a follow-on task, but prefer to wire all routes in this task.

### 5. Update the front end to pass selector state to every workflow

Update `/demo` JavaScript so the current selector state is included in all provider-backed workflow requests:

- importer/create;
- Recipe Session Alpha start;
- Recipe Session Alpha message when generation can occur;
- Ask My Cookbook;
- Dataset Ask/RAG;
- Meal Planner.

The UI should show:

- selected mode;
- allowed model;
- actual provider/model used in the response;
- warning if selected live mode was unavailable or blocked;
- no mismatch where mock output appears as live.

Keep `/demo` back navigation to `/product`.

### 6. Add tests

Add deterministic offline tests for:

- shared routing helper accepts mock mode;
- shared routing helper accepts live mode only with `gpt-5.4-nano`;
- unsupported provider/model values are rejected or safely warned;
- live selected without live configuration fails safely;
- importer still honors selected mode;
- Recipe Session start/message includes and honors selected mode;
- Ask My Cookbook includes and honors selected mode;
- Dataset Ask includes and honors selected mode;
- Meal Planner includes and honors selected mode;
- UI JavaScript includes selector state in every provider-backed request payload;
- responses expose actual effective provider/model safely;
- no secret/env/path/prompt/provider-response leakage;
- `/demo` back-to-product link remains present.

Do not add tests that require live OpenAI.

### 7. Update mock smoke

Update `scripts/demo-ai-mock.ps1` so it verifies:

- selector exists;
- mock/offline mode can be forced or is respected for smoke;
- importer reports mock/mock-basic;
- Recipe Session Alpha reports mock/mock-basic when generation occurs;
- Ask My Cookbook, Dataset Ask, and Meal Planner remain mock/offline during smoke;
- live wrappers still skip unless explicitly opted in.

### 8. Update docs

Update:

- `docs/local-cookbook-ai-product-integration.md`;
- `docs/local-product-acceptance-checklist.md`;
- `docs/ai-ui-integration-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/live-openai-smoke-tests.md` if relevant;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md`.

Create:

```text
outbox/0030I-4-shared-ai-mode-provider-routing-results.md
```

The outbox should summarize:

- importer-only limitation from `0030I-3`;
- shared routing helper added;
- workflows wired;
- UI request payload updates;
- live unavailable behavior;
- tests and smoke updates;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A shared request-scoped AI mode/provider routing helper exists.
- All supported provider-backed local workflows honor the selected AI mode.
- Mock selected uses mock/mock-basic.
- Live selected requests OpenAI/gpt-5.4-nano only when live config and budget allow it.
- Live selected but unavailable fails safely or reports safe unavailable metadata; it does not silently pretend mock output is live.
- Workflow responses expose actual effective provider/model safely.
- UI sends selector state for importer, Recipe Session Alpha, Ask My Cookbook, Dataset Ask, and Meal Planner.
- `/demo` navigation back to `/product` remains available.
- Automated validation remains offline/mock-only.
- No live OpenAI calls are required for normal validation.
- No arbitrary model picker is added.
- No AWS/platform work is implemented.
- No secrets, env values, raw prompts, raw provider responses, stack traces, local paths, or raw dataset content are exposed.

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

The mock demo and validator must not call live OpenAI.

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest is run and fails due to the known local `pytest-of-scott` temp ACL issue, document that separately and rely on Git Bash validation if it passes.

## Non-Goals

- no arbitrary model picker;
- no multiple live model choices;
- no AWS resource creation;
- no Terraform;
- no CDK;
- no CloudFormation;
- no DNS or Cloudflare changes;
- no production deployment;
- no production auth;
- no payment implementation;
- no public route exposure;
- no provider-routing overhaul beyond the local request-scoped selector;
- no secondary-provider runtime;
- no vector database;
- no embeddings;
- no upstream Vanilla Cookbook vendoring;
- no full upstream UI rewrite;
- no production database migrations;
- no persistent production memory;
- no screenshots;
- no browser automation;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-4-shared-ai-mode-provider-routing-results.md

git commit -m "mailbox: complete task 0030I-4 shared ai mode provider routing"

git pull --rebase origin main

git push origin main
```
