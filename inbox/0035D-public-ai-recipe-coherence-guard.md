# 0035D Public AI Recipe Coherence Guard

## Goal

Reject provider drafts whose title, major ingredients, and instructions clearly
describe incompatible dishes.

## Required behavior

- Reject pasta-bake drafts that retain omelet-only directions.
- Reject fried-rice drafts whose directions never use rice or a frying,
  stir-fry, skillet, or wok action.
- Reject a non-omelet draft that retains an explicit omelet instruction anchor.
- Require clearly named major base starches and proteins to appear in the
  instructions for the guarded dish families.
- Use the existing safe retryable/transactional failure path so a rejected
  revision preserves the prior draft, requirements, successful-change count,
  and remaining allowance.

## Validation

- Add direct deterministic guard cases and a route-level transactional
  regression for stale omelet directions under a pasta-bake title.
- Run the full offline suite and evaluations without live provider calls.

## Boundaries

- Do not log or persist provider output rejected by the guard.
- Do not weaken existing identity, scaling, transaction, authentication,
  budget, or no-save controls.
