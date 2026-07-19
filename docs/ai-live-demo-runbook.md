# AI Live Demo Runbook

Use this runbook for a 15 to 30 minute hands-on demo of the AI cookbook sidecar.

## Pre-Demo Checklist

- Pull the latest `main`.
- Confirm normal validation is mock/offline.
- Confirm no private `.env` values, provider keys, private recipes, or raw dataset files will be shown.
- Run the mock demo path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

- Start the local browser demo path:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

- Open the local integrated product first at `http://127.0.0.1:8000/product`.
  It links the external Vanilla Cookbook container and the existing AI workspace.
  The direct AI browser UI remains at `http://127.0.0.1:8000/demo`.
- Open a terminal for logs.

## Mock/Demo Mode Path

The default demo path uses the mock provider and generated fixtures. It is free, deterministic, and safe for screenshots.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

The start script generates a small local fixture under `.tmp-ai-demo/`, sets `AI_PROVIDER=mock`, points `COOKBOOK_DB_PATH` at a generated SQLite database, points `RECIPE_DATASET_DIR` at generated CSV data, and starts the sidecar on `127.0.0.1:8000`. It does not write to production cookbook data.

The script also supports an intentional provider override for manual acceptance. It respects existing environment variables unless explicit script parameters are supplied.

Live OpenAI browser demo mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Live OpenAI browser demo mode with explicit limits:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests -OpenAIModel gpt-5.4-nano -MaxOutputTokens 900 -LiveTestBudgetCents 25 -Port 8001
```

If you prefer explicit local config loading, the live smoke wrapper also accepts `-EnvFile .\.env`. Live mode still stays off unless the file or process environment explicitly sets `OPENAI_ENABLE_LIVE_TESTS=true` and `AI_PROVIDER=openai`. The underlying Python live helpers do not auto-read `repo_root/.env`, so passing `-EnvFile` or exporting the variables yourself is required for live mode.

Full local RAG browser demo mode with local provider diagnostics:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

`OPENAI_API_KEY` must already exist in the environment for `-Provider openai`. The start script does not prompt for it and does not print it. OpenAI mode defaults to `OPENAI_MODEL=gpt-5.4-nano`, `OPENAI_LIVE_TEST_BUDGET_CENTS=25`, `AI_MAX_OUTPUT_TOKENS=900` for the manual recipe-creator path, a generated `.tmp-ai-demo` fixture dataset, `AI_TIMEOUT_SECONDS=20`, and `AI_PROVIDER_DEBUG=false` unless environment variables or explicit parameters override those values. The 500-token cap used by tiny smoke tests can truncate RAG-informed structured recipe drafts.

For live smoke and live eval wrappers, you can keep the live settings in an ignored local `.env` file and load it explicitly:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env -WriteMissingEnvDefaults

# Then manually edit the ignored local .env only if you intend live calls:
# AI_PROVIDER=openai
# OPENAI_ENABLE_LIVE_TESTS=true
# OPENAI_API_KEY=<set locally, never commit or paste>

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1 -EnvFile .\.env
```

`-WriteMissingEnvDefaults` appends safe missing defaults only. It does not write `OPENAI_API_KEY`, does not enable live mode by itself, and preserves existing comments and values. Existing process environment values still take precedence over the file.

The startup summary now prints only safe values: provider, model, live-test enabled state, budget cents, max output tokens, AI timeout seconds, provider-debug enabled state, local URL, cookbook DB path, dataset path, and dataset index limit. The provider budget guard uses `AI_PROVIDER_CALLS_ENABLED`, `AI_PROVIDER_GLOBAL_DISABLE`, and the per-call/session token and cost caps described in [AI Provider Budget Enforcement](ai-provider-budget-enforcement.md).

The UI readiness panel shows whether:

- the sidecar is healthy;
- provider mode is mock or OpenAI;
- saved-recipe demo data is available;
- local dataset demo data is available.

In the local mock demo path, readiness should show saved recipes available and dataset available. If either is missing, stop and rerun `scripts\start-ai-demo-local.ps1`; missing data should appear as a friendly recoverable condition, not a browser failure.

The generated `.tmp-ai-demo` fixture dataset still contains only three records. That is enough for smoke testing, but importer citations there can be semantically weak. Use the full `recipe-dataset` path with `-RecipeDatasetIndexLimit 5000` for meaningful RAG validation.

