# AI Feature Status

This matrix summarizes what is complete, how to demo it, and what evidence supports each claim. Normal validation is offline and mock-only.

For the final phase-close acceptance matrix, see [AI Feature Completion Review](ai-feature-completion-review.md).

| Feature | Status | Endpoint or Script | Proof | Notes |
| --- | --- | --- | --- | --- |
| Health/config | Complete | `GET /health`, `GET /ai/config` | pytest, mock demo | Reports readiness and non-secret provider availability. |
| Structured recipe import/create | Complete | `POST /ai/import-recipe` | pytest, offline evals, live smoke | Produces schema-validated recipe drafts from pasted notes, defaults to 4 servings in application behavior, estimates missing quantities with notes, uses bounded local dataset examples for structure/provenance when available, packs only concise relevance-ranked snippets into the provider prompt, applies anchor-aware retrieval relevance so exact dish names and core ingredients outrank broad category matches, classifies RAG support as strong/moderate/weak/none, labels weak or partial citations honestly, and strips unsupported strict-schema metadata before OpenAI structured calls. Manual live importer validation now recommends `AI_MAX_OUTPUT_TOKENS=900`. |
| Ask My Cookbook | Complete | `POST /ai/ask` | pytest, offline evals, live smoke | Retrieves saved recipes first and cites recipe IDs/titles. |
| Local dataset search | Complete | `GET /dataset/search`, `POST /dataset/search` | pytest, mock demo | Uses bounded deterministic keyword retrieval over generated fixtures. |
| Dataset normalization | Complete | dataset index internals | pytest, offline evals | Normalizes aliases, punctuation, accents, singular/plural variants, and preserved phrases for deterministic retrieval while keeping original values for display and citations. |
| Dataset Ask/RAG | Complete | `POST /dataset/ask` | pytest, offline evals, live smoke | Answers from retrieved dataset records with provenance citations. |
| Saved-recipe meal planning | Complete | `POST /ai/meal-plan` | pytest, offline evals, live smoke | Plans from selected saved recipe candidates; no DB write-back. |
| Local operator gate | Complete, local/private | `ai-api/app/ai_operator_gate.py`, protected AI routes | pytest, offline route tests | Opt-in gate compares safe token fingerprints, supports an explicit local bypass, protects importer/dataset ask/recipe-session/meal-plan workflows when enabled, and returns safe allow/block/misconfigured decisions without raw token leakage. |
| Provider-call budget guard | Complete, local/private | `ai-api/app/ai_budget_guard.py`, protected provider-backed routes | pytest, offline route tests | Centralizes per-call and per-session provider budget checks, blocks live provider calls when disabled or exhausted, records safe meter snapshots/events, and leaves mock/offline workflows zero-cost by default. |
| Invite-only demo sessions | Complete, local/private | `ai-api/app/ai_invite_sessions.py`, `POST /ai/invite/grants`, `POST /ai/invite/redeem`, invite status/get/revoke routes | pytest, offline route tests | Creates short-lived invite grants and demo sessions with one-time raw tokens, stores only safe fingerprints, enforces allowed-workflow limits, and lets protected demo routes accept invite session tokens when invite sessions are enabled. |
| Local usage report prototype | Complete, local/private | `ai-api/app/ai_usage_report.py`, `GET /ai/admin/usage-report`, local demo card | pytest, offline route tests | Summarizes safe process-local sessions, grants, meter events, budget snapshots, quality events, audit events, and threshold warnings without exposing raw tokens, prompts, responses, or local paths. |
| 29/30 integrated regression harness | Complete, local/private | `scripts/e2e-ai-29-30-regression.py`, `scripts/run-ai-29-30-regression.ps1` | pytest, offline regression harness | Locks the 0029/0030 baseline with offline mock coverage for operator gate, invite sessions, protected workflows, budget guard, usage reporting, route exposure, and monetization boundaries, while keeping live-smoke checks opt-in only. |
| Public route exposure review | Complete, local/private | [AI Public Route Exposure Review](ai-public-route-exposure-review.md) | pytest, offline route tests | Inventories the AI route surface, classifies public/local/invite/operator/never-public exposure, and documents proxy and CORS boundaries before any public AI route exposure. |
| Monetization and entitlement boundary ADR | Complete, docs-only | [AI Monetization And Entitlement Boundary ADR](ai-monetization-and-entitlement-boundary-adr.md) | docs-only tests, repository validation | Defines the near-term ads/sponsors/partner-placement revenue path, keeps paid access out of scope for now, and preserves future entitlement seams without runtime enforcement. |
| Secondary provider offload ADR and eval harness | Complete, docs-only | [AI Secondary Provider Offload ADR](ai-secondary-provider-offload-adr.md), `evals/ai_cookbook/secondary_provider_offload_eval.py` | docs-only tests, offline eval harness | Treats `GLM-4.7 Flash` as a candidate name only, keeps secondary/offload behavior disabled by default, limits future offload ideas to advisory low-risk task classes, and rejects blocked or unsafe simulated outputs without adding runtime routing. |
| Bounded input quality | Complete | importer, Ask, dataset search/RAG, meal planning | pytest, offline evals | Rejects unusable input before provider calls, asks at most one clarification question for recoverable vague input, and lets weak usable input proceed with warnings. |
| Offline eval harness | Complete | `evals/ai_cookbook/run_evals.py` | repository validation | Checks citations, no-match behavior, schema validity, and secret-like leakage. |
| Retrieval relevance eval harness | Complete | `evals/ai_cookbook/run_evals.py` | offline eval tests | Deterministically scores importer retrieval relevance against generated distractor fixtures, including top-1 dish match, top-k material relevance, anchor coverage, and weak-match warnings. |
| Recipe-session eval harness | Complete | `evals/ai_cookbook/session_eval.py`, `evals/ai_cookbook/session_cases.yaml` | offline eval tests, `run_evals.py` | Regression-tests start/message/get/finalize session flows with generated fixtures and mock provider, including clarification, RAG refresh, no-refresh chatter/formatting, demo finalize, finalize-without-draft, equipment/exclusion refreshes, missing-session safety, and leakage checks. |
| Manual OpenAI smoke | Complete, manual-only | `scripts/smoke-openai-live.py`, `scripts/demo-ai-live-smoke.ps1` | recorded manual run | Requires explicit opt-in, API key, token cap, and budget cap. |
| Importer live diagnostic | Complete, manual-only | `scripts/smoke-openai-importer-live.py`, `scripts/smoke-openai-importer-live.ps1` | offline smoke tests | Runs importer-only live checks without the browser, prints safe counts and classifications, and supports token/timeout/provider-debug overrides. |
| Live OpenAI demo evals | Complete, manual-only | `scripts/run-openai-demo-evals.ps1` | offline harness tests; first GPT-nano baseline; post-0028B 6/6 acceptance run | Requires explicit opt-in and writes ignored metrics/results under `.tmp-ai-demo/live-evals/`. Includes usefulness checks, tuned importer ingredient-evidence checks, calibrated importer step scoring with aggregate conciseness metrics and short context-phrase handling, importer-only live output caps, importer-specific token thresholds, sanitized provider failure categories, latency/token thresholds, and GPT-nano cost estimates with `cost_source`. |
| Strict OpenAI structured schema | Complete | provider harness | offline fake-client tests | Normalizes Pydantic schemas for strict structured outputs, strips unsupported metadata like `default`/`examples`/`title`/`description`, keeps `additionalProperties=false`, and keeps strict required-property behavior. |
| Mock demo path | Complete | `scripts/demo-ai-mock.ps1` | local script validation | Runs offline evals and endpoint checks with generated fixtures. |
| Local browser demo launch | Complete | `scripts/start-ai-demo-local.ps1` | pytest, mock demo | Seeds generated saved recipes and dataset fixtures, starts `/demo` on `127.0.0.1:8000`. Defaults to mock, supports intentional `-Provider openai -EnableLiveTests`, plus dataset/time-limit/provider-debug overrides for full local RAG testing, respects existing env vars unless explicit parameters override them, and prints only a safe startup summary. OpenAI manual launch defaults to `AI_MAX_OUTPUT_TOKENS=900`. |
| REST examples | Complete | `scripts/demo-ai-requests.http` | docs/examples | Manual request examples for portfolio walkthroughs. |
| Sidecar demo UI | Complete | `GET /demo`, `GET /demo/ai`, `GET /demo/readiness` | TestClient UI/readiness tests | Guided browser page exercises existing endpoints without upstream UI rewrite. |
| Structured sidecar logging | Complete | stdout JSON logs | TestClient logging tests | Logs safe request/workflow metadata, including UI workflow labels. Optional `AI_PROVIDER_DEBUG=true` adds sanitized local provider error category/type/summary without logging secrets, raw prompts, or raw provider responses. |
| Production access and metering architecture | Proposed | docs only | `docs/production-access-metering-architecture.md` | Designs gated access, time-limited sessions, metering, cost controls, threat model, and paid-access boundary. No runtime auth, billing, public live AI exposure, migrations, or route changes are implemented. |
| Session and metering schema scaffold | Complete, schema-only | `ai-api/app/ai_access_models.py`, [AI Session Metering Schema](ai-session-metering-schema.md) | `test_ai_access_models.py` | Defines safe offline models for demo sessions, access grants, provider meter events, quality events, admin audit events, and budget snapshots. No runtime auth, storage, budget enforcement, invite flow, billing, or public access is implemented. |
| Live script env-file loader | Complete, manual-only | `scripts/lib/ai-env-file.ps1`, `scripts/test-ai-env-file-loader.ps1` | PowerShell script test, pytest docs check | Loads ignored local `.env` files explicitly through the wrappers, preserves comments and existing values, appends only safe missing defaults, and redacts secret-like names in summaries. |

