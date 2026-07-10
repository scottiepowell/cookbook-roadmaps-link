# Vanilla Cookbook GitOps Lab

This mailbox-driven DevOps lab deploys Vanilla Cookbook to AWS EC2 at [cookbook.roadmaps.link](https://cookbook.roadmaps.link). Coder and Codex handle reviewed tasks, GitHub stores desired state, and GitHub Actions operates EC2 through AWS Systems Manager.

## AI Cookbook Showcase

This repo now includes a portfolio-ready AI cookbook sidecar: Vanilla Cookbook remains the source app, while a FastAPI `ai-api` service provides offline-first AI workflows for structured recipe import, saved-recipe Q&A, deterministic local dataset search/RAG, and saved-recipe meal planning. The architecture is intentionally conservative: retrieval happens before provider calls, responses carry citations/provenance, normal validation uses generated fixtures and the mock provider, and live OpenAI calls are manual-only.

Completed AI workflows:

- Structured recipe import/create: `POST /ai/import-recipe` returns schema-validated recipe drafts from pasted notes, defaults to 4 servings, estimates missing quantities, and uses local dataset examples for structure/provenance when available.
- Ask My Cookbook: `POST /ai/ask` answers over saved recipes with recipe citations.
- Dataset search/RAG: `GET/POST /dataset/search` and `POST /dataset/ask` use bounded local dataset fixtures with provenance citations.
- Meal planning: `POST /ai/meal-plan` builds plans from saved recipe candidates.
- Bounded input quality: weak or vague input gets deterministic warnings or one clarification question, while empty or nonsensical input is rejected before provider calls.
- Sidecar demo UI: `GET /demo` and `GET /demo/ai` serve a lightweight browser demo for completed AI workflows, including the local Recipe Session Alpha panel.
- Provider harness: mock provider by default, OpenAI path available only through explicit manual opt-in.

Validation proof:

- Offline evals cover dataset ask, saved-recipe ask, importer, meal plan, recipe-session alpha flows, provider config hygiene, citations, and secret-like leakage checks.
- Retrieval relevance evals now regression-test importer ranking against deterministic cheesecake, carbonara, omelet, and chicken/rice casserole distractor fixtures.
- Repository validation runs pytest and offline evals without provider keys, Docker-only services, the real Kaggle dataset, or a production cookbook database.
- Manual live OpenAI smoke validation passed with `provider=openai`, `model=gpt-5.4-nano`, `live_calls=4`, `estimated_usage_tokens=1200`, `workflows=importer,ask_my_cookbook,dataset_ask,meal_plan`, `budget_cents=25`, `status=passed`.
- Live GPT-nano demo eval acceptance is current through the post-`0028B` `2026-07-08` run: 6/6 workflows passed, `default_model_rate` cost populated, and latency/token thresholds had 0 warnings and 0 failures. A post-`0028A` importer false failure is preserved as sanitized regression evidence.

Demo and evidence links:

- [AI portfolio showcase](docs/ai-portfolio-showcase.md)
- [AI feature completion review](docs/ai-feature-completion-review.md)
- [AI UI integration plan](docs/ai-ui-integration-plan.md)
- [AI sidecar logging](docs/ai-sidecar-logging.md)
- [AI live demo runbook](docs/ai-live-demo-runbook.md)
- [Live OpenAI demo evals](docs/live-openai-demo-evals.md)
- [Live OpenAI GPT-nano baseline](docs/live-openai-demo-baseline-2026-07-07.md)
- [Live OpenAI regression notes](docs/live-openai-demo-regression-notes-2026-07-08.md)
- [Production access metering architecture](docs/production-access-metering-architecture.md)
- [AI session metering schema](docs/ai-session-metering-schema.md)
- [AI provider budget enforcement](docs/ai-provider-budget-enforcement.md)
- [AI production readiness roadmap](docs/ai-production-readiness-roadmap.md)
- [Recipe session requirements architecture](docs/recipe-session-requirements-architecture.md)
- [Recipe Session Alpha acceptance runbook](docs/recipe-session-alpha-acceptance-runbook.md)
- [AI invite-only demo session flow](docs/ai-invite-only-demo-session-flow.md)
- [AI demo walkthrough](docs/ai-demo-walkthrough.md)
- [AI feature status](docs/ai-feature-status.md)
- [REST request examples](scripts/demo-ai-requests.http)
- [AI evals plan](docs/ai-evals-plan.md)
- [Manual live OpenAI smoke tests](docs/live-openai-smoke-tests.md)
- [AI screenshot capture guide](docs/ai-screenshot-capture-guide.md)

Run the safe mock demo:

```powershell
.\scripts\demo-ai-mock.ps1
```

Start the local browser demo with generated demo-safe saved recipes and dataset fixtures:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

Then open `http://127.0.0.1:8000/demo` for the guided browser demo UI.

For intentional live OpenAI manual demo mode, keep `OPENAI_API_KEY` in the local environment and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Optional bounded live overrides:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests -OpenAIModel gpt-5.4-nano -MaxOutputTokens 900 -LiveTestBudgetCents 25 -Port 8001
```

Full local RAG manual importer launch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

The start script defaults to mock mode, respects existing provider environment variables unless explicit parameters override them, and never prints API keys or environment file contents. `AI_PROVIDER_DEBUG=true` is opt-in and only adds sanitized local provider diagnostics such as error category, exception type, and a short redacted summary. It does not log API keys, Authorization headers, raw prompts, raw provider responses, `.env` contents, or secret-like strings.

The generated `.tmp-ai-demo` fixture dataset still only contains three records, so citation/provenance quality there is useful for smoke tests but not for meaningful RAG evaluation. Use the full `recipe-dataset` path for manual importer validation.

Importer-only diagnostic without the browser:

```powershell
$body = @{
  text = "omelet with eggs cheese maybe onions cooked in butter fold it over"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ai/import-recipe -ContentType "application/json" -Body $body |
  ConvertTo-Json -Depth 8
```

For a script-based importer smoke test with safe success/failure summaries, run `scripts\smoke-openai-importer-live.ps1`.

With `-ProviderDebug` enabled, local logs can distinguish timeout, schema rejection, bad model, quota/rate limit, auth, and network failures while keeping the public `503` response safe.

Run the live OpenAI demo eval wrapper only with explicit live opt-in settings:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Without opt-in settings, it skips cleanly and performs no live calls.

The first successful GPT-nano live eval baseline is recorded in [Live OpenAI Demo Baseline: 2026-07-07](docs/live-openai-demo-baseline-2026-07-07.md). The current acceptance baseline is the post-`0028B` 6/6 run recorded in [Live OpenAI Demo Regression Notes: 2026-07-08](docs/live-openai-demo-regression-notes-2026-07-08.md), after the post-`0028A` importer evaluator false failure was fixed. Future live eval runs should compare correctness, usefulness, importer ingredient preservation, latency, token use, cost visibility, and input-quality/provider-call-avoidance metrics against that acceptance history. `gpt-5.4-nano` evals use maintained default cost rates unless operator pricing env vars override them.

Normal validation is mock/offline and safe. No provider keys, raw dataset files, generated indexes, private environment files, or private recipe data are committed.

The importer now behaves as an import/create workflow for rough recipe notes. When local dataset fixtures are configured, it retrieves a small bounded set of similar recipes before the provider call and passes them as structure guidance only. The retrieval is anchor-aware, and the dataset index normalizes conservative aliases, phrases, punctuation, and singular/plural variants so exact dish names and core ingredients outrank broad category matches. Weak matches are called out in warnings, the user's ingredients and dish intent remain primary, retrieved recipes are not copied verbatim, citations/provenance are returned for transparency, estimated quantities are disclosed in notes, provider prompts receive a bounded packed snippet block instead of raw retrieved records, and the API/UI classify RAG support as strong, moderate, weak, or none so broad examples are not described as authoritative grounding.

The local dataset search/retrieval path also uses a small process-local in-memory cache so repeated requests with the same dataset limit, source metadata, normalization version, and query can reuse work without writing generated indexes to disk. The UI exposes only short fingerprints and hit/miss state.

The RAG importer path now has an offline E2E regression test that exercises the real `/ai/import-recipe` route with generated dataset fixtures and the mock provider, covering retrieval, normalization, context packing, support labels, citations, schema validation, and cache metadata together.

The next recipe-creation product layer is documented, not implemented, in [Recipe session requirements architecture](docs/recipe-session-requirements-architecture.md). It designs a session-scoped requirements state, one-question clarification policy, follow-up delta classifier, and RAG refresh rules so future revisions like `actually make it no-bake` can update requirements, refresh retrieval, and explain why citations changed. It does not add production storage, persistent user memory, auth, paid access, public route exposure, embeddings, vector databases, or a full chat UI.

The first local alpha implementation for that layer now exists in `ai-api/app/recipe_requirements.py`, `ai-api/app/recipe_session.py`, and `ai-api/app/recipe_session_routes.py`. It provides deterministic requirements extraction, confidence labels, clarification and follow-up classification, RAG refresh decisions, a bounded in-memory test/demo session store, and local `/ai/recipe-session/*` endpoints for start/message/get/finalize flows. The `/demo` UI includes a compact Recipe Session Alpha panel for starting a session, sending a follow-up, viewing RAG refresh/no-refresh state, and finalizing for demo. `evals/ai_cookbook/run_evals.py` now includes deterministic `recipe_session` cases for draft generation, clarification, method/equipment/exclusion RAG refresh, no-refresh, finalize, finalize-before-draft, missing-session safety, and leakage checks. The [Recipe Session Alpha acceptance runbook](docs/recipe-session-alpha-acceptance-runbook.md) documents the local demo checklist and boundaries. These endpoints, UI controls, evals, and runbook are offline/mock-friendly and are not production storage, auth, paid access, public access, persistent user memory, or a full chat UI.

The manual importer path now recommends `AI_MAX_OUTPUT_TOKENS=900`. The earlier 500-token cap was sufficient for small smoke tests but could truncate RAG-informed structured recipe drafts.

The live importer `503` blocker from manual testing was traced to strict structured-output schema metadata that OpenAI rejected. The schema normalizer now strips unsupported metadata such as `default`, `examples`, `title`, and `description` before the provider call, while application behavior still defaults importer servings to 4.

Production access architecture is proposed, not implemented. Before any public live provider-backed AI exposure, the AI demo needs an access layer with time-limited sessions, per-call metering, provider budget enforcement, a global live-provider disable switch, protected routes, and metadata-only logging by default. The first schema-only scaffold for that future layer is in `ai-api/app/ai_access_models.py` and [AI session metering schema](docs/ai-session-metering-schema.md), covering demo sessions, access grants, meter events, quality events, audit events, and budget snapshots. Local/private invite-only demo sessions now build on those schemas in `ai-api/app/ai_invite_sessions.py`, but they remain disabled by default, process-local, and separate from production auth, billing, or public access. Payment integration is deferred, and the platform rule remains: shared infrastructure is allowed, but each demo owns its own data boundary.

The first local/private access guardrail now exists in [AI Local Operator Access Gate](docs/ai-local-operator-access-gate.md). It is disabled by default, protects importer/dataset ask/recipe-session/meal-plan workflows when enabled, and compares safe fingerprints on `X-AI-Operator-Token` or `Authorization: Bearer ...` without echoing raw tokens or local paths. The provider budget guard in [AI Provider Budget Enforcement](docs/ai-provider-budget-enforcement.md) runs after the gate and blocks live provider calls when the demo is globally disabled, caps are exceeded, or the live budget configuration is invalid.

## Architecture

GitHub Actions assumes a repository-scoped AWS role through OIDC and deploys Docker Compose through Systems Manager. Vanilla Cookbook listens only on EC2 loopback; `cloudflared` creates the outbound public route.

```text
Coder + Codex -> GitHub -> GitHub Actions --OIDC/SSM--> AWS EC2
Browser -> Cloudflare edge -> Cloudflare Tunnel -> Docker Compose -> Cookbook
```

See [Architecture](docs/architecture.md).

## Technology

Coder, Codex, GitHub, GitHub Actions, AWS EC2, AWS Systems Manager, Docker Compose, Cloudflare Tunnel, and a FastAPI AI sidecar with deterministic offline-first AI features.

## Security Model

- No inbound app HTTP/HTTPS on EC2; port 3000 binds to `127.0.0.1`.
- Cloudflare Tunnel publishes the app through an outbound connection.
- Sensitive values live in GitHub Actions secrets and a mode `0600` host `.env`.
- AWS OIDC avoids static AWS access keys.
- Routine administration uses Systems Manager, not public SSH.

## Quick Start

Follow the [First Deploy Guide](docs/first-deploy-guide.md).

- [Repository map](docs/repo-map.md)
- [AI medium-path roadmap](docs/ai-medium-path-roadmap.md)
- [AI portfolio showcase](docs/ai-portfolio-showcase.md)
- [AI feature completion review](docs/ai-feature-completion-review.md)
- [AI UI integration plan](docs/ai-ui-integration-plan.md)
- [AI sidecar logging](docs/ai-sidecar-logging.md)
- [AI live demo runbook](docs/ai-live-demo-runbook.md)
- [Live OpenAI demo evals](docs/live-openai-demo-evals.md)
- [Live OpenAI GPT-nano baseline](docs/live-openai-demo-baseline-2026-07-07.md)
- [Live OpenAI regression notes](docs/live-openai-demo-regression-notes-2026-07-08.md)
- [Production access metering architecture](docs/production-access-metering-architecture.md)
- [AI session metering schema](docs/ai-session-metering-schema.md)
- [AI production readiness roadmap](docs/ai-production-readiness-roadmap.md)
- [Recipe session requirements architecture](docs/recipe-session-requirements-architecture.md)
- [Recipe Session Alpha acceptance runbook](docs/recipe-session-alpha-acceptance-runbook.md)
- [AI invite-only demo session flow](docs/ai-invite-only-demo-session-flow.md)
- [AI session metering data model](docs/ai-session-metering-data-model.md)
- [AI access control threat model](docs/ai-access-control-threat-model.md)
- [AI sidecar architecture](docs/ai-sidecar-architecture.md)
- [AI demo walkthrough](docs/ai-demo-walkthrough.md)
- [AI feature status](docs/ai-feature-status.md)
- [AI screenshot capture guide](docs/ai-screenshot-capture-guide.md)
- [Local recipe dataset adapter](docs/local-recipe-dataset-adapter.md)
- [Shared infrastructure data boundaries](docs/shared-infrastructure-data-boundaries.md)
- [Meal planner foundation](docs/meal-planner-foundation.md)
- [AI evals plan](docs/ai-evals-plan.md)
- [Manual live OpenAI smoke tests](docs/live-openai-smoke-tests.md)
- [AI implementation backlog](docs/ai-implementation-backlog.md)
- [Resume from Windows clone](docs/resume-from-windows-clone.md)
- [Windows local development](docs/windows-local-development.md)
- [Current deployment state](docs/current-deployment-state.md)
- [Codex mailbox continuation](docs/codex-mailbox-continuation.md)
- [Repository validation](docs/repo-validation.md)
- [Runtime scaffold](docs/runtime-scaffold.md)
- [EC2 bootstrap](docs/ec2-runtime-bootstrap.md)
- [AWS OIDC policy](docs/aws-github-oidc-policy.md)
- [GitHub settings](docs/github-settings-checklist.md)
- [GitHub Actions workflow](docs/github-actions-deploy-workflow.md)
- [Cloudflare setup](docs/cloudflare-tunnel-setup.md)
- [Backup and restore](docs/backup-restore.md)
- [Operations](docs/operations-runbook.md)

## GitOps Mailbox Workflow

Numbered `inbox/` specifications drive work. Codex inspects, implements, validates, writes a matching `outbox/` report, and commits reviewed state. GitHub is the source of truth; deployments pull `main` onto EC2. Never put credentials, tokens, private keys, or host `.env` content in mailbox files.

## AI Sidecar Status

The `ai-api` service provides health/config endpoints, deterministic saved-recipe search, structured recipe import drafts, Ask My Cookbook RAG over saved recipes, a saved-recipe meal-plan endpoint, read-only cookbook DB inspection, local-only Kaggle recipe dataset search/RAG, deterministic input-quality handling, offline evals, and a manual-only live OpenAI smoke script. Automated validation uses the mock provider and generated fixtures; it does not require provider keys, live AI calls, the Vanilla Cookbook database, or committed raw dataset files.

For a portfolio or interview walkthrough, start with [AI demo walkthrough](docs/ai-demo-walkthrough.md), [AI feature status](docs/ai-feature-status.md), and the mock demo helper:

```powershell
.\scripts\demo-ai-mock.ps1
```

For the full local browser UI path, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

## Status

Runtime, EC2 control, bootstrap, verification, and backup/restore assets exist. An operator must still configure EC2, IAM and instance profile, GitHub settings, Cloudflare Tunnel/DNS, and the first admin user. The repository does not create cloud resources.
