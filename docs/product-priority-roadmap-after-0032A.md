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
