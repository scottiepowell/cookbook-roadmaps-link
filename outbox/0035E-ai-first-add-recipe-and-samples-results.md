# 0035E AI-First Add Recipe and Samples Results

## Result

Complete and deployed.

The authenticated New Recipe navigation and empty-cookbook action now open the
core AI recipe chat as the default Add Recipe experience. The duplicate AI
navigation action was removed. A visible Manual entry action opens the complete
existing `/recipe/new` form, while direct and bookmarklet manual-import paths
remain unchanged.

The opt-in sample catalog now contains five complete recipes. Two original
Cookbook samples were added, and sample seeding is user-scoped and idempotent.
The current public cookbook seed created five missing samples with zero
failures; an immediate replay created zero, skipped all five, and had zero
failures.

## Safe outcomes

- Primary Add Recipe destination is AI-first: yes.
- Duplicate AI navigation action removed: yes.
- Complete manual entry remains available: yes.
- Bookmarklet/manual route preserved: yes.
- Five sample recipes visible in the signed-in public homepage: yes.
- Seed replay is idempotent: yes.
- Automatic AI-draft saving introduced: no.
- Public health: 200.
- Public core image: `local/vanilla-cookbook-adapter:0035e`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035d`.
- Sidecar health: healthy.

## Validation

- Focused core navigation, seed, and AI proxy tests: 15 passed.
- Core production Docker build: passed.
- Sidecar repository validator: 468 passed.
- Offline evaluations: 39 passed.
- Compose configuration: valid with ignored public env prerequisites present.
- Public container startup and HTTPS health: passed.
- Signed-in browser verification: five recipe cards visible; New Recipe opened
  the AI Add Recipe screen; Manual entry opened the full recipe form.
- Live/provider recipe generation: skipped; this task did not require an LLM
  call.

The broader upstream core suite recorded 683 passes, 3 skips, and 7 unrelated
baseline failures in legacy parser, conversion-fixture, and local commit-route
tests. The focused changed surfaces and production build passed.

Existing build warnings about Browserslist age, CSS `@property`, and the
SvelteKit/Svelte export combination remain. Core startup also reports the
existing non-fatal permission warning while rewriting an unused `.svelte-kit`
service-worker copy; the built service worker is updated and public health
reaches 200.

No provider prompt, provider output, identity data, credential, token, cookie,
session value, environment value, database path, browser artifact, or ignored
artifact is recorded or staged.

## Delivery

The external core changes are committed locally on
`openclaw/0035E-ai-first-add-recipe` at
`03a89116f0cd6373a5ead13c6bb9c9aa04d65a13`. The third-party upstream core
repository was not pushed. The 0035E mailbox, documentation, Compose pin, and
safe results are committed and pushed in
`scottiepowell/cookbook-roadmaps-link`.
