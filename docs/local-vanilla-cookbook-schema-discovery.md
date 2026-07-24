# Local Vanilla Cookbook Schema Discovery

Status: complete, read-only discovery; Phase 3 write/rollback testing remains blocked

Date: 2026-07-24

## Scope and method

This report records read-only inspection of the disposable local runtime from
`docker-compose.local.yml` using the repository start/check/stop scripts. The
runtime used image `jt196/vanilla-cookbook:stable` under the `cookbook-local`
Compose project and bound only to `127.0.0.1:3000`.

The inspection used container status, image/entrypoint and bind-mount metadata;
filenames inside `/app`; `/app/prisma/schema.prisma` read-only; SQLite metadata
through a `mode=ro` connection with `PRAGMA query_only=ON`; and local source
route files for recipe create/update shape.

No row contents, recipe text, user records, tokens, environment values, or
uploads were read. No SQL write, migration, HTTP create/update request, upload,
or synthetic recipe operation was performed. The local container was stopped
after discovery. Disposable files remain under ignored relative paths
`.local/vanilla-cookbook/db` and `.local/vanilla-cookbook/uploads` and are not
committed.

## Confidence labels

- **Observed fact**: directly present in local Prisma schema, SQLite metadata,
  container metadata, or route source inspected.
- **Inference**: bounded interpretation useful for adapter planning, not a
  guarantee of runtime behavior.
- **Unknown**: not established by this read-only inspection.
- **Not inspected**: deliberately omitted to avoid reading rows, secrets, or
  unnecessary application data.

## Runtime and app metadata

| Item | Result | Confidence |
| --- | --- | --- |
| Docker/runtime | Docker Desktop Linux engine available; repo start/check succeeded | Observed fact |
| Compose project | `cookbook-local` | Observed fact |
| Service | Only `app` started; no `cloudflared` service | Observed fact |
| Image | `jt196/vanilla-cookbook:stable` | Observed fact |
| Binding | `127.0.0.1:3000 -> 3000` | Observed fact |
| Readiness | `http://127.0.0.1:3000/` returned HTTP 200 | Observed fact |
| Entrypoint | `/app/scripts/docker/entrypoint.sh` | Observed fact |
| App metadata | Prisma schema/migrations and SvelteKit route tree present | Observed fact |
| Local DB | `/app/prisma/db/dev.sqlite`, mounted from ignored `.local/vanilla-cookbook/db/dev.sqlite` | Observed fact |
| Upload roots | `/app/uploads/images` and `/app/uploads/imports` existed under ignored upload mount | Observed fact |

The local DB was inspected only through read-only schema metadata. Its row
contents, users, recipes, uploads, and migration history contents are not part
of this report.

## Prisma and SQLite schema facts

### Recipe model

The local Prisma model is `Recipe`, backed by SQLite table `Recipe`:

- `uid` is a required `String` primary key with Prisma `@default(uuid())`;
- `userId` is required and references `auth_user.id` with cascade behavior;
- `created` is required `DateTime` with no schema default shown;
- `name`, `description`, `source`, `source_url`, `notes`, timing fields,
  `servings`, and nutrition fields are nullable unless otherwise stated;
- `ingredients` and `directions` are nullable `TEXT`, with corresponding
  `ingredients_original` and `directions_original` text fields;
- state fields include `is_public`, `in_trash`, `is_pinned`, `on_favorites`,
  and `on_grocery_list`, with Prisma defaults shown for some;
- `embedding` is nullable `BLOB`; `embeddingModel` is nullable text and
  `embeddingVersion` is required with default `0`;
- no unique constraint on recipe name/title was observed;
- the inspected Recipe metadata showed the primary-key index but no separate
  `userId` index.

**Inference:** the 0033M/0033N candidate `title` must map to canonical
`name`, and `servings` must be converted from an integer to the upstream string
representation. A future core adapter must supply an authorized `userId` and
`created` value; those cannot come from the AI sidecar candidate.

### Related recipe models

- `RecipePhoto` has UUID `id`, required `recipeUid`, optional `url`, `fileType`,
  `notes`, and required `isMain` defaulting false. It cascades from `Recipe`.
- `Category` has UUID `uid`, required `userId`, optional name/parent/order
  fields, and a self-relation for parent/children.
- `RecipeCategory` is a many-to-many join with required `recipeUid` and
  `categoryUid`, composite primary key, and cascade foreign keys.
- `RecipeLog`, `RecipeFavorite`, and `ShoppingListItem` reference recipes and
  users; these are downstream behavior, not import candidate fields.
- `AuthUser` is mapped to `auth_user`; its ID is a UUID primary key and
  username/email have unique indexes. Ownership is a core-app concern.
- `Ingredient` is a separate catalog table with autoincrement integer ID,
  unique name, and required nutrition conversion fields. It is not a direct
  foreign-key relation from `Recipe` in the inspected Prisma model.

