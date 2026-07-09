## Summary

Added a deterministic offline retrieval evaluation harness for the importer/recipe-creator RAG path. The harness now scores dish-specific ranking quality against generated fixture datasets, and `evals/ai_cookbook/run_evals.py` includes those cases in normal offline validation.

## Problem Observed

Manual review had already shown that importer generation quality improved, but retrieval quality still needed a measurable regression guard. The missing piece was a repeatable offline harness that could score top-1 dish match, top-k relevance, anchor coverage, generic drift, and weak-match warnings without relying on live OpenAI calls.

## Retrieval Relevance Changes

- Added `evals/ai_cookbook/retrieval_cases.yaml` with hand-maintainable cases for baked cheesecake, no-bake cheesecake, carbonara, omelet, and chicken-and-rice casserole.
- Added `evals/ai_cookbook/retrieval_eval.py` with deterministic fixture generation, retrieval scoring, relevance categorization, warning inference, and concise pass/fail summaries.
- Integrated retrieval relevance cases into `evals/ai_cookbook/run_evals.py`.
- Kept the harness offline and mock-only; it uses generated fixtures rather than the real `recipe-dataset/` folder.

## Tests Added

- `ai-api/tests/test_retrieval_eval_harness.py`
- Static UI coverage in `ai-api/tests/test_demo_ui.py` was tightened so importer citation/provenance/snippet/retrieval rendering is asserted explicitly.

## Manual Validation Notes

No live OpenAI validation was run for this task. The new offline harness reports:

- baked cheesecake top-1 strong, top-3 relevant 2/3;
- no-bake cheesecake top-1 strong, top-3 relevant 2/3;
- carbonara top-1 strong, top-3 relevant 1/3;
- omelet top-1 strong, top-3 relevant 3/3;
- chicken-and-rice casserole top-1 strong, top-3 relevant 3/3.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed: 22 offline eval cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` failed on this Windows environment with the known `pytest-of-scott` temp-directory ACL issue.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed: 148 tests, offline evals, repo validation checks.
- `git diff --check` passed; only line-ending normalization warnings were emitted.
- `docker compose config --quiet` passed via the validator and the explicit check path.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly without live opt-in.

## Remaining Limitations

- The carbonara fixture case still reports only 1/3 materially relevant results in the current deterministic ranking model, which is useful as a regression signal but shows there is still headroom in adjacent-match quality.
- Direct Windows `pytest` remains subject to the existing temp ACL issue on this machine; the Git Bash validator is the reliable path.

## Recommended Next Task

Run the full-dataset manual live importer flow with the documented `recipe-dataset` path and compare the live ranking matrix against the new offline harness baselines. After that, continue to the next planned architecture task if retrieval behavior remains stable.

## Artifact Safety Confirmation

No raw dataset files, generated live artifacts, `.tmp-ai-demo/`, secrets, env files, screenshots, logs, credentials, or provider responses were committed.
