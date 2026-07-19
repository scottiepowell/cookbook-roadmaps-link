# 0030I-5 Local Live Mode Product Acceptance And Mode Audit

## Goal

Add a focused local product acceptance/audit pass for the AI mode selector after `0030I-4`.

`0030I-4` added shared request-scoped provider-mode routing for importer, recipe sessions, Ask My Cookbook, Dataset Ask, and Meal Planner. This task should prove the integrated local product uses that routing consistently from the UI through the API responses and safe logs.

This is primarily validation, smoke coverage, and small hardening. It may fix minor wiring/copy/test gaps found during the audit, but it should not start AWS/platform work.

## Background

The local product has:

```text
GET /product
GET /product/cookbook
GET /product/ai
GET /demo
```

The AI mode selector should support:

```text
Live OpenAI -> openai / gpt-5.4-nano when explicit live config and budget allow it
Mock offline -> mock / mock-basic
Live selected but unavailable -> safe unavailable message, not silent fallback
```

The only allowed live model is:

```text
gpt-5.4-nano
```

Normal validation must remain offline/mock-only. Manual live validation may run only with explicit local opt-in and safe budget caps.

## Required Work

### 1. Audit the current selector wiring

Inspect:

```text
ai-api/app/ai_mode_routing.py
ai-api/app/routes/ai.py
ai-api/app/recipe_session_routes.py
ai-api/app/static/product.html
ai-api/app/static/product.js
ai-api/app/static/demo.html
ai-api/app/static/demo.js
scripts/start-ai-demo-local.ps1
scripts/demo-ai-mock.ps1
scripts/demo-ai-live-smoke.ps1
scripts/run-openai-demo-evals.ps1
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
README.md
outbox/0030I-4-shared-ai-mode-provider-routing-results.md
```

Confirm:

- `/product` exposes the mode selector/status;
- `/product/ai` preserves mode into `/demo` where practical;
- `/demo` displays the selected mode and allowed model;
- every provider-backed workflow request includes the mode/model preference;
- every provider-backed response shows the actual provider/model used or a safe unavailable reason;
- live unavailable is not silently rendered as successful mock output.

### 2. Add or strengthen mode audit smoke coverage

Create or update a focused script if useful, for example:

```text
scripts/audit-ai-mode-routing-local.ps1
```

or integrate this into `scripts/demo-ai-mock.ps1` if that is cleaner.

The audit should run without live OpenAI by default and assert:

- product shell route is available;
- AI workspace route is available;
- selector exists;
- mock/offline mode is selectable/forceable;
- importer returns mock/mock-basic when mock is selected;
- Recipe Session start/message returns mock/mock-basic when generation occurs;
- Ask My Cookbook returns mock/mock-basic when mock is selected;
- Dataset Ask returns mock/mock-basic when mock is selected;
- Meal Planner returns mock/mock-basic when mock is selected;
- live selected without explicit live config returns safe unavailable metadata/message;
- no raw key/env/path/prompt/provider-response/stack trace leaks.

The script should print a concise pass/fail summary that an operator can read.

### 3. Add an explicit manual live acceptance path

Add documentation and optional script support for a manual live-local acceptance run.

Do not make live calls during normal validation.

Manual live acceptance should require explicit opt-in values such as:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_API_KEY present
OPENAI_MODEL=gpt-5.4-nano
OPENAI_LIVE_TEST_BUDGET_CENTS within 1-25
AI_MAX_OUTPUT_TOKENS within the accepted live wrapper cap
```

The manual live acceptance path should verify at least importer live mode end to end, and, if budget allows, one additional workflow such as Recipe Session Alpha start.

The output should show only safe facts:

- workflow name;
- requested mode/model;
- effective provider/model;
- status;
- citation/retrieval counts if available;
- safe unavailable reason if blocked.

It must not print:

- API keys;
- `.env` values;
- raw prompts;
- raw provider responses;
- local filesystem paths;
- full stack traces.

### 4. Reconcile live startup guidance

Update docs/scripts so a local user understands the difference between:

- normal mock/offline start;
- UI default live selection;
- live selected but unavailable because the local process is mock-only;
- explicit live start/smoke/eval path with budget caps.

If `scripts/start-ai-demo-local.ps1` supports `-Provider openai -EnableLiveTests`, document the exact safe command. If the accepted live token cap differs from the mock default, document the live-safe override.

Do not weaken live budget or token limits.

### 5. Add tests

Add deterministic tests for:

- the audit helper/script, if added;
- UI payloads include mode/model for all provider-backed workflows;
- safe live-unavailable behavior is displayed;
- all workflow schemas accept the shared mode/model preference;
- unsupported provider/model values are rejected or safely warned;
- responses expose effective provider/model safely;
- no raw secrets, env values, local paths, prompts, provider responses, stack traces, or raw dataset content appear.

Do not add tests that require live OpenAI.

### 6. Update docs

Update:

- `docs/local-cookbook-ai-product-integration.md`
- `docs/local-product-acceptance-checklist.md`
- `docs/ai-ui-integration-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/live-openai-smoke-tests.md` if relevant
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Create:

```text
outbox/0030I-5-local-live-mode-product-acceptance-and-mode-audit-results.md
```

The outbox should summarize:

- mode audit performed;
- smoke/script changes;
- workflows verified in mock mode;
- live-unavailable behavior verified;
- manual live acceptance path added or documented;
- any minor fixes made;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- A local mode audit path exists and runs offline/mock-only by default.
- Mock/offline mode is verified across importer, Recipe Session, Ask My Cookbook, Dataset Ask, and Meal Planner.
- Live-selected-without-config is verified as safe unavailable behavior, not silent mock fallback.
- Manual live acceptance guidance exists for `gpt-5.4-nano` with explicit opt-in and budget/token caps.
- UI and API response metadata clearly show requested mode and actual effective provider/model.
- Normal validation remains offline/mock-only.
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

The live wrappers should skip cleanly unless explicitly opted in.

If a manual live acceptance script is added, it must also skip unless explicit live opt-in settings are present.

## Non-Goals

- no arbitrary model picker;
- no AWS resource creation;
- no Terraform;
- no CDK;
- no CloudFormation;
- no DNS or Cloudflare changes;
- no production deployment;
- no production auth;
- no payment implementation;
- no public route exposure;
- no provider-routing overhaul beyond the local shared resolver;
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
git add ai-api docs README.md scripts outbox/0030I-5-local-live-mode-product-acceptance-and-mode-audit-results.md

git commit -m "mailbox: complete task 0030I-5 local live mode product acceptance"

git pull --rebase origin main

git push origin main
```
