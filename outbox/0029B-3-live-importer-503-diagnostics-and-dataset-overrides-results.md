# 0029B-3 Live Importer 503 Diagnostics And Dataset Overrides

Status: complete.

## Summary

Fixed the local live importer blocker and the operator startup gap without widening normal runtime behavior.

Primary changes:

- Added safe opt-in provider diagnostics through `AI_PROVIDER_DEBUG=true`.
- Normalized strict OpenAI JSON schemas by recursively stripping unsupported metadata such as `default`, `examples`, `title`, and `description`.
- Preserved `additionalProperties=false` and strict required-property behavior in normalized schemas.
- Kept importer application behavior defaulting `servings` to `4` without relying on provider-schema defaults.
- Extended `scripts/start-ai-demo-local.ps1` with:
  - `-RecipeDatasetDir`
  - `-RecipeDatasetIndexLimit`
  - `-AiTimeoutSeconds`
  - `-ProviderDebug`
- Documented a browser-free importer-only diagnostic using `Invoke-RestMethod`.

## Root Cause

The manual live importer `503` path was consistent with strict OpenAI structured-output schema rejection. The importer schema sent Pydantic metadata such as `default: 4` on `RecipeImportDraft.servings`, plus other descriptive fields that are valid for local validation but brittle for strict provider schema acceptance.

The normalization path now strips unsupported metadata recursively before the provider call. This keeps the provider request strict while preserving local validation and application-side defaults.

## Safe Provider Diagnostics

When `AI_PROVIDER_DEBUG=true` is enabled locally, structured logs can now include:

- `provider_error_category`
- `provider_error_type`
- `safe_error_summary`

Categories distinguish:

- `timeout`
- `schema_rejection`
- `bad_model`
- `quota_or_rate_limit`
- `auth`
- `network`
- `provider_call_failed`

Diagnostics remain sanitized. They do not log API keys, Authorization headers, raw prompts, raw provider responses, `.env` contents, or secret-like strings.

Public browser/API errors remain unchanged and safe.

## Startup Script Result

`scripts/start-ai-demo-local.ps1` still defaults to:

- `AI_PROVIDER=mock`
- generated `.tmp-ai-demo` fixtures
- no live OpenAI unless `-Provider openai -EnableLiveTests`

It now also supports full local RAG operator overrides, including the documented command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 `
  -Provider openai `
  -EnableLiveTests `
  -OpenAIModel gpt-5.4-nano `
  -MaxOutputTokens 900 `
  -LiveTestBudgetCents 25 `
  -AiTimeoutSeconds 60 `
  -RecipeDatasetDir recipe-dataset `
  -RecipeDatasetIndexLimit 5000 `
  -ProviderDebug
```

The startup summary remains secret-safe and now also prints timeout, provider-debug state, and dataset index limit.

## Documentation Updated

- `docs/ai-live-demo-runbook.md`
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md`

## Validation

Ran the required offline validation commands:

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` -> passed `17/17`
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` -> hit the known direct-Windows temp-directory ACL issue under `C:\Users\scott\AppData\Local\Temp\pytest-of-scott`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` -> passed, including `130` pytest cases and `17` offline eval cases
- `git diff --check` -> passed
- `docker compose config --quiet` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` -> skipped cleanly without opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` -> skipped cleanly without opt-in

Optional live OpenAI validation was not run.

## Artifact Hygiene

No raw dataset files, generated live artifacts, `.tmp-ai-demo/`, raw provider responses, secrets, API keys, environment files, screenshots, logs, or credentials were committed.
