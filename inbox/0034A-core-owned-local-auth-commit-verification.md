# 0034A Core-Owned Local Auth Commit Verification

## Goal

Prove the `0033Z` core-owned commit adapter against a real disposable local Vanilla Cookbook runtime using a safe core-owned synthetic auth/ownership fixture and backup/restore verification, without exporting cookies, tokens, sessions, or real user credentials.

This is a local-only verification task. It may modify the separate source-owned Vanilla Cookbook workspace and build a new local image, but it must not vendor external source into this sidecar repository. It must not implement production Save-to-Cookbook, public production routes, sidecar UI real-save wiring, auth bypass, browser/session automation, direct sidecar database writes, AWS/GitHub Actions/Cloudflare deployment, QMD, analytics, ads, payment, provider routing changes, or live calls.

## Context

`0033Z` implemented the first core-owned authenticated commit adapter in the separate Vanilla Cookbook source workspace:

```text
External branch: openclaw/0033Z-core-owned-local-commit-adapter
External commit: c8ee3ed8234135d5b889b84b2b14bd69397e4de3
Route: POST /api/adapter/recipes/import-candidate/commit
Image: local/vanilla-cookbook-adapter:0033z
```

The route is disabled by default, requires explicit local enablement, loopback HTTP target, normal core authentication, and `confirm_save: true`. It derives ownership from core auth context, uses the existing `Recipe.hash` field for opaque versioned idempotency, maps first-scope recipe fields, excludes categories/media/uploads/embeddings, and has focused external tests.

`0033Z` did **not** attempt a real authenticated runtime commit because obtaining or exporting session credentials would violate the task boundary. Its remaining work states that future sidecar UI wiring should wait until a safe local auth/ownership fixture and disposable backup/restore verification are approved.

## Required Work

### 1. Read current state

Read in this sidecar repository:

```text
outbox/0033Z-core-owned-local-commit-adapter-results.md
docs/core-owned-local-commit-adapter.md
outbox/0033Y-core-owned-local-dry-run-route-results.md
docs/core-owned-local-dry-run-route.md
outbox/0033Q-local-save-to-cookbook-readiness-evidence-harness-results.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/local-vanilla-cookbook-schema-discovery.md
docs/ai-importer-save-to-cookbook-adapter-design.md
docs/source-owned-vanilla-cookbook-workspace-bootstrap.md
docker-compose.local.yml
scripts/start-vanilla-cookbook-local.ps1
scripts/check-vanilla-cookbook-local.ps1
scripts/stop-vanilla-cookbook-local.ps1
README.md
```

Then inspect the separate Vanilla Cookbook source workspace created by `0033W`. Keep all source changes outside this sidecar repository.

### 2. Create an external workspace branch

In the external Vanilla Cookbook source workspace, create a focused branch:

```text
openclaw/0034A-core-owned-local-auth-commit-verification
```

Do not copy external source into this sidecar repository.

### 3. Implement safe local auth/ownership verification

Implement the smallest safe verification boundary needed to prove the commit adapter against a real disposable local database.

Preferred approach:

```text
core-app integration test or dev-only local harness that injects a synthetic current-user context server-side and calls the core commit service without exporting browser cookies, auth tokens, session values, or real credentials
```

Acceptable approaches:

- a server-side integration test that creates a synthetic user fixture in a disposable test DB and calls the commit service directly;
- a local-only harness inside the external core workspace that creates a synthetic user and invokes the commit adapter through core-owned service boundaries;
- a route-handler test that constructs authenticated `locals.user` test context without creating/exporting a browser session or cookie.

Avoid if possible:

- real browser login;
- exported cookies;
- exported session tokens;
- browser/session automation;
- sidecar-to-core credential forwarding;
- direct sidecar DB writes.

If route-level verification cannot be done safely without credentials/session export, verify the service-level core-owned commit path and document the remaining route/session limitation precisely.

### 4. Preserve strict local-only guards

The verification must:

- run only against the local source-owned/custom image or external workspace test DB;
- use synthetic local user data only;
- use a disposable DB/uploads location;
- create backup/restore before any runtime write, if using the `cookbook-local` runtime;
- restore/clean up DB/uploads after success and failure;
- refuse production/exposed/non-loopback targets;
- use no AWS, GitHub Actions, Cloudflare, tunnel, or production deployment;
- not call live OpenAI or any provider;
- not print or commit cookies, tokens, sessions, secrets, absolute local paths, raw row dumps, recipe private contents, prompts, provider bodies, stack traces, or SQL dumps.

