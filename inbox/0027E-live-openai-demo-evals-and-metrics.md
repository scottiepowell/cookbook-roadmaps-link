# Task 0027E: Live OpenAI Demo Evals And Metrics

## Goal

Prepare the cookbook AI demo for real OpenAI-backed operation using the configured GPT nano model path, then add repeatable live-provider evaluation and metrics reporting.

The local mock UI demo is now passing after `0027D`. This task moves from mock-first demo validation to controlled live-provider validation. The output should be a repeatable test/eval run that produces files showing what was tested, what the expected behavior was, what the model returned, and how the result was scored.

Do not focus on screenshots in this task.

## Product Direction

Treat this as the start of production hardening for a paid or time-limited application. The demo is no longer just a portfolio screenshot path. It should become a real application flow that can support multiple future use cases.

This task does not implement billing, time limits, multi-tenant access, production storage, or public launch controls. Those should become later tasks after live-provider quality is measurable.

## Current Context

Completed foundation:

- `0027A`: sidecar AI demo UI and logging foundation
- `0027B`: production-quality local UI demo usability
- `0027C`: manual UI acceptance checklist
- `0027D`: generated demo data and fixed local demo launch

Current local mock status after `0027D`:

- `/demo` loads locally.
- generated saved recipes are available.
- generated dataset fixtures are available.
- importer works in mock mode.
- Ask My Cookbook works in mock mode.
- dataset search and dataset ask/RAG work in mock mode.
- meal planner works in mock mode.

Now prepare an OpenAI-backed run using the configured live model path.

## External Guidance To Respect

Use current OpenAI API docs and keep implementation aligned with them:

- OpenAI structured outputs should use strict JSON schema where possible and should prefer Structured Outputs over basic JSON mode when schema adherence matters.
- OpenAI evals require test data and testing criteria/graders to determine whether outputs are correct.
- Keep token/cost controls explicit because GPT nano is inexpensive but still a live paid provider call.

Record the exact docs/pricing references used in the outbox report.

## Scope

Add a live-provider evaluation harness for the AI demo workflows.

The harness should:

1. seed generated demo-safe data;
2. run against OpenAI provider mode, not mock;
3. exercise the same user-facing workflows as the UI;
4. define expected answer checks before the run;
5. capture actual model responses;
6. score results with deterministic checks where possible;
7. record token usage and estimated cost where available;
8. record latency per workflow;
9. write machine-readable JSONL/JSON results and a Markdown summary;
10. fail safely when live provider settings are missing or opt-in flags are not enabled.

## Live Provider Guardrails

Do not run live OpenAI calls unless explicitly opted in.

Require all of these before live calls:

```text
AI_PROVIDER=openai
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_API_KEY present
OPENAI_LIVE_TEST_BUDGET_CENTS present and within a small cap
OPENAI_MODEL configured, expected default gpt-5.4-nano
AI_MAX_OUTPUT_TOKENS capped for eval runs
```

If any guardrail is missing, skip cleanly and explain what is required.

Do not add live OpenAI calls to normal CI.

Do not expose keys, key fragments, raw environment files, auth headers, or provider secrets in logs or artifacts.

## Expected Workflows

Create a live eval case set for at least:

1. Structured importer.
2. Ask My Cookbook.
3. Dataset search, deterministic non-provider baseline.
4. Dataset ask/RAG.
5. Meal planner.

Dataset search may remain deterministic and should still be included in the report as a baseline step.

## Expected Answer Criteria

Create explicit expected checks for each workflow.

Examples:

### Importer

Input: short tomato pasta or lemon beans recipe notes.

Expected checks:

- response parses as the expected schema;
- title is non-empty;
- ingredient list is non-empty;
- instructions are non-empty;
- provider is OpenAI;
- model matches configured OpenAI model;
- no warnings unless justified.

### Ask My Cookbook

Question: `What saved recipe uses lemon?`

Expected checks:

- answer mentions or cites `Lemon Herb White Beans`;
- at least one citation is returned;
- citation includes saved recipe id `1` or matching title;
- retrieved count is greater than zero;
- no hallucinated recipe title outside retrieved citations.

### Dataset Ask/RAG

Question: `What indexed recipe uses tomato pasta?`

Expected checks:

