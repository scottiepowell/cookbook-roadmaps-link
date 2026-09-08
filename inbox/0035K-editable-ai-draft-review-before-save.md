# 0035K Editable AI Draft Review Before Save

## Goal

Let authenticated users edit a generated AI recipe draft directly in the core
review surface before explicitly saving it to Cookbook.

## Required behavior

- Add an explicit Edit draft / Done editing control.
- Support local editing of title, description, servings, ingredient quantity,
  unit, name and note, and instruction text.
- Allow ingredient and instruction rows to be added or removed.
- Validate required title, positive whole-number servings, at least one named
  ingredient, and at least one non-empty instruction before Save.
- Save the edited draft through the existing authenticated core recipe-create
  path; do not invoke the provider for local edits.
- Preserve the current AI conversation and explicit Save semantics. Nothing is
  saved automatically.

## Boundaries

Core owns the UI, authentication, validation, and canonical write. Do not give
the sidecar database, cookie, identity, OAuth, session, or direct write access.
Do not alter grounding, retries, replacement confirmation, recipe scaling, or
provider behavior. Do not log or commit private prompts, outputs, credentials,
tokens, cookies, browser artifacts, env values, database paths, or runtime data.

## Validation

Run focused core draft/page tests, Svelte checks, the core production build,
sidecar repository validation as applicable, Compose validation, image builds,
and public health checks. Record safe results in the matching outbox file.
