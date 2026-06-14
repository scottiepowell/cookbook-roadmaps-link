#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/cookbook}
BACKUP_DIR=${BACKUP_DIR:-/opt/cookbook-backups}
force=false

usage() {
  echo "Usage: $0 [--force] BACKUP_ARCHIVE"
}

if [[ ${1:-} == --force ]]; then
  force=true
  shift
fi
if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

archive=$1
if [[ ! -f $archive ]]; then
  echo "Backup archive does not exist: $archive" >&2
  exit 1
fi
archive=$(realpath "$archive")
checksum_file="$archive.sha256"

if [[ -f $checksum_file ]]; then
  expected_checksum=$(awk 'NR == 1 {print $1}' "$checksum_file")
  if [[ ! $expected_checksum =~ ^[0-9a-fA-F]{64}$ ]]; then
    echo "Checksum file has an invalid format: $checksum_file" >&2
    exit 1
  fi
  actual_checksum=$(sha256sum "$archive" | awk '{print $1}')
  if [[ $actual_checksum != "$expected_checksum" ]]; then
    echo "Backup checksum verification failed." >&2
    exit 1
  fi
  echo "Backup checksum verified."
else
  echo "WARN: No matching checksum file found: $checksum_file" >&2
fi

if [[ ! -d $APP_DIR ]]; then
  echo "Application directory does not exist: $APP_DIR" >&2
  exit 1
fi

if [[ $force == false ]]; then
  if [[ ! -f $APP_DIR/docker-compose.yml ]]; then
    echo "Cannot verify service state without $APP_DIR/docker-compose.yml" >&2
    echo "Stop services and use --force only after verifying they are stopped." >&2
    exit 1
  fi
  if ! command -v docker >/dev/null 2>&1 || \
     ! docker compose version >/dev/null 2>&1; then
    echo "Cannot verify Compose service state." >&2
    echo "Stop services and use --force only after verifying they are stopped." >&2
    exit 1
  fi
  running_services=$(cd "$APP_DIR" && docker compose ps --status running --services)
  if [[ -n $running_services ]]; then
    echo "Refusing to restore while Compose services are running:" >&2
    while IFS= read -r service; do
      printf '  %s\n' "$service" >&2
    done <<<"$running_services"
    echo "Stop the services first, or use --force only when the risk is understood." >&2
    exit 1
  fi
else
  echo "WARN: --force bypasses the Docker Compose running-service check." >&2
fi

while IFS= read -r member; do
  normalized=${member#./}
  case $normalized in
    db|db/*|uploads|uploads/*) ;;
    *) echo "Archive contains an unexpected path: $member" >&2; exit 1 ;;
  esac
  if [[ /$normalized/ == *'/../'* || $normalized == /* ]]; then
    echo "Archive contains an unsafe path: $member" >&2
    exit 1
  fi
done < <(tar -tzf "$archive")

if tar -tvzf "$archive" | \
   awk 'substr($1, 1, 1) !~ /^[-d]$/ {found=1} END {exit !found}'; then
  echo "Archive contains links or special files; restore refused." >&2
  exit 1
fi

work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
tar -C "$work_dir" -xzf "$archive" --no-same-owner --no-same-permissions

for runtime_dir in db uploads; do
  if [[ ! -d $work_dir/$runtime_dir ]]; then
    echo "Archive is missing required directory: $runtime_dir" >&2
    exit 1
  fi
done

mkdir -p "$BACKUP_DIR"
current=()
[[ -d $APP_DIR/db ]] && current+=(db)
[[ -d $APP_DIR/uploads ]] && current+=(uploads)
if ((${#current[@]} > 0)); then
  safety_timestamp=$(date -u +%Y%m%dT%H%M%SZ)
  safety_name="cookbook-data-pre-restore-$safety_timestamp.tar.gz"
  safety_path="$BACKUP_DIR/$safety_name"
  tar -C "$APP_DIR" -czf "$safety_path" "${current[@]}"
  (cd "$BACKUP_DIR" && sha256sum "$safety_name" > "$safety_name.sha256")
  echo "Safety backup created: $safety_path"
fi

rm -rf "$APP_DIR/db" "$APP_DIR/uploads"
mv "$work_dir/db" "$APP_DIR/db"
mv "$work_dir/uploads" "$APP_DIR/uploads"

echo "Restore completed from: $archive"
echo "Restored: $APP_DIR/db"
echo "Restored: $APP_DIR/uploads"
echo "The .env file was not read, changed, or printed."
