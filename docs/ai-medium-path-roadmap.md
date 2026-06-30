# AI Cookbook Medium-Path Roadmap

This roadmap designs a 2-4 week AI expansion for the existing Vanilla Cookbook deployment. The first AI phase keeps the cookbook app as a black-box container and adds a Python/FastAPI sidecar instead of forking or rebuilding the app.

## Goals

- Add useful AI features over saved recipes without changing the cookbook container first.
- Keep the app deployable on the current EC2/Compose/Cloudflare Tunnel model.
- Prefer hosted AI APIs for generation on t3.micro; make local Ollama optional.
- Build deterministic search and evals before relying on model output.
- Keep secrets in GitHub Actions secrets and the host `.env`, never in Git.

## Phase 0: Baseline And Data Discovery

Scope:

- Verify the existing app, DB volume, upload volume, and current `status`, `start`, `deploy`, `restart`, and `stop` workflow behavior.
- Inspect the SQLite schema from a copy of `db/` or a read-only mount.
- Document recipe table names, primary keys, title fields, ingredient fields, instruction fields, tags/categories, source URLs, upload references, and timestamps.
- Record schema unknowns before writing code that depends on them.

Acceptance criteria:

- A schema notes document or generated artifact identifies known recipe fields and unknowns.
- No command mutates the production database during discovery.
- The deployment and backup paths are understood before the sidecar reads data.

## Phase 1: AI Sidecar Skeleton

Scope:

- Add `ai-api` as a Python/FastAPI service.
- Add `GET /health`.
- Add config loading and provider detection for OpenAI, optional Anthropic/Google, and optional Ollama through `OLLAMA_BASE_URL`.
- Add a Dockerfile and Compose wiring without exposing new EC2 inbound ports.
- Add pytest coverage using FastAPI `TestClient`.

Acceptance criteria:

- `ai-api` starts locally with no provider key and reports configured provider availability without printing secrets.
- `GET /health` returns a stable JSON response.
- Unit tests run in CI without live provider calls.
- Compose can start the sidecar alongside the existing app.

## Phase 2: Recipe Reader And Search

Scope:

- Read the cookbook SQLite DB read-only.
- Create a normalized recipe document model with stable recipe IDs and titles.
- Implement deterministic keyword search first.
- Add optional embeddings or an index only after the reader is stable.
- Treat upload files as metadata until a reviewed parser is added.

Acceptance criteria:

- Search works without an AI provider.
- Tests cover empty DB, missing optional fields, multi-ingredient recipes, and special characters.
- The reader opens the DB in read-only mode and never writes back.
- Search responses include recipe IDs, titles, snippets, and match reasons.

## Phase 3: AI Assistant And RAG

Scope:

- Add endpoints for chat or question answering over saved recipes.
- Use a retrieval phase before generation.
- Ground answers in retrieved recipe documents with cited recipe IDs and titles.
- Refuse or say it does not know when no recipe matches.
- Add a provider abstraction so tests can use a mock provider.

Acceptance criteria:

- `POST /ai/ask` returns an answer plus cited recipe references.
- The prompt includes only retrieved recipe context, not secrets or raw environment values.
- Tests prove no-match questions return uncertainty instead of invented recipes.
- Provider failures return useful errors without leaking credentials.

## Phase 4: Structured Recipe Importer

Scope:

- Accept pasted recipe text.
- Return schema-constrained JSON for title, description, ingredients, steps, yield, time, tags, and source.
- Validate model output with Pydantic.
- Do not write imported recipes back to Vanilla Cookbook in the first version unless a later task explicitly reviews that path.

Acceptance criteria:

- `POST /ai/import-recipe` returns valid JSON matching the importer schema.
- Golden fixtures cover common web recipe text, terse notes, malformed text, and missing fields.
- The API clearly labels parsed output as a draft.
- No direct cookbook DB writes exist in this phase.

## Phase 5: Meal Planner And Shopping List

Scope:

- Generate a structured meal plan from saved recipe search results.
- Normalize a shopping list by ingredient group.
- Clearly label estimates.
- Avoid medical, allergy, or nutrition certainty claims.

Acceptance criteria:

- `POST /ai/meal-plan` returns a validated meal-plan schema.
- Plans cite saved recipe IDs/titles unless the request explicitly allows external ideas.
- Shopping lists group ingredients and preserve units when possible.
- Responses include a non-medical disclaimer for nutrition-like requests.

## Phase 6: Evals, Docs, Screenshots, And Demo Polish

Scope:

- Add eval fixtures and quality checks for search, RAG, importer, and meal planner behavior.
- Add CI validation that runs unit tests and offline evals.
- Add screenshot and demo-script docs for the portfolio.
- Add a concise portfolio section to the README.

Acceptance criteria:

- CI runs without live AI provider keys.
- Evals cover grounded answers, no-match uncertainty, importer schema validity, and meal-plan constraints.
- Demo docs show the existing cookbook, the AI assistant, search, importer, and meal planner.
- The portfolio README explains the sidecar design, security model, and eval strategy.

## Suggested Timeline

| Window | Focus | Deliverable |
| --- | --- | --- |
| Days 1-3 | Phase 0 | Schema notes and baseline checks |
| Days 4-6 | Phase 1 | FastAPI sidecar skeleton and tests |
| Days 7-10 | Phase 2 | Read-only reader and deterministic search |
| Days 11-15 | Phase 3 | RAG ask endpoint with citations |
| Days 16-19 | Phases 4-5 | Importer, meal planner, and schemas |
| Days 20-24 | Phase 6 | Evals, CI, screenshots, and demo polish |

## Non-Goals For The First AI Phase

- Forking or rebuilding the Vanilla Cookbook app.
- Writing directly to the cookbook DB.
- Requiring local LLM inference on EC2.
- Opening inbound HTTP/HTTPS ports on EC2.
- Running live provider calls in CI.
