# Live OpenAI Demo Baseline: 2026-07-07

This sanitized baseline preserves the first successful live GPT-nano demo eval run after `0027E`.

For the post-`0028A` regression, `0028B` importer-check fix, and current post-fix acceptance baseline, see [Live OpenAI Demo Regression Notes: 2026-07-08](live-openai-demo-regression-notes-2026-07-08.md).

It intentionally excludes local filesystem paths, raw generated artifacts, environment files, API keys, provider secrets, and response JSON contents. Generated `.tmp-ai-demo/live-evals/` artifacts are not committed.

## Run Summary

| Field | Value |
| --- | --- |
| Created | `2026-07-07T18:47:37.881688+00:00` |
| Expected model | `gpt-5.4-nano` |
| Overall result | Pass |
| Workflows passed | 6/6 |
| Total latency | 9967 ms |
| Total tokens | 1423 |
| Estimated cost USD | Not available; local pricing env vars were not provided |
| Failed checks | None |

## Workflow Results

| Workflow | Result | Latency ms | Citations | Retrieved | Tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| readiness | Pass | 1 | 0 | 0 | 0 |
| importer | Pass | 5249 | 0 | 0 | 602 |
| ask_my_cookbook | Pass | 1760 | 2 | 2 | 266 |
| dataset_search | Pass | 3 | 0 | 1 | 0 |
| dataset_ask | Pass | 1278 | 1 | 1 | 221 |
| meal_plan | Pass | 1676 | 1 | 1 | 334 |

## Response Quality Notes

- Importer produced `Lemon Herb White Beans` with a useful description, ingredient list, two clear action-oriented steps, and notes about missing quantities.
- Ask My Cookbook correctly answered with `Lemon Herb White Beans` and `Chickpea Cucumber Bowls`, both cited from retrieved saved recipes.
- Dataset Ask correctly answered `Tomato Pasta Skillet` with source id `demo-dataset-1`.
- Meal Planner selected `Lemon Herb White Beans` from retrieved candidates and cited recipe id `1`.

## Token And Latency Notes

| Area | Observation | Tuning Target |
| --- | --- | --- |
| Importer latency | Slowest workflow at 5249 ms. | Keep below the initial 7000 ms warning threshold and investigate prompt/schema trimming if it grows. |
| Importer tokens | Highest token user at 602 tokens. | Keep below the initial 900-token warning threshold and watch for schema or prompt bloat. |
| Total latency | 9967 ms across all workflows. | Keep below the initial 15000 ms warning threshold. |
| Total tokens | 1423 tokens across live-provider workflows. | Keep below the initial 2500-token warning threshold. |
| Cost visibility | Estimated cost was not calculated. | Future GPT-nano runs now use maintained defaults unless local pricing env vars override them. |

## Known Limitations

- Estimated cost was unavailable for this historical run because default GPT-nano cost estimates were added later. Future `gpt-5.4-nano` evals populate estimated cost from maintained default rates unless operator override env vars are provided.
- The baseline was produced from generated demo fixtures, not production cookbook data.
- Dataset search remains deterministic and non-provider-backed.
- This baseline does not cover authentication, billing, time limits, multi-tenant use, durable production storage, public deployment exposure, or admin/operator workflows.
- Human review is still useful for tone, usefulness, and demo narrative even when deterministic checks pass.
- A post-0028A live run showed the importer check was too strict when it required ingredient evidence only in `description`; 0028B tuned this so title, ingredient names, and instructions also count as structured ingredient evidence.

## Later Acceptance History

| Date | Run | Result | Notes |
| --- | --- | --- | --- |
| 2026-07-07 | First GPT-nano live eval baseline | Pass, 6/6 workflows | Preserved in this file as the original baseline. |
| 2026-07-08 | Post-`0028A` live eval | Fail, 5/6 workflows | Importer false-failed because the evaluator required ingredient evidence only in `description`. |
| 2026-07-08 | Post-`0028B` live eval | Pass, 6/6 workflows | Current acceptance baseline: 0 threshold warnings, 0 threshold failures, 1467 tokens, estimated cost USD 0.0007029. |

## Next Tuning Targets

- Continue monitoring importer usefulness checks around non-placeholder titles, structured ingredient preservation, ingredient-grounded descriptions when present, missing-quantity notes, concise instructions, and unrelated ingredient avoidance.
- Add concise answer and citation-support checks for Ask My Cookbook.
- Require dataset answers to include cited source titles and traceable source IDs or equivalent provenance.
- Require meal plans to use only retrieved candidate IDs and match selected meal titles to citations.
- Add latency and token thresholds so future live runs flag slow or expensive regressions.
- Reduce generated demo fixture warning noise for missing optional dataset files without hiding real production warnings.
- Override cost visibility when needed by setting:

```powershell
$env:OPENAI_INPUT_COST_PER_1M_TOKENS="<current input rate>"
$env:OPENAI_OUTPUT_COST_PER_1M_TOKENS="<current output rate>"
```
