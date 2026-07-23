# AI Implementation Backlog

## 0033D: Traffic Analytics and Behavior Tracking ADR

Status: complete, docs/research-only.

The ADR defines the product questions and safe event categories needed for
future aggregate measurement, while explicitly excluding recipe text, prompts,
provider outputs, tokens, private storage data, sensitive details, and raw
identifiers. It separates anonymous, pseudonymous, account-linked, operator,
and commercial modes; preserves the AI metering and timer boundaries; and
defers ads/conversions to the future monetization ADR. No tracking or vendor
integration is implemented.

## 0033C: SSO and BYOS Identity/Storage Architecture ADR

Status: complete, docs/research-only.

The ADR separates email/SSO identity from user-authorized BYOS storage,
documents high-level Google, Meta, Dropbox, and Microsoft provider constraints,
and defines portable bundles, consent/scope, token, revocation, deletion,
privacy, failure-mode, and staged implementation boundaries. No auth or cloud
integration is implemented. Future work must preserve mock/offline validation,
server-side token handling, least privilege, and the 30-minute timer boundary.

## 0033A: Manual Product Integration Usability Validation

Status: complete as a mock/offline validation exercise.

The local sidecar ran with generated demo fixtures and mock mode. The mock
endpoint smoke passed all workflows and the existing 4-test UI harness passed,
including controlled Live-unavailable behavior against a mock server. Follow-
up candidates are native navigation/visual continuity, shared loading,
empty/error/accessibility states, safe session/user context handoff, and a
production-shaped acceptance checklist once the upstream Cookbook container
is available locally. No implementation was added; AWS/platform work remains
separate.

## 0033B: Application Session Timer and Access Exceptions ADR

Status: complete, docs-only.

The ADR proposes a server-authoritative 30-minute application session for a
future public/free experience, five-minute and one-minute warnings, safe
read-only expiry with draft preservation, and scoped operator/trusted/invite
exceptions. It distinguishes the UI timer, application session expiry, and
provider budget enforcement, and keeps exceptions from bypassing budgets,
kill switches, workflow scopes, or authorization. Runtime enforcement,
production auth, persistence, and all platform work remain future tasks.

This backlog breaks the medium-path AI design into follow-on mailbox tasks. Task numbers are proposed and may change if new operational fixes are needed first.

## 0030I-6: Local Live Runtime Profile and Secret Injection

Status: complete.

The local launcher imports ignored `.env` values into the server process with
safe precedence, supports non-secret default initialization, permits only
`gpt-5.4-nano` for live mode, and keeps mock validation explicit and offline.
No production secret store or deployment secret mechanism is implemented.

## 0030I-7: Playwright UI Troubleshooting Harness

Status: complete.

Adds optional local Chromium browser QA for `/product` and `/demo`, including
mode propagation, payload inspection, safe live-unavailable behavior, mock
workflow checks, and layout bounds. It remains outside normal offline
validation and produces ignored local artifacts only.

## 0030I-5: Local Live Mode Product Acceptance and Mode Audit

Status: complete with a recorded bounded live-provider availability failure.

The mock audit confirms all six provider-backed workflows use `mock/mock-basic`
and that Live selection on a mock server remains safely unavailable. The
optional browser suite stays mock-only. A no-argument local launcher audit
confirmed `openai/gpt-5.4-nano` readiness; its one permitted importer call
returned controlled HTTP 503 and was not retried. Follow up with explicit
provider-account/quota diagnosis before claiming a successful new live run.

## 0030I-8: Bounded Live Importer 503 Diagnostics

Status: complete for safe diagnosis; additional live acceptance remains manual.

The importer route returns a bounded unavailable envelope with a safe
category/guidance pair. `scripts/diagnose-live-importer.ps1` performs redacted
preflight and requires explicit operator approval before one `gpt-5.4-nano`
importer call. No retry, provider body, prompt, key, or stack trace is emitted.

The 0030I-8R correction makes model preflight truthful when inherited process
values override `.env`, adds explicit `-PreflightOnly`, and makes the local
launcher refuse an occupied port before attempting Uvicorn.

The 0030I-8S correction maps bounded helper failures such as
`output_cap_or_incomplete_response` and `JSONDecodeError` into safe diagnostic
fields without leaking PowerShell native error frames.

The bounded importer diagnostic uses a tiny deterministic scrambled-egg input
and remains separate from product/runtime caps and the full-RAG importer eval
profile. Operator-approved live evidence for `openai` / `gpt-5.4-nano` passed
at 1000 and 500 output tokens. The recommended manual acceptance cap is 500.
The 400-token run failed safely with
`output_cap_or_incomplete_response` / `JSONDecodeError`; the earlier 300-token
run was also too low for complete strict-schema JSON. 1000 remains the manual
troubleshooting ceiling, not the recommended default. Preflight plus explicit
approval permits exactly one bounded call per invocation, with no retries;
normal validation remains mock/offline and does not call live OpenAI.

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

## 0028A: Bounded Input Quality And Clarification Handling

Status: complete.

Goal: Add production-oriented handling for weak, vague, malformed, or nonsensical user input across cookbook AI workflows.

Files likely touched:

- `ai-api/app/input_quality.py`
- `ai-api/app/schemas.py`
- `ai-api/app/importer.py`
- `ai-api/app/rag.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/dataset_rag.py`
- `ai-api/app/meal_plan_endpoint.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/`
- `evals/ai_cookbook/run_evals.py`
- `scripts/live-openai-demo-evals.py`
- docs and outbox

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- input quality is classified as `ready`, `weak_but_usable`, `needs_clarification`, or `rejected`;
- empty, whitespace-only, symbol-only, no-alpha, repeated junk, placeholder, too-short, and too-long inputs can be rejected before provider calls;
- vague but recoverable inputs return one bounded clarification question;
- weak usable inputs proceed with warnings or assumptions;
- importer, Ask My Cookbook, dataset search, dataset Ask/RAG, and meal planning expose `input_quality` metadata;
- live eval records include input-quality and provider-call-avoidance metrics;
- no open-ended chat loop, multi-turn state, normal-validation live calls, generated live artifacts, secrets, private env files, raw datasets, screenshots, logs, or credentials are added.

## 0028B: Live Importer Quality Check Tuning

Status: complete.

