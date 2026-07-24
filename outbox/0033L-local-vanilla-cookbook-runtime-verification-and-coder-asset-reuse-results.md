# 0033L Local Vanilla Cookbook Runtime Verification and Coder Asset Reuse Results

## Verification

- Docker Desktop daemon was available; `docker info` reported a running Linux
  engine.
- The repository start script successfully started the `cookbook-local`
  Compose project and pulled/started `jt196/vanilla-cookbook:stable`.
- `docker compose -f docker-compose.local.yml -p cookbook-local ps` showed only
  the `app` service, with `127.0.0.1:3000->3000/tcp`; no `cloudflared` container
  was started.
- The first HTTP probe found the container still warming up. A repeat check
  then confirmed `http://127.0.0.1:3000/` responded with HTTP 200.
- Disposable runtime directories remained under ignored
  `.local/vanilla-cookbook/db` and `.local/vanilla-cookbook/uploads`. The local
  Cookbook container was stopped with the repository stop script after
  verification.

## AI handoff verification

- A mock AI sidecar was started locally for the handoff check and then stopped.
- `http://127.0.0.1:8000/product` returned HTTP 200 with local recovery
  guidance.
- `/product/cookbook` redirected to `http://127.0.0.1:3000/` with
  `COOKBOOK_TARGET_URL` unset.
- `/product/ai` redirected to `/demo`.
- No live OpenAI call was made.

## Coder asset inspection

Read-only inspection of likely local paths found `C:\Users\scott\coder-docker-template`,
which contains a generic Coder Docker workspace template, and unrelated VS
Code server caches. No Vanilla Cookbook-specific image, Dockerfile, Compose
file, or non-secret application pattern was found. The generic template was
not copied because its Docker-socket/Terraform workspace behavior belongs to
Coder infrastructure, not this localhost-only app runtime. No `.env`, token,
database, upload, browser artifact, or other local runtime data was read or
committed.

## Code/docs changed

- Added Docker daemon preflight messages to the local start/check/stop scripts.
- Updated local integration, acceptance, live-runbook, status, backlog, roadmap,
  and README guidance with Docker Desktop readiness, production separation,
  stop/recovery behavior, and the 0033J disposable-runtime prerequisite.
- Added the verification outbox and retained the existing ignored local data
  boundary.

## Validation

Passed: local start/check/stop verification, local Compose configuration,
PowerShell syntax checks, focused runtime/handoff tests, env-loader checks, 39
offline eval cases, 364 repository tests, repository validation, mock demo, and
`git diff --check`.

## Explicit non-goals

No Save-to-Cookbook implementation, database write-back beyond disposable
upstream startup initialization, AI provider routing or token-cap change, QMD,
analytics, ads, SSO/BYOS, payment, AWS/platform, Cloudflare/DNS, public
infrastructure, production secrets, prompts, provider outputs, screenshots,
traces, raw datasets, generated indexes, local DBs, uploads, or browser
artifacts were committed.
