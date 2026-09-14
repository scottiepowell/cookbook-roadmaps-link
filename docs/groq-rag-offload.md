# Groq RAG offload and recipe discovery

Goal: [Issue #10](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/10).
Mailbox: `0035N-groq-rag-offload-and-grounded-recipe-discovery.md`.

## Acceptance thresholds established before live comparison

Compare identical generated cooking requests against the installed public dataset.
Require all structured drafts to validate, original ingredient/quantity evidence
and citation IDs to survive, at least 10% lower combined estimated provider cost,
at least 10% lower nano input tokens, and no more than 2 seconds added p95 latency.
Require no visibility leaks and baseline fallback on every failed offload.
Small-sample latency percentiles are descriptive, not an SLA or production proof.
Failure of any gate keeps the Groq RAG flag off. Ingredient search does not need
an LLM and is independent of this experiment.

## Live comparison and decision

Four identical public/generated requests ran through the installed dataset and
real Groq and OpenAI APIs on 2026-09-13. Each mode produced four valid structured
drafts and retained the same three retrieval citation IDs per request. Core
ingredient concepts were present in every draft; wording and optional additions
varied, so this small sample is not a proof of recipe equivalence. The JSON
artifact `docs/0035n-rag-comparison.json` contains aggregate usage, timing and
safe per-request metadata. No user recipes or prompts are recorded there.

| Measure | Nano baseline | Groq dedup + nano | Change |
| --- | ---: | ---: | ---: |
| Nano input tokens | 4,651 | 4,548 | -2.2% |
| Nano output tokens | 2,583 | 2,567 | -0.6% |
| Groq input / output tokens | 0 / 0 | 2,913 / 1,104 | +4 calls |
| Estimated combined cost | $0.004159 | $0.004668 | +12.2% |
| p50 end-to-end | 6.28 s | 5.41 s | -0.87 s |
| p95 end-to-end | 7.09 s | 6.85 s | -0.23 s |
| Valid drafts | 4/4 | 4/4 | unchanged |

Cost and nano-input gates both failed. Keep `AI_RAG_GROQ_DEDUP_ENABLED=false`.
The result gives no reason to spend more on Groq RAG for this small context.
Optional deterministic duplicate removal is separately flagged and needs its
own comparison before enabling. Latency changes at n=4 are directional only.

## Other offload candidates

The baseline already performs retrieval, matching and context packing locally;
the 4-request comparison is the only measured provider delta. Entries below
with no delta are deliberately unpriced rather than presented as savings.

| Candidate | Nano work displaced; privacy | Deterministic path and quality risk | Extra calls; measured net change | Decision |
| --- | --- | --- | --- | --- |
| Query expansion | None in current retrieval; queries may be private | Local token normalization; expansion can drift intent | +1; unmeasured | Defer |
| Candidate reranking | None; retrieved public examples only | Existing local scoring; wrong rank loses evidence | +1; unmeasured | Defer |
| Context duplicate removal | Repeats in public context; public-only with hash pin | Exact substring check; protected source fields stay | +1; nano input -2.2%, cost +12.2%, p95 -0.23 s | Groq off |
| No-match triage | None; no-match is local | Return honest no-match; fabricated match risk | +1; no displaced cost | Keep local |
| Clarification | No automated baseline call | Ask user in UI; unnecessary prompts | +1; unmeasured | Defer |
| Public ingredient normalization | None in discovery | Local singularization; synonym overmatch risk | +1; no displaced cost | Keep local |
| Duplicate recipe detection | None | Compare normalized title/ingredients; false merge risk | +1; no displaced cost | Defer |
| Conversation summarization | Potential future long chat; private state excluded | Bounded recent turns; lost constraints risk | +1; unmeasured | Defer pending privacy and longer-chat evidence |
| Caching and batching | Repeated final generation, but requests are personalized | Visibility-scoped cache with invalidation; stale/private leakage risk | 0 or batched; unmeasured | Defer |

Other hosted providers would add another paid call to the same small context;
this experiment does not justify provisioning a second service. Recipe discovery
quality is improved in 0035O through reviewed public links and deterministic
matching, without a second hosted model.

## Runtime path and boundaries

Native recipe chat calls `recipe_session_routes._generate_and_store_draft`, then
`importer.import_recipe_text`. Dataset retrieval scores three examples locally;
`pack_importer_rag_context` keeps at most two examples with a nominal 2,000-character
budget. The optional `optimize_context` step runs after reserving nano's baseline
budget and before final structured generation. Source records, quantities, instructions, citations,
the original query and the final save/review contract remain authoritative.

`AI_RAG_GROQ_DEDUP_ENABLED` plus `AI_OFFLOAD_ENABLED` enable the Groq experiment.
The operator must pin all configured source files using
`AI_RAG_PUBLIC_DATASET_SHA256` (see comparison script). The fingerprint includes
CSV, both SQLite sources, and missing-file markers because the adapter can use
fallback databases. Unapproved or changed data bypasses Groq. It receives only
public example fields, never user queries, personal preferences, saved recipes,
chat state or account IDs. Account ZDR remains unverified, with no private-data
approval implied. No cross-user response cache is added.

The adapter suggests keep/omit decisions for snippets. Local validation permits
omission only when the entire snippet occurs verbatim in another preserved field.
No paraphrasing or ingredient/instruction deletion is allowed. Timeout, malformed
output, unsafe decisions, budget exhaustion, missing keys, changed dataset or
concurrency saturation preserve the original pack. Two in-flight Groq RAG calls
are allowed per process, each with an 8-second attempt timeout and one transient
retry. Each attempt reserves budget; returned tokens are metered even if rejected.
Failed attempts without usage are marked incomplete rather than counted as free.

`AI_RAG_DEDUP_ENABLED` independently applies the same proven duplicate omission
without a provider. Both flags default off pending comparison. No-match retrieval
remains deterministic. The primary model remains `gpt-5.4-nano`.

## Grounded discovery

The authenticated core `/api/recipe/discover` searches up to 5,000 visible recipes,
in 500-row pages, and returns up to 20 ingredient matches with real view links.
It preserves existing admin/own/public visibility and excludes trash. All matched
and unmatched entered ingredients are shown. Matching ingredient names does not
guarantee that the user has every required ingredient or imply substitutions.

The sidecar owns a small reviewed public link catalog. Core fetches the same
catalog without sending user input and matches it locally. A sidecar outage
leaves saved-recipe results usable. Public results are labeled as a limited
catalog; they are not a live web search. Only titles, attribution, selected
ingredient keywords and verified URLs are stored, not full recipes or images.
The installed Epicurious-derived dataset has no per-recipe URLs, so its record
IDs are not converted into invented website links.

Catalog entries were checked on 2026-09-13 at their original pages:

- [Spring Vegetable Salad](https://www.foodnetwork.com/recipes/food-network-kitchen/spring-vegetable-salad-3364967), Food Network Kitchen.
- [Carrot Soup](https://www.budgetbytes.com/carrot-soup/), Budget Bytes.
- [Carrot Salad](https://www.loveandlemons.com/carrot-salad-recipe/), Love and Lemons.

Five further metadata-only entries were checked on 2026-09-14:

- [Carrot and Red Onion Salad](https://www.foodnetwork.com/fnk/recipes/carrot-and-red-onion-salad-10034791), Food Network / Hawa Hassan.
- [Roasted Carrots and Red Leaf Lettuce Salad](https://www.foodnetwork.com/recipes/katie-lee/roasted-carrots-and-red-leaf-lettuce-salad-with-buttermilk-herb-dressing-3319689), Food Network / Katie Lee Biegel.
- [Mediterranean Lentil Soup](https://www.budgetbytes.com/mediterranean-lentil-soup/), Budget Bytes.
- [Greek Salad](https://www.loveandlemons.com/greek-salad-/), Love and Lemons.
- [Cucumber Tomato Salad](https://www.loveandlemons.com/cucumber-tomato-salad/), Love and Lemons.

Catalog maintenance: review the original page and its ingredient list before
adding metadata; store a stable HTTPS URL, source attribution, a review date,
and only ingredient keywords present on that page. Keep source-host validation
in the core route synchronized. Recheck links periodically; remove dead or
redirected entries instead of fabricating replacement URLs. This is an
editorially reviewed list, not an exhaustive recipe index.

## Comparison pricing sources

Official pages checked on 2026-09-13: [Groq model pricing](https://console.groq.com/docs/model/openai/gpt-oss-20b)
lists USD 0.075 input and 0.30 output per million tokens;
[OpenAI nano pricing](https://developers.openai.com/api/docs/models/gpt-5.4-nano)
lists USD 0.20 input and 1.25 output per million tokens. Comparison estimates
use uncached paid rates rather than treating free quota as permanent capacity.
[Groq structured outputs](https://console.groq.com/docs/structured-outputs) and
[data controls](https://console.groq.com/docs/your-data) describe model/schema
support and account retention controls; API success does not establish ZDR.
