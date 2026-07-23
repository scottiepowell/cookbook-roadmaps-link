# ADR: Application Session Timer and Access Exceptions

Status: proposed, docs-only

Date: 2026-07-23

## Decision summary

If a future production access layer needs an abuse and cost boundary, use a
server-authoritative 30-minute application session for the default public/free
experience. Treat the timer as an access/session policy, not as a provider
timeout and not as a browser-only countdown. Keep it separate from provider
budget enforcement while allowing both policies to contribute to a safe
decision.

The default policy is:

```text
Default public/free session: 30 minutes
Warnings: 5 minutes remaining and 1 minute remaining
Expired session: read-only/restart state with safe draft export or copy path
Operator/trusted exception: disabled or explicitly extended timer
Invite/demo exception: configured per invite/session
Abuse fallback: short cooldown or request limit, never silent failure
```

This ADR does not implement runtime enforcement, production auth, persistence,
or a new route. It defines a future contract that can build on the existing
operator gate, invite-session concepts, process-local session models, and
provider budget guard.

## Problem statement

AI workflows can be expensive, long-lived, and attractive to automated abuse.
The product also needs a bounded experience that is understandable to a free
or preview user. A hard, unexplained cutoff would make recipe creation feel
hostile and could discard valuable work. A client-only timer would be easy to
evade and would not protect provider spend.

The design therefore needs a friendly application boundary, safe exceptions
for operators and selected users, and clear separation between session access,
workflow state, and provider-call cost controls.

## User experience

At session start, show that the session is time-limited, the approximate
expiry, and what the user can do before it expires. Use a visible but calm
countdown, an accessible live status announcement, and clear text rather than
color alone. Warn at five minutes and one minute, with language such as
“Your Cookbook session ends in about five minutes. Finish or copy your draft
to keep working later.”

At expiry, do not silently drop a draft or recipe session. Transition to a
read-only/restart state. Preserve only the bounded state that the future
product policy allows, offer a safe copy/export action for user-visible draft
content, explain that a new session is required for further AI actions, and
provide a clear restart path. Export must not include prompts, provider
responses, tokens, private diagnostics, or unrelated user data.

The UI timer is an aid, not the authority. A stale tab, sleep/wake event, or
clock change must resolve against a server decision on the next protected
request. Normal users should see a friendly expired-session message rather
than a 401/403 diagnostic, stack trace, or unexplained blank panel.

## Policy boundary

The recommended model is application-session-based with workflow state scoped
inside the session. It is not route-based, because users should not receive a
fresh thirty minutes by navigating between pages. It is not provider-call-based,
because a provider call may be short while a recipe session includes reading,
clarification, drafting, and copying work. It is not only UI-based, because a
browser timer cannot enforce cost or abuse limits.

Distinguish three decisions:

| Decision | Purpose | Authority | Typical result |
| --- | --- | --- | --- |
| UI timer | Explain remaining access time | Browser display, refreshed from server | Warning or countdown |
| Application session expiry | Bound access to protected workflows | Server-side session policy | Allow, read-only/expired, or restart |
| Provider budget enforcement | Bound calls, tokens, and estimated cost | Server-side budget guard/provider policy | Allow, mock/fallback, or safe blocked response |

Session expiry and provider budget may both block an action. The user-facing
message should identify the actionable reason without exposing internal policy
details. A budget exhaustion must not be disguised as timer expiry, and a
timer expiry must not reset the provider budget.

## Exceptions and bypass model

Exceptions should be explicit policy metadata, not an undocumented magic token.
They should build on existing concepts without assuming production auth exists:

- **Local operator:** a configured local operator gate can grant a disabled or
  extended timer for private testing. Store only a token fingerprint and safe
  operator label; never print or persist the raw token.
- **Trusted user:** a future authenticated account may receive a policy class
  such as `trusted_extended` or `trusted_unlimited`, subject to review and
  separate provider budgets. This ADR does not add authentication or decide
  who qualifies.
- **Invite/demo session:** an invite grant may carry a configured duration,
  maximum session count, allowed workflows, and provider limits. The invite
  session inherits the shortest applicable safety limit unless an explicit
  operator policy says otherwise.
- **Support override:** a time-limited, auditable operator action may extend a
  single session. It should have a reason, expiry, safe actor label, and
  revocation path.

