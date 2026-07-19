# 0032A Portfolio Platform AWS Scaling Architecture ADR

## Goal

Create a formal architecture decision record for the AWS scaling path of the broader portfolio platform that will host Cookbook AI and future unrelated apps.

This task should turn the existing brainstorm in `docs/portfolio-platform-aws-scaling-brainstorm.md` into a decision-oriented ADR with phases, boundaries, acceptance criteria, and follow-on implementation tasks.

This is a docs/architecture task only.

## Background

`0030G` completed local Recipe Session Alpha operator UX polish. The 0029/0030 AI demo baseline is now strong enough to preserve as a product slice while planning the broader platform around it.

The existing brainstorm says the future platform should separate:

```text
Portfolio platform layer
  - app registry
  - app metadata
  - health/status reporting
  - usage and cost visibility
  - provider/model policy
  - deployment inventory
  - cross-app observability
  - future session/metering/access controls

Individual app silos
  - Cookbook app
  - stock/market app
  - future unrelated apps
  - each owns its own data boundary, routes, limits, logs, and feature flags
```

The brainstorm also recommends an EC2-first path that can later evolve into ALB + Auto Scaling and ECS on EC2 without jumping directly into Kubernetes.

Earlier task numbering suggested this as `0031A`, but `0031A/B` are now used for secondary-provider offload/fact-gate work. Use `0032A` for the portfolio platform AWS architecture line.

## Primary Objective

Create a formal ADR that decides the near-term and staged AWS architecture for the portfolio platform.

The ADR should answer:

- What is the near-term production-shaped hosting model?
- Why EC2-first instead of ECS/Fargate/EKS immediately?
- What must be externalized before the app can scale horizontally?
- How do multiple apps share infrastructure while keeping app data separated?
- What should be tracked in a portfolio metadata layer?
- How are AI provider usage, budget controls, kill switches, and app-specific limits represented?
- What are the migration triggers from one phase to the next?
- What remains explicitly out of scope?

## Required Work

### 1. Create the ADR

Create:

```text
docs/portfolio-platform-aws-scaling-architecture-adr.md
```

The ADR should include:

- status;
- context;
- decision;
- architecture phases;
- shared infrastructure model;
- app silo model;
- portfolio metadata model;
- AI cost/usage controls;
- migration triggers;
- risks and mitigations;
- explicit non-goals;
- follow-on implementation task list.

### 2. Decide the staged platform path

Use the existing brainstorm as the source.

Document phases similar to:

```text
Phase 1: Single EC2 portfolio host with Docker Compose
Phase 2: Production-shaped single EC2 with externalized config/data/logs
Phase 3: ALB + EC2 Auto Scaling Group
Phase 4: ECS on EC2 for per-service scaling
Later options: Fargate or EKS only if justified
```

Keep the decision practical for a portfolio/demo product.

### 3. Define the app boundary model

Document how the platform should host multiple apps without mixing data or business logic.

At minimum, define boundaries for:

- app routes/domains;
- app-owned database schema or database;
- object storage prefixes;
- feature flags;
- usage limits;
- logs and metrics labels;
- AI provider budget controls;
- RAG/index boundaries;
- data retention rules;
- export/import rules.

Include a rule of thumb:

```text
Shared infrastructure is acceptable. Shared uncontrolled state is not.
```

### 4. Define the shared infrastructure model

Document expected shared resources:

- VPC/subnets/security groups;
- ALB when the platform reaches phase 3;
- EC2 host or ECS-on-EC2 cluster capacity;
- RDS/Postgres when local SQLite is no longer appropriate;
- S3 for object/file storage;
- CloudWatch logs/metrics/dashboards;
- SSM Parameter Store or Secrets Manager for secrets/config;
- GitHub Actions OIDC deployment role;
- portfolio metadata database/schema;
- shared authentication/session layer later;
- shared AI provider policy and cost controls.

Do not implement any AWS resources in this task.

### 5. Define the portfolio metadata model

Design a conceptual metadata model for tracking apps.

Possible records/tables:

