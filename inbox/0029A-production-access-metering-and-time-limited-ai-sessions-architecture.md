# Task 0029A: Production Access, Metering, And Time-Limited AI Sessions Architecture

## Goal

Design the production architecture for safely exposing the Cookbook AI demo as a controlled product experience with authentication, metering, time-limited sessions, provider cost controls, and future paid access.

This is an architecture/design task only. Do not implement runtime auth, billing, public AI exposure, payment processing, database migrations, or Cloudflare route changes in this task.

## Context

The AI feature set is now demo-complete and live-eval validated.

Completed recent milestones:

- `0027D`: seeded local demo data and local launch workflow.
- `0027E`: manual live OpenAI demo eval harness.
- `0027F`: live GPT-nano quality baseline and thresholds.
- `0027G`: default GPT-nano cost estimates.
- `0028A`: bounded input-quality and one-question clarification handling.
- `0028B`: live importer quality-check tuning.

Current checkpoint:

```text
Mock UI demo: PASS
Seeded local demo: PASS
Live GPT-nano eval: PASS
Quality gates: PASS
Cost estimate: PASS
Input-quality guardrails: PASS
Importer eval tuning: PASS
Latest live GPT-nano eval: PASS 6/6
```

Latest human live eval after `0028B`:

```text
Expected model: gpt-5.4-nano
Overall passed: True
Workflows passed: 6/6
Total latency ms: 9615
Total tokens: 1467
Estimated cost USD: 0.0007029
Cost sources: default_model_rate, unavailable
Threshold warnings: 0
Threshold failures: 0
Failed checks: None
```

The app currently has AI workflows for:

- recipe importer;
- Ask My Cookbook over saved recipes;
- deterministic dataset search;
- dataset Ask/RAG;
- saved-recipe meal planner;
- demo readiness;
- bounded input-quality handling.

## Problem

The app is not ready to expose live provider-backed AI publicly because there is not yet a production access layer.

Before exposing live OpenAI calls to public users, the project needs a design for:

- who can access the AI features;
- how sessions are started and ended;
- how long a user can use a demo;
- how many provider-backed calls are allowed;
- how cost is budgeted and capped;
- how abuse and accidental spend are prevented;
- how usage can later become paid access;
- how multiple future AI use cases can share infrastructure without sharing data boundaries.

## Product Direction

Design for a controlled product path:

1. Public read-only cookbook site can remain public.
2. AI demo access should be gated.
3. Demo sessions should be time-limited and/or usage-limited.
4. Provider-backed AI calls should be metered.
5. Cost should be estimated and stored per session/user/workflow.
6. The system should support a future paid path but not implement payment yet.
7. Each future demo/use case should own its own data boundary.

Important existing rule:

```text
The platform may share infrastructure, but each demo owns its own data boundary.
```

Do not create a shared vector corpus across unrelated apps/use cases.

## Required Deliverables

Create an architecture package under `docs/` plus an outbox report.

Suggested files:

```text
docs/production-access-metering-architecture.md
docs/ai-production-readiness-roadmap.md
docs/ai-session-metering-data-model.md
docs/ai-access-control-threat-model.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0029A-production-access-metering-and-time-limited-ai-sessions-architecture-results.md
```

You may adjust file names if a better structure already exists.

## Architecture Topics To Cover

### 1. Access Modes

Define at least these modes:

- local/offline developer mode;
- private operator demo mode;
- invite-only demo mode;
- future paid access mode;
- admin/operator mode.

For each mode, specify:

- who can access it;
- whether OpenAI calls are allowed;
- session limit behavior;
- provider budget behavior;
- data persistence behavior;
- logging/metrics behavior.

### 2. Session Model

Design a session model for time-limited AI access.

Cover fields such as:

```text
session_id
user_id or anonymous_demo_id
access_mode
started_at
expires_at
status
max_duration_seconds
max_provider_calls
max_input_tokens
max_output_tokens
max_estimated_cost_usd
provider_calls_used
input_tokens_used
output_tokens_used
estimated_cost_usd
created_ip_hash or coarse abuse marker
user_agent_hash or coarse abuse marker
revoked_reason
```

Do not store raw API keys.
Do not store sensitive prompt data by default.
Do not store full recipe/private user text unless explicitly needed and documented.

### 3. Metering Model

Design per-call metering.

Cover fields such as:

```text
meter_event_id
session_id
workflow
provider
model
input_quality_status
provider_called
input_tokens
output_tokens
total_tokens
estimated_cost_usd
cost_source
latency_ms
passed_quality_checks
threshold_warning_count
threshold_failure_count
created_at
```

Explain how this builds on the existing live eval metrics.

### 4. Budget And Limit Enforcement

Define enforcement order:

1. validate session;
2. validate access mode;
3. run deterministic input-quality checks;
4. reject bad input before provider calls;
5. check session/provider budget before provider call;
6. execute provider call only if allowed;
7. record usage;
8. return response with safe metadata.

Cover hard caps:

- max provider calls per session;
- max estimated cost per session;
- max tokens per call;
- max total tokens per session;
- max session duration;
- rate limit by user/session/IP hash;
- disable live provider globally with an environment switch.

### 5. Authentication And Authorization Options

Compare reasonable options but do not implement them:

- simple shared demo invite code;
- magic link email login;
- OAuth/OIDC such as Google/GitHub;
- Cloudflare Access in front of the AI demo;
- future paid account integration.

Recommend an incremental path.

Likely recommendation:

```text
Phase 1: private operator mode only
Phase 2: invite-only demo sessions
Phase 3: authenticated accounts
Phase 4: paid access integration
```

