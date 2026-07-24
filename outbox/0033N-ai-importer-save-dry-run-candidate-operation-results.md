# 0033N AI Importer Save Dry-Run Candidate Operation Results

## Summary

- Added the internal `dry_run_import_candidate_operation` service in
  `ai-api/app/cookbook_import_dry_run.py` around the 0033M fixture adapter.
- The operation defaults to a safe unavailable response and requires an
  explicit non-secret `enabled=True` call to run locally.
- No HTTP route was added because the current sidecar lacks an authenticated
  core-app adapter boundary; this avoids creating a public/exposure decision.
- Enabled calls return a stable envelope containing mapped payloads,
  field-level errors, warnings, duplicate candidates, idempotency replay or
  key-conflict metadata, and contract/schema versions.
- The operation has no database, upload, filesystem, network, provider,
  production, or authentication dependency.
- Focused tests cover disabled gating, valid mapping, invalid/unsafe fields,
  duplicates, idempotent replay, key reuse conflict, schema mismatch, and
  safe-envelope/no-write boundaries.

## Validation

Passed: 17 focused dry-run/adapter tests, 375 sidecar tests, env-loader checks,
offline evals, repository validation, Compose configuration, mock demo, and
`git diff --check`. Normal validation made no live OpenAI calls and did not
require Docker or a running Vanilla Cookbook container.

## Explicit non-goals

No Save-to-Cookbook button, public route, commit endpoint, database or upload
write, production integration, auth, SSO/BYOS, analytics, ads, payment,
AWS/platform work, provider routing/model change, QMD integration, live call,
secret, prompt, provider output, screenshot, trace, raw dataset, generated
index, local environment value, local DB, upload, or browser artifact was
added.
