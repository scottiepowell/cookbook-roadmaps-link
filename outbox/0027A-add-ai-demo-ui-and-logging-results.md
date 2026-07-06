# 0027A Add AI Demo UI And Logging Results

## Summary

Added the first product-facing AI integration for the FastAPI sidecar: a lightweight sidecar-served browser demo and a structured stdout logging foundation. The implementation uses existing AI endpoints only and does not add production storage, deployment changes, Cloudflare changes, controller workflows, external logging infrastructure, embeddings, vector databases, upstream Vanilla Cookbook frontend changes, screenshots, raw datasets, generated artifacts, private environment files, or credentials.

## Files Changed

- Added `ai-api/app/observability.py`.
- Updated `ai-api/app/main.py`.
- Added `ai-api/app/static/demo.html`.
- Added `ai-api/app/static/demo.css`.
- Added `ai-api/app/static/demo.js`.
- Added `ai-api/tests/test_demo_ui.py`.
- Added `ai-api/tests/test_observability.py`.
- Added `docs/ai-ui-integration-plan.md`.
- Added `docs/ai-sidecar-logging.md`.
- Updated `README.md`.
- Updated `docs/ai-feature-status.md`.
- Updated `docs/ai-demo-walkthrough.md`.
- Updated `docs/ai-portfolio-showcase.md`.
- Updated `docs/ai-implementation-backlog.md`.
- Updated `docs/repo-map.md`.

## UI Routes Added

- `GET /demo`
- `GET /demo/ai`
- Static assets under `/static/demo.html`, `/static/demo.css`, and `/static/demo.js`.

## UI Features Included

- Health/config check.
- Structured recipe importer.
- Ask My Cookbook.
- Dataset search.
- Dataset Ask/RAG.
- Meal planner.
- Provider/status display.
- Safety and data-boundary note.
- JSON response previews.
- Citations/provenance, warnings, provider/model metadata, retrieval details, and friendly error messages.

## Logging Behavior Added

- Request middleware assigns a request ID, measures duration, and emits `ai.request` JSON logs to stdout.
- Workflow handlers emit `ai.workflow` logs with safe metadata such as provider, model, retrieved count, citation count, warning count, status, and safe error type.
- Docker Compose can collect logs with `docker compose logs ai-api`.

## What Is Not Logged

The logging foundation does not log provider keys, full environment contents, authorization headers, full prompts, full pasted recipes, full provider response bodies, raw provider config, private local filesystem paths, raw dataset records, or private recipe/user data by default.

## Tests Added

- Demo UI route returns HTML.
- `/demo/ai` route returns HTML.
- Static demo CSS/JS assets load.
- Demo HTML avoids obvious sensitive-value placeholders.
- Request logging middleware emits safe fields.
- Workflow logging helper emits safe counts/provider/model metadata without raw prompt/response payload keys.

## Validation

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 88 tests; 51 passed before 37 `tmp_path` setup errors.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `88 passed` for `ai-api\tests`.
  - Includes offline evals, Markdown link checks, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`
- Passed targeted: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_demo_ui.py ai-api\tests\test_observability.py`

## Known Limitations

- The demo UI is intentionally sidecar-served because the upstream Vanilla Cookbook frontend source tree is not in this repo.
- Saved-recipe workflows need configured cookbook data; missing local data is surfaced as a friendly API/UI error.
- Dataset workflows need a configured local dataset directory for real dataset results.
- No browser automation or screenshots were added.
- No external logging backend was added.

## Safety Confirmation

- Normal validation remains offline and mock-only.
- Live provider calls were not run during normal validation.
- No private environment files, raw datasets, generated artifacts, screenshots, or credentials were added.

## Recommended Next Task

`0027B: Capture Safe AI Demo Screenshots With Mock Data`
