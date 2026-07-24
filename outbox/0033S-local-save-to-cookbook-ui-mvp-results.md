# 0033S Local Save-to-Cookbook UI MVP Results

Status: complete, local/internal-only.

## Routes and UI

Added two internal sidecar routes, both disabled by default and hidden from
the OpenAPI schema:

- `POST /adapter/recipes/import-candidate/dry-run`
- `POST /adapter/recipes/import-candidate/local-commit`

They require the three explicit non-secret local gates, verified loopback
target, `cookbook-local` scope, synthetic ownership, and a loopback client.
They reject exposed, production, tunnel, AWS, GitHub, and non-loopback targets
before service execution. No native upstream `POST /api/recipe` call is made.

The `/demo` importer now renders an unsaved AI draft review panel. It permits
bounded title/description review, local dry-run, safe status/error/warning
display, and explicit confirmation before invoking the local commit service.
The UI states that production save is unavailable and keeps the 0033Q harness
as the disposable DB/write proof path.

## Behavior and validation

The routes delegate to the existing 0033N dry-run operation and 0033R
in-memory local commit service. Normal UI/API code does not write SQLite,
uploads, files, or the upstream app. Existing importer/mock flows remain
unchanged, and no live provider is called.

Focused UI/route, dry-run, commit, and demo tests: 28 passed. Full repository
validation, offline evals, compose checks, and mock demo validation were run
without live OpenAI. No screenshots, traces, browser artifacts, local runtime
data, secrets, prompts, or provider bodies were committed.

## Explicit non-goals

This does not implement production Save-to-Cookbook, a public production route,
the native authenticated core-app adapter, SQLite/database or upload writes,
migrations, auth/SSO/BYOS, analytics, ads, payment, AWS, GitHub Actions,
Cloudflare/tunnels, provider routing, QMD, or live calls. The 0033Q readiness
harness remains the only approved disposable DB/write evidence path.
