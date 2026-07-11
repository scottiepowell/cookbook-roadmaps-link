Title: 0030N Importer Instruction Conciseness Scorer Refinement Results

Summary

- Refined the importer live-eval instruction scorer so realistic structured recipe steps no longer fail only because one or two steps include a short label plus a useful clause.
- Kept the importer token thresholds from `0030M` unchanged.
- Preserved the safe provider diagnostics from `0030L`.

Scorer Changes

- Replaced the brittle `all steps <= 24 words` rule with a bounded aggregate policy:
  - every non-empty step must still be action-oriented;
  - any individual step above `45` words fails;
  - average step length must stay at or below `28` words;
  - most steps must remain compact, with compact-step coverage measured against the full step text;
  - empty steps and placeholder steps still fail.
- Added placeholder-step detection for clearly generic filler such as `Cook until done.` and `Serve and enjoy.`

Colon-Label Handling

- Colon-labeled steps remain valid when otherwise concise and action-oriented.
- Labels are not a loophole for rambling instructions because the scorer now measures full-step length for the max, average, and compact-step metrics.

Failure-Detail Improvements

- The importer instruction quality check now reports safe detail metrics such as:
  - `max_words`
  - `average_words`
  - `compact_steps`
  - `action_oriented`
- Failure details can also include bounded counts like `empty_steps` or `placeholder_steps`.
- No raw prompts, raw provider responses, keys, `.env` contents, or local absolute paths are included.

Tests Added Or Updated

- Updated the sanitized live importer fixture to use the observed realistic instruction shape and verified it passes.
- Added coverage that proves:
  - a realistic labeled live importer instruction set passes;
  - labeled steps and common cooking verbs still pass;
  - `saute` and `sauté` both pass;
  - one longer `33`-word step can pass when the overall set remains compact;
  - a single extremely long step still fails;
  - many rambling steps still fail;
  - non-action steps still fail;
  - empty steps still fail;
  - generic placeholder steps still fail;
  - importer token thresholds from `0030M` remain unchanged;
  - safe diagnostics from `0030L` remain intact.

Docs Updated

- `docs/live-openai-demo-evals.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Validation

- `python -m pytest ai-api/tests/test_live_openai_demo_evals.py -q`: passed
- `python evals/ai_cookbook/run_evals.py`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-ai-env-file-loader.ps1`: passed
- `python scripts/e2e-ai-29-30-regression.py`: passed
- `bash scripts/validate-repo.sh`: passed
- `git diff --check`: passed
- `docker compose config --quiet`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1`: skipped cleanly without live opt-in

Explicit Non-Goals

- No provider behavior changes
- No model routing changes
- No GLM integration
- No secondary-provider routing
- No live opt-in changes
- No auth, billing, storage, or public route changes

Artifact Safety

- No `.env` file committed
- No provider keys or key fragments committed
- No raw provider prompts committed
- No raw provider responses committed
- No `.tmp-ai-demo` artifacts committed
- No logs or screenshots committed
- No local absolute paths added to public docs examples by this task

Recommendation

- `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.
- Use the `0030N` importer conciseness scorer as part of the locked baseline comparison, alongside the `0030M` importer token-threshold calibration and the `0030L` safe diagnostics behavior.
