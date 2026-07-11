# Production Access, Metering, And Time-Limited AI Sessions Architecture

## Status

Proposed.

This is a design document only. It does not implement runtime authentication, billing, payment processing, database migrations, Cloudflare routing, public live AI exposure, or production storage changes.

## Scope

Design the control plane needed before the Cookbook AI demo can safely expose provider-backed AI to users outside a trusted local/operator context.

The architecture covers:

- access modes;
- time-limited AI sessions;
- per-call metering;
- budget and provider-call enforcement;
- authentication and authorization options;
- future paid access boundaries;
- multi-use-case data isolation;
- deployment exposure controls;
- admin/operator reporting;
- threat model and ADR decisions.

## Current State

The AI cookbook feature set is demo-complete and validated through offline tests, mock demo checks, manual live smoke, and manual live GPT-nano evals. Current live OpenAI use remains manual-only and requires explicit local opt-in. Normal validation is offline and mock-only.

Current workflows:

- structured recipe importer;
- Ask My Cookbook over saved recipes;
- deterministic dataset search;
- dataset Ask/RAG;
- saved-recipe meal planning;
- demo readiness;
- deterministic input-quality handling.

The latest recorded post-`0028B` live GPT-nano eval passed 6/6 workflows with 0 threshold warnings and 0 threshold failures.

## Target State

The target production architecture allows a controlled AI demo experience while preventing unbounded public spend and cross-demo data leakage.

Required properties:

- no public unauthenticated live OpenAI endpoint;
- deterministic input-quality checks always run before provider calls;
- live provider calls can be globally disabled;
- every provider-backed request is tied to a valid access mode and session;
- session duration, provider call count, tokens, and estimated cost are capped;
- raw prompt logging is off by default;
- payment integration is deferred behind a later ADR;
- shared platform infrastructure is allowed, but each demo owns its own data boundary.

## Access Modes

| Mode | Who Can Access | OpenAI Calls | Session Limits | Provider Budget | Data Persistence | Logging And Metrics |
| --- | --- | --- | --- | --- | --- | --- |
| Local/offline developer | Developer on local machine | No by default; mock provider unless explicit live opt-in is set | None required for mock; optional short live test session | Live wrapper budget only when explicitly enabled | Generated fixtures and local ignored artifacts only | Safe workflow logs; no raw prompt logging by default |
| Private operator demo | Trusted operator running a controlled demo | Allowed only with operator opt-in and global provider enabled | Short operator-defined session window | Strict per-session and per-run caps | Session and meter summaries only | Provider call metadata, cost estimate, warnings, failures |
| Invite-only demo | Invited external user or reviewer | Allowed only after invite/session validation | Time-limited and usage-limited | Per-session caps for calls, tokens, and estimated cost | Durable session and meter records; no raw prompt storage by default | Audit-friendly metadata and aggregate usage |
| Future paid access | Authenticated user with valid entitlement | Allowed within entitlement and platform kill switches | Entitlement-defined limits plus abuse controls | Subscription, credit, or trial budget | Durable account, entitlement, session, and meter records | Metering, audit events, charge reconciliation summaries |
| Admin/operator | Maintainer or support operator | Indirect only; may inspect and revoke sessions | N/A | Can view budgets and kill switches; cannot bypass without explicit override audit | Admin actions and audit logs | Dashboard metrics, exports, revocation reasons |

## Session Lifecycle

1. Access request arrives at the protected AI demo entry point.
2. The access layer validates the mode: operator, invite, authenticated account, or future paid entitlement.
3. The platform creates or resumes a session with explicit limits.
4. Each AI workflow request validates the session before doing workflow work.
5. Deterministic input-quality checks run before retrieval or provider calls where applicable.
6. Rejected or clarification responses return without a provider call and still record safe meter metadata.
7. Provider calls proceed only when the session, access mode, global live-provider switch, and budget checks all pass.
8. Usage is recorded after the call using provider usage fields when available and estimates when configured.
9. Sessions end by expiry, budget exhaustion, manual revocation, user logout, invite revocation, or global provider disable.

Session states:

- `active`: request may proceed if all budget checks pass;
- `expired`: max duration reached;
- `exhausted`: call, token, or cost cap reached;
- `revoked`: admin/operator revoked access;
- `disabled`: global provider or access mode disabled;
- `closed`: user or operator ended the session.

## Metering Data Model

The session and per-call models are specified in [AI Session Metering Data Model](ai-session-metering-data-model.md). At a high level:

