# 0029B-6 RAG Retrieval Evaluation Harness

## Goal

Add a deterministic retrieval evaluation harness for the RAG-informed recipe creator/importer so retrieval relevance can be measured and regression-tested instead of judged only by manual UI inspection.

This task follows `0029B-5`, which added anchor-aware importer retrieval scoring, relevance metadata, and weak-match warnings.

## Background

Manual live testing after `0029B-5` showed that generation quality improved, but top-k retrieval quality still needs measurable evaluation.

Observed manual examples:

### Cheesecake

Input:

```text
classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight
```

Observed:

- generated draft was useful;
- `servings=4`;
- quantities were populated;
- `dataset_limit=5000`;
- `relevance=strong`;
- top two citations were cheesecake-specific:
  - `Creole Cream Cheesecake With Caramel-Apple Topping`;
  - `Pumpkin Cheesecake with Bourbon–Sour Cream Topping`;
- third citation was broad dessert-adjacent:
  - `Apple Crumble with Calvados and Créme Fraîche Ice Cream`.

### Carbonara

Input:

```text
carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream
```

Observed:

- generated draft was useful;
- `servings=4`;
- quantities were populated;
- `dataset_limit=5000`;
- `relevance=strong`;
- top two citations were carbonara-specific:
  - `Pasta Carbonara with English Peas`;
  - `Miso Carbonara with Broccoli Rabe and Red-Pepper Flakes`;
- third citation was pasta-adjacent:
  - `Spaghetti Aglio e Olio with Lots of Kale`.

### Omelet

Input:

```text
omelet for 4 with eggs cheddar cheese onions butter fold it over cook in a skillet
```

Observed:

- generated draft was useful;
- `servings=4`;
- quantities were populated;
- instructions started by beating eggs;
- `dataset_limit=5000`;
- `relevance=moderate`;
- citations were not truly omelet examples:
  - `Skillet Phyllo Pie with Butternut Squash, Kale, and Goat Cheese`;
  - `Breakfast Sandwich on an English Muffin With Charred Red Onions, Herbs, and Cheddar`;
  - `Steakburger with Tangy Caramelized Onions and Herb Butter`.

This is acceptable generation behavior but weak RAG evidence. The next step is an evaluation harness that can make this visible, score it, and protect against regressions.

## Primary Objective

Create an offline deterministic RAG retrieval evaluation harness that can score whether the retrieved examples are materially relevant to the intended dish.

The harness should be independent of live OpenAI calls and should test the retrieval layer directly.

## Required Features

### 1. Retrieval eval case format

Create a small eval case format for importer retrieval relevance.

Suggested file:

```text
evals/ai_cookbook/retrieval_cases.yaml
```

Each case should support fields like:

- `id`
- `query`
- `required_anchors`
- `preferred_title_terms`
- `preferred_ingredient_terms`
- `preferred_instruction_terms`
- `negative_title_terms`
- `negative_generic_terms`
- `expected_relevance_min`
- `min_relevant_in_top_k`
- `top_k`
- `notes`

Keep the format simple enough to maintain by hand.

### 2. Deterministic fixture dataset

Use generated fixture datasets for tests. Do not require the real `recipe-dataset/` folder in CI or normal validation.

Fixtures should include both relevant records and distractors.

Required dish families:

- cheesecake;
- carbonara;
- omelet;
- chicken and rice casserole;
- no-bake cheesecake or baked-vs-no-bake contrast if easy to include.

Each family should include:

- at least one strong match;
- at least one medium/adjacent match;
- at least one distractor that shares generic terms but not dish intent.

### 3. Retrieval scoring metrics

Add deterministic metrics such as:

- top-1 relevance pass/fail;
- top-k relevant count;
- expected anchor coverage;
- negative/generic drift count;
- relevance category check;
- warning expectation check.

The harness should clearly report why a case failed.

Example report line:

```text
cheesecake_baked: PASS top1=cheesecake top3_relevant=2/3 relevance=strong anchors=6/8
```

Failure example:

```text
omelet_basic: FAIL top1=skillet pie expected title term omelet/omelette; top3_relevant=0/3
```

### 4. Integrate with existing eval runner

Integrate retrieval relevance evals into:

```powershell
& .\.venv\Scripts\python.exe evals\ai_cookbook\run_evals.py
```

The existing eval runner currently reports 17 cases. It should include the new retrieval relevance cases and fail non-zero on retrieval regressions.

Normal validation must remain offline and mock-only.

### 5. Add importer retrieval unit tests

Add focused tests around the retrieval scoring functions so the behavior is covered at both unit and eval levels.

Tests should cover:

- cheesecake strong match beats apple crumble / pear dessert;
- carbonara strong match beats creamy pasta / aglio e olio;
- omelet match beats breakfast sandwich / toast / skillet pie;
- chicken rice casserole match beats chicken-only and rice-only records;
- weak-match warning appears when only generic/distractor records are available;
- relevance category calculation is deterministic.

### 6. Add manual-live results capture guidance

Update docs so manual live RAG tests can be recorded consistently.

Include a simple matrix with:

- input text;
- provider/model;
- dataset limit;
- document count;
- relevance category;
- warning;
- top-1 title;
- top-3 titles;
- relevant count in top 3;
- notes.

Do not commit raw live JSON artifacts.

### 7. Update docs and status

Update as needed:

- `docs/ai-evals-plan.md`
- `docs/ai-feature-status.md`
- `docs/ai-live-demo-runbook.md`
- `docs/manual-recipe-entry-acceptance-2026-07.md` if present
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

Create:

```text
outbox/0029B-6-rag-retrieval-evaluation-harness-results.md
```

## Acceptance Criteria

- Retrieval relevance eval cases exist and are easy to extend.
- Eval fixtures include relevant records and distractors.
- Eval runner includes retrieval relevance checks.
- Eval runner fails non-zero on retrieval regressions.
- Unit tests cover retrieval relevance scoring and weak-match warnings.
- Normal validation remains offline and mock-only.
- No live OpenAI calls are required.
- No raw dataset files are committed.
- No generated live artifacts are committed.
- Manual live RAG result capture guidance is documented.

## Validation

Run:

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

If direct Windows pytest still fails with the known temp-directory ACL issue, document it and confirm Git Bash validator passes.

Do not run live OpenAI during normal validation.

## Non-Goals

- No embeddings
- No vector database
- No Qdrant
- No Postgres
- No pgvector
- No persistent generated index
- No production storage
- No production auth
- No paid access
- No public route exposure
- No Cloudflare changes
- No upstream Vanilla Cookbook frontend rewrite
- No browser automation
- No screenshots
- No raw dataset commits

## Commit

```bash
git add ai-api evals docs README.md outbox/0029B-6-rag-retrieval-evaluation-harness-results.md

git commit -m "mailbox: complete task 0029B-6 rag retrieval evaluation harness"

git push origin main
```
