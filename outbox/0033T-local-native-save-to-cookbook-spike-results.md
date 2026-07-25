# 0033T Local Native Save-to-Cookbook Spike Results

Status: blocked by a precise local native ownership/session boundary.

## Review result

The disposable `cookbook-local` runtime started on `127.0.0.1:3000` and was
stopped after read-only inspection. The upstream `POST /api/recipe` route was
inspected but not called. It requires `requireAuth(locals)`, where `locals.user`
comes from Lucia session validation in `hooks.server.js`. An anonymous request
cannot create a recipe.

The route accepts multipart form data, creates the Prisma Recipe row with the
authenticated `userId`, then may process remote image URLs, uploaded images,
and background semantic embeddings. It does not provide a dry-run mode or an
adapter-specific transaction/rollback envelope. The route response exposes a
canonical UID only after the initial row write.

## Blocker

A safe native spike would need a synthetic authenticated local session and
cookie, plus a controlled user setup and proof that all post-create side
effects are disabled or compensated. This task explicitly forbids committing
or exposing cookies, auth tokens, session values, real accounts, or unsafe
session handling. Therefore native local save was not implemented, no route
was wired to it, and no database/auth row was modified.

The existing 0033S UI remains an in-memory local simulation, and 0033Q remains
the approved disposable DB/write evidence harness. A future task may proceed
only after the core app provides a reviewed local synthetic-user/session or
service-to-service adapter contract with explicit side-effect and rollback
semantics.

## Validation and non-goals

The local runtime start/check path and read-only source review completed. No
live OpenAI call, production/exposed target, browser session, cookie, token,
row dump, upload, or artifact was used. No native service, production save
path, public route, migration, auth integration, analytics, ads, payment,
AWS, GitHub Actions, Cloudflare, provider, QMD, or UI behavior was added.
