# Task 0025B: Expand Offline AI Evals

## Goal

Expand the offline AI cookbook eval harness added in `0025A` so it covers the major AI workflows, not just the first dataset-ask cases.

This task should add broader deterministic eval cases for:

- dataset ask/RAG over the local Kaggle dataset index;
- saved-recipe Ask My Cookbook RAG;
- structured recipe importer;
- meal-plan generation from saved recipe candidates;
- cross-cutting secret leakage and citation completeness checks.

Keep everything offline, deterministic, mock-only, and safe for local validation and CI callers.

## Build On

Completed work:

- `0019`: provider harness with mock default and OpenAI optional/manual path
- `0021`: structured recipe importer
- `0022`: Ask My Cookbook RAG over saved Vanilla Cookbook recipes
- `0023A`: meal planner foundation
- `0023B`: meal plan endpoint
- `0024A`: local Kaggle dataset adapter/schema inspection
- `0024B`: deterministic local dataset index/search helpers
- `0024C`: indexed dataset retrieval endpoint
- `0024D`: RAG over indexed dataset with citations
- `0025A`: offline eval harness and validation hygiene

Before implementing, confirm the repo has:

- `evals/ai_cookbook/run_evals.py`
- `evals/ai_cookbook/dataset_ask_cases.json`
- `evals/ai_cookbook/README.md`
- `scripts/validate-repo.sh` running evals when present
- `scripts/validate-repo.ps1`
- `docs/ai-evals-plan.md`
- `docs/shared-infrastructure-data-boundaries.md`
- `outbox/0025A-add-offline-evals-and-validation-hygiene-results.md`

If prerequisites are missing, stop and write a short report explaining what is missing.

## Scope

Add additional eval coverage and keep the harness maintainable.

The eval runner should still:

- use stdlib only unless a dependency is already present;
- use JSON fixtures unless YAML support already exists without dependency friction;
- run offline;
- use generated fixture data only;
- not require the real `recipe-dataset/` folder;
- not require a Vanilla Cookbook production DB;
- not require OpenAI API keys;
- not call live providers;
- not call the network;
- not require Docker runtime;
- return non-zero on failed evals;
- print compact pass/fail output.

## Suggested Eval Files

Create or modify as appropriate:

```text
evals/ai_cookbook/run_evals.py
evals/ai_cookbook/dataset_ask_cases.json
evals/ai_cookbook/saved_recipe_ask_cases.json
evals/ai_cookbook/importer_cases.json
evals/ai_cookbook/meal_plan_cases.json
evals/ai_cookbook/README.md
```

If the runner grows too large, split helper modules under:

```text
evals/ai_cookbook/lib/
```

Do not over-engineer the harness. Prefer clear small helper functions over a framework.

## Dataset Ask Evals

Expand dataset ask cases beyond the initial 3 cases from `0025A`.

Add cases for:

1. Positive match with citation completeness.
2. No-match with `provider: none` and empty citations.
3. Missing dataset with `provider: none` and controlled warning.
4. Multiple retrieved matches with all citation source IDs present.
5. Non-retrieved recipe guard: ensure non-retrieved fixture rows do not appear in the provider prompt/answer where detectable.
6. Secret leakage guard.
7. Dataset license/provenance completeness.
8. Empty/blank question validation if practical.

Use tiny generated CSV fixtures only.

## Saved Recipe Ask Evals

Add evals for Ask My Cookbook RAG over saved recipes.

Use a tiny generated SQLite fixture or the existing test fixture pattern from the AI API tests.

Cases should check:

1. Matching saved recipe answer includes saved recipe citation(s).
2. No-match saved recipe question avoids provider call and does not invent an answer.
3. Provider prompt contains only retrieved saved recipe context, not non-retrieved saved recipes.
4. Response does not leak secrets.

If fixture setup is too large for this task, implement one high-signal saved-recipe ask eval and document the deferred cases in the outbox.

## Importer Evals

Add evals for the structured recipe importer.

Cases should check:

1. Mock/provider output validates against the recipe import schema.
2. Required fields are present in the validated draft.
3. Empty/bad input is rejected or handled safely.
4. Output does not leak secrets.

Do not call OpenAI. Use mock/stub provider only.

## Meal Plan Evals

Add evals for meal-plan generation.

Use tiny saved recipe fixtures.

Cases should check:

1. Meal plan uses saved recipe IDs only.
2. Citations refer to saved recipe candidates only.
3. Not-enough-candidates response is partial with warnings, not invented recipes.
4. No-match response uses `provider: none` or the established controlled no-match behavior and does not call the provider.
5. No medical/nutrition certainty claims are present in output.
6. Output does not leak secrets.

