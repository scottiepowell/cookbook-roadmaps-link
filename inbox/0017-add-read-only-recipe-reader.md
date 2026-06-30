# Task 0017: Add Read-Only Recipe Reader

## Goal

Add a fixture-driven SQLite schema inspector and read-only recipe reader for the `ai-api` service. This prepares for deterministic recipe search in task 0018.

Do not implement search, RAG, recipe importing, meal planning, or live AI provider calls.

## Current Context

- Task 0016 added `ai-api` with `GET /health`, `GET /ai/config`, Dockerfile, Compose service, tests, and validation integration.
- Existing tests must remain offline and deterministic.

## Requirements

1. Add a normalized `RecipeDocument` model under `ai-api/app/`.
   Suggested fields:
   - `id: str`
   - `title: str`
   - `description: str | None`
   - `ingredients: list[str]`
   - `instructions: list[str]`
   - `tags: list[str]`
   - `source: str | None`
   - `raw: dict[str, Any]`
   Use safe defaults for list/dict fields.

2. Add SQLite schema inspection.
   Suggested file:
   - `ai-api/app/schema_inspector.py`

   It should list user tables and columns and return structured objects, not raw cursor tuples.

3. Add read-only recipe reader.
   Suggested file:
   - `ai-api/app/recipe_reader.py`

   It should:
   - open SQLite database paths read-only using sqlite3 URI mode, e.g. `mode=ro` with `uri=True`;
   - support a configurable future DB path such as `COOKBOOK_DB_PATH`;
   - support generated test fixture schema;
   - conservatively detect recipe-like tables/columns;
   - return normalized `RecipeDocument` objects;
   - fail with a clear controlled exception when no recipe-like table is found;
   - avoid database writes completely.

4. Add pytest tests using a generated temporary SQLite fixture DB.
   Do not commit a binary database.

   Tests should cover:
   - schema inspection returns expected tables/columns;
   - reader returns recipe documents from fixture data;
   - missing optional fields are handled;
   - no recipe-like table returns a controlled error;
   - tests require no real `db/` directory and no provider keys.

5. Compose/docs:
   - If adding a db mount to `ai-api`, use read-only mount syntax like `./db:/data/cookbook-db:ro`.
   - It is acceptable to defer the mount and only document the future path.
   - Update `ai-api/README.md`.
   - Update `docs/ai-sidecar-architecture.md`.
   - Update `docs/ai-implementation-backlog.md`.
   - Create `docs/ai-schema-notes.md`.
   - Update `docs/repo-map.md` if useful.
   - Schema notes should explain fixture-driven testing, read-only access, and production-schema unknowns.

6. Do not add recipe search API yet. Task 0018 will add deterministic search endpoints.

7. Run local validation only:
   - `pytest ai-api/tests`
   - `bash -n scripts/validate-repo.sh`
   - `bash scripts/validate-repo.sh`
   - `git diff --check`
   - `docker compose config --quiet` if Docker Compose is available

   Do not run `docker compose up`.

8. Create `outbox/0017-add-read-only-recipe-reader-results.md` with:
   - Summary of implementation
   - Files created/modified
   - Read-only SQLite approach
   - Fixture schema used for tests
   - Validation commands and results
   - Compose config validation result, if run
   - Assumptions and production-schema unknowns
   - Recommended next task

9. Commit:

```bash
git add inbox/0017-add-read-only-recipe-reader.md ai-api docs docker-compose.yml scripts outbox/0017-add-read-only-recipe-reader-results.md
git commit -m "mailbox: complete task 0017 add read only recipe reader"
git push origin main
```

## Done Criteria

- `RecipeDocument` model exists.
- SQLite schema inspection exists and is tested.
- Read-only recipe reader exists and is tested with generated fixture DB data.
- Tests require no real cookbook DB and no provider keys.
- Documentation records schema assumptions and unknowns.
- Validation passes.
- Outbox report exists.
- Changes are committed and pushed.
