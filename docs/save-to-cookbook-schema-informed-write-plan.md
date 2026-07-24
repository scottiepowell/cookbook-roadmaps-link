# Save-to-Cookbook Schema-Informed Write Plan

Status: proposed readiness plan; no-write implementation remains unapproved

Date: 2026-07-24

## Decision summary

The first disposable write test should be deliberately narrow: one synthetic
local user, one synthetic recipe, no categories, no photos/uploads, no
embeddings, and no imported local user or recipe data. The test should use the
native core-app ownership and transaction boundary only after a separately
approved local harness has created a backup/restore point and passed every
localhost guard.

This document plans that test. It does not implement a harness, button, commit
endpoint, database mutation, migration, or production integration. Vanilla
Cookbook remains the canonical owner, and the AI sidecar remains a candidate and
dry-run producer.

## Schema-informed decisions

0033O observed a Prisma/SQLite `Recipe` model with UUID `uid`, required
`userId`, required `created`, nullable text fields for `ingredients`,
`directions`, and `servings`, a `name` field rather than `title`, relational
categories, and a separate `RecipePhoto` model. The local app source also has
an authenticated `POST /api/recipe` create path and ownership-protected
update/delete paths. These are local observations, not production approval.

The core-owned adapter should use the following first-test mapping:

| Candidate field | First disposable mapping | Rationale and gate |
| --- | --- | --- |
| `title` | `Recipe.name` | Explicit upstream name/title translation; preserve the candidate contract name. |
| `description` | `Recipe.description` | Nullable direct field, bounded before write. |
| `servings` | `Recipe.servings = str(integer)` | Upstream is text; use a deterministic decimal string such as `4`, not a locale string. |
| `ingredients[]` | `Recipe.ingredients` plain text | Use deterministic one-line-per-ingredient serialization; confirm the normal editor can read it before accepting the result. |
| `instructions[]` | `Recipe.directions` numbered plain text | Use `1. ...\n2. ...`; preserve contiguous order and verify normal display. |
| `source` | `Recipe.source` only for a safe fixture label | Keep source label separate from URL; do not overload URL fields. |
| `source` URL | `Recipe.source_url` only after URL policy check | Use a fixed `https://example.invalid/...` fixture or approved harmless example; never send a remote-fetching image URL. |
| `notes` | `Recipe.notes` with bounded provenance label | Store only `Imported from AI draft; reviewed in disposable test.`; never provider text or prompt. |
| `tags` | Omit in first test | Categories require a synthetic ownership policy and relation transaction. |
| media/photo fields | Omit and send null/absent | Avoid `RecipePhoto`, remote image fetches, uploads, and cleanup ambiguity. |
| embeddings | Omit; ensure semantic work is disabled | Avoid BLOB/model writes and provider or background side effects. |
| `uid` | Core/Prisma UUID generation | The candidate must not provide a primary key. |
| `userId` | Synthetic core-owned user ID | Never accept identity from the AI draft or local user data. |
| `created` | Core-generated fixed test timestamp | The harness records a deterministic test timestamp or lets the core transaction assign it, according to the approved API contract. |

The exact ingredient and direction text format is still an implementation
compatibility question. The first harness must prove round-trip readability
through the normal local Cookbook path before the format is accepted. It must
not infer that the separate `Ingredient` catalog is the storage format for a
recipe's ingredient list.

## Serialization rules

The future core adapter should normalize each ingredient as:

```text
<quantity><space><unit><space><name><space>(<note>)
```

with empty components removed, whitespace collapsed, and one ingredient per
line. For example, a synthetic fixture could become `2 cups beans` and
`1 medium lemon`. This is a proposed deterministic fixture format, not a claim
about the upstream parser. The test must compare the exact serialized value
without exposing real recipe content.

Directions should be serialized as contiguous numbered lines:

```text
1. Warm the beans gently.
2. Add lemon and serve.
```

The core adapter must reject missing/empty steps and non-contiguous numbers
before any write. It should retain the candidate's structured form until the
last core-owned mapping step so dry-run and error messages remain structured.

