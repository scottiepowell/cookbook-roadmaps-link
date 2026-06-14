#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/cookbook}
BACKUP_DIR=${BACKUP_DIR:-/opt/cookbook-backups}
dry_run=false
quiet=false

usage() {
  echo "Usage: $0 [--dry-run] [--quiet]"
}

while (($# > 0)); do
  case $1 in
    --dry-run) dry_run=true ;;
    --quiet) quiet=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

for runtime_dir in db uploads; do
  if [[ ! -d $APP_DIR/$runtime_dir ]]; then
    echo "Missing required runtime directory: $APP_DIR/$runtime_dir" >&2
    exit 1
  fi
done

timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive_name="cookbook-data-$timestamp.tar.gz"
archive_path="$BACKUP_DIR/$archive_name"
checksum_path="$archive_path.sha256"

if [[ $dry_run == true ]]; then
  echo "Dry run: would create $archive_path from $APP_DIR/db and $APP_DIR/uploads"
  echo "Dry run: .env and application source files are excluded"
  exit 0
fi

mkdir -p "$BACKUP_DIR"
tar -C "$APP_DIR" -czf "$archive_path" db uploads
(
  cd "$BACKUP_DIR"
  sha256sum "$archive_name" > "$archive_name.sha256"
)

if [[ $quiet == false ]]; then
  size=$(du -h "$archive_path" | awk '{print $1}')
  echo "Backup created: $archive_path"
  echo "Archive size: $size"
  echo "Checksum file: $checksum_path"
fi
