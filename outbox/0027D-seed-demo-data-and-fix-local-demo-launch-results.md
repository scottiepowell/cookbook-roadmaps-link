# 0027D Seed Demo Data And Fix Local Demo Launch Results

## Summary

Completed `0027D` by adding a generated local demo data seed path and a clear local browser demo launch command.

Human testing after `0027C` showed the UI loaded and most workflows worked, but saved recipes were unavailable. This task fixes the local mock demo path so Ask My Cookbook and Meal Planner can run with small, generated, demo-safe saved recipes.

## Files Changed

- Added `ai-api/app/demo_data.py`.
- Added `scripts/seed-ai-demo-data.ps1`.
- Added `scripts/start-ai-demo-local.ps1`.
- Updated `scripts/demo-ai-mock.ps1`.
- Updated `ai-api/app/static/demo.html`.
- Updated `ai-api/app/static/demo.js`.
- Updated `ai-api/tests/test_demo_ui.py`.
- Updated `docker-compose.yml`.
- Updated `.gitignore`.
- Updated `README.md`.
- Updated `docs/ai-live-demo-runbook.md`.
- Updated `docs/ai-manual-ui-acceptance-test.md`.
- Updated `docs/ai-ui-integration-plan.md`.
- Updated `docs/ai-feature-status.md`.
- Updated `docs/ai-demo-walkthrough.md`.
- Updated `docs/ai-implementation-backlog.md`.

## Implementation Notes

- `app.demo_data` generates a small SQLite saved-recipe fixture and a small CSV dataset fixture.
- The default generated fixture location is `.tmp-ai-demo/local`.
- `.tmp-ai-demo/` is ignored by Git.
- The seed path does not write to production cookbook data.
- The local launch script sets `AI_PROVIDER=mock`, `COOKBOOK_DB_PATH`, `RECIPE_DATASET_DIR`, and `RECIPE_DATASET_INDEX_LIMIT` for the sidecar process.
- The local launch script starts the sidecar on `127.0.0.1:8000`.
- Docker Compose now exposes `ai-api` locally as `127.0.0.1:8000:8000`.
- Dataset UI samples were changed from `lemon beans` to `tomato pasta` for more intuitive demo results.

## Operator Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Then open:

```text
http://127.0.0.1:8000/demo
```

## Expected Local Readiness

- Sidecar: healthy.
- Provider: `mock / mock-basic`.
- Saved recipes: at least 3 recipe(s).
- Dataset: available.

## Acceptance Criteria Status

| Criterion | Status |
| --- | --- |
| Local demo operator has a clear command to start the AI demo. | Complete |
| `/demo` opens reliably at the documented local URL. | Documented; pending human URL re-test |
| Readiness shows saved recipes available in demo mode. | Covered by TestClient test with generated fixture |
| Ask My Cookbook returns a readable answer with citations in mock demo mode. | Covered by TestClient test with generated fixture |
| Meal Planner returns a readable plan with citations in mock demo mode. | Covered by TestClient test with generated fixture |
| Dataset Search/RAG still works. | Covered by mock demo script and existing tests |
| Error handling still works. | Existing friendly error path retained |
| Logs remain safe and useful. | Existing structured logging retained |
| No secrets, private env files, raw datasets, generated artifacts, screenshots, or credentials are committed. | Complete |

## Human Follow-Up

Human-run browser testing is still needed after this code change:

1. Run `scripts\start-ai-demo-local.ps1`.
2. Open `http://127.0.0.1:8000/demo`.
3. Confirm readiness shows saved recipes and dataset available.
4. Run importer, Ask My Cookbook, Dataset Search, Dataset Ask/RAG, and Meal Planner.
5. Confirm citations/provenance, raw JSON details, loading states, reset buttons, and logs.
6. Record any remaining findings in a later human UI findings task.

## Validation Results

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 90 tests; 52 passed before 38 `tmp_path` setup errors.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `90 passed` for `ai-api\tests`.
  - Includes offline evals, shell script syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`
- Passed targeted seed check: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\seed-ai-demo-data.ps1 -OutputDir .tmp-ai-demo\check`

Normal validation stayed offline. The live smoke wrapper skipped because live OpenAI tests were not explicitly opted in.

## Safety Confirmation

- No production cookbook data is written.
- No raw Kaggle dataset files are committed.
- No generated SQLite or CSV fixtures are committed.
- No screenshots, generated artifacts, logs, private environment files, provider keys, or credentials are committed.
