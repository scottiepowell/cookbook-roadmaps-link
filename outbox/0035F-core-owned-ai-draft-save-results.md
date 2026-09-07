# 0035F Core-Owned AI Draft Save Results

## Result

Complete and deployed.

The authenticated AI recipe page now presents an explicit Save to Cookbook
action for a complete draft. The browser maps the structured draft into the
existing core recipe shape and submits it through the canonical authenticated
recipe-create route. The core assigns ownership and applies the user's existing
public-recipe default. Successful creation discards the transient AI chat and
opens the normal saved-recipe view.

Save failure leaves the visible draft, conversation, and ten-change count
intact. The button remains disabled while generation or saving is active, and
incomplete drafts cannot be submitted.

## Safe outcomes

- Complete AI draft became explicitly savable: yes.
- Canonical authenticated core create route used: yes.
- Core retained user and persistence ownership: yes.
- User public-recipe default applied: yes.
- Duplicate click guarded during save: yes.
- Failure path preserves draft and change count: yes.
- Successful save cleared the transient chat: yes.
- Canonical recipe view opened after save: yes.
- Saved title, ingredients, and directions visible: yes.
- Automatic draft saving introduced: no.
- Sidecar database or identity/session ownership introduced: no.
- Public health: 200.
- Public core image: `local/vanilla-cookbook-adapter:0035f`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035d`.

## Validation

- Focused core draft mapping, page wiring, entry, and AI proxy tests: 19 passed.
- Core production Docker build: passed.
- Sidecar repository validator: 468 passed.
- Offline evaluations: 39 passed.
- Compose configuration and diff checks: passed.
- Public container startup and HTTPS health: passed.
- Signed-in browser verification: one live draft saved once and redirected to
  its canonical recipe page with mapped content present.

The live draft generation recovered on its final allowed bounded retry before
the save test; no duplicate provider request was issued by the verifier.
Existing build warnings about Browserslist age, CSS `@property`, and the
SvelteKit/Svelte export combination remain. Core startup also reports the
existing non-fatal permission warning while rewriting an unused `.svelte-kit`
service-worker copy; public health reaches 200.

No prompt, provider output, identity data, credential, token, cookie, session
value, environment value, database path, or browser artifact is recorded or
staged.

## Delivery

The external core change is committed locally on
`openclaw/0035F-save-ai-recipe` at
`bc6eb524093773b3a2122981869495d5ee00384f`. The third-party upstream core
repository is not pushed. The 0035F mailbox, documentation, Compose pin, and
safe results are committed and pushed in `scottiepowell/cookbook-roadmaps-link`.
