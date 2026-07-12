# 0030O Importer Action-Oriented Context Phrase Scorer Refinement

## Goal

Fix the remaining live importer eval false failure where a realistic recipe instruction starts with a short setup/context phrase before the imperative verb.

This is a focused follow-up to:

- `0030L Live Importer Eval Output Cap And Safe Diagnostics`
- `0030M Live Importer Eval Scoring Calibration`
- `0030N Importer Instruction Conciseness Scorer Refinement`

Do **not** change provider behavior, model routing, prompts sent to the provider, live opt-in behavior, public routes, storage, auth, billing, GLM, or secondary-provider behavior.

## Observed Failure After 0030N

A live OpenAI demo eval run still failed only on importer instruction scoring:

```text
Overall passed: False
Workflows passed: 5/6
Threshold warnings: 0
Threshold failures: 0
importer: instructions should be concise and action-oriented - max_words=25 average_words=17.3 compact_steps=7/7 action_oriented=6/7
```

The importer output is otherwise good:

```text
Title: Lemon Herb White Beans with Toast
Citations: 3
Retrieved examples: 3
Warnings: none
Tokens: 1397, under importer token thresholds
```

Generated instructions:

```text
1. Warm the white beans in a saucepan over medium heat, with a splash of water if needed to loosen them (about 3–5 minutes).
2. In a small bowl, mix olive oil with minced garlic, then stir into the warm beans. Cook 1–2 minutes, just until fragrant.
3. Stir in lemon juice and lemon zest. Season with salt and black pepper to taste.
4. Simmer very briefly (about 1 minute) until the beans are hot and glossy; if the mixture seems thick, add a tablespoon or two of water.
5. Turn off the heat and fold in the chopped parsley.
6. Toast the bread until crisp.
7. Spoon the warm lemon-herb beans over toast. Drizzle with a little extra olive oil if you like and serve right away.
```

The likely false failure is step 2:

```text
In a small bowl, mix olive oil with minced garlic, then stir into the warm beans. Cook 1–2 minutes, just until fragrant.
```

This is action-oriented because the first short context phrase is followed by the imperative verb `mix`, plus `stir` and `cook`. The current scorer appears to require the first word of the full segment to be an action verb, so it treats `In` as non-action.

## Primary Objective

Refine importer instruction action-oriented scoring so instructions with short leading context/prepositional phrases pass when they contain an early valid imperative cooking verb, while genuinely non-action instructions still fail.

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

## Expected Updated Files

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
outbox/0030O-importer-action-oriented-context-phrase-scorer-refinement-results.md
```

## Required Work

### 1. Refine action-oriented instruction detection

Update `evals/ai_cookbook/expected_checks.py` so `_instruction_is_action_oriented(...)` accepts realistic instructions with a short leading context phrase before the action verb.

Examples that should pass:

```text
In a small bowl, mix olive oil with minced garlic, then stir into the warm beans.
In a medium saucepan, warm the beans over medium heat.
On a baking sheet, arrange the bread and toast until crisp.
With a spoon, mash a few beans against the side of the pan.
If the mixture seems thick, add a tablespoon or two of water.
After the beans are warm, stir in lemon juice and parsley.
```

Recommended scoring behavior:

- Continue accepting instructions that start directly with known action verbs.
- Continue accepting colon-labeled steps from `0030M` and `0030N`.
- Also accept a valid action verb when it appears early in the instruction after a short setup phrase.
- Suggested bound: first valid action verb must appear within the first 6 to 8 normalized words, or after one short comma-delimited/prepositional setup phrase.
- Do not accept instructions just because they contain any action verb anywhere late in a long paragraph.
- Do not make labels or context phrases a loophole for rambling instructions.

### 2. Keep conciseness scoring from 0030N intact

Preserve the aggregate conciseness policy from `0030N`:

```text
- any individual step above 45 words fails;
- average instruction length must stay at or below 28 words;
- most steps must remain compact;
- empty steps and placeholder steps still fail.
```

Do not revert back to the old all-steps <= 24 words rule.

### 3. Improve safe failure detail if useful

The existing failure detail already reports:

```text
max_words=25 average_words=17.3 compact_steps=7/7 action_oriented=6/7
```

If straightforward, add bounded detail showing which step indexes failed action orientation, for example:

```text
action_failed_steps=2
```

Do not include raw prompts, provider responses, keys, `.env` contents, or local absolute paths.

### 4. Add focused tests

Add or update tests so the observed live instruction set passes.

Tests should prove:

- the exact observed 7-step instruction set passes importer scoring;
- `In a small bowl, mix...` passes because `mix` is an early valid action verb;
- context phrases such as `In a medium saucepan`, `On a baking sheet`, `With a spoon`, `If the mixture seems thick`, and `After the beans are warm` pass when followed by an early action verb;
- direct action-verb starts from 0030M/0030N still pass;
- colon-labeled steps still pass;
- non-action instructions still fail;
- instructions where the first action verb appears only very late in a rambling paragraph still fail;
- empty and placeholder instructions still fail;
- token threshold behavior from `0030M` remains unchanged;
- safe diagnostics from `0030L` remain intact.

Use deterministic fixtures and mocks. Do not require a live OpenAI call in pytest.

### 5. Update docs as needed

Update docs/runbook/status/backlog to explain that importer instruction scoring allows short recipe setup phrases before an imperative verb, while still rejecting non-action and rambling instructions.

### 6. Add outbox report

Create:

```text
outbox/0030O-importer-action-oriented-context-phrase-scorer-refinement-results.md
```

Include:

- summary of the false failure found;
- action-oriented scorer refinement made;
- context/prepositional phrase handling;
- tests added/updated;
- validation results;
- explicit non-goals;
- artifact safety confirmation;
- recommendation on whether `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.

## Acceptance Criteria

- The observed 7-step live importer instruction set passes importer quality scoring.
- A short context phrase before an early action verb passes.
- Non-action instructions still fail.
- Rambling instructions with only late action verbs still fail.
- Conciseness scoring from `0030N` remains intact.
- Importer token thresholds from `0030M` remain intact.
- Safe diagnostics from `0030L` remain intact.
- Normal validation remains offline/mock-only.
- Live evals remain explicit opt-in.
- No secrets, raw provider prompts, raw provider responses, local absolute paths, `.env`, or generated live artifacts are committed.
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
git add evals ai-api docs README.md outbox/0030O-importer-action-oriented-context-phrase-scorer-refinement-results.md

git commit -m "mailbox: complete task 0030O importer action oriented context phrase scorer refinement"

git pull --rebase origin main
git push origin main
```
