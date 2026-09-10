# ADR: Free-Tier LLM Offload and QMD-Assisted Chat

Status: proposed for an isolated evaluation; runtime use is not approved

Date: 2026-09-10

Goal: [GitHub Issue #2](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/2), expanded by [GitHub Issue #4](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/4)

Mailbox source: `inbox/0033G-free-tier-llm-offload-qmd-chat-adr.md`

## Decision

The best first free-tier candidate is **Groq-hosted `openai/gpt-oss-20b`**.
Use it only in a future, separately approved pilot for bounded advisory work.
The first pilot should not be limited to RAG: conversation classification and
compression, recipe metadata suggestions, shopping-list organization, grounded
support triage, and aggregate usage-report narratives are also good candidates.
Keep OpenAI `gpt-5.4-nano` as the trusted final-answer and final-structured-output
baseline until Cookbook evals prove another path is at least as reliable.

The recommendation is a provider/model pair, not an endorsement of free quota
as production capacity. Groq's free limits support evaluation and light traffic
without a production availability guarantee. Quota exhaustion, model retirement,
and capacity errors must fall back to deterministic behavior or the baseline.

QMD remains a separate optional local retrieval experiment. Its BM25, vector,
hybrid, query-expansion, and reranking pipeline may improve paraphrase recall
and reduce context size, but its Node/native-model/index lifecycle is not
justified until a corpus benchmark shows a material gain.

The juice is worth the squeeze for a small Groq adapter and comparison harness.
QMD is conditional on retrieval benchmarks. Self-hosted `gpt-oss-20b` is not
worth it now: free weights still require roughly 16 GB of memory plus serving
and operations, while current Cookbook hosted-model costs are very low.

## Problem

Deterministic input checks and retrieval already avoid some OpenAI calls, but
many classification, transformation, drafting, and exploratory tasks can still
spend a hosted call despite not needing final-answer authority. A cheap advisory
tier could handle those bounded tasks directly or prepare a smaller, better
input for the baseline.

Free price alone is insufficient. A useful option also needs a stable API,
adequate quota, acceptable data handling, predictable failures, structured
output, a viable end-user application path, and enough quality to reduce calls.
A poor offload result increases latency and tokens by forcing fallback.

## Baseline and ownership

The accepted comparison floor is:

```text
OpenAI gpt-5.4-nano final-answer path
status=passed workflows=6/6 tokens=2227 estimated_cost_usd=0.00125495
```

The corrected 0030 baseline, including `0030P` no-bake cheesecake clarification,
remains part of every comparison. The core owns users, sessions, authorization,
and canonical recipes. The sidecar owns retrieval, provider calls, budgets, and
AI diagnostics. No model picker is exposed to users.

## Sources and verification

Facts were checked on 2026-09-10 against primary documentation. Free quotas,
catalogs, prices, and terms can change and must be rechecked before implementation.

- Groq: [rate limits](https://console.groq.com/docs/rate-limits),
  [`gpt-oss-20b`](https://console.groq.com/docs/model/openai/gpt-oss-20b),
  [structured outputs](https://console.groq.com/docs/structured-outputs),
  [OpenAI compatibility](https://console.groq.com/docs/openai),
  [data handling](https://console.groq.com/docs/your-data), and
  [services agreement](https://console.groq.com/docs/legal/services-agreement).
- Cloudflare: [pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/),
  [limits](https://developers.cloudflare.com/workers-ai/platform/limits/),
  [data use](https://developers.cloudflare.com/workers-ai/platform/data-usage/),
  [`gpt-oss-20b`](https://developers.cloudflare.com/workers-ai/models/gpt-oss-20b/),
  and [JSON mode](https://developers.cloudflare.com/workers-ai/features/json-mode/).
- Google: [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing),
  [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits), and
  [additional terms](https://ai.google.dev/gemini-api/terms).
- OpenRouter: [FAQ](https://openrouter.ai/docs/faq),
  [provider logging](https://openrouter.ai/docs/guides/privacy/provider-logging),
  and [ZDR controls](https://openrouter.ai/docs/guides/features/zdr).
- Local/open weight: [OpenAI's `gpt-oss` announcement](https://openai.com/index/introducing-gpt-oss/)
  and [`gpt-oss-20b` model page](https://developers.openai.com/api/docs/models/gpt-oss-20b).
- QMD: [official repository](https://github.com/tobi/qmd).

## Recommended provider fact register

| Fact | Verified state on 2026-09-10 | Implication |
| --- | --- | --- |
| Availability | `openai/gpt-oss-20b` is listed by Groq. | Recheck before implementation because hosted catalogs retire models. |
| Free quota | 30 RPM, 1,000 RPD, 8,000 TPM, and 200,000 TPD; limits are organization-wide. | Enough for evaluation/light advisory use, not guaranteed public capacity. |
| Paid price | $0.075/M input, $0.037/M cached input, and $0.30/M output; Developer upgrade needs a payment method. | Paid overflow is cheap but is not automatically approved. |
| API/auth | Bearer key and mostly OpenAI-compatible APIs; Chat Completions and Responses are documented. | Pin one endpoint/schema in a separate adapter; do not treat the current OpenAI adapter as drop-in. |
| Limits | 131,072-token context and 65,536 maximum output. | Retain much smaller task-specific Cookbook caps. |
| Structured output | Strict JSON Schema is supported; strict mode excludes streaming and tool use. | Strong fit for compact advisory contracts; validate locally anyway. |
| Retention | Inference is not retained by default except temporary reliability/abuse cases up to 30 days. Admins can enable ZDR; usage metadata remains. | Require ZDR before live tests and keep private recipes blocked pending privacy review. |
| End-user apps | Services agreement permits API integration into customer applications and access by end users, subject to terms/policies. | Public-app use is contemplated; operator must accept/check current terms. |
| Latency | Model page displays approximately 1,000 tokens/second. | Provider claim only; measure Cookbook end-to-end latency. |
| Region | Retained data is documented in US GCP buckets; inference locality is not established here. | Regional locality remains `unverified`. |
| Errors | Standard HTTP errors include 429 and 5xx failures. | Short timeout, bounded retry where safe, then deterministic/baseline fallback. |

The facts support an evaluation, not production approval. Account-specific
limits, current terms, model availability, ZDR state, and real error/latency
behavior remain implementation-time gates.

## Candidate comparison

| Candidate | Strengths | Material drawback | Decision |
| --- | --- | --- | --- |
| Groq + `openai/gpt-oss-20b` | 1,000 RPD/200k TPD free; 131k context; strict JSON; compatible API; controllable retention. | Free capacity has no production SLA; model/quota can change. | **Recommended bounded pilot.** |
| Cloudflare + `@cf/openai/gpt-oss-20b` | Existing Cloudflare relationship; same model family; 128k context; compatible Chat API; customer content is not used for training. The $0.11-equivalent daily allocation could cover roughly 846 illustrative 500-input/100-output calls at listed token rates. | Free usage is a compute allocation rather than a simple token quota; exact consumption must be measured. The reviewed docs expose `response_format` but do not provide Groq's strict-schema guarantee. | Strongest runner-up; compare if infrastructure consolidation or call volume outweighs strict-schema behavior. |
| Gemini 2.5 Flash-Lite unpaid | Free token pricing and capable low-cost model. | Unpaid terms permit product-improvement use and human review and say not to submit sensitive/confidential/personal data. Exact free quota is project-specific. | Public-fixture experiment only; blocked for private Cookbook data. |
| OpenRouter free models | Compatible API, many models, provider-policy filters. | Default 50 RPD (1,000 after buying $10 credits); its docs say free models are usually unsuitable for production. Routing variability hurts reproducibility/privacy review. | Benchmark lab only. |
| Local `gpt-oss-20b` | Apache 2.0; local data; same model family; 131k context. | About 16 GB memory plus download, serving, patching, cold starts, and capacity operations. | Defer until utilization or privacy justifies it. |
| QMD local model set | BM25/vector/RRF, local expansion/reranking/cache, retrieval benchmark support. | Node 22/Bun, native dependencies, three GGUF downloads around 2 GB, index freshness/deletion, hardware latency, model-license review. | Benchmark retrieval only. |
| GLM/Zhipu, direct DeepSeek, direct MiniMax | Possible low-cost candidates. | Complete primary-source free quota, privacy, retention, schema, and failure facts were not established; some current Cloudflare frontier variants require paid billing. | `Unverified`; blocked by existing fact gate. |

## General offload decision rule

A task is eligible when its output is advisory, reversible, privacy-safe,
bounded by a narrow contract, and cheap to verify mechanically or through the
existing user review step. It stays on deterministic/core or baseline paths
when it makes an authoritative decision, changes persisted state, handles
sensitive identity or account data, makes a safety-critical claim, or is more
expensive to verify than to generate correctly on the trusted path.

| Question | Eligible answer | Otherwise |
| --- | --- | --- |
| Can failure be ignored or regenerated without losing user work? | Continue. | Baseline/core. |
| Can the input be reduced to public, synthetic, aggregate, or minimal authorized data? | Continue. | Block pending privacy review. |
| Can a schema, closed candidate set, citation set, or human review cheaply verify it? | Continue. | Baseline. |
| Does it avoid auth, entitlement, payment, deletion, publication, or persistence authority? | Continue. | Deterministic/core authority. |
| Does it avoid food-safety, allergy, medical, and nutrition certainty? | Continue. | Safety policy and baseline. |
| Does it save a baseline call, reduce total tokens, or measurably improve success? | Pilot candidate. | Do not offload. |

This rubric matters more than whether a task happens to use retrieval.

## Proposed general offload flow

```text
User turn
  -> deterministic auth, safety, intent, scope, and input checks
  -> when grounding is needed:
       current keyword retrieval
       optional QMD/local hybrid retrieval when healthy and scoped
       merge by canonical source ID and preserve provenance
  -> optional Groq advisory task from an allowlist
       classify | transform | suggest | expand | rerank | compress
  -> deterministic contract, citation-ID, and scope validation
  -> local exploratory/clarification response when approved, or
  -> OpenAI gpt-5.4-nano final answer/structured output when needed
  -> safe response plus provider/task/usage/budget metadata
```

The offload model never receives a raw database, unrestricted corpus, cookie,
session, account record, secret, provider response, or authorization decision.
Retrieved snippets carry stable citation IDs through compression. Unknown,
dropped, duplicated, or invented IDs reject the advisory result.

## Quality and cost mechanisms

- Expansion adds bounded aliases and paraphrases while preserving the original
  query at highest weight.
- Hybrid lexical/semantic retrieval can improve paraphrase recall without
  sacrificing exact title/ingredient anchors.
- Reranking sees only authorized candidates and cannot add documents.
- Compression selects supporting sentences with citation IDs, shrinking the
  final prompt and removing distractors.
- Clarification resolves ambiguity before retrieval/generation.
- Deterministic no-match, malformed-input, cache-hit, and clarification paths
  avoid every provider whenever possible.
- Cache expansion, rerank, and compression results by corpus version, contract
  version, model ID, normalized query hash, and visibility scope.
- An offload call always followed by a baseline call is not a saving unless it
  reduces baseline tokens, prevents retries, or improves answer success.

Free-tier users may receive more exploratory or clarification turns while final
answer limits and session budgets remain authoritative. The UI shows consistent
degraded/unavailable states and no model picker.

Outside retrieval, savings come from accepting a validated advisory result as
the completed low-risk task, such as classifying an intent, grouping a shopping
list, or drafting an aggregate report narrative. Where the baseline still must
run, the offload step counts only when it reduces total tokens, retries, or
end-to-end failures.

## Task classification

| Task | Policy and guard |
| --- | --- |
| Query expansion / ingredient synonyms | Allowed for public vocabulary or minimal scoped terms; bound count/length and fall back to original query. |
| Clarification candidate | Advisory only; deterministic policy approves one non-invasive question. |
| Retrieval reranking | Input IDs only; output must be a permutation/subset; fall back to deterministic rank. |
| Context compression | Bounded snippets only; all claims retain input citation IDs; fall back to uncompressed context. |
| QMD/local-note summary | Authorized generated snapshots only; preserve source/version/citation mapping. |
| No-match triage | Cannot invent a match; fall back to no-match or baseline policy. |
| Cache-key/retrieval-plan suggestion | Advisory; local code computes the scoped key and executes only approved plans. |
| Low-risk brainstorming/title suggestion | Facts already fixed; never auto-persist or publish. |
| Draft checklist critique | Cannot become the final answer; deterministic/baseline checks decide. |
| Intent/workflow classification | Closed label set with confidence threshold; unknown or low-confidence results use deterministic routing or baseline. |
| Conversation summary/memory compression | Minimal authorized turns only; preserve explicit constraints and mark omissions; never replace the canonical transcript. |
| Help/onboarding or FAQ draft | Ground only in approved product documentation; retain citations; user or support agent reviews before use. |
| Recipe title, description, tags, cuisine, or technique suggestions | Advisory candidates from known recipe facts; validate length/enums; never auto-save. |
| Ingredient normalization and unit parsing suggestions | Return source spans and normalized candidates; deterministic parser or user decides the accepted value. |
| Instruction cleanup or ordering suggestions | Preserve ingredients, exclusions, and safety constraints; user/baseline owns final recipe. |
| Substitution candidates | Clearly advisory; exclude allergy, medical, and guaranteed-equivalence claims; require user review. |
| Duplicate-recipe candidate detection | Rank only an authorized closed candidate set; deterministic thresholds and user decide merge behavior. |
| Meal-plan brainstorming or candidate ranking | Rank only supplied recipes against explicit preferences; final plan JSON and save remain baseline/core. |
| Shopping-list grouping, aisle labels, and duplicate suggestions | Transform a supplied list without adding purchases; deterministic quantity reconciliation and user review remain authoritative. |
| Pantry-use and leftovers ideas | Brainstorm from explicitly supplied facts; no freshness or food-safety determination. |
| Draft translation, plain-language rewrite, or formatting | Preserve protected terms, quantities, citation IDs, and placeholders; user reviews before publish. |
| Support ticket classification/routing | Closed queue and priority labels from sanitized text; no account action, promise, or customer message is sent automatically. |
| Sanitized log clustering and incident summary | Aggregate/redacted diagnostics only; cite event IDs; operators diagnose and act. |
| Aggregate usage-report narrative | Receive precomputed non-identifying metrics only; cannot calculate billing, entitlement, or enforcement decisions. |
| Release-note or documentation draft | Generate from an approved change set; reviewer verifies before commit or publication. |
| Synthetic eval cases, failure clustering, and prompt critique | Offline development aid only; deterministic tests and reviewer acceptance remain required. |
| Content-risk tag suggestion | Advisory signal only; deterministic policy/baseline makes any enforcement or refusal decision. |
| Final importer JSON, meal-plan JSON, final answer, citation-faithfulness decision | Baseline only. |
| Food safety, allergy, medical, or nutrition certainty | Baseline/safety policy only. |
| Auth, account, deletion/export, admin, entitlement, payment, or budget decisions | Deterministic/core authority only. |
| Any write/publish action | Blocked; existing user review, authorization, and core transaction remain required. |

## Integration options

| Option | Pros | Cons | Sequence |
| --- | --- | --- | --- |
| Direct Groq adapter | Pinned model, explicit boundary, clear metrics/circuit breaker. | New Chat mapping and provider errors/config. | First hosted pilot. |
| Internal OpenAI-compatible contract | Reusable message/schema concepts. | Compatibility is partial; lowest-common-denominator design can hide behavior. | Small interface with explicit adapters. |
| Cloudflare Workers AI | Existing operator relationship, same `gpt-oss-20b` family, serverless, favorable data statement, and useful short-call capacity. | Neuron accounting needs measurement and strict schema behavior is less explicit. | Strong runner-up if consolidation or volume matters. |
| OpenRouter | Rapid access to many models and privacy controls. | Dynamic routes and weak free capacity. | Evaluation lab. |
| Local `gpt-oss-20b` | Control and no marginal provider bill. | Disproportionate hardware/operations now. | Revisit after usage evidence. |
| QMD adapter | Purpose-built local hybrid retrieval/cache. | Node/native/GGUF/index lifecycle beside Python. | Benchmark before integration. |

## Prioritized pilot sequence

| Phase | Candidate tasks | Why here |
| --- | --- | --- |
| 1A | Intent classification, conversation compression, title/tag suggestions, shopping-list grouping, support routing, and aggregate usage-report narrative | Small contracts, easy validation, low consequence, and several can complete without a baseline call. |
| 1B | Query expansion, reranking, context compression, and grounded FAQ drafts | Existing retrieval evidence and citation checks provide clear comparison gates. |
| 2 | Ingredient/unit suggestions, instruction cleanup, meal-plan candidate ranking, translation/plain-language drafts, sanitized incident summaries, and substitution ideas | Higher semantic risk or more human-review burden; promote one at a time. |
| Keep authoritative | Final recipes/plans/answers, persistence/publication, auth/accounts, billing/entitlements, deletion/export, moderation enforcement, and health/safety claims | Failure is costly, sensitive, or difficult to verify cheaply. |

## Future implementation plan

A separate mailbox task should implement Phase 1A first:

1. Define an `OffloadProvider` contract with task, schema version, bounded
   payload, model, timeout, and an accept-or-ignore result.
2. Add a Groq Chat Completions adapter with a dedicated key, pinned
   `openai/gpt-oss-20b`, strict JSON Schema, low reasoning effort, low token cap,
   temperature zero, and short timeout. Do not merely change the current OpenAI
   Responses client's base URL.
3. Add a deterministic task allowlist and payload builder. Start with generated
   fixtures for intent classification, conversation compression, title/tag
   suggestions, shopping grouping, support routing, aggregate-report narrative,
   public-dataset expansion, and reranking. Keep private saved recipes blocked.
4. Enable Groq ZDR before a live test and record only non-secret status.
5. Meter provider/model/task attempts, accepted/rejected output, timeout,
   rate-limit, fallback, tokens, latency, and cache hit.
6. Add a 429/5xx circuit breaker and bounded retry. Never cascade through
   multiple free providers on one user turn.
7. Extend offline evals for malformed JSON, closed-label violations, lost user
   constraints, changed quantities, invented/missing citations, unsafe claims,
   privacy violations, timeout, and quota fixtures.
8. Run a manual opt-in live comparison using generated public fixtures only.
9. Promote one task class at a time after it meets all gates.

Phase 2 may benchmark QMD in an isolated local process/container using generated
Markdown snapshots. Compare deterministic BM25, vector, hybrid without rerank,
and full rerank. Do not add QMD to the Python image or index canonical storage.

## Metrics and starting gates

| Metric | Starting decision rule |
| --- | --- |
| Provider calls avoided | At least 25% of eligible turns avoid the baseline call. |
| Baseline context tokens | Median reduction at least 30%, with no citation loss. |
| Total tokens | Must decrease across all providers per successful answer. |
| Retrieval | Improve recall@5 or MRR at least 10% on paraphrases without reducing exact-match precision more than 2%. |
| Citation fidelity | 100% of citation IDs are authorized inputs; zero invented IDs. |
| Answer quality | No regression in locked Cookbook workflows. |
| Advisory acceptance | At least 80% of accepted Phase 1A outputs pass their task-specific deterministic contract without repair. |
| Human correction | Track rejection and material-edit rates for reviewed drafts; do not promote a task whose review cost erases the saving. |
| Constraint preservation | 100% preservation of explicit quantities, exclusions, protected terms, placeholders, and closed-set IDs where applicable. |
| Latency | Eligible-turn P95 no more than 20% slower; local/clarification turns should improve. |
| Cache | Report scoped hit rate and prove correct invalidation/no cross-scope hits. |
| Failure safety | 100% of deterministic rejection/fallback fixtures pass. |
| Cost | Report both providers and estimated local compute per successful answer and avoided baseline call. |

These thresholds are evaluation hypotheses, not production SLAs. Record corpus,
model, provider tier, contract version, and hardware class with results.

## Risks and controls

- Hallucinated expansions: validate/cap terms and retain original query.
- Semantic false positives: retain exact anchors, filters, and precision floor.
- Citation drift: use a closed ID set and reject unsupported sentences.
- Stale QMD indexes: version sources, deny stale mappings, process deletions,
  and keep indexes disposable/rebuildable.
- Abuse/quota: session and task limits, concurrency cap, circuit breaker, no
  automatic paid overflow.
- Provider churn: pin model/contract and re-evaluate replacements.
- Privacy: public/minimal payloads first; Groq ZDR required; Gemini unpaid and
  OpenRouter dynamic routing blocked for private data.
- Mixed quality: consistent UI/support states with provider metadata hidden from
  ordinary users.
- Local cost: measure download, warm-up, CPU/RAM/GPU, index time, query latency,
  and maintenance before adopting QMD/local inference.
- Retry multiplication: at most one safe bounded retry; no provider cascade.
- Cheap but low-value generation: require task-level acceptance, edit-effort,
  call-avoidance, and total-cost evidence before promotion.

## Related product work

Session timers still govern access independently of provider quota. SSO does
not authorize private-recipe transfer, and BYOS stays in its authorized scope.
Analytics may record aggregate task/latency/fallback/cache metrics but not
prompts, recipe content, identity, or secrets. Monetization cannot weaken
safety, privacy, citation, or provider gates. Usage reports must distinguish
primary, offload, and local retrieval activity.

## Go/no-go

The Groq pilot requires a separate approved task, refreshed facts, operator
acceptance of current terms, ZDR enabled, a dedicated secret, approved payload
examples, and offline failure/eval fixtures. Production remains no-go until a
generated-fixture live comparison passes quality, citation, latency, avoidance,
and total-token gates.

QMD remains no-go pending its benchmark. Self-hosted `gpt-oss-20b`, Gemini
unpaid private-data use, OpenRouter production free routing, and unverified
GLM/DeepSeek/MiniMax candidates remain no-go.

## Non-goals

- No provider SDK, adapter, account, key, request, or routing change.
- No live provider call.
- No QMD/Node/Bun/native dependency, model download, index, snapshot, vector DB,
  embedding implementation, or local model server.
- No model picker, timer, SSO/BYOS, analytics, Resend, ads, monetization, AWS,
  auth, payment, public route, or canonical recipe change.
- No secrets, prompts, provider outputs, datasets, traces, screenshots, or
  generated artifacts are committed.
