# 0030I-8 bounded live importer 503 diagnostics results

## Outcome

The 0030I-5 audit recorded one authorized live importer attempt returning HTTP
503. It was not retried, and no live call was made during this follow-up.
The cause therefore remains a provider-availability/configuration category,
not a claimed live success.

This task adds `scripts/diagnose-live-importer.ps1`. It loads the ignored local
environment through the existing helper, prints a redacted preflight, requires
explicit `-ApproveLiveCall`, and permits at most one importer call using only
`gpt-5.4-nano`. It stops before any provider call when live opt-in, key, model,
budget, token, timeout, or provider-call settings are invalid. Output is
limited to safe facts and categories such as `missing_api_key`,
`live_not_enabled`, `model_not_allowed`, `provider_timeout`,
`provider_account_or_quota_unavailable`, and `provider_http_error_redacted`.
No retry is attempted.

The importer API now returns a bounded `status=unavailable` envelope containing
`safe_unavailable_category` and `safe_guidance`; the demo UI renders that safe
guidance without exposing provider internals. Deterministic tests cover
approval gating, missing-key/model preflight, timeout categorization, the safe
503 response, and forbidden-secret markers. Existing mock and Playwright paths
remain offline-only.

## Validation

- `scripts/test-ai-env-file-loader.ps1`: passed.
- Offline evals: passed (39/39).
- Git Bash repository validator: passed; the direct Windows run may show the
  known `pytest-of-scott` temp ACL failure.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- Mock smoke: passed; no live provider call.
- Live smoke/eval wrappers: skipped without an explicit live opt-in.
- Playwright UI runner: remains mock-only and was not used for live diagnosis.

The optional manual `-ApproveLiveCall` diagnostic was not run in this task;
no additional live call was authorized. Follow-up live acceptance is not yet
ready to claim until an operator explicitly runs the one-call diagnostic and
records only its safe provider category/result.

## Explicit non-goals

No production storage, auth, payment, public exposure, AWS/platform work,
secondary provider, vector database, embeddings, upstream UI rewrite, raw
dataset, persistent index, disk cache, screenshots, traces, or provider secret
handling was added.
