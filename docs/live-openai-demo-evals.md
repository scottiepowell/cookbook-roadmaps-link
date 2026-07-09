# Live OpenAI Demo Evals

This is the repeatable live-provider evaluation path for the AI cookbook demo. It is manual-only and is not part of CI, normal repository validation, or the mock demo path.

The harness uses generated demo-safe data, runs the same user-facing workflows as `/demo`, captures model responses, scores deterministic checks, records usage/latency metrics, and writes ignored artifacts under:

```text
.tmp-ai-demo/live-evals/<timestamp>/
```

Generated files:

- `results.jsonl`
- `summary.json`
- `summary.md`
- `responses/*.json`

Do not commit generated live eval results by default.

## Workflows

The case set mirrors the UI workflow order:

1. readiness;
2. structured importer;
3. Ask My Cookbook;
4. dataset search as a deterministic non-provider baseline;
5. dataset Ask/RAG;
6. meal planner.

Cases are defined in `evals/ai_cookbook/live_cases.json`. Deterministic scoring helpers live in `evals/ai_cookbook/expected_checks.py`.

The first successful live GPT-nano baseline is recorded in [Live OpenAI Demo Baseline: 2026-07-07](live-openai-demo-baseline-2026-07-07.md). The post-`0028A` regression, `0028B` importer-check fix, and current post-fix acceptance baseline are recorded in [Live OpenAI Demo Regression Notes: 2026-07-08](live-openai-demo-regression-notes-2026-07-08.md).

## Input Quality Metrics

The API applies deterministic input-quality checks before retrieval or provider calls. Responses may include `input_quality.status`:

- `ready`: process normally;
- `weak_but_usable`: process with bounded warnings or assumptions;
- `needs_clarification`: return exactly one short clarification question and do not call the main generation path;
- `rejected`: return friendly recovery guidance without a provider call.

Live eval records include `input_quality_status`, `input_quality_reason`, `clarification_question_present`, `rejected_before_provider`, and `provider_called` when available. These fields make bad-input handling measurable without adding an open-ended chat loop or extra live calls.

## Guardrails

