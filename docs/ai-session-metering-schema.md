# AI Session Metering Schema

## Purpose

This document describes the local schema scaffold for future AI demo access control, session tracking, metering, quality reporting, admin audit events, and budget snapshots.

The current AI sidecar already supports a strong local demo surface: RAG-informed importer, deterministic retrieval, citation/provenance metadata, recipe-session alpha endpoints, Recipe Session Alpha UI, and offline evals. The next production-readiness boundary is controlled access and cost observability. These schemas define the data shape future tasks can use before adding an operator gate, invite-only flow, provider budget enforcement, or admin reports.

This is schema-only work. It does not add production storage, auth, billing, public live AI exposure, database migrations, invite emails, budget enforcement runtime, or an admin dashboard.

`0029E` builds the runtime provider budget guard on top of these models. That task keeps the guard deterministic and process-local while using the schema shapes below for safe snapshots, meter events, and operator views.

## Model Module

The draft models live in:

```text
ai-api/app/ai_access_models.py
```

They are Pydantic models intended to be deterministic, offline-testable, and safe to serialize. They are independent from any production database and do not define migrations.

## AI Demo Session

`AiDemoSession` represents a future controlled demo session.

Fields include:

- `session_id`
- `session_type`: `local_operator`, `invite`, or `public_preview`
- `status`: `active`, `expired`, `revoked`, or `completed`
- `created_at`, `expires_at`, `revoked_at`, `last_activity_at`
- `revoked_reason`
- `operator_label`
- `access_grant_id`
- `session_token_fingerprint`
- `allowed_workflows`
- `max_provider_calls`
- `max_estimated_cost_usd`
- `request_count`
- `provider_call_count`
- `estimated_cost_usd`
- `metadata_fingerprint`

The model intentionally excludes user secrets, API keys, raw IP addresses by default, raw provider prompts, raw provider responses, and long-term user memory.

## Access Grant

`AiAccessGrant` represents a future local operator grant, invite-code grant, or admin override.

Fields include:

- `grant_id`
- `grant_type`: `local_operator`, `invite_code`, or `admin_override`
- `status`: `active`, `expired`, `revoked`, or `used`
- `created_at`, `expires_at`, `used_at`, `revoked_at`
- `revoked_reason`
- `max_sessions`
- `max_provider_calls`
- `max_estimated_cost_usd`
- `allowed_workflows`
- `notes`
- `metadata_fingerprint`
- `invite_token_fingerprint`

The model does not store plain invite codes or raw tokens. Future tasks that need token-like identifiers should store only fingerprints or hashes.

## Local Operator Gate

`AiOperatorGateDecision` captures a safe allow/block decision for the local operator gate used by the AI demo workflows.

Fields include:

- `enabled`
- `allowed`
- `workflow`
- `reason`
- `status`: `allowed`, `blocked`, `disabled`, or `misconfigured`
- `grant_type`
- `metadata_fingerprint`
- `safe_message`
- `safe_metadata`

The helper compares fingerprints, not raw tokens, and the safe view omits raw headers, raw tokens, API keys, request bodies, and private paths. The gate is optional, disabled by default, and intended for local/private operator workflows only.

## Provider Meter Event

`AiProviderMeterEvent` represents one provider-metering decision or provider-call outcome.

Fields include:

- `event_id`
- `session_id`
- `workflow`
- `provider`
- `model`
- `input_tokens`, `output_tokens`, `total_tokens`
- `estimated_cost_usd`
- `status`: `allowed`, `skipped`, `blocked`, or `failed`
- `reason`
- `created_at`
- `request_id`
- `safe_metadata`

The model supports mock/offline workflows where cost and token counts may be absent. It does not include raw prompts, raw provider responses, request bodies, API keys, or user secrets.

## Quality Event

`AiQualityEvent` captures future quality, eval, or acceptance evidence without storing raw artifacts.

Fields include:

- `event_id`
- `session_id`
- `workflow`
- `eval_group`
- `case_id`
- `status`: `passed`, `failed`, `warning`, or `skipped`
- `support_level`
- `retrieved_count`
- `citation_count`
- `warning_count`
- `latency_ms`
- `created_at`
- `safe_summary`

This shape can support future operator reports for eval drift, support-level quality, citation coverage, and latency warnings.

## Admin Audit Event

`AiAdminAuditEvent` represents a future metadata-only audit record for operator actions.

Fields include:

- `event_id`
- `actor_label`
- `action`
- `target_type`
- `target_id`
- `created_at`
- `reason`
- `safe_metadata`

Supported action names include:

- `grant_created`
- `grant_revoked`
- `session_revoked`
- `provider_disabled`
- `budget_limit_changed`
- `live_access_enabled`
- `live_access_disabled`

This model does not implement auth, admin permissions, or an admin UI.

## Budget Snapshot

`AiBudgetSnapshot` represents a calculated budget view for a session or grant.

Fields include:

- `session_id`
- `grant_id`
- `provider_call_count`
- `max_provider_calls`
- `estimated_cost_usd`
- `max_estimated_cost_usd`
- `remaining_provider_calls`
- `remaining_estimated_cost_usd`
- `is_exhausted`
- `status_reason`
- `created_at`

Remaining calls and remaining cost are calculated by the model. Exhaustion reasons are deterministic:

- `within_budget`
- `provider_call_limit_exhausted`
- `cost_limit_exhausted`
- `provider_call_and_cost_limits_exhausted`

Budget snapshots are models only. They do not block provider calls at runtime in this task.

## Provider Budget Decision

`AiProviderBudgetDecision` is the safe decision object used by the provider budget guard introduced in `0029E`.

Fields include:

- `allowed`
- `status`: `allowed`, `blocked`, `disabled`, `exhausted`, `misconfigured`, or `skipped`
- `workflow`
- `provider`
- `model`
- `reason`
- `safe_message`
- `provider_call_count`
- `max_provider_calls`
- `estimated_cost_usd`
- `max_estimated_cost_usd`
- `estimated_input_tokens`
- `estimated_output_tokens`
- `max_input_tokens`
- `max_output_tokens`
- `budget_snapshot`
- `meter_event`
- `safe_metadata`

The runtime helper is still local-only and process-local; the schema doc remains non-persistent and non-production.

## Safe Serialization

Each model exposes `safe_view()` for future public/operator response shaping. The module also provides `safe_operator_view()` as a uniform helper.

Safe views may include:

- IDs;
- statuses;
- timestamps;
- workflow names;
- provider and model names;
- counts;
- cost estimates;
- safe metadata;
- fingerprints.

Safe views must not include:

- API keys;
- authorization headers;
- environment values;
- raw invite codes;
- raw tokens;
- raw prompts;
- raw provider responses;
- request bodies;
- stack traces;
- local filesystem paths;
- private storage URLs.

The tests reject known forbidden strings such as provider key names, token prefixes, local temp/demo paths, raw prompt/response labels, and database/cache URLs.

## Future Consumers

Later tasks can use these models for:

- `0029D` local operator access gate;
- `0029E` provider-call budget enforcement;
- `0029F` invite-only demo session flow (implemented as a local/private alpha on top of these models);
- `0029G` admin usage report prototype;
- `0029H` public route exposure review;
- `0029I` paid access integration ADR.

## Non-Goals

This schema scaffold does not implement:

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
- runtime budget enforcement;
- admin dashboard UI.
