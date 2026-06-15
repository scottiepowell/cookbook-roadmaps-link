# Day-2 Operations Runbook

Use the manual **Cookbook EC2 Control** GitHub Actions workflow for routine EC2
and deployment actions. Use Systems Manager, not SSH, for host diagnostics.
For initial setup and the first live run, complete
`docs/first-deploy-guide.md` before using this day-2 sequence.

## Start And Inspect

1. Run workflow action `status` to check the current EC2 state.
2. Run `start` and wait for EC2 status checks when the host is stopped.
3. Confirm Systems Manager reports the instance online.

## Deploy And Verify

1. Create a data backup before upgrades or significant changes:

   ```bash
   cd /opt/cookbook
   docker compose stop
   sudo APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
     bash scripts/backup-cookbook-data.sh
   ```

   The following deployment starts the services again.

2. Run workflow action `deploy` with `stop_after_deploy` disabled while
   validating a change.
3. Through Systems Manager, verify the local stack:

   ```bash
   APP_DIR=/opt/cookbook bash /opt/cookbook/scripts/verify-local-compose.sh
   ```

4. From an external machine, verify the public route:

   ```bash
   bash scripts/verify-cloudflare-route.sh cookbook.roadmap.links
   ```

5. Check the browser flow at `https://cookbook.roadmap.links`.

## Back Up And Stop

For a consistent end-of-session backup, stop Compose, create the archive, then
stop EC2 through the workflow:

```bash
cd /opt/cookbook
docker compose stop
sudo APP_DIR=/opt/cookbook BACKUP_DIR=/opt/cookbook-backups \
  bash scripts/backup-cookbook-data.sh
```

Run workflow action `stop`. EBS storage and retained backups can still incur
charges while compute is stopped.

## Troubleshooting

Safe status commands:

```bash
systemctl status docker --no-pager
systemctl status amazon-ssm-agent --no-pager
systemctl status snap.amazon-ssm-agent.amazon-ssm-agent --no-pager
cd /opt/cookbook
docker compose ps --all --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'
curl --fail --silent --show-error --output /dev/null http://127.0.0.1:3000/
df -h /opt/cookbook /opt/cookbook-backups
```

For targeted logs, inspect only the service needed and limit output:

```bash
docker compose logs --tail 100 app
```

Avoid `set -x`, `env`, `printenv`, `cat .env`, unfiltered `docker inspect`, and
the full `cloudflared` container command. Those can expose the tunnel token or
other secrets. Do not paste `.env`, SSM command payloads, or unredacted logs
into issues or chat.

If the local app works but the public route fails, follow
`docs/cloudflare-tunnel-setup.md`. If data is damaged or missing, stop services
and follow `docs/backup-restore.md` rather than editing SQLite files directly.

## Weekend Lab Rhythm

1. Start EC2 and check status.
2. Back up before upgrades or first real use.
3. Deploy, then verify locally and publicly.
4. Use the app and record any operational issue without secrets.
5. Stop Compose for a consistent end-of-session backup.
6. Stop EC2 when the lab is idle.
