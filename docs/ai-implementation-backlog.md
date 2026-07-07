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

## 0026B: Add AI Portfolio README Polish

Status: complete.

Goal: Polish the AI cookbook feature set into a portfolio-ready README and supporting showcase docs.

Files likely touched:

- `README.md`
- `docs/ai-portfolio-showcase.md`
- `docs/ai-screenshot-capture-guide.md`
- `docs/ai-feature-status.md`
- `docs/ai-demo-walkthrough.md`
- `docs/repo-map.md`

Validation:

- offline eval command;
- AI API pytest suite;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- no committed secrets, raw datasets, generated artifacts, or provider keys.

Done criteria:

- README has a clear AI showcase section.
- Portfolio showcase doc exists.
- Screenshot capture guide exists and screenshots are deferred until safe mock captures are explicitly requested.
- Feature status is accurate and portfolio-readable.
- Normal validation remains offline and mock-only.

## 0026C: Final AI Feature Completion Review

Status: complete.

Goal: Perform an acceptance review of the completed AI cookbook feature set and produce a final feature-completion matrix without adding new infrastructure.

Files likely touched:

- `docs/ai-feature-completion-review.md`
- `docs/ai-feature-status.md`
- `docs/ai-portfolio-showcase.md`
- `docs/ai-demo-walkthrough.md`
- `docs/ai-implementation-backlog.md`
- `docs/repo-map.md`
- `README.md`
- `outbox/0026C-final-ai-feature-completion-review-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior.

Done criteria:

- final acceptance matrix confirms completed importer, saved-recipe ask, dataset search/RAG, meal planning, evals, and manual live smoke paths;
- deferred production/storage/UI boundaries are explicit;
- no Qdrant, Postgres, pgvector, embeddings, vector DB, persistent indexes, deployment changes, raw datasets, private env files, or provider keys are added.

## 0027: Future AI/Platform Options

Status: deferred options.

Goal: Capture possible next-phase AI and platform work as separately scoped options, not immediate work for the completed AI cookbook feature slice.

Deferred options:

- production storage architecture ADR;
- demo control-plane ADR;
- screenshot capture with safe mock data;
- optional UI integration for selected AI endpoints;
- embeddings/vector DB spike only if deterministic retrieval becomes insufficient;
- app-specific data-plane isolation for cookbook, stock, and Army demos.

Guardrails:

- each option needs a separate task and acceptance criteria;
- do not add live provider calls to CI;
- do not add Qdrant, Postgres, pgvector, embeddings, vector DB, persistent generated indexes, deployment changes, raw datasets, private env files, or provider keys without an explicit future task.

## 0027A: Add AI Demo UI And Logging

Status: complete.

Goal: Start the product-facing phase with a sidecar-served AI demo UI and safe structured logging foundation.

Files likely touched:

- `ai-api/app/main.py`
- `ai-api/app/observability.py`
- `ai-api/app/static/`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_observability.py`
- `docs/ai-ui-integration-plan.md`
- `docs/ai-sidecar-logging.md`
- `docs/ai-feature-status.md`
- `docs/ai-demo-walkthrough.md`
- `README.md`

Validation:

- UI route/static asset TestClient tests;
- logging TestClient/helper tests;
- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior.

Done criteria:

- `GET /demo` and `GET /demo/ai` serve a lightweight AI demo UI from the sidecar.
- UI exercises existing AI endpoints and shows responses, citations/provenance, warnings, provider/model metadata, and friendly errors.
- structured stdout logging emits safe request/workflow metadata without raw prompts, pasted recipes, provider responses, env contents, local private paths, or secrets.
- no upstream Vanilla Cookbook frontend rewrite, deployment changes, external logging infrastructure, screenshots, raw datasets, generated artifacts, or provider keys are added.

## 0027B: Production-Quality AI Demo Usability

Status: complete.

Goal: Harden the sidecar-served AI demo UI for a 15 to 30 minute hands-on live demo.

Files likely touched:

- `ai-api/app/main.py`
- `ai-api/app/observability.py`
- `ai-api/app/static/`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_observability.py`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-ui-integration-plan.md`
- `docs/ai-sidecar-logging.md`
- `docs/ai-screenshot-capture-guide.md`
- `docs/ai-feature-status.md`
- `docs/ai-demo-walkthrough.md`
- `README.md`

Validation:

- UI/readiness/static TestClient tests;
- logging TestClient/helper tests;
- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior.

Done criteria:

- demo UI has a clear landing section, readiness panel, guided workflow order, sample inputs, reset controls, loading states, answer cards, citations/provenance, warnings, friendly errors, and raw JSON details.
- readiness clearly reports sidecar health, provider mode/model, saved-recipe availability, dataset availability, and offline demo mode without exposing local paths.
- operator logs include request ID, UI workflow, endpoint, status, duration, provider/model where available, retrieved count, citation count, and warning count.
- live demo runbook exists for 15 and 30 minute flows.
- no production storage, deployment changes, Cloudflare changes, control-plane workflows, live CI provider tests, vector infrastructure, upstream frontend rewrite, browser automation, screenshots, raw datasets, generated artifacts, private env files, or credentials are added.

## 0027C: Manual UI Demo Acceptance Test

