## Summary

Added a deterministic dataset normalization layer for local recipe indexing and scoring. The importer and dataset retrieval paths now normalize aliases, punctuation, Unicode variants, accents, and common singular/plural forms before scoring, while preserving original recipe values for snippets, citations, provenance, and display.

## Problem Observed

The RAG importer and dataset retrieval path were already functional, but ranking still depended too much on raw surface forms. That left common recipe variants such as `omelette`, `no-bake`, `graham crackers`, and `parmigiano-reggiano` more brittle than they should be for a deterministic index.

## Normalization Changes

- Added `ai-api/app/dataset_normalization.py` with deterministic text cleanup, alias handling, singular/plural normalization, safe tokenization, and small phrase extraction helpers.
- Updated the dataset index to score against normalized fields while preserving original recipe values for output.
- Kept the phrase list small and explicit so terms such as `cream cheese`, `graham cracker crust`, `black pepper`, `no bake`, and `cream of chicken soup` remain matchable without introducing a large ontology.
- Kept the original record values intact for citations, snippets, and provenance.

## Retrieval/Eval Changes

- Extended the deterministic retrieval fixture dataset with no-bake cheesecake, cream-cheese frosting, and cream-of-chicken-soup casserole normalization targets.
- Added retrieval cases for `omelette`, `no bake` versus `no-bake`, `graham crackers`, `parmigiano-reggiano`, and `cream of chicken soup`.
- Added unit tests for normalization helpers, normalized index scoring, phrase extraction, alias handling, singular/plural behavior, and preservation of original display values.

## Manual Validation Notes

No live OpenAI validation was run for this task. The optional full local RAG launch command remains documented for later operator use, but this task stayed on the offline/mock-only path.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed with 28 offline eval cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` hit the known Windows temp-directory ACL issue on this machine.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed: 158 tests, offline evals, and repo validation checks.
- `git diff --check` passed; only line-ending normalization warnings were emitted.
- `docker compose config --quiet` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly without live opt-in.

## Remaining Limitations

- The normalization layer is intentionally conservative. It improves deterministic matching for common recipe variants, but it is not a linguistic parser and it does not try to model every food synonym.
- Direct Windows `pytest` still hits the existing temp ACL problem here; the Git Bash validator is the reliable full-suite path.

## Recommended Next Task

Continue with `0029C: Session And Metering Schema Draft` so the production access and metering architecture can build on the normalized and bounded retrieval path.

## Artifact Safety Confirmation

No raw dataset files, generated live artifacts, `.tmp-ai-demo/`, secrets, env files, screenshots, logs, credentials, or provider responses were committed.
