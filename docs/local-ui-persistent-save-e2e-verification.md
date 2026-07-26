# Local UI Persistent Save E2E Verification

Status: verified local/dev-only API-level E2E; production Save-to-Cookbook
remains unimplemented.

Date: 2026-07-26

## Verification path

Run the explicit local verifier from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-local-ui-persistent-save-e2e.ps1 `
  -ApproveLocalWrite -SidecarPort 8001
```

The verifier uses only:

- `cookbook-local`;
- `local/vanilla-cookbook-adapter:0034g`;
- `http://127.0.0.1:3000/` for the core target;
- a mock importer and an isolated disposable sidecar fixture database; and
- non-secret local fixture gates.

It refuses missing approval, production/CI/deployment/tunnel indicators, and
non-loopback targets. It starts the local Cookbook app, waits for HTTP
readiness, starts an isolated mock Uvicorn sidecar, checks `/demo/readiness`,
obtains a mock importer draft, calls the dry-run route, then sends
`confirm_local_save=true` to the persistent sidecar route. The sidecar sends
only the reviewed candidate and approval to the existing 0034G core transport.

## Evidence

The successful run returned safe status evidence including:

- persistent local-save readiness enabled;
- reviewed mock draft accepted by dry-run;
- core status `verified`;
- opaque local recipe UID;
- core `read_after_write=verified`; and
- idempotency replay status.

The core route owns synthetic identity, commit authorization, persistence,
duplicate/replay/conflict handling, and disposable DB/uploads backup/restore.
The verifier stops the sidecar and Cookbook container and removes its
temporary sidecar log and demo-data directory in `finally` cleanup.

This is API-level rather than browser-level E2E. The saved recipe is not
opened in the Vanilla Cookbook browser because that would require a real
authenticated session, cookie, token, or browser state. Safe UID/status and
read-after-write evidence are the supported observation.

## Explicit non-goals

No production route/auth/save, Google/OAuth flow, provider call, storage scope,
cookie/session/token handling, direct sidecar DB write, browser credential
automation, migration, deployment integration, or external source was added.
