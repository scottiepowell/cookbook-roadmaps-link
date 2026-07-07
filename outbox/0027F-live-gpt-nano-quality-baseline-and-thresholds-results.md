# 0027F Live GPT-Nano Quality Baseline And Thresholds Results

## Summary

Completed `0027F` by preserving the first successful live `gpt-5.4-nano` demo eval as a sanitized baseline and tightening live-eval quality gates for correctness, answer usefulness, latency, token usage, cost visibility, and demo readiness.

The requested local inbox file `inbox/0027F-live-gpt-nano-quality-baseline-and-thresholds.md` was not present at the start of this local run. It was added on `origin/main` during the final rebase, then read and checked against this implementation before push.

## Files Changed

- Added `docs/live-openai-demo-baseline-2026-07-07.md`.
- Updated `docs/live-openai-demo-evals.md`.
- Updated `evals/ai_cookbook/expected_checks.py`.
- Updated `evals/ai_cookbook/live_cases.json`.
- Updated `scripts/live-openai-demo-evals.py`.
- Updated `ai-api/app/demo_data.py`.
- Updated `ai-api/app/dataset_retrieval.py`.
- Updated `ai-api/tests/test_live_openai_demo_evals.py`.
- Updated `docs/ai-feature-status.md`.
- Updated `docs/ai-implementation-backlog.md`.
- Updated `README.md`.
- Added `outbox/0027F-live-gpt-nano-quality-baseline-and-thresholds-results.md`.

## Sanitized Baseline

Added `docs/live-openai-demo-baseline-2026-07-07.md` with:

- run date/time;
- expected model;
- overall result;
- workflow table;
- response quality notes;
- token and latency table;
- known limitations;
- next tuning targets.

The baseline does not include local private filesystem paths, raw generated artifacts, raw secrets, environment file contents, API keys, or generated response JSON.

Baseline summary:

- Created: `2026-07-07T18:47:37.881688+00:00`
- Expected model: `gpt-5.4-nano`
- Overall result: pass
- Workflows passed: 6/6
- Total latency: 9967 ms
- Total tokens: 1423
- Estimated cost USD: not available because local pricing env vars were not provided

## Quality Checks Added

Importer:

- title should not be a generic placeholder;
- description should mention at least two input ingredients;
- notes should mention missing quantities or unspecified details when source input is sparse;
- instructions should be concise and action-oriented;
- ingredient names should not include unrelated foods.

Ask My Cookbook:

- answer should be concise;
- answer should not claim more than retrieved citations support;
- answer should include recipe titles from citations;
- answer should not include unsupported saved recipe titles.

Dataset Ask/RAG:

- answer should include cited source title;
- answer should include source id or enough provenance for traceability;
- answer should not introduce unsupported dataset titles.

Meal Planner:

- selected meal title should match cited recipe title;
- reason should refer to user preference;
- selected recipe ids must be a subset of retrieved candidate ids;
- plan should not include invented extra meals.

## Threshold Checks Added

Defaults:

| Setting | Default | Severity |
| --- | ---: | --- |
| `TOTAL_LATENCY_MS_WARN` | 15000 | warning |
| `IMPORTER_LATENCY_MS_WARN` | 7000 | warning |
| `WORKFLOW_LATENCY_MS_FAIL` | 10000 | failed check |
| `TOTAL_TOKENS_WARN` | 2500 | warning |
| `IMPORTER_TOKENS_WARN` | 900 | warning |
| `WORKFLOW_TOKENS_FAIL` | 1200 | failed check |

Thresholds are configurable through environment variables. Warning thresholds are recorded without failing the run; failure thresholds append failed checks to affected workflow records.

## Cost Visibility

Cost estimation remains opt-in through local environment rates:

```powershell
$env:OPENAI_INPUT_COST_PER_1M_TOKENS="<current input rate>"
$env:OPENAI_OUTPUT_COST_PER_1M_TOKENS="<current output rate>"
```

No volatile provider pricing rates were hardcoded into source code.

## Generated Demo Fixture Warning Noise

Generated demo dataset fixtures now include a marker file. When that marker is present, warnings for missing optional files are filtered:

- `13k-recipes.db`
- `5k-recipes.db`
- `metadata.json`
- `README.md`
- `tutorial.md`

Real dataset directories without the generated-demo marker still emit the original warnings.

## Offline Tests Added

Updated `ai-api/tests/test_live_openai_demo_evals.py` to cover:

- quality checks passing on representative useful responses;
- quality checks failing on placeholder, unrelated, or unsupported responses;
- threshold warnings and failures;
- generated demo fixture warning filtering;
- result writing under ignored generated paths;
- secret and private-path artifact checks.

## Validation Results

- Passed: `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
  - Offline evals passed: 9 cases.
- Failed as expected on the known local Windows temp-directory ACL issue: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`
  - Exact root error: `PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'`
  - The command collected 102 tests; 64 passed before 38 `tmp_path` setup errors.
  - The updated `test_live_openai_demo_evals.py` tests passed in this run.
- Passed targeted: `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_live_openai_demo_evals.py`
  - 12 passed.
- Passed: `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - Includes `102 passed` for `ai-api\tests`.
  - Includes offline evals, shell script syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- Passed: `git diff --check`
- Passed: `docker compose config --quiet`
- Passed: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
  - Offline evals plus health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal plan endpoint checks passed.
  - Generated demo fixture dataset warning count is now `0` for dataset search and dataset ask in the mock demo path.
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
  - Output: `Live smoke skipped: set OPENAI_ENABLE_LIVE_TESTS=true to opt in.`
- Passed clean skip: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`
  - Output begins: `SKIP: OPENAI_ENABLE_LIVE_TESTS=true is required.`

Normal validation stayed offline. Live OpenAI calls were not run.

## Live Run Status

No live OpenAI calls were run during this task. Normal validation should keep `scripts\run-openai-demo-evals.ps1` in skip mode unless live opt-in settings are explicitly present.

## Known Limitations

- Cost estimation remains `None` unless local pricing-rate environment variables are provided.
- The baseline is based on generated demo fixtures, not production cookbook data.
- The usefulness checks are deterministic heuristics, not full human review.
- The generated-demo warning filter depends on the generated fixture marker and intentionally does not suppress warnings for real dataset directories.

## Recommended Next Task

`0027G: Live Demo Cost Visibility And Regression Comparison`

Suggested scope:

- add an explicit baseline comparison command;
- compare new live eval runs against the sanitized baseline;
- show latency/token/cost deltas;
- require local pricing rates for cost reporting;
- produce a compact operator regression summary.

## Safety Confirmation

- No `.tmp-ai-demo` live eval artifacts are committed.
- No generated response JSON is committed.
- No raw Kaggle dataset files are committed.
- No screenshots are committed.
- No browser automation was added.
- No live OpenAI calls were added to CI or normal validation.
- No private environment files, API keys, key fragments, auth headers, raw env contents, local private paths, or credentials are committed.
