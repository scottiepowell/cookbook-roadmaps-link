# 0034I Local UI Persistent Save E2E Verification Results

## Result

Completed a local API-level E2E verification of the 0034H UI/API wiring. A
browser-level assertion was intentionally not attempted because no real
Vanilla Cookbook session may be created or exported.

## Exact local path

Command run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-local-ui-persistent-save-e2e.ps1 `
  -ApproveLocalWrite -SidecarPort 8001
```

The verifier used `cookbook-local`, loopback `http://127.0.0.1:3000/`, and
`local/vanilla-cookbook-adapter:0034g`. It enabled only non-secret local
fixture flags and ran the sidecar with mock AI data. It did not call OpenAI,
Google, OAuth, Microsoft, storage, or any other provider.

## Evidence

- Docker runtime started and passed local HTTP readiness.
- Sidecar readiness reported persistent local save enabled.
- Mock importer returned a reviewed draft without an external provider call.
- Sidecar dry-run returned a valid candidate.
- UI/API-equivalent confirmation sent `confirm_local_save=true`.
- Persistent core route returned `status=verified`.
- Safe opaque recipe UID was returned.
- `read_after_write=verified` was returned.
- Idempotency replay status was returned safely.
- Core 0034G disposable backup/restore boundary reported completion; no DB
  rows, recipe bodies, SQL, or uploads were printed.
- Sidecar temporary demo data/logs and the local Cookbook container/network
  were cleaned up by the verifier.

The saved recipe was not browser-observed. The core synthetic user has no real
browser session, and creating/exporting one would violate the task boundary.

## Guards and identity boundary

The verifier requires `-ApproveLocalWrite`, rejects CI/deployment/tunnel/AWS
contexts, fixes the loopback target and `cookbook-local` project, requires the
exact 0034g image, and enables the local persistent fixture explicitly. The
sidecar sends no `userId`, cookie, session, token, OAuth code, provider grant,
or storage grant. Core creates/owns the synthetic AuthUser and authorization.

## Validation

Focused static/script tests passed, including no-approval refusal and leakage
guards. The local E2E command above passed. The final repository validation
also passed:

- `python -m pytest ai-api/tests`: 410 passed;
- `scripts/validate-repo.sh`: passed;
- `docker compose config --quiet`: passed;
- local Compose config: passed; and
- `git diff --check`: passed.

## Remaining blockers

Production Save-to-Cookbook still requires approved persistent real-user core
authentication and production transport. Real Google login and browser
observation remain unimplemented. No production or normal authenticated user
save is implied by this disposable synthetic verification.

## Explicit non-goals

No production Save-to-Cookbook/auth, Google/OAuth/provider call, cookie/token/
session creation or export, direct sidecar DB write, browser automation,
migration, AWS, GitHub Actions, Cloudflare, tunnel, analytics, ads, payment,
QMD, or external source was added.
