# 0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness

## Goal

Create a docs-first architecture decision record and offline eval harness for considering `GLM-4.7 Flash` as a future secondary/offload provider for bounded, low-risk AI tasks.

This task must **not** add runtime GLM provider integration, live GLM calls, secondary-provider routing, or public production behavior. The goal is to define the policy boundary and create a deterministic offline comparison harness before any future provider adapter work.

## Baseline Context

The current live OpenAI demo baseline is now clean after the 0030L through 0030O fixes:

- `0030L` fixed live importer provider failures by giving importer a bounded workflow-specific live output cap and safe diagnostics.
- `0030M` calibrated importer token thresholds and action-verb scoring.
- `0030N` relaxed brittle all-steps word-count scoring while keeping rambling/non-action failures.
- `0030O` refined action-oriented scoring so short setup/context phrases such as `In a small bowl, mix...` are accepted.
- Latest manual live OpenAI eval result reported by the operator: `status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495`.

Use the current OpenAI `gpt-5.4-nano` path and calibrated 0030L-O eval behavior as the baseline comparison point.

## Primary Objective

Add an ADR plus offline eval scaffolding that answers:

1. Which tasks are safe candidates for a secondary/offload provider?
2. Which tasks must remain with the final trusted provider path?
3. How will we prove that an offload improves cost/latency or token efficiency without reducing quality, citation grounding, privacy, or safety?
4. What config names would be used later if a provider adapter is approved?
5. What failure behavior is required when a secondary/offload output is poor, missing, unsafe, unsupported, or over budget?

## Important Framing

Treat `GLM-4.7 Flash` as a **candidate provider name**, not as an implemented dependency.

Do not make unverified claims about its current price, API compatibility, context window, rate limits, model quality, data policy, or availability. If docs mention those items, mark them as values to verify before a future implementation task.

## Non-Negotiable Boundaries

Do not add:

- GLM provider runtime integration;
- GLM API calls;
- GLM SDK dependencies;
- secondary-provider routing in runtime request paths;
- automatic model fallback;
- production provider selection changes;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- production auth;
- durable storage;
- Redis/Postgres/SQLite persistence;
- paid access;
- payment integration;
- ad/sponsor runtime code;
- live OpenAI calls during normal validation;
- live GLM calls during normal validation;
- committed `.env` files;
- committed API keys or key fragments;
- raw provider prompts or raw provider responses in committed docs/outbox/tests;
- local absolute paths in public docs examples;
- screenshots, logs, generated live artifacts, or `.tmp-ai-demo` outputs.

Normal validation must remain offline/mock-only.

## Suggested Files

Likely new files:

```text
docs/ai-secondary-provider-offload-adr.md
evals/ai_cookbook/secondary_provider_offload_cases.yaml
evals/ai_cookbook/secondary_provider_offload_eval.py
ai-api/tests/test_ai_secondary_provider_offload_docs.py
outbox/0031A-glm-47-flash-secondary-provider-offload-adr-and-eval-harness-results.md
```

Likely updated files:

```text
docs/ai-evals-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md if relevant
```

## Required Work

### 1. Add a secondary-provider offload ADR

Create:

```text
docs/ai-secondary-provider-offload-adr.md
```

The ADR should document a clear decision boundary:

- The primary/final answer provider remains the existing OpenAI `gpt-5.4-nano` path unless a later task explicitly changes that.
- Secondary providers may only be considered for bounded, low-risk offload tasks after offline evals prove no quality regression.
- Secondary/offload outputs are advisory inputs, not final user-visible answers.
- Final answer generation, citation faithfulness, safety decisions, and admin/budget decisions must not be delegated to an unproven secondary provider.
- Any future live secondary provider must still pass operator/invite/budget controls where applicable.
- A free or lower-cost provider still has cost-like risks: privacy, quota, latency, failure modes, and quality regression.

The ADR should include sections:

```text
Status
Context
Decision
Allowed offload task classes
Blocked task classes
Privacy and data-boundary policy
Budget and usage-reporting policy
Fallback and failure behavior
Evaluation plan
Future implementation gates
Non-goals
```

### 2. Define allowed offload candidates

Document allowed candidate task classes such as:

```text
query expansion for retrieval
ingredient synonym expansion
dataset metadata cleanup suggestions
title or slug suggestions
non-final clarification candidate generation
context compression draft with citation IDs preserved
draft critique against a quality checklist
formatting-only rewrites where factual content is already fixed
```

Each allowed task should include:

- why it is low risk;
- what input data it may receive;
- what it must not receive;
- what downstream validation is required;
- what fallback behavior is used if the offload output is bad or missing.

### 3. Define blocked task classes

Document blocked tasks such as:

```text
final user answer generation
final recipe draft generation
food safety advice
medical, allergy, diet, or nutrition claims
citation truth or faithfulness final decisions
safety refusal decisions
admin/operator decisions
provider budget decisions
invite/session/security decisions
private user recipe data processing without an explicit future privacy decision
any task that can publish or persist data
```

### 4. Add offline eval cases

Create deterministic offline eval cases, likely:

```text
evals/ai_cookbook/secondary_provider_offload_cases.yaml
```

