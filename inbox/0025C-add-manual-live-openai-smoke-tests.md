# Task 0025C: Add Manual Live OpenAI Smoke Tests

## Goal

Add a safe, manual-only live OpenAI smoke-test path for the AI cookbook sidecar.

This task should prove that the existing OpenAI provider path works against real API calls for the app's major AI workflows, while keeping normal tests, offline evals, CI, and repo validation deterministic, mock-only, and free.

Live tests must be opt-in, bounded, low-cost, and impossible to run accidentally in normal validation.

## Build On

Completed work:

- `0019`: provider harness with mock default and OpenAI optional path
- `0021`: structured recipe importer
- `0022`: Ask My Cookbook RAG over saved Vanilla Cookbook recipes
- `0023B`: meal-plan endpoint
- `0024D`: dataset RAG endpoint over indexed Kaggle dataset results
- `0025A`: offline eval harness and validation hygiene
- `0025B`: expanded offline evals if completed

Before implementing, confirm the repo has:

- `ai-api/app/providers/openai_provider.py`
- `ai-api/app/providers/registry.py`
- `ai-api/app/importer.py`
- `ai-api/app/rag.py`
- `ai-api/app/meal_plan_endpoint.py`
- `ai-api/app/dataset_rag.py`
- `evals/ai_cookbook/run_evals.py`
- `.env.example`
- `.gitignore` rules for `.env`, `.env.*`, `recipe-dataset/`, and `.tmp-pytest*/`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

Add manual live OpenAI smoke tests only.

The smoke tests should cover at least:

1. Provider health/config sanity without leaking secrets.
2. Structured recipe importer live call.
3. Ask My Cookbook live call over tiny generated saved-recipe fixture.
4. Dataset Ask live call over tiny generated local dataset fixture.
5. Meal-plan live call over tiny generated saved-recipe fixture.

Keep each test tiny and bounded.

If all five workflows are too large for this task, implement provider sanity + importer + one RAG endpoint first, and document deferred smoke tests in the outbox.

## Manual-Only Guardrails

Live smoke tests must not run unless all required opt-in controls are set.

