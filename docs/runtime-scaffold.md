# Vanilla Cookbook Runtime Scaffold

This repository contains the deployment scaffold for running Vanilla Cookbook on
an EC2 host and publishing it through Cloudflare Tunnel.

For the complete first-run order across AWS, GitHub, EC2, and Cloudflare, start
with `docs/first-deploy-guide.md`.

## Files

- `docker-compose.yml` runs the stable Vanilla Cookbook image and the official
  Cloudflare Tunnel client, plus the minimal `ai-api` FastAPI sidecar scaffold.
  Cookbook persists the SQLite database in `db/` and uploads in `uploads/`.
- `.env.example` documents the runtime configuration without containing usable
  credentials.
- `.gitignore` prevents local secrets, runtime data, private keys, Terraform
  state, and common generated files from being committed.
- `deploy.sh` updates and restarts the stack from `/opt/cookbook` on the future
  EC2 host.

## Local Use

Docker with the Compose plugin is required.

```bash
cp .env.example .env
mkdir -p db uploads
```

Replace `CLOUDFLARE_TUNNEL_TOKEN=replace_me` in `.env` with a real tunnel token,
then start the stack:

```bash
docker compose pull
docker compose up -d
docker compose ps
```

For app-only local testing, start `app` and browse to `http://127.0.0.1:3000`:

```bash
docker compose up -d app
```

The `ai-api` service is wired into the Compose network without a host port. It
currently exposes `GET /health` and `GET /ai/config` only to other Compose
services. It does not read the cookbook database or call live AI providers yet.

The production `ORIGIN` remains `https://cookbook.roadmaps.link`. Use
`ORIGIN=http://localhost:3000` in the untracked `.env` when testing login flows
locally.

## Configuration And Secrets

Never commit `.env` or credentials. GitHub Actions should create or update the
host's `/opt/cookbook/.env` from protected repository or environment settings at
deployment time. Prefer AWS OIDC with a short-lived role session instead of
static AWS access keys.

GitHub Actions secrets:

```text
CLOUDFLARE_TUNNEL_TOKEN
OPENAI_API_KEY
AWS_ROLE_ARN
```

GitHub Actions variables:

```text
AWS_REGION
EC2_INSTANCE_ID
ORIGIN
APP_DIR
DOMAIN
```

`ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` are also sensitive if enabled and must
be stored as GitHub Actions secrets. `OLLAMA_BASE_URL` is configuration and can
be a GitHub Actions variable unless its value discloses private infrastructure.
The AI sidecar reports only whether provider settings are configured; it does
not return secret values.

## Network Model

The app publishes port 3000 only on `127.0.0.1`, so it is reachable from the EC2
host but not from the public network interface. No inbound HTTP or HTTPS port is
published by this stack.

Cloudflare Tunnel makes an outbound connection to Cloudflare and routes
`cookbook.roadmaps.link` to the app service. This avoids opening inbound web
ports on the EC2 security group, keeps the origin address private, and lets
Cloudflare terminate public TLS.

Follow `docs/cloudflare-tunnel-setup.md` for tunnel and DNS setup. After
deployment, validate EC2 locally with `scripts/verify-local-compose.sh` and the
public route with `scripts/verify-cloudflare-route.sh`.

Use `docs/backup-restore.md` for runtime-data recovery and
`docs/operations-runbook.md` for routine start, deploy, verify, backup, and stop
procedures.
