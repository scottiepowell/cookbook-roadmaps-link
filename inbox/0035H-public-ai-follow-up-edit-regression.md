# 0035H Public AI Follow-Up Edit Regression

## Objective

Restore the public AI-first recipe-chat follow-up path for an existing draft.
Short serving adjustments, ingredient substitutions, and their compound form
must remain revisions of the displayed recipe rather than falling back to an
initial-request clarification.

## Required outcomes

- Preserve the existing core-owned chat-to-sidecar session binding.
- Treat ordinary serving updates, doubling, and ingredient substitutions as
  current-draft edits.
- Commit a compound serving-and-substitution revision only when the exact yield
  and the requested substitution both appear in a coherent candidate.
- Keep replacement confirmation and clean confirmed replacement behavior from
  0035B–0035D unchanged.
- Retain transactional behavior: an unsuccessful candidate leaves the draft and
  successful-change counter unchanged.

## Boundaries

No automatic save, sidecar identity/session ownership, database access,
canonical Cookbook write authority, live provider validation, or production
route expansion. Record only safe validation outcomes; do not commit runtime
secrets, tokens, cookies, prompts, provider output, browser artifacts, or
ignored runtime data.
