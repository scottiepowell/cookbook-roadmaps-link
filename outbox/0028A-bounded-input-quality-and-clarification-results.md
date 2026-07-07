# 0028A: Bounded Input Quality And Clarification Results

Status: complete.

## Summary

Added deterministic input-quality handling for weak, vague, malformed, and nonsensical input across the cookbook AI workflows. Bad input is rejected before provider calls, vague recoverable input returns exactly one clarification question, weak usable input proceeds with warnings, and valid input continues through existing paths.

## Files Changed

- `ai-api/app/input_quality.py`
- `ai-api/app/schemas.py`
- `ai-api/app/importer.py`
- `ai-api/app/rag.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/dataset_rag.py`
- `ai-api/app/meal_plan_endpoint.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_input_quality.py`
- `ai-api/tests/test_dataset_ask.py`
- `ai-api/tests/test_dataset_search_api.py`
- `ai-api/tests/test_importer.py`
- `ai-api/tests/test_rag.py`
- `evals/ai_cookbook/run_evals.py`
- `scripts/live-openai-demo-evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`
- `outbox/0028A-bounded-input-quality-and-clarification-results.md`

## Input-Quality Statuses Added

- `ready`
- `weak_but_usable`
- `needs_clarification`
- `rejected`

## Deterministic Checks Added

- Empty or whitespace-only input.
- No alphabetical characters.
- Mostly symbols.
- Repeated junk and obvious placeholders.
- Too-short input.
- Configured maximum length checks.
- Vague meal/cooking phrases that need one bounded clarification.
- Weak but usable short cooking inputs that can proceed with warnings.

## Endpoint Behavior Changes

- `POST /ai/import-recipe`: rejects or clarifies before provider calls; weak input includes warnings.
- `POST /ai/ask`: rejects or clarifies before recipe retrieval/provider calls.
- `GET/POST /dataset/search`: rejects or clarifies before dataset inspection; no provider is involved.
- `POST /dataset/ask`: rejects or clarifies before dataset retrieval/provider calls.
- `POST /ai/meal-plan`: rejects or clarifies before saved-recipe loading/provider calls; weak preferences proceed with warnings.

## UI Behavior Changes

- The demo UI renders `needs_clarification` as a "Needs one more detail" card.
- The demo UI renders `rejected` as an "Input not usable yet" card.
- Recovery guidance and raw JSON remain available without showing stack traces or provider errors.

## Eval Cases Added

Offline evals now cover:

- empty importer input;
- symbol-only importer input;
- vague importer input;
- weak but usable importer input;
- empty saved-recipe question;
- vague meal planner preferences;
- nonsense dataset search;
- valid classifier input.

## Provider-Call Avoidance Behavior

Rejected and clarification responses return `provider="none"` and do not call the injected provider. Tests use failing providers to prove deterministic bad-input paths do not call text or structured generation.

## Metrics Added

Live eval records now include:

- `input_quality_status`
- `input_quality_reason`
- `clarification_question_present`
- `rejected_before_provider`
- `provider_called`

## Tests Added

- Classifier status tests.
- Empty, whitespace, no-alpha, symbol-heavy, too-short, vague, weak, and valid input tests.
- Importer rejection and clarification tests.
- Meal planner vague preference tests.
- Dataset search bad-query provider-avoidance tests.
- Live eval metadata tests.

## Validation

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 17 offline eval cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: direct Windows run hit the known pytest temp ACL issue; 71 tests passed and 38 tests errored during fixture setup.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed, including 109 AI API tests, 17 offline eval cases, shell syntax, Docker Compose config, whitespace, Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly without live opt-in.

## Live OpenAI

No live OpenAI calls were run for this task.

## Known Limitations

- The classifier is deterministic and intentionally conservative; future tuning may adjust vague/weak thresholds from real demo findings.
- No multi-turn state is stored; the returned clarification question is a one-shot recovery prompt for the operator/user to resubmit.
- Input-quality checks are not a full abuse, safety, or policy classifier.

## Recommended Next Task

0028B: Input Quality Tuning From Human Demo Findings.

## Artifact Safety

No private env files, API keys, raw datasets, generated live results, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts were committed.
