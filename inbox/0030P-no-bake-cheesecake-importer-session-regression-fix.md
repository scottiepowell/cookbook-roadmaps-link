# 0030P No-Bake Cheesecake Importer And Session Regression Fix

## Goal

Fix the Recipe Session Alpha clarification path where the session correctly captures `cooking_method=no-bake`, but the generated draft still contains baked cheesecake instructions.

This is a 0030 baseline bugfix, not part of the 0031 secondary-provider/GLM line. Complete this before treating the recipe-session baseline as stable for future secondary-provider offload comparisons.

## Observed Manual Failure

Manual Recipe Session Alpha test:

1. Start session with vague input:

```text
make dessert
```

2. App correctly returns a clarification question.

3. Answer with:

```text
cheesecake, no-bake, for 4 people
```

4. Response correctly captures requirements:

```text
dish_intent=cheesecake
serving_count=4
cooking_method=no-bake
response_state=rag_refreshed
changed_fields=dish_intent,cooking_method
resolved_questions includes the clarification answer
```

5. But generated draft instructions are baked cheesecake steps:

```text
Preheat the oven and press the graham cracker crust into the pan.
Beat cream cheese, sugar, vanilla, and eggs until smooth.
Pour the filling into the crust and bake until the center is just set.
Cool the cheesecake gradually, then chill until firm before slicing.
```

This violates the clarified no-bake requirement.

## Root Cause

`ai-api/app/importer.py` currently post-processes any draft whose source text contains `cheesecake` into a baked cheesecake instruction template:

```python
elif "cheesecake" in text:
    instructions = _instruction_set(
        [
            "Preheat the oven and press the graham cracker crust into the pan.",
            "Beat cream cheese, sugar, vanilla, and eggs until smooth.",
            "Pour the filling into the crust and bake until the center is just set.",
            "Cool the cheesecake gradually, then chill until firm before slicing.",
        ]
    )
```

That branch triggers for `no-bake cheesecake` because it checks only for `cheesecake` and does not guard against `no-bake`, `no bake`, or similar method constraints.

## Primary Objective

Make the importer improvement layer preserve the clarified cooking method. A no-bake cheesecake request must produce no-bake instructions and must not include baked-only words such as `preheat`, `oven`, or `bake` unless the user explicitly requested a baked cheesecake.

## Non-Negotiable Boundaries

Do not add:

- GLM provider integration;
- secondary-provider routing;
- model fallback behavior;
- provider selection changes;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- production auth;
- durable storage;
- Redis/Postgres/SQLite persistence;
- paid access;
- payment integration;
- ad/sponsor runtime code;
- live OpenAI calls during normal validation;
- live GLM calls;
- committed `.env` files;
- committed provider keys;
- raw provider prompts;
- raw provider responses;
- logs, screenshots, or `.tmp-ai-demo` artifacts.

Normal validation must remain offline/mock-only.

## Required Work

### 1. Fix cheesecake instruction override logic

Update `ai-api/app/importer.py` so cheesecake instruction selection distinguishes no-bake cheesecake from baked cheesecake.

Expected logic:

```text
if cheesecake and no-bake/no bake/chilled/no oven style is requested:
    use no-bake cheesecake instructions
elif cheesecake:
    use baked cheesecake instructions
```

Use a helper if helpful, for example:

```python
def _requests_no_bake(text: str) -> bool:
    ...
```

The helper should recognize common variants such as:

```text
no-bake
no bake
no oven
without baking
do not bake
chilled cheesecake
refrigerator cheesecake
```

Avoid overly broad matching that would incorrectly treat `bake and chill overnight` as no-bake.

### 2. Add no-bake cheesecake instruction template

A no-bake cheesecake instruction set should include no-bake structure, for example:

```text
1. Press the graham cracker crust into the pan and chill while preparing the filling.
2. Beat cream cheese, sugar, and vanilla until smooth.
3. Fold in whipped topping or whipped cream if included, or keep the filling smooth if not specified.
4. Spread the filling into the chilled crust.
5. Cover and chill until firm.
6. Slice and serve cold.
```

