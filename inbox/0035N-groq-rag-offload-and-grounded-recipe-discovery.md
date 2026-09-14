# 0035N Groq RAG Offload and Grounded Recipe Discovery

## Source and Goal

Goal: https://github.com/scottiepowell/cookbook-roadmaps-link/issues/10

The operator asked whether Groq reduces nano work inside retrieval augmented
generation (RAG), requested a committed execution prompt if it does not, and
asked for other efficient offload opportunities. The preceding request asked
what carrots, lettuce, and onions map to and requested actual database recipes
and links to recipes on public websites. Execute this combined follow-on goal.

## Verified Starting Point

At prompt creation, Groq is called only through the separate Kitchen ideas
advisory route. Shopping aisle labels are generated suggestions, not recipe
matches. Search wording is not wired into retrieval. The nano recipe generation
path is unchanged; no RAG token or cost savings have been demonstrated.
Read AGENTS.md, docs/groq-advisory-pilot.md and
docs/free-tier-llm-offload-qmd-chat-adr.md, then verify current code before edits.

## Required Implementation

1. Trace the actual recipe query, retrieval, context assembly, and final nano
   generation path. Record baseline provider calls, input/output tokens, latency,
   groundedness, ingredient match quality, and empty-result behavior.
2. Integrate the existing server-side Groq adapter into that real flow behind
   independent feature flags. Evaluate bounded query normalization/expansion,
   candidate reranking, and evidence-preserving context compression. Implement
   the stages that demonstrate useful net savings; do not add a call merely to
   advertise offload. Preserve original-query retrieval and a baseline fallback.
3. Treat carrots, lettuce, and onions together as one ingredient query. Search
   canonical recipes through the authenticated external core with existing
   visibility and ownership rules. Show real recipe links, matched ingredients,
   missing ingredients, and clearly labeled partial matches or no matches.
   Keep deterministic ingredient matching available without an LLM.
4. Add a separately labeled public recipe source path using real, verified
   source URLs and approved public search/catalog data. Inspect the existing
   dataset for provenance and synthetic fixtures before using it. Do not invent
   recipes or URLs, present fixtures as real sources, or imply whole-web search
   when using a limited catalog. Preserve title, source attribution and links;
   respect source terms and avoid copying complete copyrighted recipes.
5. Keep OpenAI gpt-5.4-nano responsible for final recipe/importer JSON and the
   established review/save contract. Groq output is untrusted: validate source
   IDs, schema, bounds, ingredient quantities, provenance, and supported claims.
   Retrieved content must not override instructions. Never let compression drop
   relevant ingredient constraints or convert suggestions into safety decisions.
6. Retain strict timeouts, bounded retries, circuit breaker, budgets, concurrency
   controls, fallback, and aggregate usage reporting. Count both providers and
   retries. Cache only with correct visibility isolation and invalidation; never
   share private recipe content across users. Log no prompts or secret values.
7. Preserve the current public/generated-data boundary. Authentication alone
   does not authorize sending saved recipes or personal preferences to Groq.
   Verify account privacy controls and applicable policy before widening it;
   otherwise keep private retrieval local/core and bypass Groq for private data.

## Additional Efficiency Assessment

Produce a measured decision table covering query expansion, reranking, context
compression, no-match triage, clarification, public ingredient normalization,
duplicate detection, conversation summarization, and caching/batching. For each,
record current nano work displaced, eligibility/privacy, deterministic alternatives,
quality risk, additional calls, net token/cost change, latency and implement/defer
decision. Avoid claiming savings where the baseline made no nano call. Refresh
provider/model capabilities and pricing from official sources before estimating
cost. Assess other hosted providers only if evidence suggests a useful advantage;
do not provision services or expose keys for a speculative comparison.

## Validation and Acceptance

- Use identical representative fixtures with offload on/off. Report total Groq
  plus OpenAI usage, nano input reduction, estimated cost, latency distributions,
  and retrieval/final-answer quality. Set and justify acceptance thresholds before
  evaluating; retain baseline defaults if savings or quality gates fail.
- Test all-ingredient, partial, and no-match queries, including the operator's
  carrots/lettuce/onions example. Check links resolve to the cited real sources.
- Test private/public visibility, cross-user isolation, malicious source text,
  malformed output, unknown IDs, lost quantities, missing keys, budget exhaustion,
  timeout, rate limits and provider outage with reliable baseline fallback.
- Run repository validation and appropriate core tests. Validate Docker/Compose
  runtime changes and Playwright browser behavior in the signed-in native flow.
  Perform a real provider smoke with public/generated data when credentials are
  available. Separate mocked tests from provider/browser evidence and report
  exact blockers without weakening assertions or claiming unperformed checks.

## GitOps and Project Boundaries

Sync and inspect the current queue before execution; keep this inbox prompt
immutable. Use Issue #10 and a codex/ implementation branch. Sidecar code, docs,
deployment and evaluations belong here. Core UI, auth and canonical recipe queries
belong in C:\Users\scott\projects\vanilla-cookbook-core; do not vendor core source
or touch Concessions. Inspect core remotes and permissions before publication.

Commit, push and open a PR with the Goal, this prompt, changed areas, validation,
deployment impact, provider status, limitations and follow-ups. Resolve checks
and merge completed work, then clean up and sync. Write
outbox/0035N-groq-rag-offload-and-grounded-recipe-discovery-results.md with actual
implementation evidence and any external core commit/publication status. Close
Issue #10 only when the implementation satisfies this Goal. Publishing this
prompt alone does not complete it and must not create a completion outbox record.