### Other observed tables and metadata

SQLite contained `Category`, `Ingredient`, `PurchaseLog`, `Recipe`,
`RecipeCategory`, `RecipeFavorite`, `RecipeLog`, `RecipePhoto`,
`ShoppingListItem`, `SiteSettings`, `auth_account`, `auth_key`,
`auth_session`, `auth_user`, and Prisma migration bookkeeping tables.

No triggers or views were observed. Migration files and Prisma schema were
read only and were not executed or modified.

## Candidate mapping impact

| 0033M/0033N candidate | Local upstream fact | Adapter implication |
| --- | --- | --- |
| `title` | Recipe field is `name` | Add approved core-side mapping; do not silently rename the fixture contract |
| `description` | Nullable `description` exists | Likely direct mapping, subject to native validation |
| `servings` integer | Recipe `servings` is nullable `TEXT` | Core adapter must normalize/display format explicitly |
| `ingredients[]` objects | Recipe has nullable `TEXT` `ingredients` | Serialization/parser format remains unknown; do not join catalog `Ingredient` automatically |
| `instructions[]` | Recipe has nullable `TEXT` `directions` | Ordered-step serialization remains unknown |
| `tags[]` | Categories are a user-owned relational join | Requires category ownership, create/reuse, and transaction policy |
| `source` | Nullable `source` and `source_url` exist | Distinguish label from URL; core validation selects field |
| `notes` | Nullable `notes` exists | Likely direct mapping, subject to user-visible semantics |
| provenance/media | `photo`, `photo_url`, `image_url`, `RecipePhoto`, uploads exist | Omit media in first candidate unless separately approved and tested |
| owner/identity | required `userId` FK and auth tables | Supplied by core authorization, never by AI candidate |
| ID/time | UUID `uid`; required `created` | Core app generates/assigns them transactionally |

The existing fixture payload is directionally useful but not write ready. It
lacks owner identity, canonical name conversion, string servings normalization,
ingredient/direction serialization, and category policy. The adapter contract
remains schema-neutral until the core app defines these mappings.

## Native create/edit path

The local source tree contains an authenticated native recipe API:

- `POST /api/recipe` requires `requireAuth`, accepts multipart form data with a
  JSON `recipe` field, and calls `prisma.recipe.create` with `userId` and
  `created` supplied by the core app;
- the create path can process remote image URLs and uploaded images, create
  `RecipePhoto` records, write under `uploads/images`, and optionally
  regenerate embeddings;
- `PUT /api/recipe/{uid}` requires authentication and ownership and applies an
  allowlist of editable fields;
- `DELETE /api/recipe/{uid}` requires authentication and ownership and removes
  related photos/files according to app behavior.

These are observed local source facts, not authorization for the AI sidecar.
No route was called. The create route is not a safe dry-run endpoint because it
mutates the DB and may touch remote images, uploads, and semantic processing.
A future adapter should use a reviewed core-app service or native API with
explicit dry-run support, not call this route from the sidecar directly.

## Known unknowns and not-inspected areas

- exact serialization format for `ingredients`, `directions`, and original
  fields;
- native parser/editor normalization and validation rules;
- whether category names are reused, created, or restricted per user;
- complete required/default behavior across Prisma/client/runtime versions;
- transaction boundary across recipe, categories, photos, uploads, and
  embedding work;
- canonical user/session handoff and adapter authorization mechanism;
- duplicate semantics beyond the absence of a recipe-name unique constraint;
- revision/history behavior for imported recipes;
- whether `hash` has application-level duplicate meaning;
- native deep-link format and success response expectations;
- whether media is optional for every create workflow;
- current local row state, recipe contents, user contents, upload contents,
  logs, and migration history beyond filenames/schema metadata.

## Phase 3 readiness

Phase 3 disposable write/rollback testing is **partially informed but blocked**.
The real model, ownership relation, required fields, related tables, and native
authenticated create/update/delete paths are now known. It remains blocked
until a separate task defines and tests:

1. core-owned mapping for name, servings, ingredient/direction serialization,
   categories, source fields, and provenance;
2. a synthetic user/ownership fixture without reading or importing local user
   data;
3. a backup/restore point and transaction/cleanup plan covering DB and uploads;
4. duplicate/idempotency and failure-injection behavior;
5. a local-only approved write harness that cannot target production.

No schema migration is required or proposed by this discovery task. The
0033M/0033N fixture and dry-run contracts remain no-write and unchanged.

## Explicit non-goals

This report does not add a Save-to-Cookbook button, public route, commit
endpoint, database write, migration, production integration, auth, SSO/BYOS,
analytics, ads, payment, AWS/platform work, provider routing/model change, QMD,
or live provider call. It does not commit a DB file, upload, row data, raw
recipe content, secret, prompt, provider output, screenshot, trace, raw
dataset, generated index, local environment value, or browser artifact.
