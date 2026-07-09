# AI Session Metering Data Model

## Status

Proposed design only. No database migrations or production storage changes are implemented by this document.

## Goals

- Tie every provider-backed AI request to an access mode and session.
- Enforce duration, call count, token, and estimated-cost limits.
- Preserve enough usage data for operator review and future paid access.
- Avoid storing raw API keys, raw prompts, private recipe text, or sensitive provider payloads by default.

## Session Record

Suggested table or collection: `ai_demo_sessions`.

| Field | Purpose | Notes |
| --- | --- | --- |
| `session_id` | Stable unique session id | Opaque random id; not guessable. |
| `user_id` | Authenticated account id | Nullable for anonymous invite sessions. |
| `anonymous_demo_id` | Invite or anonymous reviewer id | Opaque id; do not store raw invite code. |
| `app_namespace` | Demo/use-case namespace | Example: `cookbook_ai`. |
| `access_mode` | `local`, `operator`, `invite`, `paid`, `admin`, `disabled` | Determines policy. |
| `started_at` | Session start timestamp | UTC. |
| `expires_at` | Session expiry timestamp | Enforces time-limited demo access. |
| `status` | `active`, `expired`, `exhausted`, `revoked`, `disabled`, `closed` | Fail closed when not `active`. |
| `max_duration_seconds` | Session time cap | Used to compute or verify `expires_at`. |
| `max_provider_calls` | Provider-call cap | Counts provider calls, not rejected offline responses. |
| `max_input_tokens` | Total input-token cap | Session aggregate. |
| `max_output_tokens` | Total output-token cap | Session aggregate. |
| `max_estimated_cost_usd` | Estimated-cost cap | Stored as decimal. |
| `provider_calls_used` | Provider-call count used | Increment after provider call attempt is recorded. |
| `input_tokens_used` | Aggregate input tokens | Provider usage or conservative estimate. |
| `output_tokens_used` | Aggregate output tokens | Provider usage or conservative estimate. |
| `estimated_cost_usd` | Aggregate estimated cost | Uses env override, default model rate, or conservative fallback. |
| `created_ip_hash` | Coarse abuse marker | Salted/rotating hash; not raw IP. |
| `user_agent_hash` | Coarse abuse marker | Salted/rotating hash; not full user agent. |
| `revoked_reason` | Operator revocation reason | Nullable. |
| `created_at` | Record creation timestamp | UTC. |
| `updated_at` | Last update timestamp | UTC. |

Do not store:

- raw provider API keys;
- browser-visible provider secrets;
- raw prompt text by default;
- full private recipe text unless a future task explicitly documents need, retention, and access controls;
- payment secrets or webhook secrets.

## Meter Event Record

Suggested table or collection: `ai_meter_events`.

| Field | Purpose | Notes |
| --- | --- | --- |
| `meter_event_id` | Stable unique event id | Opaque random id. |
| `session_id` | Owning AI session | Required. |
| `app_namespace` | Demo/use-case namespace | Required for cross-demo separation. |
| `workflow` | AI workflow name | Examples: `importer`, `ask_my_cookbook`, `dataset_ask`, `meal_plan`. |
| `provider` | Provider name | Example: `openai`, `mock`, `none`. |
| `model` | Model name | Nullable when no provider call occurs. |
| `input_quality_status` | Deterministic input-quality result | `ready`, `weak_but_usable`, `needs_clarification`, `rejected`. |
| `provider_called` | Whether provider call happened | False for rejected/clarification/offline paths. |
| `input_tokens` | Provider input tokens | Nullable if unavailable. |
| `output_tokens` | Provider output tokens | Nullable if unavailable. |
| `total_tokens` | Total tokens | Provider value or sum. |
| `estimated_cost_usd` | Estimated event cost | Decimal, nullable only in local/mock contexts. |
| `cost_source` | Cost estimate source | `env_override`, `default_model_rate`, `conservative_fallback`, `unavailable`. |
| `latency_ms` | Workflow latency | End-to-end workflow timing. |
| `passed_quality_checks` | Deterministic quality checks passed | Boolean or count depending on implementation. |
| `threshold_warning_count` | Threshold warnings | Numeric. |
| `threshold_failure_count` | Threshold failures | Numeric. |
| `denial_reason` | Why provider call was blocked | Nullable; examples: `session_expired`, `budget_exhausted`, `input_rejected`. |
| `created_at` | Event timestamp | UTC. |

This model intentionally mirrors the live eval summary fields so live validation evidence and production metering remain comparable.

## Access Grant Record

Suggested table or collection: `ai_access_grants`.

| Field | Purpose | Notes |
| --- | --- | --- |
| `grant_id` | Stable grant id | Opaque random id. |
| `app_namespace` | Demo namespace | Keeps grants scoped to one demo unless explicitly shared. |
| `user_id` | Authenticated user id | Nullable for invite-only mode. |
| `grant_type` | `operator`, `invite`, `account`, `paid_entitlement`, `admin_override` | Defines source of access. |
| `status` | `active`, `used`, `expired`, `revoked` | Fail closed when not active. |
| `starts_at` | Grant start | UTC. |
| `expires_at` | Grant expiry | UTC. |
| `max_sessions` | Session creation cap | Useful for invite links. |
| `sessions_used` | Sessions already created | Numeric. |
| `policy_ref` | Reference to limit policy | Avoids duplicating policy details. |
| `created_by` | Operator/admin creator | Nullable for system-created paid entitlement. |
| `created_at` | Creation timestamp | UTC. |
| `revoked_reason` | Revocation reason | Nullable. |

Do not store raw invite codes. Store a hash of the invite token and show the token only once at creation time.

## Admin Audit Event Record

Suggested table or collection: `ai_admin_audit_events`.

| Field | Purpose |
| --- | --- |
| `audit_event_id` | Stable event id |
| `actor_user_id` | Admin/operator actor |
| `action` | Example: `revoke_session`, `disable_provider`, `export_usage`, `override_budget` |
| `target_type` | Session, grant, user, access mode, provider switch |
| `target_id` | Target id |
| `app_namespace` | Demo namespace |
| `reason` | Human-readable reason |
| `created_at` | UTC timestamp |

## Privacy And Retention

- Store summaries and metadata by default, not raw prompts.
- Hash coarse abuse markers with a rotating salt where practical.
- Keep session and meter events long enough for abuse review and cost reconciliation.
- Keep future paid audit records long enough to satisfy payment dispute and support needs.
- Define per-demo deletion/export rules before storing private user content.

## Budget Accounting Notes

Budget calculations should be conservative:

- count a provider call as used once a provider request is attempted;
- use provider-reported token usage when available;
- use configured worst-case estimates when provider usage is missing in public/invite/paid modes;
- fail closed when pricing is unavailable and no conservative fallback is configured;
- aggregate session totals transactionally before allowing more provider calls.
