# Task 0005: Create Cloudflare Tunnel and DNS runbook

## Goal

Create Cloudflare Tunnel and DNS preparation assets for publishing Vanilla Cookbook at:

https://cookbook.roadmap.links

This task should create documentation and safe verification scripts only. Do not create Cloudflare resources, do not call real Cloudflare APIs, and do not commit secrets.

## Project context

Current project pieces:

- Task 0002 created Docker Compose runtime files for Vanilla Cookbook and Cloudflare Tunnel.
- Task 0003 created the GitHub Actions EC2 control and SSM deployment workflow.
- Task 0004 created EC2 bootstrap and preflight assets.
- The next practical step is documenting and validating the Cloudflare Tunnel and DNS path before the first deployment.

The intended network model is:

```text
User browser
  -> https://cookbook.roadmap.links
  -> Cloudflare edge
  -> Cloudflare Tunnel
  -> cloudflared container on EC2
  -> app service on Docker Compose network
  -> Vanilla Cookbook on port 3000
```

The EC2 security group should not expose inbound HTTP or HTTPS for the app.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not print Cloudflare tunnel tokens.
- Do not call Cloudflare APIs in this task.
- Do not require `cloudflared` to be installed locally.
- Keep all instructions copy-paste friendly.
- Treat `CLOUDFLARE_TUNNEL_TOKEN` as a GitHub Actions secret only.
- Use placeholders for any account-specific values.

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

### 2. Create `docs/cloudflare-tunnel-setup.md`

Create a runbook that explains how to create and configure the Cloudflare Tunnel manually in the Cloudflare Zero Trust dashboard.

Include:

- Purpose of the tunnel.
- Expected public hostname: `cookbook.roadmap.links`.
- Expected service target: `http://app:3000` when using the Compose network.
- Why the service target should use `app` instead of `localhost` inside Compose.
- Where to store the tunnel token: GitHub Actions secret `CLOUDFLARE_TUNNEL_TOKEN`.
- DNS expectations for `cookbook.roadmap.links`.
- What not to do, including not opening inbound EC2 port 3000 to the internet.
- First-deploy validation steps.
- Troubleshooting notes for common failures:
  - tunnel token missing
  - Cloudflare hostname not configured
  - Docker Compose service not healthy
  - wrong service URL such as `localhost:3000` from the tunnel container
  - app origin mismatch

Do not include a real token.

### 3. Create `scripts/verify-cloudflare-route.sh`

Create a Bash script for checking the public route after deployment.

Requirements:

- Use `set -euo pipefail`.
- Default domain should be `cookbook.roadmap.links`.
- Allow overriding the domain with the first argument.
- Check DNS resolution with available tools such as `getent`, `dig`, or `nslookup` if present.
- Check HTTPS reachability with `curl`.
- Print HTTP status code, final URL, and basic timing if available.
- Do not print secrets.
- Exit nonzero if HTTPS check fails.
- Keep the script portable and readable.

### 4. Create `scripts/verify-local-compose.sh`

Create a Bash script intended to run on the EC2 host after deployment.

Requirements:

- Use `set -euo pipefail`.
- Default app directory should be `/opt/cookbook`, overridable through `APP_DIR`.
- Check that `docker-compose.yml` exists.
- Check that `.env` exists but do not print it.
- Run `docker compose ps` if available.
- Check whether the app is reachable from the host at `http://127.0.0.1:3000`.
- Check whether the Cloudflare container appears present or running.
- Print useful diagnostics without exposing secrets.
- Exit nonzero if the local app check fails.

### 5. Update related documentation if useful

Update these files only if the links are useful and minimal:

- `docs/runtime-scaffold.md`
- `docs/ec2-runtime-bootstrap.md`
- `docs/github-settings-checklist.md`
- `docs/github-actions-deploy-workflow.md`

Add references to the new Cloudflare tunnel runbook and verification scripts where appropriate.

### 6. Validate as much as possible

Run:

```bash
git diff --check
bash -n deploy.sh
bash -n scripts/bootstrap-ec2-runtime.sh
bash -n scripts/preflight-ec2-runtime.sh
bash -n scripts/verify-cloudflare-route.sh
bash -n scripts/verify-local-compose.sh
```

If `shellcheck` is available, run it on all scripts. If it is not available, do not install it just for this task. Mention availability in the outbox report.

Do not run Cloudflare or AWS commands.

### 7. Create outbox report

Create:

```text
outbox/0005-create-cloudflare-tunnel-dns-runbook-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 8. Commit changes

If possible, commit with:

```bash
git add docs/cloudflare-tunnel-setup.md scripts/verify-cloudflare-route.sh scripts/verify-local-compose.sh docs/runtime-scaffold.md docs/ec2-runtime-bootstrap.md docs/github-settings-checklist.md docs/github-actions-deploy-workflow.md outbox/0005-create-cloudflare-tunnel-dns-runbook-results.md
git commit -m "mailbox: complete task 0005 cloudflare tunnel dns runbook"
```

If some documentation files are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `docs/cloudflare-tunnel-setup.md` exists.
- `scripts/verify-cloudflare-route.sh` exists.
- `scripts/verify-local-compose.sh` exists.
- Related docs link to the Cloudflare runbook where useful.
- Validation has been performed.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