```text
portfolio.app_registry
portfolio.app_deployments
portfolio.app_usage_daily
portfolio.ai_provider_usage
portfolio.cost_estimates
portfolio.feature_flags
portfolio.health_checks
portfolio.runtime_events
```

Possible fields:

- app id;
- app name;
- domain/subdomain;
- deployment version;
- current health;
- feature status;
- provider/model policy;
- AI/API usage;
- AWS estimated cost;
- request count;
- error rate;
- RAG/index status;
- session/metering status;
- last deployment time;
- active feature flags;
- kill-switch state.

Keep this conceptual. No migrations.

### 6. Define AI cost and usage controls

Document how Cookbook AI and future apps should handle free public use safely.

Include:

- no user-selectable model picker;
- approved low-cost model path for free/default usage;
- per-app budget caps;
- per-session request limits;
- daily/monthly provider budget caps;
- max output token caps;
- bounded RAG context packing;
- provider kill switch;
- fallback behavior when live AI is disabled;
- usage reporting for the portfolio layer.

Do not add runtime payment or monetization logic.

### 7. Define migration triggers

Create a clear decision table for moving between phases.

Examples:

- move from single EC2 to production-shaped EC2 when local state/config/logs become operational risk;
- move to ALB + ASG when uptime or instance replacement matters;
- move to ECS on EC2 when per-app scaling and repeatable deployments matter;
- consider Fargate when host management is no longer worth the control/cost tradeoff;
- consider EKS only if Kubernetes itself becomes a deliberate portfolio story or required capability.

### 8. Define operational acceptance criteria

For each phase, document expected acceptance evidence.

Examples:

- health endpoint checks;
- deployment version reporting;
- rollback plan;
- secret/config boundary;
- app data boundary;
- logs/metrics visibility;
- AI budget kill-switch behavior;
- backup/restore expectations;
- cost visibility.

### 9. Update docs

Update as appropriate:

- `docs/portfolio-platform-aws-scaling-brainstorm.md` to link to the ADR;
- `docs/ai-feature-status.md` to include the ADR as a planning/demo starting point if appropriate;
- `docs/ai-implementation-backlog.md` with `0032A` status;
- `README.md` if relevant.

Create:

```text
outbox/0032A-portfolio-platform-aws-scaling-architecture-adr-results.md
```

The outbox should summarize:

- ADR created;
- platform path decision;
- app boundary model;
- shared infrastructure model;
- portfolio metadata model;
- migration triggers;
- docs updated;
- validation results;
- explicit non-goals.

## Acceptance Criteria

- Formal portfolio platform AWS scaling ADR exists.
- ADR clearly chooses an EC2-first staged path.
- ADR explains why ECS/Fargate/EKS are not first-step defaults.
- ADR defines app silo boundaries and shared infrastructure boundaries.
- ADR defines conceptual portfolio metadata model.
- ADR defines AI budget/usage controls for multi-app free/public usage.
- ADR defines migration triggers between phases.
- ADR defines operational acceptance evidence for each phase.
- Existing brainstorm links to the ADR.
- Normal validation remains offline/mock-only.
- No AWS resources are created.
- No Terraform/CDK/CloudFormation is added.
- No production deployment, DNS, Cloudflare, database, auth, payment, provider-routing, or public route changes are implemented.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke/eval wrappers should skip cleanly unless explicitly opted in.

Do not run live OpenAI during normal validation.

Do not run or create live AWS resources.

## Non-Goals

- no AWS resource creation;
- no Terraform;
- no CDK;
- no CloudFormation;
- no GitHub Actions deploy workflow;
- no production deployment;
- no DNS or Cloudflare changes;
- no database migrations;
- no auth implementation;
- no payment implementation;
- no public route exposure;
- no provider-routing changes;
- no live OpenAI calls;
- no secondary provider runtime;
- no vector database;
- no embeddings;
- no EKS implementation;
- no ECS implementation;
- no screenshots or browser automation;
- no raw dataset commits;
- no generated persistent indexes.

## Commit

```bash
git add docs README.md outbox/0032A-portfolio-platform-aws-scaling-architecture-adr-results.md

git commit -m "mailbox: complete task 0032A portfolio platform aws scaling architecture adr"

git pull --rebase origin main

git push origin main
```
