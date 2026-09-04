# 0034W - Initial Recipe Ingredient Fidelity

## Trigger

A public recipe-session request named chicken, cauliflower, and cheese, but the
initial generated draft omitted cauliflower. A later explicit follow-up added
riced cauliflower successfully.

## Goal

Ensure the initial recipe-session generation receives the complete bounded user
request instead of a lossy reconstructed requirements summary.

## Required behavior

- Pass the original initial request text to the importer/RAG generation path.
- Do not silently drop ingredients because they are absent from the
  deterministic requirement vocabulary.
- Track cauliflower, cheese, and mushroom requirements for retrieval/diff
  decisions while retaining wording such as `riced cauliflower` in the full
  model input.
- Keep input limits, private-sidecar routing, `gpt-5.4-nano`, transactional
  revisions, budgets, safe responses, and no-save behavior unchanged.

## Acceptance

- Tests prove the complete initial request reaches importer generation and the
  named ingredients are represented in requirements.
- Repository validation, image/Compose checks, safe live verification,
  deployment, documentation, commit, and push complete without recording
  credentials, tokens, cookies, sessions, provider output, or real user data.
