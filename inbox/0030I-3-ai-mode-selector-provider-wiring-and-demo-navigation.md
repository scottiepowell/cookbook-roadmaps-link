# 0030I-3 AI Mode Selector Provider Wiring And Demo Navigation

## Goal

Make the local AI mode selector functional end-to-end, not only visible in the UI.

The user can currently see the Live/Mock toggle, but manual testing shows AI calls still use the mock provider after navigating into `/demo` and running the importer:

```text
"endpoint_name":"recipe.import","model":"mock-basic","provider":"mock"
```

This means the selector is not yet reliably wired into the workflow requests or backend provider resolution.

Also add simple internal navigation from `/demo` back to `/product` so users do not need the browser Back button.

## Context

The local product now has:

```text
GET /product
GET /product/cookbook
GET /product/ai
GET /demo
```

`0030I-2` added an AI mode/model selector concept with:

```text
Live OpenAI / Mock offline
gpt-5.4-nano as the only live model
```

Manual validation found two follow-up gaps:

1. The selector appears in the UI, but provider-backed workflow calls still run as mock unless the whole server process was started in mock mode.
2. `/demo` needs a visible navigation link/button back to `/product`.

## Primary Objective

Wire the selected AI mode through the front-end and backend so supported AI workflows actually use the selected mode when safe.

When the user selects Live OpenAI and live configuration is available, provider-backed workflows should call:

```text
provider=openai
model=gpt-5.4-nano
```

When the user selects Mock offline, workflows should call:

```text
provider=mock
model=mock-basic
```

If Live is selected but unavailable, the workflow must fail safely with a clear UI message. It must not silently fall back to mock while implying live was used.

## Required Work

### 1. Inspect current selector implementation

Inspect:

```text
ai-api/app/config.py
ai-api/app/providers/
ai-api/app/importer.py
ai-api/app/rag.py
ai-api/app/dataset_rag.py
ai-api/app/meal_plan.py
ai-api/app/routes/ai.py
ai-api/app/recipe_session_routes.py
ai-api/app/static/product.html
ai-api/app/static/product.js
ai-api/app/static/demo.html
ai-api/app/static/demo.js
ai-api/app/static/demo.css
scripts/start-ai-demo-local.ps1
scripts/demo-ai-mock.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
.env.example
```

Find where the UI selector state is stored and whether workflow requests include it.

Find how provider/model selection currently resolves for:

- structured recipe importer;
- Recipe Session Alpha start/message;
- Ask My Cookbook;
- Dataset Ask/RAG;
- Meal Planner.

### 2. Add safe provider mode request plumbing

Implement the least invasive safe mechanism for per-request or per-session provider preference.

Prefer per-request or browser-session preference over process-global mutable state.

Acceptable request shape examples:

```json
{
  "provider_mode": "openai",
  "model": "gpt-5.4-nano"
}
```

or:

```json
{
  "ai_mode": "live",
  "ai_model": "gpt-5.4-nano"
}
```

Use existing schema naming if already introduced.

Rules:

- only allow `mock` / `offline` and `openai` / `live` modes;
- only allow live model `gpt-5.4-nano`;
- reject or ignore unsafe free-form model names with a safe warning/error;
- do not allow arbitrary provider names;
- do not mutate global provider config from browser actions;
- do not bypass provider budget guards;
- do not bypass live opt-in/config checks;
- do not expose API keys or raw provider errors.

### 3. Add shared backend provider resolution helper if needed

If provider selection is duplicated across routes, add a small shared helper to resolve workflow provider mode safely.

The helper should take:

- server config;
- request/UI preference;
- workflow name if needed;
- budget/live availability state.

It should return safe metadata such as:

- requested_mode;
- effective_provider;
- effective_model;
- live_available;
- safe_unavailable_reason;
- warning messages.

It should never return:

- API keys;
- raw env values;
- local paths;
- raw provider exception bodies;
- raw prompts or responses.

### 4. Wire selector through supported workflows

The selected mode must be used by all provider-backed local demo workflows where feasible:

- `POST /ai/import-recipe`;
- Recipe Session Alpha `POST /ai/recipe-session/start`;
- Recipe Session Alpha `POST /ai/recipe-session/{id}/message` when generation is needed;
- `POST /ai/ask`;
- `POST /dataset/ask`;
- `POST /ai/meal-plan`.

If any route cannot safely support per-request mode yet, surface a clear UI and docs note and add a follow-on recommendation. Do not silently ignore the selector.

