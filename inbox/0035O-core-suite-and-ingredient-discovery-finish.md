# 0035O Core Suite and Ingredient Discovery Finish

Goal: https://github.com/scottiepowell/cookbook-roadmaps-link/issues/13
Related prior Goal: https://github.com/scottiepowell/cookbook-roadmaps-link/issues/10

The operator requested that we repair the seven failures in the full external
Vanilla Cookbook core test suite, retaining tests that cover useful parsing and
conversion behavior and removing tests only if shown obsolete. Then finish and
improve ingredient-based recipe discovery. The operator no longer considers
Groq RAG savings a worthwhile investment on the measured workload.

## Required work

1. Reproduce all seven full-suite failures and identify source-code, fixture,
   assertion, or shared-state causes. Preserve meaningful conversion and parser
   assertions; do not weaken production behavior to turn tests green. Add or
   update focused regressions for the actual fixes.
2. Check the installed recipe fixture and source parser for the failing 750g
   case. If the saved source is malformed or genuinely obsolete, document that
   evidence and update the compatibility manifest appropriately; otherwise fix
   extraction while preserving source provenance.
3. Improve the existing core ingredient discovery from commit `6628c79`:
   meaningful normalization/ranking and real saved-recipe links with visibility
   isolation; add verified public recipe links or a sustainable reviewed catalog
   maintenance path. Keep all/partial/no-match distinctions honest and do not
   imply whole-web search.
4. Resolve the external-core publication path. Check upstream permissions and
   an existing or possible operator fork; publish core code through a branch/PR
   where authorized. Do not vendor it into the sidecar. If upstream cannot be
   merged by this account, document that exact boundary and deploy only through
   the established local-image public-stack path when safe.
5. Run focused and full core tests, sidecar repository validation, Docker and
   Compose checks, signed-in Playwright on isolated data, and public smoke if
   deploying. Distinguish test, provider, browser, and production evidence.
6. Keep Groq RAG disabled by default. Do not add speculative Groq or other
   provider calls. Close Issue #10 only if the completed discovery delivery and
   measured decision resolve its remaining scope; otherwise explain what is
   still open. Close this Goal only when its requirements are actually complete.

## GitOps

Keep this inbox prompt immutable after publication. Implement sidecar changes
here and core changes in `C:\Users\scott\projects\vanilla-cookbook-core`.
Record actual outcomes in
`outbox/0035O-core-suite-and-ingredient-discovery-finish-results.md`. Commit,
push, open a PR linked to Issue #13 and this prompt, resolve checks, merge
completed work, and sync the canonical checkout. Keep ignored credentials and
runtime data out of commits.
