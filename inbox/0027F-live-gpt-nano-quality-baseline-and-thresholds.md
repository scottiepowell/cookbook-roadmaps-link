# Task 0027F: Live GPT-Nano Quality Baseline And Thresholds

## Goal

Preserve the first successful live GPT-nano eval as a sanitized baseline and tighten the eval quality gates so future runs measure not only correctness, but also answer usefulness, latency, token usage, cost visibility, and demo-readiness.

`0027E` proved the OpenAI-backed workflow can pass all deterministic checks. This task turns that result into a durable quality baseline and prepares the next iteration loop for production hardening.

## Context

A human ran the live eval harness after `0027E`.

Run summary provided by the operator:

```text
Created: 2026-07-07T18:47:37.881688+00:00
Expected model: gpt-5.4-nano
Overall passed: True
Workflows passed: 6/6
Total latency ms: 9967
Total tokens: 1423
Estimated cost USD: None
Failed checks: None
```

Workflow results:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| readiness | PASS | 1 | 0 | 0 | 0 |
| importer | PASS | 5249 | 0 | 0 | 602 |
| ask_my_cookbook | PASS | 1760 | 2 | 2 | 266 |
| dataset_search | PASS | 3 | 0 | 1 | 0 |
| dataset_ask | PASS | 1278 | 1 | 1 | 221 |
| meal_plan | PASS | 1676 | 1 | 1 | 334 |

The operator also inspected response JSONs. Quality summary:

- Importer produced `Lemon Herb White Beans`, useful description, ingredients, two clear steps, and notes about missing quantities.
- Ask My Cookbook correctly answered with `Lemon Herb White Beans` and `Chickpea Cucumber Bowls`, both cited.
- Dataset Ask correctly answered `Tomato Pasta Skillet` with source id `demo-dataset-1`.
- Meal planner selected `Lemon Herb White Beans` from retrieved candidates and cited recipe id `1`.

Known improvement items:

- Importer is the slowest workflow at 5249 ms and highest token user at 602 tokens.
- Dataset warning messages about missing optional files are still noisy in generated demo fixture mode.
- Estimated cost is `None` because local pricing env vars were not provided.
- Current checks are mostly deterministic correctness checks; add more quality/usefulness checks.

## External Guidance To Respect

Use current OpenAI docs already referenced in `0027E`:

- OpenAI evals use test data and testing criteria/graders to determine whether model outputs satisfy requirements.
- OpenAI structured outputs should use JSON Schema with strict schema constraints where schema adherence matters.

Do not add live OpenAI calls to normal validation or CI.

## Scope

Add a sanitized baseline and stronger gates for the live eval system.

This task should not rerun live OpenAI by default. It should work from the operator-provided successful run data and update docs/eval checks accordingly.

## Required Work

### 1. Add a sanitized baseline report

Create a committed Markdown report that does not include local private filesystem paths, raw secrets, env files, API keys, or generated artifact contents.

Suggested file:

```text
docs/live-openai-demo-baseline-2026-07-07.md
```

Include:

- date/time of run;
- expected model;
- overall result;
- workflow table;
- response quality notes;
- token/latency table;
- known limitations;
- next tuning targets.

Do not commit generated `.tmp-ai-demo/live-evals/...` artifacts.

### 2. Add quality/usefulness checks

Extend `evals/ai_cookbook/expected_checks.py` and case definitions as appropriate so future live eval runs check more than basic correctness.

Recommended new checks:

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

### 3. Add threshold checks

Add configurable thresholds for live eval summaries.

Initial suggested defaults:

```text
TOTAL_LATENCY_MS_WARN=15000
IMPORTER_LATENCY_MS_WARN=7000
WORKFLOW_LATENCY_MS_FAIL=10000
TOTAL_TOKENS_WARN=2500
IMPORTER_TOKENS_WARN=900
WORKFLOW_TOKENS_FAIL=1200
```

Thresholds should produce warnings or failed checks according to severity. Keep them configurable by constants or environment variables.

### 4. Add cost visibility guidance

Update docs so future live runs can estimate cost when local rates are provided:

```powershell
$env:OPENAI_INPUT_COST_PER_1M_TOKENS="<current input rate>"
$env:OPENAI_OUTPUT_COST_PER_1M_TOKENS="<current output rate>"
```

Do not bake volatile pricing rates into source code unless already intentionally designed as user-provided env settings. Pricing changes over time; keep current rates as operator-provided values.

### 5. Reduce demo-fixture warning noise if safe

Investigate whether generated demo fixture mode can downgrade or suppress warnings about missing optional dataset files such as:

```text
13k-recipes.db is missing.
5k-recipes.db is missing.
metadata.json is missing.
README.md is missing.
tutorial.md is missing.
```

Do not hide real production warnings. The change should apply only to generated demo fixture mode, if clearly detectable.

If this is risky, document it as a follow-up instead of changing behavior.

### 6. Update docs/backlog

Update:

```text
docs/live-openai-demo-evals.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0027F-live-gpt-nano-quality-baseline-and-thresholds-results.md
```

Docs should explain:

- baseline pass result;
- where the sanitized baseline lives;
- how future live evals compare against the baseline;
- which thresholds are enforced;
- how to enable cost estimates;
- known remaining production-hardening tasks.

## Tests

Add offline tests only. Do not call OpenAI.

Tests should cover:

- new quality checks pass on representative good responses;
- new quality checks fail on placeholder/generic/unsupported responses;
- threshold warnings/failures are generated correctly;
- summary comparison/baseline helpers if added;
- demo-fixture warning filtering if implemented;
- no secrets or local private paths are written to committed baseline docs;
- existing eval harness tests still pass.

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

## Non-Goals

Do not implement:

- billing;
- payment processing;
- time-limited sessions;
- authentication;
- multi-tenant user accounts;
- production storage;
- public deployment changes;
- Cloudflare routing changes;
- admin dashboard;
- screenshot workflow;
- browser automation;
- live OpenAI calls in CI;
- committed `.tmp-ai-demo/` artifacts;
- committed API keys or private env files.

## Outbox Report

Create:

```text
outbox/0027F-live-gpt-nano-quality-baseline-and-thresholds-results.md
```

Include:

- Summary
- Files changed
- Baseline report added
- Quality checks added
- Thresholds added
- Cost visibility changes
- Dataset warning handling decision
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Known limitations
- Recommended next task
- Confirmation that no private env files, API keys, raw datasets, generated live results, screenshots, credentials, or `.tmp-ai-demo/` artifacts were committed

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0027F-live-gpt-nano-quality-baseline-and-thresholds-results.md

git commit -m "mailbox: complete task 0027F live gpt nano quality baseline and thresholds"

git push origin main
```

## Done Criteria

- Sanitized baseline report exists.
- Baseline report records the successful 6/6 live GPT-nano eval without private local paths or generated raw artifacts.
- Quality/usefulness checks are stronger than `0027E` basic correctness checks.
- Latency/token threshold checks exist.
- Cost-estimation guidance is documented.
- Dataset warning noise is addressed or explicitly deferred.
- Offline tests cover new checks and thresholds.
- Normal validation remains offline.
- No generated live eval artifacts, secrets, private env files, raw datasets, screenshots, or credentials are committed.