Serving normalization should accept only the validated integer range already
defined by the importer contract, convert it to an invariant string, and
reject locale-specific or free-form values. The first test should use `4`.

## Source, provenance, categories, and media

The first fixture should use a non-sensitive source label and, if URL mapping
is explicitly tested, a safe fixture URL that cannot cause a remote fetch. A
source URL is provenance, not authorization to download content or images.

The notes field may contain only a bounded reviewed provenance label. Raw
prompts, provider bodies, citations as canonical content, model diagnostics,
keys, tokens, local paths, and user data are prohibited.

Categories are excluded from the first write. Although `Category` and
`RecipeCategory` are known, category ownership, reuse versus creation, naming
normalization, and rollback behavior are not yet proven. A later category test
must create a synthetic category owned by the synthetic user or use a reviewed
core helper and verify the join is removed on rollback.

Photos, image URLs, uploads, and embeddings are excluded. The native create
path can process remote images, create `RecipePhoto` records, write under
`uploads/images`, and regenerate embeddings. Those side effects make the
smallest first proof less deterministic and are not necessary to prove recipe
field persistence.

## Synthetic ownership fixture

The future harness must create a synthetic user only through the approved local
core-app setup/API or a disposable database fixture mechanism. It must never
read an existing user row, import a local account, copy an auth session, or
reuse a real email/username. Suggested properties:

- generated UUID ID owned by the harness/core app;
- clearly synthetic username in a reserved test form;
- no password, OAuth account, session token, email, or production identity;
- private/default visibility and no public profile;
- recorded only as a safe opaque test status/ID, not in committed output;
- deleted or restored with the database snapshot after the test.

The AI candidate must not include `userId`, auth headers, session identifiers,
or ownership assertions. The core app establishes ownership from the approved
local test context.

## Backup, restore, and cleanup plan

Before any future write, the harness must verify it is operating on the
`cookbook-local` Compose project and create a restorable snapshot of the
disposable database and uploads. The snapshot must be made outside tracked
paths or in a securely managed temporary location and must never be committed.

Required sequence:

1. Resolve and validate the local Compose project and localhost target.
2. Confirm the DB and upload mounts are the ignored `.local/vanilla-cookbook/`
   paths and that no production target/config is present.
3. Stop or quiesce the app as needed for a consistent copy; record only safe
   status metadata.
4. Back up the DB file and upload tree using a recoverable local mechanism;
   verify the backup exists and is non-empty without printing its path.
5. Start the local app and run exactly one synthetic candidate write.
6. Verify safe status, canonical ID shape, and normal read behavior.
7. Exercise duplicate/retry and approved failure cases.
8. Stop/quiesce the app, restore the DB and upload tree, and verify the
   pre-test state by schema/count/checksum metadata only.
9. Remove temporary backup material and confirm no test container/process is
   left running.

Restoration is the default success path, including after an assertion or
exception. If restoration fails, the harness must stop and report a safe
blocked status rather than retrying, deleting broad paths, or claiming
completion. Cleanup must remove only explicitly resolved paths under the local
runtime root; it must never target the repository root, a home directory, or a
production path.

## Transaction and cleanup expectations

The preferred core operation is one transaction covering the `Recipe` row and
any first-test related records. Since the first test excludes categories,
photos, uploads, and embeddings, the expected write set is only the synthetic
user/recipe fixture under the approved local core boundary. The harness must
prove that validation failure creates nothing and that a post-create failure
does not leave an orphaned recipe.

If the native API performs side effects outside its DB transaction, the future
adapter must use staging and compensating cleanup, or the test remains blocked.
No “best effort” success is acceptable. A successful response must be followed
by a normal read and ownership check; a failed response must be followed by a
safe absence/restore check.

## Duplicate and idempotency strategy

The first candidate fingerprint should be deterministic over normalized title,
ingredient names/quantities, and owner scope. The core adapter should compare
normalized `Recipe.name` plus the bounded ingredient fingerprint immediately
before commit. Because no unique recipe-name constraint was observed, the
application must provide the duplicate decision; a database uniqueness error
cannot be the only protection.

