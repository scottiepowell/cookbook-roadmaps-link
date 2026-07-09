# 0029B-11 RAG End-To-End Integration Test Harness Results

## Summary

Added an automated offline E2E integration test harness for the RAG-informed recipe creator/importer path. The test exercises the real `POST /ai/import-recipe` API route with generated local dataset fixtures and the mock provider.

## E2E Test File Added

- `ai-api/tests/test_rag_e2e_integration.py`

The test runs through FastAPI `TestClient` and does not call private importer helpers as the primary behavior under test.

## Fixture Dataset Design

The generated fixture dataset is written during the test run only and includes:

- `Classic Baked Cheesecake`
- `Spaghetti Carbonara`
- `Cheese Omelet`
- `Chicken and Rice Casserole`
- generic distractors such as apple crumble, creamy pasta, egg toast, and rice bowl

The fixture is small, deterministic, and does not require the real `recipe-dataset/` folder.

## API Route Tested

The E2E test posts to:

```text
POST /ai/import-recipe
```

The test forces `AI_PROVIDER=mock`, generated dataset fixtures, and process-local cache settings.

## Strong-Support Cases Covered

The test covers these representative rough notes:

- classic baked cheesecake with cream cheese and graham cracker crust
- carbonara with spaghetti, eggs, parmesan, pancetta, black pepper, and no heavy cream
- omelette spelling variant matching omelet fixture records
- chicken and rice casserole with cream of chicken soup and cheddar

For these cases, the test asserts a schema-valid draft, safe provider/model metadata, ready input quality, citations/provenance, readable original citation titles/snippets, retrieval metadata, relevance/support metadata, bounded context-packing metadata, and cache metadata.

## Weak/Partial Support Case Covered

The broad prompt `make a dessert with sugar and cream` is covered as a weak/partial-support case. The test asserts the response does not claim strong RAG grounding and that the support message remains safe.

## Cache Metadata Behavior Tested

Each strong case is submitted twice. The first request validates cache metadata exists, and the repeated equivalent request asserts index and retrieval cache-hit behavior where exposed by the implementation.

## Safety Checks

The test asserts the public API response does not include:

- raw provider prompt text;
- raw retrieved prompt context;
- local absolute dataset paths;
- API key names or key-like values;
- Authorization header text.

## Validation Results

Passed:

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`
  - 179 pytest tests passed
  - offline evals passed: 28 cases
  - repository validation passed: 7 checks
- `git diff --check`
- `docker compose config --quiet`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`

Direct Windows pytest:

- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` still fails on the known local temp-directory ACL issue: `PermissionError: [WinError 5] Access is denied: C:\Users\scott\AppData\Local\Temp\pytest-of-scott`.
- Git Bash validation passed the full test suite including the new E2E file.

## Live OpenAI

Live OpenAI was not run. This harness is offline/mock-only.

## Artifact Safety

No raw dataset files, generated live artifacts, screenshots, browser automation artifacts, disk cache files, persistent indexes, `.env` files, logs, credentials, or secrets are committed.
