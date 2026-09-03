# 0034U Public AI Recipe Chat Results

Status: complete and deployed.

## Delivered

- authenticated core-owned recipe chat handles bound to the current user;
- initial clarification questions and ongoing natural-language revisions;
- current-draft context supplied to each revision with preserve-unchanged
  instructions;
- explicit confirmation before a likely different recipe replaces the draft;
- a server-enforced maximum of ten post-draft changes;
- persistent-on-page conversation UI with collapsible recipe, ingredients,
  instructions, and grounding sections;
- safe response shaping that excludes sidecar IDs and retrieval internals.

Chat ownership and sidecar sessions are bounded in-memory for one hour and are
lost when either process restarts. Starting over creates a new recipe chat.
This task does not save a draft to canonical Cookbook storage.

## Validation

- Core `svelte-check`: 0 errors and 0 warnings.
- Core focused Vitest: 9 passed across the chat and existing importer proxies.
- Sidecar repository validation: 422 tests passed, 39 offline evaluations
  passed, and all 7 repository checks passed.
- `git diff --check`: passed in both workspaces.
- Public Compose config: passed using ignored core environment files without
  displaying their values.
- Images built: `local/vanilla-cookbook-adapter:0034u` and
  `local/cookbook-ai-sidecar:0034u`.
- Deployment: core running, sidecar healthy, no host port published for either
  public container, and the independent tunnel remained running.
- Public boundary: health returned 200, anonymous `/ai` returned the expected
  redirect, and anonymous chat submission returned 401.
- Safe internal smoke: initial draft returned at change zero; a different-dish
  request returned `new_recipe_confirmation` and retained the draft; ten
  changes completed; the next change returned `change_limit_reached` with a
  maximum of ten. No draft, prompt, provider output, dataset row, credential,
  token, session value, cookie, or user data was recorded.

The external core work is committed locally on
`openclaw/0034U-public-ai-recipe-chat` at
`6d387f4ccd97b8ba6eed52354f242d48e4361baa`. It was not pushed to the
third-party core remote. The sidecar completion commit records the deployable
Compose and mailbox result.
