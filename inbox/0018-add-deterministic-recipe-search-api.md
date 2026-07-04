# Task 0018: Add Deterministic Recipe Search API

## Goal

Add the first user-facing recipe data capability to the `ai-api` sidecar: deterministic keyword search over `RecipeDocument` objects from the read-only recipe reader.

This task should not add RAG, embeddings, importer, meal planner, write-back, or live AI provider calls.

## Context

Task 0016 added the FastAPI sidecar scaffold. Task 0017 added:

- `RecipeDocument`
- SQLite schema inspection
- read-only recipe reader
- generated SQLite fixture tests
- schema notes

Now add a small search layer that works offline and is easy to test.

## Requirements

### 1. Search module

Add a module such as:

```text
ai-api/app/search.py
```

Implement deterministic keyword search over a list of `RecipeDocument` objects.

Suggested behavior:

- normalize query text by lowercasing and tokenizing simple words;
- search title, description, ingredients, instructions, tags, and source;
- rank title/tag matches higher than body matches;
- return stable ordering for equal scores;
- include match reasons/snippets where practical;
- return an empty list for empty/no-match queries.

### 2. Response schemas

Add Pydantic schemas for search request/response.

Suggested fields:

```text
RecipeSearchRequest:
  query: str
  limit: int = 10

RecipeSearchResult:
  id: str
  title: str
  score: float | int
  matched_fields: list[str]
  snippet: str | None

RecipeSearchResponse:
  query: str
  count: int
  results: list[RecipeSearchResult]
```

Use validation for sane limits.

### 3. API routes

Add routes:

```text
GET  /recipes/search?q=<query>&limit=<n>
POST /recipes/search
```

The endpoints should:

- use `COOKBOOK_DB_PATH` through the existing reader;
- return a controlled error if no recipe-like table is found;
- return empty results for empty/no-match queries;
- not expose raw recipe private data beyond minimal search result snippets;
- not require provider keys.

### 4. Tests

Add offline tests with generated SQLite fixture data.

Cover:

- title match ranks first;
- ingredient match works;
- tag match works;
- no-match returns empty results;
- empty query returns empty results;
- limit is respected;
- GET and POST endpoints work through FastAPI TestClient;
- endpoint works with `COOKBOOK_DB_PATH` set to fixture DB;
- no provider keys are required.

### 5. Docs

Update:

- `ai-api/README.md`
- `docs/ai-sidecar-architecture.md`
- `docs/ai-implementation-backlog.md`
- `docs/ai-schema-notes.md` if useful
- `docs/repo-map.md` if useful

Document that this is deterministic search only, not RAG or embeddings yet.

### 6. Validation

Run local validation only:

```bash
pytest ai-api/tests
bash -n scripts/validate-repo.sh
bash scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct pytest is unavailable, the repo validator must still run the tests in its temporary venv and the limitation must be recorded.

Do not run `docker compose up`, deployment workflows, cloud commands, or live AI-provider commands.

## Outbox report

Create:

```text
outbox/0018-add-deterministic-recipe-search-api-results.md
```

Include:

- Summary of implementation.
- Files created/modified.
- Search ranking behavior.
- Endpoints added.
- Validation commands and results.
- Assumptions and limitations.
- Recommended next task.

## Commit

Commit with:

```bash
git add inbox/0018-add-deterministic-recipe-search-api.md ai-api docs outbox/0018-add-deterministic-recipe-search-api-results.md
git commit -m "mailbox: complete task 0018 add deterministic recipe search api"
git push origin main
```

## Done criteria

- Deterministic recipe search exists and is tested.
- `GET /recipes/search` works.
- `POST /recipes/search` works.
- Tests use generated fixture data and no provider keys.
- Docs explain this is search only, not RAG.
- Validation passes.
- Outbox report exists.
- Changes are committed and pushed.
