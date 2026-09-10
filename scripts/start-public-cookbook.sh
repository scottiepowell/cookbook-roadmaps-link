#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
CORE_DIR=${COOKBOOK_CORE_DIR:-"$HOME/projects/vanilla-cookbook-core"}
COMPOSE_FILE="$REPO_ROOT/docker-compose.public.yml"
DOCKER_DESKTOP_EXE=${DOCKER_DESKTOP_EXE:-'/c/Program Files/Docker/Docker/Docker Desktop.exe'}
TUNNEL_CONTAINER=${COOKBOOK_TUNNEL_CONTAINER:-cookbook-public-cloudflared}
STARTUP_TIMEOUT_SECONDS=${COOKBOOK_STARTUP_TIMEOUT_SECONDS:-180}

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

native_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -aw "$1"
  else
    printf '%s\n' "$1"
  fi
}

wait_for_docker() {
  local elapsed=0
  local desktop_running=''
  until docker info >/dev/null 2>&1; do
    if (( elapsed >= STARTUP_TIMEOUT_SECONDS )); then
      fail "Timed out waiting for Docker Desktop Linux engine after ${STARTUP_TIMEOUT_SECONDS}s."
    fi
    if (( elapsed >= 10 )); then
      desktop_running=$(MSYS2_ARG_CONV_EXCL='*' powershell.exe -NoProfile -NonInteractive -Command \
        "if (Get-Process -Name 'Docker Desktop','com.docker.backend' -ErrorAction SilentlyContinue) { 'yes' }" \
        2>/dev/null | tr -d '\r')
      if [[ "$desktop_running" != yes ]]; then
        fail 'Docker Desktop exited before its engine became ready. If startup reports an inaccessible dockerInference socket, restart Windows (or restart WslService as Administrator) and run this launcher again.'
      fi
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
}

wait_for_sidecar_health() {
  local elapsed=0
  local status=''
  while (( elapsed < STARTUP_TIMEOUT_SECONDS )); do
    status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{end}}' \
      cookbook-public-ai 2>/dev/null || true)
    [[ "$status" == healthy ]] && return 0
    [[ "$status" == unhealthy ]] && fail 'AI sidecar became unhealthy during startup.'
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "Timed out waiting for AI sidecar health after ${STARTUP_TIMEOUT_SECONDS}s."
}

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) fail 'This launcher is intended for Windows Git Bash.' ;;
esac

command -v docker >/dev/null 2>&1 || fail 'Docker CLI is unavailable in Git Bash.'
[[ -f "$COMPOSE_FILE" ]] || fail "Missing public Compose file: $COMPOSE_FILE"
[[ -f "$CORE_DIR/.env" ]] || fail 'Missing ignored core .env file.'
[[ -f "$CORE_DIR/.env.public" ]] || fail 'Missing ignored core .env.public file.'
[[ -f "$REPO_ROOT/.env" ]] || fail 'Missing ignored sidecar .env file.'
[[ -f "$REPO_ROOT/.env.public-ai" ]] || fail 'Missing ignored sidecar .env.public-ai file.'

if ! docker info >/dev/null 2>&1; then
  [[ -f "$DOCKER_DESKTOP_EXE" ]] || fail "Docker Desktop executable was not found: $DOCKER_DESKTOP_EXE"
  printf 'Starting Docker Desktop...\n'
  docker_desktop_native=$(native_path "$DOCKER_DESKTOP_EXE")
  MSYS2_ARG_CONV_EXCL='*' powershell.exe -NoProfile -NonInteractive -Command \
    "Start-Process -FilePath '$docker_desktop_native'" >/dev/null
  wait_for_docker
fi

docker compose version >/dev/null 2>&1 || fail 'Docker Compose plugin is unavailable.'
printf 'Docker Desktop is ready.\n'

docker network inspect cookbook-public-tunnel >/dev/null 2>&1 || \
  docker network create cookbook-public-tunnel >/dev/null
docker volume inspect cookbook-public-core-db >/dev/null 2>&1 || \
  docker volume create cookbook-public-core-db >/dev/null
docker volume inspect cookbook-public-core-uploads >/dev/null 2>&1 || \
  docker volume create cookbook-public-core-uploads >/dev/null

export PUBLIC_CORE_ENV_FILE
PUBLIC_CORE_ENV_FILE=$(native_path "$CORE_DIR/.env")
export PUBLIC_CORE_OIDC_ENV_FILE
PUBLIC_CORE_OIDC_ENV_FILE=$(native_path "$CORE_DIR/.env.public")

cd "$REPO_ROOT"
docker compose -f "$COMPOSE_FILE" config --quiet
docker compose -f "$COMPOSE_FILE" up -d

if docker container inspect "$TUNNEL_CONTAINER" >/dev/null 2>&1; then
  tunnel_running=$(docker inspect --format '{{.State.Running}}' "$TUNNEL_CONTAINER")
  if [[ "$tunnel_running" != true ]]; then
    docker start "$TUNNEL_CONTAINER" >/dev/null
  fi
  printf 'Cloudflare connector: running.\n'
else
  printf 'WARNING: Existing Cloudflare connector container was not found: %s\n' "$TUNNEL_CONTAINER" >&2
fi

wait_for_sidecar_health

sidecar_health=$(docker inspect --format '{{.State.Health.Status}}' cookbook-public-ai)
core_status=$(docker inspect --format '{{.State.Status}}' cookbook-public-core)
core_image=$(docker inspect --format '{{.Config.Image}}' cookbook-public-core)
sidecar_image=$(docker inspect --format '{{.Config.Image}}' cookbook-public-ai)

printf 'Core: %s (%s)\n' "$core_image" "$core_status"
printf 'AI sidecar: %s (%s)\n' "$sidecar_image" "$sidecar_health"

if command -v curl >/dev/null 2>&1; then
  local_status=$(docker exec cookbook-public-core node -e \
    "fetch('http://127.0.0.1:3000/api/health').then(r=>process.stdout.write(String(r.status))).catch(()=>process.exit(1))")
  printf 'Local core health: HTTP %s\n' "$local_status"
  public_status=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    --max-time 15 https://cookbook.roadmaps.link/api/health || true)
  printf 'Public health: HTTP %s\n' "${public_status:-unavailable}"
fi

printf 'Public Cookbook services are running.\n'
