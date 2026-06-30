# Architecture

Vanilla Cookbook runs as a two-service Docker Compose project on one EC2 host.

## Plain-Text Diagram

```text
Coder/Codex -> GitHub -> GitHub Actions --OIDC--> IAM role
                              |
                              +-- EC2 control + SSM deployment
                                               |
Browser -> Cloudflare edge -> outbound tunnel -> EC2 Compose
                                                   +-- app:3000
                                                   +-- db/ + uploads/
Local backup: db/ + uploads/ -> /opt/cookbook-backups/*.tar.gz + checksum
```

## Components

- Coder/Codex: workspace and mailbox execution.
- GitHub: desired source and documentation state.
- GitHub Actions: manual `status`, `start`, `deploy`, `restart`, and `stop`.
- AWS OIDC role: short-lived, repository-scoped EC2/SSM access.
- EC2 and Systems Manager: runtime host and administration without routine SSH.
- Docker Compose: Vanilla Cookbook and `cloudflared`.
- Cloudflare: public TLS and routing to `http://app:3000`.

The proposed AI expansion keeps Vanilla Cookbook as a black-box service and
adds a FastAPI sidecar. See [AI Sidecar Architecture](ai-sidecar-architecture.md)
and [AI Medium-Path Roadmap](ai-medium-path-roadmap.md).

## Runtime Flow

Browser traffic reaches Cloudflare, crosses the outbound tunnel, and is routed by `cloudflared` to Compose service `app:3000`. Cookbook persists SQLite data and uploads in host-mounted `db/` and `uploads/`. The host mapping `127.0.0.1:3000:3000` supports local checks without public exposure.

## Deployment Flow

An operator starts the manual workflow. GitHub exchanges OIDC identity for a short-lived role, controls EC2, waits for SSM, then updates `/opt/cookbook`, writes protected `.env`, and runs `deploy.sh`. The script fast-forwards source, pulls images, and reconciles Compose.

## Secrets Flow

Sensitive values enter only through GitHub Actions secrets. Deployment carries them in the privileged SSM payload and writes `/opt/cookbook/.env` mode `0600` without printing it. AWS uses OIDC, not static keys; non-sensitive settings use variables. Restrict GitHub settings, IAM, SSM history, host `.env`, and backups.

## Backup And Restore Flow

Backup archives only `db/` and `uploads/` with a SHA-256 checksum, excluding source and `.env`. Restore validates checksum and paths, requires stopped services unless overridden, and creates a safety backup. See [Backup and Restore](backup-restore.md).

## Intentionally Not Exposed

No inbound HTTP/HTTPS, public port 3000, routine public SSH, committed secrets/account IDs/keys, runtime data in Git, or automatic cloud-resource creation.