Goal: Fix the first post-0028A live eval failure by tuning importer quality checks so useful GPT-nano importer responses do not false-fail when ingredient evidence appears outside `description`.

Files likely touched:

- `evals/ai_cookbook/expected_checks.py`
- `evals/ai_cookbook/live_cases.json`
- `ai-api/app/importer.py`
- `ai-api/tests/test_live_openai_demo_evals.py`
- `docs/live-openai-demo-evals.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0028B-live-importer-quality-check-tuning-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- importer scoring accepts ingredient evidence from title, description, ingredient names, and instructions;
- canonical ingredient alias groups are used for white beans, olive oil, garlic, lemon, parsley, and toast;
- descriptions are checked for ingredient grounding only when present;
- generic placeholder, unrelated ingredient, and truly ungrounded outputs still fail;
- normal validation remains offline and no live OpenAI calls are added to CI;
- no generated live eval artifacts, API keys, private env files, screenshots, raw datasets, logs, or credentials are committed.

## 0028C: Live Eval Regression Notes And Acceptance Baseline

Status: complete.

Goal: Preserve the post-`0028A` live eval regression, the `0028B` importer-check fix, and the latest passing live GPT-nano acceptance run as sanitized project evidence.

Files likely touched:

- `docs/live-openai-demo-regression-notes-2026-07-08.md`
- `docs/live-openai-demo-baseline-2026-07-07.md`
- `docs/live-openai-demo-evals.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0028C-live-eval-regression-notes-and-acceptance-baseline-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior;
- Docker Compose config check;
- diff whitespace check.

Done criteria:

- the post-`0028A` failed live run is documented without private paths, raw response JSON, secrets, or generated live artifacts;
- root cause is recorded as a brittle description-only importer check rather than a model-quality failure;
- the `0028B` fix is recorded;
- the post-`0028B` 6/6 passing live run is recorded as the current acceptance baseline;
- a concise acceptance matrix records mock demo, seeded UI demo, live eval, cost, thresholds, input guardrails, importer robustness, and provider-call avoidance;
- normal validation remains offline and no live OpenAI calls are added to CI;
- no generated live eval artifacts, API keys, private env files, screenshots, raw datasets, logs, credentials, or `.tmp-ai-demo/` artifacts are committed.

## 0029A: Production Access, Metering, And Time-Limited AI Sessions Architecture

Status: complete.

Goal: Design the production architecture for safely exposing the Cookbook AI demo as a controlled product experience with authentication, metering, time-limited sessions, provider cost controls, and future paid access.

Files likely touched:

- `docs/production-access-metering-architecture.md`
- `docs/ai-production-readiness-roadmap.md`
- `docs/ai-session-metering-data-model.md`
- `docs/ai-access-control-threat-model.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029A-production-access-metering-and-time-limited-ai-sessions-architecture-results.md`

Validation:

- repo validation;
- diff whitespace check;
- Docker Compose config check;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- architecture docs exist for production access, metering, and time-limited AI sessions;
- access modes are defined for local/offline developer, private operator demo, invite-only demo, future paid access, and admin/operator mode;
- session and per-call metering data models are documented;
- budget enforcement flow is documented in the required order;
- authentication options are compared with an incremental recommendation;
- future paid access is bounded but not implemented;
- multi-use-case data boundary pattern preserves the rule that shared infrastructure is allowed but each demo owns its own data boundary;
- deployment exposure controls explicitly prohibit unauthenticated public live AI endpoints;
- threat model exists;
- follow-on tasks are listed with `0029B` reserved for manual end-user recipe-entry acceptance and production-readiness implementation continuing at `0029C`;
- normal validation remains offline;
- no runtime auth, billing, public live route exposure, payment integration, migrations, secrets, env files, raw datasets, generated artifacts, screenshots, logs, credentials, or `.tmp-ai-demo/` artifacts are committed.

## 0029B: Manual End-User Recipe Entry Acceptance

Status: planned.

Goal: Validate the manual end-user recipe-entry path before production access and metering implementation begins.

Notes:

- This number is reserved for manual recipe-entry acceptance.
- Production-readiness implementation resumes with `0029C`.

## 0029B-1: Start AI Demo Provider Override

Status: complete.

Goal: Fix `scripts/start-ai-demo-local.ps1` so manual end-user recipe-entry acceptance can intentionally run with either safe mock mode or live OpenAI mode.

Files likely touched:

- `scripts/start-ai-demo-local.ps1`
- `ai-api/tests/test_start_ai_demo_local_script.py`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-manual-ui-acceptance-test.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-1-start-ai-demo-provider-override-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior;
- safe mock launch validation.

Done criteria:

- `start-ai-demo-local.ps1` defaults to mock safely;
- `start-ai-demo-local.ps1` supports `-Provider openai -EnableLiveTests`;
- live manual-demo defaults are available for model, budget cents, and max output tokens;
- existing environment variables are respected unless explicit script parameters override them;
- missing `OPENAI_API_KEY` fails fast only for OpenAI mode;
- startup summary is useful and secret-safe;
- normal validation remains offline;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-2: RAG-Informed Recipe Creator Importer

Status: complete.

Goal: Improve the importer so `POST /ai/import-recipe` behaves like a RAG-informed recipe creator/importer for rough notes, not only a thin extractor.

Files likely touched:

- `ai-api/app/importer.py`
- `ai-api/app/schemas.py`
- `ai-api/app/main.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/`
- `evals/ai_cookbook/`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-2-rag-informed-recipe-creator-importer-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repo validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- importer retrieves bounded local dataset examples before provider calls when dataset is available;
- importer falls back with warning when dataset retrieval is unavailable;
- input-quality rejected and clarification paths still avoid retrieval/provider calls;
- response includes retrieval metadata and dataset citations/provenance;
- draft defaults to 4 servings when user does not specify servings;
- missing quantities are estimated where reasonable and disclosed in notes;
- prompt uses retrieved examples only for structure, proportions, and step completeness;
- user-provided core ingredients and dish intent remain primary;
- demo UI displays servings, estimated quantities, steps, and importer citations/provenance;
- eval checks cover servings, quantities, citations, step depth, and recipe-specific issues for omelet, carbonara, cheesecake, and chicken casserole;
- normal validation remains offline;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-3: Live Importer 503 Diagnostics And Dataset Overrides

