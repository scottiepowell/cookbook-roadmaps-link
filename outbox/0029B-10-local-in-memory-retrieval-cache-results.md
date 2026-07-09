# 0029B-10 Local In-Memory Retrieval Cache Results

## Summary

Completed the process-local retrieval cache hardening task for the RAG-informed recipe creator/importer. The implementation adds bounded in-memory caching for dataset indexes and retrieval results, exposes safe cache metadata in API/UI responses, and keeps normal validation offline and mock-only.

## Cache Implemented

- Added `ai-api/app/retrieval_cache.py` with process-local caches for dataset indexes and retrieval results.
- Added cache settings:
  - `AI_RETRIEVAL_CACHE_ENABLED=true`
  - `AI_RETRIEVAL_CACHE_MAX_ENTRIES=128`
  - `AI_RETRIEVAL_CACHE_TTL_SECONDS=900`
- Wired index caching into `build_index_from_dataset()` and dataset search/importer retrieval paths.
- Added UI display for concise cache status such as index hit/miss, retrieval hit/miss, entry count, and TTL.

## Cache Keys And Invalidation

Dataset index cache keys include safe fingerprints for:

- dataset source identity;
- expected dataset file names;
- source file size and modified time;
- configured record/index limit;
- normalization version;
- scoring/cache schema version.

Retrieval result cache keys include:

- index cache fingerprint;
- normalized query text, tokens, and phrases;
- retrieval limit/top-k;
- normalization version;
- scoring/cache schema version.

Changing the dataset limit, source file metadata, query, top-k, normalization version, or scoring/cache version invalidates the relevant cache entry. The cache is bounded by max entries and supports TTL expiration.

## Safe Metadata

API and UI metadata expose only:

- `cache_enabled`;
- `index_cache_hit`;
- `retrieval_cache_hit`;
- short safe cache fingerprints;
- cache entry count;
- max entries;
- TTL seconds;
- invalidation reason when applicable.

The metadata does not expose raw local paths, provider prompts, provider responses, API keys, `.env` values, raw dataset contents, or secret-like values.

## Recovery Fixes

The first recovery issue was a Pydantic nested-model mismatch in `DatasetAskRetrievalMetadata`. The dataset Ask path embedded a `DatasetIndexSummaryResponse` instance created after schema redefinition, while the retrieval metadata field expected the earlier schema identity. The fix converts nested index summaries with `.model_dump(exclude={"cache"})` in `ai-api/app/dataset_rag.py`.

The second recovery issue was a `run_evals.py` hang after cache hits. Root cause was a non-reentrant cache lock path: cache-hit metadata called `entry_count` while already holding `threading.Lock`. The fix computes entry counts without re-acquiring the same lock. The eval runner now also emits safe per-case progress lines and writes an ignored debug log to `.tmp-ai-demo/eval-debug/run-evals-debug.log`.

## Tests Added

Added `ai-api/tests/test_retrieval_cache.py` covering:

- index cache hit after first build;
- index cache miss when dataset limit changes;
- index cache miss when source file metadata changes;
- retrieval cache hit for identical normalized query/top-k/index config;
- retrieval cache miss when query changes;
- retrieval cache miss when top-k changes;
- max-entry eviction;
- TTL expiration;
- cache disabled behavior;
- safe fingerprint metadata;
- deterministic fixture retrieval with caching.

Updated UI tests for cache metadata display.

## Validation Results

Passed:

- `& .\.venv\Scripts\python.exe -u evals\ai_cookbook\run_evals.py`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - 174 pytest tests passed
  - offline evals passed: 28 cases
  - repository validation passed: 7 checks
- `git diff --check`
- `docker compose config --quiet`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`

Direct Windows pytest:

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` still fails on the known local temp-directory ACL issue: `PermissionError: [WinError 5] Access is denied: C:\Users\scott\AppData\Local\Temp\pytest-of-scott`.
- The Git Bash validator path passed the full 174-test suite.

## Live OpenAI

Live OpenAI was not run. The live smoke and live eval wrappers skipped cleanly because explicit live opt-in settings were not present.

## Artifact Safety

No persistent generated indexes, disk cache, Redis, SQLite cache, production memory, raw dataset files, `.tmp-ai-demo/` artifacts, screenshots, logs, credentials, `.env` files, raw provider responses, or API keys are committed.

Recommended next task: move from the completed 0029B RAG hardening sequence into 0030 requirements interaction and session memory architecture.