An exception can disable the application timer, extend it, or change warning
thresholds, but it cannot bypass provider budgets, model allowlists, global
kill switches, workflow scopes, or data authorization. No browser-controlled
flag may create an exception.

## Relationship to existing controls

The operator gate answers whether a protected local/operator workflow is
allowed. Invite sessions answer who may use a bounded demo and which workflows
are allowed. The provider budget guard answers whether a provider call fits
within call, token, cost, and global-disable policy. A future session timer
answers whether the application session is still active.

These controls should compose as a fail-closed decision for live calls:

```text
session active or approved exception
        AND operator/invite/account access allowed
        AND workflow scope allowed
        AND provider budget available
        AND provider kill switch is off
        -> provider-backed action may proceed
```

Mock/offline workflows may remain usable for deterministic validation when live
provider access is disabled, provided the UI truthfully labels the mode. The
timer policy must not turn normal repository validation into a live call or
require a provider key.

## Privacy and security

Future server-side state should contain only the minimum session identifiers,
status, creation/expiry timestamps, policy class, allowed workflows, safe
exception metadata, and bounded draft/session references. Do not store raw
tokens, API keys, prompts, provider bodies, local paths, raw IP addresses by
default, or unrelated profile data. Use fingerprints for token-like values and
safe operator labels for support views.

Expiry and exception events should be metadata-only and retained for the
shortest operational period that supports abuse review and troubleshooting.
User-visible export must be scoped to the current draft and must clearly state
what is being copied. A future authenticated core app remains the authority for
user identity and ownership; the AI sidecar must not invent a durable identity
system.

## Abuse prevention

The timer is one layer, not a complete abuse system. Add bounded request counts,
per-session provider-call limits, token caps, cost caps, workflow allowlists,
and a global provider kill switch as separate controls. When a user repeatedly
creates sessions or hits a policy limit, prefer a short, clearly messaged
cooldown or request limit over silent failure. Do not create a loophole where
refreshing the browser renews free provider access without policy evaluation.

Exceptions should be rarer and more observable than default access. An
operator/trusted exception can remove the time limit while retaining budgets,
rate limits, and kill switches.

## Implementation options

1. **Signed server-side session assertion:** the core app issues a short-lived,
   audience-bound assertion; the sidecar evaluates the timer policy and keeps
   bounded session state. Best fit for the plugin/adapter architecture, but
   requires a future auth/session security design.
2. **Core-app session with adapter policy call:** the core app remains the
   session authority and the adapter passes an expiry/policy result to the
   sidecar. Minimizes sidecar identity responsibility but requires reliable
   server-to-server context propagation.
3. **Sidecar-managed local demo session:** useful for a private prototype only,
   using the existing process-local models and invite/operator concepts. It is
   not sufficient for production or multi-instance enforcement.

The recommendation is option 1 or 2 for production, chosen after the separate
identity/session ADR. Option 3 is acceptable only for a deterministic local
proof of concept and must not be mistaken for production enforcement.

## Testing strategy

Future implementation tests should remain deterministic and mock/offline:

- session starts with a 30-minute policy and records safe expiry metadata;
- warnings appear at five and one minute, once per threshold;
- server time wins over client clock changes and stale tabs;
- expiry blocks protected actions but preserves safe read/copy/export behavior;
- drafts and in-progress Recipe Sessions are not silently discarded;
- operator and invite exceptions apply only to their configured scope;
- exceptions do not bypass provider budget, kill switch, model, or workflow
  limits;
- repeated new sessions hit request/cooldown policy where configured;
- mock mode remains available without keys and normal validation makes no live
  calls;
- safe responses omit raw tokens, prompts, provider output, headers, and
  stack traces;
- accessibility tests cover live announcements, keyboard access, focus,
  contrast, responsive layout, and readable expired-state recovery.

Time should be injected through a clock in tests rather than sleeping. Contract
tests should cover the core-app/adapter/sidecar policy shape without requiring
AWS, a live provider, production auth, or a persistent database.

## Explicit non-goals

This ADR does not implement timer middleware, session storage, countdown UI,
export endpoints, auth, SSO, payment, analytics, ads, monetization, AWS or
platform work, database migrations, public routes, provider routing, a
secondary provider, vector retrieval, or live OpenAI calls. It does not select
the final identity mechanism or define a production retention schedule.
