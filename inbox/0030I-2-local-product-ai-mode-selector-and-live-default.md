# 0030I-2 Local Product AI Mode Selector And Live Default

## Goal

Add a local product front-end AI mode/model selector so the integrated Cookbook AI UI can run as a more realistic end-user product: live OpenAI by default when safely configured, with an explicit mock/offline toggle available for demos, testing, and cost-free validation.

The only live model choice for now should be the approved project model:

```text
gpt-5.4-nano
```

This task should make the local product experience clearer without adding arbitrary model choice, production public exposure, payment, AWS infrastructure, or unbounded provider use.

## Background

The local product shell and AI sidecar are now integrated around:

```text
GET /product
GET /product/cookbook
GET /product/ai
GET /demo
```

The current local product default has been mock/offline for safety. That was appropriate during hardening, but a finalized local product should let a user intentionally run the live AI path from the UI, with one approved live model and clear cost/safety boundaries.

The user-facing product behavior should be:

- default selected mode: live OpenAI;
- only live model option: `gpt-5.4-nano`;
- user can toggle to mock/offline mode;
- if live is selected but not configured, show a clear safe configuration/budget message and do not leak secrets;
- normal automated validation remains mock/offline and must not make live OpenAI calls.

## Primary Objective

Add a safe UI/runtime mode selector to the local AI product experience.

The UI should allow:

```text
AI mode: Live OpenAI / Mock offline
Model: gpt-5.4-nano
```

The selector must make the current mode obvious before the user runs importer, recipe-session, Ask, Dataset Ask, or Meal Planner flows.

## Required Work

### 1. Inspect existing provider configuration

Inspect the current provider and budget flow before changing UI behavior:

```text
ai-api/app/config.py
ai-api/app/providers/
ai-api/app/routes/ai.py
ai-api/app/recipe_session_routes.py
ai-api/app/static/demo.html
ai-api/app/static/demo.js
ai-api/app/static/product.html
ai-api/app/static/product.js
scripts/start-ai-demo-local.ps1
scripts/demo-ai-mock.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
.env.example
```

Identify how `AI_PROVIDER`, `OPENAI_ENABLE_LIVE_TESTS`, `OPENAI_MODEL`, budget caps, token caps, and provider config are currently applied.

Do not bypass the existing budget guard or live-call safety checks.

### 2. Add a UI mode selector

Add a visible AI mode selector to the local product/AI UI.

Preferred locations:

- `/product`: compact high-level selector/status card;
- `/demo`: workflow-level selector/status that affects AI calls from the AI workspace.

The UI should show:

```text
Mode: Live OpenAI | Mock offline
Live model: gpt-5.4-nano
```

Rules:

- live should be the default selected user-facing option;
- mock/offline should remain selectable;
- only `gpt-5.4-nano` should be selectable as a live model;
- do not add a free-form model picker;
- do not expose API keys, env values, raw provider errors, raw prompts, or raw provider responses.

### 3. Decide safe request/runtime behavior

Implement the least invasive safe mechanism for the selected UI mode.

Acceptable approaches:

#### Option A: Client-sent mode preference

The UI sends a safe explicit provider preference with workflow requests, for example:

```json
{
  "provider_mode": "openai",
  "model": "gpt-5.4-nano"
}
```

or an equivalent safe header/query parameter if that better fits existing endpoint patterns.

#### Option B: Session/UI-local preference

The UI stores the selected mode in local browser state and each request uses the selected mode when calling the sidecar.

#### Option C: Server setting plus UI display

If the existing runtime provider is process-wide only, document that limitation and implement UI selection as a safe local control only where endpoint design allows it. Do not introduce global mutable provider state that can race across users.

Prefer a per-request or per-session mode over process-global mutation.

### 4. Preserve validation safety

Even though the product UI default should be live, automated validation must remain mock/offline unless explicitly opted in.

Requirements:

- `scripts/demo-ai-mock.ps1` must force or verify mock/offline behavior;
- offline evals must not call live OpenAI;
- Git Bash validator must not call live OpenAI;
- live smoke/eval wrappers remain explicit opt-in;
- if live mode is unavailable in local UI due to missing key or budget config, the UI shows a safe unavailable/configuration message.

### 5. Add safe live readiness state

Extend readiness/config responses if needed so the UI can show safe live availability.

The UI should be able to distinguish:

```text
Live selected and available
Live selected but missing configuration
Live selected but budget disabled/exhausted
Mock selected and active
```

Safe readiness metadata may include:

- current selected mode;
- configured default mode;
- available modes;
- allowed live model list containing only `gpt-5.4-nano`;
- live availability status;
- safe unavailable reason category.

Do not include:

- raw API key;
- full env values;
- filesystem paths;
- raw provider exception body;
- stack traces;
- raw prompts or responses.

### 6. Update workflow calls

Ensure the selected mode is respected, or clearly documented if a workflow cannot yet support per-request provider selection.

Cover:

- structured recipe importer;
- Recipe Session Alpha start/message flows;
- Ask My Cookbook;
- Dataset Ask/RAG;
- Meal Planner.

If a route cannot support live/mock switching yet, surface a clear UI note and add a follow-on task recommendation rather than silently ignoring the selector.

### 7. UX copy

Use clear end-user wording.

Examples:

```text
Live OpenAI uses the approved gpt-5.4-nano model and may use API budget.
```

```text
Mock offline is free and deterministic for local demos.
```

```text
Live mode is selected but unavailable because live provider settings are not configured.
```

```text
Only gpt-5.4-nano is available for this product. Users cannot choose arbitrary models.
```

### 8. Add tests

Add deterministic tests for:

- UI renders the AI mode selector;
- live OpenAI is the default selected product option;
- model list contains only `gpt-5.4-nano`;
- mock/offline toggle is available;
- unsafe/free-form model names are not accepted;
- readiness/config metadata is safe;
- live unavailable state is displayed safely when no live config exists;
- mock smoke continues to force mock/offline and does not make live calls;
- existing `/product`, `/product/ai`, `/demo`, and Recipe Session Alpha tests still pass;
- no raw secrets, env values, local paths, prompts, provider responses, or stack traces appear in UI/config responses.

### 9. Update docs

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
outbox/0030I-2-local-product-ai-mode-selector-and-live-default-results.md
```

The outbox should summarize:

- UI selector added;
- live default behavior;
- mock toggle behavior;
- approved model restriction;
- safe live unavailable/budget behavior;
- tests added;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Local product UI includes an AI mode selector.
- Live OpenAI is the default selected user-facing mode.
- The only live model option is `gpt-5.4-nano`.
- Mock/offline mode remains available and clear.
- Automated validation remains offline/mock-only.
- UI and config/readiness responses never expose secrets, env values, prompts, raw provider responses, stack traces, local paths, or raw dataset content.
- Existing `/product`, `/product/cookbook`, `/product/ai`, and `/demo` behavior remains intact.
- Recipe Session Alpha remains functional.
- Live calls are still gated by explicit safe configuration and budget controls.
- No arbitrary/free-form model picker is added.
- No AWS/platform work is implemented.
- No production auth, payment, public route exposure, upstream UI rewrite, provider-routing overhaul, secondary provider runtime, vector DB, embeddings, screenshots, browser automation, raw dataset, persistent index, or disk cache work is added.

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
- no provider-routing overhaul;
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
git add ai-api docs README.md scripts outbox/0030I-2-local-product-ai-mode-selector-and-live-default-results.md

git commit -m "mailbox: complete task 0030I-2 local product ai mode selector"

git pull --rebase origin main

git push origin main
```
