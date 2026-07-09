# Live OpenAI Demo Regression Notes: 2026-07-08

This sanitized note preserves the post-`0028A` live eval regression, the `0028B` importer-check fix, and the latest passing post-fix GPT-nano acceptance run.

It intentionally excludes private local paths, raw generated response JSON, API keys, environment values, provider secrets, and generated `.tmp-ai-demo/live-evals/` artifacts.

## What Failed After 0028A

After `0028A`, a manual live GPT-nano demo eval failed one workflow:

| Field | Value |
| --- | --- |
| Created | `2026-07-08T12:59:55.107559+00:00` |
| Expected model | `gpt-5.4-nano` |
| Overall result | Fail |
| Workflows passed | 5/6 |
| Total latency | 10245 ms |
| Total tokens | 1452 |
| Estimated cost USD | 0.0007125 |
| Threshold warnings | 0 |
| Threshold failures | 0 |

Workflow results:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens | Cost USD | Cost Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| readiness | Pass | 1 | 0 | 0 | 0 | None | unavailable |
| importer | Fail | 5590 | 0 | 0 | 615 | 0.0003729 | default_model_rate |
| ask_my_cookbook | Pass | 1642 | 2 | 2 | 279 | 0.0001293 | default_model_rate |
| dataset_search | Pass | 16 | 0 | 1 | 0 | None | unavailable |
| dataset_ask | Pass | 1351 | 1 | 1 | 221 | 0.0000883 | default_model_rate |
| meal_plan | Pass | 1645 | 1 | 1 | 337 | 0.000122 | default_model_rate |

Failed check:

```text
importer: description should mention at least two input ingredients - mentioned=[]
```

## Root Cause

The failed importer response was useful. It produced `Lemon Herb White Beans`, preserved white beans, olive oil, garlic, lemon juice, parsley, and toast in structured ingredients, included action-oriented instructions, and noted missing quantities or details.

The evaluator failed because it looked for ingredient evidence only in `description`. In this run, `description` was absent, while the structured title, ingredients, and instructions still preserved the input. That made the failure evaluator brittleness rather than a model-quality failure.

## 0028B Fix

`0028B` changed importer quality checks so useful GPT-nano structured importer responses can pass when ingredient evidence is preserved in title, ingredient names, or instructions, even when `description` is absent or worded differently.

The fix was recorded in commit `682483746d4c98857fed5684c8c564f87f971f74` with message:

```text
mailbox: complete task 0028B live importer quality check tuning
```

Key changes preserved for acceptance history:

- replaced the description-only ingredient check with `draft should preserve at least two input ingredients across structured fields`;
- added `description should be ingredient-grounded when present`;
- added alias-aware evidence for white beans, olive oil, garlic, lemon, parsley, and toast;
- kept failures for generic placeholders, unrelated foods, and truly ungrounded outputs;
- updated importer prompt guidance to request a concise description with one or two core ingredients when possible.

## Passing Post-0028B Acceptance Run

After `0028B`, the live GPT-nano demo eval passed all workflows:

| Field | Value |
| --- | --- |
| Created | `2026-07-08T13:40:41.967056+00:00` |
| Expected model | `gpt-5.4-nano` |
| Overall result | Pass |
| Workflows passed | 6/6 |
| Total latency | 9615 ms |
| Total tokens | 1467 |
| Estimated cost USD | 0.0007029 |
| Threshold warnings | 0 |
| Threshold failures | 0 |
| Failed checks | None |

Workflow results:

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens | Cost USD | Cost Source |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| readiness | Pass | 4 | 0 | 0 | 0 | None | unavailable |
| importer | Pass | 5249 | 0 | 0 | 626 | 0.0003583 | default_model_rate |
| ask_my_cookbook | Pass | 1685 | 2 | 2 | 279 | 0.0001293 | default_model_rate |
| dataset_search | Pass | 7 | 0 | 1 | 0 | None | unavailable |
| dataset_ask | Pass | 1215 | 1 | 1 | 221 | 0.0000883 | default_model_rate |
| meal_plan | Pass | 1455 | 1 | 1 | 341 | 0.000127 | default_model_rate |

## Current Acceptance Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Mock demo | Pass | `scripts/demo-ai-mock.ps1` |
| Seeded local UI demo | Pass | generated demo fixtures and `/demo` readiness path |
| Live OpenAI eval | Pass | post-`0028B` 6/6 live run from `2026-07-08T13:40:41.967056+00:00` |
| Cost estimate | Pass | `default_model_rate` cost populated for provider workflows |
| Latency thresholds | Pass | 0 warnings / 0 failures |
| Token thresholds | Pass | 0 warnings / 0 failures |
| Input quality guardrails | Pass | `0028A` offline tests |
| Importer eval robustness | Pass | `0028B` tests plus post-fix live pass |
| Provider-call avoidance | Pass | rejected and clarification paths tested offline |

## Current Baseline

The `2026-07-07` live run remains the first successful GPT-nano baseline. The current live acceptance baseline is the post-`0028B` `2026-07-08` 6/6 run because it includes the bounded input-quality changes from `0028A`, the importer evaluator robustness fix from `0028B`, default cost estimates, and zero threshold warnings or failures.

Normal repository validation remains offline and mock-only. Live OpenAI wrappers must skip unless explicit live opt-in settings are present.

## Out Of Scope

This note does not introduce new runtime behavior, model prompts, eval scoring behavior, billing, authentication, time-limited sessions, production storage, public deployment changes, provider price changes, browser automation, live OpenAI calls in CI, or committed generated live artifacts.
