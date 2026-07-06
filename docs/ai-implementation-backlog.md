# AI Implementation Backlog

This backlog breaks the medium-path AI design into follow-on mailbox tasks. Task numbers are proposed and may change if new operational fixes are needed first.

## 0016: Scaffold AI FastAPI Sidecar

Status: complete.

Goal: Add the minimal `ai-api` FastAPI service without AI features.

Files likely touched:

- `ai-api/`
- `ai-api/Dockerfile`
- `ai-api/pyproject.toml` or `requirements.txt`
- `docker-compose.yml`
- `.env.example`
- `.github/workflows/repo-validation.yml`
- `docs/runtime-scaffold.md`

Validation:

- `pytest ai-api/tests`
- `docker compose config --quiet`
- `bash scripts/validate-repo.sh`

Done criteria:

- `GET /health` works.
- Tests run without provider keys.
- Compose includes `ai-api` without exposing public EC2 ports.

## 0017: Add DB Schema Inspection And Read-Only Recipe Reader

Status: complete.

Goal: Inspect the cookbook SQLite schema safely and add a read-only recipe reader.

Files likely touched:

- `ai-api/app/recipe_reader.py`
- `ai-api/tests/test_recipe_reader.py`
- `ai-api/tests/fixtures/`
- `docs/ai-schema-notes.md`

Validation:

- reader tests with fixture SQLite DB;
- no writes to fixture DB;
- repo validation.

Done criteria:

- Recipe document model captures IDs, titles, ingredients, steps, tags, and unknowns.
- Reader uses read-only SQLite access.
- Schema notes document known and unknown fields.

## 0018: Add Deterministic Recipe Search API

Status: complete.

Goal: Add keyword search before embeddings or model-based retrieval.

Files likely touched:

- `ai-api/app/search.py`
- `ai-api/app/routes/recipes.py`
- `ai-api/tests/test_search.py`
- `docs/ai-sidecar-architecture.md`

Validation:

- search unit tests;
- FastAPI `TestClient` endpoint tests;
- repo validation.

Done criteria:

- `GET /recipes/search?q=` and/or `POST /recipes/search` return recipe IDs, titles, snippets, and match reasons.
- Search works without provider keys.
- Empty and no-match cases are covered.

## 0019: Add AI Provider Abstraction And Mock Provider

Status: complete.

Goal: Add a provider interface that supports hosted providers later while keeping tests offline.

Files likely touched:

- `ai-api/app/providers/`
- `ai-api/app/config.py`
- `ai-api/tests/test_config.py`
- `ai-api/tests/test_providers.py`
- `.env.example`

Validation:

- provider config tests;
- mock provider tests;
- no live API calls in CI;
- repo validation.

Done criteria:

- OpenAI config path exists but is optional, defaults to `gpt-5.4-nano`, and records `gpt-5.4-mini` as the configured fallback.
- Mock provider supports deterministic responses.
- `/ai/config` reports non-secret provider availability only.

## 0021: Add Structured Recipe Importer

Status: complete.

Goal: Parse pasted recipe text into schema-constrained draft recipe JSON.

Files likely touched:

- `ai-api/app/schemas/importer.py`
- `ai-api/app/routes/ai.py`
- `ai-api/tests/test_import_recipe.py`
- `ai-api/tests/fixtures/importer_inputs/`
- `evals/ai_cookbook/importer_cases.yaml`

Validation:

- Pydantic schema tests;
- golden fixture tests;
- mock provider tests;
- repo validation.

Done criteria:

- `POST /ai/import-recipe` returns valid draft JSON.
- Invalid or incomplete input returns a controlled response.
- No direct cookbook DB write-back exists.

## 0022: Add RAG Ask Endpoint

Status: complete.

Goal: Answer questions over saved recipes with retrieval, grounding, and citations.

Files likely touched:

- `ai-api/app/rag.py`
- `ai-api/app/routes/ai.py`
- `ai-api/tests/test_ai_ask.py`
- `evals/ai_cookbook/rag_cases.yaml`

