# AI Importer Save-to-Cookbook Adapter Design

Status: Phase 2 dry-run contract complete; write implementation requires separate approval

Date: 2026-07-24

## Decision summary

The Vanilla Cookbook application remains the canonical owner of saved recipes.
The AI sidecar may produce a validated import candidate, but it must not write
to Cookbook-owned tables. A future Cookbook-side adapter will accept a bounded
candidate, run core-app validation, show the user a reviewable draft, and only
commit after explicit confirmation. The adapter belongs at the `0031C`
boundary:

```text
Vanilla Cookbook core app
        |
        | authorized, versioned adapter contract
        v
Cookbook AI Adapter
        |
        | bounded candidate request/response
        v
AI sidecar importer
```

Phase 1 now has a pure in-memory contract in
`ai-api/app/cookbook_import_adapter.py`. It adds no button, public endpoint,
database mutation, production integration, authentication flow, or live
provider call. The contract is deliberately not a claim about the upstream
Vanilla Cookbook write schema.

Phase 2 now wraps that contract with the internal service function
`dry_run_import_candidate_operation` in
`ai-api/app/cookbook_import_dry_run.py`. It is disabled unless the caller
explicitly passes the non-secret `enabled=True` gate and otherwise returns a
safe unavailable envelope. No HTTP route was added because the current app has
no authenticated core-app adapter boundary; adding a route would create a
public/exposure decision before that boundary is approved.

## Problem statement

`POST /ai/import-recipe` can turn rough recipe notes into a strict
`RecipeImportDraft`. The draft is useful but is not yet a saved Cookbook
recipe. Users need a safe path to review and edit that draft before deciding
whether it should become a canonical recipe in Vanilla Cookbook.

The local disposable runtime from `0033K`/`0033L` is now the correct place for
future schema discovery and write/rollback experiments. The exposed Cookbook
deployment and any production database remain out of scope until a separately
reviewed adapter path exists.

## Why direct sidecar database write-back is risky

The sidecar does not own Cookbook authorization, canonical IDs, revisions,
uploads, relationships, validation rules, or deletion semantics. Direct SQLite
access could therefore:

- bypass user ownership, authorization, CSRF/session, and tenancy checks;
- create rows that the Cookbook UI cannot render or later edit safely;
- mis-map JSON, text, or related ingredient/instruction records;
- violate required defaults, foreign keys, uniqueness, or audit behavior;
- partially write a recipe or upload and leave orphaned data;
- duplicate a recipe on retry or overwrite an existing recipe unexpectedly;
- expose private database paths, tokens, raw provider bodies, or unrelated rows;
- make schema upgrades an undocumented coupling between two applications.

The AI sidecar must never receive a writable database path or an unrestricted
database export. A database reader is not an import API.

## Preferred adapter boundary

The core Cookbook app should expose or internally implement an adapter contract
that it owns. The adapter translates a versioned, bounded candidate into the
native Cookbook create/edit transaction, using the same authorization and
validation rules as a normal user-created recipe. The sidecar supplies only
the candidate data and safe provenance summary; it does not choose a target
table, primary key, storage path, or production write mechanism.

Possible contract sketches, not routes added by this task:

```text
POST /adapter/recipes/import-candidate
POST /adapter/recipes/import-candidate/dry-run
POST /adapter/recipes/import-candidate/{candidate_id}/commit
GET  /adapter/recipes/{candidate_id}
```

The commit operation should be core-app-authenticated, scoped to the current
user/cookbook, idempotent, and versioned. A dry run should return field-level
validation errors, normalized mapping information, duplicate candidates, and
the intended write set without mutating a database or upload directory.

The adapter should use safe status/error envelopes. It may retain a short-lived
candidate identifier and a schema/contract version, but must not persist raw
prompts, provider response bodies, secrets, tokens, local paths, or hidden
environment values.

## Draft-to-Cookbook user flow

1. The user runs the AI importer with pasted notes.
2. The sidecar returns a schema-validated draft, warnings, citations, and a
   bounded provenance summary. The result is visibly labeled as an unsaved AI
   draft.
3. The user reviews and edits title, description, servings, ingredients,
   instructions, tags, source, and notes in an editable form.
4. The core app submits the edited candidate to the adapter dry-run.
5. The UI shows validation errors, normalization, and possible duplicates. It
   does not present a warning or citation as proof that the recipe is correct.
6. The user explicitly confirms `Save to Cookbook` after reviewing the dry-run.
7. The core app performs the authorized, transactional save and returns the
   canonical Cookbook recipe ID and a normal Cookbook URL/view.
8. On success, the UI says the recipe is saved and opens the canonical recipe.
   On failure, it reports a safe recovery message and does not claim success.

The user must be able to cancel, continue editing, or discard the candidate.
There must be no automatic save at the end of an AI generation request.

## Candidate validation and field mapping

Before a candidate can reach a future commit operation, validate all of the
following in both the sidecar contract and the core app:

