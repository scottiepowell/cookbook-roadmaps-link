# AI Feature Completion Review

## Final Status

The AI cookbook sidecar feature slice is complete for portfolio/demo purposes. It includes importer, saved-recipe RAG, dataset search/RAG, meal planning, offline evals, mock demo scripts, REST examples, portfolio docs, and manual live OpenAI validation. Production storage, embeddings/vector DB, UI rewrite, and deployment changes remain intentionally deferred.

## Acceptance Matrix

| Area | Complete? | Evidence | Notes |
| --- | --- | --- | --- |
| Architecture | Yes | `ai-api/`, [AI sidecar architecture](ai-sidecar-architecture.md), [AI portfolio showcase](ai-portfolio-showcase.md) | Vanilla Cookbook stays the source app; FastAPI sidecar handles AI workflows without production storage changes. |
| Provider harness | Yes | `ai-api/app/providers/`, `ai-api/tests/test_providers.py`, `ai-api/tests/test_openai_live_smoke_script.py` | Mock provider is default for validation; OpenAI path is manual-only and guarded. |
| Structured importer | Yes | `POST /ai/import-recipe`, `ai-api/tests/test_importer.py`, offline evals, live smoke | Produces schema-validated recipe drafts and does not write to the cookbook DB. |
| Ask My Cookbook | Yes | `POST /ai/ask`, `ai-api/tests/test_rag.py`, offline evals, live smoke | Retrieves saved recipes first and returns cited answers. |
| Dataset search | Yes | `GET/POST /dataset/search`, `ai-api/tests/test_dataset_search_api.py`, mock demo | Uses bounded deterministic local retrieval over generated fixtures; no persistent indexes. |
| Dataset ask/RAG | Yes | `POST /dataset/ask`, `ai-api/tests/test_dataset_ask.py`, offline evals, live smoke | Answers from retrieved dataset records and includes provenance citations. |
| Meal planner | Yes | `POST /ai/meal-plan`, `ai-api/tests/test_meal_plan_endpoint.py`, offline evals, live smoke | Uses saved recipe candidates and avoids DB write-back. |
| Offline tests | Yes | `ai-api/tests`, `scripts/validate-repo.sh` | Git Bash validator confirms the full AI API suite; direct Windows pytest has a known local temp ACL issue. |
| Offline evals | Yes | `evals/ai_cookbook/run_evals.py`, [AI evals plan](ai-evals-plan.md) | Covers dataset ask, saved-recipe ask, importer, meal plan, citations, no-match cases, and secret-like leakage checks. |
| Manual live OpenAI smoke | Yes | `scripts/smoke-openai-live.py`, [Manual Live OpenAI Smoke Tests](live-openai-smoke-tests.md) | Manual-only, budget-capped, opt-in validation has a recorded passing run. |
| Demo scripts/docs | Yes | `scripts/demo-ai-mock.ps1`, `scripts/demo-ai-live-smoke.ps1`, `scripts/demo-ai-requests.http`, [AI demo walkthrough](ai-demo-walkthrough.md) | Mock demo is safe by default; live wrapper skips unless explicitly opted in. |
| Portfolio README | Yes | [README](../README.md), [AI portfolio showcase](ai-portfolio-showcase.md) | Repository landing page now explains the AI value, evidence, commands, and boundaries. |
| Security/secrets hygiene | Yes | `scripts/validate-repo.sh`, outbox reports, `.gitignore`, [AI screenshot capture guide](ai-screenshot-capture-guide.md) | No provider keys, private env files, raw datasets, generated indexes, or screenshots are committed. |
| Data boundaries | Yes | [Shared infrastructure data boundaries](shared-infrastructure-data-boundaries.md), [Local recipe dataset adapter](local-recipe-dataset-adapter.md), tests | Saved-recipe and dataset workflows use generated fixtures for validation and do not mutate production data. |
| Known limitations | Documented | This document, [AI feature status](ai-feature-status.md), [AI implementation backlog](ai-implementation-backlog.md) | Production storage, UI integration, embeddings/vector DB, screenshots, and deployment changes are deferred. |

## Recorded Live Validation

```text
provider=openai
model=gpt-5.4-nano
live_calls=4
estimated_usage_tokens=1200
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

## Current Validation

Current validation for this review:

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Known local issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Direct Windows pytest collected 82 tests and failed during `tmp_path` setup with `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`.
  - 45 tests passed before 37 temp-fixture setup errors.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `82 passed` for `ai-api\tests`, offline evals, Markdown link checks, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`

## Deferred Items

These are intentionally not part of the completed feature slice:

- production storage architecture;
- deployment changes;
- Cloudflare changes;
- controller/demo launch workflows;
- GitHub Actions live provider tests;
- Qdrant;
- Postgres;
- pgvector;
- embeddings;
- vector database;
- persistent generated indexes;
- UI rewrite;
- screenshots unless safely generated later;
- real raw dataset commits;
- provider key commits.

## Conclusion

The current AI phase is complete as a demoable, evidence-backed sidecar feature slice. Future work should be treated as separately scoped platform or product hardening, not as missing acceptance criteria for this phase.