The wrapper exits without live calls unless all required settings are present:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
```

`OPENAI_API_KEY` must be present in the process environment or ignored local environment. The script must not print or persist the key, key fragments, auth headers, raw environment files, or provider secrets.

Budget must be between 1 and 25 cents. `AI_MAX_OUTPUT_TOKENS` must be between 1 and 300 for eval runs.

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Without opt-in settings, the command skips cleanly and explains the required settings.

When opt-in settings are present, the script prints the generated report path and a compact pass/fail summary.

## Cost Metrics

The harness records provider usage fields when available:

- input tokens;
- output tokens;
- total tokens.

Estimated cost is written when token usage is available and either local rate inputs or a maintained model default can be used. For `OPENAI_MODEL=gpt-5.4-nano`, the harness uses the current standard short-context default rates when local rate inputs are not provided:

- input: 0.20 USD per 1M tokens;
- output: 1.25 USD per 1M tokens.

Pricing reference: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), checked 2026-07-07. The default uses standard short-context direct OpenAI API pricing only; it does not use cached-input, Batch, Flex, Priority, regional uplift, long-context, or Amazon Bedrock pricing.

Operator-provided rate inputs override the model defaults:

```powershell
$env:OPENAI_INPUT_COST_PER_1M_TOKENS="<current input rate>"
$env:OPENAI_OUTPUT_COST_PER_1M_TOKENS="<current output rate>"
```

Each record includes `cost_source`:

- `env_override` when both local rate inputs are provided;
- `default_model_rate` when local rate inputs are missing and the configured model has a maintained default;
- `unavailable` when the model is unknown or token usage is unavailable.

The default rates are intentionally kept in one source-code table in `evals/ai_cookbook/expected_checks.py`. The harness does not scrape pricing automatically. If rates are not available for a model, `estimated_cost_usd` remains `null`.

## Expected Checks

Importer checks include schema shape, non-empty title, ingredients, instructions, provider/model, warning count, non-placeholder title, at least two preserved input ingredients across structured fields, ingredient-grounded descriptions when descriptions are present, missing-quantity or unspecified-detail notes, concise action-oriented instructions, generic-placeholder avoidance, and unrelated-food avoidance. Ingredient evidence uses canonical alias groups, so useful outputs can pass when ingredients are preserved in the title, ingredient list, or instructions even if the description is absent or worded differently.

Ask My Cookbook checks that the answer or citations include `Lemon Herb White Beans`, citations are present, retrieved count is positive, the answer is concise, cited recipe titles appear in the answer, and no known saved-recipe title outside retrieved citations is mentioned.

Dataset Ask/RAG checks that the answer or citations include `Tomato Pasta Skillet`, source ID `demo-dataset-1` is cited, retrieved count is positive, the answer includes cited source title and traceable provenance, and unsupported known dataset titles are not introduced outside citations.

Meal Planner checks that the plan has at least one meal, selected recipe IDs come from retrieved candidates, the selected meal title matches the cited recipe title, the reason refers to the user preference, citations are present, no invented recipe IDs are used, and no invented extra meals are added.

## Thresholds

The harness applies initial quality thresholds after workflow checks. Warning thresholds do not fail the run; failure thresholds add failed checks to affected workflow records.

| Setting | Default | Severity |
| --- | ---: | --- |
| `TOTAL_LATENCY_MS_WARN` | 15000 | warning |
| `IMPORTER_LATENCY_MS_WARN` | 7000 | warning |
| `WORKFLOW_LATENCY_MS_FAIL` | 10000 | failed check |
| `TOTAL_TOKENS_WARN` | 2500 | warning |
| `IMPORTER_TOKENS_WARN` | 900 | warning |
| `WORKFLOW_TOKENS_FAIL` | 1200 | failed check |

Override these with environment variables when tuning live eval strictness.

## Acceptance History

| Date | Context | Result | Evidence |
| --- | --- | --- | --- |
| 2026-07-07 | First successful GPT-nano live eval baseline | Pass, 6/6 workflows | `docs/live-openai-demo-baseline-2026-07-07.md` |
| 2026-07-08 | Post-`0028A` live eval | Fail, 5/6 workflows | Importer false failure: description-only ingredient check was too brittle. |
| 2026-07-08 | Post-`0028B` live eval | Pass, 6/6 workflows | Current acceptance baseline: 0 threshold warnings, 0 threshold failures, `default_model_rate` cost populated. |

Current acceptance matrix:

| Area | Status | Evidence |
| --- | --- | --- |
| Mock demo | Pass | `scripts/demo-ai-mock.ps1` |
| Seeded local UI demo | Pass | generated fixtures |
| Live OpenAI eval | Pass | post-`0028B` 6/6 run |
| Cost estimate | Pass | `default_model_rate` cost populated |
| Latency thresholds | Pass | 0 warnings / 0 failures |
| Token thresholds | Pass | 0 warnings / 0 failures |
| Input quality guardrails | Pass | `0028A` offline tests |
| Importer eval robustness | Pass | `0028B` tests plus post-fix live pass |
| Provider-call avoidance | Pass | rejected and clarification paths tested offline |

## Generated Demo Fixture Warnings

Generated demo dataset fixtures intentionally contain only the small CSV needed for the UI and live evals. When the generated fixture marker is present, warnings about missing optional dataset files are filtered:

- `13k-recipes.db`
- `5k-recipes.db`
- `metadata.json`
- `README.md`
- `tutorial.md`

Real dataset directories without the generated-demo marker still emit the original warnings.

## Future Production Hardening

Future production tasks may include:

- authenticated access;
- time-limited sessions;
- paid access or monetization gates;
- usage metering;
- user/session isolation;
- durable storage;
- multi-use-case routing;
- deployment exposure controls;
- provider cost controls;
- admin/operator dashboard.

Those are intentionally not implemented in this task.
