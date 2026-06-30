# Vanilla Cookbook GitOps Lab

This mailbox-driven DevOps lab deploys Vanilla Cookbook to AWS EC2 at [cookbook.roadmaps.link](https://cookbook.roadmaps.link). Coder and Codex handle reviewed tasks, GitHub stores desired state, and GitHub Actions operates EC2 through AWS Systems Manager.

## Architecture

GitHub Actions assumes a repository-scoped AWS role through OIDC and deploys Docker Compose through Systems Manager. Vanilla Cookbook listens only on EC2 loopback; `cloudflared` creates the outbound public route.

```text
Coder + Codex -> GitHub -> GitHub Actions --OIDC/SSM--> AWS EC2
Browser -> Cloudflare edge -> Cloudflare Tunnel -> Docker Compose -> Cookbook
```

See [Architecture](docs/architecture.md).

## Technology

Coder, Codex, GitHub, GitHub Actions, AWS EC2, AWS Systems Manager, Docker Compose, and Cloudflare Tunnel.

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
- [AI sidecar architecture](docs/ai-sidecar-architecture.md)
- [AI evals plan](docs/ai-evals-plan.md)
- [AI implementation backlog](docs/ai-implementation-backlog.md)
- [Resume from Windows clone](docs/resume-from-windows-clone.md)
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

## Status

Runtime, EC2 control, bootstrap, verification, and backup/restore assets exist. An operator must still configure EC2, IAM and instance profile, GitHub settings, Cloudflare Tunnel/DNS, and the first admin user. The repository does not create cloud resources.
