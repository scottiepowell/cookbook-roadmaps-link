# Task 0025E: Fix Live Smoke Windows Cleanup And Record Validation

## Goal

Make `scripts/smoke-openai-live.py` Windows-safe when cleaning up temporary SQLite fixtures and record the successful manual live OpenAI smoke validation.

## Context

The manual live OpenAI smoke test passed with:

```text
provider=openai
model=gpt-5.4-nano
live_calls=4
estimated_usage_tokens=1200
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

Before that, Windows sometimes failed during temporary SQLite cleanup with `WinError 32` on `cookbook.sqlite`. The live workflows passed, but cleanup should not mask success.

## Requirements

- Use best-effort temporary directory cleanup, such as `TemporaryDirectory(ignore_cleanup_errors=True)`.
- Successful live workflows should still print the compact summary.
- Cleanup failure after success should be a warning or ignored cleanup error, not a false failure.
- Workflow/provider/assertion failures should still exit non-zero.
- Add or update offline cleanup behavior tests if practical.
- Update `docs/live-openai-smoke-tests.md`.
- Update `docs/ai-implementation-backlog.md` so 0025C/0025D/0025E statuses are accurate.
- Add `outbox/0025E-fix-live-smoke-windows-cleanup-results.md`.

## Validation

Run:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct Windows pytest still fails with the known temp-directory issue, document it and confirm Git Bash validator passes.

## Constraints

- Do not commit `.env`, API keys, raw datasets, generated indexes, or temp files.
- Do not add live OpenAI calls to normal validation or CI.
- Do not add deployment, Cloudflare, Qdrant, Postgres, pgvector, embeddings, or vector DB changes.
