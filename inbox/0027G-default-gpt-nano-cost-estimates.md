# Task 0027G: Default GPT-Nano Cost Estimates

## Goal

Make live OpenAI demo eval cost estimates populate by default for `gpt-5.4-nano` while preserving operator override support.

The latest live eval after `0027F` passed under the new quality gates, but still reported:

```text
estimated_cost_usd=None
```

because `OPENAI_INPUT_COST_PER_1M_TOKENS` and `OPENAI_OUTPUT_COST_PER_1M_TOKENS` were not set locally.

## Current Live Eval Result

Operator run:

```text
report=C:\Users\scott\cookbook-roadmaps-link\.tmp-ai-demo\live-evals\20260707T194255Z\summary.md
status=passed workflows=6/6 tokens=1469 estimated_cost_usd=None
```

Summary:

```text
Created: 2026-07-07T19:43:05.517039+00:00
Expected model: gpt-5.4-nano
Overall passed: True
Workflows passed: 6/6
Total latency ms: 9233
Total tokens: 1469
Estimated cost USD: None
Threshold warnings: 0
Threshold failures: 0
```

Workflow totals:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| readiness | PASS | 1 | 0 | 0 | 0 |
| importer | PASS | 5171 | 0 | 0 | 628 |
| ask_my_cookbook | PASS | 1455 | 2 | 2 | 279 |
| dataset_search | PASS | 2 | 0 | 1 | 0 |
| dataset_ask | PASS | 858 | 1 | 1 | 221 |
| meal_plan | PASS | 1746 | 1 | 1 | 341 |

No failed checks, no threshold warnings, and no threshold failures.

## Official Pricing Reference

Use the current OpenAI API pricing page as the source for the default `gpt-5.4-nano` standard short-context rates.

As of the referenced page, standard short-context `gpt-5.4-nano` pricing is:

```text
input:  $0.20 per 1M tokens
cached input: $0.02 per 1M tokens
output: $1.25 per 1M tokens
```

Task implementation should record the official pricing page and retrieval date in docs/outbox.

Do not use Batch, Flex, Priority, long-context, regional uplift, or Amazon Bedrock pricing for the default unless explicitly configured later.

## Required Behavior

Update the live eval cost estimation so that:

1. If `OPENAI_INPUT_COST_PER_1M_TOKENS` and `OPENAI_OUTPUT_COST_PER_1M_TOKENS` are provided, those env vars override everything.
2. If env vars are not provided and `OPENAI_MODEL=gpt-5.4-nano`, use default standard short-context rates:
   - input: `0.20`
   - output: `1.25`
3. If the model is not recognized and env vars are not provided, keep `estimated_cost_usd` as `None` and explain why in summary output.
4. The summary should state whether pricing came from `env_override`, `default_model_rate`, or `unavailable`.
5. The default should be easy to update in one place.
6. Do not require a live OpenAI call to test this.

## Cost Math

Keep using actual `input_tokens` and `output_tokens` from provider usage when available.

Formula:

```text
estimated_cost_usd = (input_tokens / 1_000_000 * input_rate) + (output_tokens / 1_000_000 * output_rate)
```

For the latest run, cost should be tiny. Do not round to zero in a way that hides the value. Prefer enough decimal precision for sub-cent runs.

## Suggested Files

Update as needed:

```text
evals/ai_cookbook/expected_checks.py
scripts/live-openai-demo-evals.py
docs/live-openai-demo-evals.md
docs/live-openai-demo-baseline-2026-07-07.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
ai-api/tests/test_live_openai_demo_evals.py
outbox/0027G-default-gpt-nano-cost-estimates-results.md
```

## Tests

Add offline tests only. Do not call OpenAI.

Tests should cover:

- default `gpt-5.4-nano` rates are used when env vars are missing;
- env-provided rates override default rates;
- unknown model without env rates returns `estimated_cost_usd=None`;
- cost source is recorded as `default_model_rate`, `env_override`, or `unavailable`;
- sub-cent cost values are not rounded to zero;
- existing live eval skip guard behavior still works;
- no secrets or private paths are written to committed docs.

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The final `run-openai-demo-evals.ps1` command should skip cleanly unless live opt-in settings are present.

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI calls during normal validation.

## Optional Human Live Confirmation

After implementation, the operator can run:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The result should show a non-`None` estimated cost without setting cost env vars.

## Non-Goals

Do not implement:

- billing;
- payment processing;
- user-facing pricing UI;
- time-limited sessions;
- authentication;
- provider price auto-scraping;
- live OpenAI calls in CI;
- committed `.tmp-ai-demo/` artifacts;
- committed secrets or private env files.

## Outbox Report

Create:

```text
outbox/0027G-default-gpt-nano-cost-estimates-results.md
```

Include:

- Summary
- Files changed
- Default rates implemented
- Override behavior
- Unknown model behavior
- Cost-source behavior
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Official pricing reference used
- Known limitations
- Recommended next task
- Confirmation that no private env files, API keys, raw datasets, generated live results, screenshots, credentials, or `.tmp-ai-demo/` artifacts were committed

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0027G-default-gpt-nano-cost-estimates-results.md

git commit -m "mailbox: complete task 0027G default gpt nano cost estimates"

git push origin main
```

## Done Criteria

- `gpt-5.4-nano` has default cost-estimation rates.
- Env-provided rates still override defaults.
- Unknown models without env rates still produce `None` instead of guessed pricing.
- Summary/report shows cost-source metadata.
- Sub-cent runs produce visible nonzero estimates when token usage exists.
- Offline tests cover default, override, and unavailable cases.
- Normal validation remains offline.
- No generated live eval artifacts, secrets, private env files, raw datasets, screenshots, or credentials are committed.
