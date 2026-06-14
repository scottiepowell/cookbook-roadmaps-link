#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/cookbook}

if [[ $EUID -ne 0 ]]; then
  echo "Run this script as root, for example: sudo $0" >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "Cannot identify the operating system." >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
if [[ ${ID:-} != ubuntu ]]; then
  echo "This bootstrap supports Ubuntu; detected ${PRETTY_NAME:-unknown}." >&2
  exit 1
fi

if [[ -n ${RUNTIME_USER:-} ]]; then
  runtime_user=$RUNTIME_USER
elif [[ -n ${SUDO_USER:-} && $SUDO_USER != root ]]; then
  runtime_user=$SUDO_USER
elif id ubuntu >/dev/null 2>&1; then
  runtime_user=ubuntu
else
  echo "Set RUNTIME_USER to an existing non-root account." >&2
  exit 1
fi

if ! id "$runtime_user" >/dev/null 2>&1; then
  echo "Runtime user does not exist: $runtime_user" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git curl ca-certificates docker.io

if ! docker compose version >/dev/null 2>&1; then
  compose_installed=false
  for package in docker-compose-v2 docker-compose-plugin; do
    if apt-cache show "$package" >/dev/null 2>&1; then
      apt-get install -y "$package"
      compose_installed=true
      break
    fi
  done
  if [[ $compose_installed == false ]] && apt-cache show docker-compose >/dev/null 2>&1; then
    apt-get install -y docker-compose
  fi
fi

systemctl enable --now docker
usermod -aG docker "$runtime_user"

if ! command -v amazon-ssm-agent >/dev/null 2>&1 && \
   ! snap list amazon-ssm-agent >/dev/null 2>&1; then
  if ! command -v snap >/dev/null 2>&1; then
    apt-get install -y snapd
    systemctl enable --now snapd.socket
  fi
  snap install amazon-ssm-agent --classic
fi

ssm_service=
for candidate in \
  snap.amazon-ssm-agent.amazon-ssm-agent.service \
  amazon-ssm-agent.service; do
  if systemctl cat "$candidate" >/dev/null 2>&1; then
    ssm_service=$candidate
    break
  fi
done

if [[ -z $ssm_service ]]; then
  echo "AWS SSM Agent was installed but no systemd service was found." >&2
  exit 1
fi
systemctl enable --now "$ssm_service"

install -d -m 0755 -o "$runtime_user" -g "$runtime_user" "$APP_DIR"

echo
echo "EC2 runtime bootstrap complete"
printf '  OS: %s\n' "${PRETTY_NAME:-Ubuntu}"
printf '  Runtime user: %s\n' "$runtime_user"
printf '  App directory: %s (%s:%s)\n' \
  "$APP_DIR" "$(stat -c %U "$APP_DIR")" "$(stat -c %G "$APP_DIR")"
printf '  Git: %s\n' "$(git --version)"
printf '  Docker: %s\n' "$(docker --version)"
if docker compose version >/dev/null 2>&1; then
  printf '  Compose: %s\n' "$(docker compose version)"
elif command -v docker-compose >/dev/null 2>&1; then
  printf '  Compose: %s (legacy command; install the plugin before deployment)\n' \
    "$(docker-compose --version)"
else
  echo "  Compose: unavailable"
fi
printf '  Docker service: %s\n' "$(systemctl is-active docker)"
printf '  SSM service (%s): %s\n' "$ssm_service" \
  "$(systemctl is-active "$ssm_service")"
echo "  Note: log out and back in before $runtime_user uses Docker without sudo."
echo "  Note: .env was not created; GitHub Actions renders it during deployment."