- title is present, bounded, and safe to display;
- servings is an allowed positive integer or an explicitly supported unknown;
- at least one ingredient and one instruction are present;
- ingredient names are non-empty; quantity, unit, and notes are normalized;
- instruction order is contiguous, non-empty, and bounded in count/length;
- tags are bounded, deduplicated, and normalized without inventing sensitive
  claims;
- source is an optional user-supplied URL or label validated by core-app rules;
- notes are clearly separate from canonical instructions and do not contain
  provider diagnostics or hidden prompt text;
- unsafe, unsupported, or medically sensitive claims receive appropriate review
  handling and are never silently presented as verified facts;
- unknown fields are rejected or explicitly ignored, never guessed into a
  Cookbook column.

The current sidecar draft fields map conceptually as follows:

| AI draft field | Candidate meaning | Cookbook mapping status |
| --- | --- | --- |
| `title` | User-facing recipe name | Required; exact native field unknown |
| `description` | Optional short summary | Optional; confirm native field/length |
| `servings` | Yield/serving count | Optional or normalized to native yield field |
| `ingredients[]` | Name, quantity, unit, note | Requires schema and UI-format discovery |
| `instructions[]` | Ordered steps | Requires schema and ordering discovery |
| `tags[]` | Categories/labels | Optional; confirm controlled vocabulary behavior |
| `source` | User-provided source reference | Confirm URL/license/provenance policy |
| `notes` | Review/context note, not a provider transcript | Confirm whether a native notes field exists |

This mapping is intentionally not the upstream implementation schema.
`RecipeDocument` and `docs/ai-schema-notes.md` describe conservative read
fixtures only; they do not establish the upstream app's write schema. The
fixture adapter uses `cookbook-import.v1` and
`cookbook-recipe-candidate.v1` as explicit contract labels so a later schema
compatibility check cannot silently accept an unknown version.

## Unknown schema and discovery requirements

Before any write implementation, inspect a copy or disposable local runtime
and record only schema facts needed for the contract:

- actual recipe table/model names and primary-key generation;
- required columns, defaults, nullability, unique constraints, and foreign keys;
- whether ingredients and instructions are JSON, text, or related records;
- tag/category relationships and whether unknown tags are allowed;
- ownership, visibility, draft, archived, and deletion fields;
- revision/audit behavior and optimistic-concurrency requirements;
- image/upload references and whether an import may omit media;
- native create/edit API behavior, validation, and CSRF/session requirements;
- supported URL/deep-link format for the saved recipe.

Discovery must use the `cookbook-local` disposable runtime and synthetic
fixtures. Do not infer write behavior from the sidecar's read-only SQLite
reader, and do not inspect or modify production data. If the upstream app has a
supported API/plugin hook, prefer it over table-level access.

### 0033M discovery result

No upstream write schema was committed or inferred in this phase. The existing
repository notes expose only the conservative read-fixture shape, and the
verified local container layout provides the ignored disposable DB/upload
mounts but does not by itself establish the native create API, table names,
relations, or transaction behavior. Those facts remain required before Phase
3. Any future inspection must be read-only until a disposable backup/restore
procedure is approved; this task performed no local DB row writes.

## Duplicate detection and provenance

The core app should perform duplicate detection immediately before commit. A
first pass can use normalized title plus a bounded ingredient fingerprint and
owner scope, with an explicit review result rather than an automatic merge.
Existing canonical IDs, revisions, and user edits always win. Retries must use
an idempotency key bound to the candidate, user/cookbook scope, and contract
version; a repeated request must return the prior result or a safe conflict,
not create another recipe.

The saved recipe may retain a concise provenance label such as “Imported from
AI draft; reviewed by user” and an optional user-supplied source URL if the
Cookbook model supports it. Citations may be shown during review, but they are
not canonical recipe content. Do not store raw prompts, raw provider outputs,
retrieved bodies, provider headers, model debug traces, or secret-bearing
metadata as recipe fields.

## Confirmation, failure, and rollback

The commit must be a single core-app transaction where possible. Before any
future local write test, create a disposable backup or restore point and record
the schema/adapter version. The test must prove:

- validation failure produces no row, revision, upload, or side effect;
- duplicate/retry returns an idempotent result or safe conflict;
- a failure in a related ingredient, tag, revision, or upload operation rolls
  back the whole candidate and cleans up temporary files;
- the saved recipe can be read by the normal Cookbook UI;
- restore returns the disposable database to its pre-test state.

If the upstream application cannot provide an atomic transaction across its
database and uploads, the adapter must use a staged temporary record/file
strategy with compensating cleanup and must surface an explicit failure. There
is no “best effort” success message. Production write-back requires an
approved backup/restore procedure, observability, authorization review, and a
tested rollback runbook before go/no-go approval.

## Local fixtures and tests before implementation

Use generated in-memory objects and temporary SQLite databases only in tests;
do not commit a database or raw recipe dataset. Contract fixtures should cover
valid drafts, missing fields, long fields, duplicate ingredients, non-contiguous
steps, unknown fields, unsafe URLs, unsupported claims, duplicate candidates,
retries, schema-version mismatch, and safe errors.

