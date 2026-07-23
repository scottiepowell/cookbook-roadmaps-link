# Portfolio Platform AWS Scaling Brainstorm

## Status

Architecture brainstorming note. This is not an implementation task and does not change runtime behavior.

## Purpose

Capture the strategic discussion about how the Cookbook AI product could fit into a broader portfolio platform that hosts multiple unrelated applications, each with its own data and product boundary, while sharing selected infrastructure and operational metadata.

The near-term product remains the Cookbook AI demo and RAG-informed recipe creator. This note documents the longer-term AWS scaling direction so later architecture tasks can reference the same assumptions.

## Core Idea

The platform should separate two concerns:

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

The applications may share infrastructure, but they should not share uncontrolled state.

## Product And Cost Assumptions

Near-term assumptions:

- Apps are portfolio products first.
- The Cookbook AI app should remain free for users initially.
- Users should not choose arbitrary AI models.
- Live AI should be restricted to the approved low-cost model path.
- API costs are expected to be low per request, but still need budget controls.
- AWS infrastructure cost is likely the larger scaling concern if traffic grows.
- Cost control should use hard limits, usage metering, and provider kill switches before paid access is introduced.

Possible later monetization paths:

- affiliate links around recipe tools/ingredients;
- optional supporter tier;
- paid advanced features such as saved history, meal plans, shopping lists, or exports;
- portfolio/consulting lead generation;
- white-label or reusable AI sidecar pattern for small businesses.

## EC2-First Direction

The current strategic preference is EC2-first because it provides:

- maximum control;
- Docker/Docker Compose flexibility;
- easy debugging with SSH/SSM;
- host-level control;
- ability to run multiple unrelated apps;
- ability to share supporting services later;
- a straightforward portfolio/homelab-to-cloud story.

This should not mean staying on a single snowflake server forever. The EC2 path should be designed so the apps can later move into an ALB/Auto Scaling or ECS-on-EC2 pattern without major rewrites.

## Suggested Scaling Phases

### Phase 1: Single EC2 Portfolio Host

Initial production-shaped setup:

```text
Cloudflare / DNS
  -> EC2 instance
      -> Docker Compose
          -> portfolio landing page
          -> cookbook web/app container
          -> cookbook ai-api sidecar
          -> future app containers
```

Good while:

- traffic is low;
- the product is still being validated;
- low cost and control matter more than high availability;
- manual debugging is still common.

Risks:

- single point of failure;
- host resource contention;
- harder per-app scaling;
- local state must be carefully avoided or backed up.

### Phase 2: Production-Shaped Single EC2

Before horizontal scaling, make the app instances more disposable:

- move secrets/config to SSM Parameter Store or Secrets Manager;
- move durable app data out of local container files;
- use RDS/Postgres or another managed database when SQLite is no longer enough;
- use S3 for object/file storage;
- add per-app health endpoints;
- add structured logs and basic dashboards;
- record deployment version and app metadata;
- add budget and live-AI kill-switch controls.

### Phase 3: ALB + EC2 Auto Scaling Group

First true horizontal scaling step:

```text
Cloudflare / Route 53
  -> Application Load Balancer
      -> target group(s)
          -> EC2 Auto Scaling Group
              -> Docker runtime / app containers
```

Routing can be host-based or path-based:

```text
cookbook.roadmaps.link      -> cookbook services
stocks.roadmaps.link        -> stock services
portfolio.roadmaps.link     -> portfolio control plane
api.roadmaps.link/cookbook  -> cookbook api/service routes
```

Benefits:

- health checks;
- multi-instance deployment;
- multi-AZ path later;
- instance replacement;
- more credible production scaling story.

Tradeoff:

- if every EC2 instance runs every app, scale is coarse-grained and inefficient.

### Phase 4: ECS On EC2

Likely best next platform once there are multiple apps and Docker Compose becomes hard to manage.

