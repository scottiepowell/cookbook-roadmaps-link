# Task 0016: Scaffold AI FastAPI Sidecar

## Goal

Implement the first code step for the AI medium-path roadmap: add a minimal Python/FastAPI `ai-api` sidecar service with health/config endpoints, Docker/Compose wiring, offline tests, and documentation.

This task must not implement RAG, recipe import, meal planning, live provider calls, or DB reading yet. It should create a safe, testable foundation.

## Current context

Task 0015 created the AI design docs:

- `docs/ai-medium-path-roadmap.md`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-evals-plan.md`
- `docs/ai-implementation-backlog.md`

The backlog defines 0016 as the AI FastAPI sidecar scaffold. Existing Compose services are:

- `app`
- `cloudflared`

The workflow/environment already references optional AI provider settings:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `OLLAMA_BASE_URL`

## Important rules

- Do not commit secrets.
- Do not print `.env` contents.
- Do not run live OpenAI, Anthropic, Google, Ollama, AWS, Cloudflare, or deployment commands.
- Do not modify GitHub repository settings.
- Tests must pass without live provider keys.
- Keep the existing cookbook app as a black-box container.
- Do not expose new EC2 inbound ports.
- Do not read or write the production cookbook database in this task.

## Required implementation

### 1. Create `ai-api/` service skeleton

Create a minimal Python/FastAPI application.

Suggested structure:

```text
ai-api/
  Dockerfile
  README.md
  requirements.txt
  app/
    __init__.py
    main.py
    config.py
    schemas.py
  tests/
    __init__.py
    test_health.py
    test_config.py
```

Use simple dependencies only:

- `fastapi`
- `uvicorn[standard]`
- `pydantic` / `pydantic-settings` if useful
- `pytest`
- `httpx` for FastAPI `TestClient` if needed

Do not add LangChain, vector databases, or provider SDKs yet.

### 2. Add endpoints

Implement:

```text
GET /health
GET /ai/config
```

`GET /health` should return stable JSON such as:

```json
{
  "status": "ok",
  "service": "ai-api"
}
```

`GET /ai/config` should return non-secret provider availability only. Example:

```json
{
  "providers": {
    "openai": {"configured": false},
    "anthropic": {"configured": false},
    "google": {"configured": false},
    "ollama": {"configured": false}
  }
}
```

Do not return actual API keys, token fragments, environment values, or `.env` content.

### 3. Add tests

Add offline tests using FastAPI `TestClient`/pytest.

Tests should cover:

- `GET /health` returns 200 and the expected service/status.
- `GET /ai/config` returns provider names and configured booleans.
- `GET /ai/config` does not leak actual secret-like values when fake env vars are set during tests.
- app imports cleanly.

All tests must pass without provider keys.

### 4. Add Dockerfile

Create a simple production-ish Dockerfile for `ai-api`.

Requirements:

- use a slim Python base image;
- install dependencies;
- copy app code;
- run `uvicorn app.main:app --host 0.0.0.0 --port 8000` or equivalent;
- avoid baking secrets into the image.

### 5. Update Docker Compose

Update `docker-compose.yml` to add `ai-api`.

Requirements:

- build from `./ai-api`;
- use `env_file: .env`;
- expose only to the Compose network by default;
- do not publish a public EC2 port;
- optional localhost-only mapping is acceptable only if clearly documented, for example `127.0.0.1:8000:8000`, but prefer no host port for first scaffold unless docs justify it;
- keep existing `app` and `cloudflared` behavior intact.

### 6. Update `.env.example`

Ensure `.env.example` documents optional AI settings without secrets:

```text
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OLLAMA_BASE_URL=
```

If those already exist elsewhere, avoid duplication and keep values placeholder/empty.

### 7. Update validation

Update repo validation so AI sidecar tests are included when possible.

Options:

- Add a script such as `scripts/validate-ai-api.sh` and call it from `scripts/validate-repo.sh`; or
- Update `scripts/validate-repo.sh` directly to run AI tests if `ai-api/` exists.

The validation should avoid live provider calls and should not require secrets.

### 8. Update docs

Update relevant docs:

- `README.md`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md` if useful
- `docs/repo-map.md`
- `docs/runtime-scaffold.md` if useful

Document:

- what the sidecar does now;
- how to run its tests locally;
- how it is wired into Compose;
- that it does not yet implement recipe search, RAG, importer, or meal planner;
- that provider configuration reports only booleans and never secrets.

### 9. Validation commands

Run local validation only:

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
```

If `pytest` is not installed in the outer environment, run tests through the project-supported method you add and document the limitation clearly. Do not skip tests silently.

Also run:

```bash
docker compose config --quiet
```

if Docker Compose is available. If unavailable, document that blocker in the outbox report.

Do not run Docker Compose up, AWS, Cloudflare, OpenAI, Anthropic, Google, Ollama, or deployment commands.

### 10. Outbox report

Create:

```text
outbox/0016-scaffold-ai-fastapi-sidecar-results.md
```

Include:

- Summary of implementation.
- Files created/modified.
- Endpoints added.
- Validation commands and results.
- Whether Docker Compose config validation ran.
- Assumptions.
- Blockers/limitations.
- Recommended next task.

### 11. Commit

Commit with:

```bash
git add ai-api docker-compose.yml .env.example scripts README.md docs outbox/0016-scaffold-ai-fastapi-sidecar-results.md
git commit -m "mailbox: complete task 0016 scaffold ai fastapi sidecar"
```

Stage only actual changed files.

Push to `origin/main` if remote access is available.

## Done criteria

This task is complete when:

- `ai-api/` exists with a minimal FastAPI app.
- `GET /health` exists and is tested.
- `GET /ai/config` exists and is tested for non-secret output.
- `ai-api` has a Dockerfile.
- Compose includes `ai-api` without opening public EC2 ports.
- `.env.example` includes optional AI provider settings without secrets.
- Local validation includes AI sidecar tests.
- Docs explain the scaffold and limitations.
- Outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
