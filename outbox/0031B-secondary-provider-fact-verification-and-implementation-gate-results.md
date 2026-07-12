Title: 0031B Secondary Provider Fact Verification And Implementation Gate Results

Summary

- Added a docs-first provider fact register and implementation gate for future secondary/offload providers.
- Kept `GLM-4.7 Flash` explicitly unverified and blocked because primary provider documentation was not available in this task.
- Added an offline fact-gate fixture set, evaluator, and docs tests so future runtime adapter work cannot start from guessed provider facts.

Fact Register Created

- Added `docs/ai-secondary-provider-fact-register.md`.
- The register records required fact categories including:
  - provider identity
  - model identifier
  - primary documentation references
  - API and auth
  - structured output, streaming, and token/context limits
  - rate limits, quota behavior, and pricing
  - privacy, retention, and training-use policy
  - regional/account/billing requirements
  - timeout, retry, and error-shape guidance
  - logging redaction requirements
  - allowed offload tasks
  - blocked tasks
  - fallback requirements
  - verification method/date
  - implementation gate decision

Implementation Gate Created

- Added `docs/ai-secondary-provider-implementation-gate.md`.
- The gate requires:
  - all required facts verified from primary documentation
  - source references recorded
  - privacy/data-use terms acceptable for intended inputs
  - private user recipe data blocked unless a future privacy decision allows it
  - allowed task classes matching the `0031A` ADR
  - blocked task classes remaining blocked
  - fallback to the current OpenAI baseline
  - budget/reporting semantics defined
  - operator/invite controls respected where applicable
  - offline validation remaining default
  - a separate future mailbox task for runtime adapter work

GLM Candidate Current Status

- Provider candidate: `GLM`
- Candidate model: `GLM-4.7 Flash`
- Current implementation status: not implemented
- Verification status: unverified
- Implementation gate: blocked
- Reason: primary provider documentation was not available in this task

Fact Verification Status

- No provider facts were invented.
- No pricing, API protocol, auth behavior, privacy policy, retention policy, context window, token limits, rate limits, quota behavior, or availability details were treated as verified.
- The safer result for this task is an explicit blocked state rather than guessed documentation.

Eval Gate Added

- Added `evals/ai_cookbook/secondary_provider_fact_gate.yaml`.
- Added `evals/ai_cookbook/secondary_provider_fact_gate_eval.py`.
- The committed fixture set covers:
  - blocked/unverified GLM candidate
  - synthetic fully verified safe candidate
  - missing privacy policy
  - missing pricing
  - blocked task class incorrectly allowed
  - final-answer generation not properly blocked
  - missing fallback behavior

The evaluator proves:

- unverified real candidates remain blocked
- only a fully verified synthetic fixture can pass
- missing privacy, pricing, fallback, or task-class rules block approval
- final-answer generation remains blocked
- no secret-like values or local paths appear in fixtures or output

Tests Added

- Added `ai-api/tests/test_ai_secondary_provider_fact_gate_docs.py`.
- The tests verify:
  - new docs exist
  - `GLM-4.7 Flash` remains not implemented
  - unverified GLM facts keep the gate blocked
  - docs do not claim verified pricing/privacy/API behavior without sources
  - runtime adapter work still requires a separate future task
  - final-answer generation stays blocked
  - private user recipe data stays blocked by default
  - the fact-gate fixture and evaluator run offline
  - app runtime files do not add GLM support or secondary-provider routing

Docs Updated

- `docs/ai-secondary-provider-offload-adr.md`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

These updates now state:

- `0031A` defined the advisory offload ADR and offline eval harness
- `0031B` adds fact verification and implementation gating
- runtime adapter work remains blocked until facts are verified
- `GLM-4.7 Flash` remains a candidate name, not implemented behavior
- future adapter work must preserve the corrected 0030 baseline, including `0030P` no-bake cheesecake behavior

Validation Results

- `python evals/ai_cookbook/secondary_provider_fact_gate_eval.py`: passed
- `python -m pytest ai-api/tests/test_ai_secondary_provider_fact_gate_docs.py -q`: passed
- `python evals/ai_cookbook/secondary_provider_offload_eval.py`: passed
- `python -m pytest ai-api/tests/test_ai_secondary_provider_offload_docs.py -q`: passed
- `python evals/ai_cookbook/run_evals.py`: passed
- `python scripts/e2e-ai-29-30-regression.py`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-ai-env-file-loader.ps1`: passed
- `bash scripts/validate-repo.sh`: passed
- `git diff --check`: passed
- `docker compose config --quiet`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-mock.ps1`: passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo-ai-live-smoke.ps1`: skipped cleanly without live opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-openai-demo-evals.ps1`: skipped cleanly without live opt-in

Explicit Non-Goals

- No runtime GLM support
- No GLM API calls
- No GLM SDK dependencies
- No secondary-provider routing
- No automatic fallback
- No production provider changes
- No public route exposure
- No production auth
- No durable storage
- No payment, ad, sponsor, or affiliate runtime behavior
- No live provider calls during normal validation

Artifact Safety Confirmation

- No local environment files committed
- No real provider keys committed
- No raw provider prompts committed
- No raw provider responses committed
- No logs or screenshots committed
- No generated live artifacts committed
- No local absolute paths added to public docs examples
- No GLM runtime code added
- No secondary-provider routing added

Recommendation

- Do not start runtime adapter work yet.
- A future runtime task should remain blocked until primary provider documentation is collected and every required fact category in the register is verified with recorded sources.
