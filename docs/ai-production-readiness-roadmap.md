# AI Production Readiness Roadmap

This roadmap breaks production access, metering, and paid-access readiness into small follow-on tasks. It is design-only and does not implement runtime auth, billing, migrations, public live AI exposure, payment processing, or Cloudflare route changes.

## Current Checkpoint

| Area | Status | Evidence |
| --- | --- | --- |
| Mock UI demo | Pass | `scripts/demo-ai-mock.ps1` |
| Seeded local demo | Pass | generated fixtures and `/demo` readiness |
| Live GPT-nano eval | Pass | post-`0028B` 6/6 run |
| Quality gates | Pass | live eval threshold warnings/failures were 0/0 |
| Cost estimate | Pass | `default_model_rate` cost populated |
| Input-quality guardrails | Pass | `0028A` offline tests |
| Importer eval tuning | Pass | `0028B` checks plus post-fix live pass |

## Follow-On Task Numbering

`0029B` is reserved for manual recipe-entry acceptance. Production-readiness implementation tasks resume at `0029C`.

| Task | Title | Goal |
| --- | --- | --- |
| `0029B` | Manual End-User Recipe Entry Acceptance | Validate the manual end-user recipe-entry path before production gating work. |
| `0029C` | Session And Metering Schema Draft | Draft schemas and tests for sessions, grants, meter events, and admin audit events without enabling public live AI. |
| `0029D` | Local Operator Access Gate | Add a local/private operator gate that can protect AI demo routes in controlled environments. |
| `0029E` | Provider Call Budget Enforcement | Centralize provider-call budget checks for call count, token caps, estimated cost, and global provider disable. |
| `0029F` | Invite-Only Demo Session Flow | Add short-lived invite sessions with expiry, revocation, and per-session budgets. |
| `0029G` | Admin Usage Report Prototype | Build an operator report for sessions, provider calls, estimated spend, warnings, failures, and revocations. |
| `0029H` | Public Route Exposure Review | Review Cloudflare, reverse proxy, CORS, and route exposure before any public live AI access. |
| `0029I` | Paid Access Integration ADR | Choose and bound the future payment/entitlement integration without implementing payment in earlier tasks. |

## Phase 1: Private Operator Mode

Objectives:

- Keep public site behavior unchanged.
- Add an operator-only gate before live provider-backed workflows.
- Keep global provider disable available.
- Keep normal validation offline.

Acceptance:

- no unauthenticated public live OpenAI endpoint;
- operator can enable a controlled local/private demo session;
- provider calls still require explicit live configuration;
- input-quality rejection and clarification still happen before provider calls.

## Phase 2: Session And Budget Enforcement

Objectives:

- Add durable or implementation-ready session records.
- Add per-call meter events.
- Enforce provider-call, token, cost, and duration limits.
- Record denial reasons when provider calls are blocked.

Acceptance:

- expired, revoked, exhausted, or disabled sessions fail closed;
- rejected inputs do not consume provider budget;
- provider calls are recorded with model, workflow, usage, cost estimate, and latency;
- concurrent usage cannot exceed caps without detection and reconciliation.

## Phase 3: Invite-Only Demo Sessions

Objectives:

- Support short-lived invite grants.
- Allow reviewer access without broad public exposure.
- Store only hashed invite tokens.
- Allow operator revocation.

Acceptance:

- invite sessions are time-limited and usage-limited;
- direct API calls without a valid session fail;
- operator can revoke grants and sessions;
- logs remain metadata-only by default.

## Phase 4: Admin Usage Reporting

Objectives:

- Give operators a safe view of active sessions and recent provider calls.
- Surface spend, latency, warnings, failures, and rejections.
- Export summary usage without raw prompts by default.

Acceptance:

- admin actions are audited;
- reports can answer what was spent, by which workflow, under which access mode;
- kill-switch state and access mode state are visible.

## Phase 5: Public Exposure Review

Objectives:

- Verify public routing and protection before any live provider-backed exposure.
- Confirm CORS, reverse proxy, Cloudflare Tunnel, and local sidecar boundaries.
- Validate that `/demo` public access cannot reach provider-backed routes without a session.

Acceptance:

- no public unauthenticated live AI endpoint;
- route protections are tested directly, not only through UI behavior;
- provider key remains server-side;
- rollback and kill-switch procedures are documented.

## Phase 6: Paid Access ADR

Objectives:

- Decide how paid entitlement will be represented.
- Choose whether subscription, credit balance, trial credits, or a hybrid model fits.
- Define payment provider integration boundaries.

Acceptance:

- payment provider is selected or explicitly deferred again;
- webhook verification and replay protection are specified;
- refund, chargeback, admin override, and audit requirements are documented;
- workflow handlers remain isolated from payment-provider APIs.

## Non-Goals

- Payment processing.
- Public live AI exposure.
- Database migrations in this architecture task.
- Cross-demo shared retrieval corpus.
- Raw prompt logging by default.
- Live OpenAI calls in normal validation.
