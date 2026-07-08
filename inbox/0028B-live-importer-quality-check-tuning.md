# Task 0028B: Live Importer Quality Check Tuning

## Goal

Fix the first post-`0028A` live eval failure by tuning importer quality checks so they catch real quality regressions without false-failing useful GPT-nano importer responses.

Do not weaken the quality bar blindly. Make the scoring more robust and, if needed, adjust the importer prompt/schema guidance so the model produces consistently checkable descriptions.

## Context

`0028A` completed and added deterministic bounded input-quality handling across importer, Ask My Cookbook, dataset search, dataset Ask/RAG, and meal planner.

Outbox confirms:

- input-quality statuses: `ready`, `weak_but_usable`, `needs_clarification`, `rejected`;
- rejected and clarification paths return before provider calls;
- live eval records include input-quality and provider-call metrics;
- offline evals now include input-quality cases;
- normal validation remains offline.

After `0028A`, the operator ran the live OpenAI demo eval with `gpt-5.4-nano`.

Live run:

```text
report=C:\Users\scott\cookbook-roadmaps-link\.tmp-ai-demo\live-evals\20260708T125943Z\summary.md
status=failed workflows=5/6 tokens=1452 estimated_cost_usd=0.0007125
```

Summary:

```text
Created: 2026-07-08T12:59:55.107559+00:00
Expected model: gpt-5.4-nano
Overall passed: False
Workflows passed: 5/6
Total latency ms: 10245
Total tokens: 1452
Estimated cost USD: 0.0007125
Cost sources: default_model_rate, unavailable
Threshold warnings: 0
Threshold failures: 0
```

Workflow table:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens | Cost USD | Cost Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| readiness | PASS | 1 | 0 | 0 | 0 | None | unavailable |
| importer | FAIL | 5590 | 0 | 0 | 615 | 0.0003729 | default_model_rate |
| ask_my_cookbook | PASS | 1642 | 2 | 2 | 279 | 0.0001293 | default_model_rate |
| dataset_search | PASS | 16 | 0 | 1 | 0 | None | unavailable |
| dataset_ask | PASS | 1351 | 1 | 1 | 221 | 0.0000883 | default_model_rate |
| meal_plan | PASS | 1645 | 1 | 1 | 337 | 0.000122 | default_model_rate |

Failed check:

```text
importer: description should mention at least two input ingredients - mentioned=[]
```

## Suspected Cause

The importer check currently derives:

```python
mentioned_description_ingredients = [
    ingredient for ingredient in IMPORTER_INPUT_INGREDIENTS if ingredient in description.lower()
]
```

and `IMPORTER_INPUT_INGREDIENTS` is:

```python
("white beans", "olive oil", "garlic", "lemon", "parsley", "toast")
```

This is likely too brittle because it only checks exact phrase matches in `draft.description`. A useful importer response can still be grounded if:

- the title contains `Lemon Herb White Beans`;
- the ingredients list contains the expected ingredients;
- the instructions mention expected ingredients/actions;
- the description uses synonyms or general phrasing such as `bright bean dish`, `herbs`, `citrus`, or `beans` instead of the exact phrase `white beans` or `lemon`.

The task is to distinguish between a real model-quality regression and a brittle evaluator false negative.

## Required Work

### 1. Inspect the generated importer response if available locally

If the local generated file exists, inspect:

```text
.tmp-ai-demo/live-evals/20260708T125943Z/responses/importer.json
```

Do not commit this file.

Use it only to understand whether the response was actually poor or whether the check was brittle.

If the file is not available, proceed from the summary and the scoring code.

### 2. Improve importer quality scoring

Update `evals/ai_cookbook/expected_checks.py` so importer groundedness is robust.

Recommended approach:

- Keep the quality intent: importer output should be grounded in the input ingredients.
- Do not require only the description field to carry all ingredient evidence.
- Add helper functions for ingredient evidence across:
  - title;
  - description;
  - ingredient names;
  - instruction text;
  - notes only if appropriate.
- Track evidence by canonical ingredient groups rather than only exact phrase strings.

