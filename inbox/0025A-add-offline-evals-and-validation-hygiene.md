# Task 0025A: Add Offline Evals And Validation Hygiene

## Goal

Add an offline eval harness for the AI cookbook sidecar and clean up local validation guidance after the Windows venv/temp-directory pytest issue seen in `0024D`.

This task should make the project safer to iterate by checking grounding, citations, no-match behavior, secret leakage, and provider-call boundaries without requiring live OpenAI calls, network access, the real Kaggle dataset, Docker runtime for tests, or raw dataset files.

## Build On

Completed work:

- `0019`: provider harness with mock default and OpenAI optional/manual path
- `0021`: structured recipe importer
- `0022`: Ask My Cookbook RAG over saved Vanilla Cookbook recipes
- `0023A`: meal planner foundation
- `0023B`: meal plan endpoint
- `0024A`: local Kaggle dataset adapter/schema inspection
- `0024B`: deterministic local dataset index/search helpers
- `0024C`: indexed dataset retrieval endpoint
- `0024D`: RAG over indexed dataset with citations

Before implementing, confirm the repo has:

- `ai-api/app/dataset_rag.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/dataset_index.py`
- `ai-api/app/dataset_adapter.py`
- `ai-api/tests/test_dataset_ask.py`
- `outbox/0024D-add-rag-over-indexed-dataset-results.md`
- `.gitignore` rule for `recipe-dataset/`
- `.gitignore` rule for `.tmp-pytest*/`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

Implement offline evals and validation hygiene only.

Add an eval harness that can be run locally and from repo validation. The harness should use deterministic fixtures and mock/provider stubs only.

The evals should cover:

1. Dataset ask grounding.
2. Dataset ask citation completeness.
3. Dataset ask no-match behavior.
4. Dataset ask missing-dataset behavior.
5. Dataset ask secret leakage checks.
6. Saved recipe Ask My Cookbook citation/grounding checks if practical.
7. Meal-plan saved-recipe citation checks if practical.
8. Importer schema validation checks if practical.

Keep the first implementation small and deterministic. It is better to add a clean extensible harness with a handful of high-signal cases than a large brittle eval suite.

## Suggested Directory Structure

Create as appropriate:

```text
evals/
  ai_cookbook/
    README.md
    cases/
      dataset_ask.yaml
      saved_recipe_ask.yaml
      meal_plan.yaml
      importer.yaml
    run_evals.py
```

Or use JSON fixtures if YAML would require a new dependency. Prefer no new dependencies unless already present.

If YAML parsing would add dependency friction, use JSON files:

```text
evals/ai_cookbook/cases/dataset_ask.json
```

## Eval Harness Requirements

The eval runner should:

- run offline;
- use tiny generated fixture data;
- not require the real `recipe-dataset/` folder;
- not require OpenAI API keys;
- not call live providers;
- not call the network;
- not require Docker runtime;
- fail clearly on missing citations;
- fail clearly on invented/non-retrieved recipe IDs where detectable;
- fail clearly on secret leakage patterns such as `OPENAI_API_KEY`, `sk-`, `Authorization:`, `.env`, or raw provider config;
- produce compact pass/fail output;
- return non-zero on failure.

Suggested command:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

and from Git Bash validator:

```bash
python evals/ai_cookbook/run_evals.py
```

Adjust paths if the repo validator uses a temporary venv.

## What To Evaluate First

### Dataset Ask

Create fixture rows like:

```text
recipe_id,title,ingredients,instructions,cuisine
abc,Lemon Beans,"beans; lemon","Warm beans",dinner
def,Toast,bread,"Toast bread",breakfast
```

Eval cases should check:

- question `What uses lemon?` retrieves/cites only `abc`;
- provider prompt does not include `Toast` when Toast was not retrieved;
- response citation includes dataset title, source ID, source file, license, and source URL;
- no-match question returns provider `none` and empty citations;
- missing dataset returns controlled warnings and provider `none`;
- output does not contain secret-like strings.

### Saved Recipe Ask

If practical, add at least one eval confirming saved recipe RAG returns citations and does not answer from non-retrieved recipes.

### Meal Plan

If practical, add at least one eval confirming meal-plan output uses saved recipe IDs and citations only.

### Importer

If practical, add at least one eval confirming structured importer output validates against schema using mock provider only.

## Validation Hygiene

The `0024D` outbox reported:

```text
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
failed with Windows PermissionError creating/scanning pytest temp directories.
```

Clean this up where reasonable.

Options:

1. Add documentation for the reliable validation path.
2. Add a PowerShell validation wrapper that uses the repo venv when available and a safe local temp directory.
3. Add a pytest config or documented command that avoids scanning problematic Windows temp paths.
4. Make sure `.tmp-pytest*/` remains ignored.

Suggested wrapper:

```text
scripts/validate-repo.ps1
```

It may run:

