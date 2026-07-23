# 0030I-8U: Bounded Live Importer 1000 Token Cap Profile

Status: queued.

## Context

The `0030I-8T` bounded live importer schema-completion task added a minimal
scrambled-egg diagnostic fixture and kept the diagnostic output cap at 300
tokens. Offline validation passed, but no live provider call was made during that
task.

The subsequent operator-approved live diagnostic used valid local live
configuration and reached the live provider path, but still failed with:

```text
status=failed
safe_unavailable_category=output_cap_or_incomplete_response
safe_provider_error_type=JSONDecodeError
safe_guidance=The bounded importer call reached the live provider path but the response could not be parsed as complete schema JSON within the configured output cap. No retry was attempted.
```

This means the current blocker is no longer environment loading, model routing,
port ownership, approval gating, or provider reachability. The likely blocker is
that the live importer response cannot fit into the current 300-token diagnostic
cap while still satisfying strict schema JSON.

## Goal

Add a bounded, explicit manual live diagnostic profile that can run the importer
with `AI_MAX_OUTPUT_TOKENS=1000` for one approved live acceptance attempt, while
preserving normal mock/offline validation and existing safety boundaries.

If the 1000-token profile succeeds, document a later manual dial-down plan to
find the lowest reliable cap. Do not perform repeated automatic live retries.

## Non-goals

- Do not claim live success unless an explicitly approved operator run actually
  passes.
- Do not make live OpenAI calls during normal validation.
- Do not increase the default mock/offline validation cap.
- Do not add arbitrary model selection.
- Do not change the allowed live model from `gpt-5.4-nano`.
- Do not hide parse failures or accept invalid JSON as success.
- Do not print raw provider output, prompts, provider bodies, stack traces,
  headers, API keys, `.env` contents, or local filesystem paths.
- Do not add retries, screenshots, traces, browser artifacts, persistent indexes,
  embeddings, vector databases, AWS/platform resources, production auth, public
  routing, payment, or storage changes.

## Requirements

### 1. Add an explicit high-cap diagnostic mode

Update the diagnostic/live-smoke path so an operator can intentionally request a
1000-token bounded live importer run.

Prefer an explicit flag, for example:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly -MaxOutputTokens 1000
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall -MaxOutputTokens 1000
```

Use the repo's existing naming/style if a better parameter convention already
exists.

The profile must:

- require `-ApproveLiveCall` for the provider call;
- keep `-PreflightOnly` no-call;
- permit only `gpt-5.4-nano`;
- show the requested cap in safe output;
- enforce an explicit manual cap upper bound of 1000 tokens;
- keep budget enforcement in place;
- perform at most one live importer call per invocation;
- never retry automatically;
- never print raw provider output.

### 2. Keep normal validation unchanged

Normal validation, mock smoke, Playwright, offline evals, and CI-style scripts
must remain mock/offline and must not call OpenAI.

Existing default local live profile behavior may remain at 300 tokens unless the
operator explicitly requests the 1000-token diagnostic mode.

### 3. Add safe result reporting

For the approved 1000-token attempt, the diagnostic output should include safe
fields such as:

```text
workflow=importer
requested_provider=openai
requested_model=gpt-5.4-nano
requested_max_output_tokens=1000
openai_model_status=allowed
ai_model_status=allowed
model_config=valid
api_key=redacted-present
live_opt_in=True
budget_config=valid
token_config=valid
timeout_config=valid
status=passed|failed
safe_unavailable_category=...
safe_provider_error_type=...
safe_guidance=...
```

If successful, record only safe success facts such as provider, model, status,
title if safe, ingredient count, instruction count, and usage token counts if
already summarized safely.

### 4. Add a dial-down plan, not automatic retries

If the 1000-token profile succeeds, document a future manual dial-down ladder,
for example:

```text
1000 -> 800 -> 600 -> 500 -> 400 -> 300
```

The plan must require one explicit operator-approved call per step and must not
be automated into repeated live calls.

### 5. Tests

Add deterministic tests for:

- default diagnostic cap behavior remains unchanged;
- `-MaxOutputTokens 1000` is accepted only for explicit diagnostic mode;
- values above 1000 are rejected safely;
- `-PreflightOnly -MaxOutputTokens 1000` never calls the provider;
- approved mode passes the requested cap to the helper;
- success and failure envelopes include `requested_max_output_tokens`;
- incomplete JSON at 1000 still maps safely;
- no secret markers, raw provider responses, prompts, env dumps, paths, headers,
  or stack traces are emitted;
- normal validation remains mock/offline.

Use fake helper/provider output. Do not make live OpenAI calls in tests.

### 6. Documentation

Update the relevant runbooks/status/backlog docs:

- `README.md`
- `docs/ai-live-demo-runbook.md`
- `docs/live-openai-smoke-tests.md`
- `docs/local-product-acceptance-checklist.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`

Docs must explain:

- 300-token live diagnostic still fails with `output_cap_or_incomplete_response`;
- the 1000-token cap is an explicit manual diagnostic profile;
- normal validation remains mock/offline;
- one approved call is allowed per operator run;
- do not retry repeatedly;
- do not expose raw provider output;
- if 1000 succeeds, dial down manually in later bounded steps.

### 7. Outbox

Create:

```text
outbox/0030I-8U-bounded-live-importer-1000-token-cap-profile-results.md
```

The outbox must summarize:

- the observed 300-token live failure baseline;
- the 1000-token diagnostic profile added;
- safety boundaries preserved;
- tests added;
- validation results;
- whether an explicit manual 1000-token live run was performed;
- if run, the safe result summary only;
- if skipped or failed, the safe category only;
- whether successful live importer acceptance can now be claimed;
- next dial-down recommendation if successful.

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

Optional operator-approved live diagnostic after validation:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly -MaxOutputTokens 1000
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall -MaxOutputTokens 1000
```

Do not retry automatically.

## Commit

```bash
git add ai-api docs README.md scripts outbox/0030I-8U-bounded-live-importer-1000-token-cap-profile-results.md

git commit -m "mailbox: complete task 0030I-8U bounded live importer token cap"

git pull --rebase origin main

git push origin main
```
