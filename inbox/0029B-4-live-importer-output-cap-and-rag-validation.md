# Task 0029B-4: Live Importer Output Cap And RAG Validation

## Goal

Fix the remaining manual live importer failures after RAG-informed recipe creation. Omelet now succeeds, but carbonara, cheesecake, and chicken/rice casserole still return `503 Service Unavailable` from the importer path.

This task should diagnose and fix the likely live structured-output failure mode, improve UI citation display, and make full-dataset RAG manual validation reliable.

## Observed Manual Results

### Launch command used

The operator launched:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Startup summary showed:

```text
Provider: openai
Model: gpt-5.4-nano
Live tests enabled: true
Budget cents: 25
Max output tokens: 500
AI timeout seconds: 20
Provider debug: false
Dataset path: C:\Users\scott\cookbook-roadmaps-link\.tmp-ai-demo\local\dataset
Dataset index limit: 25
```

This means the test was still using the generated fixture dataset, not the full local recipe dataset.

### Omelet success

Input:

```text
omelet with eggs cheese maybe onions cooked in butter fold it over
```

Result:

```text
status=200
provider=openai
model=gpt-5.4-nano
servings=4
retrieved_count=2
dataset_limit=25
index.document_count=3
usage.output_tokens=476
```

Omelet quality improved:

- title: `Cheese-Onion Omelet`
- default servings: 4
- quantities were populated
- steps included beating eggs before cooking
- retrieval metadata was present
- raw JSON contained citations

Important token observation:

```text
AI_MAX_OUTPUT_TOKENS was 500 and omelet used 476 output tokens.
```

This is very close to the configured output cap. The remaining recipe types likely require more structured JSON output and may be failing due to incomplete/truncated provider responses or invalid JSON after output cap exhaustion.

### Remaining failures

The next three importer attempts returned 503:

```text
POST /ai/import-recipe HTTP/1.1 503 Service Unavailable
safe_error_type=RecipeImportProviderError
```

Durations:

```text
4783.1 ms
3724.48 ms
4304.16 ms
```

These were likely the carbonara, cheesecake, and chicken/rice casserole cases from `0029B` manual testing.

### UI citation inconsistency

The UI text said:

```text
Citations and provenance
No citations returned for this response.
```

But the raw JSON contained importer citations and retrieval metadata.

This suggests the demo UI is not rendering importer citations correctly even though the API response includes them.

### RAG quality issue

The omelet response retrieved fixture dataset records:

- `Tomato Pasta Skillet`
- `Lemon White Bean Toasts`

Those are not good omelet matches. This happened because the startup script used the generated `.tmp-ai-demo` fixture dataset with only 3 documents.

For meaningful RAG validation, the operator needs to use the real local `recipe-dataset` directory or another explicit full dataset path.

## Likely Root Causes To Investigate

1. `AI_MAX_OUTPUT_TOKENS=500` is too low for RAG-informed structured recipe creation. Omelet used 476 output tokens, so richer recipes may be truncated/incomplete.
2. Provider errors are still opaque because `ProviderDebug=false` was used in the observed run.
3. The manual run used generated fixture dataset instead of the full recipe dataset.
4. Importer citations exist in raw JSON but are not displayed in the demo UI.
5. The provider path may still collapse invalid JSON/incomplete structured output into generic `RecipeImportProviderError` without classifying the cause.

## Required Fixes

### 1. Increase live manual-demo default output tokens for recipe creation

The startup script currently defaults live manual demo to `MaxOutputTokens=500`.

For RAG-informed recipe creation, use a safer default such as:

```text
AI_MAX_OUTPUT_TOKENS=900
```

or document and recommend `900` for live importer testing.

Requirements:

- Keep mock/offline defaults safe.
- Keep live smoke/eval wrappers budgeted separately if needed.
- Ensure manual live recipe creation has enough output room for 4-serving quantities, notes, citations, and 4-8 steps.
- Add docs explaining why the importer needs a larger output cap than tiny smoke tests.

### 2. Improve provider error classification for incomplete/truncated structured output

When OpenAI structured generation fails, distinguish these local diagnostic categories when possible:

- output cap / incomplete response;
- invalid JSON after provider response;
- schema rejection;
- model not available;
- quota/rate/auth/network failure;
- timeout.

Keep public UI response safe, but local logs with `AI_PROVIDER_DEBUG=true` should include sanitized error type and summary.

