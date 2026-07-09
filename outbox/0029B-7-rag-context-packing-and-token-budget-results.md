## Summary

Added a deterministic bounded RAG context-packing layer for the importer/recipe-creator path. The importer now sends concise, relevance-ranked dataset snippets to the provider instead of raw retrieved records, and the demo UI shows safe packing metadata alongside the existing citations/provenance view.

## Problem Observed

The importer had already become functional again, but it still handed too much unbounded retrieved content toward the provider prompt. That made prompt size less predictable and left the UI without clear evidence of how much of the retrieved set actually made it into the provider context.

## Context Packing Changes

- Added `ai-api/app/rag_context.py` with deterministic packing defaults and a bounded prompt builder.
- Kept the importer prompt focused on user notes, serving target, and a short packed context block.
- Preferred strong/moderate matches over weak ones, with weak examples only included when no stronger support exists.
- Bounded example count and per-field text length with character limits instead of a tokenizer dependency.
- Added safe response metadata for packed counts, packed IDs, dropped IDs, budget warnings, and weak-example status.
- Updated the demo UI importer panel to display retrieved examples, packed examples, dropped examples, context chars used, weak-example status, and context-budget warnings.

## Tests Added

- `ai-api/tests/test_rag_context.py`
- `ai-api/tests/test_importer.py`
- `ai-api/tests/test_demo_ui.py`

These tests cover strong-vs-weak selection, weak-only fallback, truncation, context-budget bounds, packed ID/provenance alignment, safe metadata rendering, and prompt construction using packed context.

## Manual Validation Notes

No live OpenAI validation was run for this task. The manual live importer launch command remains documented for later operator testing, but this task stayed on the offline/mock-only path.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` passed.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` hit the known Windows temp-directory ACL issue on this machine.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` passed.
- `git diff --check` passed; only line-ending normalization warnings were emitted.
- `docker compose config --quiet` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` skipped cleanly without live opt-in.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` skipped cleanly without live opt-in.

## Remaining Limitations

- The packer uses fixed character budgets, so it is bounded and predictable but not token-accurate.
- Direct Windows `pytest` still hits the existing temp ACL problem here; the Git Bash validator is the reliable full-suite path.

## Recommended Next Task

Continue with `0029C: Session And Metering Schema Draft` so the production access and metering architecture can build on the now-bounded importer context path.

## Artifact Safety Confirmation

No raw dataset files, generated live artifacts, `.tmp-ai-demo/`, secrets, env files, screenshots, logs, credentials, or provider responses were committed.
