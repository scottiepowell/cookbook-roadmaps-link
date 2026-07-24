# 0033I Product Cookbook Link Target Correction Results

## Summary

- Root cause: `/product/cookbook` always redirected to
  `http://127.0.0.1:3000/`, which is correct for local Compose but unreachable
  from an exposed browser when the public Cookbook URL is used.
- Added validated, non-secret `COOKBOOK_TARGET_URL` configuration. Unset or
  invalid values safely fall back to the local Compose target; public exposed
  operation can select `https://cookbook.roadmaps.link/` or its appropriate
  configured Cookbook URL.
- Updated the product shell recovery copy and integration/runbook/checklist/
  status/backlog/roadmap/README documentation to distinguish the local
  Cookbook target, exposed Cookbook target, and sidecar `/demo` workspace.
- Kept `/product/ai` redirecting to `/demo` and did not proxy or rewrite the
  external Vanilla Cookbook application.
- Added deterministic tests for target defaults, safe URL validation, public
  target generation, recovery messaging, secret non-leakage, and existing AI
  handoff behavior.

## Validation

Required mock/offline validation passed. No live OpenAI call was made.

## Explicit non-goals

No AI provider routing, live token cap, importer schema, Save to Cookbook,
QMD, analytics, ads, SSO/BYOS, payment, AWS/platform, Cloudflare/DNS, public
infrastructure, upstream proxy/rewrite, secret, prompt, provider output,
screenshot, trace, local environment value, raw dataset, generated index, or
browser artifact was added.