```powershell
$env:TMP = "$PWD\.tmp-pytest"
$env:TEMP = "$PWD\.tmp-pytest"
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Keep the wrapper conservative and well documented. If implementing the wrapper becomes too large, document the recommended commands instead and explain the tradeoff in the outbox.

## Repo Validator Integration

Update `scripts/validate-repo.sh` to run the offline eval harness if present.

The validator currently creates a temporary venv and runs pytest. Reuse that venv for evals where possible.

Do not require Docker inside the eval harness. Docker Compose config validation may remain in the existing validator as it already is.

## CI / GitHub Actions

If a repo-validation GitHub Actions workflow already exists, update it to run the validator/evals.

If no workflow exists, add a minimal workflow only if safe and simple:

```text
.github/workflows/repo-validation.yml
```

It should:

- run on pull request and push to main;
- install requirements through the existing validation path;
- run `scripts/validate-repo.sh`;
- not require secrets;
- not require OpenAI;
- not require the real Kaggle dataset;
- not deploy anything;
- not run Docker services unless only validating Compose config and GitHub runner supports Docker Compose.

If GitHub Actions would be risky or too large for this task, defer it to `0025B` and document why.

## Shared Infrastructure Design Note

Add a short note to the docs/backlog reflecting the current architecture decision:

```text
The platform may share infrastructure, but demo data planes stay isolated.
```

For example:

- Controller state may eventually use Postgres.
- Shared vector infrastructure such as Qdrant may eventually exist at the platform layer.
- Individual apps should keep separate collections/indexes/data boundaries.
- Cookbook, stock market, and Army demos should not share one combined vector corpus.
- Qdrant/Postgres implementation is deferred until after evals/control-plane design.

Do not implement Qdrant or Postgres in this task.

## Suggested Files

Create or modify as appropriate:

```text
evals/ai_cookbook/README.md
evals/ai_cookbook/run_evals.py
evals/ai_cookbook/cases/dataset_ask.json
evals/ai_cookbook/cases/saved_recipe_ask.json
evals/ai_cookbook/cases/meal_plan.json
evals/ai_cookbook/cases/importer.json
scripts/validate-repo.sh
scripts/validate-repo.ps1
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
docs/ai-sidecar-architecture.md
docs/repo-map.md
ai-api/README.md
outbox/0025A-add-offline-evals-and-validation-hygiene-results.md
```

Keep changes narrow. Do not do broad refactors.

## Non-Goals

Do not implement:

- Qdrant
- Postgres
- pgvector
- embeddings
- vector database
- persistent generated indexes
- live OpenAI smoke tests
- provider calls during validation except deterministic mock/stub providers
- UI changes
- Cloudflare/deployment changes
- controller/demo launch workflows
- TTL cleanup workflows
- raw dataset commits
- generated index artifact commits
- `.env` or secret commits

## Tests / Evals

Add tests if needed for the eval runner itself.

The combined validation should confirm:

- existing 69+ AI API tests still pass;
- eval runner passes;
- eval runner fails if a required citation is missing, where practical;
- secret-pattern scan still passes;
- no raw dataset files are staged;
- no generated index artifacts are staged.

## Validation

Run from Windows PowerShell in the repo.

Prefer the repo venv for direct pytest/evals:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If the direct Windows pytest path still fails because of local temp-directory permissions, document the exact error and confirm whether `scripts/validate-repo.sh` passes.

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no raw dataset files, generated index artifacts, `.env`, or secrets are staged.

## Outbox Report

Create:

```text
outbox/0025A-add-offline-evals-and-validation-hygiene-results.md
```

Include:

- Summary
- Files changed
- Eval cases added
- Validation hygiene changes
- Whether GitHub Actions was added or deferred
- Shared infrastructure/data-boundary note
- Validation results
- Confirmation that no live OpenAI calls were run
- Confirmation that no Qdrant/Postgres/pgvector/embeddings/vector DB were added
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add .gitignore ai-api evals scripts docs README.md outbox/0025A-add-offline-evals-and-validation-hygiene-results.md

git commit -m "mailbox: complete task 0025A add offline evals and validation hygiene"

git push origin main
```

## Done Criteria

- Offline eval harness exists.
- Dataset ask evals cover grounding, citations, no-match, missing dataset, and secret leakage.
- The harness runs without real Kaggle data, network access, OpenAI keys, or live provider calls.
- Repo validation runs the eval harness or clearly documents why integration is deferred.
- Windows validation guidance/wrapper is improved or the limitation is documented clearly.
- Shared infrastructure vs isolated app data-plane design note exists.
- No Qdrant/Postgres/pgvector/embeddings/vector DB are added.
- No raw dataset files or generated index artifacts are committed.
- No secrets are exposed.
- Documentation is updated.
- Outbox report exists.
- Validation passes or any local-only blocker is clearly documented with the validator still passing.
- Changes are committed and pushed.
