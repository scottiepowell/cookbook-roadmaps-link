# Vanilla Cookbook GitOps Lab

This mailbox-driven DevOps lab deploys Vanilla Cookbook to AWS EC2 at [cookbook.roadmaps.link](https://cookbook.roadmaps.link). Coder and Codex handle reviewed tasks, GitHub stores desired state, and GitHub Actions operates EC2 through AWS Systems Manager.

## AI Cookbook Showcase

Current product-validation priority: [Manual Product Integration Usability
Validation](docs/manual-product-integration-usability-validation.md). Run the
local shell with `-Provider mock` and use `/product` as the starting point for
checking the Cookbook handoff, readiness, and AI workspace. This is an
app-level usability exercise; AWS/platform work is a separate future effort.

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
- [Local Cookbook AI product integration](docs/local-cookbook-ai-product-integration.md)
- [Manual product integration usability validation](docs/manual-product-integration-usability-validation.md)
- [Product priority roadmap after 0032A](docs/product-priority-roadmap-after-0032A.md)
- [Application session timer and access exceptions ADR](docs/application-session-timer-access-exceptions-adr.md)
- [SSO and BYOS identity/storage architecture ADR](docs/sso-byos-identity-storage-architecture-adr.md)
- [Traffic analytics and behavior tracking ADR](docs/traffic-analytics-behavior-tracking-adr.md)
- [Website marketing and community outreach ADR](docs/website-marketing-community-outreach-adr.md)
- [Ads, sponsors, and monetization ADR](docs/ads-sponsors-monetization-adr.md)
- [AI sidecar logging](docs/ai-sidecar-logging.md)
- [AI live demo runbook](docs/ai-live-demo-runbook.md)
- [Live OpenAI demo evals](docs/live-openai-demo-evals.md)
- [Live OpenAI GPT-nano baseline](docs/live-openai-demo-baseline-2026-07-07.md)
- [Live OpenAI regression notes](docs/live-openai-demo-regression-notes-2026-07-08.md)
- [Production access metering architecture](docs/production-access-metering-architecture.md)
- [AI session metering schema](docs/ai-session-metering-schema.md)
- [AI provider budget enforcement](docs/ai-provider-budget-enforcement.md)
- [AI secondary provider offload ADR](docs/ai-secondary-provider-offload-adr.md)
- [AI secondary provider fact register](docs/ai-secondary-provider-fact-register.md)
- [AI secondary provider implementation gate](docs/ai-secondary-provider-implementation-gate.md)
- [AI production readiness roadmap](docs/ai-production-readiness-roadmap.md)
- [Recipe session requirements architecture](docs/recipe-session-requirements-architecture.md)
- [RAG requirements interaction architecture](docs/rag-requirements-interaction-architecture.md)
- [Recipe creator session memory model](docs/recipe-creator-session-memory-model.md)
- [Recipe Session Alpha acceptance runbook](docs/recipe-session-alpha-acceptance-runbook.md)
- [AI invite-only demo session flow](docs/ai-invite-only-demo-session-flow.md)
- [AI demo walkthrough](docs/ai-demo-walkthrough.md)
- [AI feature status](docs/ai-feature-status.md)
- [REST request examples](scripts/demo-ai-requests.http)
- [AI evals plan](docs/ai-evals-plan.md)
- [Manual live OpenAI smoke tests](docs/live-openai-smoke-tests.md)
- [Playwright UI troubleshooting](docs/playwright-ui-troubleshooting.md)
- [AI screenshot capture guide](docs/ai-screenshot-capture-guide.md)

Run the safe mock demo:

```powershell
.\scripts\demo-ai-mock.ps1
```

Start the local integrated product with generated demo-safe saved recipes and
dataset fixtures:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1
```

For a complete local Cookbook/AI integration, use two terminals. Terminal 1
starts only the localhost-bound Vanilla Cookbook Docker runtime; it does not
start `cloudflared`, require AWS, GitHub Actions, or production secrets:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1
```

Docker Desktop must be running first; verify with `docker info`. If the daemon
is unavailable, the local runtime script stops before Compose startup with a
recovery message. The production/exposed Cookbook URL and its AWS/Cloudflare
Tunnel path are separate from this local development runtime.

Terminal 2 starts the deterministic AI sidecar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider mock
```

Open `http://127.0.0.1:3000/` for Vanilla Cookbook,
`http://127.0.0.1:8000/product` for the integrated shell, and
`http://127.0.0.1:8000/demo` for the AI workspace. Check or stop the local
Cookbook runtime with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Local Cookbook database and uploads are disposable under ignored
`.local/vanilla-cookbook/`. The production-shaped `docker-compose.yml` still
owns the AWS/Cloudflare deployment path; do not use it for this local-only
check when avoiding `cloudflared`.

The local disposable runtime is the prerequisite for `0033J` Save-to-Cookbook
adapter schema discovery and later write/rollback tests. It does not enable
Save to Cookbook or any production write-back.

When ignored local `.env` contains valid live settings, this starts the sidecar
in local OpenAI mode. Open `http://127.0.0.1:8000/product` first; `/demo`
remains the guided AI workspace.

For an explicitly authorized manual live sidecar check, keep the local
Cookbook runtime in Terminal 1 and use the existing bounded launcher profile
in Terminal 2. Normal validation remains mock/offline and must not run this
profile.

Create safe, ignored live defaults without writing a key:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -WriteMissingLiveDefaults -Provider mock -CheckRuntimeProfile
```

Then add `OPENAI_API_KEY` only to local ignored `.env` (or the process
environment). The launcher imports that file into its own server process,
redacts the key in its summary, and permits only `gpt-5.4-nano` with a
500–1000 output-token cap in local live mode; 500 is the recommended default
and 1000 is the explicit ceiling. Precedence is explicit script arguments, existing
process environment, local `.env`, then script defaults. To force the free
deterministic path, use `-Provider mock`; that explicit override also disables
inherited live enablement and uses `mock-basic` for the child process.

For a one-off explicit live override:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests -OpenAIModel gpt-5.4-nano -MaxOutputTokens 500 -LiveTestBudgetCents 25 -Port 8001
```

Full local RAG manual importer launch:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 500 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

The browser sends only a safe mode/model preference; it never receives or
stores provider keys. The server-side launcher controls whether live is
available, so a UI Live selection still gets a controlled unavailable response
when the process lacks valid opt-in/key/budget configuration. `AI_PROVIDER_DEBUG=true`
is opt-in and only adds sanitized local provider diagnostics.

For optional local browser QA of `/product` and `/demo`, install Chromium for
Playwright and run `scripts\run-ui-playwright.ps1` with a separately started
mock sidecar. This troubleshooting harness intercepts normalized mode/model
payloads and checks safe live-unavailable behavior; it is not part of normal
validation and produces ignored artifacts only.

For a separately authorized live acceptance, start the sidecar with the normal
no-argument launcher, verify its redacted summary says `openai` and
`gpt-5.4-nano`, then run one minimal importer request within the configured
budget. The browser runner deliberately refuses live-capable sidecars, and the
browser never receives provider credentials.

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

To diagnose one live importer 503 safely, run the preflight (no provider call)
first, then add `-ApproveLiveCall` only after reviewing its redacted summary:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall
```

This path is importer-only, bounded to one call, and reports only safe failure
categories/guidance. It never prints keys, prompts, response bodies, or stack
traces and is not part of normal offline validation.

Run the no-call preflight explicitly when checking a live configuration:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly
```

The launcher preserves existing process environment values over `.env`; stale
`AI_MODEL` or `OPENAI_MODEL` values must be cleared or aligned to
`gpt-5.4-nano`. The launcher also stops before Uvicorn if port 8000 is already
occupied. Inspect it with `netstat -ano | findstr :8000` and stop only an old
sidecar you recognize (`Stop-Process -Id <PID>`); it never kills unknown
processes automatically.

If an approved diagnostic reports `output_cap_or_incomplete_response`,
preflight and configuration succeeded and the live path was reached, but the
provider response was incomplete or not schema-parseable within the output
cap. Do not retry repeatedly or raise caps automatically in normal validation;
make at most one explicitly approved follow-up with a documented cap/timeout
adjustment.

With `-ProviderDebug` enabled, local logs can distinguish timeout, schema rejection, bad model, quota/rate limit, auth, and network failures while keeping the public `503` response safe.

Run the live OpenAI demo eval wrapper only with explicit live opt-in settings:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Without opt-in settings, it skips cleanly and performs no live calls.

If you prefer local ignored config files, the live smoke and live eval wrappers also accept `-EnvFile .\.env`. The wrappers are the only supported `.env` loader for these live paths, so an ignored local `.env` does not opt you into live calls unless you pass `-EnvFile` or export the variables yourself. The live smoke wrapper can seed safe missing defaults with `-WriteMissingEnvDefaults`, but it does not write `OPENAI_API_KEY`, does not enable live mode by itself, and still skips cleanly when `OPENAI_ENABLE_LIVE_TESTS=false` or `AI_PROVIDER=mock`.

The first successful GPT-nano live eval baseline is recorded in [Live OpenAI Demo Baseline: 2026-07-07](docs/live-openai-demo-baseline-2026-07-07.md). The current acceptance baseline is the post-`0028B` 6/6 run recorded in [Live OpenAI Demo Regression Notes: 2026-07-08](docs/live-openai-demo-regression-notes-2026-07-08.md), after the post-`0028A` importer evaluator false failure was fixed. Future live eval runs should compare correctness, usefulness, importer ingredient preservation, action-oriented step quality, short context-phrase handling, aggregate instruction conciseness, latency, token use, cost visibility, and input-quality/provider-call-avoidance metrics against that acceptance history. `gpt-5.4-nano` evals use maintained default cost rates unless operator pricing env vars override them.

Future secondary/offload provider exploration is documented only in [AI Secondary Provider Offload ADR](docs/ai-secondary-provider-offload-adr.md). `GLM-4.7 Flash` is treated there as a candidate provider name only, secondary outputs are advisory only, and the current OpenAI `gpt-5.4-nano` path remains the final-answer baseline until a later approved implementation task changes that. `0031B` adds [AI Secondary Provider Fact Register](docs/ai-secondary-provider-fact-register.md) and [AI Secondary Provider Implementation Gate](docs/ai-secondary-provider-implementation-gate.md), which keep runtime adapter work blocked until primary provider documentation verifies the required facts. Any future secondary-provider work must also preserve the corrected 0030 baseline, including the `0030P` no-bake cheesecake clarification behavior.

The future production integration direction is documented in the [Cookbook AI Plugin and Adapter Architecture ADR](docs/cookbook-ai-plugin-adapter-architecture-adr.md). It keeps the core Cookbook app, a stable Cookbook AI Adapter, and the RAG/AI sidecar modular while requiring native, seamless user experience. The ADR is docs-only: it adds no plugin endpoints, production auth, public routes, provider integration, vector/embedding infrastructure, upstream UI rewrite, or deployment work. Normal validation remains mock/offline and current server-side live gating is unchanged.

QMD is documented in [QMD Local Hybrid Retrieval Adapter Spike](docs/qmd-local-hybrid-retrieval-adapter-spike.md) as an optional local retrieval candidate only. It is not installed, vendored, or accepted as a repository dependency; the current deterministic keyword retrieval remains the default and normal validation remains mock/offline. The spike keeps any future QMD path behind a retrieval adapter, maps hits back to canonical Cookbook IDs/provenance, and preserves the seamless native UX requirement.

The broader portfolio hosting direction is documented in the [Portfolio Platform AWS Scaling Architecture ADR](docs/portfolio-platform-aws-scaling-architecture-adr.md). It proposes a staged EC2-first path—single Compose host, production-shaped EC2, ALB/Auto Scaling, then ECS on EC2—with Fargate/EKS deferred until justified by evidence. This remains a docs-only architecture decision: the repository creates no AWS resources, deployment code, DNS/Cloudflare changes, migrations, auth/payment systems, public routes, or provider-routing changes.

Normal validation is mock/offline and safe. No provider keys, raw dataset files, generated indexes, private environment files, or private recipe data are committed.

The importer now behaves as an import/create workflow for rough recipe notes. When local dataset fixtures are configured, it retrieves a small bounded set of similar recipes before the provider call and passes them as structure guidance only. The retrieval is anchor-aware, and the dataset index normalizes conservative aliases, phrases, punctuation, and singular/plural variants so exact dish names and core ingredients outrank broad category matches. Weak matches are called out in warnings, the user's ingredients and dish intent remain primary, retrieved recipes are not copied verbatim, citations/provenance are returned for transparency, estimated quantities are disclosed in notes, provider prompts receive a bounded packed snippet block instead of raw retrieved records, and the API/UI classify RAG support as strong, moderate, weak, or none so broad examples are not described as authoritative grounding.

The local dataset search/retrieval path also uses a small process-local in-memory cache so repeated requests with the same dataset limit, source metadata, normalization version, and query can reuse work without writing generated indexes to disk. The UI exposes only short fingerprints and hit/miss state.

The RAG importer path now has an offline E2E regression test that exercises the real `/ai/import-recipe` route with generated dataset fixtures and the mock provider, covering retrieval, normalization, context packing, support labels, citations, schema validation, and cache metadata together.

The next recipe-creation product layer is documented, not implemented, in [Recipe session requirements architecture](docs/recipe-session-requirements-architecture.md). It designs a session-scoped requirements state, one-question clarification policy, follow-up delta classifier, and RAG refresh rules so future revisions like `actually make it no-bake` can update requirements, refresh retrieval, and explain why citations changed. It does not add production storage, persistent user memory, auth, paid access, public route exposure, embeddings, vector databases, or a full chat UI.

The first local alpha implementation for that layer now exists in `ai-api/app/recipe_requirements.py`, `ai-api/app/recipe_session.py`, and `ai-api/app/recipe_session_routes.py`. It provides deterministic requirements extraction, confidence labels, clarification and follow-up classification, RAG refresh decisions, a bounded in-memory test/demo session store, and local `/ai/recipe-session/*` endpoints for start/message/get/finalize flows. Follow-up responses include a safe requirement diff and concise revision summary so operators can see what changed and why retrieval refreshed or was reused. The `/demo` UI includes a compact Recipe Session Alpha panel for starting a session, sending a follow-up, viewing RAG refresh/no-refresh state, and finalizing for demo. `evals/ai_cookbook/run_evals.py` now includes deterministic `recipe_session` cases for draft generation, clarification, method/equipment/exclusion RAG refresh, no-refresh, finalize, finalize-before-draft, missing-session safety, and leakage checks. The [Recipe Session Alpha acceptance runbook](docs/recipe-session-alpha-acceptance-runbook.md) documents the local demo checklist and boundaries. These endpoints, UI controls, evals, and runbook are offline/mock-friendly and are not production storage, auth, paid access, public access, persistent user memory, or a full chat UI.

The full-RAG manual importer/eval path uses a separate `AI_MAX_OUTPUT_TOKENS=900`
profile because retrieved structured recipe drafts can be larger. That profile
is distinct from the approval-gated diagnostic acceptance cap documented below;
it does not change normal product/runtime caps or mock/offline validation. The
live eval harness keeps its separate importer-only cap with a 900-token default
and a 1200-token ceiling so importer evals stay distinct from the 300-token
non-importer guard.

The approval-gated diagnostic deliberately uses a smaller scrambled-egg fixture
and remains separate from normal product/runtime caps and full-RAG evaluation.
The explicit manual `openai` / `gpt-5.4-nano` diagnostic has now passed at both
500 and 1000 output tokens. The current recommended manual acceptance cap is
500 tokens. The 400-token run failed safely as
`output_cap_or_incomplete_response` / `JSONDecodeError`, and the earlier
300-token run was also too low for complete strict-schema JSON.

Use 500 for the recommended one-call acceptance check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -PreflightOnly -MaxOutputTokens 500
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\diagnose-live-importer.ps1 -ApproveLiveCall -MaxOutputTokens 500
```

1000 remains the explicit manual troubleshooting ceiling, not the recommended
default acceptance cap. Every approved run requires preflight and permits
exactly one bounded importer call; it never retries. Normal validation remains
mock/offline and does not call live OpenAI.

The live importer `503` blocker from manual testing was traced to strict structured-output schema metadata that OpenAI rejected. The schema normalizer now strips unsupported metadata such as `default`, `examples`, `title`, and `description` before the provider call, while application behavior still defaults importer servings to 4.

Production access architecture is proposed, not implemented. Before any public live provider-backed AI exposure, the AI demo needs an access layer with time-limited sessions, per-call metering, provider budget enforcement, a global live-provider disable switch, protected routes, and metadata-only logging by default. The first schema-only scaffold for that future layer is in `ai-api/app/ai_access_models.py` and [AI session metering schema](docs/ai-session-metering-schema.md), covering demo sessions, access grants, meter events, quality events, audit events, and budget snapshots. Local/private invite-only demo sessions now build on those schemas in `ai-api/app/ai_invite_sessions.py`, but they remain disabled by default, process-local, and separate from production auth, billing, or public access. Payment integration is deferred, and the platform rule remains: shared infrastructure is allowed, but each demo owns its own data boundary. The monetization and entitlement boundary is documented in [AI Monetization And Entitlement Boundary ADR](docs/ai-monetization-and-entitlement-boundary-adr.md), which keeps the near-term ads/sponsors model separate from access control and provider budgets. The local/operator usage report prototype in [AI Admin Usage Report Prototype](docs/ai-admin-usage-report-prototype.md) summarizes that same safe state in the demo UI and a local JSON endpoint, and the locked 29/30 baseline is exercised by [29/30 Integrated Regression And E2E Harness](docs/ai-29-30-regression-e2e-harness.md) and `scripts\run-ai-29-30-regression.ps1`. The docs-only [AI Secondary Provider Offload ADR](docs/ai-secondary-provider-offload-adr.md), [AI Secondary Provider Fact Register](docs/ai-secondary-provider-fact-register.md), and [AI Secondary Provider Implementation Gate](docs/ai-secondary-provider-implementation-gate.md) keep any future secondary/offload provider idea disabled by default, blocked until facts are verified, and explicitly subordinate to that locked baseline.

The first local/private access guardrail now exists in [AI Local Operator Access Gate](docs/ai-local-operator-access-gate.md). It is disabled by default, protects importer/dataset ask/recipe-session/meal-plan workflows when enabled, and compares safe fingerprints on `X-AI-Operator-Token` or `Authorization: Bearer ...` without echoing raw tokens or local paths. The provider budget guard in [AI Provider Budget Enforcement](docs/ai-provider-budget-enforcement.md) runs after the gate and blocks live provider calls when the demo is globally disabled, caps are exceeded, or the live budget configuration is invalid.

The route exposure boundary is reviewed in [AI Public Route Exposure Review](docs/ai-public-route-exposure-review.md). It documents which routes can ever be public, which must stay private, and which proxy and CORS controls are required before any public exposure work.

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
- [AI admin usage report prototype](docs/ai-admin-usage-report-prototype.md)
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

Open `http://127.0.0.1:8000/product` first. This local product shell links the
external Vanilla Cookbook container at `127.0.0.1:3000` with the AI workspace
at `/demo`, without vendoring or rewriting the upstream frontend.

## Status

Runtime, EC2 control, bootstrap, verification, and backup/restore assets exist. An operator must still configure EC2, IAM and instance profile, GitHub settings, Cloudflare Tunnel/DNS, and the first admin user. The repository does not create cloud resources.
