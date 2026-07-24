# 0033O Local Vanilla Cookbook Schema Discovery Results

## Runtime and method

- Docker Desktop was available.
- The repository start/check scripts started `cookbook-local` with only the
  `app` service; no `cloudflared` container ran.
- `http://127.0.0.1:3000/` returned HTTP 200.
- Discovery inspected container metadata, image filesystem filenames,
  `/app/prisma/schema.prisma`, SQLite metadata through a read-only
  `mode=ro`/`query_only` connection, and local recipe route source.
- The runtime was stopped afterward. No rows, uploads, secrets, user data, or
  recipe contents were read or modified.

## Facts discovered

- Local DB: ignored relative path `.local/vanilla-cookbook/db/dev.sqlite`.
- Prisma/SQLite `Recipe` has UUID `uid`, required `userId` and `created`,
  nullable text `ingredients`, `directions`, and `servings`, plus name,
  description, source/source URL, notes, state, and timing fields.
- `RecipePhoto` is a separate relation; `Category`/`RecipeCategory` provide
  user-owned relational categories; auth ownership is through `auth_user`.
- The local app source contains authenticated `POST /api/recipe` create and
  ownership-protected update/delete routes. Create may write photos/uploads and
  trigger embedding work, so no route was called.

## Impact and readiness

The 0033M/0033N candidate is directionally useful but not write-ready. A
future core adapter must map title→name, normalize integer servings to text,
define ingredient/direction serialization, handle category ownership, supply
user identity and created time, and explicitly exclude or separately approve
media/embedding behavior.

Phase 3 disposable write/rollback testing is **partially informed but blocked**
until those mappings, synthetic ownership fixtures, DB/upload backup/restore,
transaction cleanup, duplicate/idempotency, and failure-injection plans are
approved. Exact serialization and runtime semantics remain unknown.

## Validation and non-goals

Validation remained mock/offline: env-loader checks, offline evals, full pytest,
repository validation, Compose config, mock demo, and diff checks were run or
scheduled with no live OpenAI call. No schema snapshot, DB file, upload, row
data, migration, route, button, commit operation, production integration,
auth, SSO/BYOS, analytics, ads, payment, AWS/platform work, provider change,
QMD, secret, prompt, provider output, screenshot, trace, raw dataset, local
environment value, or browser artifact was committed.