### 5. Verify real commit behavior locally

The verification should prove or precisely block:

```text
synthetic ownership setup and teardown
confirm_save requirement
valid candidate creates exactly one recipe in disposable local persistence
canonical UID/relative URL is returned safely
read-after-write works through safe core-owned lookup/status
same-key same-payload replay returns the original result without second write
same-key changed-payload returns safe conflict without write
duplicate fingerprint returns review-required status without unbounded duplicates
injected failure rolls back
backup/restore returns disposable state to pre-test status
categories/media/uploads/remote images/embeddings remain excluded
```

If any evidence cannot be proven safely, stop and document the precise blocker. Do not weaken guardrails.

### 6. Build a new custom local image if gates pass

If the external verification passes, build a new local-only image:

```text
local/vanilla-cookbook-adapter:0034a
```

Do not push or deploy it. Do not retag `jt196/vanilla-cookbook:stable`.

Optionally verify startup from this sidecar repo:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034a

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

### 7. Update sidecar documentation only

In this sidecar repository, do not copy external source or generated artifacts.

Create:

```text
docs/core-owned-local-auth-commit-verification.md
outbox/0034A-core-owned-local-auth-commit-verification-results.md
```

Update as appropriate:

```text
README.md
docs/core-owned-local-commit-adapter.md
docs/core-owned-local-dry-run-route.md
docs/local-cookbook-ai-product-integration.md
docs/local-product-acceptance-checklist.md
docs/save-to-cookbook-schema-informed-write-plan.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

The docs must clearly state:

- whether a safe synthetic auth/ownership fixture now exists;
- whether a real disposable local commit was verified;
- whether route-level verification remains blocked or is proven;
- whether sidecar UI real-save wiring is now ready, partially ready, or still blocked;
- production Save-to-Cookbook remains not implemented;
- direct sidecar DB writes and browser/session automation remain rejected.

## Acceptance Criteria

- A safe local auth/ownership verification path exists in the external core workspace, or the precise blocker is documented.
- No cookies, auth tokens, session values, or real user credentials are exported, printed, or committed.
- Verification uses synthetic user/recipe data only.
- If runtime DB writes are performed, backup/restore and cleanup are proven.
- Commit behavior proves valid save, read-after-write, idempotency replay/conflict, duplicate handling, and rollback, or precisely documents remaining blockers.
- A new local image `local/vanilla-cookbook-adapter:0034a` is built or the build blocker is documented.
- Sidecar docs/outbox record the external branch/commit, test/build results, local image result, and remaining sidecar UI wiring readiness.
- No external source is committed into this sidecar repository.
- No production save, public production route, migration, auth bypass, browser/session automation, direct sidecar DB write, AWS/GitHub Actions/Cloudflare work, provider routing, QMD, analytics, ads, payment, SSO/BYOS, or live call is added.
- No secrets, prompts, provider outputs, screenshots, traces, raw datasets, generated indexes, local env values, DB files, uploads, row dumps, browser artifacts, source archives, container snapshots, cookies, auth tokens, or session values are committed.

## Validation

In the external Vanilla Cookbook workspace, run the focused tests/builds needed for the new verification and record exact commands/results in the sidecar outbox.

In this sidecar repository, run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link

git diff --check

& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh

docker compose config --quiet

docker compose -f docker-compose.local.yml -p cookbook-local config --quiet
```

If sidecar code/config changes beyond docs are made, also run:

```powershell
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
```

Optional custom-image startup verification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-vanilla-cookbook-local.ps1 -CookbookImage local/vanilla-cookbook-adapter:0034a

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-vanilla-cookbook-local.ps1

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\stop-vanilla-cookbook-local.ps1
```

Do not run live OpenAI.

## Commit

Commit external workspace changes if appropriate and record that external commit SHA in the sidecar outbox.

Then commit sidecar docs/outbox:

```bash
git add docs README.md outbox/0034A-core-owned-local-auth-commit-verification-results.md

git commit -m "docs: record core owned local auth commit verification"

git pull --rebase origin main

git push origin main
```
