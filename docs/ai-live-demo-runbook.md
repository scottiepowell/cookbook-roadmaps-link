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

- Open the browser UI at `http://127.0.0.1:8000/demo`.
- Open a terminal for logs.

## Mock/Demo Mode Path

The default demo path uses the mock provider and generated fixtures. It is free, deterministic, and safe for screenshots.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

The start script generates a small local fixture under `.tmp-ai-demo/`, sets `AI_PROVIDER=mock`, points `COOKBOOK_DB_PATH` at a generated SQLite database, points `RECIPE_DATASET_DIR` at generated CSV data, and starts the sidecar on `127.0.0.1:8000`. It does not write to production cookbook data.

The UI readiness panel shows whether:

- the sidecar is healthy;
- provider mode is mock or OpenAI;
- saved-recipe demo data is available;
- local dataset demo data is available.

In the local mock demo path, readiness should show saved recipes available and dataset available. If either is missing, stop and rerun `scripts\start-ai-demo-local.ps1`; missing data should appear as a friendly recoverable condition, not a browser failure.

## Optional Live OpenAI Smoke Path

Use this only when intentionally proving the live provider path. It is not part of normal validation.

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
```

`OPENAI_API_KEY` must come from a local ignored environment source. Never show the key or environment file contents during the demo.

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

The command seeds generated demo data, runs readiness, importer, Ask My Cookbook, dataset search, dataset Ask/RAG, and meal planning, then writes ignored results under `.tmp-ai-demo/live-evals/<timestamp>/`.

See [Live OpenAI Demo Evals](live-openai-demo-evals.md).

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
3. Run the structured importer with the sample input.
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
3. Run importer and inspect the raw JSON details.
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
| Workflow shows "Needs one more detail" | Add one ingredient, recipe name, cooking method, or meal scope; the app intentionally asks only one bounded clarification question. |
| Workflow shows "Input not usable yet" | Replace empty, symbol-only, placeholder, or junk text with a concrete cooking request. |
| Provider unavailable | Confirm provider mode and use mock mode for normal demos. |
| Direct Windows pytest fails | Use the Git Bash validator path documented in repo validation; the known issue is a local temp-directory ACL problem. |

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
