# 0034H Local UI Real-Save Wiring Results

## Result

Implemented the local/dev-only UI bridge to the already-proven 0034G
persistent core transport.

## Changes

- Added a disabled-by-default sidecar route:
  `/adapter/recipes/import-candidate/local-persistent-commit`.
- The route requires explicit per-request confirmation, local settings, the
  loopback target, `cookbook-local`, the exact `local/vanilla-cookbook-adapter:0034g`
  marker, and non-production/non-CI/non-tunnel context before calling the
  transport.
- The importer review panel now uses this route only when the readiness gates
  report it available. Otherwise the existing 0033S in-memory prototype is
  preserved.
- The UI labels drafts and results as local/dev-only and renders only safe
  status, UID/link, idempotency, duplicate/conflict, rollback, and
  read-after-write fields.
- The request model now carries the explicit local confirmation flag; no
  identity, session, cookie, token, OAuth, provider, or storage-grant fields
  are accepted or forwarded.

## Verification

Focused sidecar tests passed for disabled behavior, missing confirmation,
exact local image gating, safe candidate forwarding, readiness reporting, and
the existing transport tests. Full repository validation is run separately
with the commands recorded below.

Validation completed:

- `python -m pytest ai-api/tests`: 407 passed;
- `python -m pytest ai-api/tests/test_demo_ui.py ai-api/tests/test_local_save_ui.py`:
  20 passed;
- `scripts/validate-repo.sh`: repository validation passed (7 checks);
- `docker compose config --quiet`: passed;
- `docker compose -f docker-compose.local.yml -p cookbook-local config --quiet`:
  passed;
- `git diff --check`: passed.

The offline eval suite also completed with 39 cases passed during the full
validation run. No live OpenAI, Google, OAuth, storage, or other provider call
was made.

No local persistent runtime/UI verification was run in this task, so no
database, upload, browser, cookie, or session artifact was created. 0034G's
previous local verification remains the evidence for the core route's
disposable commit, replay/conflict, duplicate, rollback, and restore behavior.
The saved recipe cannot be browser-observed without a real session; the safe
UID/read-after-write envelope is the supported observation.

## Remaining blockers

Production Save-to-Cookbook still requires approved core-owned persistent user
authentication and a production transport boundary. Real Google login and
normal authenticated sidecar UI wiring remain future work. This task does not
change those boundaries.

## Explicit non-goals

No production auth or save, real provider call, Google/OAuth flow, cookie/token/
session creation or export, direct sidecar DB write, browser automation,
migration, public production route, AWS, Cloudflare, GitHub Actions, analytics,
ads, payment, QMD, or external source was added.
