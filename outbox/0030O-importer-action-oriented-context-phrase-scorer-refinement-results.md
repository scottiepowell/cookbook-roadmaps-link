Title: 0030O Importer Action-Oriented Context Phrase Scorer Refinement Results

Summary

- Refined the importer live-eval action-oriented scorer so realistic instructions with a short setup phrase before an early imperative verb no longer false-fail.
- Preserved the aggregate conciseness policy from `0030N`.
- Preserved the importer token-threshold behavior from `0030M`.
- Preserved the safe diagnostics behavior from `0030L`.

False Failure Addressed

- Observed live importer failure detail:
  - `max_words=25 average_words=17.3 compact_steps=7/7 action_oriented=6/7`
- The failing shape was a realistic step like:
  - `In a small bowl, mix olive oil with minced garlic, then stir into the warm beans. Cook 1-2 minutes, just until fragrant.`
- The previous scorer treated the leading setup phrase as if the step had to begin directly with the imperative verb.

Action-Oriented Scorer Refinement

- Direct imperative starts still pass.
- Colon-labeled steps from `0030M` and `0030N` still pass.
- Short setup or context phrases before an early imperative verb now pass.
- Supported patterns include:
  - `In a medium saucepan, warm...`
  - `On a baking sheet, arrange...`
  - `With a spoon, mash...`
  - `If the mixture seems thick, add...`
  - `After the beans are warm, stir...`
- Rambling paragraphs with only a late action verb still fail.

Safe Failure Detail

- The instruction-quality check still reports safe metrics:
  - `max_words`
  - `average_words`
  - `compact_steps`
  - `action_oriented`
- It now also reports bounded failed step indexes when useful, such as:
  - `action_failed_steps=2`
- No raw prompts, raw provider responses, keys, `.env` contents, or local absolute paths are included.

Tests Added Or Updated

- Added a fixture for the exact observed 7-step live importer instruction set and verified it passes.
- Added coverage proving:
  - short context phrases before an early imperative verb pass;
  - direct action-verb starts still pass;
  - colon-labeled steps still pass;
  - `saute` and `sauté` still pass;
  - non-action instructions still fail;
  - late-action-verb rambling paragraphs still fail;
  - empty and placeholder instructions still fail;
  - importer token-threshold behavior from `0030M` remains unchanged;
  - safe diagnostics from `0030L` remain intact.

Docs Updated

- `docs/live-openai-demo-evals.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

Validation Results

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
- No prompt changes
- No GLM integration
- No secondary-provider routing
- No auth, billing, storage, or public route changes
- No live calls added to normal validation

Artifact Safety Confirmation

- No `.env` file committed
- No API keys or key fragments committed
- No raw provider prompts committed
- No raw provider responses committed
- No `.tmp-ai-demo` artifacts committed
- No logs or screenshots committed
- No local absolute paths added to public docs examples by this task

Recommendation

- `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.
- Use the `0030O` context-phrase refinement together with the `0030N` conciseness policy, `0030M` importer token thresholds, and `0030L` safe diagnostics as the importer baseline for future comparison.
