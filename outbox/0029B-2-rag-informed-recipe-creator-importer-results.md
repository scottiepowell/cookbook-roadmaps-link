# 0029B-2: RAG-Informed Recipe Creator Importer Results

Status: complete.

## Summary

Updated `POST /ai/import-recipe` so the importer behaves as an import/create workflow for rough recipe notes. It now defaults to 4 servings, estimates missing quantities where reasonable, discloses estimates in notes, retrieves bounded local dataset examples before provider calls when available, and returns retrieval metadata plus citations/provenance.

## Manual Findings And Root Cause

Preserved operator observations:

```text
Results from omelet with cheese: steps are pretty weak; step 1 should be to scramble the eggs.
Results from carbonara recipe were acceptable.
Results from cheesecake: the steps were just one, very weak.
Results from chicken and rice casserole: weak steps.
```

The manual run used:

```text
provider=openai
model=gpt-5.4-nano
```

Root cause: the importer prompt only sent the raw user recipe text to the provider. It did not retrieve similar dataset examples, did not require a default serving count, did not require estimated quantities, returned no citations/provenance, and did not strongly require multi-step recipe structure.

## Current Importer Behavior Before Change

Before this task, `ai-api/app/importer.py` built a provider prompt from only:

```text
Recipe text:
<user input>
```

The response schema did not include servings, retrieval metadata, or importer citations.

## RAG Retrieval Design

The importer now:

1. runs deterministic input-quality checks first;
2. returns rejected or clarification responses without retrieval or provider calls;
3. searches the configured local dataset for a small bounded set of similar examples;
4. passes up to 3 examples into the provider prompt;
5. uses examples only for structure, proportions, and step completeness;
6. preserves the user's core ingredients and dish intent;
7. falls back with a warning when dataset examples are unavailable.

## Serving-Size Behavior

`RecipeImportDraft` now includes `servings`, defaulting to 4 when the user does not specify a serving count. The importer also reads simple explicit serving phrases such as `serves 2` or `for 6`.

## Schema Changes

Added:

- `RecipeImportDraft.servings`
- `RecipeImportCitation`
- `RecipeImportRetrievalMetadata`
- `RecipeImportResponse.retrieval`
- `RecipeImportResponse.citations`

## Prompt Changes

The importer prompt now asks for:

- practical import/create behavior from rough notes;
- default 4 servings unless specified;
- plausible quantities when omitted;
- estimate disclosure in notes;
- bounded use of retrieved examples for structure only;
- no verbatim copying of retrieved recipes;
- preservation of user ingredients and dish intent;
- 4 to 8 action-oriented steps for normal recipes;
- recipe-specific quality targets for omelet, carbonara, cheesecake, and chicken casserole.

## UI Changes

The demo importer result now displays:

- servings;
- ingredient quantities and notes;
- multi-step instructions;
- warnings/notes;
- importer citations and provenance when dataset examples are retrieved.

## Tests Added

- Importer uses dataset RAG when dataset is available.
- Importer falls back when dataset is unavailable.
- Response includes retrieval metadata and citations.
- Default servings is 4.
- Missing quantities are estimated and disclosed.
- Prompt includes serving-size and RAG guidance.
- Input-quality clarification still avoids provider calls.
- UI rendering includes importer servings and citations.
- Live-eval checks catch weak recipe-creator outputs, including one-step cheesecake and carbonara with heavy cream.
- OpenAI strict schema tests include the new servings field.

## Validation Results

- `& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py`: passed, 17 cases.
- `& .\.venv\Scripts\python.exe -m pytest ai-api\tests`: known Windows temp ACL issue; 122 tests collected, 82 passed, 40 setup errors rooted in `PermissionError: [WinError 5] Access is denied` on the per-user pytest temp directory.
- `& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh`: passed; includes 122 AI API tests passed and 17 offline eval cases passed.
- `git diff --check`: passed.
- `docker compose config --quiet`: passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1`: passed; offline evals and endpoint smoke checks passed.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1`: skipped cleanly because `OPENAI_ENABLE_LIVE_TESTS=true` was not set.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1`: skipped cleanly because live eval opt-in settings were not present.

## Live OpenAI

No live OpenAI calls were run for this task.

## Recommended Next Task

Resume `0029B`: Manual End-User Recipe Entry Acceptance, using the improved importer in mock mode first and optional live OpenAI mode only with explicit operator opt-in.

## Artifact Safety

No generated artifacts, raw response JSON, `.tmp-ai-demo/`, API keys, private env files, raw datasets, screenshots, logs, or credentials were committed.
