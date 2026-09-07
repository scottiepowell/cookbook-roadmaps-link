# 0035I Ingredient Quantity Sanity and Scaled Grammar Results

## Result

Complete. This sidecar-only increment keeps existing 0035H follow-up,
replacement, coherence, retry, and explicit-save behavior intact.

## Changes

- Added narrow deterministic singular/plural normalization for tablespoon,
  teaspoon, cup, clove, and common onion/egg/mushroom count nouns.
- Added conservative normalization of clearly excessive newly added mushroom
  quantities in baked-ziti/pasta-bake drafts, retaining the ingredient and an
  estimate note. Explicit extra/mushroom-heavy requests are left to the
  provider within existing guards.
- Added focused unit and scaling tests and updated mailbox/status documentation.

## Validation

- Focused scaling and session tests: passed (77 tests).
- Live provider/browser checks: skipped; offline/mock validation only.
- External core: unchanged.
- Grounding/RAG behavior: unchanged.

No secrets, prompts, raw provider output, cookies, tokens, session values,
local paths, browser artifacts, database paths, or ignored runtime files were
staged.
