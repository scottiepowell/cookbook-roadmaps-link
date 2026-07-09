# 0028C: Live Eval Regression Notes And Acceptance Baseline Results

Status: complete.

## Summary

Added sanitized project evidence for the post-`0028A` live eval regression, the `0028B` importer-check fix, and the latest passing post-`0028B` live GPT-nano acceptance run. No runtime behavior changes were made.

## Files Changed

- `docs/live-openai-demo-regression-notes-2026-07-08.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/live-openai-demo-evals.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0028C-live-eval-regression-notes-and-acceptance-baseline-results.md`

## Failed Run Recorded

Recorded the post-`0028A` failed live run from `2026-07-08T12:59:55.107559+00:00`:

- overall result: failed;
- workflows passed: 5/6;
- failed workflow: importer;
- failed check: `description should mention at least two input ingredients - mentioned=[]`;
- total latency: 10245 ms;
- total tokens: 1452;
- estimated cost USD: 0.0007125;
- threshold warnings: 0;
- threshold failures: 0.

## Root Cause Recorded

Documented the root cause as evaluator brittleness rather than model-quality failure. The generated importer draft preserved the input ingredients in structured fields, but the evaluator only looked for ingredient evidence in `description`, which was absent.

## 0028B Fix Recorded

Recorded the `0028B` fix from commit `682483746d4c98857fed5684c8c564f87f971f74`:

- ingredient evidence can now come from title, description, ingredient names, and instructions;
- description grounding is checked only when a description is present;
- alias-aware ingredient evidence covers white beans, olive oil, garlic, lemon, parsley, and toast;
- generic placeholders, unrelated foods, and truly ungrounded outputs still fail.

## Passing Acceptance Run Recorded

Recorded the post-`0028B` passing live GPT-nano run from `2026-07-08T13:40:41.967056+00:00`:

- overall result: passed;
- workflows passed: 6/6;
- total latency: 9615 ms;
- total tokens: 1467;
- estimated cost USD: 0.0007029;
- threshold warnings: 0;
- threshold failures: 0;
- failed checks: none.

## Acceptance Matrix Summary

Current acceptance evidence is documented for:

- mock demo;
- seeded local UI demo;
- live OpenAI eval;
- default cost estimate;
- latency thresholds;
- token thresholds;
- input quality guardrails;
- importer eval robustness;
- provider-call avoidance.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 17 cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: known Windows temp ACL issue; 112 tests collected, 74 passed, 38 setup errors rooted in `PermissionError: [WinError 5] Access is denied` on the per-user pytest temp directory.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed; includes 112 API tests passed and 17 offline eval cases passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed; offline evals and endpoint smoke checks passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live eval opt-in settings were not present.

## Live OpenAI

No live OpenAI calls were run during this task. The task records the already-provided live run summaries only.

## Recommended Next Task

0029A: Production access metering and time-limited AI sessions architecture.

## Artifact Safety

No generated live eval artifacts, raw response JSON, API keys, private environment files, raw datasets, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts were committed.
