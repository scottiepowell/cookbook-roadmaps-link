# AI Invite-Only Demo Session Flow

This document describes the local/private invite-only demo session layer that now sits above the schema scaffold from `0029C`, the operator gate from `0029D`, and the provider budget guard from `0029E`.

It is a demo control surface, not production auth. The flow is process-local, disabled by default, and intended for offline/mock validation or tightly controlled local operator use.

## Purpose

Invite-only demo sessions let a local operator create a short-lived grant, redeem it into a short-lived demo session, and then exercise protected AI workflows without exposing public access, user accounts, billing, or durable storage.

The main use case is local acceptance and review:

1. create a grant;
2. redeem it into a demo session;
3. call protected workflows with the session token;
4. inspect safe status and budget metadata;
5. revoke or expire the grant/session when done.

## Relationship To The Existing Layers

- `0029C` defines safe models for demo sessions, access grants, meter events, quality events, audit events, and budget snapshots.
- `0029D` adds the local operator gate. When it is enabled, grant/session creation and revocation can be protected by the same operator token flow.
- `0029E` adds provider-call budget enforcement. Invite demo sessions reuse that guard so a demo session can carry its own workflow and cost limits.
- `0029G` adds a local/operator usage report that can safely summarize invite grants, sessions, meter events, budget snapshots, and threshold warnings from the same process-local state.
- `0029H` keeps the invite surface under review and recommends that invite redemption, invite grants, and recipe-session routes stay private until a future exposure task explicitly stages them.

Invite-only demo sessions do not replace the operator gate. They are a separate local/private access path that can be used when the operator wants short-lived, workflow-limited demo access.

## Configuration

Suggested settings:

- `AI_INVITE_SESSIONS_ENABLED=false`
- `AI_INVITE_SESSION_TTL_SECONDS=1800`
- `AI_INVITE_GRANT_TTL_SECONDS=3600`
- `AI_INVITE_MAX_SESSIONS_PER_GRANT=1`
- `AI_INVITE_DEFAULT_MAX_PROVIDER_CALLS=5`
- `AI_INVITE_DEFAULT_MAX_ESTIMATED_COST_USD=0.50`
- `AI_INVITE_ALLOWED_WORKFLOWS=importer,dataset_ask,recipe_session,meal_plan`
- `AI_INVITE_LOCAL_OPERATOR_CREATE_ENABLED=true`

Defaults keep the feature off and leave existing offline/mock validation unchanged.

## Local Endpoint Flow

The alpha endpoints are:

- `POST /ai/invite/grants`
- `POST /ai/invite/redeem`
- `GET /ai/invite/grants/{grant_id}`
- `GET /ai/invite/sessions/{session_id}`
- `POST /ai/invite/grants/{grant_id}/revoke`
- `POST /ai/invite/sessions/{session_id}/revoke`
- `GET /ai/invite/status`

Typical flow:

1. Local operator creates a grant.
2. The response may include a raw invite token once, for local handoff only.
3. The grant stores only a fingerprint after creation.
4. The invite token is redeemed into a short-lived demo session.
5. Protected workflows accept `X-AI-Demo-Session-Token` for that session.
6. The grant or session can be revoked or allowed to expire.

## Safety Rules

- Raw invite tokens are not stored.
- Safe status views do not echo tokens.
- No raw prompts, raw provider responses, secrets, `.env` values, or local paths are returned.
- The invite session token is one-time visible only if a local operator creation path chooses to expose it.
- The session and grant stores are process-local and bounded.

## Token And Fingerprint Handling

Token-like values are fingerprinted before storage. Comparisons use safe fingerprints rather than raw token values where practical.

The invite session helper can accept the raw demo session token through `X-AI-Demo-Session-Token` and match it against stored fingerprints. If invite sessions are disabled, the flow returns a safe disabled response instead of creating access state.

## TTL, Expiration, And Revocation

Invite grants and demo sessions are short-lived. They can also be revoked explicitly.

Recommended behavior:

- grants expire after their grant TTL;
- sessions expire after their session TTL;
- grants may be single-use by default;
- revoked grants block redemption;
- revoked sessions block protected workflow access.

## Workflow Limits

Invite grants and sessions carry allowed-workflow lists so a demo can be scoped to a small surface such as importer, dataset ask, recipe session, and meal plan.

Protected workflows block safely when the session token is missing, wrong, expired, revoked, or not allowed for that workflow.

## Budget Interaction

Invite demo sessions reuse the provider budget guard. Their session and grant limits can be used as the budget context for provider-backed calls.

The budget layer remains separate from invite redemption:

- invite flow decides who gets a demo session;
- the budget guard decides whether a provider call may happen;
- the meter event records the safe outcome.

## Local Testing

The default mock smoke script keeps invite sessions disabled.

Optional local smoke path:

```powershell
$env:AI_INVITE_SESSIONS_ENABLED = "true"
$env:AI_INVITE_SMOKE_ENABLED = "true"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
```

The smoke path can create a grant, redeem it, call a protected mock workflow with `X-AI-Demo-Session-Token`, revoke the session, and confirm the revoked session blocks access.

## Explicit Non-Goals

- no production auth;
- no user accounts;
- no login UI;
- no OAuth or OIDC;
- no paid access;
- no payment provider integration;
- no invite emails;
- no public route exposure;
- no production storage;
- no Redis, Postgres, or SQLite persistence;
- no persistent user memory;
- no admin dashboard UI;
- no live OpenAI calls during normal validation.
