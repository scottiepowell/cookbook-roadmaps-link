# AI Schema Notes

Task 0017 added fixture-driven SQLite schema inspection and a read-only recipe reader for the AI sidecar. Task 0018 uses those normalized documents for deterministic keyword search. These tasks do not inspect or depend on a live production cookbook database.

## Fixture-Driven Testing

Tests generate a temporary SQLite database at runtime. No binary database fixture is committed.

The generated fixture schema is:

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

Fixture rows cover:

- a complete recipe with JSON-array ingredients, newline-separated instructions, newline-separated tags, and a source URL;
- a minimal recipe with only required fields and missing optional fields.
- search fixture rows that exercise title, ingredient, tag, empty-query, no-match, and limit behavior.

## Read-Only Access

The reader opens SQLite using URI mode:

```text
file:<resolved-path>?mode=ro
```

This prevents accidental writes through the reader connection. The production path is intended to be configurable through `COOKBOOK_DB_PATH`. No Compose DB mount is enabled yet. When the production database is mounted, use read-only syntax such as:

```yaml
./db:/data/cookbook-db:ro
```

## Normalized Document Shape

Rows are normalized into `RecipeDocument`:

```text
id: str
title: str
description: str | None
ingredients: list[str]
instructions: list[str]
tags: list[str]
source: str | None
raw: dict[str, Any]
```

List fields default to empty lists, and `raw` keeps the original row values for later debugging and search work.

## Deterministic Search

The search layer reads `RecipeDocument` objects and does not access SQLite directly. It lowercases and tokenizes simple words, searches title, tags, ingredients, instructions, description, and source, and returns minimal result data: ID, title, score, matched fields, and a short snippet.

This is not RAG, embeddings, semantic retrieval, importing, meal planning, provider-backed generation, or write-back.

## Conservative Table Detection

The reader looks for a table with a title-like column and either recipe-body columns or a recipe-like table name. It currently recognizes common column names such as:

- ID: `id`, `uuid`, `slug`
- title: `title`, `name`
- description: `description`, `summary`, `notes`
- ingredients: `ingredients`, `ingredient_text`, `ingredient`
- instructions: `instructions`, `directions`, `steps`, `method`
- tags: `tags`, `categories`, `category`
- source: `source`, `source_url`, `url`, `link`

If no conservative match is found, the reader raises a controlled `NoRecipeTableFoundError`.

## Production Schema Unknowns

The real Vanilla Cookbook SQLite schema is still unknown in this repo. Before production use or semantic retrieval, inspect a copy or read-only mount of the production DB and confirm:

- actual recipe table names;
- primary key type and stability;
- title, description, ingredient, instruction, tag, and source URL fields;
- whether ingredients and instructions are JSON, text, related tables, or another format;
- upload/file references;
- whether deleted, archived, private, or draft recipes exist and should be filtered.

Do not write to the cookbook database from the AI sidecar without a later reviewed task that covers backups, migrations, and rollback.

## 0033M fixture adapter boundary

The Phase 1 fixture adapter in `ai-api/app/cookbook_import_adapter.py` maps the
validated `RecipeImportDraft` into an in-memory candidate payload. Its explicit
labels are `cookbook-import.v1` and `cookbook-recipe-candidate.v1`; these are
contract identifiers, not discovered Vanilla Cookbook table or API names.

The adapter accepts only title, description, servings, ingredients,
instructions, tags, source, and notes. It rejects unknown fields, invalid or
non-contiguous steps, unsafe URL schemes, unsupported versions, and bounded
field violations. It can compare against synthetic existing-recipe fixtures
for duplicate warnings and keeps idempotency results in process memory. It
does not open SQLite, call the local container, expose a route, or write any
data.

The upstream write schema remains unknown. Before disposable write/rollback
testing, discover the native recipe model/table, relations, required defaults,
ownership fields, revision behavior, transaction boundary, upload handling,
and supported create API using only disposable local data and a verified
restore point. No local runtime schema facts are treated as production facts.

## 0033N dry-run operation

`ai-api/app/cookbook_import_dry_run.py` provides the Phase 2 internal operation
`dry_run_import_candidate_operation`. It defaults to a safe unavailable result
and requires an explicit non-secret `enabled=True` caller decision. When
enabled, it delegates to `FakeCookbookAdapter` and returns a stable operation
envelope containing the no-write adapter result, mapped candidate, field
errors, warnings, duplicate signals, idempotency metadata, and contract/schema
versions.

No HTTP route is exposed in this phase. The current sidecar does not have an
authenticated core-app adapter boundary, so a route would prematurely create
an exposure decision. The operation does not require Docker, the local
Vanilla Cookbook container, SQLite, uploads, provider keys, or live OpenAI.
Phase 3 disposable write/rollback testing must still use `cookbook-local` only
after schema and restore-point review.