The importer prompt now packs a bounded snippet set instead of sending raw retrieved records. The demo UI exposes `retrieved_examples`, `packed_examples`, `context_chars_used`, `weak_examples_included`, and `context_budget_warning` so you can tell whether the provider saw strong support or only weak structure-only examples.

The demo UI also includes a local `Recipe Session Alpha` panel. Use it to start a session from rough recipe notes, inspect interpreted requirements, answer one clarification, send a follow-up, see whether RAG refreshed, get the current session state, and finalize for demo. The session store is process-local and expires; `Finalize for demo` does not write to production cookbook storage. For the full local acceptance checklist, see [Recipe Session Alpha Acceptance Runbook](recipe-session-alpha-acceptance-runbook.md).

Invite-only demo sessions are documented in [AI Invite-Only Demo Session Flow](ai-invite-only-demo-session-flow.md). They are disabled by default, use `X-AI-Demo-Session-Token` for short-lived demo access when enabled, and keep only safe fingerprints after creation. The optional invite smoke path in `scripts/demo-ai-mock.ps1` stays off unless `AI_INVITE_SMOKE_ENABLED=true` is set in the local shell.

The local/operator usage report prototype is documented in [AI Admin Usage Report Prototype](ai-admin-usage-report-prototype.md). The demo UI shows a compact report card with active session counts, provider-call status counts, estimated spend, and threshold warnings. The JSON endpoint is local/operator-only when the operator gate is enabled.

Future public exposure should follow [AI Public Route Exposure Review](ai-public-route-exposure-review.md) before any `/ai/*` path is routed at the edge.

## Importer-Only Diagnostic