Status: complete.

Goal: Fix the live importer blocker where `POST /ai/import-recipe` returned `503 Service Unavailable` during manual OpenAI recipe-entry testing, and add local startup overrides for full-dataset RAG validation.

Files likely touched:

- `ai-api/app/providers/openai_schema.py`
- `ai-api/app/providers/openai_provider.py`
- `ai-api/app/providers/errors.py`
- `ai-api/app/config.py`
- `ai-api/app/main.py`
- `ai-api/tests/`
- `scripts/start-ai-demo-local.ps1`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-3-live-importer-503-diagnostics-and-dataset-overrides-results.md`

Validation:

- offline eval command;
- AI API pytest suite;
- repo validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- strict OpenAI structured schemas recursively strip unsupported metadata such as `default`, `examples`, `title`, and `description` before provider calls;
- object schemas still keep `additionalProperties=false` and strict required-property behavior;
- importer application behavior still defaults servings to 4 without relying on provider-schema defaults;
- opt-in `AI_PROVIDER_DEBUG=true` emits sanitized local provider diagnostics that help distinguish timeout, schema rejection, bad model, quota/rate limit, auth, and network failures;
- diagnostics never log API keys, Authorization headers, raw prompts, raw provider responses, `.env` values, or secret-like strings;
- `start-ai-demo-local.ps1` supports `-RecipeDatasetDir`, `-RecipeDatasetIndexLimit`, `-AiTimeoutSeconds`, and `-ProviderDebug`;
- mock remains the safe default, generated `.tmp-ai-demo` fixtures remain the default dataset path, and live OpenAI still requires explicit opt-in;
- importer-only diagnostics are documented without exposing secrets or raw provider responses;
- normal validation remains offline;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-4: Live Importer Output Cap And RAG Validation

Status: complete.

Goal: Raise the live manual importer output cap to a level that can carry RAG-informed structured drafts, document the full-dataset validation command, and keep importer citations visible in the demo UI.

Files likely touched:

- `scripts/start-ai-demo-local.ps1`
- `scripts/smoke-openai-importer-live.py`
- `scripts/smoke-openai-importer-live.ps1`
- `ai-api/app/providers/errors.py`
- `ai-api/app/providers/openai_provider.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-4-live-importer-output-cap-and-rag-validation-results.md`

Validation:

- offline eval command;
- AI API pytest suite;
- repo validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- `scripts/start-ai-demo-local.ps1` recommends or defaults to `AI_MAX_OUTPUT_TOKENS=900` for the OpenAI manual recipe-creator path;
- provider diagnostics classify output-cap or incomplete structured responses separately from generic invalid JSON where practical;
- importer-only live smoke scripts print provider/model/title/servings/ingredient counts/instruction counts/retrieval counts/citation counts/token usage on success and safe classifications on failure;
- importer citations render in the demo UI with citation count, titles, snippets, source IDs, provenance, and retrieval metadata when present;
- the default `.tmp-ai-demo` fixture dataset remains available for smoke tests, but docs point to the full `recipe-dataset` path for meaningful RAG validation;
- manual findings about omelet, cheesecake, and the 508-output-token cheesecake run are preserved in the outbox report;
- normal validation remains offline;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-5: Importer RAG Retrieval Relevance Tuning

Status: complete.

Goal: Improve importer retrieval relevance so dish-specific recipes outrank broad category matches, and warn when retrieved examples are weak.

Files likely touched:

- `ai-api/app/dataset_index.py`
- `ai-api/app/importer.py`
- `ai-api/app/schemas.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_importer.py`
- `ai-api/tests/test_importer_rag_relevance.py`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-5-importer-rag-retrieval-relevance-tuning-results.md`

Validation:

- offline importer search ranking checks;
- importer retrieval metadata and weak-warning checks;
- repository validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- importer dataset retrieval uses anchor-aware relevance scoring and prefers exact dish names and core ingredients over broad dessert/pasta/chicken matches;
- importer metadata includes query anchors, matched result IDs, result scores, dataset limit, document count, and a weak-match warning when appropriate;
- cheesecake, carbonara, omelet, and chicken/rice casserole queries rank the intended recipe above distractor recipes in deterministic tests;
- weak retrieval warnings appear only when matches are genuinely weak;
- demo UI surfaces the retrieval metadata without exposing private local paths;
- normal validation remains offline;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-6: RAG Retrieval Evaluation Harness

Status: complete.

Goal: Add a deterministic offline harness that scores importer retrieval relevance so ranking regressions can be tested instead of judged only by manual UI inspection.

Files likely touched:

- `evals/ai_cookbook/retrieval_cases.yaml`
- `evals/ai_cookbook/retrieval_eval.py`
- `evals/ai_cookbook/run_evals.py`
- `ai-api/tests/test_retrieval_eval_harness.py`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-6-rag-retrieval-evaluation-harness-results.md`

Validation:

- offline eval command;
- AI API pytest suite through the Git Bash validator if Windows direct pytest hits the known temp ACL issue;
- repository validation;
- diff whitespace check;
- Docker Compose config check;
- mock demo script;
- live smoke wrapper skip behavior;
- live demo eval wrapper skip behavior.

Done criteria:

- retrieval eval cases are hand-maintainable and cover cheesecake, carbonara, omelet, chicken/rice casserole, and baked-versus-no-bake style contrasts;
- the offline eval runner includes retrieval relevance cases and fails non-zero on ranking regressions;
- deterministic tests cover top-1 relevance, top-k relevance counts, anchor coverage, generic drift, category classification, and weak-match warnings with distractor-only fixtures;
- manual live capture guidance records provider/model, dataset limit, document count, relevance category, warning state, top-1 title, top-3 titles, and relevant-count notes without committing raw live JSON artifacts;
- normal validation remains offline and mock-only;
- no live OpenAI calls, raw datasets, generated live artifacts, secrets, env files, screenshots, logs, or credentials are committed.

## 0029B-7: RAG Context Packing And Token Budget

Status: complete.

Goal: Add a deterministic bounded prompt-context packer so importer/provider prompts include only concise, relevance-ranked dataset snippets and safe packing metadata.

Files likely touched:

- `ai-api/app/rag_context.py`
- `ai-api/app/importer.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_rag_context.py`
- `ai-api/tests/test_importer.py`
- `ai-api/tests/test_demo_ui.py`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-7-rag-context-packing-and-token-budget-results.md`

