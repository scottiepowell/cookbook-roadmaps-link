# 0033H Local Live Output Token Cap Correction Results

## Summary

- Updated `scripts/start-ai-demo-local.ps1` so the safe local live default is
  `AI_MAX_OUTPUT_TOKENS=500`.
- OpenAI local live mode now accepts `500..1000` inclusive and fails fast with
  the required clear error for values below 500 or above 1000.
- Preserved the `gpt-5.4-nano` local model allowlist, live opt-in, 1..25-cent
  budget guard, secret redaction, startup summary, and mock/offline behavior.
- Updated the local live launcher guidance in README, runbooks, acceptance,
  feature-status, and backlog documentation. Separate smoke/eval/importer
  workflow caps remain distinct.
- Added deterministic subprocess coverage for caps 500, 1000, 499, and 1001,
  plus mock isolation and safe-default writer behavior. No live provider call
  was made.

## Validation

The required env-loader test, offline evals, repository validation, mock demo,
live-wrapper skip behavior, Compose config check, and `git diff --check` were
run for handoff. Live smoke/eval wrappers remain opt-in and skip without live
configuration.

## Explicit non-goals

No provider routing, model allowlist, model support, QMD, browser UI,
analytics, ads, monetization, auth, payment, SSO/BYOS, session timer,
AWS/platform, Cloudflare/DNS, public route, live OpenAI call, secret, prompt,
provider output, screenshot, trace, raw dataset, generated index, or local
environment value was added.
