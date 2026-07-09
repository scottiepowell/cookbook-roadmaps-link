# Task 0029B-2: RAG-Informed Recipe Creator Importer

## Goal

Improve the recipe importer so it behaves like a practical recipe creator, not just a thin extractor.

Manual end-user testing showed that the importer preserved ingredients, but often produced weak or incomplete steps and no usable quantities. Add a RAG-informed creation path that uses similar recipes from the local dataset as structure guidance while preserving the user's input and avoiding unsupported hallucinations.

## Background

During manual `0029B` recipe-entry testing, live OpenAI mode produced useful titles/ingredients, but the steps were often too weak:

- Omelet: steps were weak; step 1 should scramble/beat the eggs before cooking.
- Carbonara pasta: acceptable.
- Cheesecake: only one very weak step.
- Chicken and rice casserole: weak steps.

Observed examples:

- Omelet produced 3 steps, but started with `Cook the omelet in butter` before properly preparing eggs.
- Cheesecake produced only one instruction: `Bake and chill the cheesecake...`.
- Chicken and rice casserole produced only 2 steps: combine ingredients and bake until hot.

The user also requested:

- default serving size should be 4 people;
- quantities should be generated when the user omits them;
- the importer should use RAG from the recipe dataset to shape recipe structure;
- the feature is closer to a recipe creator than a simple importer.

## Current State

`ai-api/app/importer.py` currently builds the provider prompt from only:

```text
Recipe text:
<user input>
```

and validates the provider response as `RecipeImportDraft`.

The importer does not currently retrieve dataset examples before the provider call. It returns no dataset citations/provenance.

Dataset search/RAG exists separately in:

```text
ai-api/app/dataset_retrieval.py
ai-api/app/dataset_rag.py
```

but importer does not use that retrieval path yet.

## Product Decision

Keep the existing endpoint name for compatibility:

```text
POST /ai/import-recipe
```

But update the behavior and docs to describe it as:

```text
Import or create a structured recipe draft from rough user notes.
```

The endpoint should support recipe creation from rough notes while remaining safe:

- user-provided ingredients and dish intent remain primary;
- dataset examples are used only as structural guidance;
- retrieved examples should not override the user's core ingredients;
- the model should not copy full dataset recipes;
- citations/provenance should show which dataset examples informed the draft;
- default servings should be 4 unless the user states otherwise.

## Required Behavior

### 1. Add default servings

Add a serving-size concept to recipe import/creation.

Recommended schema change:

```python
class RecipeImportDraft(BaseModel):
    title: str
    description: str | None = None
    servings: int | None = Field(default=4, ge=1, le=24)
    ingredients: list[RecipeIngredientDraft]
    instructions: list[RecipeInstructionDraft]
    tags: list[str]
    source: str | None = None
    notes: str | None = None
```

Behavior:

- if user provides servings, use that serving size;
- if not, default to 4;
- ingredient quantities should be generated for that serving size when reasonable;
- notes should state that quantities are estimated for 4 servings when not provided by the user.

### 2. Add RAG retrieval before provider call

Before calling the provider in the importer path:

1. classify input quality;
2. reject/clarify bad input before provider calls as today;
3. derive a retrieval query from the user's recipe text;
4. search the local dataset index for similar recipes;
5. pass a small, bounded set of retrieved recipe examples into the importer prompt;
6. call the provider only after input-quality and retrieval steps.

Recommended defaults:

```text
importer_rag_enabled = true when RECIPE_DATASET_DIR is configured and available
importer_rag_limit = 3
importer_rag_dataset_limit = existing recipe dataset index limit
```

Do not require RAG for the endpoint to work. If dataset retrieval is unavailable, fall back to provider-only creation with a warning.

### 3. Prompt behavior

Update the importer system/user prompt to require:

