#!/usr/bin/env bash
set -euo pipefail

cd /opt/cookbook
git pull --ff-only
mkdir -p db uploads
docker compose pull
docker compose up -d --remove-orphans
docker compose ps
