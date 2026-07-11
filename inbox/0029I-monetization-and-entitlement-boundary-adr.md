# 0029I Monetization And Entitlement Boundary ADR

## Goal

Create an architecture decision record that defines the future monetization and entitlement boundary for the AI demo/product without implementing paid access, payments, billing, subscriptions, checkout, public monetization runtime, or production entitlement enforcement.

This task intentionally reframes the older backlog idea of `Paid Access Integration ADR` as `Monetization And Entitlement Boundary ADR`.

The near-term business intent is not to collect money from users for access. The near-term revenue model should be ads, sponsorships, partner placements, and similar non-user-paid monetization. Paid access should be treated only as a possible future option for advanced features such as storage, higher limits, private sync, team/family features, or business tools.

## Context

`0029C` added schema-only access and metering models.

`0029D` added the local/private operator access gate.

`0029E` added centralized provider-call budget enforcement.

`0029F` added local/private invite-only demo sessions.

`0029G` added the local/operator usage-report prototype.

`0029H` completed the public route exposure review and confirmed that no public route exposure, Cloudflare change, auth layer, payment integration, or storage change was added.

`0029I` should close the 0029 guardrail track by documenting monetization options and entitlement seams without implementing any monetization runtime.

## Primary Objective

Write an ADR that answers:

```text
What is the intended near-term monetization model?
What revenue models are explicitly allowed later?
What is explicitly not being implemented now?
What technical seams should remain so future paid advanced features are possible without contaminating the free/ad/sponsor model?
How should ads, sponsors, affiliate links, and future premium entitlements be kept separate from access control, budgets, and route exposure?
```

## Business Direction To Encode

The ADR must reflect this decision:

```text
Near term: free/basic access supported by ads, sponsors, and partner/sponsor placements.
Not now: charging users for access, subscriptions, checkout, billing, invoices, tax/VAT, refunds, or payment-provider integration.
Future optional: paid advanced features only if a later decision explicitly approves them.
```

Potential future paid advanced features may include:

- cloud recipe storage;
- larger saved history;
- private cookbook sync;
- family/team accounts;
- advanced meal planning;
- exports/download packs;
- larger AI usage limits;
- custom/private datasets;
- business/creator/brand tooling.

Do not imply these are committed features. They are examples of future entitlement categories only.

## External Policy Considerations To Document

Use official/public references where appropriate in the ADR notes, but do not add legal advice.

Document that ad/sponsor monetization introduces disclosure and platform-policy obligations, including:

- sponsorship/endorsement disclosures;
- native advertising disclosure considerations;
- ad network policy compliance;
- invalid click/impression avoidance;
- avoiding deceptive labels or confusing ad placement;
- separation of sponsored content from recipe/AI outputs where appropriate.

The ADR should state that detailed legal/policy review is future work before production monetization.

## Non-Negotiable Boundaries

Do not add:

- payment provider integration;
- Stripe integration;
- PayPal integration;
- checkout;
- subscriptions;
- invoices;
- tax/VAT logic;
- refunds;
- paid user accounts;
- production auth;
- paid access enforcement;
- entitlement runtime enforcement;
- ad network runtime code;
- sponsor placement runtime code;
- affiliate link runtime code;
- public route exposure;
- Cloudflare changes;
- database migrations;
- production storage;
- Redis/Postgres/SQLite persistence;
- persistent user memory;
- live OpenAI calls during normal validation;
- committed secrets, `.env` files, tokens, logs, screenshots, generated artifacts, ad network IDs, sponsor contracts, payment keys, or affiliate secrets.

This task is ADR/docs/tests only unless a tiny static-doc reference test is useful.

## Suggested Files

Likely new files:

- `docs/ai-monetization-and-entitlement-boundary-adr.md`
- `ai-api/tests/test_ai_monetization_boundary_docs.py`
- `outbox/0029I-monetization-and-entitlement-boundary-adr-results.md`

