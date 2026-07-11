# 0030L Live Importer Eval Output Cap And Safe Diagnostics

## Goal

Harden the live OpenAI importer eval so it becomes a reliable baseline before starting `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness`.

The current live eval path successfully runs in OpenAI mode through the `.env` loader and passes most workflows, but the importer workflow fails with a generic `RecipeImportProviderError` even when latency is below threshold. The likely cause is that the integrated live eval caps `AI_MAX_OUTPUT_TOKENS` at `300`, while the importer must return a full structured recipe draft JSON.

## Observed Behavior

A live run with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env
```

loaded the local `.env`, entered live mode, and ran all workflows.

Observed summary:

```text
status=failed workflows=5/6 tokens=791 estimated_cost_usd=0.00033145
```

Passing workflows:

```text
readiness
ask_my_cookbook
dataset_search
dataset_ask
meal_plan
```

Failing workflow:

```text
importer failed with RecipeImportProviderError
```

The second run had importer latency around 4503ms, zero threshold warnings, and zero threshold failures, so this is not primarily a latency-threshold failure.

The importer response file contained only:

```json
{
  "error": "Recipe importer provider failed."
}
```

## Context

Current code observations:

- `scripts/live-openai-demo-evals.py` enforces `MAX_OUTPUT_TOKENS_LIMIT = 300` for live eval runs.
- The live eval suite dispatches the importer workflow through `import_recipe_text(RecipeImportRequest(...), provider=provider)`.
- `import_recipe_text` wraps provider failures as `RecipeImportProviderError("Recipe importer provider failed.")`.
- `OpenAIProvider.generate_structured` already classifies invalid/incomplete JSON as `output_cap_or_incomplete_response`, but the live eval summary currently only reports the high-level importer error.
- `scripts/smoke-openai-importer-live.py` already has better sanitized provider classification for importer-specific smoke testing and uses a higher default output cap.

## Primary Objective

Make the live importer eval either:

1. pass reliably with a realistic workflow-specific output cap, or
2. fail with safe provider diagnostics that identify whether the failure was output cap/incomplete response, invalid JSON, timeout/provider error, or budget block.

Do this without weakening normal offline validation, without printing secrets, and without adding GLM or secondary-provider behavior.

## Non-Negotiable Boundaries

Do not add:

- GLM provider integration;
- secondary-provider routing;
- new provider selection behavior;
- production auth;
- paid access;
- payment integration;
- ad/sponsor runtime code;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- production storage;
- Redis/Postgres/SQLite persistence;
- live OpenAI calls during normal validation;
- committed `.env` files;
- committed API keys or key fragments;
- raw provider prompts or raw provider responses in committed docs/outbox;
- screenshots, logs, or generated live artifacts.

Live checks must remain explicit opt-in.

## Suggested Files

Likely updated files:

```text
scripts/live-openai-demo-evals.py
scripts/run-openai-demo-evals.ps1
scripts/smoke-openai-importer-live.py if useful
scripts/demo-ai-live-smoke.ps1 if useful
ai-api/tests/test_live_openai_demo_evals.py or existing related test file
ai-api/tests/test_ai_env_file_script_docs.py if relevant
docs/live-openai-demo-evals.md
docs/live-openai-smoke-tests.md
docs/ai-live-demo-runbook.md
docs/ai-29-30-regression-e2e-harness.md
docs/ai-feature-status.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
README.md if relevant
```

Required new file:

```text
outbox/0030L-live-importer-eval-output-cap-and-safe-diagnostics-results.md
```

## Required Work

### 1. Add workflow-specific live eval output caps

Keep the live eval suite globally conservative, but allow importer to use a larger explicit cap.

Suggested behavior:

```text
AI_MAX_OUTPUT_TOKENS remains capped at 300 for general live evals.
OPENAI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS or AI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS can allow importer only to use 700-900 tokens.
Default importer live cap should be safe and bounded, likely 900.
Maximum importer live cap should be bounded, likely 1200.
```

The importer-specific cap must:

- apply only to the importer workflow;
- not raise caps for ask/dataset_ask/meal_plan unless explicitly designed and documented;
- remain budget-guarded;
- be documented as a live eval harness cap, not a production default;
- keep overall cost very small.

Implementation may temporarily override `AI_MAX_OUTPUT_TOKENS` only around the importer case and restore it afterward, or pass a workflow-specific cap if the architecture supports that cleanly.

### 2. Add safe provider diagnostics to live eval records

When a live eval workflow fails because of a provider/importer exception, record safe diagnostic fields in the JSONL and Markdown summary.

Examples:

```text
provider_error_category=output_cap_or_incomplete_response
provider_error_type=JSONDecodeError
safe_error_summary=Structured response ended before JSON completed; the output cap may be too low or the response may be incomplete.
```

Requirements:

- do not print API keys;
- do not print raw prompts;
- do not print raw provider responses;
- do not print Authorization headers;
- do not print `.env` contents;
- do not print local secret values;
- keep diagnostics short and sanitized;
- reuse existing provider diagnostic helpers if available.

### 3. Improve importer failure reporting in live eval summary

The Markdown summary should distinguish:

```text
threshold failure
provider call failure
structured output cap/incomplete response
invalid JSON
budget blocked before provider invocation
validation/schema failure
```

Do not make the suite pass just because a diagnostic exists. If importer fails, the overall run should still fail, but it should fail informatively.

### 4. Add focused tests

Add or update tests to prove:

- importer workflow can use a higher bounded live eval output cap;
- other workflows stay on the lower cap;
- cap overrides are restored after importer execution;
- invalid/incomplete structured JSON diagnostics are surfaced safely;
- live eval summary includes provider diagnostic fields when available;
- no raw provider prompt/response/key material appears in records or summaries;
- live mode remains opt-in;
- normal offline validation does not invoke OpenAI.

Use mocks/fakes for provider behavior. Do not require a real OpenAI call in pytest.

### 5. Update docs

Update the live eval docs/runbook to explain:

- importer needs a larger structured-output cap than short answer workflows;
- how the importer-specific cap works;
- safe defaults;
- how to override it locally if needed;
- how to read provider diagnostics;
- live evals remain opt-in through `.env` and explicit settings;
- normal validation remains offline/mock.

Suggested example:

```env
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_API_KEY=<set locally, never commit or paste>
OPENAI_MODEL=gpt-5.4-nano
AI_MAX_OUTPUT_TOKENS=300
OPENAI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS=900
OPENAI_LIVE_TEST_BUDGET_CENTS=25
```

Then:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env
```