Validation:

- retrieval tests;
- no-match tests;
- citation tests;
- mock provider RAG evals;
- repo validation.

Done criteria:

- `POST /ai/ask` cites recipe IDs/titles.
- No-match questions say the system does not know.
- Secret-probe tests pass.

## 0023A: Add Meal Planner Foundation

Status: complete.

Goal: Add deterministic saved-recipe candidate selection and meal-plan foundation schemas without adding the meal-plan endpoint.

Files likely touched:

- `ai-api/app/meal_planner.py`
- `ai-api/app/schemas.py`
- `ai-api/tests/test_meal_planner.py`

Validation:

- schema tests;
- saved-recipe candidate selection tests;
- excluded ingredient filtering tests;
- no provider calls;
- no database write-back;
- repo validation.

Done criteria:

- Foundation schemas exist.
- Candidate selection returns only saved recipe references.
- Excluded ingredients produce deterministic filtering or warnings.
- No `POST /ai/meal-plan` route exists yet.

## 0023B: Add Meal Planner Endpoint

Status: complete.

Goal: Generate a structured meal plan from selected saved recipes.

Files likely touched:

- `ai-api/app/schemas/meal_plan.py`
- `ai-api/app/meal_planner.py`
- `ai-api/tests/test_meal_plan.py`
- `evals/ai_cookbook/meal_plan_cases.yaml`

Validation:

- schema tests;
- saved-recipe constraint tests;
- shopping-list grouping tests;
- repo validation.

Done criteria:

- `POST /ai/meal-plan` returns validated JSON.
- Plans cite saved recipes unless external suggestions are explicitly allowed.
- Medical/nutrition certainty claims are avoided.
- No shopping-list generation, indexing, embeddings, or database write-back is added.

## 0024A: Add Local Recipe Dataset Adapter

Status: complete.

Goal: Inspect local Kaggle recipe dataset files without committing raw data or building an index.

Files likely touched:

- `ai-api/app/dataset_adapter.py`
- `ai-api/tests/test_dataset_adapter.py`
- `docs/local-recipe-dataset-adapter.md`

Validation:

- generated temporary CSV/SQLite/metadata fixtures;
- no raw `recipe-dataset/` files staged;
- repo validation.

Done criteria:

- `RECIPE_DATASET_DIR` can point at a local dataset directory.
- Expected files are detected with safe warnings.
- CSV, SQLite, and metadata previews return structured objects.
- No embeddings, vector DB, RAG over the dataset, image ingestion, provider calls, or write-back are added.

## 0024B: Build Local Deterministic Recipe Index

Status: complete.

Goal: Build a bounded, local-only deterministic keyword index over records read through the 0024A dataset adapter.

Files likely touched:

- `ai-api/app/dataset_adapter.py`
- `ai-api/app/dataset_index.py`
- `ai-api/tests/test_dataset_index.py`
- `scripts/inspect-recipe-index.py`
- `docs/local-recipe-dataset-adapter.md`

Validation:

- no raw dataset files committed;
- no generated index artifacts committed;
- deterministic offline tests;
- repo validation.

Done criteria:

- bounded CSV/SQLite record reading exists;
- local in-memory keyword index exists;
- deterministic search/ranking returns matched fields and snippets;
- raw `recipe-dataset/` files remain ignored;
- no API endpoint, RAG over the dataset, embeddings, vector DB, provider calls, or write-back are added;
- no production data is mutated.

## 0024C: Add Indexed Dataset Retrieval Endpoint

Status: complete.

Goal: Expose deterministic retrieval over the bounded local Kaggle dataset index.

Files likely touched:

- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `ai-api/tests/test_dataset_search_api.py`
- `docs/local-recipe-dataset-adapter.md`

Validation:

- generated temporary CSV fixtures;
- missing dataset directory warning case;
- no raw dataset files or generated index artifacts committed;
- repo validation.

