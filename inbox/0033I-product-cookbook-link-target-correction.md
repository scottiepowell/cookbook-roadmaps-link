# 0033I Product Cookbook Link Target Correction

## Goal

Fix the product-shell link/handoff to the Vanilla Cookbook app so local and exposed deployments can route users to the correct Cookbook surface without breaking the AI workspace.

This is a focused product-integration correction. Do not change AI provider routing, live token caps, importer schemas, QMD, analytics, ads, SSO/BYOS, payments, AWS/platform work, or public infrastructure in this task.

## Context

Manual live product testing on 2026-07-24 confirmed that the live AI sidecar path is working with `openai` / `gpt-5.4-nano` and `-MaxOutputTokens 800`.

Observed live workflow evidence included:

- `/ai/import-recipe` returned HTTP 200 with provider `openai`, model `gpt-5.4-nano`, `status=ok`, 3 citations, and 3 retrieved examples.
- `/dataset/ask` returned HTTP 200 with provider `openai`, model `gpt-5.4-nano`, `status=ok`, and 2 citations.
- `/ai/meal-plan` returned HTTP 200 with provider `openai`, model `gpt-5.4-nano`, `status=ok`, and 1 citation.
- `/ai/recipe-session/start` and `/ai/recipe-session/{id}/message` returned HTTP 200 with provider `openai`, model `gpt-5.4-nano`, and successful session behavior.
- `/product/cookbook` returned a local 307 redirect, but the local destination did not work for the operator.
- The exposed production Cookbook URL, `https://cookbook.roadmaps.link`, did work, so the app itself appears available and the issue is likely the product shell's local/exposed Cookbook target behavior.

## Required Work

### 1. Inspect current product routing and link configuration

Read:

```text
docs/local-cookbook-ai-product-integration.md
docs/ai-ui-integration-plan.md
docs/manual-product-integration-usability-validation.md
outbox/0033A-manual-product-integration-usability-validation-results.md
docs/ai-live-demo-runbook.md
docs/local-product-acceptance-checklist.md
ai-api/app/main.py
ai-api/app/static/product.html
ai-api/app/static/product.js
ai-api/app/static/product.css
```

Use actual file names if the static product files differ.

### 2. Fix or design the smallest safe correction

The product shell should not hardcode a local Cookbook target in a way that makes the integrated product feel broken after the sidecar starts.

Preferred behavior:

- local development can still point at `http://127.0.0.1:3000/` when the Vanilla Cookbook container is running;
- exposed/browser usage can point at `https://cookbook.roadmaps.link` when appropriate;
- the target should be configurable through a safe non-secret setting if the current architecture supports it;
- the UI should show a friendly explanation if the local Cookbook target is unavailable;
- `/product/ai` should continue to route to `/demo` correctly;
- mock/offline validation should remain deterministic.

Do not proxy or rewrite the upstream Vanilla Cookbook app unless the existing architecture already supports that safely.

### 3. Add tests

Add or update deterministic tests for:

- `/product/cookbook` redirect or target generation;
- configurable Cookbook target behavior if added;
- safe fallback/recovery messaging for local unavailable Cookbook target if testable;
- no leakage of secrets/local env values;
- existing `/product/ai` behavior remains intact;
- mock/offline validation remains unchanged.

### 4. Update docs

Update as appropriate:

```text
README.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The docs should distinguish:

- local Vanilla Cookbook target;
- exposed production Cookbook URL;
- AI sidecar workspace URL;
- what to do when the local Cookbook container is not running.

### 5. Add outbox report

Create:

```text
outbox/0033I-product-cookbook-link-target-correction-results.md
```

The outbox should summarize:

- root cause or likely cause;
- code/docs changed;
- local/exposed Cookbook target behavior;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Product shell no longer feels broken when the local Vanilla Cookbook link target is unavailable.
- Local Cookbook target and exposed Cookbook target behavior are documented.
- `/product/ai` continues to route to `/demo`.
- No AI provider routing or live-call policy is changed.
- No AWS/platform, SSO/BYOS, analytics, ads, payment, QMD, or importer-save behavior is implemented.
- No secrets, prompts, provider outputs, screenshots, traces, local env values, raw datasets, or generated indexes are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

Do not run live OpenAI during normal validation.

## Commit

```bash
git add ai-api scripts docs README.md outbox/0033I-product-cookbook-link-target-correction-results.md
git commit -m "fix: correct product cookbook link target"
git pull --rebase origin main
git push origin main
```
