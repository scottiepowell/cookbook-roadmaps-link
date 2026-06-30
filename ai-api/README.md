# AI API Sidecar

This is the minimal FastAPI scaffold for the AI cookbook sidecar.

Current endpoints:

- `GET /health`: returns service health.
- `GET /ai/config`: returns non-secret provider availability booleans.

This scaffold does not implement recipe search, RAG, recipe import, meal planning, cookbook DB reading, live provider calls, or write-back to Vanilla Cookbook.

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
