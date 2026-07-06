# Manual Live OpenAI Smoke Tests

The live OpenAI smoke-test path is manual-only. It is not part of pytest discovery, offline evals, CI, repository validation, deployment, or normal local validation.

Use it only when you intentionally want to confirm the existing OpenAI provider path can make real API calls for the AI sidecar workflows.

## What It Covers

`scripts/smoke-openai-live.py` uses tiny generated fixtures and the existing provider harness to cover:

- provider/config sanity without printing secrets;
- structured recipe importer;
- Ask My Cookbook over generated saved recipes;
- Dataset Ask over a generated local `13k-recipes.csv`;
- meal planning over a generated saved-recipe SQLite fixture.

It does not use the real `recipe-dataset/` folder, the production Vanilla Cookbook database, embeddings, images, audio, files, batch jobs, Qdrant, Postgres, pgvector, vector storage, generated persistent indexes, deployment, or Cloudflare.

## Required Opt-In

The script exits without live calls unless all of these controls are set:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
```

`OPENAI_API_KEY` must also be available in the process environment or local ignored `.env`. Never commit `.env` or paste key values into mailbox files, docs, logs, issues, or PRs.

The configured model comes from the existing provider settings:

```text
OPENAI_MODEL=gpt-5.4-nano
OPENAI_FALLBACK_MODEL=gpt-5.4-mini
```

The smoke script does not silently switch models. If the configured model is unavailable, quota is exhausted, or the provider returns a rate-limit/provider error, the script fails with a concise provider-error message and no retry loop beyond the provider's existing behavior.

## Run From PowerShell

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
# OPENAI_API_KEY should already be in local .env or process env, never committed
& .\.venv\Scripts\python.exe scripts\smoke-openai-live.py
```

Expected compact success shape:

```text
provider=openai
model=<configured model>
live_calls=4
estimated_usage_tokens=<token count if provider reports usage>
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

Last recorded manual live validation:

```text
provider=openai
model=gpt-5.4-nano
live_calls=4
estimated_usage_tokens=1200
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

Skip/fail behavior:

- disabled live flag: exits `0` with a skip message and no live calls;
- missing API key: exits `0` with a skip message and no live calls;
- missing, invalid, or greater-than-25-cent budget: exits non-zero before live calls;
- `AI_MAX_OUTPUT_TOKENS` above `300`: exits non-zero before live calls;
- unavailable model, rate limit, quota, or provider error: exits non-zero with a clear provider failure.

The script must not print API keys, key prefixes, authorization headers, raw `.env` content, raw provider config, or cloud secret names.

On Windows, the script uses best-effort temporary directory cleanup so a transient SQLite file handle during cleanup does not mask successful live workflow validation. Provider errors, assertion failures, guardrail failures, and workflow failures still exit non-zero.

## Normal Validation

Normal validation remains offline and mock-only:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
```

Do not add live smoke tests to GitHub Actions or repository validation.