Done criteria:

- `GET /dataset/search` and `POST /dataset/search` exist;
- responses include ranked results, matched fields, snippets, provenance, index summary, and warnings;
- missing local dataset path is controlled;
- no RAG over the indexed dataset, embeddings, vector DB, provider calls, generated index artifacts, or write-back are added.

## 0024D: Add RAG Over Indexed Dataset

Status: complete.

Goal: Answer questions over retrieved local Kaggle dataset results with provider synthesis and dataset provenance citations.

Files likely touched:

- `ai-api/app/dataset_rag.py`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `ai-api/tests/test_dataset_ask.py`
- `docs/local-recipe-dataset-adapter.md`

Validation:

- generated temporary CSV fixtures;
- no-match and missing-dataset no-provider-call tests;
- mock provider endpoint test;
- no raw dataset files or generated index artifacts committed;
- repo validation.

Done criteria:

- `POST /dataset/ask` exists;
- provider receives only retrieved dataset result context;
- responses include answer, citations/provenance, provider/model, retrieval metadata, warnings, and optional usage;
- no-match and missing-dataset cases do not call the provider;
- no embeddings, vector DB, generated index artifacts, image ingestion, Vanilla Cookbook imports/write-back, or deployment changes are added.

## 0025A: Add Offline Evals And Validation Hygiene

Status: complete.

Goal: Add offline evals for the AI cookbook sidecar and document Windows validation hygiene.

Files likely touched:

- `evals/ai_cookbook/`
- `scripts/validate-repo.sh`
- `scripts/validate-repo.ps1`
- `docs/ai-evals-plan.md`
- `docs/repo-validation.md`
- `docs/shared-infrastructure-data-boundaries.md`

Validation:

- offline eval command;
- repository validator;
- generated fixtures only;
- no live provider keys;
- no raw dataset files or generated indexes committed.

Done criteria:

- eval harness returns non-zero on failure;
- evals cover dataset ask grounding, citations, no-match, missing-dataset, and secret-like output leakage;
- Bash validation runs offline evals;
- Windows temp-directory pytest issue is documented with a PowerShell wrapper;
- shared infrastructure/data-boundary note exists.

## 0025B: Expand Offline AI Evals

Status: complete.

Goal: Expand the offline AI cookbook eval harness across major AI workflows while keeping validation deterministic and mock-only.

Files likely touched:

- `evals/ai_cookbook/`
- `docs/ai-evals-plan.md`

Validation:

- offline eval command;
- AI API pytest suite;
- repo validation;
- no live provider keys;
- no raw dataset files or generated indexes committed.

Done criteria:

- evals cover dataset ask, saved-recipe ask, importer, meal plan, provider config hygiene, citations, and secret-like leakage checks.
- normal validation remains offline and mock-only.

## 0025C: Add Manual Live OpenAI Smoke Tests

Status: complete.

Goal: Add a safe manual-only script that proves the existing OpenAI provider path can make real calls for major AI workflows without affecting CI or normal validation.

Files likely touched:

- `scripts/smoke-openai-live.py`
- `ai-api/tests/test_openai_live_smoke_script.py`
- `docs/live-openai-smoke-tests.md`
- `.env.example`
- `README.md`
- `ai-api/README.md`

Validation:

- guardrail unit tests without live calls;
- offline eval command;
- AI API pytest suite;
- repo validation;
- manual live command only when explicitly opted in.

Done criteria:

- manual live smoke script requires `AI_PROVIDER=openai`, `OPENAI_ENABLE_LIVE_TESTS=true`, a local OpenAI key, and `OPENAI_LIVE_TEST_BUDGET_CENTS` at or below 25.
- script covers provider sanity, importer, saved-recipe ask, dataset ask, and meal plan with tiny generated fixtures.
- script does not run from CI, normal pytest selection beyond offline guardrail tests, offline evals, or repository validation as a live call.
- no production deployment, Cloudflare, Qdrant, Postgres, pgvector, embeddings, vector DB, generated persistent indexes, raw dataset files, `.env`, or secrets are added.

