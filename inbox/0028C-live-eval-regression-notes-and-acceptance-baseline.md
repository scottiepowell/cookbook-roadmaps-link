# Task 0028C: Live Eval Regression Notes And Acceptance Baseline

## Goal

Preserve the post-`0028A` live eval regression, the `0028B` importer-check fix, and the latest passing live GPT-nano acceptance run as sanitized project evidence.

This is primarily a documentation, baseline, and acceptance-matrix task. Do not make runtime behavior changes unless a documentation or test-reference update requires a very small supporting change.

## Context

The project has reached a strong AI demo checkpoint:

- `0027D`: seeded local demo data and local launch flow.
- `0027E`: live OpenAI demo eval harness and metrics.
- `0027F`: live GPT-nano quality baseline and thresholds.
- `0027G`: default GPT-nano cost estimates.
- `0028A`: bounded input quality and one-question clarification handling.
- `0028B`: live importer quality-check tuning after a brittle evaluator false failure.

The latest live run after `0028B` passed all workflows with no threshold issues.

## Regression To Preserve

After `0028A`, the operator ran a live eval and got one failure.

Failed run:

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

Root cause from `0028B` outbox:

The generated importer response was useful. It produced `Lemon Herb White Beans`, included white beans, olive oil, garlic, lemon juice, parsley, and toast in structured ingredients, included action-oriented instructions, and noted missing quantities/details. The failed check was brittle because it required ingredient evidence only in `description`, which was `null`.

## Fix To Preserve

`0028B` completed with commit:

```text
682483746d4c98857fed5684c8c564f87f971f74
mailbox: complete task 0028B live importer quality check tuning
```

`0028B` changed importer quality checks so useful GPT-nano structured importer responses pass when ingredient evidence is preserved in title, ingredient names, or instructions, even when `description` is absent or worded differently.

Key changes:

- replaced the description-only ingredient check with `draft should preserve at least two input ingredients across structured fields`;
- added `description should be ingredient-grounded when present`;
- added alias-aware evidence for:
  - white beans: `white beans`, `beans`, `bean`;
  - olive oil: `olive oil`, `oil`;
  - garlic: `garlic`;
  - lemon: `lemon`, `lemon juice`, `citrus`;
  - parsley: `parsley`, `herbs`, `herb`;
  - toast: `toast`, `bread`;
- kept failures for generic placeholders, unrelated foods, and truly ungrounded outputs;
- updated importer prompt guidance to request one concise description with one or two core ingredients when possible.

## Acceptance Run To Preserve

After `0028B`, the operator reran the live GPT-nano eval and got a clean pass.

Passing run:

```text
Created: 2026-07-08T13:40:41.967056+00:00
Expected model: gpt-5.4-nano
Overall passed: True
Workflows passed: 6/6
Total latency ms: 9615
Total tokens: 1467
Estimated cost USD: 0.0007029
Cost sources: default_model_rate, unavailable
Threshold warnings: 0
Threshold failures: 0
```

Workflow table:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens | Cost USD | Cost Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| readiness | PASS | 4 | 0 | 0 | 0 | None | unavailable |
| importer | PASS | 5249 | 0 | 0 | 626 | 0.0003583 | default_model_rate |
| ask_my_cookbook | PASS | 1685 | 2 | 2 | 279 | 0.0001293 | default_model_rate |
| dataset_search | PASS | 7 | 0 | 1 | 0 | None | unavailable |
| dataset_ask | PASS | 1215 | 1 | 1 | 221 | 0.0000883 | default_model_rate |
| meal_plan | PASS | 1455 | 1 | 1 | 341 | 0.000127 | default_model_rate |

Failed checks:

```text
None.
```

Threshold warnings:

```text
None.
```

Threshold failures:

```text
None.
```

## Required Work

### 1. Add a sanitized regression and acceptance note

Create a new documentation file, suggested path:

```text
docs/live-openai-demo-regression-notes-2026-07-08.md
```

It should include:

- what failed after `0028A`;
- why it failed;
- why the failure was considered evaluator brittleness rather than a model-quality failure;
- what `0028B` changed;
- the latest passing live acceptance run after `0028B`;
- current acceptance baseline;
- what remains intentionally out of scope.

Do not include:

- local private file paths except sanitized references if necessary;
- raw generated response JSON;
- API keys;
- `.env` values;
- provider secrets;
- full `.tmp-ai-demo` artifact contents.

### 2. Update the main live baseline / acceptance docs

Update as needed:

```text
docs/live-openai-demo-baseline-2026-07-07.md
docs/live-openai-demo-evals.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
```

The docs should now distinguish:

- original first GPT-nano baseline from `2026-07-07`;
- post-`0028A` failed regression run from `2026-07-08`;
- `0028B` evaluator fix;
- post-`0028B` acceptance run from `2026-07-08`.

### 3. Update or add an acceptance matrix

Add or update a concise acceptance matrix showing the current state:

| Area | Status | Evidence |
| --- | --- | --- |
| Mock demo | Pass | mock demo script |
| Seeded local UI demo | Pass | generated fixtures |
| Live OpenAI eval | Pass | post-0028B 6/6 run |
| Cost estimate | Pass | default_model_rate cost populated |
| Latency thresholds | Pass | 0 warnings / 0 failures |
| Token thresholds | Pass | 0 warnings / 0 failures |
| Input quality guardrails | Pass | 0028A offline tests |
| Importer eval robustness | Pass | 0028B tests + post-fix live pass |
| Provider-call avoidance | Pass | rejected/clarification paths tested offline |

### 4. Add an outbox report

Create:

```text
outbox/0028C-live-eval-regression-notes-and-acceptance-baseline-results.md
```

Include:

- Summary
- Files changed
- Failed run recorded
- Root cause recorded
- 0028B fix recorded
- Passing acceptance run recorded
- Acceptance matrix summary
- Validation results
- Whether live OpenAI was run or skipped during the task
- Recommended next task
- Artifact safety confirmation

### 5. Keep validation offline

Do not run live OpenAI calls during normal validation.

This task records the already-provided live run results; it does not need a new live call.

## Suggested Files

Update only what is necessary:

```text
docs/live-openai-demo-regression-notes-2026-07-08.md
docs/live-openai-demo-baseline-2026-07-07.md
docs/live-openai-demo-evals.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0028C-live-eval-regression-notes-and-acceptance-baseline-results.md
```

If no code changes are required, avoid code changes.

## Validation

Run normal offline validation:

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

## Non-Goals

Do not implement:

- new input-quality behavior;
- new model prompts;
- new eval scoring behavior;
- billing;
- authentication;
- time-limited sessions;
- public deployment changes;
- production storage;
- provider price changes;
- screenshot workflow;
- browser automation;
- live OpenAI calls in CI;
- committed `.tmp-ai-demo/` artifacts;
- committed secrets or private env files.

## Commit

Commit and push:

```bash
git add docs README.md outbox/0028C-live-eval-regression-notes-and-acceptance-baseline-results.md

git commit -m "mailbox: complete task 0028C live eval regression notes and acceptance baseline"

git push origin main
```

## Done Criteria

- The post-`0028A` failed live run is documented as a sanitized regression note.
- The `0028B` root cause and fix are documented.
- The post-`0028B` passing live acceptance run is documented.
- The project has a clear current acceptance matrix.
- No runtime behavior changes are made unless strictly necessary.
- Normal validation remains offline.
- No generated live eval artifacts, raw response JSON, API keys, env files, raw datasets, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts are committed.
