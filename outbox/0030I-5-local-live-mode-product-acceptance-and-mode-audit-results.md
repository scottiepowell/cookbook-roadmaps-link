# 0030I-5 Local live mode product acceptance and mode audit

## Mock audit

- Started the sidecar with explicit `-Provider mock`.
- Safe readiness reported `mock` / `mock-basic` with offline demo mode enabled;
  ignored live configuration did not enable live calls for that process.
- `scripts/demo-ai-mock.ps1` passed, including importer, Recipe Session
  start/follow-up, Ask My Cookbook, Dataset Ask, and Meal Planner metadata.
- The Chromium Playwright suite passed 4/4. It confirmed normalized
  `mock`/`mock-basic` request payloads for all provider-backed workflows and
  confirmed Live selection on the mock server produces safe unavailable UI
  guidance rather than a disguised mock success.

## No-argument local live profile audit

- The ignored local runtime profile started the sidecar as live-capable with
  safe readiness `openai` / `gpt-5.4-nano`.
- One allowed importer acceptance request was made with requested
  `openai` / `gpt-5.4-nano`.
- It returned controlled HTTP 503. No raw provider body, prompt, key,
  environment value, or stack trace was captured or reported, and the request
  was not retried. Therefore this audit does **not** claim a successful new
  live importer acceptance.

## Validation

- `scripts/test-ai-env-file-loader.ps1`: passed, 5/5.
- Launcher profile tests: passed, 12/12.
- Playwright mock mode audit: passed, 4/4 Chromium tests.
- Offline evals: passed, 39/39.
- Git Bash repository validator: passed, 338 pytest tests plus offline evals.
- `git diff --check`, Docker Compose configuration, and mock smoke: passed.
- Live smoke and live-eval wrappers were run with live variables explicitly
  disabled for normal validation and skipped without provider calls.

## Boundaries and follow-up

No AWS/platform work, production auth, payment, public routing, provider
routing overhaul, secondary-provider runtime, vectors/embeddings, datasets,
screenshots, traces, videos, persistent indexes, or disk cache were added.

Before claiming a new successful live acceptance, diagnose the controlled 503
with explicit local operator approval and safe provider-account/quota/model
availability checks. Keep that investigation bounded to one approved workflow
and do not expose provider details or secrets. Playwright remains mock-only.
