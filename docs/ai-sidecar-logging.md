# AI Sidecar Logging

The AI sidecar now emits structured JSON logs to stdout. Docker Compose can collect these logs per service without adding external logging infrastructure.

## Request Logs

Middleware assigns a request ID, measures duration, and logs one `ai.request` event per request.

Safe fields include:

- `event`
- `timestamp`
- `request_id`
- `endpoint_name`
- `ui_workflow` when the browser demo sends a workflow label
- `status`
- `duration_ms`
- `safe_error_type` when an unhandled exception occurs

## Workflow Logs

AI workflow handlers emit `ai.workflow` events after successful workflow calls and for handled provider/read/validation errors.

Safe fields can include:

- `event`
- `timestamp`
- `request_id`
- `endpoint_name`
- `provider`
- `model`
- `status`
- `retrieved_count`
- `citation_count`
- `warning_count`
- `safe_error_type`

## What Is Not Logged

The logging foundation does not log by default:

- provider API keys;
- full environment contents;
- authorization headers;
- full prompts;
- full pasted recipes;
- full provider response bodies;
- raw provider config;
- private local filesystem paths;
- raw dataset records;
- private recipe/user data.

## Viewing Logs

Local process logs appear in the terminal running the FastAPI sidecar.

With Docker Compose, use the service log stream:

```powershell
docker compose logs ai-api
docker compose logs ai-api --tail 100
```

The current Compose file includes an `ai-api` service. This task only adds the application logging foundation and does not add an external log backend.

## Validation

Tests cover:

- request middleware emits safe structured fields;
- workflow helper emits counts and provider/model metadata;
- demo UI requests include a safe `ui_workflow` label;
- obvious sensitive markers are absent from logged test output.

Log shape may grow in later tasks, but raw secrets and large payloads should remain excluded by default.
