# 0033G Free-Tier LLM Offload And QMD-Assisted Chat ADR

## Goal

Investigate a future architecture for using free, near-free, or local LLM options as an offload tier for Cookbook AI so the application can support more dynamic user/chat interaction without relying exclusively on the primary OpenAI `gpt-5.4-nano` path.

This ADR should also examine whether QMD-style local hybrid retrieval could reduce provider calls, improve chat responsiveness, and support a richer conversational experience while preserving the current safety, cost, and modularity boundaries.

This is docs/architecture/research only. Do not implement provider runtime, QMD runtime, routing, auth, payment, analytics, or public exposure in this task.

## Context

Current product direction after `0032A`:

1. main effort: manual validation of AI sidecar + Vanilla Cookbook integration and production usability;
2. session timer and access exceptions;
3. SSO and BYOS identity/storage architecture;
4. traffic/user behavior analytics;
5. marketing/community outreach ADR;
6. ads/sponsors/monetization ADR.

This task is a related future architecture investigation. It must not displace `0033A` as the next main usability-validation effort.

The operator wants to investigate whether a free-tier model layer could:

- offload API calls from OpenAI `gpt-5.4-nano`;
- allow more chat/discussion turns for free-tier users;
- reduce cost pressure for public usage;
- combine with QMD/local retrieval so simple or retrieval-heavy interactions do not always require hosted OpenAI calls;
- make the AI/chat interface feel more dynamic while still preserving accurate final answers and safe provider boundaries.

The operator supplied candidate examples and routes such as GLM-family models, Gemma-style local models, Groq free tier, DeepSeek/MiniMax/Gemini-style free or near-free options, Cloudflare Workers AI, Zhipu AI native APIs, and OpenRouter-style OpenAI-compatible endpoints. Treat these as hypotheses to verify, not accepted facts.

## Required Work

### 1. Read current architecture and provider docs

Read:

```text
docs/product-priority-roadmap-after-0032A.md
docs/cookbook-ai-plugin-adapter-architecture-adr.md
docs/qmd-local-hybrid-retrieval-adapter-spike.md
docs/ai-secondary-provider-fact-register.md
docs/ai-secondary-provider-implementation-gate.md
docs/ai-sidecar-architecture.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/ai-live-demo-runbook.md
docs/live-openai-smoke-tests.md
docs/live-openai-demo-evals.md
outbox/0031D-qmd-local-hybrid-retrieval-adapter-spike-results.md
outbox/0032A-portfolio-platform-aws-scaling-architecture-adr-results.md
```

Use these as the source of truth for the current provider boundary, fact gate, plugin/adapter boundary, QMD candidate status, and mock/offline validation posture.

### 2. Verify external model/provider facts

If internet access is available, verify current public facts from primary or reputable sources for any provider/model claims used in the ADR.

Investigate at least these categories when possible:

- provider/model availability;
- whether a free tier actually exists;
- whether free-tier terms permit this kind of public app usage;
- API compatibility, including OpenAI-compatible endpoints if claimed;
- rate limits, quota, latency, region, privacy, retention, and data-use terms;
- model input/output limits;
- structured output / JSON reliability;
- pricing after free tier exhaustion;
- license implications for open-weight or local models;
- operational risk and support maturity.

Candidate examples from the operator may include:

```text
GLM-family / Zhipu AI options
Cloudflare Workers AI-hosted models
OpenRouter-hosted model routing
Gemini free-tier / Google AI Studio options
Groq free tier
DeepSeek flash/low-cost options
MiniMax low-cost options
Gemma/open-weight local options
other free or near-free hosted/local models that are currently well documented
```

Do not copy unverified claims into the ADR as facts. Mark unverified items as `unverified` and blocked behind the existing provider fact gate.

If internet access is not available, explicitly say so and base the ADR only on local repo docs and the operator-provided hypothesis list.

### 3. Create the ADR

Create:

```text
docs/free-tier-llm-offload-qmd-chat-adr.md
```

The ADR should cover:

- problem statement;
- why a free/near-free/local offload tier may be useful;
- why the OpenAI `gpt-5.4-nano` path remains the trusted baseline for final answers until alternatives are proven;
- how QMD/local retrieval could reduce hosted-provider calls;
- how a free-tier LLM could support longer exploratory chat without becoming the final-answer authority by default;
- task classification: what can safely be offloaded vs what must stay on the baseline model;
- provider fact verification table;
- candidate provider/model comparison table;
- integration options: direct provider adapter, OpenAI-compatible gateway, Cloudflare Workers AI, OpenRouter, local GGUF/QMD-assisted path;
- pros/cons for each integration option;
- expected cost/latency/usability tradeoffs;
- safety and quality risks;
- privacy/data-retention risks;
- abuse/rate-limit risks for free public usage;
- fallback behavior when the free tier is unavailable or exhausted;
- interaction with future session timer, SSO/BYOS, analytics, and monetization tasks;
- go/no-go criteria for any future implementation task;
- explicit non-goals.

