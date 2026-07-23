# ADR: Traffic Analytics and Behavior Tracking

Status: proposed, docs/research-only

Date: 2026-07-23

## Decision summary

Do not add analytics or tracking yet. If the product later needs measurement,
start with a small, first-party, privacy-preserving event taxonomy and
aggregate reporting. Prefer server-side events that contain safe event names,
bounded categories, timestamps, and coarse operational dimensions over raw
behavioral logs. Require a documented purpose, lawful basis, retention period,
user choice, deletion path, and data map before any production collection.

Advertising, sponsor, attribution, and conversion tracking are separate,
higher-risk decisions. They must not be smuggled into product analytics and
remain deferred to the future ads/sponsors/monetization ADR (`0033F`).

This ADR adds no scripts, cookies, pixels, beacons, analytics vendor, database
schema, public route, browser tracker, or runtime event collection.

## Research note

Reputable public guidance was reviewed on 2026-07-23. It is not legal advice
and does not replace jurisdiction-specific counsel or a future data-protection
assessment:

- The [ICO cookies and similar technologies guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/)
  says non-essential cookies generally require clear, positive consent and
  that analytics cookies are not automatically strictly necessary.
- The [CNIL audience-measurement guidance](https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies-solutions-de-mesure-daudience)
  describes a narrow possible consent exemption only when measurement is
  strictly limited to the publisher, produces anonymous statistics, does not
  cross-reference other processing, and meets additional conditions. It also
  warns that many large offerings do not fit the exemption.
