# 0030N Importer Instruction Conciseness Scorer Refinement

## Goal

Fix the remaining brittle importer live-eval scorer rule that requires every importer instruction to be very short. The current live importer output is usable and action-oriented, but the eval still fails because the conciseness check is too strict for realistic recipe instructions that include a short label plus a useful clause.

This is a focused follow-up to:

- `0030L Live Importer Eval Output Cap And Safe Diagnostics`
- `0030M Live Importer Eval Scoring Calibration`

Do **not** change provider behavior, model routing, prompt provider selection, live opt-in behavior, public routes, storage, auth, billing, GLM, or secondary-provider behavior.

## Observed Behavior

After `0030M`, the live OpenAI demo eval still reports:

```text
Overall passed: False
Workflows passed: 5/6
Threshold failures: 0
```

The only failed check is:

```text
importer: instructions should be concise and action-oriented - failed
```

The importer response is otherwise good:

```text
Title: Lemon Herb White Beans with Toast
Citations: 3
Retrieved examples: 3
Warnings: none
Usage: 1447 total tokens, under the importer threshold
```

The generated instructions are usable and action-oriented:

```text
1. Warm the beans: In a medium saucepan, add olive oil and heat over medium-low. Add the minced garlic and cook 30–60 seconds until fragrant (don’t brown).
2. Simmer gently: Add the drained/rinsed beans. Stir and warm through 3–5 minutes, mashing a few beans against the side of the pan for a creamy texture.
3. Brighten with lemon: Stir in lemon juice (and zest if using). Season with salt, black pepper, and red pepper flakes (if using). Simmer 1 more minute.
4. Finish: Turn off the heat and fold in the chopped parsley.
5. Toast the bread: Toast until crisp and golden.
6. Serve: Spoon warm lemon herb white beans over toast. Drizzle with a little extra olive oil and serve immediately.
```

The issue is not provider failure, token threshold, missing citations, or bad recipe quality. It is a scoring rule problem.

## Current Scorer Problem

`evals/ai_cookbook/expected_checks.py` currently evaluates importer instruction quality roughly as:

```python
bool(instructions)
and all(_instruction_word_count(instruction) <= IMPORTER_MAX_INSTRUCTION_WORDS for instruction in instructions)
and all(_instruction_is_action_oriented(instruction) for instruction in instructions)
```

`IMPORTER_MAX_INSTRUCTION_WORDS` is currently `24`.

`0030M` added broader action verbs and colon-label support, which fixed the action-verb side. However, `_instruction_word_count` still effectively punishes realistic labeled instructions because it counts too much text and requires every step to fit a short hard cap.

For example, this is a good recipe instruction but may exceed 24 words:

```text
Warm the beans: In a medium saucepan, add olive oil and heat over medium-low. Add the minced garlic and cook 30–60 seconds until fragrant.
```

## Primary Objective

Replace the brittle `all steps <= 24 words` rule with a more realistic importer instruction conciseness scorer.

The scorer should still require action-oriented, reasonably concise recipe steps, but it should not fail otherwise good recipe output just because one or two useful instructions are 25–40 words.

## Non-Negotiable Boundaries

Do not add:

- GLM provider integration;
- secondary-provider routing;
- new provider selection behavior;
- production auth;
- paid access;
- payment integration;
- ad/sponsor runtime code;
- public route exposure;
- Cloudflare changes;
- DNS changes;
- production storage;
- Redis/Postgres/SQLite persistence;
- live OpenAI calls during normal validation;
- committed `.env` files;
- committed API keys or key fragments;
- raw provider prompts or raw provider responses in committed docs/outbox/tests;
- local absolute paths in public docs examples;
- screenshots, logs, or generated live artifacts.

Live checks must remain explicit opt-in.

## Suggested Files

Likely updated files:

```text
evals/ai_cookbook/expected_checks.py
ai-api/tests/test_live_openai_demo_evals.py
docs/live-openai-demo-evals.md
docs/ai-live-demo-runbook.md
docs/ai-feature-status.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
README.md if relevant
```

Required new file:

```text
outbox/0030N-importer-instruction-conciseness-scorer-refinement-results.md
```

## Required Work

### 1. Refine importer instruction conciseness scoring

Update `evals/ai_cookbook/expected_checks.py` so the importer instruction quality check is no longer a brittle `all steps <= 24 words` rule.

Recommended approach:

- Keep the action-oriented requirement strict: every non-empty step should still have action-oriented language.
- Replace the single hard per-step word cap with a combined conciseness policy such as:
  - hard fail any individual step above a high cap, for example `45` words;
  - require average instruction length to stay reasonable, for example `<= 28` words;
  - require most steps to be compact, for example at least 70% or at least 4 of 6 steps under `32` words;
  - keep empty or placeholder instructions failing.

The exact numbers may be adjusted if tests justify them, but the observed valid live output above should pass, and truly rambling steps should still fail.

### 2. Treat colon-labeled steps fairly

For colon-labeled steps, evaluate conciseness in a way that does not over-penalize the label plus body.

