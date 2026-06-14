# Backup And Restore

The local backup tools protect Vanilla Cookbook runtime data before recipes are
added, before upgrades, and before risky maintenance. They do not upload data or
call cloud APIs.

## Backup Scope

Backups contain only these directories from `/opt/cookbook`:

```text
db/
uploads/
```

The SQLite database, application-generated backups, and uploaded images are
therefore included. Source code, Docker images, Git metadata, Compose files, and
`.env` are intentionally excluded. Secrets must continue to live in GitHub
Actions settings and the protected host `.env`, never in backup archives.

## Create A Backup

For the most consistent snapshot, stop Compose before a manual backup so the
database and uploads are not changing:

```bash
cd /opt/cookbook
docker compose stop
sudo APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
  bash scripts/backup-cookbook-data.sh
docker compose start
```

Preview the operation without writing an archive:

```bash
APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
  bash scripts/backup-cookbook-data.sh --dry-run
```

Each archive is named `cookbook-data-<UTC_TIMESTAMP>.tar.gz` and has a matching
`.sha256` file. Back up before upgrades, before the first real recipe is entered,
and after significant data changes.

## List Backups

```bash
BACKUP_DIR=/opt/cookbook-backups bash scripts/list-cookbook-backups.sh
```

The helper prints archive names, sizes, and UTC modification times. Confirm
there is enough disk space for both retained archives and restore safety copies.

## Restore Safely

1. Start EC2 and connect through Systems Manager.
2. List backups and choose the intended archive.
3. Stop all Compose services:

   ```bash
   cd /opt/cookbook
   docker compose down
   ```

4. Restore the archive:

   ```bash
   sudo APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
     bash scripts/restore-cookbook-data.sh \
     /opt/cookbook-backups/<BACKUP_ARCHIVE>.tar.gz
   ```

The restore verifies a matching checksum when present, rejects archive content
outside `db/` and `uploads/`, refuses to run while Compose services are active,
and creates a pre-restore safety backup of current data. `--force` bypasses only
the service-state check and should be used only after independently confirming
the services cannot write data.

5. Start and verify the deployment:

   ```bash
   cd /opt/cookbook
   docker compose up -d
   APP_DIR=/opt/cookbook bash scripts/verify-local-compose.sh
   bash scripts/verify-cloudflare-route.sh cookbook.roadmap.links
   ```

Open the app and verify recipes and images. Keep the pre-restore safety archive
until the restored data has been checked.

## Retention, Cost, And Security

Backups can contain personal recipe data and uploaded images. Restrict access to
`/opt/cookbook-backups`, retain only the copies required for recovery, and
remove obsolete archives deliberately. Local backups consume EBS storage even
while EC2 is stopped and may increase snapshot costs.

A future improvement can encrypt archives and sync them to a private S3 bucket
or another storage service through GitHub Actions or Systems Manager. That flow
should use short-lived AWS credentials, retention rules, encryption, and tested
restore procedures. It is not implemented by the current scripts.
