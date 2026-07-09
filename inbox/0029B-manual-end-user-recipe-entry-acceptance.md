# Task 0029B: Manual End-User Recipe Entry Acceptance

## Goal

After `0029A` is complete, run a manual end-user acceptance pass against the AI recipe importer using realistic recipe entries typed by the operator in the application UI.

This task validates whether the model can take normal, imperfect end-user recipe notes and construct reasonably good structured recipe drafts without hallucinating, over-asking questions, or failing basic input-quality checks.

## Dependency

Do this after:

```text
0029A: Production Access, Metering, And Time-Limited AI Sessions Architecture
```

If `0029A` changes access, routing, launch instructions, or demo/user entry flow, use the post-`0029A` manual run path.

## Manual Test Recipes

Use these four operator-provided recipe topics:

1. Omelet
2. Carbonara pasta
   - User originally wrote `carbonare pasta`; treat that as the common recipe `carbonara pasta` unless the user intentionally enters the typo during testing.
3. Cheesecake
4. Chicken and rice casserole

## Test Style

Run this as an end user, not as a developer-only API test.

Use the UI or end-user entry surface that exists after `0029A`.

The operator should manually enter rough recipe notes for each recipe. Do not require perfect recipe formatting.

Example input styles to test:

### Omelet

Use short rough notes such as:

```text
omelet with eggs cheese maybe onions cooked in butter fold it over
```

Expected behavior:

- Should produce a reasonable omelet draft.
- Should infer basic omelet structure without inventing excessive ingredients.
- Should include warnings/notes for missing quantities if appropriate.
- Should not ask clarification unless the input is too vague.

### Carbonara Pasta

Use rough notes such as:

```text
carbonara pasta spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat
```

Expected behavior:

- Should produce a reasonable carbonara-style pasta draft.
- Should preserve core inputs: spaghetti/pasta, eggs, parmesan, pancetta, black pepper, pasta water.
- Should avoid inventing heavy cream as a required ingredient unless entered by the user.
- Should mention uncertainty for missing quantities/timing.

### Cheesecake

Use rough notes such as:

```text
cheesecake cream cheese sugar eggs vanilla graham cracker crust bake and chill
```

Expected behavior:

- Should produce a reasonable cheesecake draft.
- Should preserve cream cheese, sugar, eggs, vanilla, graham cracker crust, bake/chill concept.
- Should not invent unusual flavorings unless clearly framed as optional.
- Should note missing amounts, pan size, baking time, and chilling time if not provided.

### Chicken And Rice Casserole

Use rough notes such as:

```text
chicken and rice casserole chicken rice cream soup cheese bake until hot
```

Expected behavior:

- Should produce a reasonable casserole draft.
- Should preserve chicken, rice, cream soup, cheese, baked casserole structure.
- Should avoid unsafe assumptions around raw chicken if the input does not specify cooked chicken.
- Should include a food-safety style note when chicken doneness is unclear, without overcomplicating the recipe.

## What To Observe

For each recipe, record:

- input text entered;
- input-quality status;
- whether the model generated a draft, asked one clarification question, or rejected the input;
- recipe title;
- description quality;
- ingredient preservation;
- instruction quality;
- notes/warnings quality;
- whether it invented unrelated ingredients;
- whether it handled missing quantities/timing honestly;
- whether the result was useful enough for a demo;
- latency if visible;
- estimated cost if available;
- raw response file path only if generated locally, but do not commit raw artifacts.

## Acceptance Criteria

Each recipe should pass if:

- the app accepts a realistic rough note;
- the app returns either a useful structured recipe or one bounded clarification question;
- the app asks no more than one clarification question;
- the recipe preserves at least two to three core user-provided ingredients or cooking ideas;
- the recipe does not invent unrelated major ingredients;
- missing quantities, timing, pan size, or method details are noted instead of fabricated with false confidence;
- instructions are concise and action-oriented;
- warnings are helpful but not noisy;
- no stack trace, raw provider error, secret, or private path is shown in the user-facing UI;
- the output is good enough to explain in a portfolio demo.

A recipe should fail if:

- the app hallucinates the main recipe into a different dish;
- the app invents unrelated major ingredients;
- the app fabricates precise quantities/times without noting uncertainty;
- the app asks multiple questions or enters a chat loop;
- the app rejects a clearly usable rough note;
- the app calls the provider for deterministic rejected junk input when it should not;
- the UI displays stack traces, raw provider errors, secrets, or private path details.

## Suggested Manual Matrix

Create a manual acceptance table like:

| Recipe | Input Quality | Result | Core Ingredients Preserved | Clarification Count | Warnings Useful | Demo Ready | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| Omelet |  |  |  |  |  |  |  |
| Carbonara pasta |  |  |  |  |  |  |  |
| Cheesecake |  |  |  |  |  |  |  |
| Chicken and rice casserole |  |  |  |  |  |  |  |

## Optional Bad-Input Spot Checks

If time allows, also test a few bad inputs to verify `0028A` behavior still works after `0029A`:

```text
!!!!!!
123456
make food
recipe
```

Expected behavior:

- symbol/number junk should be rejected before provider calls;
- vague recoverable inputs should ask one clarification question;
- no open-ended chat loop should appear.

## Required Documentation

Create a manual test report after execution:

```text
docs/manual-recipe-entry-acceptance-2026-07.md
```

Create an outbox report:

```text
outbox/0029B-manual-end-user-recipe-entry-acceptance-results.md
```

The report should include:

- summary;
- test environment;
- how the app was launched/accessed after `0029A`;
- whether live OpenAI was enabled;
- model used;
- the four recipe inputs;
- acceptance matrix;
- notable good outputs;
- notable weak outputs;
- failures or follow-up tuning needed;
- screenshots only if intentionally captured, but do not commit screenshots unless the repo already has an approved screenshot policy;
- confirmation that raw generated response artifacts, `.tmp-ai-demo/`, secrets, env files, API keys, raw datasets, logs, screenshots, and credentials were not committed.

## Validation

Run normal offline validation after any docs/checklist changes:

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

If direct Windows pytest still fails with the known temp ACL issue, document it and confirm Git Bash validator passes.

## Non-Goals

Do not implement:

- automated browser testing;
- new provider prompts unless a clear failure is found and separately scoped;
- billing implementation;
- new auth implementation;
- production storage changes;
- dataset import changes;
- screenshot automation;
- committed `.tmp-ai-demo/` artifacts;
- committed raw provider response files;
- committed secrets, env files, raw datasets, screenshots, logs, or credentials.

## Recommended Follow-On Tasks

If all four recipes are good:

```text
0029C: Manual Recipe Entry Demo Script And Portfolio Narrative
```

If one or more recipes fail:

```text
0029C: Manual Recipe Entry Tuning From Acceptance Findings
```

## Commit

Commit and push after the manual acceptance report is created:

```bash
git add docs README.md outbox/0029B-manual-end-user-recipe-entry-acceptance-results.md

git commit -m "mailbox: complete task 0029B manual end user recipe entry acceptance"

git push origin main
```

## Done Criteria

- The four manual recipe-entry scenarios are documented.
- The operator can run them as an end user after `0029A`.
- The acceptance matrix records pass/fail and useful notes for each recipe.
- Follow-up tuning is clearly identified only if needed.
- Normal validation remains offline.
- No generated artifacts, raw response JSON, `.tmp-ai-demo/`, screenshots, secrets, env files, raw datasets, logs, or credentials are committed.