If fixture setup is too large for this task, implement one high-signal meal-plan eval and document the deferred cases in the outbox.

## Cross-Cutting Eval Checks

Create common checks if useful:

- `assert_no_secret_leakage(text_or_object)`
- `assert_has_citation_fields(citation, required_fields)`
- `assert_provider_none_for_no_match(response)`
- `assert_ids_subset(actual_ids, allowed_ids)`
- `assert_no_terms_present(text, forbidden_terms)`

Secret-like patterns should include at least:

```text
OPENAI_API_KEY
sk-
Authorization:
.env
raw provider config
CLOUDFLARE_TUNNEL_TOKEN
AWS_SECRET_ACCESS_KEY
AWS_ACCESS_KEY_ID
```

Avoid false positives where possible, but bias toward catching obvious leaks.

## Validation Integration

Keep `scripts/validate-repo.sh` running the eval harness.

After adding cases, the validation output should show a higher eval count than `0025A`'s 3 cases.

If `scripts/validate-repo.ps1` needs small updates for the expanded eval runner, make them. Do not overwork Windows validation in this task.

## Documentation

Update docs to explain:

- what eval categories exist;
- how to run evals locally;
- what each fixture file covers;
- how evals enforce grounding/citations/no-secret-leakage;
- that evals use mock/stub behavior only;
- that live provider smoke tests remain deferred;
- that Qdrant/Postgres/pgvector/embeddings remain deferred.

Update as appropriate:

```text
evals/ai_cookbook/README.md
docs/ai-evals-plan.md
docs/ai-implementation-backlog.md
docs/repo-map.md
docs/repo-validation.md
README.md
```

## Non-Goals

Do not implement:

- Qdrant
- Postgres
- pgvector
- embeddings
- vector DB
- persistent generated indexes
- live OpenAI smoke tests
- CI-specific reporting dashboards
- GitHub Actions changes unless a tiny safe workflow fix is necessary
- UI changes
- Cloudflare/deployment changes
- controller/demo launch workflows
- TTL cleanup workflows
- raw dataset commits
- generated index artifact commits
- `.env` or secret commits

## Tests / Validation

The combined validation should confirm:

- existing 69+ AI API tests still pass;
- expanded offline eval runner passes;
- eval count increased beyond 3 cases;
- secret-pattern scan still passes;
- no raw dataset files are staged;
- no generated index artifacts are staged.

Run from Windows PowerShell in the repo:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
& .\.venv\Scripts\python.exe -m pytest ai-api\tests
& "C:\Program Files\Git\bin\bash.exe" scripts/validate-repo.sh
git diff --check
docker compose config --quiet
```

If direct Windows pytest still fails because of local temp-directory permissions, document the exact error and confirm whether `scripts/validate-repo.sh` passes.

Before committing, explicitly check:

```powershell
git status --short
```

Confirm no raw dataset files, generated index artifacts, `.env`, or secrets are staged.

## Outbox Report

Create:

```text
outbox/0025B-expand-offline-ai-evals-results.md
```

Include:

- Summary
- Files changed
- Eval categories added
- Number of eval cases before/after
- Validation results
- Any deferred eval coverage and why
- Confirmation that no live OpenAI calls were run
- Confirmation that no Qdrant/Postgres/pgvector/embeddings/vector DB were added
- Confirmation that no `.env`, secrets, raw dataset files, or generated index artifacts were committed
- Recommended next task

## Commit

Commit and push:

```bash
git add ai-api evals scripts docs README.md outbox/0025B-expand-offline-ai-evals-results.md

git commit -m "mailbox: complete task 0025B expand offline ai evals"

git push origin main
```

## Done Criteria

- Offline eval harness covers dataset ask beyond the initial 3 cases.
- At least one saved-recipe ask eval exists, unless clearly deferred with reason.
- At least one importer eval exists, unless clearly deferred with reason.
- At least one meal-plan eval exists, unless clearly deferred with reason.
- Cross-cutting secret leakage checks exist or are improved.
- Evals run without real Kaggle data, production DB, network access, OpenAI keys, or live provider calls.
- Repo validation still runs evals.
- Documentation is updated.
- No Qdrant/Postgres/pgvector/embeddings/vector DB are added.
- No raw dataset files or generated indexes are committed.
- No secrets are exposed.
- Outbox report exists.
- Validation passes or any local-only blocker is clearly documented with Git Bash validator still passing.
- Changes are committed and pushed.