- create a practical recipe draft for the requested dish;
- default to 4 servings unless the user states a different serving size;
- provide plausible ingredient quantities for 4 servings when the user omits quantities;
- use retrieved dataset examples only for structure, proportion hints, and step completeness;
- preserve user-provided core ingredients and cooking intent;
- do not add unrelated major ingredients;
- do not copy a retrieved recipe verbatim;
- include 4 to 8 concise, action-oriented steps for normal recipes;
- combine trivial steps when appropriate but avoid one-step recipes for multi-step dishes;
- include food-safety guidance when needed, especially for chicken/raw meat;
- place assumptions in notes.

Recipe-specific quality targets from manual findings:

- Omelet should include beating/scrambling eggs before cooking and folding.
- Carbonara should avoid requiring heavy cream unless the user supplied it.
- Cheesecake should include crust/filling/bake/cool/chill style steps, not one generic step.
- Chicken and rice casserole should include preheat/prepare/combine/bake/doneness or safe chicken handling guidance.

### 4. Add importer retrieval metadata and citations

Extend `RecipeImportResponse` to include retrieval/citation metadata without breaking existing clients.

Suggested fields:

```python
class RecipeImportRetrievalMetadata(BaseModel):
    query: str
    retrieved_count: int
    limit: int
    dataset_limit: int
    matched_result_ids: list[str]
    index: DatasetIndexSummaryResponse | None = None

class RecipeImportCitation(BaseModel):
    id: str
    source_id: str
    title: str
    snippet: str
    matched_fields: list[str]
    provenance: DatasetSearchProvenance
```

Add to response:

```python
retrieval: RecipeImportRetrievalMetadata | None = None
citations: list[RecipeImportCitation] = Field(default_factory=list)
```

The demo UI should show citations/provenance for importer when RAG is used.

### 5. Improve output quality checks

Update importer eval/test expectations so recipe-creator quality is measured.

Add checks for:

- `servings` defaults to 4 when not provided;
- ingredients include at least some non-null quantities for normal recipe-creation inputs;
- notes mention estimated/default quantities when user omitted quantities;
- instructions have enough step depth for multi-step dishes;
- instructions include expected preparation actions;
- retrieved citations are present when dataset RAG is available;
- no heavy cream required for carbonara unless user input includes it;
- chicken/casserole output includes safety/doneness guidance when chicken is ambiguous;
- cheesecake output has more than one step and covers bake/chill;
- provider fallback without dataset still works with warning.

Keep existing checks for:

- no unrelated foods;
- no generic placeholders;
- structured ingredient preservation;
- concise action-oriented instructions;
- input-quality provider-call avoidance.

### 6. Dataset size and performance

The user expects the importer to be informed by the available recipe dataset, described informally as about 14K recipes.

Implementation should use the existing local dataset/indexing path and existing configured limits. Do not commit raw dataset files.

If the current `DatasetSearchRequest.dataset_limit` max of 5000 blocks practical local use, propose or implement a safe configuration update, but keep performance bounded.

Potential safe approach:

- keep default test/demo dataset limit small for generated fixtures;
- allow local operator override for larger dataset limits through env/config;
- do not load unlimited records by default in CI;
- document expected performance tradeoffs.

### 7. UI updates

Update the demo UI importer panel so it can display:

- servings;
- generated quantities;
- stronger multi-step instructions;
- importer citations/provenance when RAG was used;
- warnings/notes that quantities are estimated for 4 servings.

Do not expose private local file paths in the UI.

### 8. Documentation

Update:

```text
docs/manual-recipe-entry-acceptance-2026-07.md if it exists
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
README.md
outbox/0029B-2-rag-informed-recipe-creator-importer-results.md
```

Docs should explain:

- importer is now import/create;
- RAG is used to shape recipe structure when dataset is available;
- default servings are 4;
- quantities can be estimated and must be disclosed;
- dataset examples are guidance, not copy/paste source recipes;
- no raw dataset is committed;
- normal validation remains offline.

## Manual Findings To Preserve

