# 0033G Free-Tier LLM Offload And QMD-Assisted Chat ADR Results

Created [Free-Tier LLM Offload and QMD-Assisted Chat ADR](../docs/free-tier-llm-offload-qmd-chat-adr.md)
for [Goal #2](https://github.com/scottiepowell/cookbook-roadmaps-link/issues/2).

## Recommendation

The best evaluated first candidate is Groq-hosted `openai/gpt-oss-20b`, limited
to a future bounded advisory pilot. The model/provider pair currently offers a
useful free quota, strict JSON Schema, an OpenAI-compatible API surface, high
claimed token speed, a 131k context window, and controllable retention/ZDR.
OpenAI `gpt-5.4-nano` remains the trusted final-answer and final-structured-
output baseline.

The conclusion is that a small hosted offload adapter is worth evaluating.
Self-hosting the same open-weight model is not currently justified by Cookbook's
low baseline cost and the roughly 16 GB memory plus serving/operations burden.
QMD remains worth benchmarking as a separate local retrieval candidate but is
not accepted as a runtime dependency.

## External facts

Primary documentation was reviewed on 2026-09-10 for Groq, Cloudflare Workers
AI, Gemini, OpenRouter, OpenAI `gpt-oss`, and QMD. The ADR links every source and
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

## Architecture and RAG value

The ADR defines a QMD-assisted flow from deterministic intent/safety checks,
through keyword and optional hybrid retrieval, bounded offload expansion/
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
Final answers/JSON, citation authority, safety/health claims, auth/account/admin/
payment/budget decisions, and all write/publish actions remain baseline,
deterministic, or blocked.

## Implementation needs

A separate future task would add a small explicit `OffloadProvider` contract,
a pinned Groq Chat Completions adapter, dedicated secret, strict JSON schema,
task/payload allowlist, enabled ZDR, per-provider/task metering, circuit breaker,
scoped cache, failure fixtures, and a manual generated-fixture live comparison.
Private saved recipes stay blocked during the first evaluation. QMD would be a
later isolated benchmark using generated snapshots, not canonical storage.

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

No provider SDK, runtime adapter, provider call, QMD install, Node/Bun/native
dependency, model download, generated index/snapshot, vector DB, route, model
picker, auth, timer, BYOS, analytics, Resend, monetization, AWS, payment, or
public exposure was added. No secrets, prompts, provider output, raw datasets,
traces, screenshots, or generated artifacts were committed.
