# 0034X Public AI Initial Request Resilience

## Goal

Make the first public recipe generation as resilient as transactional recipe
revisions without changing the model, public exposure, authentication, storage,
or ten-change product boundary.

## Required behavior

- Core generates one opaque idempotency key for an initial recipe request and
  sends the identical key and body on at most one bounded retry.
- Retry only a transport failure or a sidecar `503` explicitly marked
  retryable. Do not retry authentication, authorization, quota, rate-limit,
  model, schema, payload, or budget failures.
- Both attempts share one total deadline. Do not create an unbounded retry
  loop.
- Sidecar deduplicates the initial request key. A retry must return the existing
  completed session or resume the same uncommitted session; it must not create a
  second session or consume a second successful initial revision.
- Reusing an idempotency key with a different request must fail safely.
- Reuse the OpenAI HTTP client within one sidecar process so successive calls
  can reuse pooled connections.
- Emit safe stage and proxy timings with only opaque IDs, durations, attempt
  counts, status, provider/model names, and bounded failure categories. Never
  log prompts, recipes, secrets, cookies, OAuth artifacts, profile data, or raw
  provider responses.

## Boundaries

- Keep `gpt-5.4-nano` pinned.
- Keep the sidecar private on the Docker network.
- Keep the warmed local 5,000-record retrieval index and current RAG behavior.
- Do not add Redis, Protocol Buffers, asynchronous jobs, EC2, AWS, another
  public route, or persistent user/chat storage in this task.
- Keep one initial generation plus ten successful recipe changes. Provider
  attempt capacity may increase only enough to permit one retry for the initial
  generation and one retry for each allowed change.

## Validation

- Add focused sidecar coverage for idempotent replay, retry after a failed
  initial attempt, conflicting key reuse, safe timing fields, and shared OpenAI
  client reuse.
- Add focused core coverage for identical retry bodies/keys, one-retry limit,
  deterministic no-retry behavior, and bounded public responses.
- Run sidecar repository validation, core focused tests and checks, Compose
  config, image builds, runtime health, `git diff --check`, and a safe public or
  container-level smoke.
- Record only safe boolean, counter, status, model, duration, and opaque-ID
  outcomes.
