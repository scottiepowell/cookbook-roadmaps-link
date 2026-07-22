# 0030I-8S Live Diagnostic Output Cap JSON Envelope

## Goal

Correct the approved live importer diagnostic wrapper so an `output_cap_or_incomplete_response` / `JSONDecodeError` result is reported as a safe diagnostic envelope instead of surfacing a PowerShell `NativeCommandError` frame.

This is a follow-up to `0030I-8R`.

## Observed operator result

The no-call preflight passed:

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

Then the approved bounded call produced:

```text
python.exe : FAIL: live importer smoke failed: provider_error_category=output_cap_or_incomplete_response
provider_error_type=JSONDecodeError
At C:\Users\scott\cookbook-roadmaps-link\scripts\diagnose-live-importer.ps1:95 char:14
...
NativeCommandError
```

The useful safe classification is present, but the wrapper did not convert it into the normal safe summary envelope.

## Required work

### 1. Fix PowerShell wrapper error handling

Update:

```text
scripts/diagnose-live-importer.ps1
```

so the Python helper failure is captured as text and mapped safely even when PowerShell represents stderr/non-zero native output as `NativeCommandError`.

Requirements:

- No raw PowerShell traceback should appear in the expected diagnostic output.
- The wrapper should parse `provider_error_category=output_cap_or_incomplete_response`.
- The wrapper should parse `provider_error_type=JSONDecodeError` safely if present.
- The wrapper should still exit non-zero for failed approved diagnostics.
- The wrapper should still stop after one provider call.
- Do not print secrets, raw prompts, raw provider bodies, env values, headers, or stack traces.

Expected safe output shape:

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

Use exact field names already present in the codebase if a better convention exists.

### 2. Add category mapping

Add or preserve mappings for:

```text
output_cap_or_incomplete_response
JSONDecodeError
```

The category should not be collapsed to `unexpected_safe_internal_block` unless parsing truly fails.

### 3. Consider output cap guidance

The current operator run used:

```text
Max output tokens: 300
AI timeout seconds: 20
```

The failure indicates the live provider path was reached but the importer response was incomplete or not parseable under the current cap. Add documentation guidance that the next live acceptance may require a deliberately approved cap adjustment, but do not increase caps automatically in normal validation.

Any future cap adjustment must remain explicit, bounded, documented, and safe. Do not weaken normal validation.

### 4. Tests

Add deterministic tests for:

- Python helper stderr/non-zero output is captured without emitting `NativeCommandError` frames.
- `provider_error_category=output_cap_or_incomplete_response` maps to the safe category.
- `provider_error_type=JSONDecodeError` is reported only as a safe type field.
- Approved diagnostic still exits non-zero on failed provider result.
- No secret markers, raw prompts, provider bodies, env dumps, local paths, or stack traces are emitted.
- Preflight-only remains no-call.
- Normal validation remains offline/mock-only.

Use fake helper output or mocks. Do not make live OpenAI calls in tests.

### 5. Docs

Update:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Document:

- preflight passed means configuration is valid;
- `output_cap_or_incomplete_response` means the live path was reached but the model output was incomplete or not schema-parseable;
- the safe next step is a single explicitly approved diagnostic/acceptance run with a documented cap/timeout adjustment if required;
- do not retry repeatedly;
- do not expose raw provider output.

### 6. Outbox

Create:

```text
outbox/0030I-8S-live-diagnostic-output-cap-json-envelope-results.md
```

Summarize:

- observed NativeCommandError leak;
- safe category mapping added;
- tests added;
- validation results;
- whether live was run;
- explicit non-goals;
- whether a bounded follow-up acceptance with adjusted cap is ready.

## Acceptance criteria

- Approved live diagnostic failures are always reported through the safe summary envelope.
- `output_cap_or_incomplete_response` / `JSONDecodeError` is classified accurately and safely.
- No raw traceback or `NativeCommandError` frame appears in expected diagnostic output.
- Failed diagnostics still exit non-zero.
- No live OpenAI call is required for tests or normal validation.
- Normal validation remains offline/mock-only.
- No secrets, env values, prompts, raw provider responses, local paths, screenshots, traces, videos, or generated artifacts are committed.
- No AWS/platform work, auth, payment, public exposure, vector DB, embeddings, provider-routing overhaul, raw dataset commit, persistent index, or disk cache is added.

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

Live wrappers should skip unless explicitly opted in. Do not run a live provider call for normal validation.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-8S-live-diagnostic-output-cap-json-envelope-results.md

git commit -m "mailbox: complete task 0030I-8S live diagnostic output cap envelope"

git pull --rebase origin main

git push origin main
```
