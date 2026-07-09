# 0029B-7 RAG Context Packing And Token Budget

## Goal

Optimize how retrieved recipe examples are packed into provider prompts for the RAG-informed recipe creator/importer.

The system now has:

- anchor-aware importer retrieval scoring;
- retrieval relevance metadata;
- weak-match warnings;
- importer citation rendering;
- full-dataset manual launch support;
- an offline retrieval evaluation harness.

The next RAG hardening step is to ensure the provider receives only the most useful bounded retrieval context, not oversized or noisy recipe records.

## Background

Manual testing showed live importer generation can require more output tokens than the original 500-token cap. The startup script now recommends a higher live importer cap, but the input/context side still needs deliberate controls.

As retrieval improves, the app may retrieve useful examples but pack too much or too little context into the provider prompt. It should pass concise, relevant context that helps the model create better structured recipes while preserving token budget and citation honesty.

This task focuses on prompt/context packing, not retrieval scoring itself.

## Primary Objective

Create a deterministic RAG context packing layer for importer recipe creation that:

- selects which retrieved examples are eligible for prompt context;
- limits how many examples are included;
- limits how much text each example contributes;
- prefers relevant snippets over full records;
- includes enough provenance IDs for citations;
- drops or labels weak examples;
- reports context-packing metadata;
- keeps input token usage bounded and predictable.

## Design Requirements

### 1. Add a context packer

Add a dedicated context-packing function/module for importer RAG.

Suggested location:

```text
ai-api/app/rag_context.py
```

or an appropriate existing module if a better fit exists.

The packer should accept retrieved dataset results and return a bounded provider-context object.

Suggested packed item fields:

- `rank`
- `id`
- `title`
- `matched_fields`
- `snippet`
- `key_ingredients`
- `instruction_summary`
- `relevance_category` or score if available
- `provenance/source_id`

Do not include private local paths.

### 2. Bound context size

Define safe defaults.

Suggested defaults:

- maximum examples packed: 2 or 3;
- maximum snippet characters per example: 240-400;
- maximum ingredient text characters per example: 240-400;
- maximum instruction text characters per example: 240-500;
- maximum total packed context characters: 1,500-2,500;
- no full raw recipe record in provider prompt.

Make these values easy to tune in code, and document them.

Do not add a tokenizer dependency unless already present and lightweight. Character budgets are acceptable for this task.

### 3. Use relevance-aware selection

Prefer examples with:

- strong or moderate relevance;
- higher retrieval score;
- dish-specific title/anchor matches;
- useful instruction snippets.

Downselect or exclude examples that are weak unless they are the only available context.

If weak examples are included, the provider prompt must clearly say they are weak/structure-only examples and must not be treated as authoritative dish examples.

### 4. Improve prompt construction

Update importer prompt construction so the provider receives:

- user recipe notes;
- default serving target;
- concise RAG context block;
- explicit instruction that user intent controls the recipe;
- explicit instruction not to copy retrieved recipes verbatim;
- explicit instruction to use retrieved examples for proportions, structure, and step completeness only when relevant;
- explicit instruction to disclose estimated quantities.

The prompt should not include full raw records or large unbounded text.

### 5. Add context-packing metadata to response

Extend importer retrieval metadata safely with context-packing information.

Suggested fields:

- `packed_count`
- `packed_ids`
- `dropped_ids`
- `max_examples`
- `max_context_chars`
- `packed_context_chars`
- `weak_examples_included`
- `context_budget_warning` if truncation occurred

Do not expose raw provider prompt text in the API/UI.

### 6. Update UI display

Update the demo UI importer retrieval section to show safe context-packing metadata, such as:

- examples retrieved;
- examples packed;
- examples dropped;
- context chars used;
- whether weak examples were included;
- budget warning if present.

Do not show raw prompt text, raw provider response, private local paths, API keys, or `.env` values.

### 7. Add tests

Add deterministic tests for context packing.

Required cases:

- top relevant examples are packed before weaker examples;
- weak examples are dropped when enough strong examples exist;
- weak examples can be included with a warning when no strong examples exist;
- long ingredient/instruction text is truncated safely;
- total packed context stays under budget;
- packed IDs match citations/provenance IDs;
- no raw local paths or secret-like strings appear in packed context or metadata;
- importer prompt builder uses packed context instead of unbounded retrieved records.

### 8. Extend eval harness if useful

If practical, extend `evals/ai_cookbook/retrieval_eval.py` or add a lightweight context-packing eval that confirms:

- expected relevant records are selected for prompt context;
- distractors are not packed when better matches exist;
- context budget metadata is stable.

Keep normal evals offline and deterministic.

### 9. Update docs

Update as needed:

- `docs/ai-evals-plan.md`
- `docs/ai-live-demo-runbook.md`
- `docs/manual-recipe-entry-acceptance-2026-07.md` if present
- `docs/ai-feature-status.md`
- `docs/ai-implementation-backlog.md`
- `README.md` if relevant

Create:

```text
outbox/0029B-7-rag-context-packing-and-token-budget-results.md
```

## Acceptance Criteria

- Dedicated bounded context-packing logic exists.
- Importer prompt construction uses packed context.
- Context size is bounded by deterministic limits.
- Strong/moderate examples are preferred over weak examples.
- Weak examples are dropped or labeled honestly.
- Response metadata includes safe context-packing details.
- Demo UI shows safe context-packing metadata.
- Tests cover selection, truncation, budget, weak examples, and safety.
- Normal evals remain offline and deterministic.
- No live OpenAI calls are required.
- No raw dataset files or generated live artifacts are committed.

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

## Manual Validation Guidance

After completion, optional manual live validation can use:

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

Manual prompts:

```text
classic baked cheesecake for 4 people with cream cheese sugar eggs vanilla graham cracker crust melted butter bake until just set then cool and chill overnight

carbonara pasta for 4 with spaghetti eggs parmesan pancetta black pepper save pasta water mix off heat no heavy cream

omelet for 4 with eggs cheddar cheese onions butter fold it over cook in a skillet

chicken and rice casserole for 4 with cooked chicken rice cream of chicken soup cheddar cheese bake until hot and bubbly
```

Expected manual signs:

- all return 200;
- provider/model are shown;
- servings are 4;
- output has useful quantities and steps;
- retrieval metadata shows `dataset_limit=5000`;
- context-packing metadata is visible;
- packed examples are fewer than or equal to retrieved examples;
- weak examples are not silently treated as strong support;
- no raw prompt text appears in the UI.

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
git add ai-api evals docs README.md outbox/0029B-7-rag-context-packing-and-token-budget-results.md

git commit -m "mailbox: complete task 0029B-7 rag context packing and token budget"

git push origin main
```
