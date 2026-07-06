# Task 0027C: Manual UI Demo Acceptance Test

## Goal

Run and document a real manual acceptance test of the AI demo UI as if you were a 15 to 30 minute demo user.

This task should start after `0027B` is complete. `0027A` creates the initial sidecar UI/logging foundation, and `0027B` hardens the UI for production-quality demo usability. `0027C` is where the human operator opens the deployed/local URL, clicks through the app, records what works, and captures follow-up fixes.

## When To Start Manual URL Testing

Use this staged approach:

1. After `0027A`: quick technical smoke check only.
   - Confirm the UI route loads.
   - Confirm static assets load.
   - Confirm logging emits request IDs and safe metadata.
   - Do not judge demo readiness yet.

2. After `0027B`: full demo-user acceptance testing.
   - Open the UI as a user.
   - Run the 15 minute and 30 minute demo flows.
   - Confirm the UI feels complete, understandable, and resilient.
   - Record defects and friction.

3. After `0027C`: create follow-up fix tasks from observed issues.
   - Screenshot-safe polish.
   - Copy/wording improvements.
   - Missing-data handling.
   - Error handling improvements.
   - Any deployment route or URL exposure gaps.

## Build On

This task depends on:

- `0027A`: sidecar AI demo UI and logging foundation
- `0027B`: production-quality AI demo usability

Before starting, confirm the repo has:

- `outbox/0027A-add-ai-demo-ui-and-logging-results.md`
- `outbox/0027B-production-quality-ai-demo-usability-results.md`
- AI demo UI route and static assets
- `docs/ai-live-demo-runbook.md`
- `docs/ai-sidecar-logging.md`
- `docs/ai-ui-integration-plan.md`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

This is an acceptance-testing and documentation task, not a feature-building task.

Create a manual test checklist and record results. If small documentation corrections are needed, make them. If functional issues are found, document them clearly and recommend follow-up tasks rather than making broad feature changes inside this task.

## Manual Test Targets

Test at least two paths if available:

1. Local developer URL.
   - Example: `http://127.0.0.1:<ai-api-port>/demo` or the route documented by `0027A`/`0027B`.

2. Deployed/public URL, if the AI UI is exposed through the current deployment.
   - Example: the existing Cookbook domain plus the documented AI demo route, only if deployment exposes the sidecar route.
   - If the sidecar UI is not publicly routed yet, document that as a deployment exposure gap and defer it to a separate task.

Do not change Cloudflare, deployment, or routing in this task unless it was already implemented by a prior task and only docs need correction.

## User Acceptance Checklist

Create a checklist covering:

- Page loads without browser console errors.
- Layout is usable on a laptop screen.
- Health/config status is understandable.
- Provider mode is clear: mock vs OpenAI.
- Importer flow works with sample input.
- Ask My Cookbook flow works or clearly explains missing saved-recipe data.
- Dataset search works or clearly explains missing dataset data.
- Dataset ask/RAG works or clearly explains missing dataset data.
- Meal planner works or clearly explains missing saved-recipe data.
- Loading states appear while requests run.
- Buttons are disabled while requests run.
- Reset buttons work.
- Errors are user-friendly and do not show raw stack traces.
- Citations/provenance are readable.
- Warnings are visible and useful.
- Raw JSON is available but not the primary user experience.
- Logs show useful request IDs and workflow metadata.
- No sensitive runtime values, private local paths, raw keys, or private data are visible in the UI or logs.
- The UI is screenshot-ready with demo-safe data.

## Demo Flow Tests

Run and document:

### 15 Minute Flow

- Open the UI.
- Check status.
- Run importer.
- Run dataset search.
- Run dataset ask.
- Run meal planner or saved-recipe ask if data is available.
- Open logs and confirm request IDs and workflow events.
- Capture observations.

### 30 Minute Flow

- Run all 15 minute checks.
- Try alternate sample inputs.
- Trigger at least one friendly error path.
- Test missing-data handling if possible.
- Test reset buttons.
- Confirm outputs remain readable after several runs.
- Confirm no confusing stale state remains between workflow runs.

## Logging Checks

Verify operator log commands from the docs, such as:

```powershell
docker compose logs ai-api --tail 100
```

or local server logging commands if running without Docker.

Confirm logs include safe operational metadata such as:

- request ID;
- endpoint/workflow;
- status;
- duration;
- provider/model when available;
- retrieved/citation/warning counts when available.

Confirm logs do not include large raw user payloads by default.

## Outputs

Create:

```text
docs/ai-manual-ui-acceptance-test.md
outbox/0027C-manual-ui-demo-acceptance-test-results.md
```

Optionally update:

```text
docs/ai-live-demo-runbook.md
docs/ai-screenshot-capture-guide.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
```

## Results Format

The acceptance test report should include:

- Test environment: local, deployed, or both.
- Exact URL(s) tested.
- Browser used.
- Provider mode tested: mock, OpenAI, or both.
- Date/time of test.
- 15 minute flow result.
- 30 minute flow result.
- Feature-by-feature pass/fail table.
- Logging verification result.
- Screenshot readiness result.
- Issues found.
- Recommended follow-up tasks.

If manual testing is not actually performed by Codex, the task should create the checklist/runbook and clearly mark the human-run results as pending.

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
```

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

The live smoke wrapper should skip cleanly unless explicitly opted in. Do not run live provider calls during normal validation.

## Non-Goals

Do not implement production storage, deployment changes, Cloudflare changes, control-plane workflows, live provider tests in CI, Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, upstream Vanilla Cookbook frontend rewrite, browser automation, committed screenshots, raw dataset commits, generated artifact commits, private environment file commits, or credential commits.

## Outbox Report

Create:

```text
outbox/0027C-manual-ui-demo-acceptance-test-results.md
```

Include:

- Summary
- Files changed
- Whether manual URL testing was performed or left pending for the human operator
- Exact URL(s) tested or planned
- Acceptance checklist status
- 15 minute flow status
- 30 minute flow status
- Logging verification status
- Screenshot readiness status
- Issues found
- Recommended follow-up tasks
- Validation results
- Confirmation that normal validation stayed offline
- Confirmation that no private environment files, raw datasets, generated artifacts, screenshots, or credentials were committed

## Commit

Commit and push:

```bash
git add docs README.md outbox/0027C-manual-ui-demo-acceptance-test-results.md

git commit -m "mailbox: complete task 0027C manual ui demo acceptance test"

git push origin main
```

## Done Criteria

- Manual acceptance checklist exists.
- 15 minute and 30 minute demo flows are documented.
- The point at which the human should start URL testing is explicit.
- The report either records actual manual testing or clearly marks human testing as pending.
- Logging checks are included.
- Follow-up issues/tasks are recommended based on observed or expected gaps.
- Normal validation passes or the known Windows direct-pytest issue is documented with Git Bash validator passing.
- No production infrastructure changes are made.
