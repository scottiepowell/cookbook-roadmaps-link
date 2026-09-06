# 0034Z Deterministic Recipe Serving Scaling Results

## Result

Complete and deployed.

The latest explicit serving request now takes precedence over older serving
numbers in the session history. Serving-only changes set the yield and scale
every parseable numeric ingredient quantity deterministically from the current
draft by one common ratio. Ingredient names, units, ordering, and recipe
identity are preserved while generated instructions may adapt non-linear pan,
batch, and timing guidance.

Numeric and written serving counts are supported, as are bounded double and
halve requests. Mixed serving/content edits must return the exact requested
yield or fail transactionally with the safe retryable category
`serving_scale_mismatch`.

## Safe verification outcomes

- Latest serving request replaced prior request: yes.
- Written serving count recognized: yes.
- Double and halve requests recognized within the 1-24 bound: yes.
- Integer quantities scaled: yes.
- Decimal quantities scaled: yes.
- Fraction and mixed-number quantities scaled: yes.
- Range quantities scaled: yes.
- Unicode fractions scaled: yes.
- Unquantified ingredients preserved: yes.
- Wrong provider yield overridden for serving-only change: yes.
- Wrong provider yield rejected for mixed change: yes.
- Rejected mixed change preserved prior draft and count: yes.
- Public 4-to-8 yield change succeeded: yes.
- Every quantified public ingredient doubled at 8 servings: yes.
- Public 8-to-16 yield change succeeded: yes.
- Every quantified public ingredient doubled again at 16 servings: yes.
- Final public yield was 16, not 2: yes.
- Public successful-change count advanced exactly twice: yes.
- Public unavailable state absent: yes.
- Public core remained running: yes.
- Public tunnel remained running: yes.
- Sidecar image: `local/cookbook-ai-sidecar:0034z`.
- Sidecar health: healthy.

No prompt text, generated recipe content, identity data, browser artifact,
credential, token, cookie, session value, environment value, or provider
payload is recorded here.

## Validation

- Repository tests: 456 passed.
- Offline evaluations: 39 passed.
- Focused scaling and recipe-session tests: 51 passed.
- Compose configuration: valid with ignored local environment file paths.
- Sidecar image build: passed.
- Public sidecar startup and health: passed.
- `git diff --check`: passed.

The only test warning is the existing Starlette/httpx compatibility deprecation
warning.

## Boundaries retained

No canonical recipe save, authentication ownership, user/session ownership,
public sidecar route, Redis, Protocol Buffers, asynchronous job system, AWS, or
new ingress was added.
