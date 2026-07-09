# AI Access Control Threat Model

## Status

Proposed design only. No runtime controls are implemented by this document.

## Assets

- Provider API keys and server-side configuration.
- Provider budget and cost controls.
- Private cookbook recipe data and generated demo fixtures.
- Session, access grant, meter event, and future entitlement records.
- User identity and invite state.
- Admin/operator controls.
- Prompt and response content where retained by future features.

## Trust Boundaries

- Browser to public site.
- Browser to protected AI endpoints.
- Reverse proxy or Cloudflare Tunnel to application containers.
- AI sidecar to provider API.
- AI sidecar to cookbook data and dataset fixtures.
- Admin/operator interface to session and metering store.
- Future payment provider webhooks to entitlement service.

## Threats And Mitigations

| Threat | Risk | Mitigation |
| --- | --- | --- |
| Unauthenticated public spend | Public users or bots trigger live provider calls. | No public unauthenticated live AI endpoint; require access layer, session, budget, and global provider switch. |
| Prompt spam | Attackers burn budget with repeated prompts. | Per-session caps, rate limits by user/session/IP hash, input-quality checks, provider kill switch. |
| API abuse bypassing UI | Users call `/ai/*` directly. | Protect provider-backed routes server-side; never rely on UI hiding; validate sessions on every workflow request. |
| Leaked provider keys | Keys are copied into client, logs, docs, or artifacts. | Server-side only keys, secret scanning, no key fragments in logs, ignored env files. |
| Session replay | Captured session token is reused. | Opaque session ids, expiry, revocation, secure cookies or signed tokens, CSRF protections where needed. |
| Excessive input size | Large inputs drive cost or resource exhaustion. | Deterministic size limits before provider calls, per-call token caps, request body limits. |
| Toxic or unsafe content | Users submit harmful content or prompt-injection attempts. | Input-quality checks, provider safety policies, bounded workflows, no tool execution from model output. |
| Cross-demo data leakage | One demo retrieves another demo's records. | App namespaces, separate stores or schemas, separate indexes/collections, separate eval suites. |
| Private recipe/data leakage | Model response exposes unintended private data. | Retrieval scoped to session/app/user, citations/provenance, no shared corpus, least-privilege data access. |
| Sensitive prompt logging | Logs retain private recipes or user text. | Raw prompt logging off by default, metadata-only logs, explicit retention decisions for any content logging. |
| Budget race condition | Concurrent calls exceed caps. | Transactional budget reservation or atomic counters before provider calls, post-call reconciliation. |
| Kill-switch bypass | Provider calls continue after operator disables live mode. | Central provider-call gate checked immediately before every provider call. |
| Admin misuse | Operator exports or changes usage data without trace. | Admin audit events for revocation, export, override, and kill-switch changes. |
| Payment/webhook abuse | Future fake webhooks grant paid access. | Defer payment integration; future ADR must include signed webhook verification, replay protection, and audit trail. |

## Security Requirements

- No public unauthenticated live provider-backed endpoint.
- Live provider can be globally disabled without code changes.
- Access mode and session are checked for every provider-backed workflow.
- Deterministic input-quality checks run before provider calls.
- Raw prompt logging is off by default.
- Provider keys are never exposed to the browser.
- Each demo owns its data boundary even when infrastructure is shared.
- Future paid entitlements are enforced through the access layer, not inside workflow handlers.

## Residual Risks

- Cost estimates can drift if provider pricing changes and defaults are stale.
- Coarse abuse markers may not stop distributed abuse.
- Magic-link or invite-code flows need careful implementation to avoid token leakage.
- Admin dashboards can become sensitive even without raw prompts because usage metadata can reveal behavior.
- Future payment integration introduces dispute, refund, tax, and support risks outside the current implementation.
