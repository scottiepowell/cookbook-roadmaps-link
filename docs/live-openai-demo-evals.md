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

Estimated cost is written only when token usage and optional local rate inputs are available:

```powershell
$env:OPENAI_INPUT_COST_PER_1M_TOKENS="<local rate>"
$env:OPENAI_OUTPUT_COST_PER_1M_TOKENS="<local rate>"
```

If rates are not provided, `estimated_cost_usd` is `null`. This avoids baking changing provider pricing into source control.

## Expected Checks

Importer checks include schema shape, non-empty title, ingredients, instructions, provider/model, and warnings.

Ask My Cookbook checks that the answer or citations include `Lemon Herb White Beans`, citations are present, retrieved count is positive, and no known saved-recipe title outside retrieved citations is mentioned.

Dataset Ask/RAG checks that the answer or citations include `Tomato Pasta Skillet`, source ID `demo-dataset-1` is cited, retrieved count is positive, and unsupported known dataset titles are not introduced outside citations.

Meal Planner checks that the plan has at least one meal, selected recipe IDs come from retrieved candidates, citations are present, and no invented recipe IDs are used.

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
