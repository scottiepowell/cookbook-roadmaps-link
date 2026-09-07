# 0035F Core-Owned AI Draft Save

## Goal

Let an authenticated user explicitly save a complete, reviewed AI recipe draft
into their Cookbook through the core's canonical recipe-create boundary.

## Required behavior

- Show Save to Cookbook only after the AI conversation has a complete draft.
- Map the structured draft into the existing canonical recipe shape.
- Submit through the authenticated core `/api/recipe` flow so the core assigns
  ownership and performs the existing create behavior.
- Respect the authenticated user's default public-recipe preference.
- Disable duplicate submissions while a save is active.
- Preserve the visible draft and change count when saving fails.
- On success, discard the transient AI chat and open the canonical saved-recipe
  view, where the user can review or edit the recipe normally.

## Boundaries

- Saving is explicit; drafts are never saved automatically.
- The sidecar does not receive database access or recipe/session ownership.
- The canonical core remains authoritative for authentication and persistence.
- Do not persist or publish prompts, provider output, identity data, credentials,
  tokens, cookies, session values, local environment values, or browser artifacts.

## Validation

- Add focused mapping, completeness, and page-wiring tests.
- Run the existing AI chat proxy regressions and the core production build.
- Run sidecar repository validation, Compose validation, and diff checks.
- Deploy a pinned public core image and verify one authenticated browser save
  reaches the canonical recipe view.