Required test layers before a runtime adapter exists:

1. Sidecar schema tests prove importer drafts remain strict and contain no
   prompt/provider/debug fields.
2. Adapter contract tests use a fake Cookbook core service and assert dry-run
   mapping, field errors, authorization scope, idempotency, duplicate handling,
   and no-write behavior.
3. Local disposable integration tests run only against the local Docker
   runtime after schema discovery, with a backup/restore assertion and a
   synthetic recipe.
4. UI tests cover draft labeling, editability, confirmation, cancellation,
   validation errors, unavailable Cookbook recovery, and success deep-linking.
5. Regression checks prove mock/offline validation remains deterministic and no
   normal test invokes a live provider or production target.

## Phased implementation plan

### Phase 0: Design and schema review

This task. Freeze ownership, candidate fields, unknowns, safety gates, error
semantics, and test fixtures. No endpoint, UI control, or write occurs.

### Phase 1: Local fixture adapter contract

Complete in this task. `FakeCookbookAdapter` and
`map_import_draft_to_candidate` use generated/in-memory fixtures only. They
return mapped payloads, field errors, bounded warnings, duplicate candidates,
schema/contract versions, and idempotency replay/conflict metadata. There is
no route, network client, database handle, production target, or persistence.

### Phase 2: Dry-run candidate operation

Complete in this task as an internal service operation. It reports mapping,
compatibility, duplicate candidates, idempotency replay/conflict metadata, and
safe errors while never writing. It is not a public route and has no commit
counterpart. A future HTTP surface requires a separately approved local/auth
and exposure design.

### Phase 3: Disposable local write/rollback test

After schema detection, implement a local-only adapter against the disposable
Vanilla Cookbook runtime. Take a backup/restore point, write synthetic data,
verify normal reads/UI behavior, exercise failure and retry paths, then restore
or delete all disposable data. No production target is accepted.

### Phase 4: Local-only review UI

Enable a Save-to-Cookbook control only for an explicitly identified disposable
local target. Require review, edit, dry-run, and confirmation. Keep the control
hidden or unavailable for exposed/production targets until separately approved.

### Phase 5: Reviewed production path

Only after security, authorization, schema compatibility, idempotency,
backup/rollback, support, and user-facing acceptance reviews may the project
choose a core-app API/plugin integration. A reviewed production adapter task
must explicitly approve scope, deployment, monitoring, and rollback; direct AI
sidecar database writes remain prohibited.

## Safety gates and go/no-go criteria

No implementation proceeds past a gate unless all applicable evidence exists:

- no production write-back without explicit approval;
- disposable/local DB test completed before any real Cookbook mutation;
- backup or restore point verified before local write testing;
- schema detection and compatibility check pass;
- strict draft and core-app validation pass;
- user review and explicit confirmation are required;
- idempotency and duplicate protection are tested;
- failures produce safe errors and no false success;
- raw provider output is not stored as canonical recipe data;
- prompts, provider bodies, secrets, local paths, and tokens are never stored
  or exposed;
- authorization and ownership are enforced by the core app, not inferred by
  the sidecar;
- mock/offline regression remains green and live providers are not required.

Go means the candidate contract and disposable rollback evidence pass review.
No-go means schema is unknown, the core app lacks an authorized create path,
rollback is unproven, duplicate behavior is ambiguous, or the only available
integration is direct sidecar database access.

## Explicit non-goals

This design does not implement:

- a Save-to-Cookbook button, UI, endpoint, adapter runtime, or production
  integration;
- direct reads or writes to the Vanilla Cookbook database;
- production write-back, API credentials, auth, SSO/BYOS, or public routes;
- schema migrations, upload handling, image generation, or recipe ownership
  changes;
- AI provider routing, new model support, token-cap changes, QMD, analytics,
  ads, monetization, payment, AWS, Cloudflare, or platform work;
- live OpenAI calls, production data inspection, committed local databases,
  uploads, raw datasets, generated indexes, prompts, provider outputs,
  screenshots, traces, secrets, or local environment values.

## Relationship to 0031C and current validation

This design specializes the `0031C` recipe read/write boundary: the core app
owns canonical persistence and authorization, the adapter translates a bounded
candidate, and the sidecar remains an AI capability provider. The local
`cookbook-local` Compose runtime from `0033K`/`0033L` is the future disposable
test target, not a production dependency. Normal repository validation remains
static, mock, and offline.

The Phase 1 contract tests cover valid mapping, missing/blank fields,
non-contiguous steps, bounded long fields, unknown fields, unsafe URLs,
duplicate candidates, idempotent replay, key reuse conflicts, schema mismatch,
and safe-envelope leakage checks. They run without Docker or provider keys.

The Phase 2 operation tests additionally cover the disabled gate, delegation to
the fixture adapter, operation-level versions/errors/warnings, duplicate and
idempotent results, schema mismatch, and no-write/safe-envelope behavior.