## Recorded Live Smoke

```text
provider=openai
model=gpt-5.4-nano
live_calls=4
estimated_usage_tokens=1200
workflows=importer,ask_my_cookbook,dataset_ask,meal_plan
budget_cents=25
status=passed
```

## Current Boundaries

| Boundary | Status | Reason |
| --- | --- | --- |
| Production AI storage | Not implemented | Kept out of scope until a dedicated architecture task. |
| Production AI access layer | Proposed, not implemented | Public live provider-backed AI requires auth/session/metering work first. |
| Public unauthenticated live AI endpoint | Not allowed | Provider-backed endpoints must be protected before public exposure. |
| Payment integration | Deferred | Paid access requires a later ADR and implementation task after the monetization/entitlement boundary ADR. |
| Embeddings/vector DB | Not implemented | Deterministic retrieval is enough for the current demo and eval scope. |
| Qdrant/Postgres/pgvector | Not implemented | Avoids unnecessary infrastructure for this feature slice. |
| Persistent generated indexes | Not implemented | Dataset indexes are request-time/in-memory only. |
| UI rewrite | Not implemented | The portfolio focus is sidecar/API behavior and validation. |
| Live provider calls in CI | Not implemented | Live calls remain manual-only to control cost and reliability. |
| Raw dataset commits | Not allowed | `recipe-dataset/` remains ignored. |
| Private env/provider keys | Not allowed | `.env` and secrets stay untracked. |

