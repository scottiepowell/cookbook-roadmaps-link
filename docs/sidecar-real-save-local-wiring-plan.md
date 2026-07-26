# Sidecar Real-Save Local Wiring Plan

Status: local transport implemented; normal UI real-save wiring remains a
planning/gate item.

Date: 2026-07-25

## Completed evidence

The current boundary is deliberately split:

- 0033S: sidecar `/demo` review panel and in-memory local commit simulation;
- 0033Q: disposable local DB/write readiness harness;
- 0033Y/0033Z: core-owned dry-run and explicitly gated commit routes in the
  separate source-owned Vanilla Cookbook workspace;
- 0034A: real core service commit against a temporary SQLite database using a
  synthetic `AuthUser`, read-after-write, replay/conflict, duplicate blocking,
  rollback, and pre-write backup/post-test restore.

The approved external custom image is
`local/vanilla-cookbook-adapter:0034c` for the dev fixture; `0034a` remains the
service-level verification image.
The sidecar local runtime remains app-only, `cookbook-local`, and bound to
`http://127.0.0.1:3000/`. The sidecar product remains at
`http://127.0.0.1:8000/product` and `/demo`.

## Remaining bridge and why credentials stay out

The sidecar UI currently has no safe way to become the authenticated core user
expected by `requireAuth(locals)`. 0034A intentionally called the core service
with an in-process synthetic user object; it did not create a Lucia session or
exercise a browser request. The core route is therefore not yet a safe target
for a sidecar HTTP client.

Cookies, session IDs, auth tokens, and real credentials must not be copied from
a browser, printed, placed in environment values, or forwarded through the
sidecar. Doing so would make the sidecar an auth owner and would create a
credential-handling boundary that the current architecture has not reviewed.
Direct sidecar DB writes remain prohibited because they bypass core ownership,
validation, transaction, and canonical URL behavior.

## Options evaluated

### Option A: retain the in-memory sidecar prototype

This is the current safe state. It preserves mock/offline testing and the
review/dry-run UX, but it cannot make a recipe appear in the normal Cookbook
app. It remains acceptable as a prototype and fallback while the core bridge
is gated.

### Option B: core-owned local dev fixture route/service

Recommended next step. Add a dev-only fixture inside the source-owned core
workspace that constructs `locals.user` or an equivalent core service context
from a synthetic local owner, calls dry-run first, requires explicit commit
confirmation, and uses the existing core transaction/adapter. It must be
disabled by default, loopback-only, opt-in, and unavailable when exposed or
production indicators are present. The fixture must keep auth context inside
the core process; it must not issue a browser cookie or token.

### Option C: sidecar-to-core local adapter client

Defer until Option B or an equivalent reviewed auth fixture exists. The client
could call the core dry-run route, then the commit route, but only if a safe
local transport can establish the core current user without sidecar-owned
credentials. The client must target only the opt-in `0034a` image at loopback,
receive safe UID/status envelopes, and never forward prompts, provider bodies,
secrets, raw sessions, or private storage.

### Option D: export or capture browser sessions

Rejected. It violates the credential boundary, is fragile across browsers and
deployments, creates replay and leakage risk, and would turn a local test into
an undocumented auth integration. Browser/session automation is not a bridge.

### Option E: direct sidecar database writes

Rejected. It bypasses core authentication, ownership, validation, transaction
and rollback behavior, and canonical recipe lifecycle. It also risks schema
drift and violates the canonical-owner decision.

## Recommended bridge sequence

The next implementation should remain in the external core workspace:

1. Start `cookbook-local` with the opt-in
   `local/vanilla-cookbook-adapter:0034a` image and assert loopback-only scope.
2. Create a synthetic core owner in a disposable fixture or test DB without
   importing local users or creating a browser session.
3. Submit a reviewed candidate to the core dry-run service first.
4. Require an explicit local operator approval and `confirm_save: true`.
5. Commit through the core adapter transaction, returning only safe UID,
   relative URL, status, duplicate, and idempotency metadata.
6. Verify read-after-write through a core-owned safe lookup, then restore the
   DB/upload backup or remove the synthetic fixture data.

