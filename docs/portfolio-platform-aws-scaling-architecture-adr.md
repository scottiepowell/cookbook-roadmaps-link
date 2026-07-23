# ADR: Portfolio Platform AWS Scaling Architecture

Status: proposed, docs-only, no infrastructure implementation

Date: 2026-07-23

## Decision summary

Adopt a staged EC2-first path for the broader portfolio platform. The
near-term production-shaped model is a single EC2 host running Docker Compose,
with the host and application boundaries designed so durable state, secrets,
logs, health, and deployment metadata can later support an ALB plus Auto
Scaling Group and then ECS on EC2.

The decision is intentionally practical for a portfolio/demo product:

1. Start with a single EC2 portfolio host and Docker Compose.
2. Make that host production-shaped by externalizing configuration, durable
   data, logs, health, version reporting, and cost controls before adding
   horizontal capacity.
3. Introduce ALB plus EC2 Auto Scaling when availability and traffic justify
   multiple instances.
4. Move from host-level Compose to ECS on EC2 when per-service deployment and
   scaling become the limiting factor.
5. Consider Fargate or EKS only after explicit evidence justifies their cost,
   operational model, or platform value.

No phase is implemented by this ADR. Shared infrastructure is acceptable.
Shared uncontrolled state is not.

## Context and problem

Cookbook AI currently runs as a local, offline-first FastAPI sidecar next to
the Vanilla Cookbook application. The plugin/adapter ADR establishes that the
core app, Cookbook AI Adapter, and RAG/AI sidecar should remain modular while
the end-user experience stays seamless. The QMD spike likewise keeps any
optional retrieval backend behind an adapter and preserves deterministic
fallback behavior.

The broader portfolio may eventually host Cookbook, a stock/market app, a
portfolio control plane, and unrelated future apps. Those apps should share
selected compute and operational primitives without sharing databases, files,
business state, RAG indexes, provider sessions, or uncontrolled feature flags.

The platform needs a credible path from a low-cost portfolio host to a more
available multi-instance and per-service model, without prematurely adopting
Kubernetes or building infrastructure that has not been justified by traffic,
team size, reliability requirements, or cost evidence.

## Near-term hosting model

The near-term production-shaped model is:

```text
Cloudflare / DNS boundary (future, separately approved)
        |
        v
Single EC2 portfolio host
        |
        v
Docker Compose
  - portfolio landing/control-plane app
  - Cookbook web/app boundary
  - Cookbook AI sidecar
  - future app containers
```

For the current repository, this remains architecture guidance only. Existing
deployment/bootstrap documentation and local Compose behavior are not changed
by this ADR. The single host is acceptable while traffic is low, product
boundaries are being validated, and manual operations are still common. It is
not treated as a permanent snowflake: the externalization work in Phase 2 is a
prerequisite to credible horizontal scaling.

## Why EC2-first

EC2-first is preferred because it fits the portfolio/demo constraints:

- low initial infrastructure complexity and cost;
- direct control over Docker Compose and host resources;
- straightforward SSH/SSM-style debugging and recovery model;
- ability to run several unrelated app containers on shared capacity;
- clear homelab-to-cloud and portfolio demonstration story;
- a gradual path to ALB, Auto Scaling, and ECS on EC2;
- no requirement to redesign every service around a task platform before the
  product has validated its traffic and boundaries.

EC2-first does not mean ignoring disposability or operations. Phase 2 must make
configuration, durable data, logs, health, versioning, backups, and kill
switches explicit. If those boundaries cannot be made clear, the platform is
not ready for horizontal scale regardless of which AWS compute service is
chosen.

## Why not ECS, Fargate, or EKS immediately

### ECS/Fargate

ECS and Fargate provide useful task-level deployment and scaling, but adopting
them immediately would add task definitions, networking, service discovery,
logging, secret injection, image lifecycle, and capacity/cost decisions before
the portfolio has established its app boundaries and operational signals.
Fargate also trades host control for a simpler server-management model and may
be less cost-effective for a small, mostly idle portfolio workload.

ECS remains a planned Phase 4 destination. ECS on EC2 is preferred before
Fargate when shared host capacity, cost control, and host-level flexibility are
still important.

### EKS

EKS is not the first-step default because Kubernetes introduces a substantial
control-plane, networking, workload, security, observability, upgrade, and
operator burden. It is justified only if Kubernetes itself is a portfolio
product goal, the platform needs Kubernetes-native capabilities, or workload
and team evidence makes that operational investment rational.

