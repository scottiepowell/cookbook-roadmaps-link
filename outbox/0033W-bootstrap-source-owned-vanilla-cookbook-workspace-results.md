# 0033W Source-Owned Vanilla Cookbook Workspace Bootstrap Results

Status: complete; bootstrap and local configuration only.

## Provenance/license review

- Public upstream source: `https://github.com/jt196/vanilla-cookbook`.
- Upstream project license: GPL-3.0, from its public `LICENCE` file.
- Declared submodule: `https://github.com/jt196/recipe-ingredient-parser.git`.
- Submodule public README identifies MIT licensing.
- Local source pin: `7d94160e90368ed8ceb55b2dccfbbb5de1fb7b2c`.
- Local submodule pin: `6e8d1dff0c05f749b435c7e19b7f6627f60aa5d0`.
- All dependency/license notices still require review before redistribution;
  no source was copied into this repository.

## Workspace and image result

A recursive upstream checkout was created outside the sidecar repository in a
sibling local projects workspace. The checkout is clean and remains external.
The source built successfully after a retry as the local-only image
`local/vanilla-cookbook-adapter:0033w`. It was not pushed or deployed.

The first build wrapper timed out; the retry completed successfully. No
production target, tunnel, cloud service, secret, database, upload, or live AI
provider was used.

## Sidecar configuration

`docker-compose.local.yml` now accepts the optional
`VANILLA_COOKBOOK_IMAGE` value and still defaults to
`jt196/vanilla-cookbook:stable`. The local start script accepts only the
default tag or `local/vanilla-cookbook-adapter:*`, verifies an opted-in local
image exists, and keeps `cookbook-local`, loopback binding, ignored runtime
mounts, and app-only startup. Focused tests cover the selector boundary.

## Adapter boundary and next task

The first core-owned boundary is defined as an authenticated, no-mutation
dry-run service with reviewed candidate input, idempotency/duplicate checks,
safe errors, canonical field mapping, and no categories/media/remote images or
embeddings initially. The next recommended task is **0033X: implement that
core-owned local dry-run adapter in the separate source workspace**. Commit and
production integration remain later, separately approved work.

## Validation

- `git diff --check` passed.
- Repository/static validation passed.
- Default and local Compose config checks passed.
- Custom image build passed with the tag above.
- No live OpenAI call was made.

## Explicit non-goals

No external source was vendored or committed. No adapter, native route,
migration, auth/session work, public route, UI production button, deployment,
provider integration, production write, production data inspection, database,
upload, cookie, token, prompt, provider output, screenshot, trace, or browser
artifact was added.
