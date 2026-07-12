# 0031B Secondary Provider Fact Verification And Implementation Gate

## Goal

Create a docs-first provider-fact verification register and implementation gate for future secondary/offload providers, starting with `GLM-4.7 Flash` as the candidate named by `0031A`.

This task must not implement runtime GLM support, secondary-provider routing, automatic fallback, SDK dependencies, live GLM calls, or production behavior. It should define what must be proven from primary provider documentation before any future runtime adapter task can start.

## Baseline Context

`0031A` created the secondary-provider offload ADR and deterministic offline eval harness. It kept the current OpenAI `gpt-5.4-nano` path as the final-answer baseline and added no runtime secondary-provider code.

`0031A` recommended the next safe follow-on as a provider-fact verification and implementation-gate task that confirms candidate-provider pricing, privacy, retention, limits, and API behavior from primary documentation before any runtime adapter work starts.

The baseline remains:

```text
OpenAI gpt-5.4-nano final-answer path
status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495
```

`0030P` also fixed the no-bake cheesecake clarification regression. Future offload comparisons must preserve that corrected 0030 baseline behavior.

## Primary Objective

Add a provider-fact register and deterministic gate so future tasks cannot add a secondary provider without explicitly documenting and verifying:

- provider identity and model naming;
- API compatibility and request/response shape;
- pricing and cost model;
- context and output limits;
- rate limits and quota behavior;
- privacy, retention, training, and data-use policy;
- regional availability and account requirements;
- failure modes and timeout behavior;
- safety/security restrictions;
- allowed task classes from the `0031A` ADR;
- blocked task classes from the `0031A` ADR;
- implementation go/no-go decision.

## Critical Rule

Do not invent provider facts.

If Codex has no web access or no primary documentation is provided locally, mark facts as:

```text
verification_status: unverified
implementation_gate: blocked
reason: primary provider documentation was not available in this task
```

It is acceptable for this task to create the register and gate with `GLM-4.7 Flash` still blocked and unverified. That is safer than inventing pricing, API behavior, privacy terms, context windows, rate limits, or availability.

## Non-Negotiable Boundaries

Do not add runtime provider code, SDK dependencies, live GLM calls, secondary routing, automatic fallback, production provider changes, public route exposure, production auth, durable storage, payment/ad/sponsor runtime behavior, live calls during normal validation, committed local env files, credentials, raw provider prompts/responses, logs, screenshots, or generated live artifacts.

Normal validation must remain offline/mock-only.

## Suggested Files

Likely new files:

```text
docs/ai-secondary-provider-fact-register.md
docs/ai-secondary-provider-implementation-gate.md
evals/ai_cookbook/secondary_provider_fact_gate.yaml
evals/ai_cookbook/secondary_provider_fact_gate_eval.py
ai-api/tests/test_ai_secondary_provider_fact_gate_docs.py
outbox/0031B-secondary-provider-fact-verification-and-implementation-gate-results.md
```

Likely updated files:

```text
docs/ai-secondary-provider-offload-adr.md
docs/ai-evals-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md if relevant
```

## Required Work

### 1. Provider fact register

Create `docs/ai-secondary-provider-fact-register.md`.

Start with one candidate:

```text
Provider candidate: GLM
Candidate model: GLM-4.7 Flash
Purpose: possible future secondary/offload provider for bounded low-risk tasks
Current implementation status: not implemented
Verification status: unverified unless primary documentation is actually available
Implementation gate: blocked unless all required facts are verified
```

Required fact categories:

```text
provider_identity
model_identifier
primary_documentation_references
api_protocol_and_auth
request_response_schema
structured_output_support
streaming_support
context_window
max_output_tokens
rate_limits
quota_behavior
pricing_input_tokens
pricing_output_tokens
free_tier_or_trial_terms
privacy_policy
data_retention_policy
training_data_use_policy
regional_availability
account_and_billing_requirements
safety_policy_or_usage_restrictions
timeout_and_retry_guidance
error_response_shape
logging_redaction_requirements
allowed_offload_tasks
blocked_tasks
fallback_requirements
verification_owner_or_method
verification_date
implementation_gate_decision
```

For any field not verified from primary documentation, write `unverified`, `unknown`, or `not approved` clearly. Do not fill guessed values.