## Current Acceptance Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Mock demo | Pass | `scripts/demo-ai-mock.ps1` |
| Seeded local UI demo | Pass | generated fixtures |
| Live OpenAI eval | Pass | post-`0028B` 6/6 run |
| Cost estimate | Pass | `default_model_rate` cost populated |
| Latency thresholds | Pass | 0 warnings / 0 failures |
| Token thresholds | Pass | 0 warnings / 0 failures |
| Input quality guardrails | Pass | `0028A` offline tests |
| Importer eval robustness | Pass | `0028B` tests plus post-fix live pass |
| Retrieval relevance regression checks | Pass | deterministic offline eval harness |
| Dataset normalization | Pass | deterministic helper tests plus normalization-sensitive retrieval cases |
| Retrieval context packing | Pass | bounded prompt packer tests plus importer metadata/UI checks |
| RAG support honesty policy | Pass | deterministic support classification tests plus importer metadata/UI checks |
| Local retrieval cache | Pass | deterministic cache hit/miss tests plus safe fingerprint metadata |
| RAG importer E2E integration | Pass | real `/ai/import-recipe` route test with generated dataset fixtures and mock provider |
| Requirements/session interaction architecture | Proposed | `docs/recipe-session-requirements-architecture.md`; designs requirement extraction, clarification, session state, delta detection, and RAG refresh policy without runtime endpoints or persistent memory |
| Requirements/session alpha scaffold | Complete, internal-only | deterministic unit tests | Adds requirements state models, conservative extraction, confidence labels, clarification decisions, follow-up delta classification, RAG refresh decisions, and a bounded process-local session store. Not wired to public endpoints. |
| Recipe-session alpha API | Complete, local alpha | `POST /ai/recipe-session/start`, `POST /ai/recipe-session/{id}/message`, `GET /ai/recipe-session/{id}`, `POST /ai/recipe-session/{id}/finalize` | Wires the requirements scaffold into local/offline session endpoints, reuses the importer/RAG pipeline for draft generation, and stores only bounded in-memory demo state. Not production storage or public access. |
| Recipe-session alpha demo UI | Complete, local alpha | `GET /demo`, `scripts/demo-ai-mock.ps1` | Adds a compact operator panel for start/message/get/finalize/reset, interpreted requirements, clarification, RAG refresh/no-refresh status, draft summaries, citations, and demo-only finalize. Mock smoke validation exercises the endpoint flow offline. |
| Recipe-session regression baseline | Pass | 11 deterministic session eval cases in `run_evals.py`; 39 total offline eval cases | Covers draft generation, clarification, method/equipment/exclusion RAG refresh, chatter/formatting no-refresh, clarification answer, demo finalize, finalize-before-draft, and missing-session safety with generated fixtures only. |
| Recipe-session alpha acceptance | Complete, local alpha | [Recipe Session Alpha Acceptance Runbook](recipe-session-alpha-acceptance-runbook.md), `scripts/demo-ai-mock.ps1` | Hardens API response safety, UI messaging, edge-case tests, mock smoke behavior, and operator runbook boundaries for local demos. |
| Provider-call avoidance | Pass | rejected and clarification paths tested offline |
| Local live importer diagnostics | Pass | offline sanitizer tests plus runbook diagnostic and dedicated importer smoke script |
| Local operator gate | Pass | helper and route tests | Gate is disabled by default, uses safe fingerprints and a local bypass, and keeps offline/mock validation unchanged unless explicitly enabled. |
| Provider-call budget guard | Pass | helper and route tests | Budget settings are opt-in, fail closed for invalid live config, treat mock calls as zero-cost, and block live provider calls before invocation when the demo is globally disabled or caps are exceeded. |
| Invite-only demo sessions | Pass | helper, route, and store tests | Invite grants can be created, redeemed, expired, revoked, and inspected safely; invite session tokens allow protected workflows when enabled, while one-time raw tokens stay out of status views and safe serialization. |
| Local usage report prototype | Pass | helper, route, and UI tests | The local/operator usage report stays process-local and safe, summarizes grant/session/meter/budget/quality/audit state, and is protected by the operator gate when enabled. |
| 29/30 integrated regression harness | Pass | offline regression script and wrapper | The combined baseline harness exercises operator gate, invite sessions, budget guard, usage reporting, route exposure assumptions, and recipe-session alpha behavior without enabling GLM or payment runtime behavior by default. |
| Secondary provider offload review baseline | Pass, docs-only | ADR plus offline offload eval harness | The current OpenAI baseline remains `gpt-5.4-nano` final-answer generation, while secondary-provider ideas are evaluated offline as advisory-only candidates with no runtime routing or live GLM calls. |

