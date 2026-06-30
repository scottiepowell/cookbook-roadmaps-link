# Task 0016 Results: Scaffold AI FastAPI Sidecar

## Summary

Implemented the minimal `ai-api` FastAPI sidecar scaffold. The service has only health and non-secret config endpoints, Docker/Compose wiring, offline tests, validation integration, and documentation.

This task did not implement RAG, recipe search, recipe import, meal planning, cookbook DB reading, live provider calls, or write-back to Vanilla Cookbook.

## Files Created

- `ai-api/Dockerfile`
- `ai-api/README.md`
- `ai-api/requirements.txt`
- `ai-api/app/__init__.py`
- `ai-api/app/config.py`
- `ai-api/app/main.py`
- `ai-api/app/schemas.py`
- `ai-api/tests/__init__.py`
- `ai-api/tests/test_config.py`
- `ai-api/tests/test_health.py`
- `outbox/0016-scaffold-ai-fastapi-sidecar-results.md`

## Files Modified

- `.env.example`
- `README.md`
- `docker-compose.yml`
- `docs/ai-implementation-backlog.md`
- `docs/ai-sidecar-architecture.md`
- `docs/repo-map.md`
- `docs/repo-validation.md`
- `docs/runtime-scaffold.md`
- `scripts/validate-repo.sh`

## Endpoints Added

- `GET /health`
  - Returns `{"status": "ok", "service": "ai-api"}`.
- `GET /ai/config`
  - Returns provider availability booleans for `openai`, `anthropic`, `google`, and `ollama`.
  - Does not return API keys, token fragments, raw environment values, or `.env` content.

## Compose And Validation Updates

- Added `ai-api` to `docker-compose.yml` with `build.context: ./ai-api`.
- `ai-api` uses `env_file: .env`.
- No host port is published for `ai-api`; it is internal to the Compose network.
- `.env.example` keeps optional AI provider settings empty.
- `scripts/validate-repo.sh` now copies `ai-api` into the temporary Compose validation directory and runs AI API tests in a temporary Python virtual environment.

## Validation Commands And Results

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `pytest ai-api/tests`: passed in a temporary local virtual environment because outer `pytest` was not installed.
  - 4 tests passed.
  - One upstream FastAPI/TestClient deprecation warning was emitted.
- `bash -n scripts/validate-repo.sh`: passed.
- `bash scripts/validate-repo.sh`: passed.
  - Shell script syntax: PASS
  - Docker Compose configuration: PASS
  - AI API tests: PASS
  - Whitespace: PASS
  - Local Markdown links: PASS
  - Old-domain guard: PASS
  - Secret-pattern scan: PASS
- `git diff --check`: passed. Git emitted expected Windows CRLF working-copy warnings.
- `docker compose config --quiet`: Docker Compose is available. The exact command initially failed because this local clone intentionally has no untracked `.env`; rerunning the exact command with a temporary copy of `.env.example` as `.env` passed, and the temporary `.env` was removed.

## Assumptions

- This session is attached to the Windows clone at `C:\Users\scott\cookbook-roadmaps-link`; `/home/coder/repo` remains the documented Coder workspace path.
- Installing Python packages into a temporary local virtual environment is acceptable local validation and does not constitute a live provider call.
- Provider configuration should be represented only as booleans until later tasks add provider abstractions.
- Keeping `ai-api` internal to Compose is the safest first scaffold because no public AI route exists yet.

## Blockers And Limitations

- Outer Python did not have `pytest` or FastAPI installed, so tests were run through a temporary venv.
- The local clone does not have `.env`, so plain `docker compose config --quiet` needs a temporary example `.env` for local validation.
- The sidecar has no recipe search, RAG, importer, meal planner, DB reader, provider SDK, or live model integration yet.

## Recommended Next Task

Proceed with task 0017: add safe DB schema inspection and a read-only recipe reader using fixtures and tests, without writing to the cookbook database.