Do not include:

```text
preheat
oven
bake
center is just set
```

unless the user explicitly asked for baked cheesecake.

### 3. Preserve baked cheesecake behavior

Existing baked cheesecake requests should still get baked cheesecake instructions when the user asks for baked cheesecake, for example:

```text
classic baked cheesecake for 4 with cream cheese sugar eggs vanilla graham cracker crust bake and chill overnight
```

Expected baked terms may still appear for baked requests:

```text
preheat
oven
bake
center is just set
chill
```

### 4. Add session-level regression coverage

Add or update tests so the exact manual clarification path is covered offline/mock-only:

```text
start: make dessert
message: cheesecake, no-bake, for 4 people
```

Expected assertions:

```text
response_state is rag_refreshed or draft_revised
requirements.dish_intent.value == cheesecake
requirements.cooking_method.value == no-bake
resolved_questions is populated
open_questions is empty
draft exists
draft instructions include chill/refrigerate/serve cold style behavior
draft instructions do not include preheat/oven/bake/center is just set
retrieval query includes no-bake or no bake
```

### 5. Add importer-level regression coverage

Add or update importer tests so direct importer text with no-bake cheesecake produces no-bake instructions:

```text
cheesecake, no-bake, for 4 people
```

Expected:

```text
instructions mention chill/refrigerate/serve cold
instructions do not mention preheat/oven/bake
servings default or parse to 4
warnings remain safe
```

Also keep a baked cheesecake test proving baked cheesecake still uses baked behavior when explicitly requested.

### 6. Dataset-unavailable behavior

The manual failure also showed:

```text
Configured recipe dataset directory does not exist.
Importer dataset RAG examples were unavailable; created the draft from user notes only.
```

Do not treat missing dataset fixtures as a failure for this task. The no-bake/baked distinction must work even when retrieval returns zero examples and the draft is shaped primarily by mock/provider output plus importer improvement logic.

### 7. Docs and backlog

Update docs as needed:

```text
docs/recipe-session-alpha-acceptance-runbook.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
```

Document the new regression case:

```text
make dessert -> cheesecake, no-bake, for 4 people
```

and clarify that no-bake method constraints must be preserved through clarification, retrieval query building, importer draft shaping, and finalize/demo display.

### 8. Outbox report

Create:

```text
outbox/0030P-no-bake-cheesecake-importer-session-regression-fix-results.md
```

Include:

- summary of the manual bug;
- root cause;
- importer fix;
- session regression coverage;
- importer regression coverage;
- docs updated;
- validation results;
- non-goals;
- artifact safety confirmation;
- recommendation on whether 0031A can continue after this baseline fix.

## Acceptance Criteria

- The manual clarification flow no longer produces baked cheesecake steps for `cheesecake, no-bake, for 4 people`.
- Requirements still capture `cooking_method=no-bake`.
- Draft instructions for no-bake cheesecake include chill/refrigerate/serve cold behavior.
- Draft instructions for no-bake cheesecake do not include `preheat`, `oven`, `bake`, or `center is just set`.
- Explicit baked cheesecake requests still produce baked cheesecake behavior.
- Tests cover both session-level and importer-level cases.
- Normal validation remains offline/mock-only.
- No provider/runtime/GLM/secondary-provider changes are introduced.
- No secrets, raw prompts, raw provider responses, local artifacts, screenshots, logs, or `.env` files are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_recipe_session_api.py -q
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_import_recipe.py -q
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

The live wrappers should skip cleanly unless local env explicitly opts into live mode.

Manual UI/API check after implementation:

```text
start: make dessert
message: cheesecake, no-bake, for 4 people
```

Expected manual result:

```text
requirements.cooking_method.value = no-bake
draft instructions mention chill/refrigerate/serve cold
draft instructions do not mention preheat/oven/bake
```

## Commit

```bash
git add ai-api docs evals outbox/0030P-no-bake-cheesecake-importer-session-regression-fix-results.md

git commit -m "mailbox: complete task 0030P no bake cheesecake importer session regression fix"

git pull --rebase origin main
git push origin main
```