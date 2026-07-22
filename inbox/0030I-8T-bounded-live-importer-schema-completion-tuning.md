# 0030I-8T Bounded Live Importer Schema Completion Tuning

## Goal

Tune the bounded live importer diagnostic/acceptance path so one explicitly approved live importer call can complete with schema-parseable JSON using `openai/gpt-5.4-nano`, without weakening normal mock/offline validation or exposing provider internals.

This task follows `0030I-8S`, where the diagnostic wrapper correctly mapped the approved live call to:

```text
safe_unavailable_category=output_cap_or_incomplete_response
safe_provider_error_type=JSONDecodeError
```

The live provider path was reached. The remaining issue is response completeness/schema parsing under the currently configured output cap.

## Observed Operator Evidence

Preflight passed:

```text
workflow=importer
requested_provider=openai
requested_model=gpt-5.4-nano
openai_model_status=allowed
ai_model_status=allowed
model_config=valid
api_key=redacted-present
live_opt_in=True
budget_config=valid
token_config=valid
timeout_config=valid
status=blocked
safe_unavailable_category=operator_approval_required
safe_guidance=Preflight passed. Pass -ApproveLiveCall after reviewing the redacted summary to permit one bounded importer call. No provider call was attempted.
```

One approved call returned the safe envelope:

```text
workflow=importer
requested_provider=openai
requested_model=gpt-5.4-nano
openai_model_status=allowed
ai_model_status=allowed
model_config=valid
api_key=redacted-present
live_opt_in=True
budget_config=valid
token_config=valid
timeout_config=valid
status=failed
safe_unavailable_category=output_cap_or_incomplete_response
safe_provider_error_type=JSONDecodeError
safe_guidance=The bounded importer call reached the live provider path but the response could not be parsed as complete schema JSON within the configured output cap. No retry was attempted.
```

## Primary Objective

Make the live importer smoke/diagnostic path reliably request and validate a minimal schema response that fits the allowed live diagnostic limits.

Do this by tuning request shape, schema expectations, prompt wording, diagnostic fixture size, and/or safe parser handling as needed.

Do **not** solve this by silently retrying, hiding parse failures, accepting invalid JSON, or raising normal validation limits.

## Required Work

### 1. Inspect the importer live path

Inspect:

```text
scripts/diagnose-live-importer.ps1
scripts/smoke-openai-importer-live.py
ai-api/app/importer.py
ai-api/app/routes/ai.py
ai-api/app/providers/openai_provider.py or equivalent provider implementation
ai-api/app/schemas/importer.py
ai-api/tests
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
outbox/0030I-8S-live-diagnostic-output-cap-json-envelope-results.md
```

Confirm:

- the exact schema the importer expects;
- whether live requests use a strict JSON/schema response format when available;
- whether the smoke fixture asks for more fields than needed;
- whether `AI_MAX_OUTPUT_TOKENS=300` is realistically enough for the expected draft JSON;
- whether the provider wrapper truncates or transforms output;
- whether the importer prompt can be shortened for the smoke path without affecting product behavior;
- whether safe parser diagnostics can distinguish truncation/incomplete JSON from other schema failures without exposing raw output.

### 2. Add a bounded live-smoke importer profile

Add or update the live importer smoke path so the approved diagnostic uses a tiny deterministic importer fixture and asks for the smallest useful valid draft.

Requirements:

- keep model fixed to `gpt-5.4-nano`;
- keep normal validation mock/offline;
- keep default live diagnostic budget limits;
- do not write or print raw provider output;
- do not expose the prompt or provider body in logs;
- do not accept invalid JSON as success;
- do not add retries;
- do not add arbitrary model selection.

Suggested minimal smoke fixture text:

```text
scrambled eggs: 2 eggs, 1 tbsp butter, pinch salt. Whisk eggs, cook in butter over medium-low heat, stir until softly set. Serves 1.
```

