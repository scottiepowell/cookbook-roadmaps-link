# 0034P — Public AI Transient Provider Recovery

## Goal

Fix the intermittent generic unavailable error observed from the authenticated
public AI recipe importer while preserving authentication, operator-gate, and
provider-budget boundaries.

## Required behavior

- classify safe sidecar provider failures as retryable or deterministic;
- permit exactly one core-owned retry only for timeout, network, temporary
  provider, or incomplete structured-output failures;
- run the retry through the existing sidecar gate and budget guard;
- never retry account/quota, authentication, model, schema, payload,
  rate-limit, or authorization failures;
- return a useful safe message if the bounded retry also fails;
- keep `gpt-5.4-nano` pinned and keep the sidecar private;
- validate, rebuild, redeploy, and record only safe outcomes.

## Non-goals

No new AI workflow, automatic recipe save, identity/session ownership change,
Cloudflare/DNS change, broader route exposure, or secret logging.