### 6. Future Paid Access

Design how paid access could work later without building it now.

Cover:

- entitlement table;
- subscription or credit balance;
- trial/demo credits;
- payment provider integration boundary;
- webhook verification;
- refund/chargeback considerations;
- internal admin override;
- audit trail.

Do not choose or integrate a payment provider in this task.

### 7. Data Boundaries For Multiple Future Use Cases

The user wants future apps/use cases beyond the cookbook demo.

Design a shared platform pattern:

```text
shared access/session/metering infrastructure
separate app namespaces
separate data stores or schemas
separate retrieval indexes
separate prompt/eval suites
separate cost budgets when needed
```

Explicitly preserve the rule:

```text
The platform may share infrastructure, but each demo owns its own data boundary.
```

Examples of future use cases may include:

- cookbook AI;
- stock or market analysis demo;
- operations-order / doctrine assistant demo;
- other portfolio AI demos.

Do not implement these future apps.

### 8. Deployment Exposure Controls

Design how live provider-backed routes should be exposed safely.

Cover:

- keeping `/demo` public vs protected;
- keeping `/ai/*` and provider-backed endpoints protected;
- Cloudflare Tunnel routing considerations;
- reverse proxy rules;
- environment variable kill switches;
- CORS origin restrictions;
- local-only sidecar access;
- no public unauthenticated live OpenAI endpoint.

### 9. Admin/Operator View

Design what the future admin/operator dashboard should show:

- active sessions;
- recent provider calls;
- estimated spend;
- failed checks;
- rejected inputs;
- threshold warnings/failures;
- kill switch state;
- access mode state;
- top workflows by cost/latency;
- exportable audit/report view.

Do not implement the dashboard yet.

### 10. Threat Model

Document threats and mitigations:

- unauthenticated public spend;
- prompt spam;
- scraping/API abuse;
- bypassing UI and calling API directly;
- leaked provider keys;
- session replay;
- excessive input size;
- toxic/unsafe content;
- cross-demo data leakage;
- private recipe/data leakage;
- logging too much sensitive prompt data;
- payment/webhook abuse in future paid mode.

### 11. Open Questions / ADR Decisions

Create a clear ADR-style decision section.

Include decisions such as:

- access layer must exist before public live AI exposure;
- session metering is required before paid access;
- deterministic input-quality checks stay before provider calls;
- live provider globally disabled by default outside explicit modes;
- data boundaries are per demo/use case;
- raw prompt logging is off by default;
- payment integration is deferred.

## Suggested Architecture Output Shape

The main architecture doc should include:

```text
# Production Access, Metering, And Time-Limited AI Sessions Architecture

## Status
Proposed

## Scope

## Current State

## Target State

## Access Modes

## Session Lifecycle

## Metering Data Model

## Request Enforcement Flow

## Budget And Limit Enforcement

## Authentication Options

## Future Paid Access Boundary

## Multi-Use-Case Data Boundary Pattern

## Deployment Exposure Controls

## Admin/Operator View

## Threat Model

## ADR Decisions

## Implementation Phases

## Non-Goals

## Open Questions
```

## Implementation Roadmap

Create a follow-on roadmap with small tasks after `0029A`.

Recommended future tasks:

```text
0029B: Session And Metering Schema Draft
0029C: Local Operator Access Gate
0029D: Provider Call Budget Enforcement
0029E: Invite-Only Demo Session Flow
0029F: Admin Usage Report Prototype
0029G: Public Route Exposure Review
0029H: Paid Access Integration ADR
```

Do not implement those tasks now.

## Tests

This is mostly docs/architecture, but add lightweight repo checks if the project has doc link validation or Markdown checks.

If you add examples or schema snippets, keep them static and safe.

No live OpenAI calls.
No database migrations.
No code changes unless needed for documentation references.

## Validation

Run normal validation that is reasonable for a docs/architecture task:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke and live eval wrappers should skip cleanly unless live opt-in settings are present.

If docs-only changes cause validation to take longer than needed, still run the repo validation script and record results.

Do not run live OpenAI calls during normal validation.

## Outbox Report

Create:

```text
outbox/0029A-production-access-metering-and-time-limited-ai-sessions-architecture-results.md
```

Include:

- Summary
- Files changed
- Architecture decisions
- Access modes covered
- Session model covered
- Metering model covered
- Budget enforcement approach
- Authentication options compared
- Paid access boundary
- Multi-use-case data boundary rule
- Threat model summary
- Recommended next task
- Validation results
- Whether live OpenAI was run or skipped
- Confirmation that no private env files, API keys, raw datasets, generated live results, screenshots, logs, credentials, payment secrets, or `.tmp-ai-demo/` artifacts were committed

## Commit

Commit and push:

```bash
git add docs README.md outbox/0029A-production-access-metering-and-time-limited-ai-sessions-architecture-results.md

git commit -m "mailbox: complete task 0029A production access metering architecture"

git push origin main
```

## Done Criteria

- Architecture docs exist for production access, metering, and time-limited AI sessions.
- Access modes are defined.
- Session and per-call metering data models are documented.
- Budget enforcement flow is documented.
- Authentication options are compared with an incremental recommendation.
- Future paid access is bounded but not implemented.
- Multi-use-case data boundary pattern is documented.
- Deployment exposure controls explicitly prohibit unauthenticated public live AI endpoints.
- Threat model exists.
- Follow-on tasks are listed.
- Normal validation remains offline.
- No runtime auth, billing, public live route exposure, payment integration, migrations, secrets, env files, raw datasets, generated artifacts, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts are committed.
