# 0035G Five Retries and Empty Prompt Guard Results

## Result

Complete and deployed.

Initial recipe generation and follow-up changes now permit five bounded retries
after the initial request, for at most six attempts inside a shared 135-second
deadline. Retryable attempts retain the identical request body, and initial
generation retains its opaque idempotency key. Deterministic failures still
stop after one attempt.

The browser and both authenticated core endpoints now use the same prompt
cleaning boundary. Empty, whitespace-only, and invisible-format-character-only
input stops before rate limiting, sidecar calls, or provider work. Invalid API
responses report zero retries against the five-retry ceiling.

## Safe outcomes

- Maximum bounded retries: 5.
- Maximum total attempts: 6.
- Shared total deadline: 135 seconds.
- Initial sixth-attempt recovery: passed.
- Follow-up sixth-attempt recovery: passed.
- Identical retry body preserved: yes.
- Initial idempotency key preserved: yes.
- Deterministic failures remain no-retry: yes.
- Empty initial prompt sidecar calls: 0.
- Empty follow-up sidecar calls: 0.
- Empty and invisible-only public send action disabled: yes.
- Public provider calls during browser verification: 0.
- Existing draft/change transactionality preserved: yes.
- Public health: 200.
- Public core image: `local/vanilla-cookbook-adapter:0035g`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035d`.

## Validation

- Focused core AI proxy, draft-save, and entry tests: 22 passed.
- Core production Docker build: passed.
- Sidecar repository validator: 468 passed.
- Offline evaluations: 39 passed.
- Compose configuration and diff checks: passed.
- Public container startup and HTTPS health: passed.
- Signed-in browser verification: blank and invisible-only input remained
  disabled, no thinking state began, and the core recorded no AI-start event.

Existing build warnings about Browserslist age, CSS `@property`, and the
SvelteKit/Svelte export combination remain. Core startup also reports the
existing non-fatal permission warning while rewriting an unused `.svelte-kit`
service-worker copy; public health reaches 200.

No prompt, provider output, identity data, credential, token, cookie, session
value, environment value, database path, or browser artifact is recorded or
staged.

## Delivery

The external core change is committed locally on
`openclaw/0035G-five-retries-empty-input` at
`b6012725c0aa619475f74840fe04da0bbe104cf4`. The third-party upstream core
repository is not pushed. The 0035G mailbox, documentation, Compose pin, and
safe results are committed and pushed in `scottiepowell/cookbook-roadmaps-link`.
