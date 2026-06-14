#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=${BACKUP_DIR:-/opt/cookbook-backups}

if [[ ! -d $BACKUP_DIR ]]; then
  echo "Backup directory does not exist: $BACKUP_DIR"
  exit 0
fi

shopt -s nullglob
archives=("$BACKUP_DIR"/cookbook-data-*.tar.gz)
if ((${#archives[@]} == 0)); then
  echo "No Cookbook backup archives found in $BACKUP_DIR"
  exit 0
fi

printf '%-52s %10s  %s\n' "ARCHIVE" "SIZE" "MODIFIED (UTC)"
for archive in "${archives[@]}"; do
  printf '%-52s %10s  %s\n' \
    "$(basename "$archive")" \
    "$(du -h "$archive" | awk '{print $1}')" \
    "$(date -u -r "$archive" '+%Y-%m-%d %H:%M:%S')"
done