Examples that should pass when otherwise reasonable:

```text
Warm the beans: In a medium saucepan, add olive oil and heat over medium-low. Add the garlic and cook until fragrant.
Brighten with lemon: Stir in lemon juice and zest. Season to taste and simmer briefly.
Serve: Spoon warm beans over toast and drizzle with olive oil.
```

Implementation options:

- Count full instruction words for hard cap only, but use the post-colon body for average/compactness checks;
- or count the shorter meaningful segment when a colon label is present;
- or implement a helper that returns a structured conciseness result with `full_words`, `label_words`, `body_words`, and `passed`.

Do not make labels a loophole for huge rambling instructions. A very long full instruction should still fail.

### 3. Improve check details

The failure detail for `instructions should be concise and action-oriented` should become more useful.

Instead of only `failed`, include safe details such as:

```text
max_words=38 average_words=24 compact_steps=5/6 action_oriented=6/6
```

Do not include raw prompts, provider responses, keys, `.env` contents, or local absolute paths.

### 4. Add focused tests

Update `ai-api/tests/test_live_openai_demo_evals.py` or a related test file.

Tests should prove:

- the observed live output shape from this task passes;
- labeled steps with realistic useful clauses pass;
- one or two steps in the 25–40 word range can pass if the overall instruction set remains compact;
- a single extremely long step still fails;
- many rambling steps still fail;
- non-action instructions still fail;
- empty instructions still fail;
- generic placeholder instructions still fail;
- action verb calibration from `0030M` still works, including `saute` and `sauté`;
- token threshold behavior from `0030M` remains unchanged;
- safe diagnostics from `0030L` remain intact.

Use mock/fake payloads only. Do not require a real OpenAI call in pytest.

### 5. Preserve existing threshold behavior

Do not undo `0030M` token-threshold changes.

Keep:

```text
IMPORTER_TOKENS_WARN=1500
IMPORTER_TOKENS_FAIL=1800
WORKFLOW_TOKENS_FAIL=1200 for non-importer workflows
```

The current live run has `1447` total importer tokens and should not fail token thresholds.

### 6. Update docs

Update docs as needed to explain:

- importer instruction scoring checks action orientation and overall conciseness;
- realistic labeled recipe steps are allowed;
- one useful instruction can be longer than a tweet-sized step, but rambling output still fails;
- importer token thresholds remain workflow-specific;
- normal validation remains offline/mock;
- live evals remain explicit opt-in through local ignored `.env` and wrapper `-EnvFile`.

### 7. Add outbox report

Create:

```text
outbox/0030N-importer-instruction-conciseness-scorer-refinement-results.md
```

Include:

- summary of the remaining brittle scorer issue;
- conciseness scoring changes;
- colon-label handling changes;
- failure-detail improvements;
- tests added/updated;
- docs updated;
- validation results;
- optional live manual result if run;
- explicit non-goals;
- artifact safety confirmation;
- recommendation on whether `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.

## Acceptance Criteria

- The observed live importer instruction set in this task passes.
- Good labeled recipe instructions pass.
- Action-oriented checks remain meaningful.
- Long/rambling/non-action/generic instructions still fail.
- Failure details are more informative than plain `failed`.
- Importer token threshold behavior from `0030M` is preserved.
- Safe diagnostics from `0030L` are preserved.
- Normal validation remains offline/mock-only.
- Live evals remain explicit opt-in.
- No secrets, raw provider prompts, raw provider responses, generated live artifacts, or local absolute paths are committed.
- No GLM, secondary-provider routing, public route exposure, payment/ad/sponsor runtime, production auth, or storage changes are added.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe -m pytest ai-api\tests\test_live_openai_demo_evals.py -q
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-ai-env-file-loader.ps1
& .\.venv\Scripts\python.exe scripts\e2e-ai-29-30-regression.py
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
git diff --check
docker compose config --quiet
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-mock.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\demo-ai-live-smoke.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1
```

Optional manual live validation, only when local ignored `.env` explicitly enables live mode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run-openai-demo-evals.ps1 -EnvFile .\.env
```

Expected live result after this task, if the provider output is comparable to the observed draft:

```text
Overall passed: True
Workflows passed: 6/6
```

If direct Windows pytest hits the known local `pytest-of-scott` temp ACL issue for unrelated fixture tests, document it and rely on Git Bash validation if it passes.

Before committing, confirm:

- no `.env` file is staged;
- no real key is staged;
- no `sk-proj-`, `sk_live_`, or `sk_test_` string is staged;
- no raw provider response is staged;
- no raw provider prompt is staged;
- no `.tmp-ai-demo` artifacts are staged;
- no logs or screenshots are staged;
- no local absolute paths are added to public docs examples;
- no GLM provider code is added;
- no secondary-provider routing is added.

## Commit

```bash
git add evals ai-api docs README.md outbox/0030N-importer-instruction-conciseness-scorer-refinement-results.md

git commit -m "mailbox: complete task 0030N importer instruction conciseness scorer refinement"

git pull --rebase origin main
git push origin main
```
