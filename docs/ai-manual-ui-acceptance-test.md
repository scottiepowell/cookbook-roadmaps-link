# AI Manual UI Acceptance Test

This checklist is the manual acceptance script for the AI demo UI after `0027A` and `0027B`.

`0027A` and `0027B` are complete. `0027C` prepared this checklist and report path, but Codex did not complete manual URL testing. Human-run URL testing is pending.

## Test Targets

Fill these fields during human testing:

| Field | Value |
| --- | --- |
| Date/time | Pending human test |
| Tester | Pending human test |
| Browser | Pending human test |
| Provider mode | Pending human test: mock, OpenAI, or both |
| Local URL | Pending human test; planned default: `http://127.0.0.1:8000/demo` |
| Deployed URL | Pending human test; fill if the sidecar demo route is publicly exposed |
| Notes on route exposure | Pending human test |

Do not treat the deployed URL as accepted until a human opens the documented `/demo` route and records the result. If the sidecar UI is not publicly routed, record that as a deployment exposure gap for a follow-up task.

## Next Human Step

Open the documented `/demo` URL and run both flows:

- 15-minute demo flow.
- 30-minute demo flow.

Record results in `outbox/0027C-manual-ui-demo-acceptance-test-results.md` or in the follow-up task `0027D: Human UI Demo Findings And Fixes`.

## Acceptance Checklist

Mark each row during human testing.

| Check | Status | Notes |
| --- | --- | --- |
| Page loads without browser console errors. | Pending human test | |
| Layout is usable on a laptop screen. | Pending human test | |
| Health/config status is understandable. | Pending human test | |
| Provider mode is clear: mock vs OpenAI. | Pending human test | |
| Importer flow works with sample input. | Pending human test | |
| Ask My Cookbook flow works or clearly explains missing saved-recipe data. | Pending human test | |
| Dataset search works or clearly explains missing dataset data. | Pending human test | |
| Dataset ask/RAG works or clearly explains missing dataset data. | Pending human test | |
| Meal planner works or clearly explains missing saved-recipe data. | Pending human test | |
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
6. Run meal planner or Ask My Cookbook if saved-recipe data is available.
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

Create `0027D: Human UI Demo Findings And Fixes` after a human has run the local and, if available, deployed `/demo` URL.

Use 0027D to address observed defects, copy polish, screenshot-safe layout issues, missing-data handling gaps, logging clarity issues, or deployment route exposure gaps. Do not fold broad UI fixes back into 0027C unless they are documentation corrections.