Only after this core fixture is proven should a sidecar client be designed. The
sidecar UI should call a narrow adapter client, never own `userId`, and never
call Prisma. Its visible flow should be dry-run -> field errors/warnings ->
explicit confirmation -> commit -> canonical local recipe link.

## Test and runtime gates

Any future UI/integration test must require:

- explicit non-secret approval for local commit;
- `cookbook-local` Compose project and app-only service;
- `COOKBOOK_TARGET_URL` resolving to HTTP loopback only;
- opt-in `local/vanilla-cookbook-adapter:0034a` image;
- no Cloudflare, AWS, GitHub Actions, tunnel, production URL, or production
  environment indicators;
- synthetic owner and candidate only;
- backup of `.local/vanilla-cookbook/db` and uploads before runtime writes;
- restore/cleanup on success, expected failure, timeout, and interruption;
- no live OpenAI or other provider call.

The test must never print recipe content, SQL, rows, absolute paths, prompts,
provider output, cookies, tokens, sessions, secrets, or environment values.
Safe operator output is limited to phase/status, HTTP status, opaque local UID,
duplicate/idempotency state, and cleanup result.

## UI behavior and messages

Until the bridge exists, the panel should say: “Local Cookbook save is not
available in this sidecar session. Use the local core verification fixture.”
It may continue to show dry-run validation and the in-memory prototype result,
but must not claim that a recipe was saved in Cookbook.

After a gated bridge is approved, user-facing states should be plain and
truthful: “Review this AI draft,” “Dry-run passed,” “Confirmation required,”
“Saved to local Cookbook,” “Duplicate requires review,” or “Local save was
rolled back; nothing was saved.” No provider internals or credential details
belong in the UI.

Safe operator diagnostics may identify the selected local image, loopback
target class, gate phase, HTTP status, opaque UID, and restore status. They
must not include session values, database paths, SQL, raw candidate bodies,
prompts, provider output, or stack traces.

## Production/exposed boundary

The local commit route must remain disabled or unavailable in exposed and
production deployments. The default external image and existing production
Compose behavior must not be changed by the future wiring task. Production
Save-to-Cookbook requires a separate reviewed auth, API, privacy, deployment,
and rollback decision; this plan does not authorize it.

The Google-first identity/storage decision in [Google-first OIDC and Future
Storage Authorization](google-first-oidc-storage-auth-architecture.md) keeps
that future authorization in the Vanilla Cookbook core. A sidecar client must
not become an OIDC session broker or receive Drive/OneDrive grants. Google
sign-in and storage consent are separate future capabilities; 0034C's
synthetic owner remains the safe local bridge.

## 0034F transport result

0034F adds a pure sidecar client for the core-owned dev-only synthetic
verification route. It is disabled by default, requires explicit local gates,
the `cookbook-local` project, loopback, and the opt-in `0034f` image marker.
It sends reviewed candidate fields and explicit approval only. It does not
export identity, sessions, cookies, tokens, provider grants, or storage grants.
The normal UI is intentionally not wired to this operator/test transport.

## 0034C result and next task

0034C completed the core-process fixture with synthetic in-process ownership,
dry-run-before-commit, explicit gates, real temporary SQLite persistence,
read-after-write, replay/conflict, duplicate review, rollback, and DB/uploads
restore. It does not establish a safe sidecar HTTP transport or browser
session, so the sidecar UI remains deferred.

The next implementation task, if approved, must define a narrow
sidecar-to-core transport using this safe local boundary without exporting
identity or credentials. It must not enable production or exposed targets.

## Next task

Recommend a future sidecar-to-core local transport task only after reviewing
the 0034C fixture evidence. It should call a narrow core-owned boundary,
preserve dry-run-before-commit and explicit approval, and never export a
session, cookie, token, or sidecar-owned identity. Production/exposed wiring
must remain out of scope.

## Explicit non-goals

No sidecar route, UI real-save path, core route change, production save,
public route, migration, auth/session integration, browser automation, direct
sidecar DB write, AWS, GitHub Actions, Cloudflare, tunnel, provider call, QMD,
analytics, ads, payment, SSO/BYOS, secrets, prompts, provider outputs,
screenshots, traces, raw datasets, generated indexes, local env values, DBs,
uploads, cookies, tokens, sessions, or browser artifacts are added here.
