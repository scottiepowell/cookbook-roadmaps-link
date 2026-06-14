# Task 0006: Create backup, restore, and day-2 operations runbook

## Goal

Create backup, restore, and day-2 operations assets for the Vanilla Cookbook deployment.

This task should create safe scripts and documentation only. Do not configure real AWS resources, do not upload data to cloud storage, and do not commit secrets.

## Project context

Vanilla Cookbook runtime data is expected to live under the app directory on the EC2 host:

```text
/opt/cookbook/db
/opt/cookbook/uploads
```

The app is deployed with Docker Compose and published through Cloudflare Tunnel at:

```text
https://cookbook.roadmap.links
```

Current project pieces:

- Task 0002 created Docker Compose runtime files.
- Task 0003 created the GitHub Actions EC2 control and SSM deployment workflow.
- Task 0004 created EC2 bootstrap and preflight assets.
- Task 0005 created Cloudflare Tunnel/DNS runbook and verification scripts.

Before putting real recipes into the app, the project needs a simple backup and restore story.

## Important rules

- Do not commit secrets.
- Do not create fake credentials.
- Do not upload backups anywhere in this task.
- Do not call AWS, Cloudflare, or OpenAI APIs.
- Do not print `.env` contents.
- Do not include real bucket names, account IDs, tokens, or keys.
- Keep scripts safe, readable, and manual-run friendly.
- Prefer local tarball backups first; cloud sync can be documented as a future optional step.

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

### 2. Create `scripts/backup-cookbook-data.sh`

Create a Bash script intended to run on the EC2 host.

Requirements:

- Use `set -euo pipefail`.
- Default `APP_DIR` to `/opt/cookbook`, overridable through the environment.
- Default `BACKUP_DIR` to `/opt/cookbook-backups`, overridable through the environment.
- Create the backup directory if missing.
- Back up only runtime data:
  - `db/`
  - `uploads/`
- Do not back up `.env`.
- Create a timestamped `.tar.gz` archive.
- Write a small `.sha256` checksum file next to the archive.
- Print the backup filename, size, and checksum path.
- Exit nonzero if required runtime folders are missing.
- Do not print secrets.

Optional but useful:

- Include a `--dry-run` mode.
- Include a `--quiet` mode if simple to implement.

### 3. Create `scripts/restore-cookbook-data.sh`

Create a Bash restore script intended to run on the EC2 host.

Requirements:

- Use `set -euo pipefail`.
- Default `APP_DIR` to `/opt/cookbook`, overridable through the environment.
- Require a backup archive path as the first argument.
- Verify the archive exists.
- If a matching `.sha256` file exists, verify it before restore.
- Refuse to restore if Docker Compose services are running, unless a clear `--force` flag is used.
- Restore only `db/` and `uploads/` into `APP_DIR`.
- Before overwriting, create a safety backup of the current `db/` and `uploads/` if present.
- Do not touch or print `.env`.
- Print concise restore results.

### 4. Create `scripts/list-cookbook-backups.sh`

Create a small helper script that lists local backup archives.

Requirements:

- Use `set -euo pipefail`.
- Default `BACKUP_DIR` to `/opt/cookbook-backups`, overridable through the environment.
- Print backup archive names, sizes, and modification times.
- Do not fail if the backup directory does not exist; print a useful message.

### 5. Create `docs/backup-restore.md`

Document the backup and restore process.

Include:

- What data is backed up.
- What is intentionally not backed up, especially `.env` and secrets.
- How to run a backup manually.
- How to list backups.
- How to restore safely.
- How to verify after restore using existing verification scripts.
- Recommended timing: backup before upgrades and before first real use.
- Future optional improvement: sync encrypted backups to S3 or another storage location through GitHub Actions or SSM, but do not implement that yet.
- Cost and security notes for retained backups.

### 6. Create `docs/operations-runbook.md`

Create a concise day-2 operations runbook.

Include:

- Start EC2.
- Check status.
- Deploy.
- Verify local Compose.
- Verify Cloudflare route.
- Back up data.
- Stop EC2.
- Common troubleshooting commands.
- Safe log inspection guidance that avoids printing `.env` or Cloudflare token values.
- A simple operating rhythm for weekend lab use.

### 7. Update related docs if useful

Add minimal references to the new backup/restore and operations docs in:

- `docs/github-settings-checklist.md`
- `docs/github-actions-deploy-workflow.md`
- `docs/cloudflare-tunnel-setup.md`
- `docs/runtime-scaffold.md`

Only update files where the link is genuinely useful.

### 8. Validate as much as possible

Run:

```bash
git diff --check
bash -n deploy.sh
bash -n scripts/bootstrap-ec2-runtime.sh
bash -n scripts/preflight-ec2-runtime.sh
bash -n scripts/verify-cloudflare-route.sh
bash -n scripts/verify-local-compose.sh
bash -n scripts/backup-cookbook-data.sh
bash -n scripts/restore-cookbook-data.sh
bash -n scripts/list-cookbook-backups.sh
```

If `shellcheck` is available, run it on all scripts. If it is not available, do not install it just for this task. Mention availability in the outbox report.

Do not run AWS, Cloudflare, or OpenAI commands.

### 9. Create outbox report

Create:

```text
outbox/0006-create-backup-restore-operations-runbook-results.md
```

The report should include:

- Summary of changes.
- Files created or modified.
- Git status before and after.
- Validation performed.
- Assumptions made.
- Any blockers.
- Recommended next task.

### 10. Commit changes

If possible, commit with:

```bash
git add scripts/backup-cookbook-data.sh scripts/restore-cookbook-data.sh scripts/list-cookbook-backups.sh docs/backup-restore.md docs/operations-runbook.md docs/github-settings-checklist.md docs/github-actions-deploy-workflow.md docs/cloudflare-tunnel-setup.md docs/runtime-scaffold.md outbox/0006-create-backup-restore-operations-runbook-results.md
git commit -m "mailbox: complete task 0006 backup restore operations runbook"
```

If some documentation files are unchanged, omit them from `git add`.

Push if remote access is configured.

If push fails, document the blocker in the outbox report.

## Done criteria

This task is complete when:

- `scripts/backup-cookbook-data.sh` exists.
- `scripts/restore-cookbook-data.sh` exists.
- `scripts/list-cookbook-backups.sh` exists.
- `docs/backup-restore.md` exists.
- `docs/operations-runbook.md` exists.
- Related docs link to the new runbooks where useful.
- Validation has been performed.
- An outbox report exists.
- Changes are committed and pushed if possible.
- No secrets are committed.