## Demo Starting Points

- [AI Portfolio Showcase](ai-portfolio-showcase.md)
- [AI Feature Completion Review](ai-feature-completion-review.md)
- [AI Demo Walkthrough](ai-demo-walkthrough.md)
- [AI Live Demo Runbook](ai-live-demo-runbook.md)
- [AI UI Integration Plan](ai-ui-integration-plan.md)
- [AI Sidecar Logging](ai-sidecar-logging.md)
- [Manual Live OpenAI Smoke Tests](live-openai-smoke-tests.md)
- [Live OpenAI Demo Evals](live-openai-demo-evals.md)
- [Live OpenAI Demo Baseline: 2026-07-07](live-openai-demo-baseline-2026-07-07.md)
- [Live OpenAI Demo Regression Notes: 2026-07-08](live-openai-demo-regression-notes-2026-07-08.md)
- [Production Access Metering Architecture](production-access-metering-architecture.md)
- [AI Production Readiness Roadmap](ai-production-readiness-roadmap.md)
- [AI Session Metering Data Model](ai-session-metering-data-model.md)
- [AI Session Metering Schema](ai-session-metering-schema.md)
- [AI Access Control Threat Model](ai-access-control-threat-model.md)
- [Recipe Session Requirements Architecture](recipe-session-requirements-architecture.md)
- [Recipe Session Alpha Acceptance Runbook](recipe-session-alpha-acceptance-runbook.md)
- [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md)
