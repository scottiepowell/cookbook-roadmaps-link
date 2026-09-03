# 0034V - Transactional AI Recipe Revisions

## Trigger

Public browser observation found that three failed attempts to add an
ingredient were displayed as messages and consumed three change slots. A later
successful request changed a different ingredient, but the previously requested
ingredient was absent from the draft.

## Goal

Make recipe revisions transactional: only a successfully generated draft may
advance the recipe requirements and ten-change counter.

## Required behavior

- A provider, validation, timeout, or network failure must retain the current
  draft, requirements, retrieval state, and revision count.
- Return a bounded retryable flag for transient sidecar failures and permit one
  identical core-owned retry.
- Do not retry deterministic authorization, quota, configuration, model, schema,
  payload, or budget failures.
- Failed UI attempts must not remain as successful-looking user messages; restore
  the requested text to the composer so the user can retry or edit it.
- Preserve the existing budget-exhaustion response while leaving the revision
  and requirements unchanged.
- Increase the public structured-output allowance enough for full recipe
  revisions and reserve provider-call capacity for one retry per allowed change.
- Preserve `gpt-5.4-nano`, the ten-successful-change product limit, the cost cap,
  core ownership, private sidecar boundary, and no-save behavior.

## Acceptance

- Regression tests prove a failed provider generation does not mutate session
  state and one retryable core request is retried with an identical body.
- Repository/core validation, image builds, Compose checks, safe runtime smoke,
  deployment, documentation, commit, and push complete without recording user
  prompts, drafts, secrets, tokens, cookies, sessions, or provider output.
