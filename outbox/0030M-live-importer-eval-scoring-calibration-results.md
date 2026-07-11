Title: 0030M Live Importer Eval Scoring Calibration Results

Summary

- Calibrated the live importer eval scorer so valid structured recipe drafts no longer false-fail on common cooking verbs or short labeled steps.
- Split importer token failure thresholds from the stricter generic workflow threshold used by shorter answer workflows.
- Preserved the safe failure diagnostics from `0030L`.
- Tightened the live-script boundary so the Python live helpers no longer auto-read `repo_root/.env`; live mode still requires explicit process env or wrapper `-EnvFile` opt-in.

False Failure Addressed

- Observed live importer output shape:
  - title like `Lemon Herb White Beans with Toast`
  - structured ingredients
  - six concise instructions beginning with verbs such as `Warm`, `Saute`, `Brighten`, `Finish`, `Prepare`, and `Serve`
  - citations and retrieval metadata present
  - total token usage around `1428`
- Previous false failures were caused by:
  - a narrow action-verb allowlist;
  - step-label handling that rejected forms like `Brighten with lemon: Stir in lemon juice and zest.`;
  - a single workflow token failure threshold that was too low for structured importer JSON plus retrieval metadata.

Instruction Scorer Calibration

- Expanded accepted recipe imperatives to include verbs such as `saute`, `sauté`, `prepare`, `brighten`, `season`, `drizzle`, `mash`, `fold`, `adjust`, `cover`, `rest`, and `garnish`.
- Added normalization so accented and unaccented forms like `sauté` and `saute` are both accepted.
- Added short colon-label support so either the label or the post-colon phrase can satisfy the action-oriented check.
- Kept meaningful failures:
  - empty instructions still fail;
  - placeholder instructions still fail;
  - rambling or overly long steps still fail;
  - non-action instructions still fail;
  - unrelated food hallucination checks and safety checks remain intact.

Importer-Specific Token Thresholds

- `IMPORTER_TOKENS_WARN=1500`
- `IMPORTER_TOKENS_FAIL=1800`
- `WORKFLOW_TOKENS_FAIL=1200` remains the generic failure threshold for non-importer workflows.
- Thresholds remain environment-configurable.
- Estimated cost behavior is unchanged.

Tests Added Or Updated

- Added focused importer eval tests in `ai-api/tests/test_live_openai_demo_evals.py` to verify:
  - the sanitized observed live importer output shape passes;
  - `saute` and `sauté` both pass;
  - colon-labeled steps pass when action-oriented;
  - rambling instructions still fail;
  - non-action instructions still fail;
  - importer token usage around `1428` does not fail by default;
  - importer usage above `IMPORTER_TOKENS_FAIL` still fails;
  - non-importer workflows still use the generic workflow token failure threshold;
  - environment threshold overrides still work.

Docs Updated

- `docs/live-openai-demo-evals.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `docs/live-openai-smoke-tests.md`
- `README.md`

Safe Diagnostics Preserved

- Live eval failure summaries still distinguish:
  - threshold failure
  - provider call failure
  - structured output cap or incomplete response
  - invalid JSON
  - budget blocked before provider invocation
  - validation or schema failure

Validation Results

- `python -m pytest ai-api/tests/test_live_openai_demo_evals.py -q`: passed
- `python evals/ai_cookbook/run_evals.py`: passed
- `powershell -File scripts/test-ai-env-file-loader.ps1`: passed
- `python scripts/e2e-ai-29-30-regression.py`: passed
- `bash scripts/validate-repo.sh`: passed
- `git diff --check`: passed
- `docker compose config --quiet`: passed
- `powershell -File scripts/demo-ai-mock.ps1`: passed
- `powershell -File scripts/demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in
- `powershell -File scripts/run-openai-demo-evals.ps1`: skipped cleanly without live opt-in

Optional Live Manual Result

- Not rerun as part of normal validation.
- Expected live success after this calibration, if provider output is comparable to the observed structured draft, remains:
  - `Overall passed: True`
  - `Workflows passed: 6/6`

Explicit Non-Goals

- No GLM provider integration
- No secondary-provider routing
- No public route exposure
- No payment, ad, sponsor, or affiliate runtime code
- No production auth or storage changes
- No live provider calls added to normal validation

Artifact Safety Confirmation

- No `.env` file committed
- No API keys or key fragments committed
- No raw provider prompts committed
- No raw provider responses committed
- No `.tmp-ai-demo` artifacts committed
- No screenshots or logs committed
- No local absolute paths added to public docs examples

Recommendation

- `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.
- Use the calibrated importer scoring and workflow-specific importer token thresholds from `0030M` as the baseline comparison point.