Use these exact operator observations in the outbox/manual report:

```text
Results from omelet with cheese: steps are pretty weak; step 1 should be to scramble the eggs.
Results from carbonara recipe were acceptable.
Results from cheesecake: the steps were just one, very weak.
Results from chicken and rice casserole: weak steps.
```

Also preserve that live OpenAI was used:

```text
provider=openai
model=gpt-5.4-nano
```

## Tests

Add offline tests only. Do not call live OpenAI during normal validation.

Tests should cover:

- importer RAG retrieval is called when dataset is available;
- importer falls back when dataset is unavailable;
- response includes retrieval metadata and citations when RAG is used;
- default servings is 4;
- prompt includes serving-size and RAG guidance;
- prompt includes retrieved examples but stays bounded;
- mock provider path still works;
- input-quality rejected/clarification paths still avoid provider calls;
- UI rendering handles importer citations and servings;
- eval checks catch weak one-step cheesecake/casserole outputs;
- eval checks pass improved recipe-creator outputs.

If testing PowerShell script changes from `0029B-1`, keep those tests separate unless this task needs to update launch docs.

## Validation

Run normal validation:

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

The live smoke and live eval wrappers should skip cleanly unless live opt-in settings are present.

Direct Windows pytest may hit the known temp ACL issue; if so, document it and confirm Git Bash validator passes.

## Optional Manual Live Confirmation

After implementation, the operator can rerun the manual recipe-entry cases in live OpenAI mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-ai-demo-local.ps1 -Provider openai -EnableLiveTests
```

Then enter:

```text
omelet with eggs cheese maybe onions cooked in butter fold it over
carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat
cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill
chicken and rice casserole chicken rice cream soup cheese bake until hot
```

Expected improvements:

- quantities appear for 4 servings;
- steps are deeper and more realistic;
- importer citations appear when dataset RAG is available;
- carbonara does not require heavy cream;
- cheesecake has multiple clear steps;
- chicken casserole includes safer doneness/bake guidance.

Do not require live OpenAI for normal task completion unless the operator explicitly chooses to run it.

## Non-Goals

Do not implement:

- production auth;
- paid access;
- invite sessions;
- database migrations;
- public route exposure;
- Cloudflare route changes;
- raw dataset commits;
- vector DB/Qdrant/Postgres unless separately scoped;
- long-term recipe write-back into Vanilla Cookbook DB;
- screenshot automation;
- committed `.tmp-ai-demo/` artifacts;
- committed raw provider response JSON;
- committed API keys, env files, raw datasets, screenshots, logs, or credentials.

## Outbox Report

Create:

```text
outbox/0029B-2-rag-informed-recipe-creator-importer-results.md
```

Include:

- Summary
- Manual findings/root cause
- Current importer behavior before change
- RAG retrieval design
- Serving-size behavior
- Schema changes
- Prompt changes
- UI changes
- Tests added
- Validation results
- Whether live OpenAI was run or skipped
- Recommended next task
- Artifact safety confirmation

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0029B-2-rag-informed-recipe-creator-importer-results.md

git commit -m "mailbox: complete task 0029B-2 rag informed recipe creator importer"

git push origin main
```

## Done Criteria

- Importer can use retrieved dataset examples to inform recipe creation when dataset is available.
- Importer still works without dataset retrieval and returns a useful warning/fallback.
- Default servings is 4 when user does not specify servings.
- Generated ingredient quantities are included where reasonable and disclosed as estimated when not user-provided.
- Instructions are stronger for omelet, cheesecake, and chicken/rice casserole style inputs.
- Importer response includes retrieval metadata and citations when RAG is used.
- Demo UI displays servings and importer citations/provenance.
- Existing input-quality guardrails remain intact.
- Normal validation remains offline.
- No generated artifacts, raw response JSON, `.tmp-ai-demo/`, secrets, env files, raw datasets, screenshots, logs, or credentials are committed.
