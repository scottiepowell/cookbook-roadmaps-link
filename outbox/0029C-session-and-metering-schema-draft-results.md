# 0029C Session And Metering Schema Draft Results

## Summary

Completed the schema-only scaffold for future AI demo access and metering. Added deterministic Pydantic models for AI demo sessions, access grants, provider meter events, quality/eval events, admin audit events, and budget snapshots.

This task did not add runtime auth, production storage, migrations, paid access, public route exposure, invite emails, budget enforcement runtime, admin UI, or live OpenAI calls.

## Models Added

New module:

```text
ai-api/app/ai_access_models.py
```

Models and enums include:

- `AiDemoSession`
- `AiAccessGrant`
- `AiProviderMeterEvent`
- `AiQualityEvent`
- `AiAdminAuditEvent`
- `AiBudgetSnapshot`
- workflow/status/type/action enums for deterministic future use
- `safe_operator_view()` helper

## Safe Serialization

Each model exposes `safe_view()` for future public/operator response shaping. The models reject secret-like or private-path-like values in safe string and metadata fields.

Tests cover forbidden strings including:

- provider key names;
- token prefixes;
- authorization headers;
- environment-file labels;
- generated demo artifact paths;
- raw prompt/response labels;
- local private path markers;
- private storage/cache URLs.

Safe views include IDs, statuses, timestamps, workflow names, provider/model names, counts, cost estimates, and safe fingerprints only.

## Budget Snapshot Behavior

`AiBudgetSnapshot` calculates:

- `remaining_provider_calls`
- `remaining_estimated_cost_usd`
- `is_exhausted`
- `status_reason`

Covered reasons:

- `within_budget`
- `provider_call_limit_exhausted`
- `cost_limit_exhausted`
- `provider_call_and_cost_limits_exhausted`

The model is calculation-only. It does not enforce budgets at runtime.

## Tests Added

New tests:

```text
ai-api/tests/test_ai_access_models.py
```

Coverage includes:

- valid sample creation for all models;
- default statuses and defaults;
- provider meter event with mock/offline provider;
- provider meter event with token/cost data;
- access grant safe serialization;
- audit event safe serialization;
- quality event safe serialization;
- budget remaining-call and remaining-cost calculations;
- exhausted budget behavior;
- forbidden-string rejection.

## Docs Updated

Created:

- `docs/ai-session-metering-schema.md`

Updated:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`

The documentation explains how these schemas support future operator gate, invite flow, provider budget enforcement, and admin usage report tasks.

## Validation Results

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_access_models.py` - passed, 12 tests.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` - passed, 39/39 offline eval cases.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` - passed, including 232 pytest tests and 39 offline eval cases.
- `git diff --check` - passed with line-ending warnings only.
- `docker compose config --quiet` - passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` - passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` - skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` - skipped cleanly without live opt-in.

## Explicit Non-Goals

Not implemented:

- production storage;
- database migrations;
- auth;
- paid access;
- public route exposure;
- Cloudflare changes;
- persistent user memory;
- Redis, Postgres, or SQLite session persistence;
- payment provider integration;
- invite emails;
- live OpenAI calls;
- budget enforcement runtime;
- admin dashboard UI;
- public API keys or secrets.

## Artifact Safety

Confirmed no raw dataset files, `.tmp-ai-demo` artifacts, generated persistent indexes, disk cache files, `.env` files, screenshots, logs, credentials, raw provider prompts, raw provider responses, production session storage, payment secrets, or invite secrets were added.
