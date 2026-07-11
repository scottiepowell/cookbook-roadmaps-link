# AI Monetization And Entitlement Boundary ADR

## Status

Accepted

## Date

2026-07-11

## Context

The AI sidecar already has separate guardrails for access, budgets, invite sessions, usage reporting, and route exposure:

- `0029D` defines the local/private operator gate.
- `0029E` defines provider-call budget enforcement.
- `0029F` defines invite-only demo sessions.
- `0029G` defines the local/operator usage report.
- `0029H` reviews public route exposure.

The product question here is not how to collect payment from users today. The near-term business intent is to keep the product free/basic-access oriented while exploring revenue that does not require user-paid access.

## Decision

The near-term monetization model for the AI sidecar is:

- display ads;
- sponsorships;
- partner placements;
- clearly labeled sponsored recipe collections;
- clearly labeled partner/brand placements;
- clearly disclosed affiliate links, only if policy-reviewed.

User-paid access is not being implemented now.

Future paid access, if it ever happens, must be handled in a separate ADR and a separate implementation task. Any future premium feature entitlement must be explicitly approved before it becomes runtime behavior.

The existing access gate, invite-session flow, provider budget guard, and usage report are not payment enforcement. They are safety and operational guardrails.

## Consequences

### Positive

- The free/basic-access model stays simple near term.
- Revenue experiments can happen without creating a checkout or billing system.
- Future premium features can be modeled without contaminating the current ad/sponsor model.
- Access control, budget enforcement, route exposure, and monetization remain distinct concerns.

### Negative

- There is no paid access implementation now.
- There is no entitlement enforcement runtime now.
- Future paid advanced features will require another decision and another implementation task.

## Allowed Now

- display ads in clearly labeled placements;
- sponsorship placements;
- sponsored recipe collections, clearly labeled;
- partner/brand placements, clearly labeled;
- affiliate links, only when clearly disclosed and policy-reviewed;
- non-invasive revenue experiments in documentation or prototypes only;
- conceptual modeling of future entitlements without runtime enforcement.

## Explicitly Not Now

- checkout;
- subscriptions;
- paywalls;
- paid login;
- premium enforcement;
- billing portal;
- invoices;
- taxes;
- refunds;
- payment provider webhooks;
- payment secrets;
- production entitlement database;
- paid access enforcement;
- entitlement runtime enforcement;
- ad network runtime code;
- sponsor placement runtime code;
- affiliate link runtime code.

## Possible Future Options

These are examples only. They are not committed features.

- cloud storage;
- higher AI limits;
- saved recipe history;
- private cookbook sync;
- team or family features;
- export packs;
- business, creator, or brand tools.

Any future paid feature should be introduced by a separate ADR and implementation task with explicit scope, policy review, and validation.

## Technical Boundary

Keep these concepts separate:

| Concept | Responsibility |
| --- | --- |
| Access control | Decides who may use protected AI workflows. |
| Budget guard | Decides whether provider calls may happen within cost and risk limits. |
| Invite sessions | Decide controlled demo access for local/private use. |
| Usage reports | Show operator visibility into safe local state. |
| Monetization | Decides how the product may generate revenue. |
| Entitlements | Decide optional future feature availability. |

Future seam concepts should remain modelable but inactive until a later approved phase:

- `EntitlementPlan`
- `EntitlementFeature`
- `RevenueChannel`
- `SponsorPlacement`
- `AdPlacement`
- `AffiliateDisclosure`

These should stay concept-only for now. They must not automatically grant AI budget, private storage, or route exposure.

How the seams relate to existing models:

- `AiAccessGrant` and `AiDemoSession` describe local/private access state, not payment status.
- `AiProviderBudgetDecision` describes provider-call allow/block/skip decisions, not billing.
- usage-report models describe safe operator visibility, not revenue collection.
- monetization should never be inferred from an access grant or a demo session.

## Policy/Disclosure Considerations

Implementation-facing policy notes, not legal advice:

- sponsor and affiliate relationships should be clearly disclosed;
- native ads and sponsored content should be distinguishable from ordinary recipe content;
- ad placements should not mislead users into clicking;
- internal recipe or AI output should not silently become sponsored content;
- sponsor/ad placement experiments should have tests for labels and forbidden unsafe copy;
- ad network IDs, sponsor contracts, affiliate secrets, and payment keys must not be committed.

Any production monetization launch requires separate legal and policy review before shipping.

## Testing/Validation

This ADR is validated by documentation-only tests that check:

- the ADR file exists;
- the near-term monetization path is ads/sponsorships/partner placements;
- paid access is not implemented now;
- future paid advanced features require a separate ADR/task;
- the ADR does not include payment secrets or live payment-provider implementation instructions;
- the repo references this ADR title in backlog/status docs.

The 29/30 integrated regression harness also treats this ADR as a locked docs-only boundary and checks that the combined local AI demo baseline does not add payment, ad, sponsor, or affiliate runtime code.

No runtime payment, ad, sponsor, affiliate, or entitlement enforcement code is added by this ADR.

## Non-Goals

- no payment provider integration;
- no checkout;
- no subscriptions;
- no invoices;
- no tax/VAT logic;
- no refunds;
- no paid user accounts;
- no production auth;
- no paid access enforcement;
- no entitlement runtime enforcement;
- no ad network runtime code;
- no sponsor placement runtime code;
- no affiliate link runtime code;
- no public route exposure;
- no Cloudflare changes;
- no database migrations;
- no production storage;
- no Redis, Postgres, or SQLite persistence;
- no live OpenAI calls during normal validation.

