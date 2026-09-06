# 0035D Public AI Recipe Coherence Guard Results

## Result

Complete and deployed.

A deterministic pre-commit guard rejects high-confidence recipe revision
contradictions, including stale omelet directions under a pasta title and a
fried-rice draft without rice or frying actions. Guarded dish families also
require their named major protein to appear in the instructions. Rejection is
safe, retryable, and transactional.

## Safe outcomes

- Stale prior-dish instruction anchor rejected: yes.
- Missing pasta instruction/method anchor rejected: yes.
- Missing fried-rice instruction/method anchor rejected: yes.
- Unused guarded major protein rejected: yes.
- Coherent pasta and fried-rice fixtures accepted: yes.
- Prior draft and revision allowance preserved on rejection: yes.
- Public health: 200.
- Public core image: `local/vanilla-cookbook-adapter:0035d`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035d`.
- Sidecar health: healthy.

## Validation

- Focused sidecar recipe tests: 58 passed.
- Full sidecar tests: 468 passed.
- Offline evaluations: 39 passed.
- Focused core proxy/UI tests: 12 passed.
- Core production build: passed.
- Repository validator: passed all 7 checks.
- Compose configuration: valid.
- Core and sidecar image builds: passed.
- Public container startup: passed.
- Live/provider recipe generation: skipped; deterministic mock/offline coverage
  was sufficient and avoided consuming provider budget.

Existing build warnings about Browserslist age, CSS `@property`, and the
SvelteKit/Svelte export combination remain. Core startup also reports an
existing non-fatal permission warning while rewriting an unused `.svelte-kit`
service-worker copy; the built service worker is updated and the app reaches
healthy public service.

No prompt, recipe output, provider payload, identity data, credential, token,
cookie, session value, environment value, local path, browser artifact, or
ignored artifact is recorded here.

## Delivery

The external core changes are committed locally on
`openclaw/0035B-0035D-recipe-replacement-coherence` at
`811a25a2430af753f1bd80b33b2814b3216058c4`. The third-party upstream core
repository was not pushed. The mailbox, sidecar, tests, Compose pin, and
documentation are committed and pushed in `scottiepowell/cookbook-roadmaps-link`.
