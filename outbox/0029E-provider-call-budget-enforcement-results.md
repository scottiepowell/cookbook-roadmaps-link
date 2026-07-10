# 0029E Provider Call Budget Enforcement Results

## Summary

Implemented a centralized provider-call budget guard for the local AI demo surface. The new guard sits after the local operator gate and before any live provider invocation, so mock/offline paths stay unchanged while live calls can be blocked safely.

## What Changed

- Added `ai-api/app/ai_budget_guard.py` with a process-local `AiProviderBudgetTracker` and `check_provider_budget(...)` helper.
- Added provider budget settings in `ai-api/app/config.py`.
- Added `AiProviderBudgetDecision` and `AiProviderBudgetStatus` in `ai-api/app/ai_access_models.py`.
- Wired budget checks into importer, dataset ask, saved-recipe Ask My Cookbook, meal plan, and recipe-session generation paths.
- Updated the manual live smoke/eval scripts to respect the centralized budget settings and skip safely when live calls are disabled.

## Budget Behavior

- Mock/local provider calls are treated as zero-cost and allowed by default.
- Live provider calls are blocked before invocation when:
  - provider calls are globally disabled;
  - the per-call input token cap is exceeded;
  - the per-call output token cap is exceeded;
  - the per-call total token cap is exceeded;
  - the per-session call-count cap is exhausted;
  - the per-call estimated cost cap is exceeded;
  - the per-session estimated cost cap is exhausted;
  - the budget configuration is invalid.
- Safe meter events and budget snapshots are produced for allow/block/skip decisions.

## Safe Metadata

The public/operator-facing models and responses only expose safe values:

- IDs;
- statuses;
- workflow names;
- provider/model names;
- token and cost counts;
- budget snapshot summaries;
- safe metadata fingerprints.

The implementation does not expose raw prompts, raw provider responses, API keys, Authorization headers, `.env` values, or local filesystem paths.

## Tests Added

- `ai-api/tests/test_ai_budget_guard.py`
- `ai-api/tests/test_ai_access_models.py` budget decision coverage

The tests cover:

- mock provider allowed with zero cost;
- global disable and provider-call disable blocks;
- input/output/total token cap blocks;
- per-call and per-session cost cap blocks;
- per-session call-count cap blocks;
- invalid budget configuration blocks live calls safely;
- allowed and blocked meter-event serialization;
- route-level blocking for importer and recipe-session flows;
- tracker reset behavior;
- forbidden-string rejection.

## Documentation Updated

- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-session-metering-schema.md`
- `docs/ai-local-operator-access-gate.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed with 39/39 offline cases.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed all 7 checks and the full `pytest` suite.
- `git diff --check` passed.
- `docker compose config --quiet` passed through the repo validator.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly without live opt-in.

## Windows Pytest Note

Direct ad hoc Windows `pytest` runs outside the repo validator still hit the known local `pytest-of-scott` temp-directory ACL issue. The Git Bash validator path passed cleanly and is the authoritative normal-validation result for this task.

## Non-Goals

This task did not add:

- production storage;
- database migrations;
- auth;
- paid access;
- payment provider integration;
- invite emails;
- public route exposure;
- Cloudflare changes;
- Redis, Postgres, or SQLite budget persistence;
- admin dashboard UI;
- persistent user memory;
- live OpenAI calls during normal validation.

## Artifact Safety Confirmation

No raw dataset files, `.tmp-ai-demo/` artifacts, generated persistent indexes, disk caches, `.env` files, screenshots, logs, credentials, raw provider prompts, raw provider responses, or local absolute paths were committed.
