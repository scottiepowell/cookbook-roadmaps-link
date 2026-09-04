# 0034X Public AI Initial Request Resilience Results

Status: complete and deployed.

## Result

Initial public recipe generation now has the same bounded transient recovery
shape as recipe revisions without introducing duplicate recipe sessions.

- Core creates one opaque request ID and sends it as both the sidecar
  idempotency key and safe trace ID.
- A transport failure or sidecar `503` explicitly marked retryable receives at
  most one retry with the identical request body and key.
- Both attempts share a 45-second total deadline; each attempt is bounded to 22
  seconds.
- Deterministic failures remain no-retry.
- Sidecar serializes matching initial keys, returns completed sessions on
  replay, resumes the same uncommitted session after a failed attempt, and
  rejects conflicting key reuse.
- OpenAI clients are shared within the sidecar process by a safe key
  fingerprint and timeout configuration, enabling HTTP connection pooling.
- Safe structured timing events separate retrieval, provider, validation,
  total sidecar, and core proxy duration without request or identity data.
- Provider-attempt capacity is 22: two initial attempts plus two attempts for
  each of ten successful changes. Existing cost ceilings remain enforced.

## Validation

- Sidecar focused tests: 38 passed.
- Sidecar full validation: 430 tests and 39 offline evaluations passed; all
  repository checks passed.
- Core focused AI/homepage tests: 17 passed.
- Core Svelte diagnostics: 0 errors and 0 warnings.
- Core changed-file formatting: passed.
- `git diff --check`: passed in both workspaces.
- Public Compose config: passed using ignored environment files without
  displaying their values.
- Images built: `local/vanilla-cookbook-adapter:0034x` and
  `local/cookbook-ai-sidecar:0034x`.
- Runtime: sidecar healthy, public core running, public health and homepage
  returned HTTP 200, neither app publishes a host port, and the existing
  Cloudflare connector was not recreated.

## Safe live evidence

One funded `gpt-5.4-nano` initial generation and one immediate replay used the
same opaque key. Safe outcomes were: initial accepted, replay accepted, same
session, draft present, revision zero, model pin correct, and exactly one
provider stage. Recorded stage durations were approximately 0.9 seconds for
retrieval, 8.4 seconds for provider generation, less than 0.1 milliseconds for
schema validation, and 9.3 seconds total. No retry was required for this live
call.

No prompt, recipe output, credential, token, cookie, OAuth artifact, user
profile, provider response, or local environment value is recorded.

The external core change is committed locally on
`openclaw/0034X-public-ai-initial-resilience` at
`fad0011453f3930d09e1f64b0b19992b3db27e52`. It is not pushed to the
third-party core remote. The sidecar completion commit owns the mailbox,
deployment configuration, tests, documentation, and result record.
