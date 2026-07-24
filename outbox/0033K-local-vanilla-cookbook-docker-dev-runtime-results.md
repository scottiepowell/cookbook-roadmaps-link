# 0033K Local Vanilla Cookbook Docker Dev Runtime Results

## Summary

- Added `docker-compose.local.yml` with only the Vanilla Cookbook `app`
  service, bound to `127.0.0.1:3000` and using ignored disposable
  `.local/vanilla-cookbook/db` and `uploads` mounts.
- Added `scripts/start-vanilla-cookbook-local.ps1`,
  `scripts/check-vanilla-cookbook-local.ps1`, and
  `scripts/stop-vanilla-cookbook-local.ps1` using the separate
  `cookbook-local` Compose project.
- Documented the two-terminal workflow: local Vanilla Cookbook at
  `http://127.0.0.1:3000/`, AI product shell at
  `http://127.0.0.1:8000/product`, and AI workspace at
  `http://127.0.0.1:8000/demo`.
- The local path does not start `cloudflared` and does not require AWS,
  GitHub Actions, `CLOUDFLARE_TUNNEL_TOKEN`, production `.env`, or production
  deployment infrastructure.
- Documented `COOKBOOK_TARGET_URL`, local stop/recovery behavior, and why the
  disposable runtime is the prerequisite for future `0033J` schema discovery
  and local write/rollback tests.

## Validation

Passed the env-loader checks, 39 offline eval cases, 364 repository tests,
repository validation, Compose configuration, mock demo, PowerShell syntax
checks, focused runtime tests, and `git diff --check`. No live OpenAI call was
made.

Docker CLI was installed, but the Docker Desktop Linux engine was unavailable
in this environment, so the upstream image was not started and localhost HTTP
readiness could not be observed here. On a machine with a running Docker
daemon, run the documented start/check commands.

## Explicit non-goals

No Save-to-Cookbook implementation, production write-back, AI provider routing
or token-cap change, QMD, analytics, ads, SSO/BYOS, payment, AWS/platform,
Cloudflare/DNS, public infrastructure, production database mutation, secret,
prompt, provider output, screenshot, trace, local environment value, raw
dataset, generated index, local DB, upload, or browser artifact was committed.
