# 0027B Production-Quality AI Demo Usability Results

## Summary

Hardened the AI demo UI from 0027A into a guided, production-quality browser demo suitable for a 15 to 30 minute hands-on walkthrough. The work remains product-facing and demo-focused: no production storage, deployment changes, Cloudflare changes, control-plane workflows, live CI provider tests, vector infrastructure, upstream Vanilla Cookbook frontend rewrite, browser automation, screenshots, raw dataset commits, generated artifact commits, private environment file commits, or credential commits were added.

## Files Changed

- Updated `ai-api/app/main.py`.
- Updated `ai-api/app/observability.py`.
- Reworked `ai-api/app/static/demo.html`.
- Reworked `ai-api/app/static/demo.css`.
- Reworked `ai-api/app/static/demo.js`.
- Updated `ai-api/tests/test_demo_ui.py`.
- Updated `ai-api/tests/test_observability.py`.
- Added `docs/ai-live-demo-runbook.md`.
- Updated `docs/ai-ui-integration-plan.md`.
- Updated `docs/ai-sidecar-logging.md`.
- Updated `docs/ai-screenshot-capture-guide.md`.
- Updated `docs/ai-feature-status.md`.
- Updated `docs/ai-demo-walkthrough.md`.
- Updated `docs/ai-implementation-backlog.md`.
- Updated `docs/repo-map.md`.
- Updated `README.md`.

## UI Usability Improvements

- Added a clear landing section explaining the sidecar demo.
- Added guided workflow order for importer, saved-recipe Q&A, dataset search, dataset RAG, and meal planning.
- Added sample inputs for every feature.
- Added reset controls for every feature.
- Added loading states and disabled buttons during requests.
- Replaced raw-output-first rendering with readable answer cards.
- Added dedicated citations/provenance areas.
- Added warning cards and friendly error recovery guidance.
- Moved raw JSON into expandable details.
- Improved responsive laptop-oriented styling for screenshots and live demos.
- Avoided stack traces, sensitive runtime values, and local private paths in browser output.

## Demo Readiness Behavior

Added `GET /demo/readiness` for safe readiness status:

- AI sidecar health.
- Provider mode/model.
- Offline demo mode.
- Saved-recipe availability and count.
- Local dataset availability.

The endpoint is best-effort and does not expose local paths or secret values. Missing saved-recipe or dataset data is reported as a recoverable demo condition.

## Logging Usability Improvements

- Request logs now include a safe `ui_workflow` label when the browser demo sends one.
- Operator logs can show which UI workflow ran, endpoint, request ID, status, duration, provider/model where available, retrieved count, citation count, and warning count.
- Updated logging docs with `docker compose logs ai-api --tail 100`.

## Runbook Updates

Added `docs/ai-live-demo-runbook.md` with:

- pre-demo checklist;
- mock/demo mode path;
- optional live OpenAI smoke path;
- UI open command;
- suggested 15 minute flow;
- suggested 30 minute flow;
- troubleshooting steps;
- log viewing commands;
- screenshot capture guidance;
- boundaries and non-goals.

## Tests Added Or Updated

- UI route includes major workflow sections and guided steps.
- Static assets load.
- Static UI assets do not expose sensitive placeholders.
- Readiness endpoint returns safe status without local private paths.
- Logging middleware emits `ui_workflow` when provided.
- Existing AI endpoints remain covered by the full test suite.

## Validation

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 89 tests; 52 passed before 37 `tmp_path` setup errors.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `89 passed` for `ai-api\tests`.
  - Includes offline evals, Markdown link checks, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`
- Passed targeted: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_demo_ui.py ai-api\tests\test_observability.py`

## Known Limitations

- The UI is still sidecar-served because the upstream Vanilla Cookbook frontend source tree is not in this repo.
- Saved-recipe Q&A and meal planning need configured saved-recipe data.
- Dataset search and dataset RAG need configured local dataset data.
- No browser automation or screenshots were added.
- No external logging backend was added.

## Safety Confirmation

- Normal validation remains offline and mock-only.
- Live provider calls were not run during normal validation.
- No private environment files, raw datasets, generated artifacts, screenshots, or credentials were added.

## Recommended Next Task

`0027C: Capture Safe AI Demo Screenshots With Mock Data`
