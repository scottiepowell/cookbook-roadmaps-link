# 0029B-10 Local In-Memory Retrieval Cache

## Goal

Add a safe process-local cache for deterministic dataset indexing and retrieval operations used by the RAG-informed recipe creator/importer.

This is the final planned `0029B` RAG hardening task before moving toward `0030` requirements interaction and session memory architecture.

This task follows:

- `0029B-5`: anchor-aware importer retrieval relevance tuning;
- `0029B-6`: retrieval evaluation harness;
- `0029B-7`: bounded RAG context packing and token budget;
- `0029B-8`: dataset normalization for deterministic RAG;
- `0029B-9`: RAG honesty and citation support policy.

## Background

The current RAG path intentionally avoids embeddings, vector databases, Qdrant, Postgres, pgvector, Redis, and persistent generated indexes. Keep that boundary in place.

Full-dataset manual testing with `RECIPE_DATASET_INDEX_LIMIT=5000` can be inefficient if the dataset index or repeated retrieval work is rebuilt too often during one process lifetime. A small process-local cache can improve demo responsiveness without adding persistent storage.

## Primary Objective

Add deterministic in-memory caching that:

- avoids rebuilding identical dataset indexes unnecessarily;
- avoids repeating identical retrieval calculations when inputs and index settings have not changed;
- invalidates safely when dataset settings or source files change;
- exposes safe operational metadata;
- never writes generated indexes or cache files to disk;
- does not introduce production persistent memory.

## Required Work

### 1. Add a cache module

Create a small cache module.

Suggested location:

```text
ai-api/app/retrieval_cache.py
```

or use an appropriate existing module if better.

The module should support process-local caching only.

Suggested cache types:

- dataset index cache;
- retrieval result cache.

Keep the implementation simple. Do not use Redis, SQLite, Postgres, file cache libraries, pickle artifacts, or generated on-disk index artifacts.

### 2. Dataset index cache

Cache built dataset indexes by a deterministic cache key.

Suggested key inputs:

- dataset source identifier;
- dataset source file name or safe fingerprint;
- source file size;
- source file modified time;
- configured record/index limit;
- normalization version or normalization config fingerprint;
- index/scoring version if available.

The cache should invalidate when any key input changes.

Public metadata should use safe fingerprints, not local absolute paths.

### 3. Retrieval result cache

Cache retrieval results by a deterministic key.

Suggested key inputs:

- index cache fingerprint;
- normalized query fingerprint;
- retrieval limit/top-k;
- normalization version;
- scoring version;
- relevant config values.

The retrieval result cache should be bounded.

Suggested bounds:

- max entries: 64-256;
- optional TTL: 5-30 minutes;
- simple LRU or insertion-order eviction is acceptable.

Keep it small and predictable.

### 4. Safe cache metadata

Expose safe metadata for operator visibility where appropriate.

Suggested metadata:

- `cache_enabled`;
- `index_cache_hit`;
- `retrieval_cache_hit`;
- `index_cache_key` as a short safe fingerprint;
- `retrieval_cache_key` as a short safe fingerprint;
- `cache_entry_count`;
- `cache_max_entries`;
- `cache_ttl_seconds` if used;
- `cache_invalidated_reason` if available.

Do not expose raw local paths, private environment values, raw provider prompt text, or full dataset file paths.

### 5. Integrate cache into dataset index/retrieval path

Wire the cache into the local dataset index and importer RAG retrieval path.

Expected behavior:

- first request for a dataset/index configuration builds the index;
- subsequent requests with the same dataset/index configuration reuse the cached index;
- repeated identical retrieval calls can reuse retrieval results;
- changing dataset limit invalidates index/retrieval cache;
- changing dataset source file metadata invalidates index/retrieval cache;
- disabling cache, if supported, restores current rebuild behavior.

Do not change retrieval result shape except for safe metadata additions.

### 6. Configuration

Add simple configuration controls if appropriate.

Suggested options:

- `AI_RETRIEVAL_CACHE_ENABLED=true` by default;
- `AI_RETRIEVAL_CACHE_MAX_ENTRIES=128`;
- `AI_RETRIEVAL_CACHE_TTL_SECONDS=900`.

Defaults should be safe for local demo and normal validation. If config is added, update `.env.example` and docs. Existing tests should pass without user configuration.

### 7. Update API/UI visibility

Update importer/dataset retrieval metadata and demo UI with safe summary fields only.

Example UI display:

```text
Cache: index hit, retrieval miss
Entries: 4/128
```

Keep the UI concise and operator-focused.

### 8. Add tests

Add deterministic tests for:

- index cache hit after first build;
- index cache miss when dataset limit changes;
- index cache miss when source file modified time or size changes;
- retrieval cache hit for identical normalized query/top-k/index config;
- retrieval cache miss when query changes;
- retrieval cache miss when top-k changes;
- cache max-entry eviction;
- TTL expiration if TTL is implemented;
- cache disabled path if config supports disabling;
- public metadata uses safe fingerprints only;
- normal fixture-based retrieval/eval behavior remains deterministic.

### 9. Performance smoke evidence

Add lightweight offline evidence that cache behavior works without requiring the real `recipe-dataset/` folder.

Acceptable evidence:

- a test asserts build logic is called once for repeated identical configs;
- a script prints first/second request cache hit metadata using generated fixtures;
- outbox report records expected behavior.

A full benchmark is not required.

### 10. Update docs

Update as needed:

- `docs/local-recipe-dataset-adapter.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/ai-evals-plan.md`;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md` if relevant;
- `.env.example` if config options are added.

Create:

```text
outbox/0029B-10-local-in-memory-retrieval-cache-results.md
```

## Acceptance Criteria

- Process-local in-memory cache exists for dataset index and/or retrieval results.
- Cache keys are deterministic and invalidate on dataset/config changes.
- Cache is bounded by max entries and optional TTL.
- Cache metadata is safe and uses fingerprints rather than local paths.
- Retrieval correctness is unchanged.
- Existing retrieval evals still pass.
- Context packing, normalization, and RAG support policy behavior still pass.
- No persistent generated index files are created.
- Normal validation remains offline and mock-only.
- No live OpenAI calls are required.
- No raw dataset files or generated live artifacts are committed.

## Validation

Run:

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

The live smoke and live eval wrappers should skip cleanly unless explicit opt-in settings are present.

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI during normal validation.

## Optional Manual Validation Guidance

After completion, optional manual live validation can use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

Manual prompts:

```text
classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight

carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream

omelette for 4 with eggs cheddar onions butter folded in a skillet

chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly
```

Expected signs:

- first request for a dataset/index config shows index cache miss/build;
- repeated requests show index cache hit;
- repeated identical query may show retrieval cache hit;
- changed query shows retrieval cache miss;
- changed dataset limit invalidates cache;
- retrieval results remain materially the same;
- UI/API metadata remains safe and concise.

## Non-Goals

- No embeddings
- No vector database
- No Qdrant
- No Postgres
- No pgvector
- No Redis
- No persistent generated index
- No disk cache
- No production storage
- No production auth
- No paid access
- No public route exposure
- No Cloudflare changes
- No upstream Vanilla Cookbook frontend rewrite
- No browser automation
- No screenshots
- No raw dataset commits
- No large food ontology
- No ML reranker
- No long-term memory

## Commit

```bash
git add ai-api evals docs README.md .env.example outbox/0029B-10-local-in-memory-retrieval-cache-results.md

git commit -m "mailbox: complete task 0029B-10 local in-memory retrieval cache"

git push origin main
```