### App Runner or other managed application services

These may be useful for individual apps, but they are not the default strategic
direction because the portfolio wants a shared platform boundary, explicit
resource/cost controls, and a staged path through EC2 and ECS on EC2.

## Architecture phases

### Phase 1: Single EC2 portfolio host with Docker Compose

Shape:

```text
EC2 instance
  -> Docker Compose
      -> portfolio app
      -> cookbook app/web boundary
      -> cookbook ai-api sidecar
      -> future app containers
```

Use while traffic is low, services are few, and operational learning is more
valuable than high availability. Each app still has its own routes, labels,
config namespace, data boundary, and resource expectations even though the
containers share a host.

Primary risks are a single point of failure, noisy-neighbor resource
contention, coarse scaling, and accidental local state. Those risks are
accepted only with explicit backups, safe recovery, resource limits, and a
documented migration trigger.

### Phase 2: Production-shaped single EC2 with externalized config/data/logs

Before horizontal scaling, make app instances disposable enough to replace.
The target shape externalizes or formalizes:

- SSM Parameter Store or Secrets Manager for secrets/configuration;
- durable data out of container files;
- RDS/Postgres when local SQLite is no longer appropriate;
- S3 for object and file storage with per-app prefixes;
- structured logs and basic CloudWatch dashboards;
- per-app health endpoints and deployment version reporting;
- provider budgets, AI kill switches, and safe fallback behavior;
- backup/restore, retention, export, import, and recovery runbooks.

Phase 2 is still one EC2 host. It is a readiness phase for scaling, not a
deployment instruction in this ADR.

### Phase 3: ALB plus EC2 Auto Scaling Group

Shape:

```text
ALB
  -> target groups
      -> EC2 Auto Scaling Group
          -> Docker runtime / app containers
```

The ALB may eventually use host-based or path-based routing, for example:

```text
cookbook.roadmaps.link       -> Cookbook services
stocks.roadmaps.link         -> stock services
portfolio.roadmaps.link      -> portfolio control plane
api.roadmaps.link/cookbook   -> Cookbook API boundary
```

The exact domains, DNS, Cloudflare, certificates, and public routes require
separate approved work. Phase 3 provides health checks, instance replacement,
multi-instance capacity, and a path toward multi-AZ operation. It does not
solve per-app scaling if every instance still runs every app.

### Phase 4: ECS on EC2 for per-service scaling

Shape:

```text
ALB
  -> ECS services
      -> EC2-backed ECS cluster capacity
          -> per-app tasks/containers
```

ECS on EC2 becomes attractive when Compose deployment and coarse host scaling
are the bottleneck. It permits service-level desired counts and deployments,
for example Cookbook AI sidecar tasks scaling independently from Cookbook web,
portfolio, or stock services. Cluster capacity, placement, task IAM, logging,
service discovery, and deployment rollback must be proven in a separate
implementation task.

### Later options: Fargate or EKS only if justified

Fargate is a later option if host management materially distracts from product
work and its per-task cost is acceptable. EKS is a later option if Kubernetes
capabilities or the portfolio story justify its complexity. Neither is an
implicit destination or acceptance criterion for the current phase.

## App boundary model

Each app is a tenant-like silo within the shared platform. At minimum, every
app has explicit ownership for:

| Boundary | App-owned rule |
| --- | --- |
| Routes/domains | App route namespace, host/path contract, health endpoint, and public/private classification. |
| Database | App-owned schema or database, migrations, connection policy, backup scope, and retention. No cross-app table reads by convention. |
| Object storage | App-specific S3 prefix and lifecycle policy. No unscoped bucket listing or path sharing. |
| Feature flags | Namespaced flags with owner, environment, default, rollout, and kill-switch semantics. |
| Usage limits | Per-app request, session, storage, and provider limits. Shared primitives may enforce them; app policy defines them. |
| Logs and metrics | App/service/environment labels, correlation IDs, redaction policy, and retention. Shared CloudWatch is acceptable; unlabeled mixed logs are not. |
| AI provider controls | App-specific approved model path, token caps, budget, call limits, and live-provider disable state. |
| RAG/index | App-owned source scope, index namespace, document IDs, refresh, deletion, and provenance. A Cookbook index cannot silently include stock-app data. |
| Data retention | App-owned retention, deletion, backup, legal/operational hold, and derived-artifact policy. |
| Export/import | Explicit app-scoped formats, authorization, validation, and audit. No platform-wide raw database export by default. |