Done criteria:

- the importer prompt receives a bounded packed context block instead of full retrieved records;
- strong/moderate examples are preferred, weak examples are dropped or explicitly labeled when unavoidable, and total prompt context stays within deterministic character budgets;
- response metadata exposes packed counts, IDs, dropped IDs, budget warnings, and weak-example status without leaking private paths or raw provider prompts;
- demo UI surfaces the safe packing metadata;
- deterministic tests cover selection, truncation, budget limits, weak-example handling, and prompt construction.

## 0029B-8: Dataset Normalization For Deterministic RAG

Status: complete.

Goal: Normalize dataset text deterministically before indexing and scoring so retrieval is more robust while original display values remain unchanged.

Files likely touched:

- `ai-api/app/dataset_normalization.py`
- `ai-api/app/dataset_index.py`
- `evals/ai_cookbook/retrieval_eval.py`
- `evals/ai_cookbook/retrieval_cases.yaml`
- `ai-api/tests/test_dataset_normalization.py`
- `ai-api/tests/test_dataset_index.py`
- `ai-api/tests/test_retrieval_eval_harness.py`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-8-dataset-normalization-for-deterministic-rag-results.md`

Done criteria:

- the index normalizes punctuation, quotes, dashes, accents, aliases, and common singular/plural variants before scoring;
- important food phrases such as cream cheese, graham cracker crust, black pepper, no bake, and cream of chicken soup remain matchable;
- retrieval evals cover alias and phrase-sensitive cases like omelette, no-bake cheesecake, parmigiano-reggiano carbonara, and cream of chicken soup casserole;
- original recipe values remain intact for citations, snippets, and display;
- normal validation remains offline and mock-only.

## 0029B-9: RAG Honesty And Citation Support Policy

Status: complete.

Goal: Classify how strongly retrieved dataset examples support importer drafts and surface that support level honestly in the API and demo UI.

Files likely touched:

- `ai-api/app/rag_support_policy.py`
- `ai-api/app/importer.py`
- `ai-api/app/schemas.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_rag_support_policy.py`
- `ai-api/tests/test_importer.py`
- `ai-api/tests/test_importer_rag_relevance.py`
- `ai-api/tests/test_demo_ui.py`
- `evals/ai_cookbook/retrieval_eval.py`
- `evals/ai_cookbook/retrieval_cases.yaml`
- `ai-api/tests/test_retrieval_eval_harness.py`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-9-rag-honesty-and-citation-support-policy-results.md`

Done criteria:

- importer responses classify dataset support as strong, moderate, weak, or none using deterministic retrieval metadata;
- the API surfaces safe support reason/message fields without exposing raw prompts, raw provider responses, private paths, or secrets;
- the demo UI shows the support level and labels weak or partial citations honestly;
- strong support can be described as grounded, while weak and none do not overstate support;
- offline retrieval evals and importer tests cover strong, moderate, weak, and none support cases;
- existing retrieval, context packing, normalization, and mock paths still pass;
- normal validation remains offline and mock-only;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-10: Local In-Memory Retrieval Cache

Status: complete.

Goal: Add a process-local in-memory cache for deterministic dataset indexing and retrieval so repeated importer and dataset search calls can reuse work without writing generated indexes to disk.

Files likely touched:

- `ai-api/app/retrieval_cache.py`
- `ai-api/app/config.py`
- `ai-api/app/dataset_index.py`
- `ai-api/app/dataset_retrieval.py`
- `ai-api/app/schemas.py`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_retrieval_cache.py`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_importer.py`
- `docs/local-recipe-dataset-adapter.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `README.md`
- `.env.example`
- `outbox/0029B-10-local-in-memory-retrieval-cache-results.md`

Done criteria:

- repeated identical dataset/index requests reuse a bounded in-memory cache;
- repeated identical retrieval calls can reuse cached results;
- cache keys invalidate on dataset source metadata, record limits, normalization version, or query changes;
- metadata exposes only safe short fingerprints, hit/miss state, and bounded counts;
- no disk cache, generated index artifact, Redis, SQLite, or production persistent memory is introduced;
- normal validation remains offline and mock-only;
- no generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.

## 0029B-11: RAG End-To-End Integration Test Harness

Status: complete.

Goal: Add an automated offline E2E integration test for the RAG-informed importer path through the real `/ai/import-recipe` API route.

Files likely touched:

- `ai-api/tests/test_rag_e2e_integration.py`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0029B-11-rag-end-to-end-integration-test-harness-results.md`

Done criteria:

- generated fixture dataset includes strong cheesecake, carbonara, omelet, and chicken/rice casserole records plus generic distractors;
- E2E cases exercise `/ai/import-recipe` with the mock provider and no live OpenAI calls;
- assertions cover schema-valid drafts, input quality, retrieval metadata, normalization signals, context packing, support policy, citations/provenance, safe responses, and cache hit behavior on repeated requests;
- a broad dessert prompt verifies weak/partial support is not claimed as strong grounding;
- normal validation remains offline and mock-only;
- no raw dataset files, disk cache, generated persistent index, live artifacts, screenshots, browser automation artifacts, `.env` files, logs, credentials, or secrets are committed.

## 0030H: Local Cookbook AI Product Integration

Status: complete.

Goal: provide a local product entry point before AWS/platform planning resumes.

Delivered:

- `GET /product` joins links to the external Vanilla Cookbook container and the existing AI sidecar workspace;
- `GET /product/cookbook` redirects only to the local upstream container, while `GET /product/ai` retains the existing `/demo` workspace;
- local mock smoke and static-route tests cover the shell and safe readiness display;
- no upstream frontend vendoring, production proxy, public routing, or cloud work is introduced.

AWS/platform architecture work remains queued until this local product path is the reviewed operator starting point.

## 0030A: RAG Requirements Interaction And Session Memory Architecture

Status: complete.

Goal: Design the alpha requirements and session-scoped interaction layer that sits between input quality checks and the completed 0029B RAG importer pipeline.

Files likely touched:

- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0030A-rag-requirements-interaction-and-session-memory-architecture-results.md`

Done criteria:

- architecture defines requirements extraction, confidence assessment, one-question clarification, delta classification, and RAG refresh decisions;
- lightweight session state distinguishes user-provided, inferred, defaulted, RAG-supported, and clarified-by-user requirements;
- RAG refresh policy explains when retrieval should rerun after material changes and when chatter or formatting-only requests should reuse context;
- proposed alpha API states include `draft_generated`, `clarification_needed`, `rag_refreshed`, `draft_revised`, `no_material_change`, `ready_to_finalize`, and `rejected`;
- UI proposal covers interpreted requirements, assumptions, current citations, RAG support, refresh reasons, and revised drafts;
- test strategy covers requirements extraction, clarification, delta classification, RAG refresh, cache/session interaction, safety boundaries, and API states;
- no production storage, auth, paid access, persistent memory, public route exposure, vector database, embeddings, runtime endpoints, or full chat UI are implemented.

## 0030B: Recipe Session Requirements Alpha Scaffold

Status: complete.

Goal: Add deterministic offline building blocks for the 0030A recipe-session requirements layer without adding public runtime endpoints.

Files likely touched:

- `ai-api/app/recipe_requirements.py`
- `ai-api/app/recipe_session.py`
- `ai-api/tests/test_recipe_requirements.py`
- `ai-api/tests/test_recipe_session.py`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0030B-recipe-session-requirements-alpha-scaffold-results.md`

Done criteria:

- requirements state models support dish intent, serving count, ingredients, exclusions, methods, equipment, time, dietary constraints, assumptions, confidence, questions, retrieval summaries, citation IDs, and TTL timestamps;
- requirement sources distinguish user-provided, inferred, defaulted, RAG-supported, and clarified-by-user values;
- deterministic extraction handles common cheesecake, carbonara, omelet, and chicken/rice casserole notes;
- confidence labels are `high`, `medium`, `low`, and `rejected`;
- clarification decisions ask one bounded question for vague or safety-relevant ambiguous input and avoid questions for specific input;
- follow-up delta classification supports the 0030A taxonomy;
- RAG refresh decisions detect retrieval-affecting requirement changes and ignore chatter, formatting-only, regenerate, and finalize requests;
- bounded in-memory test/demo session store supports create/get/update/expire/clear with no disk persistence;
- normal validation remains offline/mock-only;
- no production storage, auth, paid access, public route exposure, persistent memory, Redis, embeddings, vector databases, runtime API endpoints, or full chat UI are implemented.

## 0030C: Recipe Session Alpha API Endpoints

Status: complete.

Goal: Add local/offline alpha recipe-session endpoints on top of the 0030B scaffold without adding production storage or public session runtime.

Files likely touched:

- `ai-api/app/recipe_session_routes.py`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `ai-api/app/recipe_session.py`
- `ai-api/app/recipe_requirements.py`
- `ai-api/tests/test_recipe_session_api.py`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`
- `outbox/0030C-recipe-session-alpha-api-endpoints-results.md`

Done criteria:

- local alpha endpoints exist for start, message, get, and finalize;
- start creates a bounded in-memory session and returns `draft_generated`, `clarification_needed`, or `rejected`;
- message classifies follow-up input, returns `no_material_change` for chatter or formatting-only messages, and refreshes RAG for material requirement changes;
- draft generation reuses the existing importer/RAG pipeline instead of duplicating provider logic;
- get returns safe current session state;
- finalize is demo-safe and does not write to production storage;
- tests cover start, message, get, finalize, clarification, rejection, no-refresh chatter, formatting-only messages, missing/expired sessions, and safe serialization;
- no production storage, persistent memory, auth, paid access, public route exposure, Redis, embeddings, vector database, or full chat UI is implemented.

## 0030D: Recipe Session Demo UI And E2E Smoke

Status: complete.

Goal: Add the smallest useful local demo UI layer and offline smoke coverage for the recipe-session alpha endpoints.

Files likely touched:

- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/app/static/demo.css`
- `ai-api/tests/test_demo_ui.py`
- `scripts/demo-ai-mock.ps1`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0030D-recipe-session-demo-ui-and-e2e-smoke-results.md`

Done criteria:

- the existing sidecar demo UI includes a `Recipe Session Alpha` panel;
- the panel can start a session, send a follow-up, get current state, finalize for demo, and reset local UI state;
- the panel displays safe interpreted requirements, clarification questions, RAG refresh/no-refresh status, changed fields, support level, citation IDs, draft summary, citations, warnings, and expiry;
- vague input such as `make dessert` shows one clarification question and no fake draft;
- material follow-up such as `actually make it no-bake` shows RAG refresh/revised state;
- chatter and formatting-only follow-ups show no-refresh behavior;
- finalize is demo-only and does not write to production storage;
- mock demo validation exercises the recipe-session endpoint flow offline;
- no production storage, persistent memory, auth, paid access, public route exposure, browser automation, screenshots, Redis, embeddings, vector database, or full chat UI is implemented.

## 0030E: Recipe Session Eval Harness And Regression Baseline

Status: complete.

Goal: Add deterministic offline/mock eval cases for recipe-session behavior so the alpha session workflow is tracked as a regression surface in `run_evals.py`.

Files likely touched:

- `evals/ai_cookbook/session_cases.yaml`
- `evals/ai_cookbook/session_eval.py`
- `evals/ai_cookbook/run_evals.py`
- `ai-api/tests/test_recipe_session_eval_harness.py`
- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `docs/recipe-session-requirements-architecture.md`
- `README.md`
- `outbox/0030E-recipe-session-eval-harness-and-regression-baseline-results.md`

Done criteria:

- dedicated recipe-session eval cases exist for detailed draft generation, vague clarification, material method-change RAG refresh, chatter no-refresh, formatting-only no-refresh, clarification answer, demo finalize, and missing-session safety;
- `evals/ai_cookbook/session_eval.py` runs start/message/get/finalize flows through FastAPI `TestClient` with generated dataset fixtures and mock provider settings only;
- `evals/ai_cookbook/run_evals.py` includes the `recipe_session` eval group and fails non-zero on session behavior regressions;
- eval responses are checked for prompt, provider-response, secret, stack trace, generated path, and local absolute path leakage;
- tests cover case loading, happy-path execution, failure summaries, and independence from live provider environment settings;
- no production storage, persistent memory, auth, paid access, public route exposure, browser automation, screenshots, Redis, embeddings, vector database, or live OpenAI calls are added.

## 0030F: Recipe Session Alpha Hardening And Acceptance

Status: complete.

Goal: Review and harden the local Recipe Session Alpha across API responses, session state safety, UI rendering, mock smoke flow, session evals, runbook coverage, edge cases, and artifact safety.

Files likely touched:

- `ai-api/app/recipe_session_routes.py`
- `ai-api/app/static/demo.html`
- `ai-api/app/static/demo.js`
- `ai-api/tests/test_recipe_session_api.py`
- `ai-api/tests/test_demo_ui.py`
- `ai-api/tests/test_recipe_session_eval_harness.py`
- `evals/ai_cookbook/session_cases.yaml`
- `evals/ai_cookbook/session_eval.py`
- `docs/recipe-session-alpha-acceptance-runbook.md`
- `docs/recipe-session-requirements-architecture.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`
- `README.md`
- `outbox/0030F-recipe-session-alpha-hardening-and-acceptance-results.md`

Done criteria:

- API response safety tests cover prompt, provider-response, secret, stack trace, generated path, and local path leakage across start/message/get/finalize paths;
- edge-case tests cover empty/symbol starts, very vague starts, expired and unknown sessions, follow-up before draft, finalize before draft, repeated finalize, repeated no-refresh, contradictory method updates, equipment changes, and excluded-ingredient updates;
- demo UI labels alpha/demo-only behavior, session expiration, no-refresh reuse, friendly missing/expired-session errors, and demo-only finalize boundaries;
- session evals include equipment-change refresh, excluded-ingredient refresh, finalize-before-draft, and missing finalize checks;
- mock demo validation continues to exercise start, material follow-up/RAG refresh, get, finalize, vague clarification, chatter/no-refresh, and forbidden-text safety offline;
- [Recipe Session Alpha Acceptance Runbook](recipe-session-alpha-acceptance-runbook.md) documents local validation, expected states, known Windows pytest temp ACL issue, and non-goals;
- normal validation remains offline/mock-only;
- no production storage, persistent memory, auth, paid access, public route exposure, browser automation, screenshots, Redis, embeddings, vector database, invite flow, budget enforcement runtime, or live OpenAI calls are added.

## 0029C: Session And Metering Schema Draft

Status: complete.

Goal: Draft schemas and tests for sessions, access grants, meter events, and admin audit events without enabling public live AI.

Files likely touched:

- `ai-api/app/ai_access_models.py`
- `ai-api/tests/test_ai_access_models.py`
- `docs/ai-session-metering-schema.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `README.md`
- `outbox/0029C-session-and-metering-schema-draft-results.md`

