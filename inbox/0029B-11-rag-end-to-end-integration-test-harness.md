# 0029B-11 RAG End-To-End Integration Test Harness

## Goal

Add an automated end-to-end integration test harness for the RAG-informed recipe creator/importer path.

This is a closing `0029B` validation task after the RAG hardening line. It should prove that the major RAG features work together as one workflow, not only as isolated unit/eval cases.

This task follows:

- `0029B-5`: anchor-aware importer retrieval relevance tuning;
- `0029B-6`: retrieval evaluation harness;
- `0029B-7`: bounded RAG context packing and token budget;
- `0029B-8`: dataset normalization for deterministic RAG;
- `0029B-9`: RAG honesty and citation support policy;
- `0029B-10`: local in-memory retrieval cache.

## Background

The repo now has many focused tests and offline evals, but the project still needs a small end-to-end integration harness that exercises the full RAG importer pipeline from API request to validated response.

The harness should answer:

```text
Can the app take rough user recipe notes, run deterministic RAG over generated fixture data, pack bounded context, classify support honestly, use the mock provider path, and return a safe schema-valid recipe response with citations and metadata?
```

This should be automated and offline. It should not rely on manual browser testing or live OpenAI calls.

## Primary Objective

Create an automated RAG end-to-end integration test that covers the complete importer workflow:

```text
request input
  -> input quality gate
  -> dataset adapter / generated fixture dataset
  -> dataset normalization
  -> deterministic retrieval
  -> retrieval relevance metadata
  -> context packing
  -> RAG support policy
  -> process-local cache metadata if available
  -> mock provider generation
  -> schema validation
  -> citations/provenance
  -> safe API response
```

## Required Work

### 1. Add an E2E integration test file

Create a dedicated integration test file.

Suggested location:

```text
ai-api/tests/test_rag_e2e_integration.py
```

The test should use FastAPI `TestClient` or the project’s existing test client pattern.

It should exercise the real API route, not only private functions.

### 2. Use generated fixture data only

The test must create a temporary local recipe dataset fixture during the test run.

Do not require the real `recipe-dataset/` folder.

Do not commit raw dataset files.

The fixture should include:

- at least one strong cheesecake record;
- at least one carbonara record;
- at least one omelet/omelette record;
- at least one chicken-and-rice casserole record;
- distractor records that share generic terms but should not be treated as strong support.

Keep fixture size small and deterministic.

### 3. Run the importer endpoint end-to-end

At minimum, test `POST /ai/import-recipe` with a representative rough recipe note.

Suggested cases:

```text
classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight

carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream

omelette for 4 with eggs cheddar onions butter folded in a skillet

chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar bake until bubbly
```

Use the mock provider path. Do not run live OpenAI.

### 4. Assert the complete RAG response shape

For each E2E case, assert:

- HTTP 200;
- `draft` exists and passes schema expectations;
- title is present;
- servings are present and reasonable;
- ingredients list is non-empty;
- instructions list is non-empty;
- provider/model metadata is safe;
- input quality status is `ready` or expected recoverable status;
- retrieval metadata exists;
- retrieved count is greater than zero for fixture-backed cases;
- citations exist when support is not none;
- citations include provenance/source identifiers;
- original citation titles/snippets remain readable;
- retrieval relevance/support metadata exists;
- context-packing metadata exists if implemented by `0029B-7`;
- cache metadata exists if implemented by `0029B-10`;
- no raw provider prompt text is returned;
- no local absolute dataset paths are returned.

### 5. Assert RAG feature interactions

The E2E test should prove that the previous RAG hardening layers interact correctly.

Assert at least:

- normalization works in the API path, for example `omelette` matches `omelet` fixture records;
- phrase preservation works, for example `cream cheese` and `graham cracker crust` support cheesecake retrieval;
- bounded context packing selects only a limited number of examples;
- weak/broad examples are not silently described as strong authoritative support;
- support policy is present and uses one of the allowed levels: `strong`, `moderate`, `weak`, `none`;
- cache metadata changes appropriately between first and repeated equivalent requests if cache is available.

### 6. Include a no/weak-support case

Add one E2E case that intentionally has weak or no fixture support.

Example:

```text
make a dessert with sugar and cream
```

Expected behavior:

- either controlled clarification/input-quality behavior or a generated draft with weak/none support;
- no claim that the draft is strongly RAG-grounded;
- safe support message;
- assumptions/warnings are disclosed as appropriate.

### 7. Add optional integration script

If useful, add a small offline script or PowerShell wrapper for local developer use.

Suggested names:

```text
scripts/test-rag-e2e-local.ps1
scripts/test-rag-e2e-local.py
```

This is optional if pytest coverage is sufficient.

The script must remain offline and mock-only.

### 8. Integrate into normal validation

Ensure the E2E integration test runs through the existing reliable validation path:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If the test is too slow for normal validation, keep it lightweight rather than excluding it.

The existing eval runner should continue to pass.

### 9. Update docs

Update as needed:

- `docs/ai-evals-plan.md`;
- `docs/ai-feature-status.md`;
- `docs/ai-live-demo-runbook.md`;
- `docs/ai-implementation-backlog.md`;
- `README.md` if relevant.

Create:

```text
outbox/0029B-11-rag-end-to-end-integration-test-harness-results.md
```

## Acceptance Criteria

- An automated offline E2E integration test exists for the RAG importer workflow.
- The test exercises the real importer API route using generated fixture data.
- The test covers retrieval, normalization, context packing, support policy, citations/provenance, schema validation, and cache metadata if available.
- At least one strong-support case and one weak/no-support case are covered.
- Normal validation remains offline and mock-only.
- The test does not require the real `recipe-dataset/` folder.
- The test does not require live OpenAI calls.
- No raw dataset files, generated live artifacts, screenshots, browser automation artifacts, or persistent indexes are committed.

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

## Non-Goals

- No live OpenAI calls
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
git add ai-api evals docs README.md scripts outbox/0029B-11-rag-end-to-end-integration-test-harness-results.md

git commit -m "mailbox: complete task 0029B-11 rag end-to-end integration test harness"

git push origin main
```
