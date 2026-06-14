#!/usr/bin/env bash
set -euo pipefail

domain=${1:-cookbook.roadmap.links}

if [[ ! $domain =~ ^[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,63}$ ]]; then
  echo "Invalid domain name: $domain" >&2
  exit 2
fi

echo "Cloudflare route check for $domain"
echo "DNS resolution:"
if command -v getent >/dev/null 2>&1; then
  if ! getent ahosts "$domain" | awk '!seen[$1]++ {print "  " $1}'; then
    echo "  No address returned by getent"
  fi
elif command -v dig >/dev/null 2>&1; then
  if ! dig +short A "$domain" | sed 's/^/  A /'; then
    echo "  A lookup failed"
  fi
  if ! dig +short AAAA "$domain" | sed 's/^/  AAAA /'; then
    echo "  AAAA lookup failed"
  fi
elif command -v nslookup >/dev/null 2>&1; then
  nslookup "$domain" || echo "  nslookup did not resolve the domain"
else
  echo "  No getent, dig, or nslookup command is available"
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for the HTTPS check." >&2
  exit 1
fi

url="https://$domain/"
format=$'HTTP status: %{http_code}\nFinal URL: %{url_effective}\nDNS time: %{time_namelookup}s\nConnect time: %{time_connect}s\nTLS time: %{time_appconnect}s\nTotal time: %{time_total}s\n'

echo "HTTPS reachability:"
if ! result=$(curl \
  --fail \
  --location \
  --max-time 20 \
  --output /dev/null \
  --show-error \
  --silent \
  --write-out "$format" \
  "$url"); then
  echo "HTTPS check failed for $url" >&2
  exit 1
fi

printf '%s\n' "$result"
echo "Cloudflare route check passed."