Done criteria:

- schema models exist for AI demo sessions, access grants, provider meter events, quality/eval events, admin audit events, and budget snapshots;
- models are deterministic, offline-testable, and independent from production databases;
- safe serialization helpers expose IDs, statuses, timestamps, workflows, counts, provider/model names, cost estimates, and fingerprints while rejecting prompt, provider-response, secret, local path, raw token, and storage URL leakage;
- budget snapshots calculate remaining provider calls, remaining estimated cost, exhaustion state, and status reason;
- tests cover defaults, sample model creation, mock/offline meter events, token/cost meter events, audit and quality event safe views, budget calculations, and forbidden-string rejection;
- documentation explains how the schema layer supports future operator gate, invite flow, provider budget enforcement, and admin report tasks;
- no production storage, database migrations, auth, paid access, public route exposure, persistent memory, Redis, Postgres, payment integration, admin dashboard, runtime budget enforcement, or live OpenAI calls are added.

## 0029D: Local Operator Access Gate

Status: complete.

Goal: Add a local/private operator gate for controlled AI demo access before invite-only or public exposure.

Completed behavior:

- local operator gate settings are opt-in and disabled by default so offline and mock demo paths remain unchanged;
- protected AI demo workflows can be blocked or allowed using safe fingerprint comparison against `X-AI-Operator-Token` or `Authorization: Bearer ...`;
- supported workflows include importer, dataset ask/RAG, recipe-session alpha, and meal plan;
- local requests can use the explicit local bypass when enabled, but the helper and API responses remain safe and do not expose raw tokens, headers, or local paths;
- TestClient-based unit tests cover disabled, allowed, blocked, misconfigured, and route-level gate behavior.

## 0029E: Provider Call Budget Enforcement

Status: complete.

Goal: Centralize provider-call budget checks for call count, token caps, estimated cost, and global provider disable.

Completed behavior:

- centralized budget settings cover live-call enablement, global disable, call-count caps, token caps, and estimated cost caps;
- mock/local provider calls remain zero-cost and allowed by default;
- live provider calls are blocked before invocation when the budget is invalid, disabled, exhausted, or over cap;
- safe `AiProviderBudgetDecision`, `AiBudgetSnapshot`, and `AiProviderMeterEvent` values are produced for operator/debug visibility;
- importer, dataset ask, recipe-session, and meal-plan paths use the shared helper so callers do not duplicate budget logic.

## 0029F: Invite-Only Demo Session Flow

Status: complete.

Goal: Add short-lived invite sessions with expiry, revocation, and per-session provider budgets.

Completed behavior:

- local/private invite sessions are disabled by default and can be enabled only for controlled demo use;
- invite grants can be created locally, expose the raw invite token once, and store only safe fingerprints afterward;
- invite tokens can be redeemed into short-lived demo sessions with session tokens, allowed-workflow limits, and per-session budget limits;
- protected workflows accept invite session tokens when invite sessions are enabled, while revoked/expired/disallowed sessions block safely;
- safe status, grant, session, and audit views are available without leaking raw invite/session tokens or local paths.

## 0029G: Admin Usage Report Prototype

Status: complete.

Goal: Prototype an operator report for active sessions, provider calls, estimated spend, quality failures, and threshold warnings.

Implemented as a safe local/operator usage report in `ai-api/app/ai_usage_report.py`, `GET /ai/admin/usage-report`, and the compact `/demo` operator card.

## 0029H: Public Route Exposure Review

Status: complete.

Goal: Review Cloudflare, reverse proxy, CORS, and route exposure before any public live provider-backed AI access.

