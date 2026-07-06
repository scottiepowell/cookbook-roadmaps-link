# AI Demo Walkthrough

This walkthrough is for portfolio, interview, or customer conversations. It shows the AI sidecar as an offline-first cookbook assistant with optional live OpenAI validation.

For a higher-level summary, start with [AI Portfolio Showcase](ai-portfolio-showcase.md). For final acceptance evidence, use [AI Feature Completion Review](ai-feature-completion-review.md). For a 15 to 30 minute operator script, use [AI Live Demo Runbook](ai-live-demo-runbook.md). For future visual assets, use [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md).

## Demo Paths

Use the browser demo UI when the AI sidecar is running locally:

```text
http://127.0.0.1:8000/demo
```

The page is served by the sidecar because this repository does not include the upstream Vanilla Cookbook frontend source tree. It exercises readiness, health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal planning through existing API endpoints. It includes sample inputs, reset buttons, loading states, answer cards, citations/provenance, warnings, and raw JSON details.

Use the mock/offline path for normal demos:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
.\scripts\demo-ai-mock.ps1
```

The script runs the offline eval harness plus focused API tests for health/config, importer, Ask My Cookbook, dataset search, dataset ask, and meal planning. It does not need provider keys, Docker, the real Kaggle dataset, or a production Vanilla Cookbook database.

Use the live smoke path only when you intentionally want to prove the OpenAI provider path:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_ENABLE_LIVE_TESTS="true"
$env:OPENAI_LIVE_TEST_BUDGET_CENTS="25"
$env:AI_MAX_OUTPUT_TOKENS="200"
# OPENAI_API_KEY should already be in local .env or process env, never committed.
.\scripts\demo-ai-live-smoke.ps1
```

REST examples live in `scripts/demo-ai-requests.http`. They assume an AI API server is already running at `http://127.0.0.1:8000`; the file is for manual request clients and is not a launch workflow.

Sidecar logs are structured JSON on stdout. See [AI Sidecar Logging](ai-sidecar-logging.md) for safe fields and local viewing commands.

## Five-Minute Talk Track

Minute 1: Problem and shape.
This is a Vanilla Cookbook GitOps lab with a FastAPI AI sidecar. The AI layer is intentionally offline-first: normal validation uses generated fixtures and a deterministic mock provider, so the repository stays cheap, repeatable, and safe.

Minute 2: Core user workflows.
The sidecar can turn pasted recipe text into a structured draft, answer questions over saved recipes with citations, search a bounded local recipe dataset, answer questions over retrieved dataset records with Kaggle provenance, and create meal plans from saved recipe candidates.

Minute 3: Grounding and data boundaries.
Ask My Cookbook retrieves saved recipes first and sends only retrieved context to the provider. Dataset Ask searches a bounded in-memory index first and cites source IDs, source files, license, and source URL. There are no embeddings, vector DB, persistent generated indexes, production writes, or raw dataset commits.

Minute 4: Validation story.
Offline evals cover dataset ask, saved-recipe ask, importer, meal plan, provider config hygiene, citations, and secret-like leakage checks. Repository validation runs pytest plus evals without provider keys. The live OpenAI smoke path is manual-only and guarded by explicit opt-in variables and a 25-cent budget cap.

Minute 5: Operational maturity.
The project documents data boundaries, validation behavior, live smoke interpretation, and Windows cleanup handling. The most recent manual live smoke passed using `gpt-5.4-nano` across importer, saved-recipe ask, dataset ask, and meal plan with four live calls.

## Suggested Demo Order

1. Open [AI Portfolio Showcase](ai-portfolio-showcase.md) and summarize the architecture.
2. Open [AI Feature Completion Review](ai-feature-completion-review.md) for the acceptance matrix.
3. Open [AI Feature Status](ai-feature-status.md) and show the feature matrix.
4. Open `http://127.0.0.1:8000/demo` if the sidecar is running.
5. Follow [AI Live Demo Runbook](ai-live-demo-runbook.md) for the 15 or 30 minute flow.
6. Run `.\scripts\demo-ai-mock.ps1`.
7. Show `evals/ai_cookbook/workflow_cases.json` for fixture-based workflow coverage.
8. Open `scripts/demo-ai-requests.http` and walk through the REST endpoints.
9. Show [Manual Live OpenAI Smoke Tests](live-openai-smoke-tests.md) and the recorded passing live output.
10. Use [AI Screenshot Capture Guide](ai-screenshot-capture-guide.md) if visual proof is needed later.

## What Not To Claim

- This does not implement production AI storage architecture.
- This does not add embeddings, Qdrant, Postgres, pgvector, or a vector database.
- This does not import the Kaggle dataset into Vanilla Cookbook.
- This does not persist generated indexes.
- This does not add live provider calls to CI.
- This does not rewrite the Vanilla Cookbook UI.
- This does not add external logging infrastructure.
