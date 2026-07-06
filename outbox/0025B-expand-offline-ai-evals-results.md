# 0025B Expand Offline AI Evals Results

## Summary

Expanded the offline AI cookbook eval harness from dataset-ask-only coverage to broader workflow coverage while keeping it offline, deterministic, and fixture-driven.

Changes made:

- Added two more indexed dataset ask/RAG cases in `evals/ai_cookbook/dataset_ask_cases.json`.
- Added `evals/ai_cookbook/workflow_cases.json` for saved-recipe Ask My Cookbook, structured importer, and meal-plan eval fixtures.
- Refactored `evals/ai_cookbook/run_evals.py` to run dataset ask, saved-recipe ask, importer, meal-plan, and provider-config evals.
- Expanded shared secret-like leakage checks for:
  - `OPENAI_API_KEY`
  - `sk-`
  - `Authorization:`
  - `.env`
  - `raw provider config`
  - `CLOUDFLARE_TUNNEL_TOKEN`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ACCESS_KEY_ID`
- Strengthened citation checks for dataset citations, saved recipe ask citations, and meal-plan saved recipe references.
- Updated `evals/ai_cookbook/README.md` to describe the broader coverage.

The requested `inbox/0025B-expand-offline-ai-evals.md` file was not present in this checkout, but all explicitly listed 0025A prerequisite files were present. I proceeded from the task text provided in the prompt.

## Validation

Passed:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

Result: 9 offline eval cases passed.

Direct Windows pytest command:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Result: failed because pytest could not access the local temp base directory:

```text
PermissionError: [WinError 5] Access is denied: 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott'
```

Before that setup failure pattern, 32 tests passed. This matches the known local temp-directory permission issue.

Passed via repository validator:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
```

The first sandboxed attempt failed before script execution with:

```text
fatal error - couldn't create signal pipe, Win32 error 5
```

Rerunning Git Bash outside the sandbox passed:

```text
69 passed, 1 warning
Offline evals passed: 9 cases.
Repository validation passed: 7 checks.
```

Passed:

```powershell
git diff --check
docker compose config --quiet
```

## Safety Checks

Before staging, `git status --short` showed only intended tracked eval changes plus the new workflow fixture. Local ignored `.env`, `recipe-dataset/`, `.tmp-pytest*`, `.venv`, and `.pytest_cache` were not staged.

No Qdrant, Postgres, pgvector, embeddings, vector DB, generated persistent indexes, live OpenAI tests, UI, deployment, controller/demo launch workflows, or TTL cleanup workflows were added.
