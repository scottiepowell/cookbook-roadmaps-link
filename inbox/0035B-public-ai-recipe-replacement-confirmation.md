# 0035B Public AI Recipe Replacement Confirmation

## Goal

Let users intentionally switch dishes from the recipe chat without weakening
the safeguards that preserve ordinary edits to the current recipe.

## Observed failure

A user working on an enchilada draft asked to change nonexistent pasta to rice,
then described a chicken-and-rice dish. Both messages fell into the generic
clarification path and the browser prevented a typed confirmation response.

## Required behavior

- Treat a staple substitution as a likely dish switch when the named source
  staple is absent from the current draft.
- Keep the same substitution as an ordinary edit when the source staple is
  present in the current draft.
- Recognize wording that asks to make the current dish more like another dish.
- Preserve the current draft and successful-change count while confirmation is
  pending.
- Ask whether to start a new recipe and discard the current draft.
- Recognize explicit switch, go-with, change-this, instead-do, scrap-and-make,
  and new-recipe wording before provider revision generation.

## Validation

- Cover context-aware staple replacement and dish-style switching in sidecar
  unit and route tests.
- Run sidecar tests, offline evaluations, focused core tests, core build,
  repository validation, Compose validation, image build/startup, and a safe
  public smoke.

## Boundaries

- Nothing is saved automatically; discarding affects only the bounded in-memory
  draft and chat.
- Do not expose prompt text, recipe content, provider payloads, identity data,
  credentials, tokens, cookies, session values, or local environment values in
  committed results or logs.
- Do not change authentication/session ownership, canonical recipe persistence,
  ingress, Redis, Protocol Buffers, asynchronous jobs, AWS, or provider budgets.
