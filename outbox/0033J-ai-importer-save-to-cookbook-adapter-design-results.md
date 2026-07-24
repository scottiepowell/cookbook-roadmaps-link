# 0033J AI Importer Save-to-Cookbook Adapter Design Results

## Summary

- Created [AI Importer Save-to-Cookbook Adapter Design](../docs/ai-importer-save-to-cookbook-adapter-design.md).
- Kept Vanilla Cookbook as the canonical recipe owner and placed future
  candidate translation and approved persistence at the core-app adapter
  boundary defined by `0031C`.
- Defined the future AI draft → review/edit → dry-run validation → explicit
  confirmation → Cookbook save → canonical recipe view flow.
- Documented the current `RecipeImportDraft` fields and separated conceptual
  mapping from the still-unknown upstream write schema.
- Required schema/compatibility discovery, strict validation, duplicate and
  idempotency protection, user confirmation, safe errors, backup/restore, and
  rollback evidence before any write implementation.
- Defined generated fixture, fake-adapter, disposable local runtime, and UI
  contract tests needed before implementation.
- Defined phases from docs/schema review through local dry-run and disposable
  write testing, with any reviewed production path deferred to a separate task.

## Local runtime relationship

The verified `cookbook-local` Docker runtime from `0033K`/`0033L` is the future
disposable target for schema discovery and synthetic write/rollback tests. It
is not a production integration target. No Vanilla Cookbook database was
mutated for this design task.

## Validation

This was a docs-only change. `git diff --check` and the repository validator
were run without live OpenAI calls, production credentials, database writes,
or external provider calls. No local database, upload, raw dataset, generated
index, prompt, provider output, secret, environment value, screenshot, trace,
or browser artifact was added.

## Explicit non-goals

No Save-to-Cookbook button, write endpoint, adapter runtime, production
write-back, direct database access, schema migration, authentication,
SSO/BYOS, analytics, ads, payment, AWS/platform work, provider routing/model
change, QMD integration, or live call was implemented.