Every attempted write must carry an idempotency key derived from the candidate,
synthetic owner scope, contract version, and test run. A same-key/same-payload
retry must return the original canonical result or a safe idempotent replay;
same-key/different-payload must be a conflict and must not write. A different
key matching the duplicate fingerprint must return a reviewable duplicate
signal, not silently merge or overwrite.

## Failure-injection matrix

Before a future implementation is allowed beyond disposable testing, the
harness should exercise these cases with synthetic data only:

| Failure | Expected result |
| --- | --- |
| Missing/invalid title, ingredient, or step | No DB/upload side effect; field-level error |
| Unsupported schema/contract version | No write; safe compatibility error |
| Missing synthetic owner | No write; ownership error without identity leakage |
| Duplicate fingerprint | Reviewable duplicate result; no second recipe |
| Same idempotency key, same payload | Idempotent replay; no second recipe |
| Same key, changed payload | Safe conflict; no write |
| DB create failure | No orphan recipe; restore/absence verified |
| Related-record failure, if later enabled | Whole transaction rollback or compensating cleanup |
| Upload failure, if media later enabled | No orphan photo/file; first test avoids this path |
| Read-after-write failure | Treat as failed and restore; never report success |
| Timeout/interrupted harness | Restore in finally/cleanup path and report blocked if uncertain |
| Non-local target/configuration | Refuse before backup or write |

Failure messages must contain only safe categories and statuses. They must not
include SQL, stack traces, absolute paths, recipe bodies, prompts, provider
outputs, credentials, or session values.

## Local-only harness guardrails

The future `scripts/test-save-to-cookbook-local-write.ps1` is a design sketch,
not a file added here. It must:

- require an explicit approval switch and a clearly local test mode;
- require the `cookbook-local` Compose project and running app;
- require the target to resolve to `http://127.0.0.1:3000/` or an equally
  explicitly approved localhost form;
- refuse any `COOKBOOK_TARGET_URL` that is not localhost, including exposed
  Cookbook URLs, hostnames, tunnel URLs, and IPs other than loopback;
- refuse production `.env`, AWS, Cloudflare, GitHub Actions, or deployment
  configuration inputs;
- verify only the ignored local DB/upload mounts are in scope;
- create and verify a backup before any write;
- create/use only a synthetic user and perform exactly one synthetic recipe
  candidate write;
- verify normal local read behavior and safe canonical ID/status output;
- exercise duplicate/idempotency behavior without a second successful write;
- restore or clean the disposable DB/uploads before exit, including failures;
- print safe statuses only, never recipe private content, secrets, absolute
  local paths, prompts, provider output, or tokens.

The harness must not call the AI provider. It should consume a fixed synthetic
candidate or the already validated local dry-run result, and it must not be
reachable from a public route.

## Evidence gate for a future implementation task

A future disposable write task may start only when all evidence is attached to
that task and remains local/non-secret:

1. schema compatibility check confirms the version and field mapping;
2. exact ingredient/direction round-trip format is accepted by the normal UI;
3. synthetic ownership setup and teardown are proven;
4. backup/restore is tested on the intended disposable mounts;
5. one-write limit and localhost/Compose guards are tested, including refusal
   cases;
6. transaction, cleanup, duplicate, idempotency, and failure-injection tests
   pass;
7. no-media/no-embedding scope is confirmed for the first write;
8. mock/offline repository tests remain green without Docker or live OpenAI;
9. explicit approval identifies the exact local target and rollback owner.

Until then, Phase 3 is **blocked**, not ready. Schema discovery narrowed the
unknowns but did not authorize mutation.

## Explicit non-goals

This plan does not implement a write harness, Save-to-Cookbook button, commit
endpoint, public route, database mutation, migration, production write-back,
native API integration, authentication, SSO/BYOS, analytics, ads, payment,
AWS/platform work, provider routing/model change, QMD, or live provider call.
It does not create a user, recipe, backup, upload, snapshot, generated index,
or local runtime artifact. It does not inspect production data or commit
secrets, prompts, provider outputs, screenshots, traces, raw datasets, local
environment values, local DBs, uploads, or browser artifacts.
