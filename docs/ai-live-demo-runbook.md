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

- Confirm the sidecar can start locally.
- Open the browser UI at `http://127.0.0.1:8000/demo`.
- Open a terminal for logs.

## Mock/Demo Mode Path

The default demo path uses the mock provider and generated fixtures. It is free, deterministic, and safe for screenshots.

```powershell
$env:AI_PROVIDER="mock"
```

The UI readiness panel shows whether:

- the sidecar is healthy;
- provider mode is mock or OpenAI;
- saved-recipe data is available;
- local dataset data is available.

If saved-recipe or dataset data is missing, continue with the workflows that are available. Missing data should appear as a friendly recoverable condition.

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

## Open The UI

Start the sidecar, then open:

```text
http://127.0.0.1:8000/demo
```

Use `GET /demo/ai` as an equivalent route.

## Suggested 15 Minute Flow

1. Show the README AI showcase and explain the sidecar architecture.
2. Open the UI and refresh readiness.
3. Run the structured importer with the sample input.
4. Run dataset search and point out ranked matches and provenance.
5. Run dataset Ask/RAG and show citations.
6. Show logs for one workflow request.
7. Close with boundaries: no production storage, no vector DB, no UI rewrite, no live CI calls.

## Suggested 30 Minute Flow

1. Start with the portfolio showcase and completion review.
2. Open the UI readiness panel and explain mock/offline mode.
3. Run importer and inspect the raw JSON details.
4. Run saved-recipe Q&A if saved-recipe data is configured; otherwise explain the friendly missing-data message.
5. Run dataset search and dataset Ask/RAG.
6. Run meal planning if saved-recipe data is configured.
7. Open `scripts/demo-ai-requests.http` and show the same API surface.
8. Run or show offline evals.
9. Show structured logs and request IDs.
10. Discuss deferred options and non-goals.

## Troubleshooting

| Symptom | Next Step |
| --- | --- |
| Readiness says saved recipes unavailable | Configure a local cookbook SQLite DB or skip saved-recipe Q&A and meal planning. |
| Readiness says dataset unavailable | Configure `RECIPE_DATASET_DIR` or focus on importer and saved-recipe flows. |
| Workflow returns a friendly error | Check readiness, then inspect sidecar logs for request ID, endpoint, status, and safe error type. |
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