### 4. Define offload task classes

Define a proposed policy table similar to:

```text
Allowed candidate offload tasks:
- query expansion
- title/slug suggestions
- low-risk follow-up brainstorming
- conversational clarifying questions
- draft critique that cannot become the final answer
- context compression over retrieved snippets
- QMD/local-note summarization with citations

Blocked or baseline-only tasks:
- final recipe importer JSON
- final meal-plan JSON
- medical/nutrition certainty claims
- account/security/auth decisions
- user-data deletion/export decisions
- monetization/payment/entitlement decisions
- any task requiring strong citation fidelity until evaluated
```

Use the existing secondary-provider fact gate where possible instead of inventing a parallel gate.

### 5. Define QMD-assisted chat concept

Include a design-only flow such as:

```text
User chat turn
  -> deterministic intent classifier
  -> QMD/local retrieval when available
  -> cheap/free/local model for low-risk exploration or clarification
  -> baseline OpenAI path for final structured outputs or high-risk answer classes
  -> safe response with provenance and provider/model metadata hidden from normal users unless appropriate
```

QMD remains optional and local-only until a later approved implementation task proves value.

### 6. Define free-tier user experience concept

Investigate a product policy such as:

```text
Free tier:
- more exploratory chat allowed when powered by local/QMD/free offload path;
- stricter final-answer limits;
- no user-selectable model picker;
- safe fallback when free provider unavailable;
- session timer and per-session budget remain enforceable;
- SSO/BYOS may later provide identity and persistence boundaries.
```

Do not implement the timer, SSO, BYOS, analytics, ads, or monetization in this task.

### 7. Update planning docs

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Keep the status clear: this ADR is an investigation only and does not approve runtime use of any candidate model/provider.

### 8. Add outbox report

Create:

```text
outbox/0033G-free-tier-llm-offload-qmd-chat-adr-results.md
```

Summarize:

- ADR created;
- external facts verified or limitation noted;
- candidate provider/model matrix;
- QMD-assisted chat concept;
- offload task policy;
- pros/cons;
- risks and unknowns;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Free-tier/offload LLM ADR exists.
- ADR treats all provider/model claims as verified, unverified, or blocked behind a fact gate.
- ADR explains how offload could reduce OpenAI `gpt-5.4-nano` usage without replacing the trusted baseline prematurely.
- ADR defines how QMD/local retrieval could support dynamic chat while preserving citations/provenance.
- ADR defines allowed vs blocked task classes for offload.
- ADR includes pros/cons for direct provider APIs, OpenAI-compatible gateways, Cloudflare Workers AI-style hosted options, OpenRouter-style routing, and local/open-weight options when supported by current facts.
- ADR preserves no user-selectable model picker unless a future task explicitly approves one.
- ADR preserves mock/offline validation and live/provider fact gates.
- No provider SDK, runtime adapter, QMD dependency, Node/Bun/native dependency, model download, generated index, browser automation, live OpenAI call, or production route is added.
- No secrets, prompts, provider outputs, local env values, screenshots, traces, raw datasets, or generated artifacts are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

If the full validator is too expensive for this design-only task, run available doc/static checks and record the limitation honestly in the outbox.

Do not run live OpenAI during normal validation.
Do not run external provider calls during normal validation.

## Non-Goals

- no runtime provider integration;
- no provider SDK;
- no OpenRouter/Cloudflare/Zhipu/Groq/Gemini/DeepSeek/MiniMax runtime adapter;
- no QMD install;
- no Node/Bun/native dependency;
- no model downloads;
- no vector DB or embeddings implementation;
- no generated indexes or snapshots;
- no model picker;
- no SSO/BYOS implementation;
- no session timer implementation;
- no analytics implementation;
- no ads/monetization implementation;
- no AWS/platform work;
- no public route exposure;
- no production auth/payment;
- no live OpenAI calls;
- no live calls to other providers.

## Commit

```bash
git add docs README.md outbox/0033G-free-tier-llm-offload-qmd-chat-adr-results.md

git commit -m "docs: add free tier llm offload adr"

git pull --rebase origin main

git push origin main
```
