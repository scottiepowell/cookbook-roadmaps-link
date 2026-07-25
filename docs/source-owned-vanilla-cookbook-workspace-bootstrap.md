# Source-Owned Vanilla Cookbook Workspace Bootstrap

Status: workspace/image bootstrap complete; adapter implementation remains
future work.

Date: 2026-07-25

## Provenance and license review

The repository's existing runtime uses the external
`jt196/vanilla-cookbook:stable` image. No upstream source was added to this
repository.

Web-current upstream facts:

- The source repository is [jt196/vanilla-cookbook](https://github.com/jt196/vanilla-cookbook).
- The repository identifies a GPL-3.0 license and stores the text in
  [`LICENCE`](https://github.com/jt196/vanilla-cookbook/blob/main/LICENCE).
- The source declares a recursive `recipe-ingredient-parser` submodule in
  [`.gitmodules`](https://github.com/jt196/vanilla-cookbook/blob/main/.gitmodules).
  The parser repository identifies its own license as MIT in its
  [README](https://github.com/jt196/recipe-ingredient-parser).
- The upstream [installation documentation](https://vanilla-cookbook.readthedocs.io/en/stable/manual/installation/)
  documents both the Docker image workflow and recursive source checkout.
- The upstream Docker Compose template uses a single app container, mounted
  database/uploads, and the `jt196/vanilla-cookbook` image; this repository
  retains its safer localhost-only compose variant.

Local bootstrap facts:

- A recursive checkout was created outside this repository using the public
  source URL.
- The local source pin is commit `7d94160e90368ed8ceb55b2dccfbbb5de1fb7b2c`.
- The checked-out parser submodule pin is
  `6e8d1dff0c05f749b435c7e19b7f6627f60aa5d0`.
- The external workspace is intentionally not named or tracked as a path in
  committed code. Operators should use a sibling project workspace such as
  `C:\Users\scott\projects\vanilla-cookbook-core` locally, or an equivalent
  path outside this repository.
- The checkout had a clean branch status at bootstrap time. Upstream sync and
  any future adapter changes need their own review and commit policy.

The GPL-3.0 and MIT findings are provenance facts, not a complete legal review
of every dependency or future redistribution. Before publishing a fork or
image, review all dependency licenses, retain required notices, and record the
source commit used for the image.

## Custom image result

The source checkout was built locally as:

```text
local/vanilla-cookbook-adapter:0033w
```

The image was not pushed, published, or used for production. The first build
timed out at the command wrapper; a retry completed successfully. The image is
only a source-owned-workspace bootstrap artifact and contains no adapter code
yet.

The sidecar repository's default local runtime remains
`jt196/vanilla-cookbook:stable`. The optional local selector accepts either the
default image or a tag in the `local/vanilla-cookbook-adapter:*` namespace:

```powershell
# Default external-image workflow remains unchanged
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1

# Opt-in local custom image, after it exists locally
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 `
  -CookbookImage local/vanilla-cookbook-adapter:0033w
```

The start script verifies the custom tag exists locally and rejects arbitrary
or exposed image namespaces. Both modes use the `cookbook-local` Compose
project, bind only `127.0.0.1:3000`, use ignored `.local/vanilla-cookbook/db`
and `.local/vanilla-cookbook/uploads` paths, and start only the `app` service.
Cloudflare, AWS, GitHub Actions, production `.env`, and production URLs are
not part of this path.

## First core adapter boundary

No adapter was implemented in this task. The first future core-owned change in
the separate workspace should be a narrow authenticated dry-run service or
internal endpoint with:

- ownership derived from the core app's current authenticated user;
- reviewed candidate input and explicit contract version;
- no mutation during dry-run;
- accepted idempotency key and duplicate fingerprint checks;
- safe field errors and warnings;
- canonical mapping for name, description, servings, ingredients, directions,
  source, and bounded provenance notes;
- no categories, media/uploads, remote image fetching, or embeddings in the
  first scope;
- commit deferred until dry-run and core transaction tests pass.

The sidecar must never provide `userId`, session, cookie, token, or ownership
assertions. The core app must own validation, transaction/rollback, canonical
recipe persistence, and the final recipe UID/URL.

## Local validation and recovery

Run the core source build and core tests in the separate workspace. Then use
this repository's offline tests, mock demo, and Compose config checks. Do not
run live OpenAI or expose the custom image.

If bootstrap must be repeated:

1. Use a new or clean sibling checkout outside this repository.
2. Clone with recursive submodules from the public upstream URL.
3. Record the exact source and submodule pins before building.
4. Build a new `local/vanilla-cookbook-adapter:<pin-or-task>` tag without
   pushing it.
5. Stop and remove only the disposable `cookbook-local` runtime when finished;
   preserve or restore ignored database/uploads according to the approved
   readiness harness.

Do not copy the checkout, Docker build context, database, uploads, or generated
artifacts into this repository.

## Next task

0033X completed authenticated-context dry-run mapping, validation, idempotency,
and core tests in the separate workspace. 0033Y then added the authenticated
dry-run route and built the opt-in `0033y` image; recommend a subsequent task
to review and design the authenticated core commit boundary before any commit
mutation. Production Save-to-Cookbook remains unimplemented.

## Explicit non-goals

This bootstrap adds no Save-to-Cookbook adapter, native route, migration,
auth/session integration, UI production button, public route, production
deployment, provider integration, database mutation, analytics, ads, payment,
AWS, Cloudflare, GitHub Actions, QMD, or live call. No upstream source,
license file, source archive, container snapshot, local DB, upload, cookie,
token, prompt, provider output, or browser artifact was committed here.
