# Task 0004: Create EC2 runtime bootstrap and preflight assets

## Goal

Create the EC2 host bootstrap and preflight assets needed before running the GitHub Actions deployment workflow from task 0003.

This task should prepare scripts and documentation only. Do not create cloud resources, do not run AWS commands against real infrastructure, and do not commit secrets.

## Project context

This repo deploys Vanilla Cookbook to:

https://cookbook.roadmap.links

Current project pieces:

- Task 0002 created the Docker Compose runtime scaffold.
- Task 0003 created the GitHub Actions EC2 control and SSM deployment workflow.
- The next practical step is preparing the EC2 instance so GitHub Actions can control it through Systems Manager.

The EC2 runtime host should eventually:

- Be small and Free Tier friendly where eligible.
- Use Ubuntu Server if possible.
- Have an EBS-backed root volume so stop/start preserves data.
- Have Docker and the Docker Compose plugin installed.
- Have Git installed.
- Have AWS Systems Manager Agent installed and running.
- Have an instance profile with Systems Manager permissions.
- Store the app checkout at `/opt/cookbook`.
- Avoid exposing inbound HTTP/HTTPS because Cloudflare Tunnel will publish the app.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not hardcode AWS account IDs, access keys, Cloudflare tokens, OpenAI API keys, or GitHub tokens.
- Do not run commands that create or modify real AWS infrastructure.
- Keep all scripts reviewable and safe to run manually.
- Prefer SSM over SSH for routine operations.
- Use placeholders where account-specific values would be needed.
- Keep this task focused on host bootstrap and validation, not Terraform.

## Work to perform

### 1. Inspect current repo state

Run:

```bash
pwd
ls -la
git status
git remote -v || true
git branch --show-current || true
find . -maxdepth 4 -type f | sort
```

Record key findings in the outbox report.

### 2. Create `scripts/bootstrap-ec2-runtime.sh`

Create a Bash script intended to run on the future Ubuntu EC2 instance.

The script should:

- Use `set -euo pipefail`.
- Require root or use clear sudo assumptions.
- Install or verify:
  - `git`
  - `curl`
  - `ca-certificates`
  - `docker.io` or Docker Engine package available through the OS package manager
  - Docker Compose plugin if available
  - AWS SSM Agent if missing
- Enable and start Docker.
- Enable and start the SSM Agent when present.
- Create `/opt/cookbook`.
- Set reasonable ownership for `/opt/cookbook`.
- Print a concise status summary.

Do not write `.env` in this script. The GitHub Actions workflow should render `.env` later from GitHub settings.

The script should be idempotent so it can be run more than once.

### 3. Create `scripts/preflight-ec2-runtime.sh`

Create a Bash preflight script intended to run on the EC2 instance.

The script should check and report:

- Operating system information.
- Current user.
- Git availability.
- Docker availability.
- Docker Compose availability.
- Docker service status.
- SSM Agent service status.
- Whether `/opt/cookbook` exists.
- Whether `/opt/cookbook` is writable by the intended runtime user.
- Whether outbound HTTPS appears available using a safe test such as checking basic connectivity to GitHub or Cloudflare.
- Whether port `3000` is currently listening.

The script should not print secrets and should not fail hard on every warning. Prefer a final pass/warn/fail summary.

### 4. Create `docs/ec2-runtime-bootstrap.md`

Document the manual EC2 setup path.

Include:

- Recommended small-instance settings.
- EBS-backed storage note.
- Security group guidance: avoid inbound HTTP/HTTPS; allow SSH only temporarily from your IP if needed.
- Required instance profile: Systems Manager managed instance permissions.
- How to run the bootstrap script manually.
- How to run the preflight script manually.
- What GitHub repository variables need the EC2 instance ID and region.
- What should be done in Cloudflare later.
- Cost-control reminder: stop the instance when not using it, but remember EBS storage can still incur cost.

Do not include real account IDs, tokens, or secrets.

### 5. Create `docs/github-settings-checklist.md`

Create a checklist for the repository settings needed before first deployment.

Include sections for:

- GitHub Actions secrets.
- GitHub Actions variables.
- AWS IAM role/OIDC readiness.
- EC2 instance readiness.
- Cloudflare Tunnel readiness.
- First workflow run order.

Expected GitHub Actions secrets:

```text
AWS_ROLE_ARN
CLOUDFLARE_TUNNEL_TOKEN
OPENAI_API_KEY optional
ANTHROPIC_API_KEY optional
GOOGLE_API_KEY optional
```

Expected GitHub Actions variables:

```text
AWS_REGION
EC2_INSTANCE_ID
ORIGIN
APP_DIR
DOMAIN
OLLAMA_BASE_URL optional
```

Use documentation placeholders only. Do not include real values.

### 6. Update `docs/github-actions-deploy-workflow.md` if useful

If the existing deployment workflow documentation would benefit from a link to the new EC2 bootstrap document or settings checklist, update it.

Keep edits minimal.

### 7. Validate as much as possible

Run:

```bash
git diff --check
bash -n deploy.sh
bash -n scripts/bootstrap-ec2-runtime.sh
bash -n scripts/preflight-ec2-runtime.sh
```

If `shellcheck` is available, run it on the scripts. If it is not available, do not install it just for this task. Mention availability in the outbox report.

### 8. Create outbox report

Create:

```text
outbox/0004-create-ec2-runtime-bootstrap-and-preflight-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 9. Commit changes

If possible, commit with:

```bash
git add scripts/bootstrap-ec2-runtime.sh scripts/preflight-ec2-runtime.sh docs/ec2-runtime-bootstrap.md docs/github-settings-checklist.md docs/github-actions-deploy-workflow.md outbox/0004-create-ec2-runtime-bootstrap-and-preflight-results.md
git commit -m "mailbox: complete task 0004 ec2 runtime bootstrap and preflight"
```

If `docs/github-actions-deploy-workflow.md` is unchanged, omit it from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `scripts/bootstrap-ec2-runtime.sh` exists.
- `scripts/preflight-ec2-runtime.sh` exists.
- EC2 bootstrap documentation exists.
- GitHub settings checklist exists.
- Existing workflow documentation links to the new docs if useful.
- Validation has been performed.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
