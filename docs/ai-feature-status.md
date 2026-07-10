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
| Bounded input quality | Complete | importer, Ask, dataset search/RAG, meal planning | pytest, offline evals | Rejects unusable input before provider calls, asks at most one clarification question for recoverable vague input, and lets weak usable input proceed with warnings. |
| Offline eval harness | Complete | `evals/ai_cookbook/run_evals.py` | repository validation | Checks citations, no-match behavior, schema validity, and secret-like leakage. |
| Retrieval relevance eval harness | Complete | `evals/ai_cookbook/run_evals.py` | offline eval tests | Deterministically scores importer retrieval relevance against generated distractor fixtures, including top-1 dish match, top-k material relevance, anchor coverage, and weak-match warnings. |
| Manual OpenAI smoke | Complete, manual-only | `scripts/smoke-openai-live.py`, `scripts/demo-ai-live-smoke.ps1` | recorded manual run | Requires explicit opt-in, API key, token cap, and budget cap. |
| Importer live diagnostic | Complete, manual-only | `scripts/smoke-openai-importer-live.py`, `scripts/smoke-openai-importer-live.ps1` | offline smoke tests | Runs importer-only live checks without the browser, prints safe counts and classifications, and supports token/timeout/provider-debug overrides. |
| Live OpenAI demo evals | Complete, manual-only | `scripts/run-openai-demo-evals.ps1` | offline harness tests; first GPT-nano baseline; post-0028B 6/6 acceptance run | Requires explicit opt-in and writes ignored metrics/results under `.tmp-ai-demo/live-evals/`. Includes usefulness checks, tuned importer ingredient-evidence checks, latency/token thresholds, and GPT-nano cost estimates with `cost_source`. |
| Strict OpenAI structured schema | Complete | provider harness | offline fake-client tests | Normalizes Pydantic schemas for strict structured outputs, strips unsupported metadata like `default`/`examples`/`title`/`description`, keeps `additionalProperties=false`, and keeps strict required-property behavior. |
| Mock demo path | Complete | `scripts/demo-ai-mock.ps1` | local script validation | Runs offline evals and endpoint checks with generated fixtures. |
| Local browser demo launch | Complete | `scripts/start-ai-demo-local.ps1` | pytest, mock demo | Seeds generated saved recipes and dataset fixtures, starts `/demo` on `127.0.0.1:8000`. Defaults to mock, supports intentional `-Provider openai -EnableLiveTests`, plus dataset/time-limit/provider-debug overrides for full local RAG testing, respects existing env vars unless explicit parameters override them, and prints only a safe startup summary. OpenAI manual launch defaults to `AI_MAX_OUTPUT_TOKENS=900`. |
| REST examples | Complete | `scripts/demo-ai-requests.http` | docs/examples | Manual request examples for portfolio walkthroughs. |
| Sidecar demo UI | Complete | `GET /demo`, `GET /demo/ai`, `GET /demo/readiness` | TestClient UI/readiness tests | Guided browser page exercises existing endpoints without upstream UI rewrite. |
| Structured sidecar logging | Complete | stdout JSON logs | TestClient logging tests | Logs safe request/workflow metadata, including UI workflow labels. Optional `AI_PROVIDER_DEBUG=true` adds sanitized local provider error category/type/summary without logging secrets, raw prompts, or raw provider responses. |
| Production access and metering architecture | Proposed | docs only | `docs/production-access-metering-architecture.md` | Designs gated access, time-limited sessions, metering, cost controls, threat model, and paid-access boundary. No runtime auth, billing, public live AI exposure, migrations, or route changes are implemented. |

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
| Payment integration | Deferred | Paid access requires a later ADR and entitlement design. |
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
| Provider-call avoidance | Pass | rejected and clarification paths tested offline |
| Local live importer diagnostics | Pass | offline sanitizer tests plus runbook diagnostic and dedicated importer smoke script |

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
- [AI Access Control Threat Model](ai-access-control-threat-model.md)
- [Recipe Session Requirements Architecture](recipe-session-requirements-architecture.md)
- [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md)
