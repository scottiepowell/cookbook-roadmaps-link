# 0030I-7 Playwright UI Troubleshooting Harness

## Goal

Add a local Playwright-based UI troubleshooting harness for the Cookbook AI sidecar product shell and AI workspace.

This task is intended to make recurring UI issues observable and repeatable, especially the Live/OpenAI versus Mock/offline toggle drift that has affected `/product` and `/demo`.

This is local development tooling only. It does not replace backend pytest coverage, mock smoke, or offline evals.

## Context

The local Cookbook AI product now has:

```text
GET /product
GET /product/cookbook
GET /product/ai
GET /demo
```

Recent work added:

- `/product` as the local integrated product shell;
- `/demo` as the AI workspace;
- a Live/Mock mode selector;
- normalized UI mode/model preferences;
- request-scoped provider routing across importer, Recipe Session, Ask, Dataset Ask, and Meal Planner;
- safe 503/unavailable behavior when Live is selected but the server was not started with valid live config;
- explicit mock smoke assertions.

The remaining problem is that DOM/browser state, localStorage, cached JavaScript, redirect behavior, and visual layout can still drift in ways backend tests do not catch.

## Primary Objective

Introduce a repo-local Playwright troubleshooting harness that can inspect and prove the browser-facing behavior of:

- `/product`;
- `/product/ai` redirect into `/demo`;
- `/demo` mode selector;
- Live/OpenAI versus Mock/offline normalization;
- request payload mode/model fields;
- safe live-unavailable UI messaging;
- visible navigation from `/demo` back to `/product`;
- layout overflow and clipping checks.

## Important Operator Note

A Codex Playwright Interactive Skill may be useful for manual, persistent-browser debugging, but it should not be the only solution.

For repeatable project validation, add repo-local Playwright scripts/tests that can run without depending on a persistent Codex session.

If documenting the interactive skill, keep it clearly optional and local-only.

## Required Work

### 1. Inspect current JavaScript and UI behavior

Inspect:

```text
ai-api/app/static/product.html
ai-api/app/static/product.css
ai-api/app/static/product.js
ai-api/app/static/demo.html
ai-api/app/static/demo.css
ai-api/app/static/demo.js
scripts/start-ai-demo-local.ps1
scripts/demo-ai-mock.ps1
scripts/lib/ai-env-file.ps1
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-ui-integration-plan.md
docs/ai-live-demo-runbook.md
```

Identify:

- where mode state is stored;
- whether `/product` and `/demo` share the same state key;
- whether stale `live` aliases can persist;
- whether `/demo` normalizes `live/openai` and `mock/offline` before dispatch;
- which fetch calls carry provider mode/model preference;
- where safe unavailable messages are rendered.

### 2. Add repo-local Playwright tooling

Add a minimal local Playwright setup.

Preferred files:

```text
package.json
package-lock.json
playwright.config.ts or playwright.config.js
tests/ui/cookbook-ai-mode.spec.ts
scripts/run-ui-playwright.ps1
```

If the repo already has a Node/package convention, follow it instead.

Keep the install small and local:

- prefer Chromium-only for the first implementation unless multi-browser coverage is explicitly needed;
- do not download browser binaries during normal backend validation;
- do not add Playwright to Python requirements;
- do not require live OpenAI for normal UI tests.

The Playwright install flow may be documented as:

```powershell
npm install
npx playwright install chromium
```

or another equivalent local setup.

### 3. Add UI troubleshooting tests

Create Playwright tests that assume the local sidecar is already running at:

```text
http://127.0.0.1:8000
```

The tests should cover:

#### Product shell

- `/product` loads successfully;
- product shell title/primary content is visible;
- Live/Mock selector is visible;
- readiness area is visible;
- no horizontal overflow at a normal desktop viewport;
- action buttons stay inside visible card regions where practical;
- `/product/ai` navigates to `/demo`;
- `/product/cookbook` redirects or points to the configured local Cookbook target without rewriting production routes.

#### Mode selector state

- selecting Mock/offline persists or propagates to `/demo`;
- selecting Live/OpenAI persists or propagates to `/demo`;
- stale alias `live` is normalized to `openai/gpt-5.4-nano` before request dispatch;
- `mock/offline` is normalized to `mock/mock-basic` before request dispatch;
- no arbitrary model picker exists;
- only `gpt-5.4-nano` appears as the live model.

#### Request payload inspection

Use Playwright request interception or route monitoring to verify that provider-backed requests include normalized fields.

Cover:

```text
POST /ai/import-recipe
POST /ai/recipe-session/start
POST /ai/recipe-session/{interaction_id}/message when feasible
POST /ai/ask
POST /dataset/ask
POST /ai/meal-plan
```

Required assertions:

- Mock-selected payloads include `provider_mode=mock` or equivalent normalized field;
- Mock-selected payloads include `ai_model=mock-basic` or equivalent normalized field;
- Live-selected payloads include `provider_mode=openai` or equivalent normalized field;
- Live-selected payloads include `ai_model=gpt-5.4-nano` or equivalent normalized field;
- no payload contains `OPENAI_API_KEY`, raw env values, raw prompts beyond the intended user input field, or stack traces.

