# AI Local Operator Access Gate

## Purpose

This document describes the first local/private operator gate for the AI demo surface. It is an opt-in guardrail for local workflows, not production auth.

The gate protects the demo routes when enabled:

- importer: `POST /ai/import-recipe`
- dataset ask/RAG: `POST /dataset/ask`
- recipe session: `GET/POST /ai/recipe-session/*`
- meal plan: `POST /ai/meal-plan`

The gate is disabled by default so normal offline validation, mock smoke tests, and local demo flows remain unchanged.

## Configuration

Recommended environment variables:

```text
AI_OPERATOR_GATE_ENABLED=false
AI_OPERATOR_GATE_TOKEN_FINGERPRINT=
AI_OPERATOR_GATE_ALLOWED_WORKFLOWS=importer,dataset_ask,recipe_session,meal_plan
AI_OPERATOR_GATE_LOCAL_BYPASS=true
```

Optional raw token convenience is supported for local development, but it is fingerprinted immediately and never returned in responses.

## Decision Model

The helper returns a safe `AiOperatorGateDecision` with:

- `enabled`
- `allowed`
- `workflow`
- `reason`
- `status`: `allowed`, `blocked`, `disabled`, or `misconfigured`
- `grant_type`
- `metadata_fingerprint`
- `safe_message`
- `safe_metadata`

The decision object is safe to serialize and does not include raw tokens, API keys, request bodies, local paths, or other secret-like values.

`0029E` applies the centralized provider budget guard after this gate. That guard can still block a request that was allowed by the operator gate if the provider is globally disabled, the call count is exhausted, or the requested token/cost budget is too large.

`0029G` protects the local/operator usage-report endpoint with the same gate when the gate is enabled, so the report stays local/private and does not become a production admin surface.

`0029F` adds invite-only demo sessions as a separate local/private boundary. When invite sessions are enabled, protected workflows can also accept a short-lived `X-AI-Demo-Session-Token` header for a redeemed invite session. Invite sessions are still not production auth, and they continue to sit behind the same local/private demo boundary.

## Verification Rules

`check_operator_gate(workflow, request_headers, settings, client_host=...)` performs the gate decision.

Behavior:

- gate disabled: allow request;
- workflow not listed in `AI_OPERATOR_GATE_ALLOWED_WORKFLOWS`: block request;
- local bypass enabled and request is local/TestClient: allow request;
- gate enabled with no configured fingerprint: return misconfigured;
- gate enabled with a missing token: block request;
- gate enabled with a fingerprint mismatch: block request;
- gate enabled with a matching `X-AI-Operator-Token` or `Authorization: Bearer ...`: allow request.
- invite sessions enabled with a valid `X-AI-Demo-Session-Token`: allow request if the workflow is listed on the invite grant/session.

Fingerprint comparison uses constant-time comparison where practical.

## Safe Responses

Blocked requests return safe HTTP errors:

- `403` for blocked requests;
- `503` for misconfigured gate settings;
- safe JSON detail only, with no raw token or header echo.

## Demo Boundaries

- The gate is local/private only.
- It is not production auth, login, OAuth/OIDC, or paid access.
- It does not add user accounts, invite emails, payment integration, or public exposure.
- Invite-only demo sessions are local/private too; they do not create a production session store or public invite flow.
- It does not persist access state to a database.
- It does not block mock/offline validation when the gate is disabled.

## Validation

The gate is covered by offline unit and route tests in `ai-api/tests/test_ai_operator_gate.py` and is exercised through TestClient in the local API surface.

The mock smoke helper pins the gate off so the smoke path stays stable in a dirty shell.

## Future Work

Later tasks may build on this helper for invite-only access, budget enforcement, or a production access layer. Those are intentionally out of scope here.
