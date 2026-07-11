# AI Admin Usage Report Prototype

## Purpose

This document describes the local/operator usage report prototype added in `0029G`.
It is a safe, process-local reporting surface for demo operators who need to answer:

- which demo sessions and grants are active, expired, revoked, used, or completed;
- how many provider decisions were allowed, blocked, skipped, or failed;
- what the current estimated spend and remaining budget look like;
- which workflows are being used;
- whether quality/eval failures or safety warnings are present;
- whether any thresholds are close to exhaustion.

The report is intentionally local/private only. It does not add production admin auth, a production dashboard, user accounts, billing, or public route exposure.
It also does not enforce monetization or entitlements.

## Relationship To Earlier Tasks

- `0029C` defined the safe access, grant, meter, quality, audit, and budget snapshot models.
- `0029D` added the local/private operator gate.
- `0029E` added the centralized provider budget guard and safe meter events.
- `0029F` added invite-only demo sessions and safe invite/session views.

`0029G` reads those process-local models and snapshots and turns them into an operator-friendly summary.

## Report Shape

The helper builds an `AiUsageReport` with these sections:

- `summary`
- `sessions`
- `grants`
- `provider_meter_events`
- `budget_snapshots`
- `quality_events`
- `audit_events`
- `warnings`
- `thresholds`
- `generated_at`

The summary keeps stable defaults when no state exists.

### Summary Fields

The summary includes:

- session counts: `active_session_count`, `expired_session_count`, `revoked_session_count`, `completed_session_count`;
- grant counts: `active_grant_count`, `used_grant_count`, `revoked_grant_count`, `expired_grant_count`;
- provider counts: `provider_calls_allowed`, `provider_calls_blocked`, `provider_calls_skipped`, `provider_calls_failed`;
- budget totals: `estimated_cost_usd_total`, `remaining_estimated_cost_usd_total`;
- quality counts: `quality_pass_count`, `quality_warning_count`, `quality_failure_count`;
- `threshold_warning_count`.

## Helper And Endpoint

The report builder lives in:

```text
ai-api/app/ai_usage_report.py
```

The local/operator endpoint is:

```text
GET /ai/admin/usage-report
```

The endpoint is protected by the local operator gate when the gate is enabled. When the gate is disabled, local/mock validation stays unchanged.

The endpoint returns safe JSON only. It does not expose raw invite/session tokens, prompts, provider responses, request bodies, API keys, stack traces, or local paths.

The route is hidden from OpenAPI and should remain private forever unless the app gains a separate, intentionally public admin design. That is not part of this prototype.

The demo UI also shows a compact local usage-report card at `/demo`.

Route exposure review for future public access lives in [AI Public Route Exposure Review](ai-public-route-exposure-review.md).

## Threshold Logic

The prototype emits deterministic warnings when:

- a session is at or above 80 percent of its provider-call limit;
- a session is at or above 80 percent of its estimated-cost limit;
- any provider decision was blocked;
- any provider decision failed;
- any quality event failed;
- any quality event warned;
- an active session or grant expires soon;
- invite sessions are enabled while the operator gate is disabled;
- invite sessions are enabled while the provider budget guard is disabled or misconfigured.

Warnings are structured and safe. They carry severity and codes only, plus safe IDs where useful.

## Quality Events

The report accepts `AiQualityEvent` values through a bounded, process-local collector. Tests can reset the collector and seed safe quality events without disk persistence.

If no runtime quality events exist, the report still serializes safely with empty quality sections.

## Safe Serialization Rules

The report only includes safe views and snapshots.

Allowed examples:

- IDs;
- statuses;
- counts;
- timestamps;
- workflow names;
- safe fingerprints;
- safe cost and budget numbers.

Forbidden examples:

- raw invite or session tokens;
- API keys;
- `Authorization` headers;
- request bodies;
- raw prompts;
- raw provider responses;
- `.env` content;
- local absolute paths;
- stack traces;
- storage URLs.

## Local Demo Examples

Check the empty report:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/ai/admin/usage-report
```

Open the report in the local demo UI:

```text
http://127.0.0.1:8000/demo
```

The UI card shows a short safe summary and a JSON link for local operators.

## Non-Goals

This prototype does not add:

- production admin auth;
- user accounts;
- login UI;
- OAuth/OIDC;
- paid access;
- payment integration;
- invite emails;
- database migrations;
- persistent storage;
- Redis, Postgres, or SQLite persistence;
- public route exposure;
- live OpenAI calls during normal validation;
- raw logs, screenshots, or generated artifacts in repo files.
