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

## 0033N dry-run candidate operation

Phase 2 adds a disabled-by-default internal service wrapper around the fixture
adapter. Explicit local callers can exercise mapped payloads, validation,
duplicate, idempotency, and schema-version results without Docker or storage.
No HTTP route or commit path was added; a future review UI remains gated on
Phase 3 disposable schema and rollback evidence.

## 0033O local schema discovery

Read-only inspection of the disposable runtime found the upstream Prisma/SQLite
Recipe model: UUID recipe IDs, required owner/time fields, text ingredients,
directions and servings, relational categories, separate photos, and an
authenticated native create/update/delete API. Exact serialization, category
ownership, transaction/rollback, and safe adapter handoff remain unknown, so
Phase 3 disposable write testing is still blocked. No rows or uploads were
modified.

## 0033P write-readiness plan

The schema-informed plan narrows a future disposable write test to one
synthetic local owner and one recipe, with deterministic text ingredient/
direction serialization, string servings, safe provenance, and no categories,
media, uploads, or embeddings. It defines backup/restore, cleanup,
duplicate/idempotency, failure injection, and strict localhost guards. This is
planning only; Phase 3 remains blocked and no harness or write was added.

## 0033Q local readiness evidence

The local-only 0033Q harness provides disposable evidence for the narrow first
write scope: synthetic owner, one recipe, deterministic text fields,
backup/restore, rollback injection, duplicate/idempotency checks, and local
read-after-write. It requires explicit approval and loopback `cookbook-local`
only. Native adapter/UI work and production write-back remain gated on a
separate reviewed task.

## 0033R local backend integration

The local-only commit service is now available as a disabled-by-default,
in-memory backend boundary with explicit approval, loopback, Compose, runtime,
and synthetic-owner guards. It preserves the readiness harness evidence and
does not expose a route or call the native authenticated upstream API. A future
UI/native adapter task remains required before any broader save behavior.

## 0033S local UI MVP

The AI demo now includes a visibly local-only review/dry-run/commit panel for
importer drafts. It requires explicit non-secret local gates, never calls the
native upstream API, and exercises only the 0033R in-memory service. The 0033Q
readiness harness remains the approved disposable DB/write path; production or
exposed Save-to-Cookbook remains unimplemented.

## 0033T native local save spike

The native local save attempt remains blocked: the upstream create route needs
Lucia session ownership and has post-create image/embedding side effects
without a safe adapter rollback contract. No session values or native route
calls were used. The local UI simulation and disposable readiness harness stay
the approved boundaries.

## 0033U core adapter path decision

Save-to-Cookbook remains prototype-only. The decision recommends a 0033W
follow-up to bootstrap a source-owned/forked Vanilla Cookbook core workspace and custom local image;
the 0033V workspace plan is documented in
[Source-Owned Vanilla Cookbook Adapter Workspace Plan](source-owned-vanilla-cookbook-adapter-workspace-plan.md).
0033W completed that external recursive checkout and local image bootstrap;
0033X completed the external core-owned no-mutation dry-run adapter and 0033Y
added the authenticated dry-run route, building and verifying the opt-in
`0033y` image on loopback. The next task must review the authenticated commit
boundary; production Save-to-Cookbook remains unimplemented.
or adopt a verified upstream plugin/API hook with equivalent ownership and
transaction guarantees. Direct sidecar DB writes and browser/session
automation are rejected; production save remains unimplemented.
