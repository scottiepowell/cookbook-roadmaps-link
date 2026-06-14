# Task 0006 Results: Backup, Restore, And Operations Runbook

## Summary

Created local runtime-data backup, restore, and listing scripts plus backup and
day-2 operations documentation. Backups contain only `db/` and `uploads/`, use
timestamped compressed archives and checksums, and never include or print
`.env`. Restore validates archive scope, checks service state, and creates a
pre-restore safety backup.

## Files Created Or Modified

- Created `scripts/backup-cookbook-data.sh`.
- Created `scripts/restore-cookbook-data.sh`.
- Created `scripts/list-cookbook-backups.sh`.
- Created `docs/backup-restore.md`.
- Created `docs/operations-runbook.md`.
- Updated related runtime, deployment, settings, and Cloudflare docs with
  minimal links to the new runbooks.
- Created `outbox/0006-create-backup-restore-operations-runbook-results.md`.

## Repository Inspection

- Working directory: `/home/coder/repo`.
- Branch: `main`.
- Remote: `origin` uses
  `https://github.com/scottiepowell/cookbook-roadmaps-link.git`.
- The working tree was clean and synchronized with `origin/main` after
  fast-forwarding to the commit that added inbox task 0006.
- Runtime data was already mapped to host `db/` and `uploads/` directories and
  excluded from Git; no manual backup or restore tools existed.
- The task's repeated full inspection command stalled in the host execution
  layer and was terminated, but the equivalent repository state had already
  been captured during task discovery.

## Git Status

- Before: clean `main`, synchronized with `origin/main`.
- After implementation: only task 0006 scripts, runbooks, related links, and
  this report are changed or added.

## Validation

- `git diff --check` passed.
- `bash -n` passed for `deploy.sh` and every script in `scripts/`.
- `shellcheck` was unavailable and was not installed, as required by the task.
- All three new scripts were verified as executable.
- Disposable sample data passed dry-run, backup, checksum creation, listing,
  restore, and pre-restore safety-backup tests.
- Restore recovered both runtime directories while leaving a sentinel `.env`
  unchanged.
- Restore rejected unexpected archive paths, symbolic links/special entries, and
  a mismatched checksum with nonzero exits.
- A content scan found no common static AWS, GitHub, OpenAI, or private-key
  credential formats.

## Assumptions

- The EC2 host provides GNU tar, GNU coreutils, Bash, and Docker Compose.
- Operators can use sudo when `/opt/cookbook` or `/opt/cookbook-backups` requires
  elevated filesystem access.
- A consistent manual backup is made while Compose services are stopped; the
  backup script itself remains usable for operator-controlled snapshots.
- `--force` on restore is an explicit operator override only for the service
  state check, not for checksum or archive-scope validation.

## Blockers

- None during implementation.

## Commit And Push

- Commit message: `mailbox: complete task 0006 backup restore operations runbook`.
- Push target: `origin/main`; no pre-push blocker was identified.

## Recommended Next Task

Exercise backup and restore on disposable sample data before first real use,
record recovery time and retained archive size, then design an encrypted offsite
retention workflow without changing the local recovery path.
