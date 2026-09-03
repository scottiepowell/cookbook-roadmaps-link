# 0034U - Public AI Recipe Chat

## Goal

Turn the authenticated public AI importer from a one-shot form into a bounded
conversation for one recipe. Preserve the current generated draft as context,
allow clarification answers and up to ten requested revisions, and require
explicit confirmation before abandoning it for a different recipe.

## Required behavior

- Keep the input available after the first draft so the user can request a
  change in natural language.
- Generate follow-up drafts from the current draft plus the latest requested
  change, preserving details the user did not ask to alter.
- Ask deterministic clarification questions when the recipe request is not
  specific enough to generate safely.
- When a follow-up appears to request a different dish or a restart, retain the
  current draft and ask whether to start a new recipe.
- Enforce a server-side maximum of ten post-draft changes per recipe.
- Let users collapse and expand the recipe, ingredients, instructions, and
  grounding details with clear plus/minus affordances.

## Boundaries

- Keep core authentication and public chat ownership in Vanilla Cookbook.
- Keep the sidecar private and send it no browser cookie, user identity, OAuth
  artifact, or canonical Cookbook data.
- Pin live generation to `gpt-5.4-nano` and reuse the existing read-only local
  recipe dataset/RAG path.
- Return only the existing bounded draft and safe grounding summary to the
  browser. Do not expose sidecar session IDs, retrieval queries, record IDs,
  snippets, prompts, provider responses, or local paths.
- Do not save recipes automatically or add production write authority.
- Conversation state may remain bounded, in-memory, and expiring for this
  increment; document restart/expiry behavior.

## Acceptance

- Initial generation, clarification, arbitrary follow-up revision, replacement
  confirmation, ownership isolation, and the ten-change limit have tests.
- Public Compose allowlists only `importer,recipe_session`, has capacity for the
  initial call plus ten changes, and publishes no sidecar host port.
- Core and sidecar images build, validation passes, the public stack is healthy,
  and safe runtime evidence confirms the conversation states.
- Update status/backlog/product docs, write the matching outbox result, commit
  the core change locally, and commit/push the sidecar result.