Prefer the dedicated live importer smoke script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-openai-importer-live.ps1 -Text "omelet with eggs cheese maybe onions cooked in butter fold it over" -MaxOutputTokens 900 -AiTimeoutSeconds 60 -ProviderDebug
```

When the browser path is ambiguous, test the importer directly without the UI:

```powershell
$body = @{
  text = "omelet with eggs cheese maybe onions cooked in butter fold it over"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ai/import-recipe -ContentType "application/json" -Body $body |
  ConvertTo-Json -Depth 8
```

Expected live-path signals for the current manual acceptance target:

- no `503`;
- `provider=openai`;
- `model=gpt-5.4-nano`;
- `draft.servings=4` when the user did not specify servings;
- estimated quantities where reasonable;
- stronger multi-step instructions;
- citations when dataset retrieval returns matches.

If `AI_PROVIDER_DEBUG=true`, local logs should add sanitized `provider_error_category`, `provider_error_type`, and `safe_error_summary` fields. Those diagnostics must not include API keys, Authorization headers, raw prompts, raw provider responses, `.env` contents, or secret-like strings. The live importer eval wrapper now records the same safe failure categories in its summary output.

The manual importer path now recommends `AI_MAX_OUTPUT_TOKENS=900`. The earlier 500-token cap was fine for smaller smoke tests, but not for RAG-informed structured drafts like cheesecake. If the provider budget guard is enabled and the budget is too tight, the importer returns a safe budget message instead of a provider call. The live eval harness uses a separate importer-only cap with a 900-token default and a 1200-token ceiling, controlled by `OPENAI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS` or `AI_IMPORTER_LIVE_MAX_OUTPUT_TOKENS`, so importer evals stay distinct from the 300-token non-importer live-eval cap.

The importer scorer is also calibrated separately from short-answer workflows. Valid imperative recipe verbs and short labeled steps such as `Brighten with lemon: Stir in lemon juice and zest.` should pass, while placeholder, rambling, or non-action steps still fail. Importer token thresholds are also separate because structured drafts include recipe JSON plus retrieval metadata.

The conciseness rule no longer requires every importer step to be extremely short. Instead it uses a high single-step cap plus average-length and compact-step coverage checks so realistic labeled steps can pass without letting rambling instructions through.

Action-oriented scoring also accepts a short setup phrase before an early imperative verb, so steps like `In a small bowl, mix olive oil with minced garlic...` or `After the beans are warm, stir in lemon juice and parsley.` pass when they remain concise and clearly procedural.

The local operator gate is opt-in, disabled by default, and documented in [AI Local Operator Access Gate](ai-local-operator-access-gate.md). When enabled, the protected AI workflows require a matching safe fingerprint on `X-AI-Operator-Token` or `Authorization: Bearer ...`, unless the explicit local bypass is turned on for local/TestClient requests. The mock smoke script pins the gate off so its checks stay stable in a dirty shell.

## Manual Live RAG Capture Matrix

Use this matrix when recording manual live importer or retrieval checks. Keep the notes terse and do not commit raw live JSON artifacts.

| Input text | Provider/model | Dataset limit | Document count | Relevance category | Warning | Top-1 title | Top-3 titles | Relevant count in top 3 | Notes |
| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | --- |
| `cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill` | `openai / gpt-5.4-nano` | `5000` | `13` | `strong` | `no` | `Classic Baked Cheesecake` | `Classic Baked Cheesecake; No-Bake Cheesecake Bars; Apple Crumble with Vanilla Ice Cream` | `2/3` | `RAG support: Strong`; full `recipe-dataset` path used; citations rendered. |
| `carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat` | `openai / gpt-5.4-nano` | `5000` | `13` | `strong` | `no` | `Spaghetti Carbonara` | `Spaghetti Carbonara; Creamy Garlic Pasta; Aglio e Olio Pasta` | `2/3` | `RAG support: Strong`; carbonara-specific examples outrank broad pasta matches. |
| `omelet with eggs cheese maybe onions cooked in butter fold it over` | `openai / gpt-5.4-nano` | `5000` | `13` | `strong` | `no` | `Cheese Omelet` | `Cheese Omelet; Breakfast Sandwich; Skillet Pie` | `2/3` | `RAG support: Strong`; omelet ranking should not depend on generic breakfast terms. |
| `chicken and rice casserole chicken rice cream soup cheese bake until hot` | `openai / gpt-5.4-nano` | `5000` | `13` | `strong` | `no` | `Chicken and Rice Casserole` | `Chicken and Rice Casserole; Lemon Chicken Skillet; Rice Pilaf` | `2/3` | `RAG support: Strong`; casserole-specific result should outrank chicken-only and rice-only distractors. |

## Optional Live OpenAI Smoke Path

Use this only when intentionally proving the live provider path. It is not part of normal validation.

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
```

`OPENAI_API_KEY` must come from a local ignored environment source. Never show the key or environment file contents during the demo. If the ignored `.env` still says `OPENAI_ENABLE_LIVE_TESTS=false` or `AI_PROVIDER=mock`, the wrappers skip cleanly until you edit the local file or export explicit process values.

## Optional Live OpenAI Demo Evals

Use this when measuring live-provider quality and metrics for the complete demo flow. It is manual-only and is not part of normal validation.

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The command seeds generated demo data, runs readiness, importer, Ask My Cookbook, dataset search, dataset Ask/RAG, and meal planning, then writes ignored results under `.tmp-ai-demo/live-evals/<timestamp>/`. Importer live eval failures can surface sanitized provider categories when available, but no raw prompts, raw responses, or local paths.

See [Live OpenAI Demo Evals](live-openai-demo-evals.md).

The live eval wrapper also accepts `-EnvFile .\.env` so you can keep the live settings in a local ignored file rather than in the shell. It still skips cleanly if the file leaves `OPENAI_ENABLE_LIVE_TESTS=false` or `AI_PROVIDER=mock`.

## Open The UI

Start the sidecar, then open:

```text
http://127.0.0.1:8000/demo
```

Use `GET /demo/ai` as an equivalent route.

Docker Compose also exposes the sidecar locally at `127.0.0.1:8000` for operator testing. Compose still relies on local environment configuration for any data paths; the PowerShell start script is the preferred complete mock demo path because it seeds generated demo data automatically.

## Suggested 15 Minute Flow

1. Show the README AI showcase and explain the sidecar architecture.
2. Open the UI and refresh readiness.
3. Run the structured import/create workflow with the sample input and note servings, estimated quantities, steps, and citations.
4. Run saved-recipe Q&A and show recipe citations.
5. Run dataset search and point out ranked matches and provenance.
6. Run dataset Ask/RAG and show citations.
7. Run meal planning and show saved-recipe citations.
8. Show logs for one workflow request.
9. Close with boundaries: no production storage, no vector DB, no UI rewrite, no live CI calls.

Optional input-quality check: enter `!!!!!` in dataset search to show the "Input not usable yet" card, then enter `plan dinner` in meal planning to show the one-question clarification behavior. These responses should be deterministic and should not require provider calls.

## Suggested 30 Minute Flow

1. Start with the portfolio showcase and completion review.
2. Open the UI readiness panel and explain mock/offline mode.
3. Run importer and inspect servings, estimated quantities, citations/provenance, and raw JSON details.
4. Run saved-recipe Q&A and show the generated demo recipe citation.
5. Run dataset search and dataset Ask/RAG.
6. Run meal planning and show generated saved-recipe citations.
7. Open `scripts/demo-ai-requests.http` and show the same API surface.
8. Run or show offline evals.
9. Show structured logs and request IDs.
10. Discuss deferred options and non-goals.

## Troubleshooting

| Symptom | Next Step |
| --- | --- |
| Readiness says saved recipes unavailable | Rerun `scripts\start-ai-demo-local.ps1` or `scripts\seed-ai-demo-data.ps1`, then confirm `COOKBOOK_DB_PATH` points at the generated SQLite fixture. |
| Readiness says dataset unavailable | Rerun `scripts\start-ai-demo-local.ps1` or confirm `RECIPE_DATASET_DIR` points at the generated dataset fixture. |
| Workflow returns a friendly error | Check readiness, then inspect sidecar logs for request ID, endpoint, status, and safe error type. |
| Importer returns `503` after several seconds in live mode | Enable `-ProviderDebug`, rerun the importer-only diagnostic, and inspect `provider_error_category`, `provider_error_type`, and `safe_error_summary`. Common categories are `schema_rejection`, `timeout`, `bad_model`, `quota_or_rate_limit`, `auth`, and `network`. |
| Workflow shows "Needs one more detail" | Add one ingredient, recipe name, cooking method, or meal scope; the app intentionally asks only one bounded clarification question. |
| Workflow shows "Input not usable yet" | Replace empty, symbol-only, placeholder, or junk text with a concrete cooking request. |
| Provider unavailable | Confirm provider mode and use mock mode for normal demos. |
| Direct Windows pytest fails | Use the Git Bash validator path documented in repo validation; the known issue is a local temp-directory ACL problem. |

## Import/Create Recipe Notes

`POST /ai/import-recipe` now handles rough recipe creation notes as well as pasted recipe text. It defaults to 4 servings unless the user states another serving count. When quantities are missing, the draft should include reasonable estimates and disclose that they are estimated in `notes`.

When `RECIPE_DATASET_DIR` is configured and available, the importer retrieves a small bounded set of similar dataset recipes before the provider call. The retrieval is anchor-aware: exact dish names, core ingredients, and dish-specific phrases outrank broad dessert, pasta, or chicken matches. These examples are used only for structure, proportion hints, and step completeness. The model must preserve the user's core ingredients and dish intent, avoid copying retrieved recipes verbatim, and return citations/provenance for the examples that informed the draft. If retrieval is weak, the API returns a warning and the UI should treat the examples as structure-only guidance.

The provider prompt uses a deterministic context pack with small character budgets, so manual live validation should expect only 2 or 3 packed examples and a short snippet block instead of full raw recipe records.

The importer UI also shows a `RAG support` label and short message. Strong support means the retrieved examples closely matched the dish intent. Moderate support means the examples were related but partial. Weak support means the examples were broad and should be treated as structure-only. No-support means the draft came from notes, defaults, and disclosed assumptions.

The demo UI also shows cache status for dataset search and importer retrieval. A cache hit means the current process reused an existing in-memory index or retrieval result; the metadata only exposes short fingerprints and bounded entry counts.

The automated E2E integration test `ai-api/tests/test_rag_e2e_integration.py` covers the same importer route offline with generated dataset fixtures and the mock provider. Use it as the regression safety net before manual live RAG checks.

The dataset index now normalizes conservative aliases and phrase variants such as `omelette` -> `omelet`, `parmigiano-reggiano` -> `parmesan`, `no-bake` -> `no bake`, and `graham crackers` -> `graham cracker` while preserving the original recipe values for citations and display.

The next product layer is documented in [Recipe Session Requirements Architecture](recipe-session-requirements-architecture.md). Local alpha endpoints now exist under `/ai/recipe-session/*` for start/message/get/finalize flows, and the demo UI has a compact `Recipe Session Alpha` panel for exercising those endpoints. They are offline/mock-friendly, use bounded process-local memory, and reuse the existing importer/RAG path for draft generation. They are not production storage, public access, auth, paid access, or a full chat UI.

Suggested local session checks:

| Flow | Input | Expected result |
| --- | --- | --- |
| Clarification | `make dessert` | `clarification_needed`, one question, no draft |
| RAG refresh | start baked cheesecake, then `actually make it no-bake` | `rag_refreshed` or revised draft, changed method visible |
| No refresh | `thanks`, `looks good`, or `make it shorter` | `no_material_change`, no RAG refresh |
| Finalize | click `Finalize for demo` after a draft | `ready_to_finalize`, demo-only warning |
| Finalize before draft | start `make dessert`, then finalize | `clarification_needed`, no generated draft warning |
| Equipment refresh | `use air fryer instead` | `rag_refreshed`, equipment constraint visible |
| Exclusion refresh | `no nuts` or `no heavy cream` | `rag_refreshed`, excluded ingredient visible |

The live importer `503` issue observed during manual recipe-entry testing was caused by strict structured-output schema metadata that OpenAI rejected. `ai-api/app/providers/openai_schema.py` now strips unsupported metadata such as `default`, `examples`, `title`, and `description` recursively before the request is sent, while application-side importer behavior still defaults servings to 4.

Normal validation remains offline. Do not commit raw dataset files, generated `.tmp-ai-demo/` artifacts, raw provider responses, screenshots, private env files, or credentials.

## Log Viewing

Local sidecar process logs appear in the terminal running the sidecar.

With Docker Compose:

```powershell
docker compose logs ai-api --tail 100
```

Useful log fields:

- `event`
- `request_id`
- `ui_workflow`
- `endpoint_name`
- `provider`
- `model`
- `status`
- `duration_ms`
- `retrieved_count`
- `citation_count`
- `warning_count`
- `safe_error_type`
- `provider_error_category`
- `provider_error_type`
- `safe_error_summary`

## Screenshot Guidance

Prefer screenshots of:

- readiness panel;
- importer result;
- dataset search provenance;
- dataset Ask/RAG citations;
- raw JSON collapsed unless needed;
- structured logs without secrets.

Follow [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md). Do not commit screenshots in this task.

## Boundaries And Non-Goals

This demo does not add production storage, deployment changes, Cloudflare changes, control-plane workflows, live provider tests in CI, Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, upstream Vanilla Cookbook frontend rewrites, browser automation, committed screenshots, raw dataset commits, generated artifact commits, private environment files, or credentials.

## Future Production Hardening

Future paid or time-limited application work should be split into separate tasks. Likely areas include authenticated access, time-limited sessions, monetization gates, usage metering, user/session isolation, durable storage, multi-use-case routing, deployment exposure controls, provider cost controls, and an admin/operator dashboard.

The monetization and entitlement boundary itself is documented in [AI Monetization And Entitlement Boundary ADR](ai-monetization-and-entitlement-boundary-adr.md). That ADR keeps the near-term ads/sponsors model separate from access control and provider budgets.

The locked 29/30 regression baseline is documented in [29/30 Integrated Regression And E2E Harness](ai-29-30-regression-e2e-harness.md). Run `scripts\run-ai-29-30-regression.ps1` to exercise the combined offline baseline; it only performs its optional live-smoke boundary when `AI_29_30_REGRESSION_LIVE=true` and the OpenAI live-test environment is explicitly configured.

The first schema-only step for that future layer is documented in [AI Session Metering Schema](ai-session-metering-schema.md). It defines safe local models for demo sessions, access grants, meter events, quality events, audit events, and budget snapshots. It does not enable runtime auth, public access, production storage, paid access, invite flows, budget enforcement, or live provider calls.

Future recipe-creation interaction work should also remain separately scoped. The 0030A architecture covers alpha requirements extraction, clarification, session memory, and RAG refresh decisions, but does not implement production storage, persistent user memory, auth, paid access, public route exposure, embeddings, vector databases, or a full chat UI.