```text
ALB
  -> ECS services
      -> EC2-backed ECS cluster capacity
          -> per-app tasks/containers
```

Why ECS on EC2 fits this strategy:

- keeps EC2 control;
- improves deployment repeatability;
- supports per-service scaling;
- lets apps share cluster capacity;
- avoids jumping immediately to Kubernetes complexity;
- better matches multiple unrelated portfolio apps.

Example service scaling:

```text
cookbook-ai-api: 1 -> 4 tasks
cookbook-web:    1 -> 3 tasks
portfolio-api:   1 -> 2 tasks
stocks-api:      0/1 -> 2 tasks
```

### Later Options

Fargate may make sense if server management becomes a distraction and cost is acceptable.

EKS should be delayed unless Kubernetes itself becomes part of the platform/portfolio story or the project needs Kubernetes-native features.

App Runner is not preferred for this strategic direction because the project wants infrastructure control and a shared multi-app platform layer.

## Shared Resources

Potential shared resources:

- VPC/subnets/security groups;
- ALB;
- EC2/ECS cluster capacity;
- RDS Postgres instance early on;
- S3 bucket with per-app prefixes;
- CloudWatch logs/metrics/dashboards;
- SSM Parameter Store / Secrets Manager;
- GitHub Actions OIDC deploy role;
- portfolio metadata database/schema;
- shared authentication/session layer later;
- shared AI provider policy and cost controls.

## App Silo Boundaries

Each app should own:

- app routes/domains;
- database schema or database;
- storage prefix;
- feature flags;
- usage limits;
- logs and metrics labels;
- OpenAI/API budget controls;
- RAG/index boundaries;
- data retention rules;
- export/import rules.

The platform may provide shared primitives, but app data should not be mixed accidentally.

Suggested early Postgres separation:

```text
portfolio schema/database
cookbook schema/database
stocks schema/database
future_app schema/database
```

Suggested S3 separation:

```text
s3://portfolio-app-data/cookbook/...
s3://portfolio-app-data/stocks/...
s3://portfolio-app-data/future-app/...
```

## Portfolio Metadata Layer

The portfolio platform should eventually track:

- app id;
- app name;
- domain/subdomain;
- deployment version;
- current health;
- feature status;
- provider/model policy;
- OpenAI/API usage;
- AWS estimated cost;
- request count;
- error rate;
- RAG/index status;
- session/metering status;
- last deployment time;
- active feature flags;
- kill-switch state.

Possible tables:

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

## AI Cost And Usage Controls

For free public use, the platform should eventually include:

- nano-only provider policy for free users;
- no user-selectable model picker;
- per-app budget caps;
- per-session request limits;
- daily/monthly provider budget caps;
- max output token caps;
- bounded RAG context packing;
- provider kill switch;
- fallback behavior when live AI is disabled;
- usage reporting for the portfolio layer.

## Architecture Rule Of Thumb

```text
Shared infrastructure is acceptable.
Shared uncontrolled state is not.
```

Use shared compute, observability, config, and cost tracking where it reduces operational overhead. Keep app data, business logic, RAG boundaries, and user-facing feature behavior separated by app.

## Recommended Future Task

The formal decision record is now [Portfolio Platform AWS Scaling Architecture ADR](portfolio-platform-aws-scaling-architecture-adr.md):

```text
0032A: Portfolio Platform AWS Scaling Architecture ADR
```

The ADR decides:

- EC2-first architecture boundary;
- when to introduce ALB + Auto Scaling;
- when to move from Docker Compose to ECS on EC2;
- shared RDS/S3/CloudWatch/SSM strategy;
- portfolio metadata model;
- app silo model;
- per-app AI budget and usage model;
- migration triggers from simple EC2 to managed container orchestration;
- explicit non-goals such as EKS, vector DB, or production persistent memory until justified.

It remains docs-only and creates no AWS resources, infrastructure-as-code,
deployment workflow, DNS/Cloudflare change, database migration, auth/payment
system, or production route.