The platform may supply shared mechanisms for these boundaries, but each app
owns policy and data. Shared infrastructure is acceptable. Shared uncontrolled
state is not.

Suggested early database separation:

```text
portfolio schema/database
cookbook schema/database
stocks schema/database
future_app schema/database
```

Suggested object storage separation:

```text
s3://portfolio-app-data/cookbook/...
s3://portfolio-app-data/stocks/...
s3://portfolio-app-data/future-app/...
```

These are conceptual names only; this ADR creates no bucket, schema, database,
or migration.

## Shared infrastructure model

Selected infrastructure can be shared when ownership and labels remain clear:

- VPC, subnets, route tables, and security groups with least-privilege rules;
- ALB and target groups once Phase 3 is approved;
- EC2 host capacity in Phases 1–3 or an ECS-on-EC2 cluster in Phase 4;
- RDS/Postgres when local SQLite is no longer appropriate;
- S3 for object/file storage with app prefixes and lifecycle policies;
- CloudWatch logs, metrics, alarms, and dashboards with app labels;
- SSM Parameter Store or Secrets Manager for secrets/configuration;
- a GitHub Actions OIDC deployment role, introduced only by separate approved
  deployment work;
- a portfolio metadata database/schema;
- a shared authentication/session layer later, with app scopes and explicit
  ownership;
- shared AI provider policy and cost controls implemented as common guardrails
  with app-specific limits.

Shared infrastructure must not imply shared application data, shared write
permissions, shared RAG indexes, or a common public route. The platform layer
should expose safe metadata and control decisions, not arbitrary app records.

## Portfolio metadata layer

The portfolio layer is a control-plane metadata surface, not a replacement for
app databases. Its purpose is inventory, health, usage, cost, feature, and
operational visibility.

Conceptual records/tables:

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

Conceptual fields include:

```text
app id
app name
domain/subdomain
deployment version
current health
feature status
provider/model policy
AI/API usage
AWS estimated cost
request count
error rate
RAG/index status
session/metering status
last deployment time
active feature flags
kill-switch state
```

Additional control-plane fields should include environment, owner, contract
version, data classification, retention class, desired/observed version,
health-check timestamp, and safe reason/status codes. These records should not
contain prompts, provider bodies, secrets, raw tokens, unrestricted user data,
or local filesystem paths.

The metadata layer may eventually power a private operator view and reports.
It is not a public route, auth implementation, billing system, or app data
warehouse in this ADR.

## AI usage, budget, and kill-switch model

Cookbook AI and future apps should use a shared policy framework with
app-specific budgets:

- no user-selectable arbitrary model picker;
- an approved low-cost model path for free/default usage;
- per-app provider budget caps;
- per-session request limits;
- daily and monthly provider budget caps;
- maximum input and output token caps;
- bounded RAG context packing and retrieval limits;
- a provider/global kill switch plus app-level kill switches;
- safe fallback behavior when live AI is disabled, unavailable, over budget, or
  not configured;
- portfolio-layer usage reporting by app, workflow, provider, model policy, and
  time bucket.

Conceptually, each AI usage event should be attributable to an app, workflow,
environment, session class, provider policy, and safe cost estimate. The event
may include counts, caps, decision status, and reason codes; it must not include
raw prompts or provider responses.

When live AI is disabled, the app should use its approved mock/offline or
deterministic fallback where the workflow supports it, or return a readable
unavailable state. It must not silently switch to an unapproved provider or
model. Existing Cookbook server-side live gating and strict structured-output
validation remain authoritative.

## Migration trigger decision table

| Transition | Trigger evidence | Required prerequisites | Decision outcome |
| --- | --- | --- | --- |
| Single EC2 → production-shaped EC2 | Any durable local state, repeated manual recovery, secret sprawl, missing restore evidence, or a planned second instance | Externalized config/secrets, durable data plan, health/version reporting, structured logs, backup/restore, app boundaries, AI budgets/kill switches | Complete Phase 2 before adding horizontal capacity. |
| Production-shaped EC2 → ALB + ASG | Availability target exceeds one host, instance replacement is needed, traffic has sustained peaks, or one host is a capacity bottleneck | Stateless/disposable app containers, external durable state, ALB health contract, idempotent startup, deployment/rollback plan, cost estimate, labeled observability | Introduce ALB/ASG for multi-instance capacity; keep app silos and fallback behavior. |
| ALB + ASG → ECS on EC2 | Per-app scaling differs materially, Compose deploys cause unrelated app coupling, or host utilization is inefficient | Container images, task/resource definitions, service health, task-level logs/metrics, IAM scopes, service rollback, cluster capacity plan | Move selected services first; do not require a portfolio-wide rewrite. |
| ECS on EC2 → Fargate consideration | Host patching/capacity operations dominate, task utilization is predictable, and Fargate cost is acceptable | Task portability, network/security model, startup/scale measurements, cost comparison, secrets/logging design, rollback | Run a separate Fargate evaluation; no automatic migration. |
| ECS/Fargate → EKS consideration | Kubernetes is a product/platform objective or required capabilities cannot be met reasonably by ECS | Kubernetes operating model, team competence, cluster security/upgrade plan, workload justification, cost/complexity case | Approve a separate EKS ADR and implementation task only if evidence is strong. |

