# 0035K Editable AI Draft Review Before Save Results

## Result

Complete and deployed. The public core AI page now provides an explicit draft
editing mode for recipe metadata, ingredients, and instructions. Local edits do
not call the provider or save automatically.

## Implementation

- Title, description, and servings are editable.
- Ingredient quantity, unit, name, and note are editable; rows can be added or
  removed.
- Instruction text is editable; rows can be added or removed and are resequenced.
- Core validation requires a title, whole-number servings from 1 through 24, a
  named ingredient, and a non-empty instruction before Save.
- The existing authenticated core recipe-create path saves the reviewed draft.

## Safe validation outcomes

- Focused core draft, public proxy, and AI-entry tests: 25 passed.
- Svelte diagnostics: 0 errors and 0 warnings.
- Core production image build: passed.
- Public Compose configuration: passed.
- Public core and sidecar containers: running; sidecar healthy.
- Public HTTPS health: HTTP 200.
- Sidecar source and provider behavior: unchanged.

## Delivery

- Public core image: `local/vanilla-cookbook-adapter:0035k`.
- Public sidecar image: `local/cookbook-ai-sidecar:0035i`.
- External core branch: `openclaw/0035K-editable-ai-draft-review`.
- External core commit: `1df0c674e29e790048a03f623d6f1477ed77a68e`.
- Mailbox task commit: `622ebc0`.
- Sidecar delivery commit: `0e0e24e65063879646994ab4a3387293fb860a32`.

No live provider request or signed-in recipe mutation was performed. No
secrets, prompts, raw provider output, cookies, tokens, session values, browser
artifacts, local private env values, database paths, or ignored runtime files
were staged.
