#!/usr/bin/env bash
set -uo pipefail

APP_DIR=${APP_DIR:-/opt/cookbook}
pass_count=0
warn_count=0
fail_count=0

pass() {
  pass_count=$((pass_count + 1))
  printf 'PASS: %s\n' "$*"
}

warn() {
  warn_count=$((warn_count + 1))
  printf 'WARN: %s\n' "$*"
}

fail() {
  fail_count=$((fail_count + 1))
  printf 'FAIL: %s\n' "$*"
}

if [[ -n ${RUNTIME_USER:-} ]]; then
  runtime_user=$RUNTIME_USER
elif id ubuntu >/dev/null 2>&1; then
  runtime_user=ubuntu
else
  runtime_user=$(id -un)
fi

echo "EC2 runtime preflight"
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  echo "OS: ${PRETTY_NAME:-unknown}"
  if [[ ${ID:-} == ubuntu ]]; then
    pass "Ubuntu operating system detected"
  else
    warn "Bootstrap is designed for Ubuntu; detected ${ID:-unknown}"
  fi
else
  echo "OS: unknown"
  warn "Cannot read /etc/os-release"
fi
echo "Current user: $(id -un) (uid $(id -u))"
echo "Runtime user: $runtime_user"

if id "$runtime_user" >/dev/null 2>&1; then
  pass "Runtime user exists"
else
  fail "Runtime user does not exist: $runtime_user"
fi

if command -v git >/dev/null 2>&1; then
  pass "$(git --version)"
else
  fail "Git is unavailable"
fi

if command -v docker >/dev/null 2>&1; then
  pass "$(docker --version)"
else
  fail "Docker is unavailable"
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  pass "$(docker compose version)"
elif command -v docker-compose >/dev/null 2>&1; then
  warn "Only the legacy docker-compose command is available"
else
  fail "Docker Compose plugin is unavailable"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet docker; then
  pass "Docker service is active"
else
  fail "Docker service is not active"
fi

ssm_service=
if command -v systemctl >/dev/null 2>&1; then
  for candidate in \
    snap.amazon-ssm-agent.amazon-ssm-agent.service \
    amazon-ssm-agent.service; do
    if systemctl cat "$candidate" >/dev/null 2>&1; then
      ssm_service=$candidate
      break
    fi
  done
fi
if [[ -n $ssm_service ]] && systemctl is-active --quiet "$ssm_service"; then
  pass "SSM Agent service is active ($ssm_service)"
elif [[ -n $ssm_service ]]; then
  fail "SSM Agent service is not active ($ssm_service)"
else
  fail "SSM Agent systemd service was not found"
fi

if [[ -d $APP_DIR ]]; then
  pass "Application directory exists: $APP_DIR"
  if id "$runtime_user" >/dev/null 2>&1; then
    if [[ $EUID -eq 0 ]]; then
      if runuser -u "$runtime_user" -- test -w "$APP_DIR"; then
        pass "$APP_DIR is writable by $runtime_user"
      else
        fail "$APP_DIR is not writable by $runtime_user"
      fi
    elif [[ $(id -un) == "$runtime_user" ]] && [[ -w $APP_DIR ]]; then
      pass "$APP_DIR is writable by $runtime_user"
    else
      warn "Run as root to verify writability for $runtime_user"
    fi
  fi
else
  fail "Application directory does not exist: $APP_DIR"
fi

if command -v curl >/dev/null 2>&1 && \
   curl --fail --silent --show-error --head --max-time 10 \
     https://github.com/ >/dev/null 2>&1; then
  pass "Outbound HTTPS connectivity to GitHub is available"
elif command -v curl >/dev/null 2>&1 && \
     curl --fail --silent --show-error --head --max-time 10 \
       https://www.cloudflare.com/ >/dev/null 2>&1; then
  pass "Outbound HTTPS connectivity to Cloudflare is available"
else
  warn "Outbound HTTPS connectivity test did not succeed"
fi

if command -v ss >/dev/null 2>&1; then
  if ss -ltnH 'sport = :3000' 2>/dev/null | grep -q .; then
    pass "TCP port 3000 is listening"
  else
    warn "TCP port 3000 is not listening; this is expected before deployment"
  fi
else
  warn "The ss command is unavailable; port 3000 was not checked"
fi

echo
printf 'Preflight summary: %d pass, %d warn, %d fail\n' \
  "$pass_count" "$warn_count" "$fail_count"

if ((fail_count > 0)); then
  exit 1
fi
exit 0
