# 0033D Traffic Analytics and Behavior Tracking ADR Results

## Summary

- Created the [Traffic Analytics and Behavior Tracking ADR](../docs/traffic-analytics-behavior-tracking-adr.md).
- Researched high-level ICO, CNIL, EDPB, and GDPR privacy/consent,
  minimization, and storage-limitation guidance.
- Defined product questions for visits, sessions, feature use, AI workflows,
  errors, timer/budget outcomes, retention, and future commercial reporting.
- Defined an allowlisted event taxonomy and explicit non-tracked data,
  including recipe text, prompts, provider output, tokens, BYOS contents,
  sensitive details, payment data, and raw identifiers.
- Defined anonymous, pseudonymous, account-linked, operator, and commercial
  analytics modes; retention/deletion; aggregation; vendor tradeoffs; and
  staged implementation options.
- Kept AI provider metering authoritative for cost controls and deferred ad/
  sponsor/conversion tracking to the future monetization ADR.

## Validation

`git diff --check` and `scripts/validate-repo.sh` passed. No analytics
collection, vendor, script, cookie, pixel, beacon, database migration, public
route, production auth, SSO/BYOS implementation, ad/monetization implementation,
AWS/platform work, live provider call, secret, prompt, provider output,
screenshot, trace, dataset, or generated index was added.

## Explicit non-goals

Provider/legal facts require jurisdiction-specific review before any future
implementation. Any implementation must preserve mock/offline validation,
purpose limitation, consent/choice, minimization, retention, and deletion.
