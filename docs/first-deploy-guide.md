# First Deploy Guide

Use this exact order for the first deployment to `https://cookbook.roadmaps.link`. Put live values only in AWS, GitHub, or Cloudflare control planes.

## 1. Confirm Repo And Coder Workspace

```bash
cd /home/coder/repo
git status --short --branch
git remote -v
```

Confirm `main`, expected `origin`, and no unreviewed changes. Run the [repository validator](repo-validation.md), then review [repo map](repo-map.md), [runtime](runtime-scaffold.md), and [architecture](architecture.md). Confirm no `.env`, credentials, keys, `db/`, or `uploads/` are tracked.

## 2. Prepare AWS EC2 Host

Create current Ubuntu Server with encrypted EBS and outbound HTTPS. Do not open inbound HTTP/HTTPS. Restrict temporary SSH to your IP and remove it after SSM works. Follow [EC2 Bootstrap](ec2-runtime-bootstrap.md):

```bash
sudo RUNTIME_USER=ubuntu bash scripts/bootstrap-ec2-runtime.sh
sudo RUNTIME_USER=ubuntu bash scripts/preflight-ec2-runtime.sh
```

Resolve failures; port 3000 not listening is expected before deployment.

## 3. Configure AWS IAM OIDC And Instance Profile

Attach `AmazonSSMManagedInstanceCore` or equivalent to the instance profile and confirm SSM is online. Create the repository- and `main`-scoped provider and workflow role in [AWS OIDC](aws-github-oidc-policy.md). Do not create static AWS keys.

## 4. Configure GitHub Actions

Complete the [settings checklist](github-settings-checklist.md).

Secrets: `AWS_ROLE_ARN`, `CLOUDFLARE_TUNNEL_TOKEN`; optional `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY`.

```text
AWS_REGION=<AWS_REGION>
EC2_INSTANCE_ID=<EC2_INSTANCE_ID>
ORIGIN=https://cookbook.roadmaps.link
APP_DIR=/opt/cookbook
DOMAIN=cookbook.roadmaps.link
```

`OLLAMA_BASE_URL` is optional. Sensitive values belong in secrets.

## 5. Configure Cloudflare Tunnel

Follow [Cloudflare setup](cloudflare-tunnel-setup.md). Create the tunnel, store its token in `CLOUDFLARE_TUNNEL_TOKEN`, and route `cookbook.roadmaps.link` to `http://app:3000`. Confirm proxied DNS. Do not point an A record at EC2 or open web ports.

## 6. Run GitHub Actions In Order

Open **Actions** > **Cookbook EC2 Control** and use the [workflow guide](github-actions-deploy-workflow.md):

1. `status`
2. `start`
3. Confirm Systems Manager is online.
4. `deploy` with `stop_after_deploy=false`

Do not continue until deployment succeeds.

## 7. Run Local EC2 Verification

```bash
sudo APP_DIR=/opt/cookbook \
  bash /opt/cookbook/scripts/verify-local-compose.sh
```

Run through SSM and resolve local failures first. The script does not print `.env` or the token.

## 8. Run Public Route Verification

```bash
cd /home/coder/repo
bash scripts/verify-cloudflare-route.sh cookbook.roadmaps.link
```

Run outside EC2 and confirm DNS, HTTPS, and final URL.

## 9. Create Or Verify First Admin

Open the public URL. Create the first admin or verify the expected admin can sign in. Never record credentials in Git, issues, logs, or reports.

## 10. Create First Backup

Follow [Backup and Restore](backup-restore.md):

```bash
cd /opt/cookbook
docker compose stop
sudo APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
  bash scripts/backup-cookbook-data.sh
docker compose start
BACKUP_DIR=/opt/cookbook-backups bash scripts/list-cookbook-backups.sh
```

Confirm the archive and `.sha256`; only `db/` and `uploads/` are included.

## 11. Stop EC2

After final verification, run workflow action `stop` and confirm the instance stops. See [Operations](operations-runbook.md). Retained EBS and other resources may still cost money.