- `ai_demo_sessions` records who or what can use provider-backed workflows, for how long, and under what caps.
- `ai_meter_events` records each attempted workflow call, whether a provider was called, usage, cost estimate, latency, quality checks, and threshold results.
- `ai_access_grants` records invite codes, account grants, operator grants, or future paid entitlements.
- `ai_admin_audit_events` records revocations, kill-switch changes, overrides, exports, and support actions.

The meter event model builds on existing live eval metrics: workflow, provider, model, input-quality status, provider-called status, token usage, estimated cost, cost source, latency, quality checks, threshold warnings, and threshold failures.

## Request Enforcement Flow

Enforcement order:

1. Validate session.
2. Validate access mode.
3. Run deterministic input-quality checks.
4. Reject bad input before provider calls.
5. Check session and provider budget before provider call.
6. Execute provider call only if allowed.
7. Record usage.
8. Return response with safe metadata.

This order is deliberate: rejected or clarification paths should not spend provider budget, and budget checks should happen immediately before provider calls so concurrent usage cannot overspend without detection.

## Budget And Limit Enforcement

Hard caps:

- max provider calls per session;
- max estimated cost per session;
- max input tokens per call;
- max output tokens per call;
- max total tokens per session;
- max session duration;
- rate limit by user, session, and coarse IP/user-agent abuse markers;
- global provider kill switch.

Recommended environment-level controls:

- `AI_LIVE_PROVIDER_ENABLED=false` by default outside controlled live modes;
- `AI_ACCESS_MODE=local|operator|invite|paid|disabled`;
- `AI_MAX_SESSION_SECONDS`;
- `AI_MAX_PROVIDER_CALLS_PER_SESSION`;
- `AI_MAX_SESSION_ESTIMATED_COST_USD`;
- `AI_MAX_INPUT_TOKENS_PER_CALL`;
- `AI_MAX_OUTPUT_TOKENS_PER_CALL`;
- `AI_RAW_PROMPT_LOGGING=false`.

The exact variable names can change during implementation, but the controls should remain distinct: access mode, provider availability, session limits, per-call token limits, and logging policy.

Budget checks should be conservative. If usage or pricing is unavailable, the request should use configured worst-case estimates or fail closed for public/invite/paid modes.

## Authentication Options

| Option | Strengths | Weaknesses | Best Fit |
| --- | --- | --- | --- |
| Shared demo invite code | Fast to implement, easy for portfolio reviewers | Weak identity, shareable, limited audit value | Short-lived private demos only |
| Magic link email login | Low-friction identity, revocable invites | Requires email service and deliverability handling | Invite-only sessions |
| OAuth/OIDC with Google or GitHub | Stronger identity, familiar login, better audit | Provider setup and callback security required | Authenticated reviewer or account mode |
| Cloudflare Access | Strong perimeter in front of demo routes, quick operator gating | Less app-level entitlement detail unless headers are mapped | Private operator mode and early invite gates |
| Future paid account integration | Ties usage to entitlement and billing | Requires payment, webhook, refund, and support processes | Later paid product mode |

Recommended path:

1. Phase 1: private operator mode only.
2. Phase 2: invite-only demo sessions.
3. Phase 3: authenticated accounts.
4. Phase 4: paid access integration.

## Future Paid Access Boundary

Paid access should be designed as an entitlement layer, not as direct payment checks inside workflow handlers.

Future paid concepts:

- `entitlement_id`;
- account or user id;
- product or plan id;
- subscription status or credit balance;
- trial/demo credits;
- current billing period;
- provider budget per period;
- admin override status;
- audit timestamps.

Payment provider integration remains out of scope. A future paid-access ADR should choose the provider and define webhook verification, replay protection, refund handling, chargeback handling, tax/accounting exports, support overrides, and audit retention.

Workflow handlers should only ask the access layer whether the session is allowed and how much budget remains. They should not call payment APIs directly.

## Multi-Use-Case Data Boundary Pattern

The platform may share infrastructure, but each demo owns its own data boundary.

Shared platform layer:

- identity and access control;
- session lifecycle;
- metering events;
- admin dashboard shell;
- provider kill switches;
- deployment routing controls;
- aggregate reporting.

Per-demo boundary:

- app namespace;
- source data store or schema;
- retrieval index or collection;
- prompt suite;
- eval suite;
- workflow-specific budget policy;
- data retention policy;
- export/delete process;
- operator runbooks.

