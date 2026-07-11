# 0030M Live Importer Eval Scoring Calibration

## Goal

Calibrate the live OpenAI importer eval scoring so good structured recipe drafts pass while the eval still catches low-quality, rambling, generic, unsupported, or unsafe importer outputs.

This is a follow-up to `0030L Live Importer Eval Output Cap And Safe Diagnostics`.

`0030L` fixed the original live importer provider failure by giving the importer workflow its own bounded live output cap and by adding safe diagnostics. After that fix, the importer live call produced a usable structured draft, but the live eval still failed because the scorer is too rigid for valid real-world recipe steps and because the importer token threshold is still using a workflow-wide limit that is too low for structured importer JSON with retrieval metadata.

## Observed Behavior

A live run after `0030L` produced a good importer draft with:

```text
Title: Lemon Herb White Beans with Toast
Ingredients: white beans, olive oil, garlic, lemon juice, lemon zest, parsley, salt, pepper, toast
Instruction count: 6
Citations: 3
Retrieved examples: 3
Warnings: none
Usage: 830 input tokens, 598 output tokens, 1428 total tokens
```

Example instruction starts:

```text
Warm the beans
Sauté the garlic
Brighten with lemon
Finish with herbs
Prepare the toast
Serve
```

The draft looked usable and grounded, but live eval failed with:

```text
importer: instructions should be concise and action-oriented - failed
importer: workflow token usage below failure threshold - 1428 > 1200
```

The issue is likely scorer calibration:

- the action-verb allowlist does not include valid imperative recipe verbs such as `sauté`, `saute`, `prepare`, `brighten`, `season`, `drizzle`, `mash`, `fold`, or `adjust`;
- the scorer treats step labels such as `Brighten with lemon: Stir in lemon juice...` as if the label must be the action verb;
- the token threshold is global workflow thresholding, while importer is a structured JSON workflow with citations/retrieval and naturally uses more tokens than short answer workflows.

## Primary Objective

Update the live importer eval scoring so:

1. valid concise recipe instructions like the observed live output pass;
2. bad/rambling/generic instructions still fail;
3. importer token thresholds are workflow-specific and realistic;
4. short-answer workflows remain strict;
5. normal validation remains offline/mock-only;
6. no new provider behavior, GLM behavior, route exposure, storage, or production auth is added.

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
outbox/0030M-live-importer-eval-scoring-calibration-results.md
```

## Required Work

### 1. Calibrate importer instruction quality scoring

Update the importer instruction quality check in `evals/ai_cookbook/expected_checks.py`.

Current behavior is too strict because it requires every instruction to:

```text
- be 24 words or fewer;
- start with a word from a narrow ACTION_VERBS allowlist.
```

Improve this without making the eval meaningless.

Acceptable approaches:

- expand `ACTION_VERBS` with common recipe imperatives:

```text
sauté
saute
prepare
brighten
season
drizzle
mash
fold
adjust
turn
sprinkle
remove
cover
rest
garnish
```

- normalize accented verbs so `sauté` and `saute` are both accepted;
- support short step labels before a colon, for example:

```text
Brighten with lemon: Stir in lemon juice and zest.
```

The scorer may treat either the label verb or the post-colon imperative as action-oriented if the instruction remains concise.

Keep meaningful failure behavior:

- empty instructions fail;
- generic placeholder instructions fail;
- extremely long/rambling steps fail;
- instructions with no action-oriented language fail;
- unrelated food hallucinations still fail;
- safety-specific checks such as chicken doneness remain intact.

### 2. Recalibrate importer token thresholds separately from other workflows

The current threshold behavior uses a single `WORKFLOW_TOKENS_FAIL` of `1200` for every workflow.

Add importer-specific threshold settings while keeping other workflows strict.

Suggested defaults:

```text
IMPORTER_TOKENS_WARN=1500
IMPORTER_TOKENS_FAIL=1800
WORKFLOW_TOKENS_FAIL=1200 for non-importer workflows
TOTAL_TOKENS_WARN can remain conservative or be adjusted only if justified
```

Requirements:

- importer threshold should apply only to the importer workflow;
- ask/dataset_ask/meal_plan should continue using the stricter generic workflow token threshold unless intentionally documented otherwise;
- thresholds should still be configurable through environment variables;
- cost reporting should remain unchanged;
- high importer token usage should still warn/fail if it exceeds the importer-specific limits.

### 3. Add focused tests using the observed live output shape

Add or update tests so a sanitized version of the observed importer output passes.

Test fixture should include:

```text
Title: Lemon Herb White Beans with Toast
Ingredients: white beans, olive oil, garlic, lemon juice, lemon zest, parsley, salt, pepper, toast
Instructions beginning with: Warm, Sauté, Brighten, Finish, Prepare, Serve
Notes disclosing estimated quantities for 4 servings
Provider: openai
Model: gpt-5.4-nano
Citations: at least one
Retrieval count: at least one
Warnings: none
Usage total tokens: 1428
```

Tests should prove:

- the sanitized live importer output passes importer quality scoring;
- action labels and valid recipe verbs do not cause false failures;
- `sauté` and `saute` are both accepted;
- overly long rambling instructions still fail;
- instructions without action language still fail;
- importer token count of about `1428` does not fail by default;
- importer token count above the importer-specific failure threshold still fails;
- non-importer workflows still use the generic workflow token failure threshold;
- threshold env overrides work;
- no raw provider prompt/response/key material appears in committed tests or summaries.

### 4. Preserve safe diagnostics from `0030L`

Do not remove the safe diagnostics added in `0030L`.

The live eval summary should continue to distinguish:

```text
threshold failure
provider call failure
structured output cap/incomplete response
invalid JSON
budget blocked before provider invocation
validation/schema failure
```

Do not make failed provider calls pass just because diagnostics exist.

### 5. Update docs

Update live eval docs/runbook/status/backlog to explain:

- importer uses different scoring and token thresholds because it returns structured recipe JSON plus retrieval metadata;
- good importer outputs should be concise and action-oriented, but valid step labels and common cooking verbs should pass;
- importer thresholds are not global thresholds;
- short-answer workflows remain strict;
- live evals remain explicit opt-in through local ignored `.env` and `-EnvFile`;
- normal validation remains offline/mock.

### 6. Add outbox report

Create:

```text
outbox/0030M-live-importer-eval-scoring-calibration-results.md
```

Include:

- summary of the false failure found;
- instruction scorer calibration made;
- importer-specific token threshold behavior;
- tests added/updated;
- docs updated;
- validation results;
- optional live manual result if run;
- explicit non-goals;
- artifact safety confirmation;
- recommendation on whether `0031A GLM-4.7 Flash Secondary Provider Offload ADR And Eval Harness` is safe to start next.

## Acceptance Criteria

- The observed live importer output shape passes quality scoring.
- The instruction quality check accepts valid recipe verbs and short step labels.
- Bad/rambling/non-action instructions still fail.
- Importer token thresholds are workflow-specific and realistic.
- Non-importer workflows continue using strict generic token thresholds.
- Existing live provider diagnostics from `0030L` remain intact.
- Normal validation remains offline/mock-only.
- Live evals remain explicit opt-in.
- No secrets, raw provider prompts, raw provider responses, or local absolute paths are committed.
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
git add evals ai-api docs README.md outbox/0030M-live-importer-eval-scoring-calibration-results.md

git commit -m "mailbox: complete task 0030M live importer eval scoring calibration"

git pull --rebase origin main
git push origin main
```
