# AI Feature Status

This matrix summarizes what is complete, how to demo it, and what evidence supports each claim. Normal validation is offline and mock-only.

For the final phase-close acceptance matrix, see [AI Feature Completion Review](ai-feature-completion-review.md).

| Feature | Status | Endpoint or Script | Proof | Notes |
| --- | --- | --- | --- | --- |
| Health/config | Complete | `GET /health`, `GET /ai/config` | pytest, mock demo | Reports readiness and non-secret provider availability. |
| Structured recipe importer | Complete | `POST /ai/import-recipe` | pytest, offline evals, live smoke | Produces schema-validated recipe drafts from pasted text. |
| Ask My Cookbook | Complete | `POST /ai/ask` | pytest, offline evals, live smoke | Retrieves saved recipes first and cites recipe IDs/titles. |
| Local dataset search | Complete | `GET /dataset/search`, `POST /dataset/search` | pytest, mock demo | Uses bounded deterministic keyword retrieval over generated fixtures. |
| Dataset Ask/RAG | Complete | `POST /dataset/ask` | pytest, offline evals, live smoke | Answers from retrieved dataset records with provenance citations. |
| Saved-recipe meal planning | Complete | `POST /ai/meal-plan` | pytest, offline evals, live smoke | Plans from selected saved recipe candidates; no DB write-back. |
| Offline eval harness | Complete | `evals/ai_cookbook/run_evals.py` | repository validation | Checks citations, no-match behavior, schema validity, and secret-like leakage. |
| Manual OpenAI smoke | Complete, manual-only | `scripts/smoke-openai-live.py`, `scripts/demo-ai-live-smoke.ps1` | recorded manual run | Requires explicit opt-in, API key, token cap, and budget cap. |
| Strict OpenAI structured schema | Complete | provider harness | offline fake-client tests | Normalizes Pydantic schemas for strict structured outputs. |
| Mock demo path | Complete | `scripts/demo-ai-mock.ps1` | local script validation | Runs offline evals and endpoint checks with generated fixtures. |
| REST examples | Complete | `scripts/demo-ai-requests.http` | docs/examples | Manual request examples for portfolio walkthroughs. |

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
| Embeddings/vector DB | Not implemented | Deterministic retrieval is enough for the current demo and eval scope. |
| Qdrant/Postgres/pgvector | Not implemented | Avoids unnecessary infrastructure for this feature slice. |
| Persistent generated indexes | Not implemented | Dataset indexes are request-time/in-memory only. |
| UI rewrite | Not implemented | The portfolio focus is sidecar/API behavior and validation. |
| Live provider calls in CI | Not implemented | Live calls remain manual-only to control cost and reliability. |
| Raw dataset commits | Not allowed | `recipe-dataset/` remains ignored. |
| Private env/provider keys | Not allowed | `.env` and secrets stay untracked. |

## Demo Starting Points

- [AI Portfolio Showcase](ai-portfolio-showcase.md)
- [AI Feature Completion Review](ai-feature-completion-review.md)
- [AI Demo Walkthrough](ai-demo-walkthrough.md)
- [Manual Live OpenAI Smoke Tests](live-openai-smoke-tests.md)
- [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md)
