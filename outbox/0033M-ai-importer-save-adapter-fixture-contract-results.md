# 0033M AI Importer Save Adapter Fixture Contract Results

## Summary

- Added the fixture-only `ai-api/app/cookbook_import_adapter.py` contract and
  `ai-api/tests/test_cookbook_import_adapter.py`.
- The pure in-memory adapter maps a validated `RecipeImportDraft` into a
  versioned candidate Cookbook payload without HTTP, SQLite, filesystem,
  provider, or authentication dependencies.
- Dry-run-style results include mapped payloads, safe field-level errors,
  bounded warnings, duplicate candidates, contract/schema versions, and
  idempotency replay or key-reuse-conflict metadata.
- Tests cover valid mapping, missing title/instructions, blank ingredient and
  step fields, non-contiguous steps, long fields, unknown fields, unsafe source
  URLs, duplicate fixtures, idempotent replay, key conflicts, schema mismatch,
  and safe-envelope leakage boundaries.

## Schema discovery

No upstream Vanilla Cookbook write schema was inspected, inferred, copied, or
committed. The verified local runtime only establishes a disposable app/DB and
upload layout; native write table/model names, relations, ownership defaults,
transaction behavior, and create API remain unknown. The adapter's
`cookbook-import.v1` and `cookbook-recipe-candidate.v1` labels are contract
versions, not upstream schema claims.

## Validation

Focused adapter tests passed: 11 tests. The normal requested validation path
remains offline/mock-only and does not require Docker or live OpenAI. No local
DB rows were written and no runtime route or UI was started by this task.

## Explicit non-goals

No Save-to-Cookbook button, public route, dry-run endpoint, database access or
mutation, production write-back, auth, SSO/BYOS, analytics, ads, payment,
AWS/platform work, provider routing/model change, QMD integration, live call,
secret, prompt, provider output, screenshot, trace, raw dataset, generated
index, local environment value, local DB, upload, or browser artifact was
added.
