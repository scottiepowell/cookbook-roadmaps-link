# 0030I-8V live importer 500-token acceptance consolidation results

Consolidated the operator-approved live diagnostic evidence for the strict
schema importer:

- `openai` / `gpt-5.4-nano` passed at 1000 output tokens.
- `openai` / `gpt-5.4-nano` passed at 500 output tokens.
- 400 output tokens failed safely as `output_cap_or_incomplete_response` /
  `JSONDecodeError`.
- The earlier 300-token diagnostic was also too low for complete strict-schema
  JSON.

The recommended manual live importer acceptance cap is 500 output tokens.
1000 remains allowed as the explicit manual troubleshooting ceiling, not the
recommended default acceptance cap. Acceptance requires explicit operator
approval after no-call preflight and permits exactly one bounded importer call
per invocation. There are no retries, and invalid or incomplete JSON is never
accepted as success.

Normal validation remains mock/offline and does not call live OpenAI. No
secrets, prompts, provider bodies, paths, headers, or stack traces are exposed.
No strict-schema validation was weakened, and no AWS/platform work was started.

Validation passed: env-loader checks, 39 offline evals, full repository
validator (353 tests), `git diff --check`, Docker Compose config, mock demo,
live wrapper skips with opt-in disabled, and Playwright mock UI checks.

Explicit non-goals: no product-wide cap change to 500, no retries, no live
call during normal validation, no raw provider output, no secret handling
changes, no schema relaxation, no AWS/platform work, and no new task.