The cases should simulate secondary-provider outputs without calling any provider.

Include at least:

- good query expansion output;
- bad query expansion output with unrelated terms;
- context compression that preserves citation IDs;
- context compression that drops or invents citation IDs;
- title/slug suggestions that stay grounded;
- title/slug suggestions that introduce unsupported claims;
- clarification candidates that are useful;
- clarification candidates that ask for irrelevant/private data;
- draft critique checklist output that catches a quality issue;
- draft critique output that tries to become the final answer.

### 5. Add offline eval runner

Create:

```text
evals/ai_cookbook/secondary_provider_offload_eval.py
```

The runner should:

- load the YAML or JSON fixture cases;
- evaluate simulated secondary output against deterministic checks;
- produce a compact pass/fail summary;
- return non-zero on failure;
- require no provider keys;
- make no network calls;
- avoid printing raw secrets or local paths;
- document estimated savings as a simple offline estimate, not actual live billing.

Suggested checks:

```text
allowed task class recognized
blocked task class rejected
no invented citation IDs
required citation IDs preserved for compression tasks
unsupported claims rejected
private data request rejected
fallback-to-primary-baseline behavior described
secondary output is advisory only
final answer provider remains primary
```

### 6. Add tests

Add tests, likely in:

```text
ai-api/tests/test_ai_secondary_provider_offload_docs.py
```

Tests should verify:

- ADR exists;
- ADR says secondary/offload providers are disabled/not implemented by default;
- ADR says OpenAI `gpt-5.4-nano` remains the final-answer baseline for now;
- ADR includes allowed and blocked task classes;
- ADR includes privacy, budget, usage-reporting, fallback, and evaluation-gate sections;
- docs do not contain fake GLM API keys or committed secret-like values;
- eval cases file exists and includes good/bad cases;
- eval runner runs offline and exits successfully for the committed fixture set;
- no live provider calls are required;
- no runtime provider routing is added.

### 7. Optional config-name proposal, docs only

The ADR may propose future config names, but they must be docs-only in this task.

Suggested future names:

```env
AI_SECONDARY_PROVIDER_ENABLED=false
AI_SECONDARY_PROVIDER=glm
AI_SECONDARY_MODEL=glm-4.7-flash
AI_SECONDARY_PROVIDER_BASE_URL=
AI_SECONDARY_PROVIDER_API_KEY=
AI_OFFLOAD_TASKS=query_expansion,context_compression,title_suggestions
AI_FINAL_PROVIDER=openai
```

Requirements:

- Do not add these as active runtime settings in `config.py` unless they are explicitly marked docs-only and unused.
- Do not wire them into request flow.
- Do not make them appear as required `.env` settings.
- Do not require real GLM credentials.

### 8. Update docs and backlog

Update:

```text
docs/ai-evals-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md if relevant
```

Docs should explain:

- this is an ADR/eval-harness planning step only;
- no secondary provider has been enabled;
- no public or production behavior changes;
- the current 0030L-O live OpenAI baseline remains the comparison target;
- future GLM/provider adapter work must be a separate task after this ADR/eval harness.

### 9. Add outbox report

Create:

```text
outbox/0031A-glm-47-flash-secondary-provider-offload-adr-and-eval-harness-results.md
```

Include:

- summary;
- ADR created;
- allowed task classes;
- blocked task classes;
- eval harness added;
- tests added;
- docs updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation;
- recommendation for the next task.

## Acceptance Criteria

- ADR exists and clearly states no GLM runtime integration is added.
- ADR says secondary/offload output is advisory only and final user-visible answers remain on the primary baseline provider for now.
- Allowed and blocked offload task classes are documented.
- Privacy/data-boundary, budget, usage-reporting, fallback, and evaluation-gate policies are documented.
- Offline eval fixture cases exist.
- Offline eval runner exists and runs without provider keys or network calls.
- Tests verify docs/eval harness boundaries.
- Normal validation remains offline/mock-only.
- No live GLM or OpenAI calls are added to normal validation.
- No secrets, raw provider prompts, raw provider responses, local absolute paths, or generated artifacts are committed.
- No public route exposure, production auth/storage, payment/ad/sponsor runtime, or routing behavior is added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
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

The live wrappers should skip cleanly unless the local environment explicitly opts into live mode.

Do not run live GLM calls; none should exist.

## Before Commit Checklist

Confirm:

- no `.env` file is staged;
- no real key is staged;
- no `sk-proj-`, `sk_live_`, `sk_test_`, `glm-key`, or fake-looking provider secret is staged;
- no raw provider response is staged;
- no raw provider prompt is staged;
- no `.tmp-ai-demo` artifacts are staged;
- no logs or screenshots are staged;
- no local absolute paths are added to public docs examples;
- no GLM provider runtime code is added;
- no secondary-provider routing is added.

## Commit

```bash
git add docs evals ai-api README.md outbox/0031A-glm-47-flash-secondary-provider-offload-adr-and-eval-harness-results.md

git commit -m "mailbox: complete task 0031A secondary provider offload adr eval harness"

git pull --rebase origin main

git push origin main
```
