# 0033G Hosted Free-Tier LLM Offload ADR Results

Created [Hosted Free-Tier LLM Offload ADR](../docs/free-tier-llm-offload-qmd-chat-adr.md)
for [Goal #2](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/2)
and expanded its task scope in
[Goal #4](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/4),
then clarified the hosted-only constraint and setup in
[Goal #6](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/6).

## Recommendation

The best evaluated first candidate is Groq-hosted `openai/gpt-oss-20b`, limited
to a future bounded advisory pilot. The model/provider pair currently offers a
useful free quota, strict JSON Schema, an OpenAI-compatible API surface, high
claimed token speed, a 131k context window, and controllable retention/ZDR.
OpenAI `gpt-5.4-nano` remains the trusted final-answer and final-structured-
output baseline.

The conclusion is that one small GroqCloud offload adapter is worth evaluating.
Externally hosted API inference is a hard requirement. Self-hosted/local models
and QMD are outside the selected solution rather than deferred alternatives.

## External facts

Primary documentation was reviewed on 2026-09-10 for Groq, Cloudflare Workers
AI, Gemini, and OpenRouter. The ADR links every source and
marks remaining facts and candidates as verified, unverified, or blocked.

The candidate matrix concludes:

- Groq `openai/gpt-oss-20b`: recommended for an isolated advisory pilot;
- Cloudflare `gpt-oss-20b`: strongest runner-up because it uses the existing
  Cloudflare relationship, has favorable data-use terms, and may support more
  short daily calls; Groq has the clearer strict-schema guarantee and token quota;
- Gemini 2.5 Flash-Lite unpaid: blocked for private data because unpaid-service
  terms allow product-improvement use and human review;
- OpenRouter free routing: useful for benchmarking but explicitly weak for
  production capacity and harder to reproduce/audit;
- local `gpt-oss-20b`: technically feasible, operationally premature;
- GLM/Zhipu, direct DeepSeek, and direct MiniMax: still unverified and blocked.

## Architecture and offload value

The ADR defines a hosted-API flow from deterministic intent/safety checks,
through current retrieval when needed, bounded offload expansion/
rerank/compression, deterministic citation validation, and the baseline final
answer only when needed. It explains how this can improve paraphrase recall,
exact-match precision, context packing, cacheability, clarification, citation
fidelity, latency, provider-call avoidance, and cost per successful answer.

The proposed go/no-go measures include baseline calls avoided, total and
baseline-context tokens, recall@5/MRR, exact-match precision, citation fidelity,
answer quality, P95 latency, scoped cache hits, failure safety, and estimated
cost including local compute. An advisory call that merely precedes every
baseline call is not counted as a saving.

Allowed candidates include bounded expansion, clarification, reranking,
compression, local-note summaries with source mapping, no-match triage, cache/
retrieval-plan suggestions, low-risk brainstorming, and checklist critique.
The expanded decision also covers cheaply verifiable non-RAG work: intent
classification, conversation compression, recipe metadata and cleanup
suggestions, shopping-list grouping, meal-plan candidate ranking, grounded help
drafts, support routing, sanitized incident summaries, aggregate usage-report
narratives, localization drafts, and offline eval/documentation assistance.
Final answers/JSON, citation authority, safety/health claims, auth/account/admin/
payment/budget decisions, and all write/publish actions remain baseline,
deterministic, or blocked.

The governing rule is task risk and verification cost rather than whether the
task uses retrieval. Phase 1 prioritizes narrow schemas, closed candidate sets,
and transformations whose outputs can be ignored or reviewed without losing
user work. Metrics now include contract acceptance, material correction effort,
and explicit-constraint preservation alongside call, token, quality, latency,
privacy, and fallback measures.

## Implementation needs

A separate future task would add a small explicit `OffloadProvider` contract,
a pinned GroqCloud Chat Completions adapter using the existing OpenAI Python
client with Groq's base URL, dedicated secret, strict JSON schema,
task/payload allowlist, enabled ZDR, per-provider/task metering, circuit breaker,
scoped cache, failure fixtures, and a manual generated-fixture live comparison.
Private saved recipes stay blocked during the first evaluation. QMD is a
separate historical retrieval idea and is not part of this hosted solution.

The ADR now includes the manual steps to create isolated GroqCloud projects and
keys, enable ZDR, confirm the model and limits, configure the ignored local
`.env`, and later add environment-scoped GitHub deployment secrets. It explicitly
states that the current codebase cannot use Groq until the adapter is implemented
and that normal CI must remain offline and keyless.

## Planning updates and validation

Updated `README.md`, `docs/ai-feature-status.md`,
`docs/ai-implementation-backlog.md`,
`docs/product-priority-roadmap-after-0032A.md`, the secondary-provider fact
register, and its implementation gate.

Validation passed:

- full repository validator: 489 AI API tests passed;
- offline evals: 39 cases passed;
- shell syntax, Docker Compose, whitespace, local Markdown links, old-domain
  guard, and secret-pattern scan passed;
- `git diff --check` passed.

The validation remained offline/mock-only. No provider or browser call was made.

GitHub's Ubuntu validation job remains red for the same pre-existing portability
failures present on `main`: tests invoke the Windows executable name
`powershell`, one script assumes `TEMP` exists, and local-save platform gates
report unavailable. The branch did not change those scripts, tests, or workflow.
Local Windows validation passed the complete suite. Repairing cross-platform CI
is separate from this documentation-only mailbox task.

## Non-goals

No provider SDK, runtime adapter, provider call, local inference, model download,
generated index/snapshot, vector DB, route, model
picker, auth, timer, BYOS, analytics, Resend, monetization, AWS, payment, or
public exposure was added. No secrets, prompts, provider output, raw datasets,
traces, screenshots, or generated artifacts were committed.
