# 0035E AI-First Add Recipe and Samples

## Goal

Make the core Cookbook Add Recipe entry point AI-first while retaining the
complete existing manual recipe form as an explicit alternative, and populate
the sample seed with five realistic recipes.

## Required behavior

- Route the authenticated navigation's Add Recipe action to the existing
  core-owned AI recipe chat.
- Route the empty-cookbook Add Recipe action to the same AI-first experience.
- Remove the duplicate standalone AI navigation action.
- Present a clear Manual entry action on the AI page that opens the existing
  full recipe form, including URL/text/image import and manual fields.
- Preserve direct `/recipe/new` and bookmarklet behavior.
- Expand the existing opt-in sample seed from three recipes to five with two
  original, complete sample recipes.
- Make repeated sample seeding idempotent for a user so an existing public
  cookbook can safely receive only missing samples.
- Populate the current public admin cookbook with the missing samples and
  report only safe created/skipped/failed counts.

## Boundaries

- Core retains recipe, user, session, and save ownership.
- AI output remains a reviewable draft and is not automatically saved.
- Do not place canonical recipe records in the sidecar.
- Do not expose identity data, recipe-session content, credentials, tokens,
  cookies, local environment values, or database paths.
- Do not alter the existing bookmarklet/manual import destination.

## Validation

- Add focused navigation, manual-fallback, sample-count, and idempotency tests.
- Run the existing core AI proxy tests and core production build.
- Run the sidecar repository validator and Compose configuration check.
- Build and deploy the pinned public core image, seed safe sample counts, and
  verify public health and the signed-in browser experience.