### 6. Add outbox report

Create:

```text
outbox/0030L-live-importer-eval-output-cap-and-safe-diagnostics-results.md
```

Include:

- summary of issue found;
- output cap behavior added;
- provider diagnostics added;
- tests added;
- docs updated;
- validation results;
- live manual result if you run one;
- explicit non-goals;
- artifact safety confirmation;
- recommendation on whether `0031A` GLM ADR/eval harness is safe to start next.

## Acceptance Criteria

- Live eval importer can use a higher bounded output cap without raising the global live eval cap for all workflows.
- Safe diagnostics identify output cap/incomplete response, invalid JSON, provider timeout/API error, or budget block when available.
- A failing importer no longer reports only `Recipe importer provider failed.` in the summary when safe diagnostic detail exists.
- Normal validation remains offline/mock-only.
- Live evals remain explicit opt-in.
- No secrets or raw provider outputs are printed or committed.
- No GLM, secondary-provider routing, public route exposure, payment/ad/sponsor runtime, production auth, or storage changes are added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe -m pytest ai-api\tests -q
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

If direct Windows pytest hits the known local `pytest-of-scott` temp ACL issue for unrelated fixture tests, document it and rely on Git Bash validation if it passes.

The live eval command with `-EnvFile .\.env` is manual and should only run when the local ignored `.env` explicitly enables live mode.

Before committing, confirm:

- no `.env` file is staged;
- no real key is staged;
- no `sk-proj-`, `sk_live_`, or `sk_test_` string is staged;
- no raw provider response is staged;
- no raw provider prompt is staged;
- no `.tmp-ai-demo` artifacts are staged;
- no logs or screenshots are staged;
- no GLM provider code is added;
- no secondary-provider routing is added.

## Commit

```bash
git add scripts ai-api docs README.md outbox/0030L-live-importer-eval-output-cap-and-safe-diagnostics-results.md

git commit -m "mailbox: complete task 0030L live importer eval hardening"

git pull --rebase origin main
git push origin main
```
