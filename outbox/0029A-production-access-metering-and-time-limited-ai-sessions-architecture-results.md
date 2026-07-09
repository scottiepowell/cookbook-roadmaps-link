# 0029A: Production Access, Metering, And Time-Limited AI Sessions Architecture Results

Status: complete.

## Summary

Created the production access, metering, session, and threat-model architecture package for safely exposing the Cookbook AI demo as a controlled product experience later. This was documentation-only; no runtime auth, billing, payment processing, database migrations, public live AI exposure, Cloudflare route changes, or production storage changes were implemented.

## Files Changed

- `docs/production-access-metering-architecture.md`
- `docs/ai-production-readiness-roadmap.md`
- `docs/ai-session-metering-data-model.md`
- `docs/ai-access-control-threat-model.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029A-production-access-metering-and-time-limited-ai-sessions-architecture-results.md`

## Architecture Decisions

- Access layer must exist before public live AI exposure.
- Session metering is required before paid access.
- Deterministic input-quality checks stay before provider calls.
- Live provider must be globally disable-able.
- Data boundaries are per demo/use case.
- Raw prompt logging is off by default.
- Payment integration is deferred to a later ADR.
- Admin overrides must be auditable.

## Access Modes Covered

- Local/offline developer mode.
- Private operator demo mode.
- Invite-only demo mode.
- Future paid access mode.
- Admin/operator mode.

## Session Model Covered

Documented the proposed `ai_demo_sessions` fields, including session id, user or anonymous demo id, app namespace, access mode, start/expiry timestamps, status, duration cap, provider-call cap, token caps, estimated-cost cap, usage counters, coarse abuse markers, and revocation reason.

## Metering Model Covered

Documented the proposed `ai_meter_events` fields, including workflow, provider, model, input-quality status, provider-called flag, token usage, estimated cost, cost source, latency, quality checks, threshold warnings/failures, denial reason, and timestamp.

## Budget Enforcement Approach

Documented enforcement order:

1. Validate session.
2. Validate access mode.
3. Run deterministic input-quality checks.
4. Reject bad input before provider calls.
5. Check session and provider budget before provider call.
6. Execute provider call only if allowed.
7. Record usage.
8. Return response with safe metadata.

Hard caps cover provider calls, estimated cost, per-call tokens, total session tokens, session duration, coarse rate limits, and a global provider kill switch.

## Authentication Options Compared

Compared shared invite codes, magic links, OAuth/OIDC, Cloudflare Access, and future paid account integration. Recommended incremental path:

- Phase 1: private operator mode only.
- Phase 2: invite-only demo sessions.
- Phase 3: authenticated accounts.
- Phase 4: paid access integration.

## Paid Access Boundary

Defined paid access as a future entitlement layer with subscription or credit concepts, trial/demo credits, provider budget per period, webhook verification, refund/chargeback considerations, internal admin overrides, and audit trail. No payment provider was selected or integrated.

## Multi-Use-Case Data Boundary Rule

Preserved the rule: the platform may share infrastructure, but each demo owns its own data boundary. Shared access/session/metering infrastructure is allowed, while each demo keeps separate namespaces, data stores or schemas, retrieval indexes, prompt/eval suites, budgets, and retention rules.

## Threat Model Summary

Documented threats and mitigations for unauthenticated spend, prompt spam, direct API abuse, leaked provider keys, session replay, excessive input size, unsafe content, cross-demo data leakage, private data leakage, sensitive prompt logging, budget races, kill-switch bypass, admin misuse, and future payment/webhook abuse.

## Recommended Next Task

`0029B`: Manual End-User Recipe Entry Acceptance.

Production-readiness implementation tasks should continue with:

- `0029C`: Session And Metering Schema Draft
- `0029D`: Local Operator Access Gate
- `0029E`: Provider Call Budget Enforcement
- `0029F`: Invite-Only Demo Session Flow
- `0029G`: Admin Usage Report Prototype
- `0029H`: Public Route Exposure Review
- `0029I`: Paid Access Integration ADR

## Validation Results

- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed; includes shell syntax, Docker Compose configuration, 112 AI API tests, 17 offline eval cases, whitespace, local Markdown links, old-domain guard, and secret-pattern scan.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live eval opt-in settings were not present.

## Live OpenAI

No live OpenAI calls were run for this task. The live smoke and live eval wrappers are expected to skip unless explicit live opt-in settings are present.

## Artifact Safety

No private env files, API keys, raw datasets, generated live results, screenshots, logs, credentials, payment secrets, or `.tmp-ai-demo/` artifacts were committed.
