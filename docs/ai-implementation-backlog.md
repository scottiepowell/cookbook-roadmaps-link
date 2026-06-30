# AI Implementation Backlog

This backlog breaks the medium-path AI design into follow-on mailbox tasks. Task numbers are proposed and may change if new operational fixes are needed first.

## 0016: Scaffold AI FastAPI Sidecar

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

- OpenAI config path exists but is optional.
- Mock provider supports deterministic responses.
- `/ai/config` reports non-secret provider availability only.

## 0020: Add Structured Recipe Importer

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

## 0021: Add RAG Ask Endpoint

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

## 0022: Add Meal Planner And Shopping List Endpoint

Goal: Generate a structured meal plan and grouped shopping list from saved recipes.

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

## 0023: Add Evals And CI Validation

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

## 0024: Add Screenshots, Demo Docs, And Portfolio README Polish

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