## 0025D: Fix OpenAI Structured Output Schema

Status: complete.

Goal: Normalize Pydantic JSON Schemas before sending strict structured-output requests to OpenAI.

Files likely touched:

- `ai-api/app/providers/openai_schema.py`
- `ai-api/app/providers/openai_provider.py`
- `ai-api/tests/test_openai_schema.py`

Validation:

- schema normalizer tests;
- fake OpenAI client payload tests without network calls;
- offline eval command;
- AI API pytest suite;
- repo validation.

Done criteria:

- strict schema payloads include `additionalProperties: false` for object schemas.
- object `required` lists include all properties, including nullable/defaulted fields.
- nested schemas and `$defs` are normalized.
- caller-provided schemas are not mutated.

## 0025E: Fix Live Smoke Windows Cleanup And Record Validation

Status: complete.

Goal: Make live OpenAI smoke temporary fixture cleanup Windows-safe and record successful manual live validation.

Files likely touched:

- `scripts/smoke-openai-live.py`
- `ai-api/tests/test_openai_live_smoke_script.py`
- `docs/live-openai-smoke-tests.md`
- `docs/ai-implementation-backlog.md`
- `inbox/0025E-fix-live-smoke-windows-cleanup.md`
- `outbox/0025E-fix-live-smoke-windows-cleanup-results.md`

Validation:

- cleanup behavior test without live calls;
- offline eval command;
- AI API pytest suite;
- repo validation.

Done criteria:

- live smoke uses best-effort temp cleanup on Windows.
- cleanup errors after successful workflows do not mask compact success output.
- provider, workflow, assertion, and guardrail failures still exit non-zero.
- docs record the successful manual live OpenAI smoke run using `gpt-5.4-nano`.

## 0025F: Keep AI Validation Deterministic In CI

Goal: Wire offline AI evals into local validation and GitHub Actions.

Files likely touched:

- `evals/ai_cookbook/`
- `.github/workflows/repo-validation.yml`
- `scripts/validate-repo.sh`
- `docs/ai-evals-plan.md`

Validation:

- local pytest;
- offline eval command;
- workflow syntax and repo validation.

Done criteria:

- CI passes without live AI keys.
- Offline evals fail on invalid schemas, missing citations, or secret leakage.
- Documentation explains how to run evals locally.

## 0026A: Add AI Demo Walkthrough And Scripts

Status: complete.

Goal: Make the completed AI cookbook features demo-ready for portfolio, interview, and customer walkthroughs without adding deployment or storage architecture.

Files likely touched:

- `scripts/demo-ai-mock.ps1`
- `scripts/demo-ai-live-smoke.ps1`
- `scripts/demo-ai-requests.http`
- `docs/ai-demo-walkthrough.md`
- `docs/ai-feature-status.md`
- `README.md`
- `docs/repo-map.md`

Validation:

- offline eval command;
- AI API pytest suite;
- repo validation;
- no committed secrets, raw datasets, generated artifacts, or provider keys.

Done criteria:

- mock/offline demo path exists.
- optional live-smoke wrapper is documented and guarded.
- REST request examples cover the AI sidecar workflows.
- feature status matrix and five-minute talk track exist.
- README links to the demo docs.

## 0026B: Add Screenshots And Portfolio README Polish

Goal: Make the AI layer presentation-ready.

Files likely touched:

- `README.md`
- `docs/ai-demo-plan.md`
- `docs/ai-medium-path-roadmap.md`
- screenshot assets if approved in a later task.

Validation:

- link validation;
- repo validation;
- no committed secrets or private recipe data.

Done criteria:

- README explains the AI sidecar, RAG, importer, meal planner, and evals.
- Demo script covers the core user flow.
- Screenshots avoid secrets and private personal data.