### 2. Implementation gate doc

Create `docs/ai-secondary-provider-implementation-gate.md`.

Define gates that must pass before any future runtime adapter task:

- all required facts verified from primary documentation;
- source references recorded;
- privacy/data-use terms acceptable for intended inputs;
- private user recipe data blocked unless a future privacy decision allows it;
- allowed task classes match the `0031A` ADR;
- blocked task classes remain blocked;
- fallback returns to primary baseline;
- budget and usage reporting semantics are defined;
- operator/invite controls are respected where applicable;
- normal validation remains offline;
- secondary output cannot become final user-visible answer without primary validation;
- offline evals prove bad secondary output is ignored;
- runtime adapter work requires a separate future mailbox task.

Include a go/no-go matrix.

### 3. Machine-readable fact gate fixture

Create `evals/ai_cookbook/secondary_provider_fact_gate.yaml`.

Include cases for:

- blocked/unverified GLM candidate;
- synthetic fully verified safe candidate, clearly labeled `synthetic_fixture_not_real_provider`;
- missing privacy policy;
- missing pricing;
- blocked task class;
- final-answer generation incorrectly allowed;
- missing fallback behavior.

Do not include real or fake-looking credentials.

### 4. Deterministic gate evaluator

Create `evals/ai_cookbook/secondary_provider_fact_gate_eval.py`.

The evaluator must make no network calls, require no provider credentials, load the YAML fixture, print compact pass/fail output, and return non-zero on failure.

It should verify:

- unverified real candidates remain blocked;
- only complete synthetic candidates can pass;
- missing privacy/pricing/fallback/task-class fields fail;
- blocked task classes fail;
- final-answer generation remains blocked;
- no secret-like values or local paths appear in fixtures/output.

### 5. Tests

Create `ai-api/tests/test_ai_secondary_provider_fact_gate_docs.py`.

Tests should verify:

- fact register exists;
- implementation gate doc exists;
- GLM candidate is marked not implemented unless facts are actually verified;
- GLM candidate does not claim verified pricing/privacy/API behavior without sources;
- runtime adapter requires a future task;
- final-answer generation remains blocked;
- private user recipe data remains blocked by default;
- fact gate YAML exists;
- gate evaluator runs offline and passes committed fixtures;
- app runtime files do not add GLM provider runtime code;
- app runtime files do not add secondary-provider routing.

### 6. Docs updates

Update existing docs to say:

- `0031A` defined the offload ADR and offline eval harness;
- `0031B` adds provider fact verification and implementation gating;
- runtime adapter work remains blocked until facts are verified;
- `GLM-4.7 Flash` remains a candidate name, not implemented behavior;
- future adapter work must preserve the corrected 0030 baseline, including `0030P` no-bake cheesecake behavior.

### 7. Outbox report

Create `outbox/0031B-secondary-provider-fact-verification-and-implementation-gate-results.md`.

Include summary, fact register created, implementation gate created, GLM candidate current status, whether facts were verified or left unverified, eval gate added, tests added, docs updated, validation results, explicit non-goals, artifact safety confirmation, and recommendation for the next task.

If facts remain unverified, recommend not starting runtime adapter work yet.

## Acceptance Criteria

- Provider fact register exists.
- Implementation gate doc exists.
- GLM candidate is not treated as implemented.
- Unverified GLM facts keep implementation blocked.
- Offline gate evaluator exists and passes committed fixtures.
- Tests verify docs, fixtures, evaluator, and no runtime routing.
- No runtime provider integration or secondary routing is added.
- Normal validation remains offline/mock-only.
- No sensitive/local/generated artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\secondary_provider_fact_gate_eval.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_secondary_provider_fact_gate_docs.py -q
& .\.venv\Scripts\python.exe evals\ai_cookbook\secondary_provider_offload_eval.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_ai_secondary_provider_offload_docs.py -q
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Live wrappers should skip cleanly unless explicitly opted in. Do not run live GLM calls; none should exist.

## Commit

```bash
git add docs evals ai-api README.md outbox/0031B-secondary-provider-fact-verification-and-implementation-gate-results.md

git commit -m "mailbox: complete task 0031B secondary provider fact gate"

git pull --rebase origin main
git push origin main
```