Example canonical groups:

```python
{
  "white beans": ["white beans", "beans", "bean"],
  "olive oil": ["olive oil", "oil"],
  "garlic": ["garlic"],
  "lemon": ["lemon", "lemon juice", "citrus"],
  "parsley": ["parsley", "herbs", "herb"],
  "toast": ["toast", "bread"]
}
```

Suggested check split:

- `draft should preserve at least two input ingredients across structured fields`
- `description should be ingredient-grounded when present`

Where:

- structured-field preservation can pass if at least two canonical input ingredient groups appear anywhere in title/description/ingredient names/instructions;
- description-grounded can pass if description is absent/short only when ingredients and instructions preserve grounding, or if description contains at least one canonical ingredient group plus the structured fields contain at least two.

Keep check names stable only if possible. If renaming is necessary, update `live_cases.json`, docs, tests, and baseline notes.

### 3. Consider prompt/schema guidance if needed

If the model response was genuinely weak, update the importer prompt guidance so descriptions are more consistently grounded.

Desired behavior:

- `description` should be one concise sentence;
- it should include at least one or two core ingredients when possible;
- it should not invent unrelated ingredients;
- missing quantities/timing should be placed in notes, not invented.

Do not make prompts long or token-heavy.

### 4. Preserve provider-call and cost behavior

Do not alter live-call guardrails.

Do not run live OpenAI during normal validation.

Do not remove cost-source behavior from `0027G`.

Do not change the default GPT-nano cost table unless necessary.

### 5. Add tests

Add offline tests for:

- current brittle false-fail pattern: useful output with ingredients in structured fields but description not exact-matching all phrases;
- bad output with unrelated ingredients still fails;
- generic placeholder output still fails;
- truly ungrounded importer output still fails;
- description with synonym/alias evidence passes if the rest of the draft is grounded;
- existing live eval harness tests still pass;
- input-quality provider-call avoidance tests still pass.

### 6. Update docs and outbox

Update as needed:

```text
evals/ai_cookbook/expected_checks.py
evals/ai_cookbook/live_cases.json
ai-api/tests/test_live_openai_demo_evals.py
docs/live-openai-demo-evals.md
docs/live-openai-demo-baseline-2026-07-07.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0028B-live-importer-quality-check-tuning-results.md
```

Docs should explain:

- why the importer check was tuned;
- what the check now measures;
- why this avoids brittle false failures;
- that deterministic quality checks still catch real hallucinations and unrelated ingredients;
- that normal validation remains offline.

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

The live smoke and live eval wrappers should skip cleanly unless live opt-in settings are present.

If direct Windows pytest still fails with the known temp ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI calls during normal validation.

## Optional Human Live Confirmation

After implementation, the operator can rerun the live eval with explicit opt-in:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Expected result:

```text
status=passed workflows=6/6
```

unless a new real quality issue is found.

## Non-Goals

Do not implement:

- billing;
- auth;
- time-limited sessions;
- production storage;
- public deployment changes;
- screenshot workflow;
- browser automation;
- live OpenAI calls in CI;
- committed `.tmp-ai-demo/` artifacts;
- committed secrets or private env files.

## Outbox Report

Create:

```text
outbox/0028B-live-importer-quality-check-tuning-results.md
```

Include:

- Summary
- Files changed
- Root cause assessment
- Scoring changes
- Prompt/schema changes if any
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Recommended next task
- Confirmation that no private env files, API keys, raw datasets, generated live results, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts were committed

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0028B-live-importer-quality-check-tuning-results.md

git commit -m "mailbox: complete task 0028B live importer quality check tuning"

git push origin main
```

## Done Criteria

- The importer quality check no longer false-fails useful grounded responses due only to exact description phrase matching.
- Real ungrounded or unrelated importer responses still fail.
- Tests cover robust groundedness and false-fail cases.
- Existing input-quality, cost, threshold, and live eval guard behavior remains intact.
- Normal validation remains offline.
- No generated live eval artifacts, secrets, private env files, raw datasets, screenshots, logs, or credentials are committed.
