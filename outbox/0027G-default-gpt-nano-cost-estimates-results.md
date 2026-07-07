# 0027G: Default GPT-Nano Cost Estimates Results

Status: complete.

Note: `inbox/0027G-default-gpt-nano-cost-estimates.md` arrived after rebasing onto the latest `origin/main`; this report was updated against that inbox specification before the final commit.

## Summary

- Added maintained default cost rates for `gpt-5.4-nano`: input `0.20` USD per 1M tokens and output `1.25` USD per 1M tokens.
- Preserved operator overrides through `OPENAI_INPUT_COST_PER_1M_TOKENS` and `OPENAI_OUTPUT_COST_PER_1M_TOKENS`.
- Added `cost_source` metadata with `env_override`, `default_model_rate`, or `unavailable`.
- Kept unknown-model behavior conservative: without explicit rates, `estimated_cost_usd` remains `null`.
- Updated live eval docs, baseline notes, feature status, backlog, and README.

## Default Rates Implemented

- Model: `gpt-5.4-nano`
- Input: `0.20` USD per 1M tokens
- Output: `1.25` USD per 1M tokens
- Default table: `DEFAULT_MODEL_COST_RATES_PER_1M_TOKENS` in `evals/ai_cookbook/expected_checks.py`

## Override Behavior

When both `OPENAI_INPUT_COST_PER_1M_TOKENS` and `OPENAI_OUTPUT_COST_PER_1M_TOKENS` are set, live eval records use those values and set `cost_source` to `env_override`.

## Unknown Model Behavior

Unknown models without both rate env vars keep `estimated_cost_usd` as `null` and set `cost_source` to `unavailable`.

## Cost-Source Behavior

Each workflow record includes `cost_source`. Summaries include the unique observed cost sources, so readiness or deterministic baseline workflows can report `unavailable` while OpenAI-backed workflows report `default_model_rate` or `env_override`.

## Files Changed

- `evals/ai_cookbook/expected_checks.py`
- `scripts/live-openai-demo-evals.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0027G-default-gpt-nano-cost-estimates-results.md`

## Offline Tests Added

- Default `gpt-5.4-nano` rates.
- Env override behavior.
- Unknown model unavailable behavior.
- `cost_source` metadata in generated records and summary.
- Sub-cent estimates remain non-zero.
- Live eval skip guard behavior remains covered.

## Official Pricing Reference

- Source: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- Checked: 2026-07-07
- Applied rate: standard short-context direct OpenAI API pricing for `gpt-5.4-nano`.
- Not applied: cached-input, Batch, Flex, Priority, regional uplift, long-context, or Amazon Bedrock pricing.

## Validation

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_live_openai_demo_evals.py`: passed, 13 tests.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 9 offline eval cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: direct Windows run hit the known pytest temp ACL issue; 65 tests passed and 38 tests errored during fixture setup.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed, including 103 AI API tests, 9 offline eval cases, shell syntax, Docker Compose config, whitespace, Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly without live opt-in.

No live OpenAI calls were run for this task.

## Known Limitations

- Default rates must be maintained manually when provider pricing changes.
- The estimate uses reported input and output tokens only; cached-input pricing is intentionally not inferred.
- Cost remains unavailable when token usage is missing.

## Recommended Next Task

0027H: Live Demo Cost Baseline Refresh And Pricing Maintenance Check.

## Artifact Safety

No private env files, API keys, raw datasets, generated live results, screenshots, credentials, or `.tmp-ai-demo/` artifacts were committed.
