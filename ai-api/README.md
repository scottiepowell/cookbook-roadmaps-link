# AI API Sidecar

This is the minimal FastAPI scaffold for the AI cookbook sidecar.

Current endpoints:

- `GET /health`: returns service health.
- `GET /ai/config`: returns non-secret provider availability booleans.

Internal reader modules:

- `app.schema_inspector`: lists SQLite user tables and columns as structured objects.
- `app.recipe_reader`: opens SQLite with URI `mode=ro` and normalizes recipe-like rows into `RecipeDocument`.

This scaffold does not implement recipe search endpoints, RAG, recipe import, meal planning, live provider calls, or write-back to Vanilla Cookbook.

## Cookbook DB Path

The future production DB path is configured with `COOKBOOK_DB_PATH`. The current default is:

```text
/data/cookbook-db/dev.db
```

No Compose DB mount is enabled yet. When the production reader is wired into Compose, mount the cookbook DB read-only, for example `./db:/data/cookbook-db:ro`.

## Local Tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest tests
```

The root repository validator also runs these tests in a temporary virtual environment:

```bash
bash scripts/validate-repo.sh
```

Provider keys are optional. `/ai/config` only reports whether provider settings are present and never returns key values.