Completed behavior:

- the AI route surface is inventoried with current exposure, OpenAPI visibility, provider-call risk, gate/invite/budget controls, and recommended exposure category;
- the admin usage-report route remains hidden from OpenAPI and is treated as never-public;
- the review documents proxy and CORS staging requirements, go/no-go checklist items, and abuse/rate-limit placeholders without changing deployment config.

## 0029I: Monetization And Entitlement Boundary ADR

Status: complete.

Goal: Define the near-term monetization model and future entitlement boundary without implementing payment or premium enforcement now.

Completed behavior:

- the ADR states that near-term revenue should focus on ads, sponsorships, partner placements, and clearly disclosed affiliate links;
- the ADR states that paid access, checkout, subscriptions, billing, invoices, taxes, refunds, and premium enforcement are not implemented now;
- the ADR keeps future paid advanced features as separate, explicitly approved possibilities rather than runtime behavior;
- surrounding docs now separate monetization from access control, budget enforcement, invite sessions, and route exposure.

## 0030J: 29/30 Integrated Regression And E2E Harness

Status: complete.

Goal: Add a deterministic integrated regression harness that exercises the combined 0029/0030 local AI demo baseline offline by default and only allows live-smoke checks when explicitly opted in.

Completed behavior:

- `scripts/e2e-ai-29-30-regression.py` runs the combined mock/offline flow end to end and keeps live checks behind an explicit opt-in flag;
- `scripts/run-ai-29-30-regression.ps1` sets safe defaults for offline validation and prints a concise pass/fail summary;
- the harness covers operator gate, invite sessions, protected importer and recipe-session flows, dataset ask, saved-recipe ask, meal plan, provider budget allow/skip/block behavior, and usage-report visibility;
- the harness verifies admin usage-report OpenAPI hiding, route exposure assumptions, and the monetization boundary docs without introducing GLM or payment/runtime behavior;
- docs and tests now anchor the next follow-on, `0031A: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness`, as a separate, disabled-by-default task.

## 0030K: Env File Live Script Config Loader

Status: complete.

Goal: Make the manual live smoke and eval wrappers easier to run locally by loading configuration from an ignored `.env` file path and writing only safe missing defaults when requested.

Files likely touched:

- `scripts/lib/ai-env-file.ps1`
- `scripts/test-ai-env-file-loader.ps1`
- `scripts/demo-ai-live-smoke.ps1`
- `scripts/run-openai-demo-evals.ps1`
- `scripts/run-ai-29-30-regression.ps1`
- `docs/live-openai-smoke-tests.md`
- `docs/live-openai-demo-evals.md`
- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-evals-plan.md`
- `README.md`

Validation:

- PowerShell loader tests;
- pytest docs/script checks;
- repository validation.

Done criteria:

- live wrappers accept `-EnvFile .\.env` without printing secret values;
- the smoke wrapper can append only safe missing defaults with `-WriteMissingEnvDefaults`;
- existing process environment values still win over file values;
- `OPENAI_ENABLE_LIVE_TESTS=false` still skips live calls cleanly;
- `.env` remains uncommitted and ignored.

## 0030L: Live Importer Eval Output Cap And Safe Diagnostics

Status: complete.

Goal: Let the live importer eval path use a workflow-specific higher output cap while keeping the general live-eval guard strict, and record sanitized provider failure diagnostics in the summary output.

Completed behavior:

- `scripts/live-openai-demo-evals.py` now applies a separate importer-only output cap with a 900-token default and a 1200-token ceiling, so importer evals can stay distinct from the 300-token non-importer live-eval guard;
- importer failures now surface sanitized `provider_error_category`, `provider_error_type`, and `safe_error_summary` fields when provider diagnostics are available;
- the regression harness and live-eval docs continue to treat live checks as explicit opt-in and keep normal validation offline/mock-only;
- the docs and status pages now describe the importer-specific cap and the safe failure classifications without exposing raw prompts, responses, keys, or local paths.

## 0030M: Live Importer Eval Scoring Calibration

Status: complete.

Goal: Calibrate the importer live eval so good structured recipe drafts pass while the eval still rejects generic, rambling, unsupported, or unsafe importer output.

Completed behavior:

- importer instruction scoring now accepts a broader set of common cooking imperatives and short colon-labeled steps instead of requiring a narrow first-word verb match;
- importer token thresholds are now workflow-specific, with separate warning and failure limits for structured importer JSON plus retrieval metadata;
- short-answer workflows still keep the stricter generic token failure threshold by default;
- safe provider diagnostics from `0030L` remain intact, and the live eval summary still distinguishes provider failures from threshold failures.

## 0030N: Importer Instruction Conciseness Scorer Refinement

Status: complete.

Goal: Remove the remaining brittle importer instruction-length rule so realistic labeled recipe steps pass without weakening the live eval into a no-op.

Completed behavior:

- importer instruction scoring no longer requires every step to be 24 words or fewer;
- the scorer now uses a high single-step cap plus average-length and compact-step coverage checks;
- short colon-labeled steps remain fair, but labels are not a loophole for rambling instructions;
- failure details now report safe metrics such as `max_words`, `average_words`, `compact_steps`, and `action_oriented`;
- importer token thresholds remain unchanged from `0030M`.

## 0030O: Importer Action-Oriented Context Phrase Scorer Refinement

Status: complete.

Goal: Remove the remaining importer false failure where a realistic recipe step starts with a short context phrase before the imperative verb.

Completed behavior:

- action-oriented scoring now accepts a short setup phrase before an early imperative cooking verb;
- comma-delimited contexts such as `In a small bowl, mix...`, `With a spoon, mash...`, and `If the mixture seems thick, add...` now pass when the action verb appears early;
- non-action instructions and rambling paragraphs with only a late action verb still fail;
- the aggregate conciseness policy from `0030N` and the importer token thresholds from `0030M` remain unchanged.

## 0030P: No-Bake Cheesecake Importer Session Regression Fix

Status: complete.

Goal: Fix the recipe-session clarification path so `cheesecake, no-bake, for 4 people` no longer produces baked-cheesecake instructions in the generated draft.

Completed behavior:

- the importer now distinguishes no-bake cheesecake requests from baked cheesecake requests instead of forcing every cheesecake draft through the baked template;
- explicit no-bake phrases such as `no-bake`, `no bake`, `no oven`, `without baking`, `do not bake`, `chilled cheesecake`, and `refrigerator cheesecake` trigger chill/refrigerate/serve-cold draft shaping;
- explicit baked cheesecake requests still keep the baked `preheat`/`oven`/`bake` path;
- recipe-session API tests and offline session evals now cover the exact clarification flow `make dessert -> cheesecake, no-bake, for 4 people`;
- the regression checks assert that the retrieval query preserves the no-bake method signal and that the final draft does not leak baked-only instructions into the no-bake path.

## 0031A: GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness

Status: complete.

Goal: Evaluate a future GLM secondary-provider offload path only after the 29/30 baseline is locked, with explicit opt-in and disabled-by-default behavior.

Completed behavior:

- added a docs-first ADR for a possible future secondary/offload provider path while keeping runtime behavior unchanged;
- treats `GLM-4.7 Flash` as a candidate provider name only and does not claim verified pricing, API compatibility, limits, quality, privacy policy, or availability;
- keeps the current OpenAI `gpt-5.4-nano` path as the final-answer baseline and limits future offload ideas to advisory low-risk task classes only;
- adds a deterministic offline eval harness for simulated query expansion, context compression, title/slug suggestions, clarification candidates, and draft critique outputs;
- rejects blocked task classes, invented citation IDs, unsupported claims, private-data requests, and critique outputs that try to become final answers;
- adds no runtime provider integration, GLM SDK, provider routing, fallback behavior, public exposure, auth, storage, or live calls during normal validation.

## 0031B: Secondary Provider Fact Verification And Implementation Gate

Status: complete.

Goal: Add a docs-first provider-fact register and implementation gate so future secondary/offload provider runtime work cannot start on guessed pricing, API, privacy, retention, quota, or failure-mode assumptions.

Completed behavior:

- added [AI Secondary Provider Fact Register](ai-secondary-provider-fact-register.md) with `GLM-4.7 Flash` recorded as a candidate name only;
- kept the current GLM candidate `unverified` and `blocked` because primary provider documentation was not available in this task;
- added [AI Secondary Provider Implementation Gate](ai-secondary-provider-implementation-gate.md) with explicit go/no-go criteria and a separate future mailbox-task requirement for any runtime adapter work;
- added `evals/ai_cookbook/secondary_provider_fact_gate.yaml` and `evals/ai_cookbook/secondary_provider_fact_gate_eval.py` so offline validation proves unverified candidates stay blocked and only a fully verified synthetic fixture can pass;
- updated surrounding docs to state that `0031A` defined the advisory offload ADR, `0031B` adds fact verification and implementation gating, and future work must preserve the corrected 0030 baseline including `0030P` no-bake cheesecake behavior.

## 0031C: Cookbook AI Plugin Adapter Architecture ADR

Status: complete, docs-only; future implementation remains unapproved.

Added [Cookbook AI Plugin and Adapter Architecture ADR](cookbook-ai-plugin-adapter-architecture-adr.md).
It defines the future boundary:

```text
cookbook.roadmaps.link core app
        |
        | stable app/plugin contract
        v