#### Live unavailable UX

When the server is started in normal mock/offline mode:

- selecting Live/OpenAI and submitting importer should receive controlled unavailable behavior;
- UI should display safe unavailable guidance;
- UI should not render mock output as if it were live;
- UI should not expose raw provider errors, environment values, keys, paths, prompts, or stack traces.

#### Mock path UX

When Mock/offline is selected:

- importer succeeds with mock output;
- response metadata shows `mock/mock-basic`;
- Recipe Session start/follow-up works in mock mode where feasible;
- Ask, Dataset Ask, and Meal Planner can be exercised lightly or via request-payload checks without consuming live API budget.

### 4. Add optional visual artifacts without committing them

Configure Playwright output so screenshots, traces, videos, and test-results are ignored.

Update `.gitignore` if needed for:

```text
test-results/
playwright-report/
ui-artifacts/
*.webm
```

Do not commit screenshots or trace zips unless a future task explicitly asks for an artifact.

### 5. Add an operator run script

Create:

```text
scripts/run-ui-playwright.ps1
```

The script should:

- check that Node/npm are available;
- check that the local sidecar responds on `http://127.0.0.1:8000/product`;
- run the Playwright UI tests;
- print concise guidance if the sidecar is not running;
- never start live OpenAI automatically;
- never print secrets.

Example operator flow:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
# second terminal
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

### 6. Optional: document Codex Playwright Interactive Skill separately

If useful, add a local-only troubleshooting section to docs that explains the optional Codex Playwright Interactive Skill.

Important guidance:

- use it only for manual troubleshooting;
- run from the project directory;
- prefer `127.0.0.1` over `localhost`;
- use a persistent browser session for visual inspection;
- treat `--sandbox danger-full-access` as a high-trust local debugging mode, not a default project requirement;
- do not paste or expose secrets;
- do not commit skill configuration that belongs under `%USERPROFILE%\.codex\skills\`;
- do not require the skill for normal validation.

### 7. Add tests/docs safeguards

Add or update deterministic checks so committed files do not include:

```text
OPENAI_API_KEY=<real value>
sk-proj-
sk_live_
sk_test_
Authorization: Bearer
raw_provider_response
raw_provider_prompt
```

Add docs/tests that say:

- Playwright UI troubleshooting is optional/local;
- normal validation remains mock/offline;
- live OpenAI is not required for UI troubleshooting;
- Playwright artifacts remain ignored;
- browser automation is now allowed only for local UI QA and not for production deployment work.

### 8. Update docs

Update:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-ui-integration-plan.md
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Create if useful:

```text
docs/playwright-ui-troubleshooting.md
```

Create outbox:

```text
outbox/0030I-7-playwright-ui-troubleshooting-harness-results.md
```

The outbox should summarize:

- why Playwright was added;
- repo-local tooling added;
- UI coverage added;
- optional Codex interactive skill guidance if documented;
- artifacts ignored;
- validation results;
- explicit non-goals;
- remaining UI troubleshooting follow-ups.

## Acceptance Criteria

- Repo-local Playwright UI troubleshooting harness exists.
- Operator can run a script to test `/product` and `/demo` in a real browser.
- Tests verify mode selector visibility and propagation.
- Tests verify request payloads carry normalized provider/model preferences.
- Tests verify Live-selected-on-mock-server shows safe unavailable UI behavior.
- Tests verify Mock/offline path still works without live OpenAI.
- Tests check for layout overflow/clipping at a normal desktop viewport.
- `/demo` back-to-product navigation remains visible.
- Playwright screenshots/traces/videos are ignored and not committed.
- Normal validation remains offline/mock-only.
- No live OpenAI call is required for normal UI troubleshooting.
- No real `.env`, API key, token, key fragment, provider output, screenshot, trace, video, generated artifact, or local secret material is committed.
- No AWS/platform work, production auth, payment, public route exposure, Cloudflare/DNS change, secondary-provider runtime, vector DB, embeddings, upstream UI rewrite, raw dataset commit, persistent index, or disk cache is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
npm install
npx playwright install chromium
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
# second terminal
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

Then run normal validation:

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

The live smoke/eval wrappers should skip unless explicitly opted in.

Do not run live OpenAI during normal validation.

## Non-Goals

- no live OpenAI call requirement;
- no browser automation in normal backend-only validator unless explicitly added later;
- no committed Playwright artifacts;
- no committed Codex user skill config;
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
- no raw dataset commits;
- no generated persistent indexes;
- no disk cache.

## Commit

```bash
git add package.json package-lock.json playwright.config.* tests scripts docs README.md .gitignore outbox/0030I-7-playwright-ui-troubleshooting-harness-results.md

git commit -m "mailbox: complete task 0030I-7 playwright ui troubleshooting harness"

git pull --rebase origin main

git push origin main
```
