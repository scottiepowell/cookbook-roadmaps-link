# 0030I-4R Complete AI Mode Route/UI Wiring

## Goal

Correct the incomplete `0030I-4` implementation by wiring the shared AI mode resolver into every provider-backed workflow and attaching the UI selector state to every workflow request payload.

This is a corrective implementation task. It must be completed before any `0030I-5` local live-mode acceptance/audit task claims success.

## Background

A follow-up audit found that `0030I-4` created shared AI mode schema/resolver pieces, but did not complete the end-to-end wiring:

- `resolve_ai_mode` exists but is not invoked by the routes/workflows;
- only importer interprets `provider_mode`;
- `/demo` defines `providerPreference()` but does not attach it to workflow request payloads;
- Ask My Cookbook, Dataset Ask, Meal Planner, and Recipe Session still resolve the process-wide provider.

Therefore the AI mode selector is not yet functional across the full local product. Do not create a misleading acceptance report until this is fixed.

## Scope

Finish request-scoped provider routing for all local provider-backed workflows used by the demo UI:

```text
POST /ai/import-recipe
POST /ai/recipe-session/start
POST /ai/recipe-session/{interaction_id}/message when generation is needed
POST /ai/ask
POST /dataset/ask
POST /ai/meal-plan
```

The only approved live model remains:

```text
gpt-5.4-nano
```

Mock/offline remains:

```text
mock-basic
```

Normal validation must remain offline/mock-only.

## Required Work

### 1. Confirm the incomplete wiring

Inspect:

```text
ai-api/app/ai_mode_routing.py
ai-api/app/routes/ai.py
ai-api/app/recipe_session_routes.py
ai-api/app/importer.py
ai-api/app/rag.py
ai-api/app/dataset_rag.py
ai-api/app/meal_plan.py
ai-api/app/static/demo.js
ai-api/app/static/product.js
ai-api/app/schemas.py
scripts/demo-ai-mock.ps1
outbox/0030I-4-shared-ai-mode-provider-routing-results.md
```

Use searches such as:

```powershell
rg -n "resolve_ai_mode|providerPreference|provider_mode|ai_model|ai_mode|AI_PROVIDER|get_provider" ai-api/app scripts
```

Document the root cause in the outbox.

### 2. Wire the shared resolver into routes/workflows

Ensure the shared resolver is invoked by every supported provider-backed route or route helper, not merely present in request schemas.

For each workflow, the implementation must use the request-scoped provider preference when deciding the effective provider/model:

- importer;
- Recipe Session Alpha start;
- Recipe Session Alpha follow-up when generation is needed;
- Ask My Cookbook;
- Dataset Ask/RAG;
- Meal Planner.

Requirements:

- mock/offline request -> `provider=mock`, `model=mock-basic`;
- live/openai request -> `provider=openai`, `model=gpt-5.4-nano` only when live opt-in/config/budget allow it;
- live unavailable -> controlled safe response/warning, not silent mock fallback;
- unsupported provider/model -> rejected or safe warning;
- actual response metadata must show effective provider/model and any safe unavailable reason.

Do not mutate process-global provider settings from browser requests.

### 3. Attach UI selector state to every workflow request

Update `/demo` JavaScript so `providerPreference()` or the equivalent selector helper is included in every provider-backed request payload:

- importer/create;
- Recipe Session Alpha start;
- Recipe Session Alpha message;
- Ask My Cookbook;
- Dataset Ask/RAG;
- Meal Planner.

If `/product/ai` preserves selected mode into `/demo`, keep that behavior intact.

The UI should not silently ignore the selected mode.

### 4. Preserve safety gates

Browser selection alone must not make live OpenAI calls possible.

Live mode still requires:

- explicit live opt-in;
- API key/configuration present;
- allowed model `gpt-5.4-nano`;
- existing budget/token caps;
- provider budget guard approval where applicable.

Do not expose:

- API keys;
- `.env` values;
- raw provider errors;
- raw prompts;
- raw provider responses;
- local filesystem paths;
- stack traces;
- raw dataset contents.

### 5. Add focused regression tests

Add tests proving this corrective wiring is real.

At minimum, cover:

- `resolve_ai_mode` is invoked or its effective decision is observable for Ask My Cookbook;
- Dataset Ask honors requested mock/live-unavailable mode;
- Meal Planner honors requested mock/live-unavailable mode;
- Recipe Session start honors requested mock/live-unavailable mode;
- Recipe Session follow-up generation honors requested mode;
- `/demo` JavaScript attaches selector preference to every provider-backed request payload;
- unsupported model/provider choices are rejected or safely warned;
- live selected without config produces safe unavailable behavior and does not silently return successful mock output as if live;
- response metadata exposes actual effective provider/model safely;
- no secret/env/path/prompt/provider-response/stack-trace leakage.

Do not add tests requiring live OpenAI.

### 6. Update mock smoke

Update `scripts/demo-ai-mock.ps1` so it validates selector plumbing across the workflows without live calls.

The smoke should verify:

- selector exists;
- mock mode can be forced;
- importer reports mock/mock-basic;
- Recipe Session generation reports mock/mock-basic;
- Ask My Cookbook reports mock/mock-basic;
- Dataset Ask reports mock/mock-basic;
- Meal Planner reports mock/mock-basic;
- live wrappers still skip without opt-in.

### 7. Update docs

Update as needed:

- `docs/local-cookbook-ai-product-integration.md`;
- `docs/local-product-acceptance-checklist.md`;
- `docs/ai-ui-integration-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md`.

Create:

```text
outbox/0030I-4R-complete-ai-mode-route-ui-wiring-results.md
```

The outbox must summarize:

- the incomplete `0030I-4` finding;
- route/workflow wiring added;
- UI payload wiring added;
- live unavailable behavior;
- tests and smoke updates;
- validation results;
- explicit non-goals;
- whether `0030I-5` can now run.

## Acceptance Criteria

- Shared AI mode resolver is actually invoked by supported provider-backed workflows.
- `/demo` includes selector state in importer, Recipe Session, Ask, Dataset Ask, and Meal Planner payloads.
- Mock selected uses `mock/mock-basic` across all supported workflows.
- Live selected requests `openai/gpt-5.4-nano` only when live config and budget allow it.
- Live selected but unavailable returns safe unavailable metadata/message and does not silently fall back to mock as success.
- Unsupported provider/model values are rejected or safely warned.
- Response metadata shows actual effective provider/model safely.
- Mock smoke proves cross-workflow mock mode behavior.
- Normal validation remains offline/mock-only.
- No live OpenAI calls are required for normal validation.
- No arbitrary model picker, AWS/platform work, public route exposure, production auth/payment, secondary provider runtime, vector DB, embeddings, upstream UI rewrite, screenshots, browser automation, raw dataset commits, persistent indexes, or disk cache are added.

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

The live wrappers should skip cleanly unless explicitly opted in.

## Non-Goals

- no arbitrary model picker;
- no AWS resource creation;
- no Terraform/CDK/CloudFormation;
- no DNS or Cloudflare changes;
- no production deployment;
- no production auth;
- no payment implementation;
- no public route exposure;
- no secondary-provider runtime;
- no vector database;
- no embeddings;
- no upstream Vanilla Cookbook vendoring;
- no full upstream UI rewrite;
- no live OpenAI calls during normal validation;
- no screenshots or browser automation;
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-4R-complete-ai-mode-route-ui-wiring-results.md

git commit -m "mailbox: complete task 0030I-4R complete ai mode route ui wiring"

git pull --rebase origin main

git push origin main
```