If the provider returns incomplete output because `max_output_tokens` is too low, surface a safe warning/log message that recommends increasing `AI_MAX_OUTPUT_TOKENS`.

### 3. Add or update importer-only live diagnostic

Add or update a diagnostic command/script so the operator can test one importer case at a time without using the browser.

It should support passing an input string and safe defaults like:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke-openai-importer-live.ps1 `
  -Text "cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill" `
  -MaxOutputTokens 900 `
  -AiTimeoutSeconds 60 `
  -ProviderDebug
```

The diagnostic should:

- require explicit live opt-in;
- never print secrets;
- print provider/model/status;
- print safe error class/summary when debug is enabled;
- print token usage when successful;
- print draft title, servings, ingredient count, instruction count, retrieval count, and citation count;
- not commit artifacts.

If a script already exists, update it instead of creating another.

### 4. Fix demo UI importer citation rendering

The raw JSON contains importer `citations`, but the UI reported no citations.

Update the demo UI so the importer panel correctly displays:

- citation count;
- citation titles;
- snippets;
- provenance/source id;
- retrieval metadata when present.

Do not expose private local file paths in the UI.

### 5. Improve full-dataset RAG launch documentation

Document that this command is the correct manual RAG test path:

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

Also document that the safe default still uses generated `.tmp-ai-demo` fixtures, so citations from default mode may not be semantically useful.

### 6. Add tests

Add offline tests only.

Tests should cover:

- startup script default/recommended live output-token behavior if testable;
- provider debug/error classifier recognizes incomplete output or invalid JSON safely;
- importer diagnostic script syntax and guard behavior;
- UI renders importer citations when present;
- UI still handles no-citation importer responses;
- docs include full-dataset RAG launch command;
- existing input-quality and mock paths remain unchanged.

Do not run live OpenAI during normal validation.

## Manual Re-Test Plan After Fix

After implementation, the operator should run:

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

Then test:

```text
omelet with eggs cheese maybe onions cooked in butter fold it over
carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat
cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill
chicken and rice casserole chicken rice cream soup cheese bake until hot
```

Expected:

- all four return 200;
- provider is `openai`;
- model is `gpt-5.4-nano`;
- servings is 4 unless user says otherwise;
- quantities are populated where reasonable;
- steps are 4-8 and useful for multi-step dishes;
- carbonara does not require heavy cream;
- cheesecake has multiple clear steps;
- chicken/rice casserole includes safe bake/doneness guidance;
- citations/provenance display in UI when retrieval returns matches;
- no secrets appear in logs or UI.

## Documentation Updates

Update as needed:

```text
docs/ai-live-demo-runbook.md
docs/manual-recipe-entry-acceptance-2026-07.md if present
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0029B-4-live-importer-output-cap-and-rag-validation-results.md
```

## Validation

Run normal offline validation:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live smoke and live eval wrappers should skip cleanly unless explicit opt-in settings are present.

Do not run live OpenAI during normal validation unless the operator explicitly chooses optional manual live validation.

## Non-Goals

Do not implement:

- production auth;
- paid access;
- invite sessions;
- database migrations;
- public route exposure;
- Cloudflare route changes;
- raw dataset commits;
- vector DB/Qdrant/Postgres;
- long-term recipe write-back;
- screenshot automation;
- committed `.tmp-ai-demo/` artifacts;
- committed raw provider response JSON;
- committed API keys, env files, raw datasets, screenshots, logs, or credentials.

## Outbox Report

Create:

```text
outbox/0029B-4-live-importer-output-cap-and-rag-validation-results.md
```

Include:

- Summary
- Observed manual results
- Likely root cause
- Output cap changes
- Provider diagnostics changes
- UI citation rendering fix
- Full-dataset RAG launch docs
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Recommended next task
- Artifact safety confirmation

## Commit

Commit and push:

```bash
git add ai-api scripts docs README.md outbox/0029B-4-live-importer-output-cap-and-rag-validation-results.md

git commit -m "mailbox: complete task 0029B-4 live importer output cap and rag validation"

git push origin main
```

## Done Criteria

- Manual live importer has enough output-token room for richer recipe creator JSON.
- Provider error diagnostics can distinguish likely output cap/incomplete response from other provider failures locally.
- Importer-only live diagnostic exists or is clearly documented.
- Demo UI displays importer citations/provenance when raw JSON contains citations.
- Full-dataset RAG launch path is documented.
- Mock/offline defaults remain safe.
- Normal validation remains offline.
- No generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.