Examples of future demos, without implementing them here:

- cookbook AI;
- stock or market analysis demo;
- operations-order or doctrine assistant demo;
- other portfolio AI demos.

Cookbook AI data must not be mixed into a stock, operations, or unrelated assistant retrieval corpus. A shared vector database could be acceptable later only if it uses separate collections, credentials, indexes, retention rules, and eval suites per demo.

## Deployment Exposure Controls

Deployment rules before public live provider exposure:

- `/demo` may remain public only when it is mock/offline or explicitly non-provider-backed.
- Provider-backed `/ai/*` and provider-backed dataset endpoints must be protected by the access layer.
- Reverse proxy or Cloudflare Tunnel routing must not expose unauthenticated live AI endpoints.
- CORS should allow only intended origins.
- The AI sidecar should prefer local-only binding behind the app/proxy boundary.
- The global live-provider switch must be able to stop all provider calls without redeploying code.
- Provider keys remain server-side only and must never be exposed to browsers.
- Public routes should return safe denial states when access mode or provider mode is disabled.

Cloudflare Access can be used as an early perimeter control, but app-level sessions and metering are still required before invite-only or paid use.

## Admin/Operator View

A future admin view should show:

- active sessions;
- session expiry and remaining provider-call budget;
- recent provider calls;
- estimated spend by session, user, workflow, and model;
- failed quality checks;
- rejected inputs and clarification counts;
- threshold warnings and failures;
- global kill-switch state;
- current access mode;
- top workflows by cost and latency;
- revoked sessions and reasons;
- exportable audit/report view.

Admin actions should be auditable. Operators should be able to revoke sessions, disable access modes, disable live provider calls, and export summary usage without exposing raw prompts by default.

## Threat Model

The threat model is detailed in [AI Access Control Threat Model](ai-access-control-threat-model.md). Primary risks:

- unauthenticated public spend;
- prompt spam and API abuse;
- bypassing the UI and calling APIs directly;
- leaked provider keys;
- session replay;
- excessive input size;
- toxic or unsafe content;
- cross-demo data leakage;
- private recipe/data leakage;
- sensitive prompt logging;
- future payment/webhook abuse.

## ADR Decisions

| Decision | Status | Rationale |
| --- | --- | --- |
| Access layer must exist before public live AI exposure | Accepted | Prevents unauthenticated spend and direct endpoint abuse. |
| Session metering is required before paid access | Accepted | Paid access needs auditable usage, budgets, and entitlement enforcement. |
| Deterministic input-quality checks stay before provider calls | Accepted | Bad inputs should be rejected or clarified without spending provider budget. |
| Live provider is globally disabled by default outside explicit modes | Accepted | A kill switch limits accidental spend and public exposure risk. |
| Data boundaries are per demo/use case | Accepted | Prevents cross-demo retrieval, privacy, provenance, and eval contamination. |
| Raw prompt logging is off by default | Accepted | Reduces sensitive data retention and support risk. |
| Payment integration is deferred | Accepted | Billing requires a separate provider, webhook, audit, and support design. |
| Admin overrides require audit events | Proposed | Overrides are useful operationally but must be traceable. |

## Implementation Phases

The follow-on roadmap is documented in [AI Production Readiness Roadmap](ai-production-readiness-roadmap.md).

Planned numbering:

- `0029B`: Manual End-User Recipe Entry Acceptance
- `0029C`: Session And Metering Schema Draft
- `0029D`: Local Operator Access Gate
- `0029E`: Provider Call Budget Enforcement
- `0029F`: Invite-Only Demo Session Flow
- `0029G`: Admin Usage Report Prototype
- `0029H`: Public Route Exposure Review
- `0029I`: Monetization And Entitlement Boundary ADR

## Non-Goals

This architecture task does not implement:

- runtime authentication;
- billing;
- payment processing;
- public live AI exposure;
- database migrations;
- Cloudflare route changes;
- production storage;
- new provider prompts;
- new workflow behavior;
- browser automation;
- live OpenAI calls in validation.

## Open Questions

- Which identity provider is preferred after private operator mode?
- Should early invite-only sessions rely on app-native magic links, Cloudflare Access, or both?
- What is the smallest durable store acceptable for session and meter records?
- What retention period is appropriate for meter events and admin audit events?
- Should public `/demo` remain visible in mock-only mode while provider routes are protected?
- What budget caps should be used for public invite sessions?
- What support process is required before paid access?
