# 0029B-4 Live Importer Output Cap And RAG Validation

Status: complete.

## Summary

Raised the live manual importer output-cap recommendation, improved provider diagnostics for truncated structured responses, fixed importer citation rendering in the demo UI, and documented the full-dataset RAG launch path.

This change stays within the existing offline-first demo model. It does not add production auth, billing, public live AI exposure, migrations, route changes, or any raw dataset commits.

## Observed Manual Results

- Omelet succeeded with the RAG-informed recipe creator behavior.
- Cheesecake succeeded after raising the output cap.
- The successful cheesecake run used `provider=openai`, `model=gpt-5.4-nano`, `servings=4`, `output_tokens=508`, `total_tokens=1246`, `status=200`.
- Cheesecake returned `Classic Cheesecake (Graham Cracker Crust)` with useful 4-step instructions, ingredient quantities, and estimated-quantity notes.
- The default `.tmp-ai-demo` fixture dataset is too small for meaningful RAG quality validation. It only has three demo records, so citations there are useful for smoke tests but semantically weak.

## Evidence That `500` Was Too Low

The cheesecake success at `508` output tokens confirms the earlier `AI_MAX_OUTPUT_TOKENS=500` cap could truncate structured JSON and trigger `RecipeImportProviderError` / `503 Service Unavailable`.

The live manual recipe-creator path now recommends `AI_MAX_OUTPUT_TOKENS=900`.

## Output Cap Change And Recommendation

- `scripts/start-ai-demo-local.ps1` now defaults the OpenAI manual recipe-creator path to `AI_MAX_OUTPUT_TOKENS=900` unless an explicit override is supplied.
- The runbook and README now call out that the smaller smoke-test cap is not enough for RAG-informed structured drafts.
- The dedicated importer-only smoke script defaults to the higher cap as well, while still allowing manual overrides.

## Provider Diagnostics Changes

- Added sanitized provider diagnostic details under `AI_PROVIDER_DEBUG=true` and `-ProviderDebug`.
- Provider failures are now better classified where possible as:
  - `output_cap_or_incomplete_response`
  - `invalid_json`
  - `schema_rejection`
  - `bad_model`
  - `auth`
  - `quota_or_rate_limit`
  - `timeout`
  - `network`
- Diagnostics stay safe. They do not log API keys, Authorization headers, raw prompts, raw provider responses, `.env` values, or secret-like strings.

## UI Citation Rendering Fix

The importer panel now renders importer citations directly instead of falling through to the empty-state message.

It shows:

- citation count;
- citation titles;
- snippets;
- provenance and source IDs;
- retrieval metadata when present.

The UI still avoids private local file paths.

## Full-Dataset RAG Launch Docs

The documented full local RAG launch command is:

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

Docs also explain that:

- the default launch still uses generated `.tmp-ai-demo` fixtures;
- fixture citations may be semantically weak because only three demo records exist;
- the full `recipe-dataset` path is needed for meaningful RAG validation;
- raw dataset files must not be committed.

## Tests Added

- UI renders importer citations when present.
- UI handles no-citation importer responses.
- Provider debug classification covers output-cap / incomplete-response and invalid-JSON paths.
- The startup script syntax remains valid.
- The new importer-only live smoke script parses and skips cleanly without opt-in.
- Docs include the full-dataset RAG launch command.
- Mock/offline defaults remain safe.
- Live smoke and live eval wrappers still skip without opt-in.

## Validation Results

Ran the required validation set:

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py` -> passed `17/17`
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests` -> hit the known Windows temp ACL issue under `C:\Users\scott\AppData\Local\Temp\pytest-of-scott`
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh` -> passed `138` pytest cases and `17` offline eval cases
- `git diff --check` -> passed
- `docker compose config --quiet` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1` -> passed
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1` -> skipped cleanly without opt-in
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1` -> skipped cleanly without opt-in

The dedicated importer-only live diagnostic script was also exercised in skip mode and returned a clean opt-out message.

## Live OpenAI

Live OpenAI was not run during normal validation.

## Recommended Next Task

Move to the next follow-on manual acceptance or architecture task in the `0029C` line, using the now-documented full-dataset RAG launch path as the baseline for importer quality checks.

## Artifact Safety

No `.tmp-ai-demo/` artifacts, raw response JSON, API keys, env files, raw datasets, screenshots, logs, credentials, or generated live artifacts were committed.
