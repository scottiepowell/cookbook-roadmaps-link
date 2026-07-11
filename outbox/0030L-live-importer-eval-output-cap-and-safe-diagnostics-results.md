# 0030L Live Importer Eval Output Cap And Safe Diagnostics Results

## Summary

This task updated the live OpenAI demo eval path so the importer workflow can use a separate, higher live output cap while the non-importer live-eval guard stays strict. The eval summary now also records sanitized provider diagnostics for importer failures when they are available.

## What Changed

- `scripts/live-openai-demo-evals.py` now resolves an importer-only output cap from `OPENAI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS` or `AI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS`.
- The importer workflow uses a 900-token default and a 1200-token ceiling, independent of the 300-token cap used by the other live-eval workflows.
- Importer failures now carry safe summary fields for `failure_category`, `provider_error_category`, `provider_error_type`, and `safe_error_summary` when diagnostics are available.
- Markdown summaries now include a failure column and sanitized failure details without exposing raw prompts, raw responses, or local paths.

## Tests Added Or Updated

- `ai-api/tests/test_live_openai_demo_evals.py`
  - importer workflow cap override is applied only inside the importer helper and is restored afterward;
  - importer provider failures surface safe diagnostics;
  - budget-block payloads are classified safely before invocation.
- `ai-api/tests/test_ai_29_30_regression_harness.py`
  - remained green after the regression baseline was tightened to stay offline and deterministic.

## Docs Updated

- `docs/live-openai-demo-evals.md`
- `docs/live-openai-smoke-tests.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

## Validation Results

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_live_openai_demo_evals.py -q` passed.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_29_30_regression_harness.py -q` passed.
- `& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py` passed.
- `git diff --check` passed.
- The live eval wrapper was also exercised against the local `.env` path in this workspace; that path is environment-dependent and is not part of normal offline validation.

## Explicit Non-Goals

- No GLM provider integration.
- No secondary-provider routing.
- No production auth, paid access, billing, or entitlement enforcement.
- No public route exposure or Cloudflare changes.
- No persisted storage, Redis, Postgres, SQLite, or durable user memory.
- No committed secrets, raw prompts, raw provider responses, or generated artifacts.

## Artifact Safety Confirmation

- No invite/session tokens were committed.
- No API keys, secret fragments, or auth headers were committed.
- No raw provider prompts or responses were committed.
- No local absolute paths were added to public docs examples.
- No `.tmp-ai-demo` artifacts were kept in the worktree.
- No production live behavior was enabled by default.
