# Vanilla Cookbook GitOps Lab

This mailbox-driven DevOps lab deploys Vanilla Cookbook to AWS EC2 at [cookbook.roadmaps.link](https://cookbook.roadmaps.link). Coder and Codex handle reviewed tasks, GitHub stores desired state, and GitHub Actions operates EC2 through AWS Systems Manager.

## AI Cookbook Showcase

This repo now includes a portfolio-ready AI cookbook sidecar: Vanilla Cookbook remains the source app, while a FastAPI `ai-api` service provides offline-first AI workflows for structured recipe import, saved-recipe Q&A, deterministic local dataset search/RAG, and saved-recipe meal planning. The architecture is intentionally conservative: retrieval happens before provider calls, responses carry citations/provenance, normal validation uses generated fixtures and the mock provider, and live OpenAI calls are manual-only.

Completed AI workflows:

- Structured recipe importer: `POST /ai/import-recipe` returns schema-validated recipe drafts.
- Ask My Cookbook: `POST /ai/ask` answers over saved recipes with recipe citations.
- Dataset search/RAG: `GET/POST /dataset/search` and `POST /dataset/ask` use bounded local dataset fixtures with provenance citations.
- Meal planning: `POST /ai/meal-plan` builds plans from saved recipe candidates.
- Sidecar demo UI: `GET /demo` and `GET /demo/ai` serve a lightweight browser demo for completed AI workflows.
- Provider harness: mock provider by default, OpenAI path available only through explicit manual opt-in.

Validation proof:

- Offline evals cover dataset ask, saved-recipe ask, importer, meal plan, provider config hygiene, citations, and secret-like leakage checks.
- Repository validation runs pytest and offline evals without provider keys, Docker-only services, the real Kaggle dataset, or a production cookbook database.
- Manual live OpenAI smoke validation passed with `provider=openai`, `model=gpt-5.4-nano`, `live_calls=4`, `estimated_usage_tokens=1200`, `workflows=importer,ask_my_cookbook,dataset_ask,meal_plan`, `budget_cents=25`, `status=passed`.

Demo and evidence links:

- [AI portfolio showcase](docs/ai-portfolio-showcase.md)
- [AI feature completion review](docs/ai-feature-completion-review.md)
- [AI UI integration plan](docs/ai-ui-integration-plan.md)
- [AI sidecar logging](docs/ai-sidecar-logging.md)
- [AI live demo runbook](docs/ai-live-demo-runbook.md)
- [Live OpenAI demo evals](docs/live-openai-demo-evals.md)
- [Live OpenAI GPT-nano baseline](docs/live-openai-demo-baseline-2026-07-07.md)
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

Run the live OpenAI demo eval wrapper only with explicit live opt-in settings:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Without opt-in settings, it skips cleanly and performs no live calls.

The first successful GPT-nano live eval baseline is recorded in [Live OpenAI Demo Baseline: 2026-07-07](docs/live-openai-demo-baseline-2026-07-07.md). Future live eval runs should compare correctness, usefulness, latency, token use, and cost visibility against that baseline. `gpt-5.4-nano` evals use maintained default cost rates unless operator pricing env vars override them.

Normal validation is mock/offline and safe. No provider keys, raw dataset files, generated indexes, private environment files, or private recipe data are committed.

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

The `ai-api` service provides health/config endpoints, deterministic saved-recipe search, structured recipe import drafts, Ask My Cookbook RAG over saved recipes, a saved-recipe meal-plan endpoint, read-only cookbook DB inspection, local-only Kaggle recipe dataset search/RAG, offline evals, and a manual-only live OpenAI smoke script. Automated validation uses the mock provider and generated fixtures; it does not require provider keys, live AI calls, the Vanilla Cookbook database, or committed raw dataset files.

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
