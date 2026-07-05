# 0025A Add Offline Evals And Validation Hygiene Results

## Summary

Added an offline AI cookbook eval harness and validation hygiene for Windows local runs. The evals focus on dataset ask grounding, citation completeness, no-match behavior, missing-dataset behavior, invented/non-retrieved source IDs where detectable, and secret-like output leakage.

No Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, live OpenAI smoke tests, UI changes, deployment changes, controller workflows, raw dataset files, generated index artifacts, `.env`, or secrets were added.

## Prerequisite Check

Confirmed before implementation:

- `ai-api/app/dataset_rag.py` exists.
- `ai-api/app/dataset_retrieval.py` exists.
- `ai-api/app/dataset_index.py` exists.
- `ai-api/app/dataset_adapter.py` exists.
- `ai-api/tests/test_dataset_ask.py` exists.
- `outbox/0024D-add-rag-over-indexed-dataset-results.md` exists.
- `.gitignore` ignores `recipe-dataset/`.
- `.gitignore` ignores `.tmp-pytest*/`.

## Files Created Or Modified

- Created `evals/ai_cookbook/run_evals.py`
- Created `evals/ai_cookbook/dataset_ask_cases.json`
- Created `evals/ai_cookbook/README.md`
- Created `scripts/validate-repo.ps1`
- Created `docs/shared-infrastructure-data-boundaries.md`
- Created `inbox/0025A-add-offline-evals-and-validation-hygiene.md`
- Created `outbox/0025A-add-offline-evals-and-validation-hygiene-results.md`
- Modified `scripts/validate-repo.sh`
- Modified `README.md`
- Modified `docs/ai-evals-plan.md`
- Modified `docs/ai-implementation-backlog.md`
- Modified `docs/repo-map.md`
- Modified `docs/repo-validation.md`

## Eval Harness

- `evals/ai_cookbook/run_evals.py` uses stdlib JSON fixtures and returns non-zero on failed checks.
- `evals/ai_cookbook/dataset_ask_cases.json` uses tiny generated CSV fixture rows only.
- The eval runner sets `AI_PROVIDER=mock` and does not require the real Kaggle dataset, network access, OpenAI keys, live providers, Docker runtime, or Vanilla Cookbook DB.
- It fails on missing required citations, no-match failures, detectable non-retrieved source IDs, and secret-like output patterns: `OPENAI_API_KEY`, `sk-`, `Authorization:`, `.env`, and `raw provider config`.

## Validation Hygiene

- `scripts/validate-repo.sh` now runs offline evals after the AI API pytest suite when `evals/ai_cookbook/run_evals.py` exists.
- `scripts/validate-repo.ps1` sets `TMP`/`TEMP` to `.tmp-pytest/`, uses an explicit pytest base temp directory, runs evals, and falls back to Git Bash validation if direct Windows pytest fails.
- `.tmp-pytest*/` remains ignored.

## Shared Infrastructure Note

Created `docs/shared-infrastructure-data-boundaries.md`.

It documents that the platform may eventually share infrastructure, including controller state in Postgres or Qdrant as infrastructure, but those are not implemented now. Cookbook, stock market, and Army demos should keep separate collections, indexes, schemas, credentials, and data boundaries and should not share one combined vector corpus.

## GitHub Actions

No GitHub Actions workflow changes were needed in this task because repository validation already runs through `scripts/validate-repo.sh`. The script now runs offline evals, so existing CI callers inherit the eval harness without adding a separate workflow.

## Validation

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: failed with Windows temp-directory `PermissionError` while scanning/creating pytest temp directories.
- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 3 eval cases.
- `& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh`: passed.
  - 69 AI API tests passed.
  - 3 offline eval cases passed.
  - Shell syntax, Docker Compose configuration, whitespace, local Markdown links, old-domain guard, and secret-pattern scan passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.

## Safety Confirmation

Before commit, confirm:

- no files under `recipe-dataset/` are staged;
- no generated index artifacts are staged;
- `.env` is not staged;
- no secrets are staged.
- no Qdrant, Postgres, pgvector, embeddings, vector DB, or persistent generated indexes were added.

## Recommended Next Task

Add broader offline eval cases for importer, saved-recipe RAG, meal planning, and dataset ask before adding CI-specific reporting or live provider smoke tests.
