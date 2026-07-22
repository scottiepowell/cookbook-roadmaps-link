# 0030I-8S live diagnostic output-cap JSON envelope results

The approved diagnostic reached the live importer path and safely classified
the provider failure as `output_cap_or_incomplete_response` with
`JSONDecodeError`, but PowerShell surfaced a native command error frame instead
of the expected diagnostic envelope.

The wrapper now captures helper stdout/stderr without emitting native error
objects, maps the bounded category and safe error type, emits a concise failed
envelope, and exits non-zero without retrying. The safe guidance explains that
preflight/configuration passed but the provider response was incomplete or not
schema-parseable within the output cap. Existing timeout, quota, auth, network,
model, and configuration categories remain mapped safely.

Deterministic tests use a fake helper and verify the category, `JSONDecodeError`,
non-zero failed status, absence of `NativeCommandError`, and secret-safe output.
Preflight remains no-call. No live provider call was made for this correction.

Validation: env-loader, offline evals, Git Bash validator (349 tests), mock
smoke, Docker config, and Playwright mock UI (4/4) passed; live wrappers
skipped. No automatic cap increase or repeated retry was added.

Explicit non-goals: no live success claim, secrets, raw provider output,
prompts, stack traces, AWS/platform work, production storage/auth, public
exposure, screenshots, browser artifacts, vector DB, embeddings, raw datasets,
persistent indexes, or disk cache.

A bounded follow-up acceptance is ready only as one explicitly approved run
after the operator documents any cap/timeout adjustment; it was not run here.
