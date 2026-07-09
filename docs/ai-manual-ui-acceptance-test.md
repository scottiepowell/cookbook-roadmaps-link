# AI Manual UI Acceptance Test

This checklist is the manual acceptance script for the AI demo UI after `0027A` and `0027B`.

`0027A`, `0027B`, and `0027C` are complete. Human manual testing after `0027C` found that saved-recipe workflows needed generated demo data. `0027D` adds a local mock launch path with small demo-safe saved recipes.

## Human Steps

Open this:

```text
http://127.0.0.1:8000/demo
```

Run this first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

This starts safe mock mode by default. For intentional live OpenAI manual acceptance, set `OPENAI_API_KEY` in the environment and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

The live launch defaults to `OPENAI_MODEL=gpt-5.4-nano`, `OPENAI_LIVE_TEST_BUDGET_CENTS=25`, and `AI_MAX_OUTPUT_TOKENS=500`. Use explicit parameters when testing a different local port or bounded output limit:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests -OpenAIModel gpt-5.4-nano -MaxOutputTokens 600 -LiveTestBudgetCents 50 -Port 8001
```

Look for this:

- readiness shows sidecar healthy;
- provider shows `mock / mock-basic` for the default path, or OpenAI/model details for an intentional live run;
- saved recipes show at least 3 recipe(s);
- dataset shows available;
- Ask My Cookbook returns a readable answer with recipe citations;
- Meal Planner returns a readable plan with recipe citations;
- Dataset Search and Dataset Ask/RAG still return readable results with provenance;
- logs show request IDs, workflow labels, endpoint/status/duration, and safe metadata.

Record this:

- exact local URL tested;
- browser used;
- readiness counts and provider mode;
- pass/fail for the 15-minute and 30-minute flows;
- issues, confusing copy, or screenshot-readiness gaps;
- whether the deployed `/demo` URL is exposed or still pending.

## Test Targets

Fill these fields during human testing:

| Field | Value |
| --- | --- |
| Date/time | Pending human test |
| Tester | Pending human test |
| Browser | Pending human test |
| Provider mode | Pending human test: mock, OpenAI, or both |
| Local URL | `http://127.0.0.1:8000/demo` |
| Deployed URL | Pending human test; fill if the sidecar demo route is publicly exposed |
| Notes on route exposure | Pending human test |

Do not treat the deployed URL as accepted until a human opens the documented `/demo` route and records the result. If the sidecar UI is not publicly routed, record that as a deployment exposure gap for a follow-up task.

## Next Human Step

Open the documented `/demo` URL through `scripts\start-ai-demo-local.ps1` and run both flows:

- 15-minute demo flow.
- 30-minute demo flow.

Record results in the current task outbox or a later human findings task.

## Acceptance Checklist

Mark each row during human testing.

| Check | Status | Notes |
| --- | --- | --- |
| Page loads without browser console errors. | Pending human test | |
| Layout is usable on a laptop screen. | Pending human test | |
| Health/config status is understandable. | Pending human test | |
| Provider mode is clear: mock vs OpenAI. | Pending human test | |
| Importer flow works with sample input. | Pending human test | |
| Ask My Cookbook flow works with generated saved-recipe demo data. | Pending human test | |
| Dataset search works or clearly explains missing dataset data. | Pending human test | |
| Dataset ask/RAG works or clearly explains missing dataset data. | Pending human test | |
| Meal planner works with generated saved-recipe demo data. | Pending human test | |
| Loading states appear while requests run. | Pending human test | |
| Buttons are disabled while requests run. | Pending human test | |
| Reset buttons work. | Pending human test | |
| Errors are user-friendly and do not show raw stack traces. | Pending human test | |
| Citations/provenance are readable. | Pending human test | |
| Warnings are visible and useful. | Pending human test | |
| Raw JSON is available but not the primary user experience. | Pending human test | |
| Logs show useful request IDs and workflow metadata. | Pending human test | |
| No sensitive runtime values, private local paths, raw keys, or private data are visible in the UI or logs. | Pending human test | |
| The UI is screenshot-ready with demo-safe data. | Pending human test | |

## 15-Minute Flow

Human-run status: pending.

1. Open the UI.
2. Check readiness, health, and provider config.
3. Run importer with sample input.
4. Run dataset search.
5. Run dataset ask/RAG.
6. Run Ask My Cookbook and meal planner with generated saved-recipe data.
7. Open logs and confirm request IDs and workflow events.
8. Capture observations, issues, and screenshot readiness notes.

Record:

| Field | Result |
| --- | --- |
| Overall result | Pending human test |
| URL tested | Pending human test |
| Provider mode | Pending human test |
| Observations | Pending human test |
| Issues found | Pending human test |

## 30-Minute Flow

Human-run status: pending.

1. Run all 15-minute checks.
2. Try alternate sample inputs.
3. Trigger at least one friendly error path.
4. Test missing-data handling if possible.
5. Test reset buttons.
6. Confirm outputs remain readable after several runs.
7. Confirm no confusing stale state remains between workflow runs.

Record:

| Field | Result |
| --- | --- |
| Overall result | Pending human test |
| URL tested | Pending human test |
| Provider mode | Pending human test |
| Observations | Pending human test |
| Issues found | Pending human test |

## Logging Verification

Human-run status: pending.

Use Docker Compose logs when testing the sidecar through Compose:

```powershell
docker compose logs ai-api --tail 100
```

If running FastAPI directly, inspect the terminal running the sidecar.

Confirm logs include safe operational metadata:

| Log check | Status | Notes |
| --- | --- | --- |
| Request ID is present. | Pending human test | |
| Endpoint or workflow is present. | Pending human test | |
| Status is present. | Pending human test | |
| Duration is present. | Pending human test | |
| Provider/model is present when available. | Pending human test | |
| Retrieved/citation/warning counts are present when available. | Pending human test | |
| Large raw user payloads are not logged by default. | Pending human test | |
| API keys, credentials, private paths, and private data are not visible. | Pending human test | |

## Screenshot Readiness

Human-run status: pending.

Confirm the UI can be captured with demo-safe data:

| Check | Status | Notes |
| --- | --- | --- |
| First viewport clearly communicates the AI demo. | Pending human test | |
| Main workflows are visible and understandable. | Pending human test | |
| Example outputs are readable. | Pending human test | |
| Citations/provenance can be captured safely. | Pending human test | |
| No secrets, local private paths, or private data are visible. | Pending human test | |

## Recommended Follow-Up

Create a later human findings task after a human has rerun the local and, if available, deployed `/demo` URL.

Use 0027D to address observed defects, copy polish, screenshot-safe layout issues, missing-data handling gaps, logging clarity issues, or deployment route exposure gaps. Do not fold broad UI fixes back into 0027C unless they are documentation corrections.