- The [EDPB cookie policy example](https://www.edpb.europa.eu/edpb-cookie-policy_en)
  demonstrates a consent-based approach where non-essential analytics is off
  by default, while the [EDPB consent guidance](https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en)
  emphasizes informed, specific, freely given choice.
- [GDPR Article 5](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679)
  establishes purpose limitation, data minimization, and storage limitation as
  core principles.

The exact result depends on geography, audience, device technology, provider
configuration, purposes, and whether events can be linked to an account.

## Problem statement and product questions

The product owner wants to understand traffic, feature adoption, workflow
quality, retention, and future sponsor performance without collecting recipe
content or turning a local/demo AI product into a surveillance system. Useful
questions are:

- Which pages and features are used most?
- Where do users drop off?
- Which AI workflows are started, completed, abandoned, or erroring?
- Which buttons/actions are clicked?
- How often do users hit timer/session limits?
- How often do users hit provider budget limits or AI-unavailable states?
- Which ads/sponsor placements are viewed or clicked?
- Which marketing sources bring engaged users?
- Which features correlate with return visits?

Each question must have an owner, an allowed event set, a decision it will
inform, and a deletion/retention rationale. “Collect everything in case it is
useful” is not an approved purpose.

## Event taxonomy

These names are design candidates only. Payloads should contain a schema
version, event name, coarse timestamp, safe anonymous/pseudonymous session
reference where justified, and bounded dimensions. Do not log raw request or
response bodies.

### Visits, navigation, and interaction

```text
page_view
session_start
session_end
timer_warning
timer_expired
feature_view
button_click
search_performed
```

Record route or feature identifiers from an allowlist, not arbitrary URLs or
query strings. Button events should use stable action names, not visible text
that may contain user content.

### AI workflow lifecycle

```text
workflow_start
workflow_complete
workflow_abandon
workflow_error
ai_unavailable
budget_limit_hit
recipe_import_started
recipe_import_completed
recipe_session_started
recipe_session_finalized
```

Use workflow name, safe status, warning count, citation count, coarse latency
bucket, and mock/live mode classification only when needed. Never attach the
prompt, imported recipe text, draft body, provider response, or model payload.

### Advertising and commercial events

```text
ad_impression
ad_click
sponsor_click
conversion
feedback_submitted
```

These remain deferred. If later approved, define each placement, sponsor,
purpose, consent state, attribution window, fraud controls, disclosure, and
retention policy separately. Do not use product analytics as a hidden ad
tracker.

## Data that must not be tracked

Never place these in raw event logs or analytics dimensions:

- raw recipe text, imported notes, drafts, or recipe instructions;
- raw AI prompts, provider responses, or retrieval context;
- API keys, access tokens, OAuth refresh tokens, invite tokens, or operator
  tokens;
- BYOS file contents, private cloud-storage paths, or file names when they may
  reveal private content;
- local file paths, stack traces, headers, request bodies, or environment values;
- raw email addresses unless a separately approved, protected operational need
  exists; default to an internal pseudonymous account reference;
- precise unnecessary location, fingerprinting attributes, or cross-site IDs;
- sensitive health, medical, allergy, religious, or dietary details beyond a
  justified, coarse aggregate category—and preferably none;
- children/minor data, payment details, and support secrets.

Recipe content and dietary details can be sensitive even when a workflow seems
harmless. Event schemas must reject unexpected free-text fields and enforce
bounded enums/lengths.

## Privacy, consent, and disclosure

Before implementation, document the controller/processor roles, purposes,
lawful basis, categories, recipients, regions, retention, user rights,
security controls, and deletion/export behavior. Publish a plain-language
analytics notice that names categories and choices without requiring users to
read source code.

### Cookie and banner implications

No cookies or client trackers are part of this task. If a future design uses
non-essential cookies, local storage, pixels, fingerprinting, or similar
storage/access technology, it needs a jurisdiction-reviewed consent design
before activation. Consent must be granular, informed, freely given, easy to
refuse, and easy to withdraw; analytics must not load before the applicable
choice. Essential session/security state must remain clearly separated from
optional measurement.

A cookieless server-side event is not automatically exempt from privacy
obligations. It can still process personal data when events are linkable to a
person, account, device, or identifiable session. The implementation should
prefer aggregation and short-lived pseudonymous references, and must document
why any identifier is necessary.

## Analytics modes

### Mode 1: anonymous aggregate analytics

Counts and coarse time buckets with no durable identifier. This is the default
target for basic page/feature usage. Small groups should be suppressed to
reduce re-identification risk.

### Mode 2: pseudonymous session analytics

A short-lived, random session reference links events within one application
session to measure workflow drop-off. It must not be a cross-site identifier,
must respect the 0033B timer/expiry policy, and should expire with the session
or a documented short retention window.

### Mode 3: account-linked analytics after SSO

Only after the 0033C identity decision is implemented and separately approved.
Use an internal account reference, never provider email or OAuth subject in
reports. Provide notice, purpose limitation, access/deletion handling, and a
way to avoid optional product analytics without losing core access.

### Mode 4: operator/admin usage reports

Safe operational summaries may show workflow counts, statuses, budget-limit
events, latency buckets, and health. Existing AI usage-report concepts are the
model: no prompts, responses, tokens, secrets, private paths, or raw content.
Operator access does not authorize broad user surveillance.

### Mode 5: ad/sponsor conversion analytics

Deferred. It needs separate commercial disclosure, consent/legal review,
attribution and fraud policy, sponsor data-sharing limits, retention, and
deletion rules. It must never be enabled merely because an analytics tool is
installed.

## Retention, aggregation, deletion, and portability

Keep raw events only as long as needed to produce the approved report; prefer
short raw retention followed by irreversible aggregation. Set different limits
for operational errors, anonymous counts, pseudonymous sessions, and
account-linked events. Document timezone, aggregation windows, small-cell
suppression, and whether a report can be recomputed.

Deletion must cover raw events, pseudonymous lookup material, account-linked
events, exports, backups, and vendor copies where applicable. If an event is
irreversibly aggregated and no longer relates to an identifiable person, say so
in the data policy; do not claim deletion if a retained lookup can relink it.
User export should include meaningful account-linked analytics only when a
future policy and format make that useful; raw tracking history should not be a
surprise data product.

## Relationship to AI metering, timer, and monetization

AI provider metering answers cost and provider-usage questions. Analytics can
consume safe summaries such as workflow status, token-count buckets, budget
limit status, and latency buckets, but should not duplicate provider meter
events or ingest raw provider data. Metering remains authoritative for budget
enforcement; analytics is observational.

The 0033B timer records access-policy outcomes such as warning/expiry counts in
safe form if approved. It must not expose session tokens or turn an expired
session into a tracking loophole. A timer exception may be represented as a
coarse policy class for operational analysis, not as a raw operator identity.

Ads, sponsors, marketing attribution, and conversions belong to 0033F. Until
that ADR and implementation approvals exist, no commercial tracking is
collected or inferred from generic click events.

## Tool and vendor options

| Option | Benefits | Risks/tradeoffs |
| --- | --- | --- |
| First-party server-side aggregate sink | Maximum data boundary/control; no browser tracker required; easy mock sink | Requires careful schema, aggregation, access control, retention jobs, and observability. |
| Self-hosted privacy-oriented analytics | Greater control and potentially configurable anonymization/retention; can avoid third-party sharing | Hosting, patching, backups, lawful-basis analysis, cookie configuration, and operator access remain the app owner's responsibility. |
| Third-party product analytics | Fast dashboards, funnels, cohorts, and integrations | Vendor transfer, cookies/SDKs, cross-context identifiers, consent, retention, subprocessor, and lock-in risks. |
| Cookieless/server-side third-party measurement | Less browser code and possibly simpler UX | Server-side identifiers can still be personal data; vendor contracts, IP handling, purpose, and consent questions remain. |

Possible products may be evaluated later, including a configured self-hosted
tool such as Matomo or a third-party service, but no vendor is selected here.
The right choice depends on jurisdiction, scale, support capacity, data-sharing
terms, and whether the product can meet its minimization/retention promises.

## Implementation phases

1. **Phase 0: ADR only.** Approve purposes, taxonomy, prohibited fields,
   consent, retention, deletion, and ownership.
2. **Phase 1: local mock event sink.** Add only deterministic in-memory or test
   fixtures in a future task; no production collection or vendor.
3. **Phase 2: server-side aggregate collection.** Collect allowlisted safe
   events, aggregate quickly, restrict operator reports, and prove deletion.
4. **Phase 3: privacy/consent-aware client events.** Add only if server events
   cannot answer an approved question; implement consent before any optional
   client storage/tracker.
5. **Phase 4: ad/sponsor click and conversion reporting.** Only after 0033F,
   commercial disclosure, consent, fraud, attribution, and data-sharing review.
6. **Phase 5: account-linked analytics.** Only after 0033C identity/storage
   decisions and explicit user/account controls.
7. **Phase 6: dashboards and lifecycle operations.** Add retention jobs,
   deletion/export support, access reviews, incident response, and audits.

## Testing and validation strategy

Future implementation should use mock event sinks only in normal validation:

- schema accepts only allowlisted event names and bounded dimensions;
- free text, secrets, prompts, provider bodies, recipe content, tokens, paths,
  and sensitive fields are rejected or redacted;
- anonymous, pseudonymous, account-linked, operator, and commercial modes are
  isolated by contract;
- timer warnings/expiry and AI budget/unavailable outcomes produce only safe
  categories;
- duplicate, late, out-of-order, and abandoned workflow events aggregate
  deterministically;
- small cohorts are suppressed and retention/deletion jobs are testable with
  an injected clock;
- opt-out/withdrawal prevents optional events and does not break core product
  use;
- export/delete covers raw, derived, lookup, backup, and vendor-boundary data;
- normal mock/offline validation makes no external analytics or provider calls.

## Explicit non-goals

This ADR does not implement analytics, event collection, dashboards, cookies,
pixels, beacons, fingerprinting, browser scripts, analytics vendors, ad
tracking, conversion tracking, marketing attribution, database migrations,
public routes, production auth, SSO/BYOS, payment, monetization, timer
enforcement, AWS/platform work, or live provider calls.
