# AI Feature Status

| Feature | Status | Demo Path | Validation |
| --- | --- | --- | --- |
| Health/config | Complete | `GET /health`, `GET /ai/config` | pytest and mock demo |
| Structured recipe importer | Complete | `POST /ai/import-recipe` | pytest, offline evals, live smoke |
| Ask My Cookbook over saved recipes | Complete | `POST /ai/ask` | pytest, offline evals, live smoke |
| Saved-recipe meal planning | Complete | `POST /ai/meal-plan` | pytest, offline evals, live smoke |
| Local dataset search | Complete | `GET /dataset/search`, `POST /dataset/search` | pytest and mock demo |
| Dataset Ask/RAG | Complete | `POST /dataset/ask` | pytest, offline evals, live smoke |
| Offline eval harness | Complete | `evals/ai_cookbook/run_evals.py` | repository validation |
| Manual OpenAI smoke | Complete, manual-only | `scripts/smoke-openai-live.py` | recorded manual run |
| OpenAI strict structured schema | Complete | provider harness | offline fake-client tests |
| Production AI storage | Not implemented | out of scope | documented boundary |
| Embeddings/vector DB | Not implemented | out of scope | documented boundary |
| UI rewrite | Not implemented | out of scope | documented boundary |

## Current Boundaries

- The mock provider remains the default for tests, evals, and CI.
- Live OpenAI validation is opt-in only and capped by guardrails.
- Dataset fixtures are generated and tiny; raw `recipe-dataset/` content stays ignored.
- Dataset indexes are in-memory request-time structures and are not persisted.
- Saved-recipe workflows read generated SQLite fixtures or configured cookbook data and do not write back.

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
