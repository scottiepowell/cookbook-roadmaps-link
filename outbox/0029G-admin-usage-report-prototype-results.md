# 0029G Admin Usage Report Prototype Results

Implemented a local/operator usage-report prototype for the AI sidecar.

## What Changed

- Added `ai-api/app/ai_usage_report.py` with:
  - `AiUsageReport` and section models for `summary`, `sessions`, `grants`, `provider_meter_events`, `budget_snapshots`, `quality_events`, `audit_events`, `warnings`, `thresholds`, and `generated_at`;
  - a safe report builder that reads process-local invite/session state, meter events, and quality/audit collectors;
  - a bounded process-local collector for safe `AiQualityEvent` and `AiAdminAuditEvent` values;
  - deterministic threshold warnings for near-exhaustion, blocked/failed provider decisions, quality failures/warnings, expiring sessions/grants, and misconfiguration patterns.
- Extended `ai-api/app/ai_budget_guard.py` so the tracker keeps safe meter-event history for allowed, blocked, skipped, and failed decisions.
- Extended `ai-api/app/ai_invite_sessions.py` so expired invite grants/sessions stay available as safe in-memory history for reporting, and added a `complete_session()` helper for local/test support.
- Added `GET /ai/admin/usage-report` in `ai-api/app/main.py`, protected by the local operator gate when enabled and hidden from OpenAPI schema.
- Added a small local usage-report status card to `/demo` in `ai-api/app/static/demo.html` and `ai-api/app/static/demo.js`.
- Added deterministic tests in `ai-api/tests/test_ai_usage_report.py`.
- Updated `ai-api/tests/test_demo_ui.py` to cover the new demo UI status card and report endpoint strings.
- Updated docs:
  - `docs/ai-admin-usage-report-prototype.md`
  - `docs/ai-session-metering-schema.md`
  - `docs/ai-local-operator-access-gate.md`
  - `docs/ai-provider-budget-enforcement.md`
  - `docs/ai-invite-only-demo-session-flow.md`
  - `docs/ai-live-demo-runbook.md`
  - `docs/ai-feature-status.md`
  - `docs/ai-evals-plan.md`
  - `docs/ai-implementation-backlog.md`
  - `README.md`
- Updated `scripts/demo-ai-mock.ps1` to verify the usage-report endpoint in the default offline path.

## Behavior

- Empty/default report is stable and safe.
- Report summarizes:
  - active, expired, revoked, used, and completed grants/sessions;
  - provider calls allowed, blocked, skipped, and failed;
  - estimated spend and remaining budget;
  - workflow usage through safe session/grant snapshots;
  - quality/eval activity and audit activity when present.
- Threshold warnings are deterministic and structured.
- The report only exposes safe snapshots and never returns raw invite/session tokens, operator tokens, prompts, provider responses, request bodies, environment values, local absolute paths, logs, or stack traces.

## Tests Added

- Empty report returns stable defaults.
- Active/expired/revoked/used/completed grants and sessions count correctly.
- Provider meter events count by status.
- Estimated cost totals and remaining budget summarize correctly.
- Near-exhaustion thresholds fire at or above 80 percent.
- Blocked provider decisions create warnings.
- Quality failures create warnings.
- Safe serialization excludes forbidden strings.
- Usage-report endpoint is protected when the operator gate is enabled.
- Usage-report endpoint does not expose raw invite/session tokens.
- Demo UI includes the new usage-report card and safe endpoint references.

## Validation

Passed:

- `pytest ai-api/tests/test_ai_usage_report.py -q`
- `pytest ai-api/tests/test_demo_ui.py -q -k 'not seeded_demo_data_supports_saved_recipe_workflows'`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1`
- `docker compose config --quiet`
- `git diff --check`

Notes:

- The full `ai-api/tests/test_demo_ui.py` module still contains one existing Windows temp-dir ACL-sensitive fixture test outside this change; the new usage-report/UI checks passed when that one case was filtered out.
- The live wrappers skipped cleanly with their default no-opt-in settings.

## Explicit Non-Goals

- No production admin dashboard.
- No production auth, user accounts, login UI, OAuth/OIDC, or paid access.
- No invite emails, public route exposure, Cloudflare changes, database migrations, Redis, Postgres, SQLite, or persistent storage.
- No live OpenAI calls during normal validation.
- No raw tokens, secrets, screenshots, logs, or generated artifacts committed to the repo.

## Artifact Safety

Confirmed safe:

- no raw invite/session tokens in committed files;
- no `.env` files;
- no credentials or API keys;
- no raw provider prompts or raw provider responses;
- no production session storage;
- no persistent user memory;
- no screenshots or log artifacts.