Likely updated files:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-public-route-exposure-review.md`
- `docs/ai-session-metering-schema.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-evals-plan.md` if relevant
- `README.md` if relevant

## Required Work

### 1. Create the ADR

Create:

```text
docs/ai-monetization-and-entitlement-boundary-adr.md
```

Use a clear ADR format:

```text
Title
Status
Date
Context
Decision
Consequences
Allowed Now
Explicitly Not Now
Possible Future Options
Technical Boundary
Policy/Disclosure Considerations
Testing/Validation
Non-Goals
```

### 2. Define the decision clearly

The ADR decision should say:

- the product remains free/basic-access oriented near term;
- monetization should first focus on ads, sponsorships, partner placements, and similar non-user-paid models;
- user-paid access is not being implemented now;
- future paid advanced features require a separate ADR and explicit implementation task;
- existing access/budget/invite/reporting guardrails are not payment enforcement;
- entitlements should remain modelable but inactive until a later approved phase.

### 3. Define monetization categories

Document categories:

#### Allowed near-term concepts

- display ads;
- sponsorship placements;
- sponsored recipe collections if clearly labeled;
- partner/brand placements if clearly labeled;
- affiliate links if clearly labeled and policy-reviewed;
- non-invasive revenue experiments in docs/prototypes only.

#### Explicitly not implemented now

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
- production entitlement database.

#### Future possible advanced-feature entitlements

Examples only:

- cloud storage;
- higher AI limits;
- saved recipe history;
- private cookbook sync;
- team/family features;
- export packs;
- business/creator/brand tools.

### 4. Define technical seams

Document future seams without implementing them:

- `EntitlementPlan` concept;
- `EntitlementFeature` concept;
- `RevenueChannel` concept;
- `SponsorPlacement` concept;
- `AdPlacement` concept;
- `AffiliateDisclosure` concept;
- relation to `AiAccessGrant`, `AiDemoSession`, `AiProviderBudgetDecision`, and usage report models;
- how access limits differ from paid entitlements;
- how ad/sponsor visibility should not automatically grant AI budget or private storage.

Do not implement these models unless they are documentation examples only.

### 5. Separate access control from monetization

The ADR must make this clear:

```text
Access control decides who can use protected AI workflows.
Budget guard decides whether provider calls are allowed within cost/risk limits.
Invite sessions decide controlled demo access.
Usage reports show operator visibility.
Monetization decides how the product may generate revenue.
Entitlements decide optional future feature availability.
```

Do not conflate ad/sponsor revenue with user identity, billing, or provider-call budget enforcement.

### 6. Ad/sponsor policy notes

Document non-legal, implementation-facing policy notes:

- sponsor/affiliate relationships should be clearly disclosed;
- native ad/sponsored content should be distinguishable from ordinary recipe content;
- ad placements should not mislead users into clicking;
- internal recipe/AI output should not silently become sponsored content;
- sponsor/ad placement experiments should have tests for labels and forbidden unsafe copy;
- ad network IDs and sponsor contracts/secrets must not be committed.

Mention that final production monetization requires legal/policy review.

### 7. Update backlog/status docs

Update:

- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-public-route-exposure-review.md`
- `docs/ai-session-metering-schema.md`
- `docs/ai-provider-budget-enforcement.md`
- `docs/ai-invite-only-demo-session-flow.md`
- `docs/ai-admin-usage-report-prototype.md`
- `docs/ai-live-demo-runbook.md`
- `README.md` if relevant

Mark `0029I` complete only after validation passes.

The backlog should reflect the renamed/reframed title:

```text
0029I: Monetization And Entitlement Boundary ADR
```

not simply `Paid Access Integration ADR`.

### 8. Add documentation tests

Add:

```text
ai-api/tests/test_ai_monetization_boundary_docs.py
```

Tests should verify:

- ADR file exists;
- ADR states ads/sponsors are the near-term monetization path;
- ADR states paid access is not implemented now;
- ADR states future paid advanced features require a separate ADR/task;
- ADR does not include payment secret examples;
- ADR does not include live payment provider implementation instructions;
- README/backlog references the new ADR title;
- forbidden strings do not appear in ADR/docs.

Forbidden strings should include:

```text
sk_live_
sk_test_
STRIPE_SECRET_KEY
PAYPAL_CLIENT_SECRET
checkout_session_secret
webhook_secret
Authorization: Bearer real
OPENAI_API_KEY
.env
C:\\Users\\
/home/
```

### 9. Create outbox report

Create:

```text
outbox/0029I-monetization-and-entitlement-boundary-adr-results.md
```

Include:

- ADR created;
- business decision captured;
- ads/sponsors first boundary;
- paid access not-now boundary;
- future advanced-feature entitlement boundary;
- technical seams documented;
- docs/tests updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation.

## Acceptance Criteria

- ADR exists at `docs/ai-monetization-and-entitlement-boundary-adr.md`.
- ADR clearly states that near-term revenue is ads/sponsors/partner placements, not user-paid access.
- ADR clearly states no payment integration, checkout, subscriptions, billing, invoices, taxes, refunds, paid login, or premium enforcement is implemented now.
- ADR documents optional future paid advanced-feature categories only as future possibilities requiring a separate decision.
- ADR separates access control, budget enforcement, invite sessions, usage reports, monetization, and entitlement concepts.
- Policy/disclosure considerations for ads/sponsors/native ads/affiliate links are documented without legal advice.
- Backlog/status docs use the reframed title `Monetization And Entitlement Boundary ADR`.
- Documentation tests pass.
- Existing offline/mock validation remains stable.
- No runtime payment, ad, sponsor, affiliate, public exposure, production storage, auth, or live OpenAI behavior is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_monetization_boundary_docs.py -q
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

If direct Windows pytest hits the known local `pytest-of-scott` temp ACL issue for unrelated fixture tests, document it and rely on Git Bash validation if it passes.

Before committing, confirm:

- no payment provider keys;
- no ad network IDs;
- no sponsor secrets/contracts;
- no raw invite/session tokens;
- no raw dataset files;
- no `.tmp-ai-demo` artifacts;
- no generated persistent index files;
- no disk cache;
- no `.env` files;
- no screenshots;
- no logs;
- no credentials;
- no raw provider prompts;
- no raw provider responses;
- no local absolute paths in public docs examples;
- no production session storage.

## Commit

```bash
git add ai-api docs README.md outbox/0029I-monetization-and-entitlement-boundary-adr-results.md

git commit -m "mailbox: complete task 0029I monetization entitlement boundary adr"

git pull --rebase origin main
git push origin main
```