Status: complete.

Goal: Create the manual acceptance checklist and report path for 15 to 30 minute human UI demo testing.

Files likely touched:

- `docs/ai-manual-ui-acceptance-test.md`
- `outbox/0027C-manual-ui-demo-acceptance-test-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior.

Done criteria:

- manual acceptance checklist exists;
- human URL testing is clearly marked pending when not performed by Codex;
- 15 and 30 minute flows are documented;
- logging checks are documented;
- no browser automation, screenshots, raw datasets, generated artifacts, private env files, or credentials are added.

## 0027D: Seed Demo Data And Fix Local Demo Launch

Status: complete.

Goal: Make the local mock browser demo complete by seeding generated saved-recipe data and documenting a reliable `/demo` launch path.

Files likely touched:

- `ai-api/app/demo_data.py`
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_demo_ui.py`
- `scripts/seed-ai-demo-data.ps1`
- `scripts/start-ai-demo-local.ps1`
- `scripts/demo-ai-mock.ps1`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-manual-ui-acceptance-test.md`
- `docs/ai-ui-integration-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-demo-walkthrough.md`
- `README.md`
- `outbox/0027D-seed-demo-data-and-fix-local-demo-launch-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior.

Done criteria:

- local demo operator has a clear command to seed demo data and start the sidecar;
- `/demo` opens at `http://127.0.0.1:8000/demo`;
- readiness shows generated saved recipes available in mock demo mode;
- Ask My Cookbook and Meal Planner work with generated saved-recipe citations;
- dataset search/RAG still work with intuitive sample prompts;
- logs remain safe and useful;
- no production cookbook data, raw datasets, screenshots, generated artifacts, private env files, or credentials are committed.

## 0027E: Live OpenAI Demo Evals And Metrics

Status: complete.

Goal: Prepare the cookbook AI demo for controlled OpenAI-backed operation by adding repeatable live-provider evals and metrics reporting.

Files likely touched:

- `scripts/run-openai-demo-evals.ps1`
- `scripts/live-openai-demo-evals.py`
- `evals/ai_cookbook/live_cases.json`
- `evals/ai_cookbook/expected_checks.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0027E-live-openai-demo-evals-and-metrics-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- live eval wrapper requires explicit OpenAI opt-in controls before live calls;
- generated demo-safe data is seeded for live evals;
- readiness, importer, Ask My Cookbook, dataset search baseline, dataset Ask/RAG, and meal planning are covered;
- expected checks are defined before the run;
- artifacts include JSONL results, JSON summary, Markdown summary, and per-workflow response JSON;
- metrics include latency, citations, retrieved counts, warnings, usage tokens when available, and estimated cost when local rates are provided;
- generated eval artifacts remain under ignored `.tmp-ai-demo/`;
- no live OpenAI calls are added to CI or normal validation;
- no secrets, private environment files, raw datasets, generated artifacts, screenshots, or credentials are committed.

Future production hardening tasks may include authenticated access, time-limited sessions, paid access or monetization gates, usage metering, user/session isolation, durable storage, multi-use-case routing, deployment exposure controls, provider cost controls, and an admin/operator dashboard. Those are intentionally not implemented in 0027E.

## 0027F: Live GPT-Nano Quality Baseline And Thresholds

Status: complete.

Goal: Preserve the first successful live GPT-nano eval as a sanitized baseline and tighten quality gates for usefulness, latency, token usage, cost visibility, and demo readiness.

Files likely touched:

- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/live-openai-demo-evals.md`
- `evals/ai_cookbook/expected_checks.py`
- `evals/ai_cookbook/live_cases.json`
- `scripts/live-openai-demo-evals.py`
- `ai-api/app/demo_data.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0027F-live-gpt-nano-quality-baseline-and-thresholds-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- sanitized GPT-nano baseline exists without local paths, secrets, raw response artifacts, or generated eval contents;
- live eval checks include correctness plus answer usefulness and demo-readiness checks;
- latency and token thresholds produce warnings or failed checks by severity;
- cost visibility guidance remains environment-driven instead of hardcoding volatile rates;
- generated demo fixture warnings about optional dataset files are filtered only when the generated fixture marker is present;
- normal validation remains offline and no live OpenAI calls are added to CI;
- no `.tmp-ai-demo` artifacts, API keys, private env files, screenshots, raw datasets, or credentials are committed.

## 0027G: Default GPT-Nano Cost Estimates

Status: complete.

Goal: Make live OpenAI demo eval cost estimates populate by default for `gpt-5.4-nano` while preserving operator override support.

Files likely touched:

- `evals/ai_cookbook/expected_checks.py`
- `scripts/live-openai-demo-evals.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0027G-default-gpt-nano-cost-estimates-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- local rate environment variables still override cost calculation;
- `gpt-5.4-nano` uses maintained default cost rates when local overrides are absent;
- unknown models without local rates keep `estimated_cost_usd` as `null`;
- generated records and summaries include `cost_source` as `env_override`, `default_model_rate`, or `unavailable`;
- no live OpenAI calls are added to normal validation;
- no `.tmp-ai-demo` artifacts, API keys, private env files, screenshots, raw datasets, or credentials are committed.
