# 0035C Public AI Clean Recipe Replacement

## Goal

Turn a confirmed dish replacement into a clean recipe session using only the
proposed new idea.

## Required behavior

- Preserve the current draft until replacement is confirmed.
- Accept the visible controls or bounded typed yes/no confirmation.
- Permit a richer replacement description while confirmation is pending.
- On confirmation, discard the browser's current in-memory draft and start a
  new sidecar session from the proposed idea.
- Treat `start a new recipe with ...` as an immediate clean restart.
- Do not carry old dish identity, base starch, protein, method, ingredients, or
  instructions unless the new idea explicitly repeats them.

## Validation

- Cover typed confirmation, explicit restart parsing, proposed-idea extraction,
  and distinct core-owned chat handles.
- Verify repeated replacement can move from an omelet to a pasta bake and then
  fried rice without mutating either prior draft.

## Boundaries

- Replacement discards only bounded in-memory chat state; canonical recipes are
  not created, changed, or deleted.
- Retain all authentication, secret-handling, provider-budget, and private
  sidecar boundaries.
