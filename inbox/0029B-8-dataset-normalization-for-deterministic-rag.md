# 0029B-8 Dataset Normalization For Deterministic RAG

## Goal

Improve deterministic RAG retrieval quality by normalizing dataset records before indexing and scoring.

This task follows:

- `0029B-5`: anchor-aware importer retrieval relevance tuning;
- `0029B-6`: retrieval evaluation harness;
- `0029B-7`: bounded RAG context packing and token budget.

The next hardening step is to make indexed recipe text cleaner and more consistent so the deterministic keyword/anchor scorer has better input.

## Background

The current dataset index works and can search up to the configured dataset limit, but recipe datasets often contain messy text:

- inconsistent casing;
- punctuation differences;
- Unicode accents and curly punctuation;
- singular/plural mismatches;
- ingredient blobs;
- instruction blobs;
- duplicated or near-duplicated titles;
- generic terms that overpower dish intent;
- inconsistent recipe IDs;
- multi-word ingredients split into weak single terms.

The current 0029 RAG strategy intentionally avoids embeddings, vector databases, Qdrant, Postgres, pgvector, or persistent generated indexes. This task should stay in that boundary and improve deterministic retrieval using lightweight normalization only.

## Primary Objective

Add a deterministic dataset normalization layer used by the local recipe dataset index so retrieval is more robust while preserving original record values for display, citations, and provenance.

## Required Work

### 1. Add normalization module

Create or update a module for text normalization.

Suggested location:

```text
ai-api/app/dataset_normalization.py
```

or an appropriate existing module if a better fit exists.

The module should provide deterministic helpers for:

- lowercasing for index terms;
- trimming and whitespace normalization;
- punctuation normalization;
- Unicode quote/dash normalization;
- optional accent folding for matching;
- singular/plural normalization for common food terms;
- safe tokenization;
- phrase extraction for important multi-word ingredients/dish names.

Preserve original raw values for API display, snippets, citations, and provenance.

### 2. Protect important multi-word terms

The index should recognize and preserve important phrases such as:

- `cream cheese`;
- `graham cracker`;
- `graham cracker crust`;
- `black pepper`;
- `pasta water`;
- `heavy cream`;
- `cream of chicken`;
- `cream of mushroom`;
- `chicken and rice`;
- `no bake` / `no-bake`;
- `baked cheesecake`;
- `egg yolk`;
- `parmesan cheese`;
- `cheddar cheese`;
- `olive oil`;
- `brown sugar`.

Keep the phrase list small, explicit, and easy to extend. Do not build a large ontology.

### 3. Normalize common variants and aliases

Add a small alias/variant map for deterministic matching.

Examples:

- `omelette` -> `omelet`;
- `parmigiano reggiano` -> `parmesan`;
- `parmigiano-reggiano` -> `parmesan`;
- `chiles` / `chili` variants if useful;
- `no-bake` -> `no bake`;
- `graham crackers` -> `graham cracker`;
- `eggs` -> `egg`;
- `tomatoes` -> `tomato`.

Keep it conservative. Do not over-normalize in a way that changes recipe meaning.

### 4. Improve ingredient/instruction field handling

If dataset records contain ingredient or instruction blobs, normalize them into indexable text more cleanly.

Potential improvements:

- split list-like strings on common separators when safe;
- remove repeated whitespace;
- preserve numbers/units only when useful;
- keep ingredient phrases together;
- avoid letting long instruction text drown title/ingredient matches.

Do not alter the public displayed ingredient/instruction values unless existing display behavior already does so.

### 5. Add normalized fields to index internals

The dataset index should use normalized fields for scoring while retaining original fields for API responses.

Suggested internal structure:

```text
original_title
original_ingredients
original_instructions
normalized_title
normalized_ingredients
normalized_instructions
normalized_tags
phrases
aliases_applied
```

Only expose safe summary metadata if useful. Do not expose large internal normalized text blobs in the UI/API unless needed for debugging and safe.

### 6. Improve generic term handling after normalization

Review how generic terms are handled after normalization.

Terms like these should not overpower dish-specific anchors:

- cream;
- cheese;
- sugar;
- bake;
- dessert;
- chicken;
- dinner;
- pasta;
- rice;
- skillet;
- butter.

The normalization layer should make it easier to distinguish `cream cheese` from generic `cream` and `cheese` matches.

### 7. Update retrieval evals

Extend the retrieval eval harness from `0029B-6` with cases that prove normalization helps.

Required eval/test cases:

- `omelette` query matches `omelet` records;
- `no-bake cheesecake` and `no bake cheesecake` normalize consistently;
- `cream cheese` does not degrade into unrelated cream/cheese records;
- `graham crackers` matches `graham cracker crust`;
- `parmigiano-reggiano` or `parmigiano reggiano` supports parmesan/carbonara matching;
- `cream of chicken soup` supports chicken/rice casserole matching;
- plural/singular variants do not break matches.

### 8. Add unit tests

Add deterministic tests for:

- text normalization;
- phrase extraction;
- alias mapping;
- singular/plural normalization;
- normalized index scoring;
- preservation of original display/citation values;
- no secret/private path leakage in normalization metadata.

### 9. Update docs

Update as needed:

- `docs/ai-evals-plan.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/local-recipe-dataset-adapter.md` if relevant;
- `docs/ai-feature-status.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md` if relevant.

Create:

```text
outbox/0029B-8-dataset-normalization-for-deterministic-rag-results.md
```

## Acceptance Criteria

- Dataset normalization helpers exist and are deterministic.
- The dataset index scores against normalized text while preserving original fields for response/citation display.
- Important multi-word recipe terms are preserved for matching.
- Conservative alias/variant mapping exists and is tested.
- Retrieval evals cover normalization-sensitive cases.
- Existing retrieval relevance cases still pass.
- Context-packing behavior from `0029B-7` still works.
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

Manual prompts to check normalization behavior:

```text
omelette for 4 with eggs cheddar onions butter folded in a skillet

no-bake cheesecake for 4 with cream cheese vanilla sugar graham cracker crust chill until firm

carbonara for 4 with spaghetti parmigiano-reggiano eggs pancetta black pepper pasta water off heat no heavy cream

chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly
```

Expected signs:

- all return 200;
- retrieval metadata shows `dataset_limit=5000`;
- relevance category is reasonable;
- citations are materially relevant;
- original citation titles/snippets remain readable;
- no raw normalized internals or private paths are exposed in UI.

## Non-Goals

- No embeddings
- No vector database
- No Qdrant
- No Postgres
- No pgvector
- No persistent generated index
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

## Commit

```bash
git add ai-api evals docs README.md outbox/0029B-8-dataset-normalization-for-deterministic-rag-results.md

git commit -m "mailbox: complete task 0029B-8 dataset normalization for deterministic rag"

git push origin main
```
