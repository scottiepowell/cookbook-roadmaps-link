# 0034Z Deterministic Recipe Serving Scaling

## Goal

Make recipe-session serving changes consistent across the displayed yield and
every numeric ingredient quantity.

## Observed failure

After a recipe was changed from its original yield to eight and then sixteen
servings, some ingredient quantities changed while the pasta amount did not,
and the final draft displayed the wrong serving count.

## Required behavior

- Recognize numeric and common written-number serving requests, including
  `change to eight servings`, plus explicit double/halve requests.
- The latest serving request must replace an older serving request in session
  requirements rather than allowing the earlier number to win.
- For a serving-only change, set the draft yield deterministically and scale
  every parseable numeric ingredient quantity by one common ratio from the
  current draft.
- Preserve ingredient names, units, ordering, and recipe identity during a
  serving-only change.
- Support integers, decimals, fractions, mixed numbers, ranges, and common
  Unicode fractions.
- Do not scale oven temperatures or cooking times linearly; provider-generated
  instructions may adjust batch/pan guidance.
- Enforce the explicit serving target before committing any revision.
- A failed serving invariant must leave the prior draft and ten-change count
  unchanged and be eligible for the existing one bounded retry.

## Validation

- Add regression coverage for chained 4 to 8 to 16 serving changes where the
  provider returns inconsistent yield and ingredient quantities.
- Cover written numbers, double/halve intent, fractions, mixed numbers, ranges,
  unquantified ingredients, and non-serving revisions.
- Run sidecar tests, offline evaluations, repository validation, Compose
  validation, image build/startup, and a safe public live smoke.

## Boundaries

- Do not change recipe persistence, ownership, authentication, or the core
  application session model.
- Do not add Redis, Protocol Buffers, asynchronous jobs, AWS, or new ingress.
- Do not record prompts, generated recipes, identity data, credentials, tokens,
  cookies, session values, environment values, or provider payloads.
