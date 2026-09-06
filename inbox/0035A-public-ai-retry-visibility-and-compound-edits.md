# 0035A Public AI Retry Visibility and Compound Edits

## Goal

Make public recipe-chat recovery visible and make one follow-up reliably apply
multiple compatible changes to the current recipe.

## Observed failure

After an omelet draft was created, `add potato's and double the servings`
returned the initial-request clarification instead of revising the existing
draft. The user also had to resubmit repeatedly without being able to see
whether the bounded automatic retry policy had been exercised.

## Required behavior

- Permit up to three bounded automatic retries for retryable transport and
  explicitly transient sidecar failures, for four total attempts.
- Keep the request body and idempotency key identical across every retry.
- Never retry authorization, quota, validation, rate-limit, or other
  non-retryable failures.
- Return only a safe retry count and maximum retry count to the browser.
- Display `0 of 3 bounded retries used` (or the actual count) immediately below
  the successful-change count for the latest request.
- Recognize additive and serving language as a relevant requirement update.
- When a valid draft already exists, do not fall back to the initial vague-idea
  clarification merely because a relevant compound follow-up lacks a dish name.
- Apply an additive ingredient change and an explicit serving change from the
  same prompt transactionally. The successful draft must contain the requested
  ingredient, use the exact requested yield, and consistently scale existing
  numeric ingredient quantities.
- A failed attempt or exhausted retry sequence must preserve the prior draft
  and successful-change count.

## Validation

- Cover success on the fourth attempt, exhaustion after four attempts,
  identical retry bodies and idempotency keys, non-retryable failures, and
  zero/three retry response metadata.
- Regress the reported omelet flow, including apostrophe-tolerant potatoes and
  doubling servings in one message.
- Run sidecar tests, core proxy/UI tests and build, repository validation,
  Compose validation, image build/startup, and a safe public live smoke.

## Boundaries

- Do not expose prompt text, generated recipes, provider payloads, identity
  data, credentials, tokens, cookies, session values, or local environment
  values in committed results or logs.
- Do not change recipe persistence, auth/session ownership, ingress, Redis,
  Protocol Buffers, asynchronous jobs, AWS, or production save behavior.
