# AI Public Route Exposure Review

## Purpose

This review answers the route-exposure questions for the AI sidecar:

- which AI routes exist;
- which routes are local-only;
- which routes could ever be public;
- what must be gated before public access;
- what Cloudflare/reverse-proxy/CORS controls are required;
- what should remain private forever.

The review is documentation-only. It does not change deployment behavior, Cloudflare config, DNS, auth, billing, or storage.
Monetization decisions are separate from route exposure; ads, sponsors, and affiliate disclosures do not make a route public.
The 29/30 integrated regression harness reuses this review as a baseline and asserts that the admin usage-report route stays hidden while the rest of the route inventory keeps its recommended exposure category.

## Current Boundary Summary

- `GET /health` is the only route that is a realistic public candidate today.
- `GET /demo` and `GET /demo/ai` are local demo entry points and may be public only if the demo UI is intentionally exposed later.
- `GET /demo/readiness` is internal status and should stay private.
- `GET /ai/config` is local/operator status and should stay private.
- `/ai/admin/*`, `/ai/invite/*`, and `/ai/recipe-session/*` are local/private control surfaces and should not be routed publicly by default.
- Provider-backed routes such as `POST /ai/import-recipe`, `POST /dataset/ask`, `POST /ai/ask`, and `POST /ai/meal-plan` are invite-only candidates only after gate, invite, budget, proxy, logging, and CORS controls are staged.

## Route Inventory

### Local status and demo surface

| Method | Path | Purpose | Current default exposure | Hidden from OpenAPI | Provider calls | Operator gate | Invite sessions | Budget guard | Admin/operator data | Recommended exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/health` | Liveness check | Local dev, safe to call | No | No | No | No | No | No | `public_candidate` |
| `GET` | `/demo` | Static local demo UI | Local-only demo entry point | Yes | No | No | No | No | No | `public_candidate` if intentionally published |
| `GET` | `/demo/ai` | Static local demo UI alias | Local-only demo entry point | Yes | No | No | No | No | No | `public_candidate` if intentionally published |
| `GET` | `/demo/readiness` | Readiness and environment summary | Local-only status | Yes | No | No | No | No | Yes | `internal_status` |
| `GET` | `/ai/config` | Non-secret provider availability | Local-only config/status | No | No | No | No | No | Yes | `internal_status` |

### Deterministic search and answer routes

| Method | Path | Purpose | Current default exposure | Hidden from OpenAPI | Provider calls | Operator gate | Invite sessions | Budget guard | Admin/operator data | Recommended exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/recipes/search` | Saved-recipe search | Local/private search | No | No | No | No | No | No | `local_only` |
| `POST` | `/recipes/search` | Saved-recipe search | Local/private search | No | No | No | No | No | No | `local_only` |
| `GET` | `/dataset/search` | Local dataset search | Local/private search | No | No | No | No | No | No | `local_only` |
| `POST` | `/dataset/search` | Local dataset search | Local/private search | No | No | No | No | No | No | `local_only` |

### Provider-backed workflow routes

| Method | Path | Purpose | Current default exposure | Hidden from OpenAPI | Provider calls | Operator gate | Invite sessions | Budget guard | Admin/operator data | Recommended exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/dataset/ask` | Dataset question answering | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |
| `POST` | `/ai/import-recipe` | Structured recipe import/create | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |
| `POST` | `/ai/ask` | Saved-recipe question answering | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |
| `POST` | `/ai/meal-plan` | Saved-recipe meal planning | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |

### Recipe Session Alpha routes

| Method | Path | Purpose | Current default exposure | Hidden from OpenAPI | Provider calls | Operator gate | Invite sessions | Budget guard | Admin/operator data | Recommended exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/ai/recipe-session/start` | Start recipe-session alpha | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |
| `POST` | `/ai/recipe-session/{interaction_id}/message` | Continue recipe-session alpha | Local/private workflow | No | Yes | Yes | Yes | Yes | No | `invite_only_candidate` |
| `GET` | `/ai/recipe-session/{interaction_id}` | Inspect recipe-session alpha | Local/private workflow | No | No direct provider call, but state is protected | Yes | Yes | Yes | Yes | `invite_only_candidate` |
| `POST` | `/ai/recipe-session/{interaction_id}/finalize` | Demo finalize | Local/private workflow | No | No direct provider call, but state is protected | Yes | Yes | Yes | Yes | `invite_only_candidate` |

### Invite and operator control routes