If the current importer schema is too large to fit 300 output tokens, design a narrowly scoped smoke-safe mode that still validates the real importer schema but encourages concise fields.

### 3. Improve schema completion behavior safely

Possible safe fixes include one or more of:

- shorten the live smoke input fixture;
- shorten system/user instructions for the smoke path;
- use strict JSON response-format/schema support if already supported by the provider abstraction;
- reduce optional verbosity in generated fields;
- ensure the live smoke passes `AI_MAX_OUTPUT_TOKENS=300` consistently;
- add a targeted parser category for incomplete JSON if not already covered;
- add safe guidance recommending one explicit operator-approved cap/timeout adjustment only if the schema truly cannot fit.

Do not implement broad prompt rewrites unless required.
Do not weaken production/product importer validation.
Do not add provider-specific secret/debug output.

### 4. Add deterministic tests

Add tests for:

- the live smoke fixture is small and deterministic;
- live smoke uses `gpt-5.4-nano` only;
- live smoke keeps output cap within the accepted limit;
- successful fake provider response produces a valid importer summary;
- incomplete fake JSON maps to `output_cap_or_incomplete_response` safely;
- parser/schema failures do not leak raw provider text;
- no retry is attempted;
- normal validation remains mock/offline;
- docs/scripts do not contain secret-like markers.

Use fake provider outputs only. Do not make live calls in tests.

### 5. Optional one-call manual acceptance

After tests and validation pass, an operator may run exactly one approved live acceptance call if ignored local live config is valid.

Required sequence:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall
```

If it passes, record only safe facts:

- workflow;
- provider;
- model;
- status;
- title if safe and generated by the schema;
- ingredient count;
- instruction count;
- usage token counts if already safely summarized.

If it fails, record only the safe category and guidance.

Do not retry repeatedly.

### 6. Update docs

Update:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Docs should explain:

- `output_cap_or_incomplete_response` means config and live path passed, but schema JSON was incomplete or not parseable;
- the live importer smoke uses a minimal fixture;
- normal validation does not call live OpenAI;
- one approved live call is enough for acceptance evidence;
- no raw provider output is stored or displayed;
- no arbitrary model selection is supported.

### 7. Add outbox report

Create:

```text
outbox/0030I-8T-bounded-live-importer-schema-completion-tuning-results.md
```

The outbox must summarize:

- observed `output_cap_or_incomplete_response` baseline;
- importer smoke/request/schema tuning performed;
- tests added;
- validation results;
- whether manual live acceptance ran;
- if run, safe result summary only;
- if skipped or failed, safe category only;
- explicit non-goals;
- whether successful live importer acceptance can now be claimed.

## Acceptance Criteria

- The live importer diagnostic/smoke path has a bounded minimal fixture/profile.
- It keeps `gpt-5.4-nano` as the only live model.
- It keeps live output cap within the allowed diagnostic limit unless a separately documented manual-only adjustment is explicitly required.
- It validates real importer schema output, not arbitrary text.
- Incomplete JSON remains a safe failure, not a hidden success.
- No raw provider output, prompt, key, env value, local path, stack trace, screenshot, trace, video, or generated artifact is committed or printed.
- Normal validation remains offline/mock-only.
- No live OpenAI call is required for tests or normal validation.
- No retries are added.
- No arbitrary model picker, AWS/platform work, production auth, payment, public route exposure, Cloudflare/DNS change, secondary-provider runtime, vector DB, embeddings, upstream UI rewrite, raw dataset commit, persistent index, or disk cache is added.

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
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-ui-playwright.ps1
```

Live wrappers should skip unless explicitly opted in.
Do not run live OpenAI for normal validation.

Optional one-call live acceptance may run only after validation and only with explicit operator approval.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-8T-bounded-live-importer-schema-completion-tuning-results.md

git commit -m "mailbox: complete task 0030I-8T bounded live importer schema completion"

git pull --rebase origin main

git push origin main
```
