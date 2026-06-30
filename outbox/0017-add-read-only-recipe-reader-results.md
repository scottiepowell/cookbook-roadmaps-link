# Task 0017 Results: Add Read-Only Recipe Reader

## Summary

Added a fixture-driven SQLite schema inspector and read-only recipe reader for the `ai-api` service. The reader normalizes recipe-like rows into `RecipeDocument` objects and fails with a controlled exception when no conservative recipe table match exists.

This task did not implement search endpoints, RAG, recipe importing, meal planning, cookbook DB write-back, or live AI provider calls.

## Files Created

- `inbox/0017-add-read-only-recipe-reader.md`
- `ai-api/app/schema_inspector.py`
- `ai-api/app/recipe_reader.py`
- `ai-api/tests/test_recipe_reader.py`
- `docs/ai-schema-notes.md`
- `outbox/0017-add-read-only-recipe-reader-results.md`

## Files Modified

- `ai-api/README.md`
- `ai-api/app/config.py`
- `ai-api/app/schemas.py`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/repo-map.md`

## Read-Only SQLite Approach

- `open_read_only_sqlite()` resolves the DB path and opens SQLite with URI mode `mode=ro` and `uri=True`.
- `COOKBOOK_DB_PATH` is supported through `get_cookbook_db_path()`.
- The default future path is `/data/cookbook-db/dev.db`.
- No Compose DB mount was added in this task. Docs record the future read-only mount pattern: `./db:/data/cookbook-db:ro`.
- The reader uses `SELECT` and schema inspection only. It does not write to the database.

## Fixture Schema Used For Tests

Tests generate a temporary SQLite DB at runtime; no binary DB fixture is committed.

```sql
CREATE TABLE recipes (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  ingredients TEXT,
  instructions TEXT,
  tags TEXT,
  source_url TEXT
);
```

Fixture data covers:

- a complete recipe with JSON-array ingredients, newline-separated instructions, newline-separated tags, and source URL;
- a minimal recipe with missing optional fields.

## Validation Commands And Results

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

Results:

- `pytest ai-api/tests`: passed in a temporary local virtual environment.
  - 9 tests passed.
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
- `docker compose config --quiet`: passed using a temporary `.env` copied from `.env.example`; no containers were started and the temporary `.env` was removed.

## Assumptions And Production-Schema Unknowns

- This session is attached to the Windows clone at `C:\Users\scott\cookbook-roadmaps-link`; `/home/coder/repo` remains the documented Coder workspace path.
- The production Vanilla Cookbook SQLite schema is still unknown in this repo.
- Actual production table names, recipe IDs, ingredient storage, instruction storage, tags/categories, source URL fields, upload references, and deleted/private/draft markers still need inspection from a copy or read-only mount.
- Conservative table detection is intentionally narrow to avoid treating unrelated tables as recipes.
- Recipe write-back remains out of scope until a later reviewed task covers backup, migration, and rollback rules.

## Recommended Next Task

Proceed with task 0018: add deterministic recipe search over `RecipeDocument` objects and expose search endpoints, still without RAG or live provider calls.
