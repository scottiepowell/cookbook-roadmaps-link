# Product Priority Roadmap After 0032A

## Decision

AWS infrastructure work should move to a separate portfolio-platform repository and separate effort. The platform will eventually hotel multiple unrelated apps and has at least two layers:

```text
Portfolio platform layer
  - shared hosting and deployment model
  - app registry and metadata
  - health, usage, cost, and observability
  - shared identity/session strategy when appropriate
  - shared provider policy and budget controls

Individual app/product layer
  - Cookbook AI and Vanilla Cookbook integration
  - application-specific UX and workflow validation
  - application-specific access controls and timers
  - application-specific identity/storage decisions
  - analytics, marketing, and monetization decisions
```

The Cookbook repo should not start AWS/IaC implementation from `0032A`. The next work should focus on product usability, app integration, access/session behavior, identity/storage strategy, analytics, marketing, and monetization.

## Current priority order

1. **Manual validation of AI sidecar and Vanilla Cookbook integration**
   - Main effort.
   - Focus on production usability and what the integrated app feels like end to end.
   - Expect follow-on tasks to emerge from the validation.

2. **30-minute application timer with user exceptions**
   - Investigate a 30-minute access/session timer for the application.
   - Include a way to turn the timer off or bypass it for certain users/operators.

3. **SSO and BYOS identity/storage ADR**
   - Investigate Google/Facebook/email registration style account access.
   - Investigate BYOS: users saving their own data to their own cloud storage such as Google Drive, Dropbox, or similar providers.
   - Goal is persistence without the app becoming the primary long-term owner of user data.

4. **Traffic, behavior, and visitation tracking ADR**
   - Investigate what people click, which features they use, ad interactions, visit/session metrics, and funnel behavior.
   - Must include privacy, consent, disclosure, retention, and safe analytics boundaries.

5. **Marketing ADR**
   - Investigate ways to market the website.
   - One idea is using transcripts from popular cooking YouTube videos to create thoughtful, curated, AI-assisted comment drafts that could promote the website to people reading comments.
   - This must be investigated carefully: the ADR should distinguish human-reviewed, policy-compliant community engagement from spam, automation, undisclosed promotion, or platform-policy violations.

6. **Ads, sponsors, and monetization ADR**
   - Investigate ads, sponsors, partner placements, affiliate-style links, and other monetization options.
   - Goal is to cover infrastructure/support costs if the website grows and users utilize live AI or storage-heavy workflows.

## Boundaries

- Do not create AWS resources from this repo.
- Do not add Terraform/CDK/CloudFormation here.
- Do not implement public production identity, analytics, ads, or monetization without separate approved tasks.
- Do not weaken existing mock/offline validation.
- Do not run live OpenAI during normal validation.
- Do not expose provider keys, prompts, raw provider output, local env values, screenshots, traces, raw datasets, or generated indexes.

## Immediate next task

`0033A-manual-product-integration-usability-validation` should be the next active Cookbook task. It should manually validate the current local product integration and identify the next concrete production-usability gaps before new feature implementation begins.

## 0033A validation emphasis

The manual validation should exercise `/product`, `/product/cookbook`,
`/product/ai`, `/demo`, readiness, importer, Ask My Cookbook, Dataset Ask,
Meal Planner, and Recipe Session in mock/offline mode. Prioritize gaps in
navigation, shared visual and interaction states, accessibility, responsive
behavior, and the visible split between the upstream Cookbook container and
the sidecar workspace. Live importer acceptance remains explicit,
operator-approved, one-call bounded, and outside normal validation.

## 0033B timer ADR emphasis

The next app-level design is the [Application Session Timer and Access
Exceptions ADR](application-session-timer-access-exceptions-adr.md). It
investigates a friendly server-authoritative 30-minute session, safe expiry,
and explicit operator/trusted/invite exceptions while keeping timer state
separate from provider budgets. No runtime enforcement or production auth is
introduced by the ADR.

## 0033C identity/storage ADR emphasis

The next app-level design is the [SSO and BYOS Identity/Storage Architecture
ADR](sso-byos-identity-storage-architecture-adr.md). It investigates email and
external identity providers separately from user-owned cloud storage, with
portable data, least-privilege scopes, revocation/deletion behavior, and local
fallback as first-class requirements. No auth or storage integration is added.

## 0033D analytics ADR emphasis

The next app-level design is the [Traffic Analytics and Behavior Tracking
ADR](traffic-analytics-behavior-tracking-adr.md). It investigates privacy-
respecting aggregate measurement, event taxonomy, consent, retention,
deletion, and vendor tradeoffs. No tracking implementation is added; ads,
sponsors, and conversions remain deferred to the future monetization ADR.

## 0033E marketing ADR emphasis

The next app-level design is the [Website Marketing and Community Outreach
ADR](website-marketing-community-outreach-adr.md). It evaluates useful,
transparent marketing and the cooking-video transcript/comment idea without
approving scraping, automation, mass commenting, fake engagement,
impersonation, or undisclosed promotion. Safer owned-content and human creator
outreach options remain the preferred exploration path.

## 0033F monetization ADR emphasis

The [Ads, Sponsors, and Monetization ADR](ads-sponsors-monetization-adr.md)
keeps monetization focused on bounded cost recovery, transparent disclosures,
privacy-aware measurement, recipe-content trust, and future SSO/BYOS data
ownership. It evaluates ads, sponsorships, partner placements, affiliate-style
links, donations, supporter options, newsletters, and creator partnerships
without implementing any of them. Payment, subscriptions, premium access,
third-party scripts, and ad-network evaluation remain separately gated.

## 0033I product Cookbook link correction emphasis

The [Local Cookbook AI Product Integration](local-cookbook-ai-product-integration.md)
handoff now distinguishes the local Compose target from an exposed Cookbook
URL through the safe non-secret `COOKBOOK_TARGET_URL` setting. The sidecar
continues to own `/product` and `/demo`, `/product/ai` remains a redirect to
`/demo`, and the upstream Cookbook remains an external link rather than a
proxy or rewrite.

## 0033K local Cookbook runtime emphasis

The local integration now has a separate app-only Docker Compose path bound to
`127.0.0.1:3000`, with ignored disposable database/uploads and no
`cloudflared`, AWS, GitHub Actions, or production secrets. This local runtime
unblocks future `0033J` adapter schema discovery and disposable write tests;
it does not implement Save to Cookbook or production write-back.
Docker Desktop verification confirmed the app-only local path and HTTP
response. Prior Coder asset inspection found no Vanilla Cookbook-specific
files to reuse; production AWS/Cloudflare remains separate.

## 0033J Save-to-Cookbook adapter design

The proposed importer handoff is documented in
[AI Importer Save-to-Cookbook Adapter Design](ai-importer-save-to-cookbook-adapter-design.md).
It preserves Vanilla Cookbook as canonical owner and requires a bounded
candidate contract, schema discovery, user review/edit/confirmation,
idempotency, duplicate detection, backup/rollback, and disposable local tests
before any write implementation. This task adds no Save-to-Cookbook button,
endpoint, database mutation, or production write-back; the verified local
runtime is only a future discovery/test target.

## 0033M fixture contract

Phase 1 now has a pure in-memory adapter contract and offline tests. The
contract maps validated AI importer drafts to a versioned candidate payload and
returns safe validation, duplicate, schema-version, and idempotency results.
It does not inspect or mutate the Vanilla Cookbook database, add routes or UI,
or contact a provider. The upstream write schema remains an explicit blocker
before disposable write/rollback testing.
