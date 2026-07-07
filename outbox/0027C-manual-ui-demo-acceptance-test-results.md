# 0027C Manual UI Demo Acceptance Test Results

## Summary

Completed `0027C` as a manual acceptance checklist and report task.

Manual URL testing was not completed by Codex. Human-run URL testing is pending. This is intentional for the recovery run because browser automation, browser tools, long-running server launch work, and live OpenAI calls were excluded.

`0027A` and `0027B` are complete. The next human step is to open the documented `/demo` URL and run the 15-minute and 30-minute flows.

## Files Changed

- Added `docs/ai-manual-ui-acceptance-test.md`.
- Added `outbox/0027C-manual-ui-demo-acceptance-test-results.md`.

No production infrastructure changes were made.

## Manual URL Testing Status

| Field | Result |
| --- | --- |
| Manual URL testing by Codex | Not completed |
| Human-run URL testing | Pending |
| Local URL | Pending human test; planned default: `http://127.0.0.1:8000/demo` |
| Deployed URL | Pending human test; fill if the sidecar demo route is publicly exposed |
| Browser used | Pending human test |
| Provider mode tested | Pending human test: mock, OpenAI, or both |
| Date/time of test | Pending human test |

## Acceptance Checklist Status

The full acceptance checklist from `inbox/0027C-manual-ui-demo-acceptance-test.md` is captured in `docs/ai-manual-ui-acceptance-test.md`.

Current status for every user-facing checklist item: pending human test.

Checklist coverage includes:

- Page loads without browser console errors.
- Layout is usable on a laptop screen.
- Health/config status is understandable.
- Provider mode is clear: mock vs OpenAI.
- Importer flow works with sample input.
- Ask My Cookbook flow works or clearly explains missing saved-recipe data.
- Dataset search works or clearly explains missing dataset data.
- Dataset ask/RAG works or clearly explains missing dataset data.
- Meal planner works or clearly explains missing saved-recipe data.
- Loading states appear while requests run.
- Buttons are disabled while requests run.
- Reset buttons work.
- Errors are user-friendly and do not show raw stack traces.
- Citations/provenance are readable.
- Warnings are visible and useful.
- Raw JSON is available but not the primary user experience.
- Logs show useful request IDs and workflow metadata.
- No sensitive runtime values, private local paths, raw keys, or private data are visible in the UI or logs.
- The UI is screenshot-ready with demo-safe data.

## 15-Minute Flow Status

Pending human test.

Human next steps:

1. Open the UI.
2. Check readiness, health, and provider config.
3. Run importer.
4. Run dataset search.
5. Run dataset ask.
6. Run meal planner or saved-recipe ask if data is available.
7. Open logs and confirm request IDs and workflow events.
8. Capture observations.

## 30-Minute Flow Status

Pending human test.

Human next steps:

1. Run all 15-minute checks.
2. Try alternate sample inputs.
3. Trigger at least one friendly error path.
4. Test missing-data handling if possible.
5. Test reset buttons.
6. Confirm outputs remain readable after several runs.
7. Confirm no confusing stale state remains between workflow runs.

## Logging Verification Status

Pending human test.

Use:

```powershell
docker compose logs ai-api --tail 100
```

Confirm logs include safe operational metadata:

- request ID;
- endpoint/workflow;
- status;
- duration;
- provider/model when available;
- retrieved/citation/warning counts when available.

Confirm logs do not include large raw user payloads by default and do not expose API keys, credentials, private paths, or private data.

## Screenshot Readiness Status

Pending human test.

No screenshots were captured or committed during this recovery task.

## Issues Found

No new UI defects were observed by Codex because manual URL testing was not performed.

Expected items for human verification:

- Local `/demo` route opens and renders the full workflow UI.
- Deployed `/demo` route is exposed, or a deployment exposure gap is recorded.
- Missing saved-recipe or dataset data is explained clearly in the UI.
- Logs remain useful and safe during UI workflows.

## Recommended Follow-Up Task

`0027D: Human UI Demo Findings And Fixes`

Use 0027D after human URL testing to fix observed UI defects, copy issues, screenshot-readiness gaps, missing-data handling issues, logging clarity issues, or deployment route exposure gaps.

## Validation Results

Validation completed for this recovery run:

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 89 tests; 52 passed before 37 `tmp_path` setup errors.
- Passed after rerun outside the sandbox because Git Bash could not start in the sandbox with `couldn't create signal pipe, Win32 error 5`: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `89 passed` for `ai-api\tests`.
  - Includes offline evals, shell script syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`

Normal validation stayed offline. The live smoke wrapper skipped because live OpenAI tests were not explicitly opted in.

## Safety Confirmation

- Browser automation was not run.
- In-app browser tools were not used.
- No long-running server was launched.
- Live OpenAI calls were not run.
- No private environment files, raw datasets, generated artifacts, screenshots, logs, or credentials were added.
