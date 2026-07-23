# 0032A portfolio platform AWS scaling architecture ADR results

Created [Portfolio Platform AWS Scaling Architecture ADR](../docs/portfolio-platform-aws-scaling-architecture-adr.md).

The platform path decision is EC2-first and staged:

1. single EC2 portfolio host with Docker Compose;
2. production-shaped single EC2 with externalized config, durable data, logs,
   health/version reporting, backups, and AI controls;
3. ALB plus EC2 Auto Scaling Group;
4. ECS on EC2 for per-service scaling;
5. Fargate or EKS only if later evidence justifies them.

The ADR defines the app boundary model, shared infrastructure model, conceptual
portfolio metadata records, AI provider usage/budget/kill-switch controls,
RAG/index boundaries, migration triggers, and operational acceptance evidence
for each phase. It preserves the rule: `Shared infrastructure is acceptable.
Shared uncontrolled state is not.`

Updated `docs/portfolio-platform-aws-scaling-brainstorm.md`,
`docs/ai-feature-status.md`, `docs/ai-implementation-backlog.md`, and
`README.md`.

Validation passed: full repository validator (353 tests), Docker Compose
configuration, and `git diff --check`. Live smoke/eval wrappers were not
allowed to opt in, so no live OpenAI call was made. No AWS resources were
created or deployed.

Explicit non-goals: no Terraform, CDK, CloudFormation, GitHub Actions deploy
workflow, deployment, DNS/Cloudflare change, database migration, auth,
payment, public route, provider routing, secondary provider, vector DB,
embeddings, ECS/EKS/Fargate implementation, UI rewrite, browser automation,
raw datasets/indexes, secrets, prompts, provider outputs, traces, screenshots,
or local environment values.