### 5. Update the UI so selected mode follows the user into `/demo`

The selected mode from `/product` should carry into `/demo`.

Use safe local browser state or query parameters if appropriate.

Required behavior:

- `/product` selector shows current mode;
- `/product/ai` navigation preserves the selected mode where practical;
- `/demo` shows the selected mode and approved model;
- workflow calls from `/demo` include the selected provider preference;
- response display shows the actual provider/model used;
- if selected mode and actual provider differ, show a safe warning.

### 6. Add `/demo` back navigation to `/product`

Add visible internal navigation on `/demo` such as:

```text
← Back to Cookbook AI Home
```

or:

```text
Product Home
```

Requirements:

- link goes to `/product`;
- it is visible near the top of `/demo`;
- it does not break existing `/demo` tests or layout;
- it does not require the browser Back button.

### 7. Fix local live-start guidance and config mismatch

Manual output currently shows the default start script running:

```text
Provider: mock
Model: mock-basic
Live tests enabled: false
Max output tokens: 500
```

But the live wrappers require:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_API_KEY present
OPENAI_LIVE_TEST_BUDGET_CENTS within 1-25
OPENAI_MODEL configured
AI_MAX_OUTPUT_TOKENS between 1 and 300
```

Document and, if needed, adjust startup guidance so a user understands the difference between:

- normal offline validation/mock mode;
- local product live mode with `gpt-5.4-nano`;
- live smoke/eval wrapper constraints.

If `AI_MAX_OUTPUT_TOKENS=500` conflicts with local live UI expectations, add safe script/docs guidance or validation so live mode uses an allowed cap without breaking mock demo defaults.

Do not weaken live budget or token limits.

### 8. Add tests

Add deterministic offline tests for:

- UI selector state is included in importer request payloads;
- UI selector state is included in Recipe Session start/message request payloads;
- UI selector state is included in Ask My Cookbook, Dataset Ask, and Meal Planner requests where supported;
- backend accepts only the approved live model `gpt-5.4-nano`;
- backend rejects or safely warns on unsupported provider/model values;
- live-selected-but-unavailable returns safe unavailable messaging and does not silently claim mock output is live;
- mock selected still uses mock provider;
- workflow responses include actual provider/model metadata;
- `/demo` contains a link back to `/product`;
- `/product/ai` preserves selected mode where practical;
- no secrets, env values, local paths, raw prompts, raw provider responses, stack traces, or raw dataset content are exposed.

Do not add tests that require live OpenAI.

### 9. Update mock smoke and live wrappers as appropriate

`demo-ai-mock.ps1` must continue forcing or verifying mock/offline behavior.

Add mock-smoke assertions that:

- selector exists;
- mock mode can be selected or forced;
- workflow output reports mock provider/model;
- `/demo` back-to-product link exists.

Live smoke/eval wrappers should still skip unless explicitly opted in.

### 10. Update docs

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
outbox/0030I-3-ai-mode-selector-provider-wiring-and-demo-navigation-results.md
```

The outbox should summarize:

- root cause of selector not affecting provider-backed calls;
- provider-mode request plumbing added;
- workflows wired;
- live unavailable behavior;
- `/demo` back navigation;
- tests and smoke updates;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Selecting Live OpenAI in the UI causes supported provider-backed workflows to request `openai` with `gpt-5.4-nano` when live config and budget allow it.
- Selecting Mock offline causes supported provider-backed workflows to use `mock` / `mock-basic`.
- Live selected but unavailable produces safe UI/API messaging and does not silently pretend mock output is live.
- Workflow responses display the actual provider/model used.
- Unsupported provider/model choices are rejected or safely warned.
- `/demo` has visible navigation back to `/product`.
- `/product/ai` preserves selected mode into `/demo` where practical.
- Automated validation remains offline/mock-only.
- No live OpenAI calls are required for normal validation.
- Existing `/product`, `/product/cookbook`, `/product/ai`, `/demo`, and Recipe Session Alpha behavior remains intact.
- No secrets, env values, raw provider prompts, raw provider responses, local paths, stack traces, raw dataset content, or API keys are exposed.
- No AWS/platform work is implemented.
- No arbitrary model picker is added.

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
- no provider-routing overhaul beyond the narrow selector plumbing needed here;
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
git add ai-api docs README.md scripts outbox/0030I-3-ai-mode-selector-provider-wiring-and-demo-navigation-results.md

git commit -m "mailbox: complete task 0030I-3 ai mode selector provider wiring"

git pull --rebase origin main

git push origin main
```
