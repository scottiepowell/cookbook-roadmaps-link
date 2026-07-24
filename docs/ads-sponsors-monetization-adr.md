# ADR: Ads, Sponsors, and Monetization

## Status

Proposed, docs/research-only (`0033F`)

## Date

2026-07-24

## Decision summary

Do not implement monetization in this task. If Cookbook AI grows enough to need cost recovery, explore the least intrusive channel that can cover a measured share of operating costs while preserving the recipe workflow and user trust. Start with direct, manually managed, clearly disclosed placements or voluntary support; evaluate an ad network only after the privacy and consent posture from `0033D` is ready. Paid access, subscriptions, and entitlement enforcement remain a separate future decision.

The principles are cost recovery first, not dark-pattern revenue maximization; no deceptive placements; no undisclosed sponsorships or affiliate incentives; no interference with the core recipe workflow; no selling private recipe text, prompts, provider outputs, BYOS contents, or sensitive user data; privacy-aware analytics only; no override of AI safety or citation quality; and respect for future SSO/BYOS data ownership.

This ADR adds no ads, affiliate links, sponsorship slots, payments, subscriptions, third-party scripts, SDKs, cookies, pixels, beacons, routes, provider changes, migrations, or runtime tracking.

## Context and cost-recovery goals

The product may eventually incur variable costs when users consume live AI or storage-heavy workflows. The goal is to recover a reasonable, documented share of those costs and the minimum support burden needed to keep the service reliable. Revenue is not a reason to increase AI usage, retain more user data, or make the free recipe experience worse.

Expected cost drivers are hosting and bandwidth; AI provider calls, tokens, retries, and bounded live-workflow capacity; recipe, export, backup, and operational storage; privacy-aware analytics and reporting; backups, restore testing, and retention operations; monitoring, alerting, abuse prevention, and incident response; and user support, moderation, policy review, and sponsor administration.

Future cost modeling should use low/base/high ranges rather than false precision. For each workflow, estimate fixed cost plus variable cost per completed live session, storage unit, backup unit, and support case. Break-even must include provider-budget headroom, privacy/compliance work, and operator time.

## Options considered

| Option | Potential value | Risks and guardrails |
| --- | --- | --- |
| Display ads | Broad, low-touch revenue without direct user payment | Low yield at small scale; clutter; third-party tracking/consent; brand-safety mismatch. Prefer only a small static/banner area on landing or product pages, never over controls or recipe steps. |
| Sponsorships | Direct relationship and better fit for cooking tools, ingredients, or education | Sponsor influence and disclosure failure. Use fixed terms, clear labels, approval/rejection rights, and no editorial or AI-quality control. |
| Partner placements | Useful optional tools or services | Can look like a recommendation or endorsement. Label the commercial relationship at the placement and explain any material incentive. |
| Affiliate-style links | Performance-based recovery from optional equipment/ingredient suggestions | Disclose the incentive; keep links optional, relevant, and outside generated recipe instructions. |
| Premium/supporter options | Voluntary support and a possible future cost-aligned tier | Payment, tax, entitlement, support, and accessibility complexity. Requires a separate payment/entitlement ADR. |
| Donations | Simple voluntary support signal | Payment processor, donor privacy, tax language, and recurring-support expectations. No pressure or fake goals. |
| Creator partnerships | Trusted education, collections, and audience reach | Disclosure, rights, claims, conflicts, moderation, and AI-generated endorsement risk. Require written terms and human review. |
| Newsletter sponsorship | Predictable, bounded inventory outside the recipe workflow | Email consent, unsubscribe, sponsor review, and audience-data sharing. Never sell the list. |

No option is approved for implementation. Direct sponsorships, optional affiliate-style suggestions, creator partnerships, donations, or newsletter sponsorships are the most plausible low-complexity experiments; programmatic display ads are later because of privacy, safety, and UX costs.

## Trust, disclosure, and content quality

Every commercial relationship must be disclosed where a user sees the placement, in plain language identifying the commercial nature and any material incentive. Labels such as `Advertisement`, `Sponsored`, `Paid partnership`, or `Affiliate link` are preferable to ambiguous labels such as `Featured`, `Recommended`, or `Promoted` when those labels could hide the relationship. The disclosure must remain visible on mobile and near the content to which it applies; a general footer policy is not enough for native content.