Require at least:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=<real key in local .env or environment>
OPENAI_ENABLE_LIVE_TESTS=true
OPENAI_LIVE_TEST_BUDGET_CENTS=25
```

If `OPENAI_ENABLE_LIVE_TESTS` is not exactly `true`, skip or exit cleanly without live calls.

If `OPENAI_API_KEY` is missing, skip or exit cleanly without live calls.

If the budget cap is missing or too high, fail safely before making calls.

Suggested budget behavior:

- default budget: 25 cents or less;
- allow override only through env var;
- estimate usage from provider response token usage if available;
- at minimum, count calls and enforce a maximum number of live calls;
- never loop indefinitely;
- max live calls should be small, for example 3 to 5 calls.

## Model Handling

Use the existing OpenAI provider configuration from the repo.

Do not hardcode a model name inside tests unless the provider already requires one. Prefer reading:

```text
OPENAI_MODEL
OPENAI_FALLBACK_MODEL
```

Document the configured default model from `.env.example` and live smoke-test docs.

If the configured model is not available to the account, fail with a clear message and no retries beyond the provider's existing behavior.

Do not silently switch to expensive models.

## Cost And Token Controls

Keep live calls cheap.

Use:

- tiny prompts;
- tiny fixture data;
- low `AI_MAX_OUTPUT_TOKENS`, for example 150 to 300;
- deterministic temperature where supported;
- low endpoint limits, for example `limit=1` or `limit=2`;
- no real 13K dataset requirement;
- no image/audio/file calls;
- no embeddings;
- no batch jobs.

The smoke-test command should print a compact summary:

```text
provider=openai
model=<configured model>
live_calls=3
estimated_usage_tokens=<n if available>
status=passed
```

Do not print the API key, key prefix, Authorization headers, raw `.env`, or full provider config.

## Suggested Implementation Options

Prefer one of these approaches:

### Option A: Script

```text
scripts/smoke-openai-live.py
```

Run with:

```powershell
& .\.venv\Scripts\python.exe scripts\smoke-openai-live.py
```

### Option B: Pytest marker

```text
ai-api/tests/live/test_openai_smoke.py
```

Run with:

```powershell
$env:OPENAI_ENABLE_LIVE_TESTS="true"
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\live -m live_openai
```

Option A is preferred because it is harder to accidentally run in normal pytest.

Normal validation must not run live tests.

## Fixture Strategy

Use generated temporary fixtures only.

For saved recipes:

- create a tiny SQLite fixture or reuse existing AI API test fixture helpers;
- include 1 to 3 recipes;
- ensure one query has a clear retrieved answer.

For dataset ask:

- create a temporary `13k-recipes.csv` with 1 to 3 rows;
- point `RECIPE_DATASET_DIR` to the temporary directory;
- do not require or read the real `recipe-dataset/` folder.

For importer:

- use one short pasted recipe text.

For meal-plan:

- use tiny saved-recipe candidates and request 1 day / 1 meal.

## Documentation

Create or update docs:

```text
docs/live-openai-smoke-tests.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
docs/repo-validation.md
ai-api/README.md
README.md
```

Docs should explain:

- live smoke tests are manual-only;
- normal validation stays mock/offline;
- required env vars;
- how to run the smoke tests from PowerShell;
- expected cost guardrails;
- how to interpret failures such as missing key, unavailable model, rate limit, or provider error;
- no keys should be committed;
- live smoke tests are not CI requirements.

## .env.example

Update `.env.example` if needed with safe non-secret placeholders:

```text
OPENAI_ENABLE_LIVE_TESTS=false
OPENAI_LIVE_TEST_BUDGET_CENTS=25
```

Do not add real keys.

Do not expose secret fragments.

## Validation Integration

Do not add live smoke tests to normal validation.

Normal validation should remain:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct Windows pytest still has temp-directory issues, document the error and rely on the Git Bash validator if it passes.

Then, only manually and only with opt-in env vars, run the live smoke script.

## OpenAI API Notes

Use the existing OpenAI Python SDK dependency path already used by the repo.

The OpenAI API quickstart documents setting an `OPENAI_API_KEY` environment variable for API authentication. Keep that pattern and do not hardcode secrets.

If using structured outputs for importer or meal-plan smoke tests, use the existing provider abstraction and schema flow rather than calling OpenAI directly from the test script.

## Safety Checks

Add smoke-test output checks where practical:

- no `OPENAI_API_KEY` string;
- no `sk-` string;
- no `Authorization:` header;
- no `.env` content;
- no raw provider config;
- citations present for RAG paths;
- no-match behavior remains no-provider-call in offline tests.

## Non-Goals

Do not implement:

- production deployment changes
- Cloudflare changes
- GitHub Actions live tests
- CI live OpenAI tests
- controller/demo launch workflows
- TTL cleanup workflows
- Qdrant
- Postgres
- pgvector
- embeddings
- vector DB
- persistent generated indexes
- image/audio/file API calls
- raw Kaggle dataset commits
- generated index artifact commits
- `.env` or secret commits

## Tests / Validation

Add offline unit tests for the smoke-test guardrails if practical.

For example:

- missing `OPENAI_ENABLE_LIVE_TESTS=true` exits/skips before provider calls;
- missing `OPENAI_API_KEY` exits/skips before provider calls;
- too-high or invalid budget cap fails safely;
- secret leakage checker catches obvious patterns.

Normal validation should pass without real OpenAI credentials.

Run from Windows PowerShell:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Manual live smoke command should be documented but not required for commit validation.

Example manual run:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
# OPENAI_API_KEY should already be in local .env or process env, never committed
& .\.venv\Scripts\python.exe scripts\smoke-openai-live.py
```

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no raw dataset files, generated index artifacts, `.env`, or secrets are staged.

## Outbox Report

Create:

```text
outbox/0025C-add-manual-live-openai-smoke-tests-results.md
```

Include:

- Summary
- Files changed
- Smoke workflows covered
- Manual command added
- Guardrails added
- Validation results
- Whether live smoke was run manually or skipped
- If skipped, why
- Confirmation that normal validation remains offline/mock-only
- Confirmation that no keys/secrets were committed
- Confirmation that no Qdrant/Postgres/pgvector/embeddings/vector DB were added
- Recommended next task to finalize AI features

## Commit

Commit and push:

```bash
git add .env.example ai-api evals scripts docs README.md outbox/0025C-add-manual-live-openai-smoke-tests-results.md

git commit -m "mailbox: complete task 0025C add manual live openai smoke tests"

git push origin main
```

## Done Criteria

- Manual live OpenAI smoke-test path exists.
- It is impossible to run live calls accidentally during normal validation.
- It requires explicit opt-in env vars.
- It uses existing provider harness.
- It covers at least provider sanity plus one or more app workflows.
- It uses tiny generated fixtures.
- It enforces low call/token/budget guardrails.
- It avoids printing secrets.
- Normal tests/evals/validator pass without OpenAI credentials.
- Docs explain how to run and interpret live smoke tests.
- No production deployment changes are made.
- No Qdrant/Postgres/pgvector/embeddings/vector DB are added.
- No raw dataset files or generated indexes are committed.
- No `.env` or secrets are committed.
- Outbox report exists.
- Changes are committed and pushed.
