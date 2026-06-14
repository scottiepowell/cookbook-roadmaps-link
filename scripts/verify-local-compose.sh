#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/cookbook}

if [[ ! -d $APP_DIR ]]; then
  echo "Application directory does not exist: $APP_DIR" >&2
  exit 1
fi
cd "$APP_DIR"

if [[ ! -f docker-compose.yml ]]; then
  echo "Missing $APP_DIR/docker-compose.yml" >&2
  exit 1
fi
if [[ ! -f .env ]]; then
  echo "Missing $APP_DIR/.env; its contents will not be printed." >&2
  exit 1
fi
echo "Found docker-compose.yml and .env (contents not displayed)."

if ! command -v docker >/dev/null 2>&1 || \
   ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is unavailable." >&2
  exit 1
fi

echo "Compose service status:"
# Limit output fields because the cloudflared command contains the tunnel token.
docker compose ps --all --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'

all_services=$(docker compose ps --all --services)
running_services=$(docker compose ps --status running --services)

if grep -qx cloudflared <<<"$all_services"; then
  if grep -qx cloudflared <<<"$running_services"; then
    echo "Cloudflare service is present and running."
  else
    echo "WARN: Cloudflare service is present but not running." >&2
  fi
else
  echo "WARN: Cloudflare service is not present in the Compose project." >&2
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for the local app check." >&2
  exit 1
fi

local_url=http://127.0.0.1:3000/
format=$'HTTP status: %{http_code}\nFinal URL: %{url_effective}\nTotal time: %{time_total}s\n'
echo "Local app reachability:"
if ! result=$(curl \
  --fail \
  --location \
  --max-time 10 \
  --output /dev/null \
  --show-error \
  --silent \
  --write-out "$format" \
  "$local_url"); then
  echo "Local app check failed for $local_url" >&2
  exit 1
fi

printf '%s\n' "$result"
echo "Local Compose verification passed."
