# 0035G Five Retries and Empty Prompt Guard

## Goal

Increase transient recovery capacity for the public Cookbook AI recipe chat and
guarantee empty prompt submissions stop before the sidecar or provider path.

## Required behavior

- Permit up to five bounded retries after the initial attempt for retryable
  transport failures and explicitly retryable sidecar failures.
- Keep deterministic failures at one attempt.
- Retain the identical request body and initial idempotency key across retries.
- Enlarge the shared total deadline enough for six bounded attempts.
- Display the latest request's retry usage as `0 of 5` through `5 of 5`.
- Treat empty, whitespace-only, and invisible-format-character-only initial or
  follow-up prompts as invalid before rate limiting, sidecar calls, or retries.
- Keep the draft and successful-change count unchanged after rejected or failed
  follow-ups.

## Boundaries

- Keep the existing live model, provider budget guards, authentication, rate
  limits, recipe-session ownership, and ten-change limit.
- Do not retry deterministic configuration, authorization, quota, schema,
  payload, or rate-limit failures.
- Do not add sidecar database access, browser identity forwarding, or automatic
  recipe persistence.
- Do not record prompt content, provider output, identity data, credentials,
  tokens, cookies, session values, or local environment values.

## Validation

- Prove sixth-attempt recovery and the five-retry ceiling for initial and
  follow-up requests with identical request bodies.
- Prove empty and invisible-only input returns zero retries and makes no sidecar
  call.
- Run focused core regressions, the production core build, repository
  validation, Compose validation, and diff checks.
- Deploy a pinned public core image and verify the signed-in UI disables an
  empty send action; verify the invalid server response reports `0 of 5`
  without making a provider call.