Traffic alone is not sufficient. A migration requires operational evidence,
data-boundary readiness, rollback confidence, and a cost/reliability tradeoff.

## Operational acceptance evidence by phase

| Phase | Required evidence before calling the phase accepted |
| --- | --- |
| Phase 1: single EC2/Compose | Health endpoint checks for each app; deployment version visible; manual rollback plan; host config boundary documented; app data paths separated; labeled logs visible; AI budget/kill switch behavior tested offline; backup/restore expectations recorded; rough AWS cost visibility. |
| Phase 2: production-shaped EC2 | Secret/config source and precedence documented; no durable state depends on disposable containers; app database/storage boundaries verified; structured logs/metrics and dashboards visible; version/health checks survive restart; AI kill switch blocks live calls safely; backup restore is rehearsed or evidenced; cost and retention reports exist. |
| Phase 3: ALB + ASG | ALB health checks and routing contract; deployment version and rollback across instances; instance replacement test; stateless startup; external data access; app-labeled logs/metrics; AI budgets consistent across replicas; backup/restore and cost alarms; no public route/DNS change without separate approval. |
| Phase 4: ECS on EC2 | Task/service health; desired-count and deployment evidence; per-service rollback; cluster capacity/placement behavior; task-level config/secrets/logging; app data isolation; AI limits enforced consistently across tasks; backup/restore, cost, and alarm visibility. |
| Later Fargate/EKS | Separate approved evaluation with health, version, rollback, secret/config, data boundaries, logs/metrics, AI controls, backup/restore, and cost evidence comparable to the target platform. |

The evidence is a go/no-go checklist, not an implementation performed by this
ADR.

## Boundaries with Cookbook AI and future retrieval

Cookbook AI remains one app silo. Its canonical recipes, adapter contract,
sidecar sessions, provider policy, usage limits, and RAG/index boundaries are
Cookbook-owned. An optional local retrieval backend such as the QMD candidate
must remain behind the sidecar retrieval adapter and may not read another app's
records or write directly to the Cookbook database.

The platform metadata layer can report safe RAG/index status, retrieval backend
name, freshness class, and error reason. It must not centralize raw recipe
content, generated indexes, embeddings, prompts, or provider bodies.

## Explicit non-goals

This ADR does not:

- create AWS resources or deploy anything;
- add Terraform, CDK, CloudFormation, or GitHub Actions deployment workflows;
- change DNS, Cloudflare, routes, certificates, or public exposure;
- add database migrations, production auth, payment, or subscription systems;
- implement ECS, EKS, Fargate, ALB, ASG, RDS, S3, CloudWatch, SSM, or Secrets
  Manager resources;
- change provider routing, add a secondary provider, or make live OpenAI calls;
- add vector databases, embeddings, QMD runtime, or retrieval implementation;
- rewrite the upstream Vanilla Cookbook UI or run browser automation;
- commit raw datasets, generated indexes, secrets, prompts, provider outputs,
  traces, screenshots, or local environment values.

## Follow-on implementation tasks

Only after a separate approval and phase trigger should follow-on tasks address:

1. Phase 1 host/app boundary inventory and resource limits.
2. Phase 2 externalized configuration, durable state, logging, health/version,
   backup/restore, and AI budget evidence.
3. Portfolio metadata schema and private operator reporting.
4. ALB/ASG design and implementation after Phase 2 acceptance.
5. ECS-on-EC2 service decomposition after ALB/ASG evidence.
6. Separate Fargate or EKS evaluation only when the decision table triggers.

Each task must preserve the app silo model, offline/mock validation, and
explicit non-goals above.