| Method | Path | Purpose | Current default exposure | Hidden from OpenAPI | Provider calls | Operator gate | Invite sessions | Budget guard | Admin/operator data | Recommended exposure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/ai/invite/status` | Invite store status | Local/private status | No | No | No | Yes | No | Yes | `internal_status` |
| `POST` | `/ai/invite/grants` | Create invite grants | Local/private operator workflow | No | No | Yes | No | No | Yes | `operator_only` |
| `POST` | `/ai/invite/redeem` | Redeem invite token | Local/private invite workflow | No | No direct provider call, but it creates a budget context | No | Yes | Yes | Yes | `invite_only_candidate` |
| `GET` | `/ai/invite/grants/{grant_id}` | Inspect invite grant | Local/private operator workflow | No | No | No | Yes | No | Yes | `operator_only` |
| `GET` | `/ai/invite/sessions/{session_id}` | Inspect invite session | Local/private operator workflow | No | No | No | Yes | Yes | Yes | `operator_only` |
| `POST` | `/ai/invite/grants/{grant_id}/revoke` | Revoke invite grant | Local/private operator workflow | No | No | Yes | Yes | No | Yes | `operator_only` |
| `POST` | `/ai/invite/sessions/{session_id}/revoke` | Revoke invite session | Local/private operator workflow | No | No | Yes | Yes | Yes | Yes | `operator_only` |
| `GET` | `/ai/admin/usage-report` | Safe usage report | Local/private operator workflow | Yes | No | Yes | Yes | Yes | Yes | `never_public` |

## What Can Ever Be Public

The current review says only the following are plausible public candidates:

- `GET /health`
- `GET /demo` and `GET /demo/ai` if the demo UI is intentionally published later

Everything else should stay local/private unless a future task explicitly stages public exposure with a tighter data boundary.

## What Must Be Gated Before Public Access

Before any provider-backed AI route is made public, the route must be protected by:

- a review of the local/private operator gate;
- invite-session controls, if the route is invite-only;
- the centralized provider budget guard;
- deterministic safe serialization that omits tokens, prompts, responses, request bodies, env values, and local paths;
- a reverse-proxy or Cloudflare rule that only routes the intended path family;
- explicit CORS allowlists for the intended browser origins only;
- request and payload limits;
- logging and rollback rules.

## Cloudflare And Reverse-Proxy Boundary

Current assumption:

- Cloudflare Tunnel or another reverse proxy is the only public ingress;
- the application itself stays on local/private origins;
- the proxy decides which path families are reachable from the public edge.

Recommended proxy policy before any public exposure:

- allow only the exact public path set, not `/ai/*` wholesale;
- block `/ai/admin/*` permanently at the edge;
- block `/ai/invite/*` unless a future task explicitly exposes a carefully scoped invite path;
- block `/ai/recipe-session/*` until the route family is re-reviewed for public exposure;
- keep `/dataset/*` and `/recipes/search` private unless the data they expose is intentionally public-safe;
- keep the local operator gate and usage-report route private even if other public routes are added later.

Safe staging order:

1. publish `GET /health` only if public liveness is required;
2. stage a single public demo path only if the static demo UI is intended to be public;
3. re-review `CORS`, rate limits, logging, and rollback before adding any provider-backed route.

## CORS Boundary

Recommended CORS posture:

- allow only explicit local development origins during local development;
- allow only explicit production origins if a public route is intentionally published;
- do not use wildcard CORS for public AI routes;
- do not expose admin/operator headers broadly in browsers;
- treat `X-AI-Operator-Token` as a private operator header, not a browser-friendly public header;
- treat `X-AI-Demo-Session-Token` as a private invite-session header, not a public browser header;
- keep credentials disabled unless a route truly requires them and the origin is explicitly allowlisted;
- verify preflight behavior for each route family before any public launch.

## Go/No-Go Checklist For Future Public Exposure

- [ ] operator gate reviewed
- [ ] invite session flow tested
- [ ] provider budget enforcement tested
- [ ] usage report reviewed
- [ ] route inventory updated
- [ ] admin/operator endpoints hidden and blocked at the proxy layer
- [ ] CORS restricted
- [ ] live opt-in confirmed
- [ ] secret scan passed
- [ ] evals passed
- [ ] mock smoke passed
- [ ] abuse and rate-limit strategy documented
- [ ] logging reviewed
- [ ] rollback plan documented

## Abuse And Rate-Limit Guidance

Do not implement rate limiting in this task unless it already exists and is trivial to reuse.

Before public exposure, add or verify:

- reverse-proxy request limits;
- per invite/session request limits;
- provider-call limits;
- payload size limits;
- abuse and error thresholds;
- temporary block or revoke behavior;
- incident and rollback process.

## Safe Serialization Rules

The review and any future exposure work must not show:

- raw invite or session tokens;
- API keys;
- `Authorization` headers;
- raw prompts;
- raw provider responses;
- request bodies;
- `.env` values;
- local absolute paths;
- stack traces.

## Explicit Non-Goals

- no public route exposure is added here;
- no Cloudflare changes are made here;
- no DNS changes are made here;
- no auth, login, OAuth/OIDC, paid access, or payment integration is added here;
- no user accounts or user memory are added here;
- no production storage or database migrations are added here;
- no Redis, Postgres, or SQLite persistence is added here;
- no live OpenAI calls are required for normal validation here;
- no generated artifacts, logs, screenshots, or tokens are committed here.

