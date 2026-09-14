# 0035N Groq RAG offload and grounded recipe discovery results

Status: partial. Goal: [Issue #10](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/10).
Source: `inbox/0035N-groq-rag-offload-and-grounded-recipe-discovery.md` (unchanged).

## Delivered

- Added optional, bounded Groq duplicate elimination in the real importer RAG
  path. It is limited to a hash-pinned public dataset, preserves source fields,
  never sends user text, and falls back to the original context on any failure.
  Provider attempts and token use are metered. It remains **disabled by default**.
- Added a metadata-only catalog of three verified public recipe links. The
  authenticated external core searches visible canonical recipes and this
  reviewed catalog for one combined ingredient query, shows all/partial/missing
  matches, and keeps local matches available during sidecar outages. This is a
  small catalog, not live web search.
- Added the live comparison harness and report in
  `docs/0035n-rag-comparison.json`, full explanation and candidate decision table
  in `docs/groq-rag-offload.md`, and the reusable `skills/mailbox-gitops/SKILL.md`.
  The skill was also installed locally at the Codex skills path.
- External core change is local commit `6628c79` on
  `codex/0035n-recipe-discovery`. The checked upstream
  `jt196/vanilla-cookbook` grants pull but not push, so this core change cannot
  be published as an upstream PR with the current permissions. No core source
  was copied into this sidecar repository.

## Evidence and decision

Four public/generated requests ran with real Groq and OpenAI calls in both
modes. Structured drafts validated 4/4 in each mode with identical retrieval
citation IDs. Nano input fell from 4,651 to 4,548 tokens (2.2%), while estimated
combined provider cost rose from $0.004159 to $0.004668 (12.2%). p95 fell from
7.09 to 6.85 seconds in this small sample. The predeclared 10% nano-input and
10% total-cost reduction gates failed. Keep Groq RAG off and do not spend further
implementation effort on it without a different, measured workload.

Sidecar: 510 Python tests passed; repository validator checked shell syntax,
Compose configuration and the existing evaluations. Core: 11 new discovery
unit/integration tests passed; the signed-in Playwright test passed against a
disposable loopback Docker stack and verified saved and public links plus
no-match behavior. Full core suite: 706 passed, 7 failed, 3 skipped; the seven
failures are in existing recipe parsing and ingredient-conversion tests, outside
the changed files. Prettier and `git diff --check` passed on changed core files.
No private recipe data was sent to Groq in the provider comparison.

## Remaining work

- Issue #10 stays open because its Groq savings gate failed and the external
  core commit lacks upstream publication. The next product task should expand
  the verified public link catalog and improve deterministic ingredient matching
  with relevance tests, rather than add another hosted RAG call.
- Public deployment of the core UI depends on an authorized writable upstream
  or other agreed core publication route. Do not imply public rollout from the
  sidecar merge alone.
