# 0026A Add AI Demo Walkthrough And Scripts Results

## Summary

Completed the AI cookbook demo-readiness task. The requested inbox file was not present locally at the start of the task, so a local copy was created from the prompt before implementation. During the final rebase, `origin/main` already contained a fuller copy of `inbox/0026A-add-ai-demo-walkthrough-and-scripts.md`, and that remote version was kept.

Added a mock/offline demo path, an optional manual live-smoke wrapper, REST request examples, a feature status matrix, and a five-minute walkthrough for portfolio, interview, or customer conversations.

## Changes

- Added `scripts/demo-ai-mock.ps1`.
- Added `scripts/demo-ai-live-smoke.ps1`.
- Added `scripts/demo-ai-requests.http`.
- Added `docs/ai-demo-walkthrough.md`.
- Added `docs/ai-feature-status.md`.
- Updated `docs/ai-implementation-backlog.md` with 0026A status.
- Updated `docs/repo-map.md` with demo docs and scripts.
- Updated `README.md` with AI demo links and mock demo command.
- Confirmed `inbox/0026A-add-ai-demo-walkthrough-and-scripts.md` after rebase.

## Demo Coverage

The mock demo path runs offline evals and generated-fixture endpoint checks for:

- AI sidecar health/config.
- Structured recipe importer.
- Ask My Cookbook over saved recipes.
- Local dataset search.
- Dataset Ask/RAG with citations.
- Saved-recipe meal planning.

The live demo wrapper delegates to `scripts/smoke-openai-live.py` and remains manual-only. Without explicit opt-in, it exits cleanly without live calls.

## Validation

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
- Failed as expected on the known local Windows temp-directory issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 82 tests; tests using `tmp_path` errored during fixture setup.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `82 passed` for `ai-api\tests`.
  - Includes offline evals.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`

## Safety Checks

- No production storage architecture was added.
- No deployment, Cloudflare, GitHub Actions live provider, controller/demo launch, TTL cleanup, or UI changes were added.
- No Qdrant, Postgres, pgvector, embeddings, or vector database was added.
- No raw dataset files, generated index artifacts, private environment files, or provider keys were added.
