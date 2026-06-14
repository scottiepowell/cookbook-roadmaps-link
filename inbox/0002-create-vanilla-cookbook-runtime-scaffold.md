# Task 0002: Create Vanilla Cookbook runtime scaffold

## Goal

Create the initial runtime scaffold for deploying Vanilla Cookbook with Docker Compose, Cloudflare Tunnel, GitHub Actions-managed secrets, and the custom domain:

https://cookbook.roadmap.links

This task should create the application deployment files only. Do not configure real AWS, Cloudflare, OpenAI, or GitHub secrets yet.

## Project context

This repo supports a weekend DevOps lab using:

- Coder as the development workspace.
- Codex as the coding agent.
- GitHub as the source repo.
- GitHub Actions as the deployment and secrets-management control plane.
- AWS EC2 as the small runtime VM.
- Docker Compose to run Vanilla Cookbook.
- Cloudflare Tunnel to expose the app.
- Custom domain: `cookbook.roadmap.links`.

The target app is Vanilla Cookbook.

Vanilla Cookbook should run on port `3000`.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not hardcode AWS keys, Cloudflare tokens, OpenAI API keys, GitHub tokens, or domain credentials.
- All sensitive values should be represented as GitHub Actions secrets or local `.env` placeholders.
- Use `.env.example` for documentation only.
- Keep `.env` ignored by git.
- Prefer GitHub Actions secrets and variables for deployment configuration.
- Prefer AWS OIDC later instead of static AWS access keys.
- Keep this task small and focused.

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
find . -maxdepth 3 -type f | sort
```

Record key findings in the outbox report.

### 2. Create `docker-compose.yml`

Create a Docker Compose file with two services:

1. `app`
2. `cloudflared`

The `app` service should:

- Use the Vanilla Cookbook stable image.
- Run on container port `3000`.
- Bind host port `3000` only to localhost using `127.0.0.1:3000:3000`.
- Use persistent folders for database and uploads.
- Use `env_file: .env`.
- Restart unless stopped.

The `cloudflared` service should:

- Use the official Cloudflare `cloudflared` image.
- Depend on the app service.
- Run the tunnel using `${CLOUDFLARE_TUNNEL_TOKEN}`.
- Restart unless stopped.

Do not expose inbound HTTP or HTTPS ports directly to the internet.

### 3. Create `.env.example`

Create `.env.example` with placeholders for:

```env
ORIGIN=https://cookbook.roadmap.links
CLOUDFLARE_TUNNEL_TOKEN=replace_me
PUID=1000
PGID=1000

# Optional Vanilla Cookbook LLM features
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
OLLAMA_BASE_URL=
```

### 4. Update `.gitignore`

Ensure `.gitignore` excludes:

```gitignore
.env
.env.*
!.env.example
db/
uploads/
*.pem
*.key
*.tfstate
*.tfstate.*
.DS_Store
node_modules/
__pycache__/
.pytest_cache/
```

### 5. Create `deploy.sh`

Create a simple deployment script for the future EC2 host.

Requirements:

- Use `set -euo pipefail`.
- Assume the app lives in `/opt/cookbook`.
- Pull latest git changes.
- Create `db` and `uploads` folders.
- Run `docker compose pull`.
- Run `docker compose up -d --remove-orphans`.
- Show `docker compose ps`.

Do not inject secrets in this script.

### 6. Create `docs/runtime-scaffold.md`

Document:

- What each file does.
- How to run locally with Docker Compose.
- How secrets should be handled.
- Which values should become GitHub Actions secrets.
- Which values should become GitHub Actions variables.
- Why the app binds to `127.0.0.1:3000`.
- Why Cloudflare Tunnel is used instead of opening inbound ports.

Use this secret/variable model:

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

### 7. Create outbox report

Create:

```text
outbox/0002-create-vanilla-cookbook-runtime-scaffold-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Any assumptions made.
- Any blockers.
- Recommended next task.

### 8. Commit changes

If possible, commit the completed task with:

```bash
git add docker-compose.yml .env.example .gitignore deploy.sh docs/runtime-scaffold.md outbox/0002-create-vanilla-cookbook-runtime-scaffold-results.md
git commit -m "mailbox: complete task 0002 vanilla cookbook runtime scaffold"
```

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `docker-compose.yml` exists.
- `.env.example` exists.
- `.gitignore` protects secrets and local runtime data.
- `deploy.sh` exists.
- `docs/runtime-scaffold.md` exists.
- The outbox report exists.
- Changes are committed if possible.
- No secrets are committed.
