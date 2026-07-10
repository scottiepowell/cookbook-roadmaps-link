# 0030F Recipe Session Alpha Hardening And Acceptance Results

## Summary

Completed the Recipe Session Alpha hardening and acceptance pass. The local alpha now has clearer API/UI behavior, expanded edge-case coverage, updated session evals, a dedicated acceptance runbook, and validated offline/mock-only acceptance evidence.

No production storage, persistent user memory, auth, paid access, public route exposure, invite flow, budget enforcement runtime, vector database, embeddings, browser automation, screenshots, or live OpenAI calls were added.

## Hardening Changes

- Kept repeated demo finalize idempotent by avoiding duplicate production write-back warnings.
- Expanded API safety tests for start/message/get/finalize responses.
- Added API edge-case tests for empty and symbol-only starts, follow-up before draft, repeated no-refresh messages, finalize before draft, repeated finalize, unknown/expired message and finalize, contradictory method updates, equipment updates, and excluded-ingredient updates.
- Extended session eval cases with air-fryer refresh, excluded-ingredient refresh, finalize-without-draft, and missing finalize safety.
- Improved the demo UI copy for alpha/demo-only boundaries, process-local session expiration, no-refresh reuse, missing/expired sessions, and finalize-for-demo behavior.
- Added `docs/recipe-session-alpha-acceptance-runbook.md`.

## Edge Cases Covered

- Empty start text and symbol-only start text return `rejected`.
- Vague `make dessert` returns `clarification_needed` with no draft.
- Unknown and expired get/message/finalize return safe `not_found` responses.
- Follow-up before a draft exists stays safe and does not invent a draft.
- Finalize before draft returns a clarification-style state with a no-draft warning.
- Repeated finalize keeps one demo-only warning.
- Repeated `thanks` / `looks good` returns `no_material_change`.
- `make it no-bake but bake it overnight` is handled as a controlled material method update.
- `use air fryer instead` refreshes RAG and records equipment constraints.
- `no nuts` refreshes RAG and records excluded ingredients.

## UI Changes

- The `Recipe Session Alpha` panel now labels the workflow as local/process-only.
- Empty state mentions interpreted requirements, expiration, and revision state.
- No-refresh copy makes clear the existing draft/citations were reused and no RAG refresh was needed.
- RAG refresh display prefers the API-provided refresh reason.
- Finalize copy states the action is demo-only and does not write production storage.
- Missing/expired session errors are friendly and recoverable.

## Eval And Test Changes

- `evals/ai_cookbook/session_cases.yaml` now includes 11 recipe-session cases.
- `run_evals.py` now passes 39 total offline cases.
- `ai-api/tests/test_recipe_session_api.py` covers additional edge cases and response safety.
- `ai-api/tests/test_demo_ui.py` covers the hardened UI copy.
- `ai-api/tests/test_recipe_session_eval_harness.py` verifies the new eval case IDs.

## Mock Smoke Coverage

`scripts/demo-ai-mock.ps1` remains the canonical local smoke path and continues to exercise:

- detailed session start;
- material no-bake follow-up and RAG refresh;
- get session;
- finalize for demo;
- vague clarification;
- chatter/no-refresh;
- forbidden-text safety checks.

## Runbook And Docs

Updated:

- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

The runbook documents the local/offline boundary, mock demo commands, expected response states, happy path, clarification, RAG refresh, no-refresh, finalize-for-demo, missing/expired sessions, known Windows pytest temp ACL note, and validation commands.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` - passed, 39/39 offline eval cases.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` - passed, including shell syntax, Docker Compose config, 220 pytest tests, 39 offline evals, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check` - passed with line-ending warnings only.
- `docker compose config --quiet` - passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` - passed, including session endpoint smoke checks.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` - skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` - skipped cleanly without live opt-in.

A focused direct Windows pytest run earlier hit the known local `pytest-of-scott` temporary-directory ACL issue before executing tests. The Git Bash validator path passed the full pytest suite.

## Artifact Safety

Confirmed this task did not add raw dataset files, `.tmp-ai-demo` artifacts, generated persistent indexes, disk cache files, `.env` files, screenshots, logs, credentials, raw provider prompts, raw provider responses, local absolute paths in public docs examples, production session storage, payment secrets, or invite secrets.

## Recommended Next Task

`0030G`: operator UX polish for requirement diff display and revision summaries, still local/offline and without production persistence.
