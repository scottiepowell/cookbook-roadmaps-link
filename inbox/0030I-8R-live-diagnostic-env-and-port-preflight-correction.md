# 0030I-8R Live Diagnostic Env And Port Preflight Correction

## Goal

Correct the confusing bounded live importer diagnostic behavior observed after `0030I-8`.

The operator ran:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

The launcher printed a live-capable profile summary:

```text
Provider: openai
Model: gpt-5.4-nano
Live tests enabled: true
OpenAI API key: redacted-present
Budget cents: 25
Max output tokens: 300
AI timeout seconds: 20
```

but Uvicorn failed to start:

```text
ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000): [winerror 10048] only one usage of each socket address (protocol/network address/port) is normally permitted
```

Then the operator ran:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall
```

The script printed:

```text
workflow=importer
requested_provider=openai
requested_model=gpt-5.4-nano
api_key=redacted-present
live_opt_in=True
budget_config=valid
token_config=valid
timeout_config=valid
status=blocked
safe_unavailable_category=model_not_allowed
safe_guidance=Only gpt-5.4-nano is allowed for this diagnostic. No provider call was attempted.
```

This is internally confusing: the summary says the requested model is `gpt-5.4-nano`, but the block category says `model_not_allowed`.

## Diagnosis To Confirm

`diagnose-live-importer.ps1` currently hardcodes the printed `requested_model=gpt-5.4-nano`, while the model gate checks real environment variables:

```powershell
if ($env:OPENAI_MODEL -ne "gpt-5.4-nano" -or $env:AI_MODEL -and $env:AI_MODEL -ne "gpt-5.4-nano") {
    ... model_not_allowed ...
}
```

Because `Import-AiEnvFile -OnlyIfMissing` preserves existing process environment values, a stale or inherited `AI_MODEL` or `OPENAI_MODEL` can cause a block while the summary still displays the desired model.

The launcher also does not fail early enough when port `127.0.0.1:8000` is already occupied. It prints the live runtime summary and then Uvicorn fails after startup begins.

## Required Work

### 1. Fix diagnostic model reporting

Update `scripts/diagnose-live-importer.ps1` so the redacted summary reflects the actual effective preflight state, not hardcoded desired values.

The summary may show safe model names because model names are not secrets, but it must avoid raw env dumps.

For example, print safe fields such as:

```text
requested_provider=openai
requested_model=gpt-5.4-nano
openai_model_status=allowed
ai_model_status=allowed
model_config=valid
```

or, when blocked:

```text
requested_provider=openai
requested_model=gpt-5.4-nano
openai_model_status=allowed
ai_model_status=disallowed
model_config=invalid
status=blocked
safe_unavailable_category=model_not_allowed
safe_guidance=AI_MODEL is set to a value outside the allowed live diagnostic model. Set both AI_MODEL and OPENAI_MODEL to gpt-5.4-nano or clear the stale process value. No provider call was attempted.
```

Do not print arbitrary environment values. If a disallowed model value is printed, it must be a safe model identifier only and must not include secret-like content.

### 2. Normalize model env checks

Trim whitespace and consistently evaluate:

```text
AI_MODEL
OPENAI_MODEL
```

Allowed live diagnostic model:

```text
gpt-5.4-nano
```

Rules:

- `OPENAI_MODEL` must equal `gpt-5.4-nano` after trimming.
- `AI_MODEL`, if set/non-empty, must equal `gpt-5.4-nano` after trimming.
- If `AI_MODEL` is missing/empty, the script may treat it as implicitly aligned with `OPENAI_MODEL` if existing app config supports that; document whichever behavior is implemented.
- Any stale `mock-basic`, old fallback, or unsupported model must block before provider calls.
- The safe guidance must identify whether `AI_MODEL` or `OPENAI_MODEL` caused the block without dumping all env values.

### 3. Add a no-call preflight mode

Add a safe preflight-only path such as:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly
```

Behavior:

- loads ignored `.env` through the existing helper;
- prints redacted preflight;
- validates live opt-in, API key presence, provider, model, budget, tokens, timeout, and provider-call flags;
- never calls the provider;
- exits success only if the preflight is valid;
- exits nonzero or prints `status=blocked` if invalid, following existing script style.

If adding a new parameter is undesirable, document the existing no-approval behavior as the preflight path and improve its output enough to diagnose stale model state.

### 4. Improve port preflight for launcher

Update `scripts/start-ai-demo-local.ps1` to detect whether `127.0.0.1:8000` is already occupied before starting Uvicorn.

If the port is already in use:

- print a clear safe message;
- do not continue into Uvicorn startup;
- do not print or expose secrets;
- include operator guidance to either stop the existing server or use the existing server intentionally;
- if feasible, show a Windows command pattern such as `netstat -ano | findstr :8000` without killing anything automatically.

Do not automatically stop the existing process.

### 5. Add tests

Add deterministic tests for:

- diagnostic summary no longer hardcodes misleading model status;
- stale `AI_MODEL=mock-basic` with `OPENAI_MODEL=gpt-5.4-nano` blocks safely and identifies `AI_MODEL` as the reason;
- stale `OPENAI_MODEL` blocks safely and identifies `OPENAI_MODEL` as the reason;
- valid `AI_MODEL=gpt-5.4-nano` and `OPENAI_MODEL=gpt-5.4-nano` preflight passes without provider calls;
- `-PreflightOnly`, if added, never calls provider;
- launcher reports port-in-use before Uvicorn attempts to bind;
- no API keys, key fragments, `.env` contents, raw prompts, raw provider responses, local paths, stack traces, or provider internals are printed.

Use fake temporary env fixtures only. Do not make live OpenAI calls in tests.

### 6. Update docs

Update as needed:

```text
README.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/local-product-acceptance-checklist.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Docs should explain:

- how to run diagnostic preflight without a provider call;
- how stale process environment values can override ignored `.env` values;
- how to clear or align `AI_MODEL` and `OPENAI_MODEL` safely;
- what port `8000` already in use means;
- how to identify the occupying process without killing it automatically;
- that successful live acceptance still requires an explicitly approved one-call diagnostic after preflight passes.

### 7. Outbox

Create:

```text
outbox/0030I-8R-live-diagnostic-env-and-port-preflight-correction-results.md
```

The outbox must summarize:

- observed contradictory diagnostic output;
- root cause;
- diagnostic reporting correction;
- model preflight behavior;
- port preflight behavior;
- tests added;
- validation results;
- explicit non-goals;
- whether a follow-up one-call live diagnostic is ready.

## Acceptance Criteria

- Diagnostic output cannot say `requested_model=gpt-5.4-nano` while hiding the actual model env value that caused `model_not_allowed`.
- Stale/inherited model environment values are identified safely.
- A no-provider-call preflight path exists or the existing no-approval path clearly fulfills that role.
- Launcher fails early and clearly when `127.0.0.1:8000` is already occupied.
- No provider calls are made during normal validation.
- No secrets or raw provider internals are printed or committed.
- The next operator step after this task is clear: stop/choose the correct sidecar process, run preflight, then run exactly one approved diagnostic only if preflight passes.

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
git add ai-api docs README.md scripts outbox/0030I-8R-live-diagnostic-env-and-port-preflight-correction-results.md

git commit -m "mailbox: complete task 0030I-8R live diagnostic env port correction"

git pull --rebase origin main

git push origin main
```