Cookbook AI Adapter
        |
        | stable AI sidecar API
        v
RAG/AI sidecar
```

The ADR preserves current ownership: the core app owns users, auth, canonical
recipes, persistence, and UI; the adapter owns translation, scopes, and safe
write-back; the sidecar owns RAG, AI sessions, provider controls, and safe AI
responses. It sketches a plugin manifest, Cookbook adapter contract, AI plugin
API, session handoff, recipe read/write and indexing boundaries, UI integration
levels, contract tests, and staged migration phases. It requires the final
product to feel seamless rather than visibly bolted on.

This task does not implement integration, endpoints, auth, public routes,
provider changes, vector/embedding infrastructure, upstream UI changes,
browser automation, live calls, AWS/platform work, or payment/subscription
behavior. Normal validation remains mock/offline and current live gating is
unchanged.

## 0031D: QMD Local Hybrid Retrieval Adapter Spike

Status: complete, docs-only; QMD remains an unaccepted optional candidate.

Added [QMD Local Hybrid Retrieval Adapter Spike](qmd-local-hybrid-retrieval-adapter-spike.md).
The spike inspected QMD's public repository and documentation at a high level,
recording its Node/Bun packaging, Markdown collections, BM25/vector/hybrid
search modes, CLI/MCP surfaces, local configuration/index artifacts, native
dependencies, local GGUF model implications, and MIT license. It does not
install or vendor QMD, download models, generate snapshots/indexes, or add any
dependency to this repository.

The note keeps QMD behind a future `RetrievalBackend`/`RetrievalAdapter` seam,
defines a Markdown snapshot and Cookbook-ID/provenance mapping concept,
compares it with the accepted deterministic keyword backend, and lists risks,
unknowns, local-only proof-of-concept shape, seamless UX requirements, and
go/no-go criteria. Normal validation remains mock/offline and the deterministic
backend remains the accepted default.

## 0032A: Portfolio Platform AWS Scaling Architecture ADR

Status: complete, docs-only; infrastructure implementation remains unapproved.

Added [Portfolio Platform AWS Scaling Architecture ADR](portfolio-platform-aws-scaling-architecture-adr.md).
The decision is an EC2-first staged path for the broader portfolio platform:
single EC2 with Docker Compose, production-shaped single EC2 with externalized
config/data/logs, ALB plus EC2 Auto Scaling, and ECS on EC2 for per-service
scaling. Fargate and EKS remain later options only when explicit evidence
justifies them.

The ADR defines app-owned routes, data, storage prefixes, flags, limits,
labels, AI budgets, RAG/index boundaries, retention, and import/export rules;
the shared VPC/compute/observability/config/cost model; conceptual portfolio
metadata records; AI provider usage, budget, token, RAG, and kill-switch
controls; migration triggers; and operational acceptance evidence per phase.
It preserves the rule `Shared infrastructure is acceptable. Shared uncontrolled
state is not.`

This task creates no AWS resources, infrastructure-as-code, deployment
workflow, DNS/Cloudflare change, database migration, auth/payment system,
public route, provider routing change, secondary provider, vector/embedding
system, or production integration. Normal validation remains offline/mock-only.
