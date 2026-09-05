# 0034Y Recipe Revision Identity Preservation

## Goal

Prevent a follow-up edit to an existing Cookbook AI draft from silently
changing the recipe into a different dish.

## Observed failure

A rigatoni pasta bake retained its pasta title and ingredients after the user
asked to add a vegetable, but its instructions changed to rice-and-soup
casserole directions. The invalid response was displayed and consumed one of
the recipe's ten changes.

## Required behavior

- Tell the provider that the current dish identity, base starch, protein, and
  cooking method are locked unless the user explicitly changes them.
- Change only what the follow-up requests and return a complete coherent draft.
- Validate a revision before committing it to the session.
- Reject a revision when its instructions omit an established dish anchor or
  introduce a conflicting dish anchor that was neither present nor requested.
- Treat identity drift as a safe, retryable unavailable result so the existing
  bounded core retry can recover once.
- A rejected revision must preserve the prior draft, context, revision count,
  and ten-change allowance.
- Explicit substitutions, such as replacing pasta with rice, must remain
  possible.

## Validation

- Add regression coverage for the reported pasta-to-rice/soup drift.
- Cover a valid vegetable addition and an explicit base substitution.
- Run sidecar tests and repository validation.
- Validate Compose and deploy a versioned sidecar image for a safe live smoke.

## Boundaries

- Do not change recipe ownership, persistence, authentication, or the core
  application's session model.
- Do not add Redis, Protocol Buffers, asynchronous jobs, AWS, or new public
  ingress.
- Do not record prompts, generated recipes, profile data, tokens, cookies,
  credentials, or local environment values in results.
