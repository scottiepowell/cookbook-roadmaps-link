# Core-Owned Local Auth Commit Verification

Status: verified against a disposable external-workspace SQLite database;
route-level browser/session verification remains intentionally blocked.

Date: 2026-07-25

## External verification

0034A added an opt-in integration test in the separate source-owned Vanilla
Cookbook workspace:

- Branch: `openclaw/0034A-core-owned-local-auth-commit-verification`
- Commit: `ffd71da4a8b2c83a8699bad4f2bc5fd77bd991d4`
- Test: `src/tests/importCommit.sqlite.test.js`
- Image: `local/vanilla-cookbook-adapter:0034a`

No external source was copied into this repository. The image was built
locally and was not pushed or deployed.

## Synthetic core ownership fixture

The integration test runs only when `RUN_LOCAL_AUTH_COMMIT_DB=1` is explicitly
set. It creates a temporary SQLite database by pushing the existing schema to
that disposable path, then creates one synthetic core `AuthUser` row. The
commit service receives an in-process core user context derived from that
fixture's generated ID. No Lucia session, browser cookie, auth token, real
account, or credential is created, exported, printed, or forwarded.

The test invokes the core `commitRecipeImport` service with real Prisma
persistence, not the sidecar and not a direct sidecar database write. It
verifies the resulting recipe by safe UID, owner ID, name, servings, and empty
categories/photos/null embedding relations only.

## Evidence

The opt-in SQLite test passes 3/3:

- one synthetic owner creates exactly one first-scope recipe;
- safe read-after-write returns the canonical UID and expected ownership;
- same-key replay returns the original UID without a second row;
- same-key changed payload returns conflict;
- different-key matching content returns review-required duplicate;
- foreign-owner create failure leaves recipe count unchanged;
- categories, photos/uploads, and embeddings remain absent;
- a schema snapshot is copied before the fixture write and restored after the
  test; restored recipe count is zero before temporary files are removed.

The combined external focused suite passes 23/23, including the existing
0033X/0033Y adapter and route tests. The `local/vanilla-cookbook-adapter:0034a`
image built successfully and the sidecar guarded scripts started it under
`cookbook-local`; only the app service ran and loopback returned HTTP 200. It
was stopped afterward.

## Route and UI readiness

The real database proof is service-level with a synthetic core user context.
0034C now adds a guarded core-process fixture that keeps synthetic auth
in-process without exporting credentials.
Route-level verification remains blocked by the explicit prohibition on
creating or exporting a session/cookie/token. The commit route still requires
the local gate, loopback target, normal `requireAuth(locals)`, and explicit
confirmation. The sidecar UI must not be wired to a real-save path until a
separate task approves a safe in-process core test/session boundary and
disposable `cookbook-local` backup/restore procedure for that route.

Production Save-to-Cookbook remains unimplemented. Direct sidecar DB writes,
browser/session automation, auth bypass, and credential forwarding remain
rejected.

## Explicit non-goals

No production or public route, production write-back, migration, sidecar UI
real-save wiring, browser automation, cookies, tokens, sessions, real users,
provider call, AWS, GitHub Actions, Cloudflare, QMD, analytics, ads, payment,
SSO/BYOS, source vendoring, screenshots, traces, row dumps, or runtime
database/uploads were committed.