This follows the high-level principles in the [FTC Native Advertising Guide](https://www.ftc.gov/business-guidance/resources/native-advertising-guide-businesses) and [FTC endorsement guidance](https://www.ftc.gov/news-events/topics/truth-advertising/advertisement-endorsements): commercial content should not appear independent or editorial when it is not, and material connections should be disclosed. This is general research, not legal advice; jurisdiction-specific review is required before launch.

Recipe and AI trust rules:

- sponsored content must be visually and semantically separate from ordinary recipes, citations, and user-owned content;
- a sponsor cannot buy a favorable AI answer, citation, ranking, safety classification, dietary claim, or recipe outcome;
- product claims require evidence and human review; do not imply testing or personal use that did not occur;
- partner recipe collections need provenance, ownership/permission review, and a partner label; and
- generated text must not silently become an endorsement or testimonial.

## Placement ideas that preserve the recipe workflow

Potentially acceptable, subject to later review:

- one non-intrusive banner on the landing or product-information page;
- a clearly labeled sponsored ingredient or tool card in an optional suggestions area, never inserted into required recipe steps;
- an optional affiliate link beside an equipment or ingredient suggestion, with disclosure adjacent to the link;
- a sponsor-supported pool of free AI sessions, described as funding rather than as a reason to bypass budget controls;
- a clearly labeled newsletter sponsorship;
- a disclosed creator/brand partner recipe collection; and
- a quiet support/donation link in an about, help, or footer area.

Do not place commercial UI between ingredient steps, beside primary submit/save controls, inside citations, in error/retry controls, over accessibility controls, or in a way that resembles navigation, a download, a required ingredient, or an AI answer. Google publisher guidance warns against misleading labels, accidental clicks, and layouts that interfere with navigation; its [publisher policies](https://support.google.com/adsense/answer/48182?hl=en) are a useful UX baseline even if no Google product is selected.

## Privacy, consent, and analytics

Monetization must not become a pretext for collecting more data. Do not monetize or disclose private recipe contents, raw AI prompts, provider outputs, BYOS cloud-storage contents, account identity data, OAuth tokens or provider metadata, children/minor data, sensitive health/dietary details, or private support information. Never sell a user list or build cross-site profiles from recipe activity.

The `0033D` analytics ADR remains authoritative for event minimization, retention, deletion, consent, and commercial-event separation. A future commercial measurement design must define placement, purpose, consent state, attribution window, fraud controls, sponsor recipients, retention, and deletion before collecting `ad_impression`, `ad_click`, `sponsor_click`, or `conversion`. These events must not contain recipe text, prompts, outputs, private storage identifiers, precise location, or sensitive dietary details.

Non-essential cookies, pixels, SDKs, fingerprinting, local storage used for tracking, and similar technologies require a separate implementation and privacy review. The [ICO cookies guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/) states that users should be told what such technologies do and generally give active consent, with only narrow strict-necessity exceptions. A cookieless server-side click count can still be personal-data processing when linkable to an account, device, or session. Prefer aggregate, short-retention, first-party measurement, and do not load optional trackers before the required choice.

For direct links, a future implementation may use a simple destination URL without behavioral tracking, or a documented first-party redirect only after the analytics/privacy decision is approved. Do not add hidden UTM identifiers, third-party pixels, or affiliate network scripts as an experiment.

## Relationship to SSO/BYOS and AI controls

SSO identifies an account; BYOS is user-authorized storage. Neither is an ad audience. Commercial systems must not receive provider emails, OAuth subjects, tokens, cloud file names, storage paths, or file contents. A user who declines optional commercial measurement must retain core access and local/offline fallback where promised.

Ads or sponsorship cannot grant extra live AI calls, raise token caps, bypass the 0033B timer, bypass operator/invite authorization, or override the global provider kill switch. The provider-budget guard remains authoritative and fail-closed. A sponsor-supported free-session pool is an accounting concept that must still honor per-call, per-session, global, and abuse limits. Monetization must not infer payment or entitlement from an access grant or session token.

## Staged experiment plan

1. **Phase 0: ADR only.** Record goals, cost drivers, options, trust rules, prohibited data, and gates.
2. **Phase 1: cost model and break-even estimates.** Use bounded synthetic or aggregate operational assumptions and low/base/high scenarios.
3. **Phase 2: static sponsorship/affiliate disclosure policy.** Draft labels, placement rules, review checklist, claims policy, rights terms, and a takedown/kill procedure. No links or slots need to be live.
4. **Phase 3: one manually managed sponsor or affiliate experiment.** Select one low-risk static placement, time-box it, review it manually, and measure only approved aggregate outcomes without trackers.
5. **Phase 4: privacy-aware analytics for impressions/clicks.** Only after `0033D` decisions are implemented and consent, retention, deletion, attribution, and vendor boundaries are approved.
6. **Phase 5: ad network evaluation.** Only after consent/privacy posture, content/brand-safety review, accessibility checks, and third-party risk review are ready. Evaluation does not authorize SDKs or scripts.
7. **Phase 6: premium/supporter model.** Only after a separate payment/entitlement ADR covers pricing, taxes, refunds, support, access, data boundaries, and failure handling.

## Go/no-go criteria

Go requires a documented cost-recovery hypothesis and bounded experiment; adjacent disclosures and a commercial policy; content, claims, rights, accessibility, and brand-safety review; no impact on recipe steps, citations, safety messaging, or core controls; a privacy/data-flow review covering consent, recipients, retention, deletion, and minimization; approved aggregate measurement and fraud controls; and a tested stop/kill switch with a named owner that cannot disable AI safety or provider-budget controls.

No-go if the proposal requires undisclosed influence, sensitive-data sharing, cross-site profiling, default-on non-essential tracking, deceptive UI, unbounded AI subsidy, unsafe product claims, route/provider changes, or a payment/entitlement system without its own ADR.

## Explicit non-goals

- ads, affiliate links, sponsorship slots, donations, payments, subscriptions, or premium/supporter runtime;
- ad network SDKs, third-party scripts, cookies, pixels, beacons, or trackers;
- database migrations, new public routes, provider routing, AWS/platform work, or production storage;
- selling or licensing private recipe text, prompts, provider outputs, BYOS contents, identity data, OAuth tokens, provider metadata, minor data, or sensitive health/dietary details;
- undisclosed AI-generated endorsements, fake scarcity, dark patterns, or incentivized ad clicks; and
- live OpenAI or external-provider calls during research or validation.

## Consequences

This keeps the near-term product free/basic-access oriented and makes cost recovery measurable without coupling revenue to private user data or AI quality. There is no revenue today, no guarantee any channel will cover costs, and future work carries policy, privacy, accessibility, support, and operational overhead. Each implementation must return to this ADR and the relevant analytics, identity/BYOS, timer, AI-budget, and payment decisions before shipping.