- answer mentions or cites `Tomato Pasta Skillet`;
- at least one citation is returned;
- citation source id includes `demo-dataset-1`;
- retrieved count is greater than zero;
- answer does not invent unsupported dataset recipes.

### Meal Planner

Preferences: `lemon dinner`.

Expected checks:

- plan has at least one day and one meal;
- selected recipe is from retrieved saved recipe candidates;
- expected likely recipe is `Lemon Herb White Beans`;
- citations are present;
- no invented recipe ids.

## Metrics To Capture

For every case, capture:

- workflow name;
- endpoint or internal function called;
- provider;
- model;
- input summary, not full raw secret-bearing environment;
- expected checks;
- actual answer summary;
- pass/fail per check;
- overall pass/fail;
- warning count;
- citation count;
- retrieved count;
- latency milliseconds;
- input tokens if available;
- output tokens if available;
- total tokens if available;
- estimated cost if possible;
- raw response path if saved;
- error type if failed.

## Artifacts

Write live eval outputs under an ignored generated directory, for example:

```text
.tmp-ai-demo/live-evals/<timestamp>/
```

Expected generated files:

```text
results.jsonl
summary.json
summary.md
responses/*.json
```

Do not commit generated live eval results by default.

Commit only docs, scripts, test code, fixture definitions, and outbox reports.

## Suggested Files

Add or update as needed:

```text
scripts/run-openai-demo-evals.ps1
scripts/live-openai-demo-evals.py
ai-api/app/demo_data.py
evals/ai_cookbook/live_cases.json
evals/ai_cookbook/expected_checks.py
docs/live-openai-demo-evals.md
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0027E-live-openai-demo-evals-and-metrics-results.md
```

If another structure fits better, keep it simple and document it.

## UI Integration Expectation

The harness can call API functions or HTTP endpoints directly. It does not need browser automation.

However, the case set should mirror the UI workflow order so the same evidence supports the live demo:

1. readiness;
2. importer;
3. Ask My Cookbook;
4. dataset search;
5. dataset ask/RAG;
6. meal planner.

## Production Direction Notes

Add a short future-production section to the docs/backlog. Capture that future production tasks may include:

- authenticated access;
- time-limited sessions;
- paid access or monetization gate;
- usage metering;
- user/session isolation;
- durable storage;
- multi-use-case routing;
- deployment exposure controls;
- provider cost controls;
- admin/operator dashboard.

Do not implement those in this task.

## Tests

Add offline tests for the live eval harness without calling OpenAI.

Tests should cover:

- guardrails skip when opt-in settings are missing;
- expected-check functions pass/fail correctly;
- metrics summary generation;
- cost estimation helper if implemented;
- result files are written to ignored generated paths;
- no secrets are written to artifacts;
- existing AI endpoints still pass.

## Validation

Run normal offline validation only:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The final `run-openai-demo-evals.ps1` command should skip cleanly unless live eval opt-in settings are present.

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI calls during normal validation.

## Optional Manual Live Run

After implementation, a human operator can run the live eval explicitly with environment variables already configured locally.

Example shape:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="300"
$env:OPENAI_MODEL="gpt-5.4-nano"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The script should print the generated report path and a compact pass/fail summary.

Do not print or persist the API key.

## Outbox Report

Create:

```text
outbox/0027E-live-openai-demo-evals-and-metrics-results.md
```

Include:

- Summary
- Files changed
- Live eval harness behavior
- Guardrails
- Case set
- Expected checks
- Metrics captured
- Generated artifact paths and ignore behavior
- Offline tests added
- Validation results
- Whether a live run was performed or skipped
- OpenAI docs/pricing references used
- Known limitations
- Recommended next task
- Confirmation no private env files, API keys, raw datasets, generated live results, screenshots, or credentials were committed

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0027E-live-openai-demo-evals-and-metrics-results.md

git commit -m "mailbox: complete task 0027E live openai demo evals and metrics"

git push origin main
```

## Done Criteria

- Live eval harness exists and is guarded by explicit opt-in.
- Harness can run the demo workflows against OpenAI provider mode.
- Expected checks are defined before the live run.
- Metrics and results are written to ignored generated artifacts.
- Offline tests cover checks, metrics, guardrails, and artifact safety.
- Normal validation remains offline.
- No live OpenAI calls are run in CI or normal validation.
- No private env files, keys, raw datasets, generated live results, screenshots, or credentials are committed.
