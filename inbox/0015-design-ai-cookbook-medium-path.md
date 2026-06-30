# Task 0015: Design AI Cookbook Medium Path

## Goal

Design the 2-4 week medium-path AI portfolio expansion for this project before implementing it.

The target is to make the existing self-hosted Vanilla Cookbook deployment feel like an original portfolio project by adding a polished AI layer:

- AI assistant over saved recipes
- recipe search
- meal planner
- structured recipe importer
- evals
- deployment docs
- screenshot/demo plan
- GitHub Actions validation

This task is design/documentation only. Do not implement the full AI service yet.

## Current project context

- Repository: `scottiepowell/cookbook-roadmaps-link`
- Public hostname: `cookbook.roadmaps.link`
- Deployment model: GitHub Actions OIDC to AWS, SSM Run Command, EC2, Docker Compose, Cloudflare Tunnel.
- Existing app service image: `jt196/vanilla-cookbook:stable`.
- Current Compose services: `app`, `cloudflared`.
- Persistent app data: `./db`, `./uploads`.
- Existing workflow already references optional provider settings: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`.

## Design constraints

- Keep the existing cookbook app as a black-box container for the first AI phase.
- Add AI as a sidecar service rather than forking/rebuilding the cookbook app at first.
- Prefer Python/FastAPI for the AI sidecar.
- Keep t3.micro limits in mind: do not require a local LLM on EC2.
- Use hosted AI API first; make Ollama/local provider optional via `OLLAMA_BASE_URL`.
- Do not commit secrets.
- Do not print `.env` contents.
- Do not run AWS, Cloudflare, OpenAI, Anthropic, Google, or deployment commands.
- Keep docs portfolio-ready and beginner-friendly.

## Sources and implementation assumptions to reflect in docs

The design should align with these patterns:

- RAG has an indexing phase and a retrieval/generation phase.
- Function/tool calling is appropriate when models need to access application data/functions.
- Structured Outputs are appropriate for schema-constrained recipe import and meal-plan responses.
- FastAPI should be testable with pytest/TestClient.

Do not copy large text from external docs. Summarize design choices.

## Work to perform

### 1. Inspect current repo

Run local inspection only:

```bash
pwd
ls -la
git status --short --branch
git log --oneline -10
find . -maxdepth 4 -type f | sort
sed -n '1,160p' docker-compose.yml
sed -n '1,220p' .github/workflows/cookbook-ec2-control.yml
sed -n '1,220p' README.md
```

Record relevant findings in the outbox report.

### 2. Create `docs/ai-medium-path-roadmap.md`

Create a 2-4 week roadmap with phases.

Include at minimum:

#### Phase 0: Baseline and data discovery

- verify existing app, DB volume, upload volume, stop/start/deploy workflows;
- inspect SQLite schema safely from a copy or read-only mount;
- document recipe fields and any schema unknowns.

#### Phase 1: AI sidecar skeleton

- `ai-api` FastAPI service;
- health endpoint;
- config loader/provider detection;
- Dockerfile;
- Compose wiring;
- tests.

#### Phase 2: Recipe reader and search

- read cookbook DB read-only;
- create recipe document model;
- deterministic keyword search first;
- optional embeddings/index after the reader is stable.

#### Phase 3: AI assistant and RAG

- endpoints for chat/query;
- grounded answers with cited recipe IDs/titles;
- refusal/uncertainty behavior when no recipe matches;
- provider abstraction.

#### Phase 4: Structured recipe importer

- paste raw recipe text;
- return schema-constrained JSON;
- validate with Pydantic;
- no direct write-back to cookbook in first version unless explicitly reviewed.

#### Phase 5: Meal planner and shopping list

- generate structured meal plan from saved recipes;
- normalize shopping list;
- clearly label estimates and avoid medical claims.

#### Phase 6: Evals, docs, screenshots, and demo polish

- eval fixtures/questions;
- CI tests;
- screenshots/demo script;
- portfolio README section.

Include acceptance criteria for each phase.

### 3. Create `docs/ai-sidecar-architecture.md`

Document the proposed architecture.

Include:

- service diagram in Mermaid if appropriate;
- services: `app`, `cloudflared`, `ai-api`, optional `ai-index` volume;
- why AI is a sidecar first;
- read-only access to recipe DB;
- API endpoint proposal:
  - `GET /health`
  - `GET /recipes/search?q=` or `POST /recipes/search`
  - `POST /ai/ask`
  - `POST /ai/import-recipe`
  - `POST /ai/meal-plan`
  - `GET /ai/config`
- provider abstraction:
  - OpenAI first;
  - Anthropic/Google later;
  - Ollama optional/homelab mode;
- secrets/config design;
- how to expose the AI UI/API safely later without opening EC2 inbound ports;
- risks/unknowns.

### 4. Create `docs/ai-evals-plan.md`

Design the eval strategy.

Include:

- unit tests for recipe parsing/search;
- integration tests for API endpoints;
- golden test fixtures for importer outputs;
- RAG quality checks:
  - answer grounded in retrieved recipes;
  - correct recipe references;
  - says it does not know when no recipe matches;
  - no secret leakage;
- meal-plan checks:
  - includes only retrieved/saved recipes unless allowed;
  - shopping list groups ingredients;
  - avoids medical/nutrition certainty claims;
- proposed directory layout:
  - `ai-api/tests/`
  - `ai-api/tests/fixtures/`
  - `evals/ai_cookbook/`
- example eval cases in a table.

### 5. Create `docs/ai-implementation-backlog.md`

Create a practical backlog of follow-on mailbox tasks.

Include tasks such as:

- 0016: scaffold AI FastAPI sidecar;
- 0017: add DB schema inspection and read-only recipe reader;
- 0018: add deterministic recipe search API;
- 0019: add AI provider abstraction and mock provider;
- 0020: add structured recipe importer;
- 0021: add RAG ask endpoint;
- 0022: add meal planner and shopping list endpoint;
- 0023: add evals and CI validation;
- 0024: add screenshots/demo docs and portfolio README polish.

Each backlog item should have a goal, files likely touched, validation, and done criteria.

### 6. Update existing docs

Add links to the new AI docs in:

- `README.md`
- `docs/repo-map.md`
- `docs/architecture.md` if useful

Keep updates minimal and focused.

### 7. Validation

Run local validation only:

```bash
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

Do not run AWS, Cloudflare, OpenAI, Anthropic, Google, or deployment commands.

### 8. Outbox report

Create:

```text
outbox/0015-design-ai-cookbook-medium-path-results.md
```

Include:

- Summary of design docs created.
- Files created/modified.
- Repo inspection findings.
- Validation commands and results.
- Assumptions.
- Risks/unknowns.
- Recommended next task.

### 9. Commit

Commit with:

```bash
git add docs/ai-medium-path-roadmap.md docs/ai-sidecar-architecture.md docs/ai-evals-plan.md docs/ai-implementation-backlog.md README.md docs/repo-map.md docs/architecture.md outbox/0015-design-ai-cookbook-medium-path-results.md
git commit -m "mailbox: complete task 0015 design ai cookbook medium path"
```

If only a subset of existing docs changed, stage only actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- The 2-4 week AI roadmap exists.
- The sidecar architecture document exists.
- The eval plan exists.
- The implementation backlog exists.
- Existing docs link to the new AI docs where useful.
- Local validation passes.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
